from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import time
from pathlib import Path
from typing import Any

import numpy as np

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT

from ai.ctx_lstm import (
    DIRECTION_CLASSES,
    direction_context_to_heading_observation,
    load_context_lstm,
    require_fitted_calibration,
)
from ai.context import ContextConfig, context_score
from ai.detection import YoloEngineDetector
from runtime.controller import NmpcPrediction
from runtime.controller import CompiledController
from runtime.kalman import SixStateKalman
from runtime.local_path import (
    FixedGlobalLocalPath,
    context_footprint_points,
    evaluate_context_replan,
    generate_context_local_detour,
    path_clearance_to_footprint,
)
from hardware import (
    AstraSSource,
    CcaCanSource,
    CsvWriters,
    N10P_PROTOCOL_PROFILES,
    N10PSerialSource,
    POSITION_STATE_FIELDS,
    PoseContextProcessor,
    RobotGeometry,
    Stm32SerialSource,
    latest_lidar_context,
    utc_ns,
    write_pose_overlay,
    write_runtime_metadata,
)
from shared import load_contract, validate_capture_calibration


ROOT = PROJECT_ROOT
DEFAULT_ROBOT_RADIUS_M = 0.1772541986
CONTEXT_DT_S = float(load_contract()["context"]["dt_s"])
ZERO_COMMAND = (0.0, 0.0, 0.0)
REQUIRED_SAFETY_FIELDS = (
    "approved",
    "emergency_stop_verified",
    "remote_disable_verified",
    "watchdog_verified",
)


def select_stm_command(
    source: Any,
    requested: tuple[float, float, float],
    stop_latched: bool,
) -> tuple[tuple[float, float, float], bool]:
    telemetry = getattr(source, "latest", None)
    observed_stop = bool(telemetry is not None and getattr(telemetry, "flag_stop", 0))
    latched = bool(stop_latched or observed_stop)
    return (ZERO_COMMAND if latched else requested), latched


def load_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path}: invalid JSON") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return payload


def validate_safety_record(path: Path) -> dict[str, Any]:
    try:
        payload = load_object(path)
    except ValueError as error:
        try:
            import yaml
        except ImportError as yaml_error:
            raise error from yaml_error
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as yaml_error:
            raise ValueError(f"{path} is not a valid safety record") from yaml_error
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain an object")
    record = payload.get("safety") if isinstance(payload.get("safety"), dict) else payload
    missing = [field for field in REQUIRED_SAFETY_FIELDS if record.get(field) is not True]
    if missing:
        raise ValueError("safety record must set true: " + ", ".join(missing))
    return payload


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_value(payload: dict[str, Any], path: str) -> Any:
    value: Any = payload
    for component in path.split("."):
        if not isinstance(value, dict) or component not in value:
            raise ValueError(f"hardware config is missing {path}")
        value = value[component]
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"hardware config requires a concrete value for {path}")
    return value


def validate_config(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "cca-hardware-runtime-v1":
        raise ValueError("hardware config must use schema cca-hardware-runtime-v1")
    for path in (
        "camera.model",
        "camera.sdk",
        "camera.depth_scale_m",
        "lidar.model",
        "lidar.port",
        "lidar.baudrate",
        "lidar.protocol_profile",
        "firmware",
        "clock",
    ):
        require_value(payload, path)
    transport = payload.get("transport", "cca_can")
    if transport not in {"stm32_serial", "cca_can"}:
        raise ValueError("hardware config transport must be stm32_serial or cca_can")
    if transport == "stm32_serial":
        for path in ("stm32.port", "stm32.baudrate"):
            require_value(payload, path)
        stm_baudrate = payload["stm32"]["baudrate"]
        if isinstance(stm_baudrate, bool) or not isinstance(stm_baudrate, int) or stm_baudrate <= 0:
            raise ValueError("hardware config stm32.baudrate must be a positive integer")
    else:
        for path in ("can.channel", "can.interface", "can.bitrate"):
            require_value(payload, path)
    if payload["camera"]["model"] != "Astra-S":
        raise ValueError("hardware config camera.model must be Astra-S")
    if payload["lidar"]["model"] != "N10P":
        raise ValueError("hardware config lidar.model must be N10P")
    if payload["lidar"]["protocol_profile"] not in N10P_PROTOCOL_PROFILES:
        supported = ", ".join(sorted(N10P_PROTOCOL_PROFILES))
        raise ValueError(f"hardware config lidar.protocol_profile must be one of: {supported}")
    baudrate = payload["lidar"]["baudrate"]
    if isinstance(baudrate, bool) or not isinstance(baudrate, int) or baudrate <= 0:
        raise ValueError("hardware config lidar.baudrate must be a positive measured integer")
    pair_skew = payload["camera"].get("max_pair_skew_us")
    if pair_skew is not None and (
        isinstance(pair_skew, bool)
        or not isinstance(pair_skew, (int, float))
        or not math.isfinite(float(pair_skew))
        or float(pair_skew) <= 0.0
    ):
        raise ValueError("hardware config camera.max_pair_skew_us must be positive and finite")
    if payload["clock"] not in {"system_time", "robot_time"}:
        raise ValueError("hardware config clock must be system_time or robot_time")
    if payload.get("control_mode", "position_state") != "position_state":
        raise ValueError("hardware config control_mode must be position_state")
    state_definition = payload.get("state_definition")
    if state_definition is not None and tuple(state_definition) != POSITION_STATE_FIELDS:
        raise ValueError("hardware config state_definition must be [x,y,theta,vx,vy,omega]")


def runtime_robot_geometry(payload: dict[str, Any]) -> dict[str, Any]:
    source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
    return {
        "model": payload.get("urdf_source", "unknown"),
        "urdf_path": payload.get("urdf_path"),
        "physical_spec_path": payload.get("physical_spec_path"),
        "geometry_authority": payload.get("geometry_authority"),
        "urdf_sha256": source.get("urdf_sha256"),
        "xacro_sha256": source.get("xacro_sha256"),
        "physical_spec_sha256": source.get("physical_spec_sha256"),
        "wheel_radius_m": payload.get("wheel_radius_m"),
        "half_length_m": payload.get("half_length_m"),
        "half_width_m": payload.get("half_width_m"),
        "sensor_mounts": payload.get("sensor_mounts"),
        "footprint": payload.get("footprint"),
    }


def validate_robot_source(payload: dict[str, Any], config_path: Path) -> dict[str, str]:
    source = payload.get("source")
    if not isinstance(source, dict):
        raise ValueError("hardware config source hashes are required")
    expected_urdf = source.get("urdf_sha256")
    expected_xacro = source.get("xacro_sha256")
    hash_pattern = re.compile(r"^[0-9a-fA-F]{64}$")
    if not isinstance(expected_urdf, str) or not hash_pattern.fullmatch(expected_urdf):
        raise ValueError("hardware config source.urdf_sha256 must be a SHA-256 hash")
    if not isinstance(expected_xacro, str) or not hash_pattern.fullmatch(expected_xacro):
        raise ValueError("hardware config source.xacro_sha256 must be a SHA-256 hash")
    urdf_value = payload.get("urdf_path")
    if isinstance(urdf_value, str) and urdf_value.strip():
        urdf_path = Path(urdf_value)
        if not urdf_path.is_absolute():
            urdf_path = config_path.parent / urdf_path
    elif payload.get("urdf_source") == "mini_mec_robot":
        urdf_path = ROOT / "reference" / "robot" / "rai_robot_urdf" / "rai_robot_urdf" / "urdf" / "mini_mec_robot.urdf"
    else:
        raise ValueError("hardware config must declare a resolvable URDF source")
    xacro_path = ROOT / "reference" / "robot" / "turn_on_rai_robot" / "urdf" / "mini_mec_gazebo.urdf.xacro"
    if not urdf_path.is_file() or not xacro_path.is_file():
        raise ValueError("hardware config URDF/xacro source files are unavailable")
    actual_urdf = sha256_path(urdf_path)
    actual_xacro = sha256_path(xacro_path)
    if actual_urdf.lower() != expected_urdf.lower():
        raise ValueError("hardware config URDF hash does not match the loaded source")
    if actual_xacro.lower() != expected_xacro.lower():
        raise ValueError("hardware config xacro hash does not match the loaded source")
    return {"urdf_sha256": actual_urdf, "xacro_sha256": actual_xacro}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Direct no-ROS CCA hardware recorder")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--map", dest="map_path", type=Path, required=True)
    parser.add_argument("--pose-engine", type=Path, required=True)
    parser.add_argument("--pose-manifest", type=Path, required=True)
    parser.add_argument(
        "--lstm-checkpoint",
        type=Path,
        help="optional frozen checkpoint; omit for the initial context-only capture",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frames-root", type=Path)
    parser.add_argument("--duration-s", type=float, required=True)
    parser.add_argument("--sample-period-s", type=float, default=CONTEXT_DT_S)
    parser.add_argument("--controller", choices=("external", "cca_nmpc"), default="external")
    parser.add_argument("--command-csv", type=Path)
    parser.add_argument("--allow-actuation", action="store_true")
    parser.add_argument("--safety-record", type=Path)
    return parser.parse_args()


def load_command_schedule(path: Path | None) -> list[tuple[float, float, float, float]]:
    if path is None:
        return [(0.0, 0.0, 0.0, 0.0)]
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or ())
        time_field = "t_s" if "t_s" in fields else "t_ns" if "t_ns" in fields else None
        required = {"vx_mps", "vy_mps", "wz_radps"}
        if time_field is None or not required.issubset(fields):
            raise ValueError("command CSV requires t_s or t_ns plus vx_mps, vy_mps, wz_radps")
        schedule: list[tuple[float, float, float, float]] = []
        previous = -math.inf
        for row_number, row in enumerate(reader, start=2):
            try:
                timestamp = float(row[time_field])
                timestamp = timestamp * 1.0e-9 if time_field == "t_ns" else timestamp
                values = tuple(float(row[name]) for name in ("vx_mps", "vy_mps", "wz_radps"))
            except (TypeError, ValueError) as error:
                raise ValueError(f"command CSV row {row_number} contains invalid numeric data") from error
            if not math.isfinite(timestamp) or timestamp < 0.0 or timestamp <= previous:
                raise ValueError(f"command CSV row {row_number} timestamps must be increasing and nonnegative")
            if not all(math.isfinite(value) for value in values):
                raise ValueError(f"command CSV row {row_number} velocity values must be finite")
            schedule.append((timestamp, *values))
            previous = timestamp
    if not schedule:
        raise ValueError("command CSV must contain at least one row")
    if any(abs(value) > 1.0e-12 for value in schedule[-1][1:]):
        raise ValueError("command CSV must end with an explicit zero-velocity row")
    return schedule


def command_at(schedule: list[tuple[float, float, float, float]], elapsed_s: float) -> tuple[float, float, float]:
    if elapsed_s > schedule[-1][0]:
        return (0.0, 0.0, 0.0)
    selected = schedule[0]
    for point in schedule:
        if point[0] > elapsed_s:
            break
        selected = point
    return selected[1:]


def load_controller_map(path: Path) -> tuple[np.ndarray, dict[str, float | int]]:
    payload = load_object(path)
    raw_path = payload.get("global_path_xy", payload.get("global_path"))
    if not isinstance(raw_path, list) or len(raw_path) < 2:
        raise ValueError("CCA map requires global_path_xy with at least two points")
    try:
        global_path = np.asarray(raw_path, dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise ValueError("CCA global_path_xy must be numeric") from error
    if global_path.ndim != 2 or global_path.shape[1] != 2 or not np.isfinite(global_path).all():
        raise ValueError("CCA global_path_xy must have shape [N,2] and finite values")
    if np.any(np.linalg.norm(np.diff(global_path, axis=0), axis=1) <= 1.0e-9):
        raise ValueError("CCA global_path_xy must not contain duplicate consecutive points")
    settings = payload.get("cca_nmpc")
    if not isinstance(settings, dict):
        raise ValueError("CCA map requires a cca_nmpc settings object")
    required = {
        "horizon": int,
        "cruise_speed_mps": (int, float),
        "human_std_m": (int, float),
        "safe_distance_m": (int, float),
        "lateral_offset_m": (int, float),
        "longitudinal_offset_m": (int, float),
    }
    values: dict[str, float | int] = {}
    for name, expected in required.items():
        value = settings.get(name)
        if isinstance(value, bool) or not isinstance(value, expected):
            raise ValueError(f"CCA map requires numeric cca_nmpc.{name}")
        numeric = float(value)
        if not math.isfinite(numeric) or numeric <= 0.0:
            raise ValueError(f"CCA map requires positive finite cca_nmpc.{name}")
        values[name] = int(value) if expected is int else numeric
    if int(values["horizon"]) < 1:
        raise ValueError("CCA map horizon must be positive")
    if float(values["safe_distance_m"]) > 1.0:
        raise ValueError("CCA map safe_distance_m must not exceed 1 m")
    return global_path, values


def _polyline_reference(
    path_xy: np.ndarray,
    state: np.ndarray,
    *,
    horizon: int,
    dt_s: float,
    cruise_speed_mps: float,
) -> np.ndarray:
    path = np.asarray(path_xy, dtype=np.float64)
    position = np.asarray(state[:2], dtype=np.float64)
    segments = np.diff(path, axis=0)
    lengths = np.linalg.norm(segments, axis=1)
    cumulative = np.concatenate(([0.0], np.cumsum(lengths)))
    projection_fraction = np.divide(
        np.sum((position[None] - path[:-1]) * segments, axis=1),
        lengths * lengths,
        out=np.zeros_like(lengths),
        where=lengths > 1.0e-12,
    )
    projection_fraction = np.clip(projection_fraction, 0.0, 1.0)
    projections = path[:-1] + projection_fraction[:, None] * segments
    nearest = int(np.argmin(np.linalg.norm(projections - position[None], axis=1)))
    progress = cumulative[nearest] + projection_fraction[nearest] * lengths[nearest]
    distances = np.clip(progress + cruise_speed_mps * dt_s * np.arange(horizon + 1), 0.0, cumulative[-1])
    indices = np.clip(np.searchsorted(cumulative, distances, side="right") - 1, 0, len(segments) - 1)
    fractions = np.divide(
        distances - cumulative[indices],
        lengths[indices],
        out=np.zeros_like(distances),
        where=lengths[indices] > 1.0e-12,
    )
    positions = path[indices] + fractions[:, None] * segments[indices]
    tangents = segments[indices] / np.maximum(lengths[indices, None], 1.0e-12)
    yaw = np.unwrap(np.arctan2(tangents[:, 1], tangents[:, 0]))
    reference = np.zeros((6, horizon + 1), dtype=np.float64)
    reference[:2] = positions.T
    reference[2] = yaw
    world_velocity = cruise_speed_mps * tangents
    for index, yaw_value in enumerate(yaw):
        cosine = math.cos(float(yaw_value))
        sine = math.sin(float(yaw_value))
        reference[3:5, index] = (cosine * world_velocity[index, 0] + sine * world_velocity[index, 1], -sine * world_velocity[index, 0] + cosine * world_velocity[index, 1])
    return reference


class OnlineCcaNmpc:
    def __init__(
        self,
        global_path_xy: np.ndarray,
        settings: dict[str, float | int],
        dt_s: float,
        robot_radius_m: float = DEFAULT_ROBOT_RADIUS_M,
    ) -> None:
        self.global_path = np.asarray(global_path_xy, dtype=np.float64).copy()
        self.path = FixedGlobalLocalPath.from_global(self.global_path)
        self.horizon = int(settings["horizon"])
        self.cruise_speed_mps = float(settings["cruise_speed_mps"])
        self.human_std_m = float(settings["human_std_m"])
        self.safe_distance_m = float(settings["safe_distance_m"])
        self.lateral_offset_m = float(settings["lateral_offset_m"])
        self.longitudinal_offset_m = float(settings["longitudinal_offset_m"])
        if not math.isfinite(robot_radius_m) or robot_radius_m <= 0.0:
            raise ValueError("online CCA robot radius must be positive and finite")
        self.robot_radius_m = float(robot_radius_m)
        configured_clearance = settings.get("human_clearance_m")
        expected_clearance = self.robot_radius_m + 0.60
        if configured_clearance is None:
            configured_clearance = expected_clearance
        if (
            not isinstance(configured_clearance, (int, float))
            or not math.isfinite(float(configured_clearance))
            or float(configured_clearance) <= 0.0
            or not math.isclose(float(configured_clearance), expected_clearance, rel_tol=0.0, abs_tol=1.0e-6)
        ):
            raise ValueError("online CCA human clearance must match the URDF robot radius")
        self.human_clearance_m = float(configured_clearance)
        self.dt_s = float(dt_s)
        self.controller = CompiledController(
            "cca_nmpc", self.dt_s, self.horizon, 1000.0 * self.dt_s,
            self.robot_radius_m, 0.60,
        )
        self.context_score_config = ContextConfig()
        self.previous_command = np.zeros(3, dtype=np.float64)
        self.previous_heading: np.ndarray | None = None

    def _observation(self, record: Any) -> Any:
        if not record.context_valid or record.direction not in DIRECTION_CLASSES:
            return None
        return direction_context_to_heading_observation(
            record.direction,
            position_xy=np.asarray((record.position_x_m, record.position_y_m), dtype=np.float64),
            speed_mps=float(record.speed_mps),
            direction_confidence=float(record.confidence),
            timestamp_ns=int(record.t_ns),
            frame_id=str(record.frame_path),
            track_id=0,
            source_sha256=hashlib.sha256(b"runtime-context").hexdigest(),
            coordinate_units="robot_m",
        )

    def _prediction(self, observation: Any, reference: np.ndarray) -> NmpcPrediction:
        velocity = np.asarray(observation.heading_unit, dtype=np.float64) * float(observation.speed_per_s)
        step_times = self.dt_s * np.arange(1, self.horizon + 1, dtype=np.float64)
        mean_xy = observation.position_xy[None, None, None, :] + step_times[None, None, :, None] * velocity[None, None, None, :]
        velocity_xy = np.repeat(velocity[None, None, None, :], self.horizon, axis=2)
        covariance = np.zeros((1, 1, self.horizon, 2, 2), dtype=np.float64)
        covariance[..., 0, 0] = self.human_std_m * self.human_std_m
        covariance[..., 1, 1] = self.human_std_m * self.human_std_m
        nominal_robot_xy = reference[:2, 1:].T
        yaw = reference[2, 1:]
        robot_world_velocity = np.column_stack(
            (
                np.cos(yaw) * reference[3, 1:] - np.sin(yaw) * reference[4, 1:],
                np.sin(yaw) * reference[3, 1:] + np.cos(yaw) * reference[4, 1:],
            )
        )
        relative_position = observation.position_xy[None, :] - nominal_robot_xy
        relative_velocity = velocity[None, :] - robot_world_velocity
        scores = []
        for index in range(self.horizon):
            scores.append(
                context_score(
                    relative_position[index],
                    relative_velocity[index],
                    robot_world_velocity[index],
                    velocity,
                    0.0,
                    self.context_score_config,
                )
            )
        context = np.asarray(scores, dtype=np.float64)[None, :]
        human_yaw = np.full((1, self.horizon), math.atan2(float(velocity[1]), float(velocity[0])))
        return NmpcPrediction(
            mean_xy=mean_xy,
            velocity_xy=velocity_xy,
            relative_covariance_xy=covariance,
            probability=np.ones((1, 1), dtype=np.float64),
            context=context,
            nominal_robot_xy=nominal_robot_xy,
            human_yaw_rad=human_yaw,
        )

    def _maybe_replan(self, state: np.ndarray, observation: Any) -> tuple[bool, tuple[str, ...]]:
        decision = evaluate_context_replan(
            self.path.local_path_xy,
            observation,
            now_ns=int(observation.timestamp_ns),
            previous_heading_unit=self.previous_heading,
            safe_distance_m=self.safe_distance_m,
        )
        if not decision.replan:
            return False, decision.reasons
        if self.path.local_generation_count > 0 and "direction_change" not in decision.reasons:
            return False, decision.reasons
        footprint = context_footprint_points(observation)
        candidates = []
        for side in (-1, 1):
            candidate = generate_context_local_detour(
                state[:2],
                self.global_path[-1],
                observation,
                side=side,
                lateral_offset_m=self.lateral_offset_m,
                longitudinal_offset_m=self.longitudinal_offset_m,
            )
            candidates.append((path_clearance_to_footprint(candidate, footprint), -side, candidate))
        _, _, selected = max(candidates, key=lambda item: (item[0], item[1]))
        self.path = FixedGlobalLocalPath(self.global_path, selected, self.path.local_generation_count + 1)
        return True, decision.reasons

    def step(self, state: np.ndarray, record: Any) -> tuple[tuple[float, float, float], dict[str, Any]]:
        state = np.asarray(state, dtype=np.float64)
        if state.shape != (6,) or not np.isfinite(state).all():
            raise ValueError("online CCA state must be six finite values")
        if not record.lstm_configured:
            raise RuntimeError("online CCA requires a configured LSTM checkpoint")
        if not record.lstm_active:
            self.previous_command[:] = 0.0
            return ZERO_COMMAND, {"status": "LSTM_WARMUP_STOP", "local_replanned": False, "local_generation_count": self.path.local_generation_count}
        observation = self._observation(record)
        if observation is None:
            self.previous_command[:] = 0.0
            return ZERO_COMMAND, {"status": "CONTEXT_INVALID_STOP", "local_replanned": False, "local_generation_count": self.path.local_generation_count}
        replanned, reasons = self._maybe_replan(state, observation)
        reference = _polyline_reference(
            self.path.local_path_xy,
            state,
            horizon=self.horizon,
            dt_s=self.dt_s,
            cruise_speed_mps=self.cruise_speed_mps,
        )
        result = self.controller.command(
            state,
            reference,
            self.previous_command,
            self._prediction(observation, reference),
        )
        command = np.asarray(result.first_command_mps, dtype=np.float64)
        if command.shape != (3,) or not np.isfinite(command).all():
            raise RuntimeError("online CCA produced an invalid body-velocity command")
        self.previous_command = command.copy()
        self.previous_heading = observation.heading_unit.copy()
        return tuple(float(value) for value in command), {
            "status": result.status,
            "solve_ms": float(result.solve_time_ms),
            "iterations": int(result.iterations),
            "deadline_missed": bool(result.deadline_missed),
            "risk_bound": float(result.risk_bound),
            "risk_slack_m": float(result.maximum_risk_slack_m),
            "constraint_violation": float(result.maximum_constraint_violation),
            "local_replanned": replanned,
            "local_generation_count": self.path.local_generation_count,
            "replan_reasons": list(reasons),
        }


def run(args: argparse.Namespace) -> int:
    config = load_object(args.config)
    validate_config(config)
    transport = str(config.get("transport", "cca_can"))
    if args.controller == "cca_nmpc":
        if transport != "stm32_serial":
            raise ValueError("online CCA requires transport=stm32_serial")
        if not args.allow_actuation:
            raise ValueError("online CCA requires --allow-actuation")
        if args.command_csv is not None:
            raise ValueError("online CCA cannot be combined with --command-csv")
        if args.lstm_checkpoint is None:
            raise ValueError("online CCA requires --lstm-checkpoint")
        global_path, controller_settings = load_controller_map(args.map_path)
        command_schedule = [(0.0, *ZERO_COMMAND)]
    else:
        global_path = None
        controller_settings = None
        command_schedule = load_command_schedule(args.command_csv)
        if args.command_csv is not None and not args.allow_actuation:
            raise ValueError("--command-csv requires --allow-actuation")
        if args.allow_actuation and args.command_csv is None:
            raise ValueError("--allow-actuation requires --command-csv")
        if transport != "stm32_serial" and args.allow_actuation:
            raise ValueError("actuation schedule requires transport=stm32_serial")
    motion_requested = bool(args.allow_actuation and (args.controller == "cca_nmpc" or args.command_csv is not None))
    safety_record = None
    if motion_requested:
        safety_path = getattr(args, "safety_record", None)
        if safety_path is None:
            raise ValueError("motion requires --safety-record with H0 stop checks")
        safety_record = validate_safety_record(safety_path.resolve())
    calibration = load_object(args.calibration)
    validate_capture_calibration(calibration, camera="Astra-S", lidar="N10P")
    if not args.map_path.is_file():
        raise FileNotFoundError(args.map_path)
    if args.duration_s <= 0.0 or args.sample_period_s <= 0.0:
        raise ValueError("duration and sample period must be positive")
    if not abs(args.sample_period_s - CONTEXT_DT_S) <= 1.0e-9:
        raise ValueError(
            f"sample period must equal the frozen context contract ({CONTEXT_DT_S:g} s)"
        )
    geometry = RobotGeometry.from_json(args.config)
    validate_robot_source(config, args.config.resolve())
    footprint = config.get("footprint")
    if not isinstance(footprint, dict):
        raise ValueError("hardware config must include the URDF-derived footprint")
    footprint_radius = footprint.get("footprint_radius_m")
    if (
        not isinstance(footprint_radius, (int, float))
        or not math.isfinite(float(footprint_radius))
        or float(footprint_radius) <= 0.0
    ):
        raise ValueError("hardware config footprint radius must be positive and finite")
    detector = YoloEngineDetector(args.pose_engine, args.pose_manifest)
    if args.lstm_checkpoint is None:
        lstm = None
        checkpoint: dict[str, Any] = {}
        lstm_checkpoint_sha256: str | None = None
    else:
        lstm, checkpoint = load_context_lstm(args.lstm_checkpoint, map_location="cpu")
        if args.controller == "cca_nmpc":
            require_fitted_calibration(checkpoint)
        lstm_checkpoint_sha256 = sha256_path(args.lstm_checkpoint.resolve())
    camera_cfg = config["camera"]
    lidar_cfg = config["lidar"]
    can_cfg = config.get("can", {})
    stm_cfg = config.get("stm32", {})
    output = args.output.resolve()
    frames_root = (args.frames_root or output.parent / f"{output.name}-frames").resolve()
    if frames_root.exists():
        raise ValueError(f"frames directory already exists: {frames_root}")
    frames_root.mkdir(parents=True)
    writers = CsvWriters(output)
    shutil.copy2(args.map_path, output / "map.json")
    shutil.copy2(args.calibration, output / "calibration.json")
    write_runtime_metadata(
        frames_root,
        camera="Astra-S",
        lidar="N10P",
        firmware=str(config["firmware"]),
        clock=str(config["clock"]),
        robot_config=args.config.resolve(),
        extra={
            "pose_engine": args.pose_engine.resolve().as_posix(),
            "pose_manifest": args.pose_manifest.resolve().as_posix(),
            "lstm_configured": lstm is not None,
            "lstm_checkpoint": args.lstm_checkpoint.resolve().as_posix() if args.lstm_checkpoint else None,
            "lstm_checkpoint_sha256": lstm_checkpoint_sha256,
            "frames_root": frames_root.as_posix(),
            "capture_interface": f"direct_{transport}_openni",
            "transport": transport,
            "actuation": (
                "cca_nmpc_online_body_velocity"
                if args.controller == "cca_nmpc"
                else "scheduled_body_velocity" if args.allow_actuation else "zero_velocity_only"
            ),
            "controller": args.controller,
            "control_mode": "position_state",
            "state_definition": list(POSITION_STATE_FIELDS),
            "state_csv_mapping": {"theta_rad": "yaw_rad", "omega_radps": "wz_radps"},
            "lidar_protocol_profile": str(lidar_cfg["protocol_profile"]),
            "camera_pair_skew_limit_us": camera_cfg.get("max_pair_skew_us"),
            "urdf_path": config.get("urdf_path"),
            "urdf_source": config.get("urdf_source"),
            "robot_geometry": runtime_robot_geometry(config),
            "robot_footprint": config.get("footprint"),
            "safety_record": (
                {
                    "path": args.safety_record.resolve().as_posix(),
                    "sha256": sha256_path(args.safety_record.resolve()),
                }
                if safety_record is not None
                else None
            ),
        },
    )
    camera = AstraSSource(
        uri=camera_cfg.get("uri"),
        sdk_path=camera_cfg.get("sdk_path"),
        depth_scale_m=float(camera_cfg["depth_scale_m"]),
        max_pair_skew_us=(
            float(camera_cfg["max_pair_skew_us"])
            if camera_cfg.get("max_pair_skew_us") is not None
            else None
        ),
    )
    lidar = N10PSerialSource(
        str(lidar_cfg["port"]),
        profile=str(lidar_cfg["protocol_profile"]),
        baudrate=int(lidar_cfg["baudrate"]),
        timeout_s=float(lidar_cfg.get("timeout_s", 0.1)),
    )
    stm_source = (
        Stm32SerialSource(
            str(stm_cfg["port"]),
            baudrate=int(stm_cfg["baudrate"]),
            timeout_s=float(stm_cfg.get("timeout_s", 0.1)),
            mode=int(stm_cfg.get("mode", 0)),
        )
        if transport == "stm32_serial"
        else None
    )
    if stm_source is not None:
        capture_path = frames_root / "capture.json"
        capture_metadata = json.loads(capture_path.read_text(encoding="utf-8"))
        capture_metadata["transport_backend"] = stm_source.backend
        capture_metadata["transport_library"] = (
            stm_source.transport_library.as_posix()
            if stm_source.transport_library is not None
            else None
        )
        capture_path.write_text(json.dumps(capture_metadata, indent=2) + "\n", encoding="utf-8")
    can_source = (
        CcaCanSource(
            str(can_cfg["channel"]),
            interface=str(can_cfg["interface"]),
            bitrate=int(can_cfg["bitrate"]),
        )
        if transport == "cca_can"
        else None
    )
    processor = PoseContextProcessor(
        detector,
        calibration,
        lstm=lstm,
        lstm_path=args.lstm_checkpoint.resolve().as_posix() if args.lstm_checkpoint else None,
        dt_s=CONTEXT_DT_S,
    )
    online_controller = (
        OnlineCcaNmpc(
            global_path,
            controller_settings,
            args.sample_period_s,
            robot_radius_m=float(footprint_radius),
        )
        if args.controller == "cca_nmpc" and global_path is not None and controller_settings is not None
        else None
    )
    estimator = SixStateKalman()
    context_last = 0
    state_last = 0
    control_last = 0
    event_last = 0
    control_seen: tuple[Any, ...] | None = None
    status_seen: tuple[Any, ...] | None = None
    fault_seen: int | None = None
    stm_state_last = 0
    lidar_last = 0

    def refresh_camera_metadata() -> None:
        metadata_path = frames_root / "capture.json"
        if not metadata_path.is_file():
            return
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["camera_timing"] = camera.timing_metadata()
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            pass

    def event(event_type: str, detail: str, status_code: str = "") -> None:
        nonlocal event_last
        timestamp = max(utc_ns(), event_last + 1)
        event_last = timestamp
        writers.write(
            "events.csv",
            {
                "t_ns": timestamp,
                "event_type": event_type,
                "solve_ms": "",
                "status_code": status_code,
                "sequence": "",
                "detail": detail,
            },
        )

    event("capture_started", f"direct_{transport}_openni")
    camera_started = False
    lidar_started = False
    stm_started = False
    can_started = False
    frame_index = 0
    control_start = time.monotonic()
    last_command_timestamp = 0
    next_command = ZERO_COMMAND
    stm_stop_latched = False
    cca_stop_latched = False
    try:
        camera.start()
        camera_started = True
        refresh_camera_metadata()
        lidar.start()
        lidar_started = True
        if stm_source is not None:
            stm_source.start()
            stm_started = True
        if can_source is not None:
            can_source.start()
            can_started = True
        deadline = time.monotonic() + args.duration_s
        while time.monotonic() < deadline:
            elapsed_s = time.monotonic() - control_start
            if stm_source is not None:
                if args.controller == "cca_nmpc":
                    requested = next_command if args.allow_actuation else ZERO_COMMAND
                else:
                    requested = command_at(command_schedule, elapsed_s) if args.allow_actuation else ZERO_COMMAND
                command, observed_stop_latched = select_stm_command(
                    stm_source, requested, stm_stop_latched
                )
                if observed_stop_latched and not stm_stop_latched:
                    event("stm32_stop_flag", "STM stop flag observed before command selection", "stop")
                stm_stop_latched = observed_stop_latched
                stm_source.send_velocity(*command)
                command_timestamp = stm_source.last_command[0] if stm_source.last_command else utc_ns()
                if command_timestamp <= last_command_timestamp:
                    command_timestamp = last_command_timestamp + 1
                last_command_timestamp = command_timestamp
                telemetry = stm_source.latest
                writers.write(
                    "control.csv",
                    {
                        "t_ns": command_timestamp,
                        "vx_cmd_mps": command[0],
                        "vy_cmd_mps": command[1],
                        "wz_cmd_radps": command[2],
                        "vx_applied_mps": telemetry.vx_mps if telemetry is not None else "",
                        "vy_applied_mps": telemetry.vy_mps if telemetry is not None else "",
                        "wz_applied_radps": telemetry.wz_radps if telemetry is not None else "",
                        "sequence": "",
                        "transport": "stm32_serial",
                    },
                )
            frame = camera.read()
            frame_index += 1
            frame_name = f"frame-{frame_index:06d}-{frame.t_ns}.jpg"
            frame_file = frames_root / frame_name
            context_path = frames_root.name + "/" + frame_name
            record, detections = processor.process(frame, context_path)
            write_pose_overlay(frame.color_bgr, detections, record, frame_file)
            context_timestamp = record.t_ns
            if context_timestamp <= context_last:
                raise RuntimeError("camera timestamps are not strictly increasing")
            context_last = context_timestamp
            lidar_minimum, lidar_valid = latest_lidar_context(lidar.latest)
            writers.write(
                "context.csv",
                {
                    "t_ns": context_timestamp,
                    "position_x_m": record.position_x_m,
                    "position_y_m": record.position_y_m,
                    "speed_mps": record.speed_mps,
                    "direction": record.direction,
                    "confidence": record.confidence,
                    "context_valid": str(record.context_valid).lower(),
                    "lstm_active": str(record.lstm_active).lower(),
                    "lstm_configured": str(record.lstm_configured).lower(),
                    "frame_path": record.frame_path,
                    "camera_device_t_ns": record.camera_device_timestamp_ns or "",
                    "lidar_min_range_m": lidar_minimum,
                    "lidar_valid": str(lidar_valid).lower(),
                },
            )
            lidar_scan = lidar.latest
            if lidar_scan is not None and lidar_scan.t_ns > lidar_last:
                lidar_last = lidar_scan.t_ns
                points = [
                    [
                        float(point.angle_rad),
                        float(point.range_m),
                        int(point.intensity),
                        int(point.return_id),
                    ]
                    for point in lidar_scan.points
                ]
                writers.write(
                    "lidar.csv",
                    {
                        "t_ns": lidar_scan.t_ns,
                        "point_count": len(points),
                        "points_json": json.dumps(points, separators=(",", ":")),
                    },
                )
            snapshot = can_source.latest if can_source is not None else None
            if snapshot is not None and snapshot.status:
                status_key = (
                    snapshot.status.get("sequence"),
                    snapshot.status.get("status"),
                    snapshot.status.get("remaining_ticks"),
                )
                if status_key != status_seen:
                    status_seen = status_key
                    event(
                        "can_status",
                        json.dumps(snapshot.status, sort_keys=True),
                        str(snapshot.status.get("status", "")),
                    )
            if snapshot is not None and snapshot.external_faults not in (None, 0) and snapshot.external_faults != fault_seen:
                fault_seen = snapshot.external_faults
                event("external_fault", str(snapshot.external_faults), "fault")
            if snapshot is not None and snapshot.wheels and all(
                name in snapshot.wheels
                for name in ("wheel_fl_radps", "wheel_fr_radps", "wheel_rl_radps", "wheel_rr_radps")
            ):
                state_timestamp = snapshot.wheels_t_ns
                if state_timestamp > state_last:
                    state = estimator.step(state_timestamp, geometry.body_velocity(snapshot.wheels))
                    state_last = state_timestamp
                    vx, vy, wz = geometry.body_velocity(snapshot.wheels)
                    writers.write(
                        "robot_state.csv",
                        {
                            "t_ns": state_timestamp,
                            "x_m": state[0],
                            "y_m": state[1],
                            "yaw_rad": state[2],
                            "vx_mps": state[3],
                            "vy_mps": state[4],
                            "wz_radps": state[5],
                            "wheel_fl_radps": snapshot.wheels["wheel_fl_radps"],
                            "wheel_fr_radps": snapshot.wheels["wheel_fr_radps"],
                            "wheel_rl_radps": snapshot.wheels["wheel_rl_radps"],
                            "wheel_rr_radps": snapshot.wheels["wheel_rr_radps"],
                            "battery_mv": snapshot.battery_mv or "",
                            "pwm_mask": snapshot.pwm_mask or "",
                            "external_faults": snapshot.external_faults or "",
                            **estimator.diagnostics(),
                        },
                    )
            if stm_source is not None:
                telemetry = stm_source.latest
                if telemetry is not None and telemetry.t_ns > stm_state_last:
                    stm_state_last = telemetry.t_ns
                    velocity = (telemetry.vx_mps, telemetry.vy_mps, telemetry.wz_radps)
                    state = estimator.step(
                        telemetry.t_ns,
                        velocity,
                        acceleration_body_mps2=(
                            telemetry.accel_x_mps2,
                            telemetry.accel_y_mps2,
                        ),
                        gyro_z_radps=telemetry.gyro_z_radps,
                    )
                    writers.write(
                        "robot_state.csv",
                        {
                            "t_ns": telemetry.t_ns,
                            "x_m": state[0],
                            "y_m": state[1],
                            "yaw_rad": state[2],
                            "vx_mps": state[3],
                            "vy_mps": state[4],
                            "wz_radps": state[5],
                            "accel_x_mps2": telemetry.accel_x_mps2,
                            "accel_y_mps2": telemetry.accel_y_mps2,
                            "accel_z_mps2": telemetry.accel_z_mps2,
                            "gyro_x_radps": telemetry.gyro_x_radps,
                            "gyro_y_radps": telemetry.gyro_y_radps,
                            "gyro_z_radps": telemetry.gyro_z_radps,
                            "voltage_v": telemetry.voltage_v,
                            "flag_stop": telemetry.flag_stop,
                            **estimator.diagnostics(),
                            "transport": "stm32_serial",
                        },
                    )
                    if telemetry.flag_stop and not stm_stop_latched:
                        stm_stop_latched = True
                        event("stm32_stop_flag", str(telemetry.flag_stop), "stop")
            if snapshot is not None and snapshot.command and snapshot.applied:
                control_key = (
                    snapshot.command.get("sequence"),
                    snapshot.command.get("vx_mps"),
                    snapshot.command.get("vy_mps"),
                    snapshot.command.get("wz_radps"),
                    snapshot.command_t_ns,
                    snapshot.applied.get("sequence"),
                    snapshot.applied.get("vx_mps"),
                    snapshot.applied.get("vy_mps"),
                    snapshot.applied.get("wz_radps"),
                    snapshot.applied_t_ns,
                )
                if control_key == control_seen:
                    time.sleep(max(0.0, args.sample_period_s))
                    writers.flush()
                    continue
                control_seen = control_key
                control_timestamp = max(snapshot.command_t_ns, snapshot.applied_t_ns)
                if control_timestamp > control_last:
                    control_last = control_timestamp
                    writers.write(
                        "control.csv",
                        {
                            "t_ns": control_timestamp,
                            "vx_cmd_mps": snapshot.command["vx_mps"],
                            "vy_cmd_mps": snapshot.command["vy_mps"],
                            "wz_cmd_radps": snapshot.command["wz_radps"],
                            "vx_applied_mps": snapshot.applied["vx_mps"],
                            "vy_applied_mps": snapshot.applied["vy_mps"],
                            "wz_applied_radps": snapshot.applied["wz_radps"],
                            "sequence": snapshot.applied.get("sequence", ""),
                        },
                    )
            if online_controller is not None:
                try:
                    if stm_stop_latched:
                        next_command = ZERO_COMMAND
                        controller_details = {
                            "status": "STM_STOP_LATCHED",
                            "local_replanned": False,
                            "local_generation_count": online_controller.path.local_generation_count,
                        }
                    elif cca_stop_latched:
                        next_command = ZERO_COMMAND
                        controller_details = {
                            "status": "CCA_STOP_LATCHED",
                            "local_replanned": False,
                            "local_generation_count": online_controller.path.local_generation_count,
                        }
                    elif state_last <= 0:
                        next_command = ZERO_COMMAND
                        controller_details = {
                            "status": "STATE_WARMUP_STOP",
                            "local_replanned": False,
                            "local_generation_count": online_controller.path.local_generation_count,
                        }
                    else:
                        next_command, controller_details = online_controller.step(estimator.state, record)
                    event(
                        "cca_nmpc_step",
                        json.dumps(controller_details, sort_keys=True),
                        str(controller_details.get("status", "")),
                    )
                    if bool(controller_details.get("deadline_missed", False)):
                        next_command = ZERO_COMMAND
                        cca_stop_latched = True
                        event("cca_deadline_stop", "online CCA solve exceeded sample deadline", "stop")
                except Exception as error:
                    next_command = ZERO_COMMAND
                    if stm_source is not None:
                        stm_source.send_velocity(*ZERO_COMMAND)
                    event("cca_control_error", str(error), "error")
                    raise
            time.sleep(max(0.0, args.sample_period_s))
            writers.flush()
        event("capture_completed", f"frames={frame_index}", "completed")
    except KeyboardInterrupt:
        event("operator_stop", f"frames={frame_index}", "operator_stop")
    except Exception as error:
        event("capture_error", str(error), "error")
        raise
    finally:
        if stm_started and stm_source is not None:
            try:
                stm_source.send_velocity(*ZERO_COMMAND)
            except Exception:
                pass
            stm_source.stop()
        if can_started and can_source is not None:
            can_source.stop()
        if lidar_started:
            lidar.stop()
        if camera_started:
            camera.stop()
            refresh_camera_metadata()
        writers.close()
    return 0


def main() -> int:
    return run(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
