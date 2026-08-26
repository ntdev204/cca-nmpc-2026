from __future__ import annotations

import argparse
import csv
from collections import deque
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import time
from typing import Callable, Iterable

import matplotlib.pyplot as plt
import numpy as np
from jsonschema import Draft202012Validator, FormatChecker

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT

from ai.ctx_lstm import (
    DIRECTION_CLASSES,
    MAX_CONTEXT_SPEED_MPS,
    direction_context_to_heading_observation,
    load_context_lstm,
    require_fitted_calibration,
)
from ai.context import ContextConfig, context_score
from runtime.controller import NmpcPrediction
from runtime.controller import CompiledController
from runtime.local_path import (
    context_footprint_points,
    evaluate_context_replan,
    FixedGlobalLocalPath,
    generate_context_local_detour,
    path_clearance_to_footprint,
)
from simulations.python.model import (
    POSITION_COMMAND_FIELDS,
    POSITION_CONTROL_INTERFACE,
    POSITION_CONTROL_MODE,
    POSITION_STATE_FIELDS,
    position_step,
)
from shared import CONTRACT_PATH, load_contract, validate_capture_calibration

CONTRACT = load_contract()
MAP_CONTRACT = CONTRACT["map"]
PROTOCOL_FREEZE_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "protocol-freeze-manifest.schema.json"


@dataclass(frozen=True)
class ContextPolicyParameters:
    safe_distance_m: float = float(MAP_CONTRACT["safe_clearance_m"])
    lateral_offset_m: float = float(MAP_CONTRACT["lateral_offset_m"])
    longitudinal_offset_m: float = float(MAP_CONTRACT["longitudinal_offset_m"])
    context_radius_m: float = float(MAP_CONTRACT["context_radius_m"])

    def __post_init__(self) -> None:
        if not 0.0 <= self.safe_distance_m <= 1.0:
            raise ValueError("safe_distance_m must lie in [0, 1]")
        if not 0.5 <= self.lateral_offset_m <= 2.5:
            raise ValueError("lateral_offset_m must lie in [0.5, 2.5]")
        if not 0.3 <= self.longitudinal_offset_m <= 1.8:
            raise ValueError("longitudinal_offset_m must lie in [0.3, 1.8]")
        if not 0.3 <= self.context_radius_m <= 1.2:
            raise ValueError("context_radius_m must lie in [0.3, 1.2]")

    def as_dict(self) -> dict[str, float]:
        return {key: float(value) for key, value in asdict(self).items()}


def outcome_score(summary: dict[str, object]) -> float:
    if bool(summary.get("collision", False)):
        return 0.0
    safe = 1.0 if bool(summary.get("safe_completion", False)) else 0.0
    margin = float(summary.get("minimum_context_margin_m", -1.0))
    goal_error = float(summary.get("final_goal_error_m", 10.0))
    failures = float(summary.get("controller_failure_count", 0.0))
    deadline_misses = float(summary.get("deadline_miss_count", 0.0))
    margin_score = float(np.clip((margin + 0.10) / 0.60, 0.0, 1.0))
    progress_score = float(np.exp(-max(0.0, goal_error)))
    penalty = min(1.0, 0.12 * failures + 0.20 * deadline_misses)
    return float(np.clip(0.55 * safe + 0.25 * margin_score + 0.20 * progress_score - penalty, 0.0, 1.0))


def load_protocol_freeze(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(PROTOCOL_FREEZE_SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(payload),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise ValueError(f"invalid protocol-freeze manifest: {errors[0].message}")
    protocol_ids = {
        str(item["protocol_id"])
        for item in payload["protocols"]
        if isinstance(item, dict) and "protocol_id" in item
    }
    if not {"PR20", "PR21"}.issubset(protocol_ids):
        raise ValueError("protocol-freeze manifest must include PR20 and PR21")
    return payload


@dataclass(frozen=True)
class ScoreSearchResult:
    best_parameters: ContextPolicyParameters
    best_score: float
    iterations: tuple[dict[str, object], ...]
    stop_reason: str
    target_reached: bool


def score_policy_search(
    candidates: Iterable[ContextPolicyParameters],
    evaluate: Callable[[ContextPolicyParameters], Iterable[dict[str, object]]],
    *,
    target_score: float = float(MAP_CONTRACT["score_target"]),
    patience: int = int(MAP_CONTRACT["score_patience"]),
) -> ScoreSearchResult:
    if not 0.0 < target_score <= 1.0:
        raise ValueError("target_score must lie in (0, 1]")
    if patience < 1:
        raise ValueError("patience must be positive")
    iterator = iter(candidates)
    try:
        first = next(iterator)
    except StopIteration as error:
        raise ValueError("at least one policy candidate is required") from error
    best = first
    best_score = -1.0
    stale = 0
    rows: list[dict[str, object]] = []
    stop_reason = "candidate_exhausted"
    for iteration, parameters in enumerate((first, *iterator), start=1):
        outcomes = list(evaluate(parameters))
        if not outcomes:
            raise ValueError("policy evaluation returned no episode outcomes")
        scores = [outcome_score(outcome) for outcome in outcomes]
        mean_score = float(np.mean(scores))
        row = {
            "iteration": iteration,
            "parameters": parameters.as_dict(),
            "episode_count": len(outcomes),
            "score": mean_score,
            "score_min": float(np.min(scores)),
            "score_max": float(np.max(scores)),
            "collision_count": int(sum(bool(item.get("collision", False)) for item in outcomes)),
            "training_targets_used": False,
        }
        rows.append(row)
        if mean_score > best_score + 1.0e-12:
            best = parameters
            best_score = mean_score
            stale = 0
        else:
            stale += 1
        if mean_score >= target_score:
            stop_reason = "score_target_reached"
            break
        if stale >= patience:
            stop_reason = "score_plateau"
            break
    return ScoreSearchResult(
        best_parameters=best,
        best_score=float(best_score),
        iterations=tuple(rows),
        stop_reason=stop_reason,
        target_reached=bool(best_score >= target_score),
    )


DT_S = float(MAP_CONTRACT["dt_s"])
DEADLINE_MS = 1000.0 * DT_S
ROBOT_RADIUS_M = float(MAP_CONTRACT["robot_radius_m"])
ROBOT_GEOMETRY = dict(MAP_CONTRACT["robot_geometry"])
HUMAN_RADIUS_M = float(MAP_CONTRACT.get("human_radius_m", 0.34))
CONTEXT_RADIUS_M = float(MAP_CONTRACT["context_radius_m"])
CONTEXT_SCORE_CONFIG = ContextConfig()
SAFE_CONTEXT_CLEARANCE_M = float(MAP_CONTRACT["safe_clearance_m"])
CRUISE_SPEED_MPS = float(MAP_CONTRACT["cruise_speed_mps"])
LOCAL_LATERAL_OFFSET_M = float(MAP_CONTRACT["lateral_offset_m"])
LOCAL_LONGITUDINAL_OFFSET_M = float(MAP_CONTRACT["longitudinal_offset_m"])
SOURCE_SEED = b"cca-context-only-map-benchmark-v2"
SOURCE_SHA256 = hashlib.sha256(SOURCE_SEED).hexdigest()
CONTROLLERS = tuple(str(item) for item in MAP_CONTRACT["controllers"])
CONFIRMATORY_CAPTURE_SOURCES = {"hardware", "hardware_in_loop", "real_offline"}
BOOTSTRAP_REPLICATES = 400
BOOTSTRAP_SEED = int(MAP_CONTRACT["seed"]) + 17
CONFIDENCE_LEVEL = 0.95
NEAR_MISS_MARGIN_M = 0.10
CONTROLLER_DEFINITIONS = {
    "mpc": {
        "implementation": "compiled::mpc",
        "control_domain": "body_velocity",
        "context_used": False,
        "risk_strategy": "none",
    },
    "nmpc": {
        "implementation": "compiled::nmpc",
        "control_domain": "body_velocity",
        "context_used": False,
        "risk_strategy": "deterministic",
    },
    "dwa": {
        "implementation": "compiled::dwa",
        "control_domain": "sampled_body_velocity",
        "context_used": True,
        "risk_strategy": "local_path_clearance",
    },
    "mppi": {
        "implementation": "compiled::mppi",
        "control_domain": "sampled_body_velocity",
        "context_used": True,
        "risk_strategy": "local_path_clearance",
    },
    "cca_nmpc": {
        "implementation": "compiled::cca_nmpc",
        "control_domain": "body_velocity",
        "context_used": True,
        "risk_strategy": "cca_fixed_budget",
    },
}
PLOT_COLORS = ("#52a7ff", "#ff5bd7", "#61e294", "#ff9f43", "#ffc857")
DEFAULT_POLICY = ContextPolicyParameters(
    safe_distance_m=SAFE_CONTEXT_CLEARANCE_M,
    lateral_offset_m=LOCAL_LATERAL_OFFSET_M,
    longitudinal_offset_m=LOCAL_LONGITUDINAL_OFFSET_M,
    context_radius_m=CONTEXT_RADIUS_M,
)


@dataclass(frozen=True)
class ContextEvent:
    start_time_s: float
    direction: str
    speed_mps: float

    def __post_init__(self) -> None:
        if self.direction not in DIRECTION_CLASSES:
            raise ValueError(f"unsupported direction: {self.direction}")
        if self.start_time_s < 0.0 or self.speed_mps < 0.0:
            raise ValueError("context event values must be nonnegative")


@dataclass(frozen=True)
class MapScenario:
    scenario_id: str
    duration_s: float
    start_xy: tuple[float, float]
    goal_xy: tuple[float, float]
    person_position_xy: tuple[float, float]
    context_events: tuple[ContextEvent, ...]

    def context_at(self, time_s: float) -> ContextEvent:
        active = self.context_events[0]
        for event in self.context_events:
            if time_s >= event.start_time_s:
                active = event
            else:
                break
        return active

    def person_position_at(self, time_s: float) -> np.ndarray:
        if not np.isfinite(time_s) or time_s < 0.0:
            raise ValueError("time_s must be finite and nonnegative")
        position = np.asarray(self.person_position_xy, dtype=np.float64).copy()
        direction_unit = {
            "left": np.asarray((-1.0, 0.0), dtype=np.float64),
            "right": np.asarray((1.0, 0.0), dtype=np.float64),
            "forward": np.asarray((0.0, 1.0), dtype=np.float64),
            "backward": np.asarray((0.0, -1.0), dtype=np.float64),
        }
        for index, event in enumerate(self.context_events):
            segment_start = float(event.start_time_s)
            segment_end = (
                float(self.context_events[index + 1].start_time_s)
                if index + 1 < len(self.context_events)
                else float(time_s)
            )
            duration = max(0.0, min(float(time_s), segment_end) - segment_start)
            if duration > 0.0:
                position += direction_unit[event.direction] * event.speed_mps * duration
            if time_s <= segment_end:
                break
        return position


SCENARIOS = (
    MapScenario(
        "dynamic_person_lateral_left_to_right",
        18.0,
        (0.0, 0.0),
        (10.0, 0.0),
        (5.0, 0.0),
        (ContextEvent(0.0, "left", 0.35), ContextEvent(5.0, "right", 0.35)),
    ),
    MapScenario(
        "dynamic_person_lateral_right_to_left",
        18.0,
        (0.0, 0.0),
        (10.0, 0.0),
        (5.0, 0.0),
        (ContextEvent(0.0, "right", 0.35), ContextEvent(5.0, "left", 0.35)),
    ),
    MapScenario(
        "dynamic_person_forward_to_backward",
        18.0,
        (0.0, 0.0),
        (10.0, 0.0),
        (5.0, 0.0),
        (ContextEvent(0.0, "forward", 0.25), ContextEvent(5.0, "backward", 0.25)),
    ),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_robot_geometry_contract() -> dict[str, object]:
    geometry = ROBOT_GEOMETRY
    source_value = geometry.get("source_urdf")
    source_hash = geometry.get("source_urdf_sha256")
    intake_value = geometry.get("source_intake")
    intake_hash = geometry.get("source_intake_sha256")
    footprint_radius = geometry.get("footprint_radius_m")
    half_extents = geometry.get("footprint_half_extents_m")
    if not isinstance(source_value, str) or not source_value.strip():
        raise ValueError("robot geometry must declare a source URDF")
    if not isinstance(source_hash, str) or len(source_hash) != 64:
        raise ValueError("robot geometry must declare a SHA-256 source hash")
    if not isinstance(intake_value, str) or not intake_value.strip():
        raise ValueError("robot geometry must declare a hardware intake")
    if not isinstance(intake_hash, str) or len(intake_hash) != 64:
        raise ValueError("robot geometry must declare a hardware intake hash")
    try:
        int(source_hash, 16)
        int(intake_hash, 16)
    except ValueError as error:
        raise ValueError("robot geometry source hash is not SHA-256") from error
    source_path = (PROJECT_ROOT / Path(source_value)).resolve()
    try:
        source_path.relative_to(PROJECT_ROOT)
    except ValueError as error:
        raise ValueError("robot geometry source URDF escapes the project root") from error
    if not source_path.is_file():
        raise ValueError("robot geometry source URDF does not exist")
    if sha256_file(source_path) != source_hash:
        raise ValueError("robot geometry source URDF hash does not match the contract")
    intake_path = (PROJECT_ROOT / Path(intake_value)).resolve()
    try:
        intake_path.relative_to(PROJECT_ROOT)
    except ValueError as error:
        raise ValueError("robot geometry intake escapes the project root") from error
    if not intake_path.is_file() or sha256_file(intake_path) != intake_hash:
        raise ValueError("robot geometry hardware intake hash does not match the file")
    try:
        intake = json.loads(intake_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("robot geometry hardware intake is not valid JSON") from error
    intake_robot = intake.get("robot") if isinstance(intake, dict) else None
    intake_footprint = intake_robot.get("footprint") if isinstance(intake_robot, dict) else None
    if not isinstance(intake_robot, dict) or intake_robot.get("model") != geometry.get("model"):
        raise ValueError("robot geometry hardware intake model does not match the contract")
    if intake_robot.get("urdf_sha256") != source_hash:
        raise ValueError("robot geometry hardware intake URDF hash does not match the contract")
    if not isinstance(intake_footprint, dict):
        raise ValueError("robot geometry hardware intake lacks the footprint record")
    if not isinstance(footprint_radius, (int, float)) or not np.isfinite(float(footprint_radius)):
        raise ValueError("robot geometry footprint radius must be finite")
    if not np.isclose(ROBOT_RADIUS_M, float(footprint_radius), rtol=0.0, atol=1.0e-12):
        raise ValueError("map robot radius does not match the contract footprint radius")
    extents = np.asarray(half_extents, dtype=np.float64)
    if extents.shape != (2,) or not np.isfinite(extents).all() or np.any(extents <= 0.0):
        raise ValueError("robot geometry footprint half extents are invalid")
    intake_extents = np.asarray(intake_footprint.get("half_extents_m"), dtype=np.float64)
    intake_radius = intake_footprint.get("footprint_radius_m")
    if (
        intake_extents.shape != (2,)
        or not np.isfinite(intake_extents).all()
        or not isinstance(intake_radius, (int, float))
    ):
        raise ValueError("robot geometry reference intake footprint is invalid")
    physical_value = geometry.get("source_physical_spec")
    physical_hash = geometry.get("source_physical_spec_sha256")
    if not isinstance(physical_value, str) or not physical_value.strip():
        raise ValueError("robot geometry must declare a measured physical specification")
    if not isinstance(physical_hash, str) or len(physical_hash) != 64:
        raise ValueError("robot geometry physical specification must declare a SHA-256 hash")
    try:
        int(physical_hash, 16)
    except ValueError as error:
        raise ValueError("robot geometry physical specification hash is not SHA-256") from error
    physical_path = (PROJECT_ROOT / Path(physical_value)).resolve()
    try:
        physical_path.relative_to(PROJECT_ROOT)
    except ValueError as error:
        raise ValueError("robot geometry physical specification escapes the project root") from error
    if not physical_path.is_file() or sha256_file(physical_path) != physical_hash:
        raise ValueError("robot geometry physical specification hash does not match the file")
    try:
        physical = json.loads(physical_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("robot geometry physical specification is not valid JSON") from error
    if (
        physical.get("schema") != "cca-physical-robot-v1"
        or physical.get("status") != "measured"
        or physical.get("robot_model") != geometry.get("model")
    ):
        raise ValueError("robot geometry physical specification identity is invalid")
    physical_extents = np.asarray(
        (physical.get("half_length_m"), physical.get("half_width_m")),
        dtype=np.float64,
    )
    physical_radius = physical.get("footprint_radius_m")
    if (
        physical_extents.shape != (2,)
        or not np.isfinite(physical_extents).all()
        or np.any(physical_extents <= 0.0)
        or not isinstance(physical_radius, (int, float))
        or not np.isclose(float(physical_radius), float(footprint_radius), rtol=0.0, atol=1.0e-12)
        or not np.allclose(physical_extents, extents, rtol=0.0, atol=1.0e-12)
    ):
        raise ValueError("robot geometry does not match the measured physical specification")
    return geometry


validate_robot_geometry_contract()


def dense_polyline(path_xy: np.ndarray, spacing_m: float = 0.05) -> np.ndarray:
    path = np.asarray(path_xy, dtype=np.float64)
    points = [path[0]]
    for start, end in zip(path[:-1], path[1:], strict=True):
        delta = end - start
        length = float(np.linalg.norm(delta))
        count = max(1, int(np.ceil(length / spacing_m)))
        points.extend(start + delta * fraction for fraction in np.linspace(0.0, 1.0, count + 1)[1:])
    return np.asarray(points, dtype=np.float64)


def path_distance(position_xy: np.ndarray, path_xy: np.ndarray) -> float:
    path = np.asarray(path_xy, dtype=np.float64)
    segments = np.diff(path, axis=0)
    lengths = np.linalg.norm(segments, axis=1)
    fractions = np.divide(
        np.sum((position_xy[None] - path[:-1]) * segments, axis=1),
        lengths**2,
        out=np.zeros_like(lengths),
        where=lengths > 1.0e-12,
    )
    fractions = np.clip(fractions, 0.0, 1.0)
    projections = path[:-1] + fractions[:, None] * segments
    index = int(np.argmin(np.linalg.norm(projections - position_xy[None], axis=1)))
    cumulative = np.concatenate(([0.0], np.cumsum(lengths)))
    return float(cumulative[index] + fractions[index] * lengths[index])


def path_cross_track_error(position_xy: np.ndarray, path_xy: np.ndarray) -> float:
    path = np.asarray(path_xy, dtype=np.float64)
    if path.ndim != 2 or path.shape[0] < 2 or path.shape[1] != 2:
        raise ValueError("path must contain at least two two-dimensional points")
    segments = np.diff(path, axis=0)
    lengths_sq = np.sum(segments * segments, axis=1)
    fractions = np.divide(
        np.sum((np.asarray(position_xy, dtype=np.float64)[None] - path[:-1]) * segments, axis=1),
        lengths_sq,
        out=np.zeros_like(lengths_sq),
        where=lengths_sq > 1.0e-12,
    )
    fractions = np.clip(fractions, 0.0, 1.0)
    projections = path[:-1] + fractions[:, None] * segments
    return float(np.min(np.linalg.norm(projections - np.asarray(position_xy)[None], axis=1)))


def sample_polyline(path_xy: np.ndarray, distance_m: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    path = np.asarray(path_xy, dtype=np.float64)
    distance = np.asarray(distance_m, dtype=np.float64)
    segments = np.diff(path, axis=0)
    lengths = np.linalg.norm(segments, axis=1)
    cumulative = np.concatenate(([0.0], np.cumsum(lengths)))
    clipped = np.clip(distance, 0.0, cumulative[-1])
    indices = np.clip(np.searchsorted(cumulative, clipped, side="right") - 1, 0, len(segments) - 1)
    fractions = np.divide(clipped - cumulative[indices], lengths[indices], out=np.zeros_like(clipped), where=lengths[indices] > 1.0e-12)
    positions = path[indices] + fractions[:, None] * segments[indices]
    tangent = segments[indices] / np.maximum(lengths[indices, None], 1.0e-12)
    return positions, tangent


def reference_horizon(position_xy: np.ndarray, path_xy: np.ndarray, horizon: int) -> np.ndarray:
    progress = path_distance(position_xy, path_xy)
    distances = progress + CRUISE_SPEED_MPS * np.arange(horizon + 1) * DT_S
    position, tangent = sample_polyline(path_xy, distances)
    yaw = np.unwrap(np.arctan2(tangent[:, 1], tangent[:, 0]))
    reference = np.zeros((6, horizon + 1), dtype=np.float64)
    reference[:2] = position.T
    reference[2] = yaw
    world_ref = CRUISE_SPEED_MPS * tangent
    for index, yaw_value in enumerate(yaw):
        rotation_transpose = np.asarray(((np.cos(yaw_value), np.sin(yaw_value)), (-np.sin(yaw_value), np.cos(yaw_value))))
        reference[3:5, index] = rotation_transpose @ world_ref[index]
    return reference


def context_observation(scenario: MapScenario, time_s: float) -> object:
    event = scenario.context_at(time_s)
    return direction_context_to_heading_observation(
        event.direction,
        position_xy=scenario.person_position_at(time_s),
        speed_mps=event.speed_mps,
        direction_confidence=0.95,
        timestamp_ns=int(round(time_s * 1.0e9)),
        frame_id=f"map-{scenario.scenario_id}-{int(round(time_s / DT_S)):04d}",
        track_id=0,
        source_sha256=SOURCE_SHA256,
        coordinate_units="map_m",
    )


class ContextLstmAdapter:
    def __init__(self, checkpoint_path: Path) -> None:
        self.model, self.metadata = load_context_lstm(checkpoint_path)
        if self.model.config.input_size != 5:
            raise ValueError("map-runner LSTM interface requires five context features")
        self.observed_steps = int(CONTRACT["context"]["observed_steps"])
        if self.observed_steps < 1:
            raise ValueError("observed_steps must be positive")
        self.history: deque[np.ndarray] = deque(maxlen=self.observed_steps)
        self.checkpoint_path = Path(checkpoint_path).resolve()

    def reset(self) -> None:
        self.history.clear()

    def observe(self, observation: object) -> np.ndarray | None:
        heading = np.asarray(observation.heading_unit, dtype=np.float32)
        velocity = heading * float(observation.speed_per_s)
        self.history.append(
            np.asarray(
                (
                    float(observation.position_xy[0]),
                    float(observation.position_xy[1]),
                    float(velocity[0]),
                    float(velocity[1]),
                    1.0 if bool(observation.heading_valid) else 0.0,
                ),
                dtype=np.float32,
            )
        )
        if len(self.history) < self.observed_steps:
            return None
        raw = np.stack(tuple(self.history), axis=0)
        relative = raw[:, :2] - raw[-1:, :2]
        history = np.concatenate((relative, raw[:, 2:]), axis=1)[None]
        import torch

        with torch.no_grad():
            prediction = self.model(torch.from_numpy(history))
        velocity_xy = prediction.context_velocity_xy[0].detach().cpu().numpy()
        if velocity_xy.shape != (2,) or not np.isfinite(velocity_xy).all():
            raise ValueError("LSTM context velocity is invalid")
        if float(np.linalg.norm(velocity_xy)) > MAX_CONTEXT_SPEED_MPS:
            return None
        return np.asarray(velocity_xy, dtype=np.float64)


def validate_confirmatory_lstm_provenance(metadata: dict[str, object]) -> dict[str, str]:
    """Require a checkpoint tied to a sealed real context capture."""
    source = metadata.get("source_capture")
    manifest_sha256 = metadata.get("source_capture_manifest_sha256")
    manifest_path_value = metadata.get("source_capture_manifest_path")
    checkpoint_calibration_sha256 = metadata.get("source_calibration_sha256")
    if source not in CONFIRMATORY_CAPTURE_SOURCES:
        raise ValueError("confirmatory LSTM checkpoint lacks a real capture source")
    if not isinstance(manifest_sha256, str) or len(manifest_sha256) != 64:
        raise ValueError("confirmatory LSTM checkpoint lacks a capture manifest hash")
    if not isinstance(manifest_path_value, str) or not manifest_path_value.strip():
        raise ValueError("confirmatory LSTM checkpoint lacks a capture manifest path")
    if not isinstance(checkpoint_calibration_sha256, str) or len(checkpoint_calibration_sha256) != 64:
        raise ValueError("confirmatory LSTM checkpoint lacks a calibration hash")
    try:
        int(manifest_sha256, 16)
    except ValueError as error:
        raise ValueError("confirmatory LSTM capture manifest hash is not SHA-256") from error
    manifest_path = (PROJECT_ROOT / Path(manifest_path_value)).resolve()
    try:
        manifest_path.relative_to(PROJECT_ROOT)
    except ValueError as error:
        raise ValueError("confirmatory LSTM capture manifest path escapes the project root") from error
    if not manifest_path.is_file():
        raise ValueError("confirmatory LSTM capture manifest does not exist")
    if sha256_file(manifest_path) != manifest_sha256:
        raise ValueError("confirmatory LSTM capture manifest hash does not match the file")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("confirmatory LSTM capture manifest is not valid JSON") from error
    if not isinstance(payload, dict):
        raise ValueError("confirmatory LSTM capture manifest must be an object")
    if (
        payload.get("status") != "verified"
        or payload.get("integrity_status") != "verified"
        or payload.get("capture_source") != source
        or payload.get("context_only") is not True
        or payload.get("human_trajectory_generated") is not False
    ):
        raise ValueError("confirmatory LSTM capture manifest has invalid provenance flags")
    calibration_record = payload.get("calibration")
    files = payload.get("files")
    if not isinstance(calibration_record, dict) or calibration_record.get("path") != "calibration.json":
        raise ValueError("confirmatory LSTM capture manifest lacks calibration provenance")
    calibration_path = manifest_path.parent / "calibration.json"
    calibration_file_record = files.get("calibration.json") if isinstance(files, dict) else None
    calibration_sha256 = str(calibration_file_record.get("sha256", "")) if isinstance(calibration_file_record, dict) else ""
    if not calibration_path.is_file() or len(calibration_sha256) != 64:
        raise ValueError("confirmatory LSTM capture manifest lacks calibration.json")
    if checkpoint_calibration_sha256 != calibration_sha256:
        raise ValueError("confirmatory LSTM calibration hash does not match checkpoint metadata")
    if calibration_sha256 != sha256_file(calibration_path) or calibration_sha256 != calibration_record.get("sha256"):
        raise ValueError("confirmatory LSTM calibration hash does not match the file")
    try:
        calibration_payload = json.loads(calibration_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("confirmatory LSTM calibration.json is not valid JSON") from error
    sensors = payload.get("sensors")
    validate_capture_calibration(
        calibration_payload,
        camera=sensors.get("camera") if isinstance(sensors, dict) else None,
        lidar=sensors.get("lidar") if isinstance(sensors, dict) else None,
    )
    return {
        "capture_source": source,
        "capture_manifest_sha256": manifest_sha256,
        "capture_manifest_path": manifest_path.relative_to(PROJECT_ROOT).as_posix(),
        "calibration_sha256": calibration_sha256,
    }


def context_obstacle(observation: object, policy: ContextPolicyParameters) -> np.ndarray:
    footprint = context_footprint_points(
        observation,
        lateral_radius_m=policy.context_radius_m,
        longitudinal_radius_m=policy.context_radius_m,
    )
    lower = footprint.min(axis=0)
    upper = footprint.max(axis=0)
    center = 0.5 * (lower + upper)
    half = 0.5 * (upper - lower)
    return np.asarray([[center[0], center[1], half[0], half[1]]], dtype=np.float64)


def context_prediction(
    observation: object,
    reference: np.ndarray,
    state: np.ndarray,
    horizon: int,
    predicted_velocity_xy: np.ndarray | None = None,
) -> NmpcPrediction:
    """Build CCA's internal one-mode future-position prediction from context velocity."""

    person = np.asarray(observation.position_xy, dtype=np.float64)
    if predicted_velocity_xy is None:
        human_velocity = np.asarray(observation.heading_unit, dtype=np.float64)
        human_velocity = human_velocity * float(observation.speed_per_s)
    else:
        human_velocity = np.asarray(predicted_velocity_xy, dtype=np.float64)
        if human_velocity.shape != (2,) or not np.isfinite(human_velocity).all():
            raise ValueError("predicted_velocity_xy must contain two finite values")
    step_times = float(CONTRACT["context"]["dt_s"]) * np.arange(1, horizon + 1, dtype=np.float64)
    mean_xy = person[None, None, None, :] + step_times[None, None, :, None] * human_velocity[None, None, None, :]
    velocity_xy = np.repeat(human_velocity[None, None, None, :], horizon, axis=2)
    covariance_xy = np.zeros((1, 1, horizon, 2, 2), dtype=np.float64)
    covariance_xy[..., 0, 0] = 0.04**2
    covariance_xy[..., 1, 1] = 0.04**2
    nominal_robot_xy = np.asarray(reference[:2, 1:].T, dtype=np.float64)
    if nominal_robot_xy.shape != (horizon, 2):
        raise ValueError("reference horizon does not match CCA prediction")
    robot_world_velocity = np.zeros((horizon, 2), dtype=np.float64)
    yaw = np.asarray(reference[2, 1:], dtype=np.float64)
    robot_world_velocity[:, 0] = np.cos(yaw) * reference[3, 1:] - np.sin(yaw) * reference[4, 1:]
    robot_world_velocity[:, 1] = np.sin(yaw) * reference[3, 1:] + np.cos(yaw) * reference[4, 1:]
    relative_velocity = human_velocity[None, :] - robot_world_velocity
    relative_position = person[None, :] - nominal_robot_xy
    scores = []
    for index in range(horizon):
        scores.append(
            context_score(
                relative_position[index],
                relative_velocity[index],
                robot_world_velocity[index],
                human_velocity,
                0.0,
                CONTEXT_SCORE_CONFIG,
            )
        )
    context = np.asarray(scores, dtype=np.float64)[None, :]
    human_yaw = np.full((1, horizon), float(np.arctan2(human_velocity[1], human_velocity[0])))
    return NmpcPrediction(
        mean_xy=mean_xy,
        velocity_xy=velocity_xy,
        relative_covariance_xy=covariance_xy,
        probability=np.ones((1, 1), dtype=np.float64),
        context=context,
        nominal_robot_xy=nominal_robot_xy,
        human_yaw_rad=human_yaw,
    )


def choose_local_path(
    robot_position: np.ndarray,
    goal: np.ndarray,
    observation: object,
    policy: ContextPolicyParameters,
) -> tuple[int, np.ndarray]:
    footprint = context_footprint_points(
        observation,
        lateral_radius_m=policy.context_radius_m,
        longitudinal_radius_m=policy.context_radius_m,
    )
    candidates = [
        generate_context_local_detour(
            robot_position,
            goal,
            observation,
            side=side,
            lateral_offset_m=policy.lateral_offset_m,
            longitudinal_offset_m=policy.longitudinal_offset_m,
        )
        for side in (-1, 1)
    ]
    ranked = [
        (path_clearance_to_footprint(candidate, footprint), float(np.linalg.norm(np.diff(candidate, axis=0), axis=1).sum()), side, candidate)
        for side, candidate in zip((-1, 1), candidates, strict=True)
    ]
    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    return int(ranked[0][2]), ranked[0][3]


def controller_for_path(method: str, path_xy: np.ndarray, seed: int, horizon: int) -> object:
    del path_xy, seed
    if method not in {"mpc", "nmpc", "dwa", "mppi", "cca_nmpc"}:
        raise ValueError(f"unsupported controller: {method}")
    return CompiledController(method, DT_S, horizon, DEADLINE_MS, ROBOT_RADIUS_M, HUMAN_RADIUS_M)


def body_velocity_command(state: np.ndarray, world_velocity: np.ndarray, yaw_rate: float) -> np.ndarray:
    yaw = float(state[2])
    cosine = float(np.cos(yaw))
    sine = float(np.sin(yaw))
    world = np.asarray(world_velocity, dtype=np.float64)
    return np.asarray(
        (cosine * world[0] + sine * world[1], -sine * world[0] + cosine * world[1], yaw_rate),
        dtype=np.float64,
    )


def advance_robot(state: np.ndarray, command: np.ndarray) -> np.ndarray:
    return position_step(state, command, DT_S)


def run_episode(
    scenario: MapScenario,
    method: str,
    seed: int,
    horizon: int,
    policy: ContextPolicyParameters = DEFAULT_POLICY,
    replicate: int = 0,
    context_lstm: ContextLstmAdapter | None = None,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    rng = np.random.default_rng(seed)
    global_path = np.asarray((scenario.start_xy, scenario.goal_xy), dtype=np.float64)
    path_state = FixedGlobalLocalPath.from_global(global_path)
    controller = controller_for_path(method, path_state.local_path_xy, seed, horizon)
    if hasattr(controller, "reset"):
        controller.reset()
    uses_internal_prediction = method == "cca_nmpc" and context_lstm is not None
    if uses_internal_prediction:
        context_lstm.reset()
    state = np.zeros(6, dtype=np.float64)
    state[:2] = global_path[0]
    previous_command = np.zeros(3, dtype=np.float64)
    previous_heading: np.ndarray | None = None
    previous_direction: str | None = None
    rows: list[dict[str, object]] = []
    min_margin = float("inf")
    local_replans = 0
    collisions = 0
    controller_failures = 0
    deadline_misses = 0
    risk_bounds: list[float] = []
    risk_slacks: list[float] = []
    solver_iterations: list[int] = []
    chance_relaxations: list[float] = []
    constraint_violations: list[float] = []
    timings: list[float] = []
    path_tracking_errors: list[float] = []
    yaw_tracking_errors: list[float] = []
    command_variations: list[float] = []
    path_length_m = 0.0
    near_miss_count = 0
    fallback_steps = 0
    previous_position = state[:2].copy()
    times = np.arange(0.0, scenario.duration_s + 0.5 * DT_S, DT_S)
    for step, time_s in enumerate(times):
        observation = context_observation(scenario, float(time_s))
        person_position = np.asarray(observation.position_xy, dtype=np.float64)
        predicted_velocity_xy = context_lstm.observe(observation) if uses_internal_prediction else None
        decision = evaluate_context_replan(
            path_state.local_path_xy,
            observation,
            now_ns=observation.timestamp_ns,
            previous_heading_unit=previous_heading,
            safe_distance_m=policy.safe_distance_m,
            heading_change_threshold_rad=0.60,
        )
        first_conflict = path_state.local_generation_count == 0 and "context_conflict" in decision.reasons
        direction_change = path_state.local_generation_count > 0 and "direction_change" in decision.reasons
        did_replan = False
        selected_side: int | None = None
        if decision.replan and (first_conflict or direction_change):
            selected_side, candidate = choose_local_path(
                state[:2], global_path[-1], observation, policy
            )
            path_state = FixedGlobalLocalPath(
                global_path_xy=path_state.global_path_xy,
                local_path_xy=candidate,
                local_generation_count=path_state.local_generation_count + 1,
            )
            if not np.array_equal(path_state.global_path_xy, global_path):
                raise AssertionError("global path changed during context local replacement")
            if method in {"dwa", "mppi"}:
                controller = controller_for_path(method, path_state.local_path_xy, seed + step, horizon)
            did_replan = True
            local_replans += 1
        previous_heading = observation.heading_unit.copy()
        previous_direction = scenario.context_at(float(time_s)).direction
        estimated = state.copy()
        estimated[:2] += rng.normal(0.0, 0.004, size=2)
        reference = reference_horizon(estimated[:2], path_state.local_path_xy, horizon)
        obstacle = context_obstacle(observation, policy)
        start_ns = time.perf_counter_ns()
        success = True
        fallback = False
        status = ""
        if method == "mpc":
            result = controller.command(estimated, reference, previous_command, obstacles=obstacle)
            command = result.first_command_mps
            status = result.status
            timings.append(float(result.solve_time_ms))
            deadline_misses += int(result.deadline_missed)
            constraint_violations.append(float(result.maximum_constraint_violation))
        elif method in {"nmpc", "cca_nmpc"}:
            prediction = (
                context_prediction(
                    observation,
                    reference,
                    estimated,
                    horizon,
                    predicted_velocity_xy=predicted_velocity_xy,
                )
                if method == "cca_nmpc"
                else None
            )
            result = controller.command(
                estimated,
                reference,
                previous_command,
                prediction,
                obstacles=obstacle,
            )
            command = result.first_command_mps
            status = result.status
            timings.append(float(result.solve_time_ms))
            deadline_misses += int(result.deadline_missed)
            risk_bounds.append(float(result.risk_bound))
            risk_slacks.append(float(result.maximum_risk_slack_m))
            solver_iterations.append(int(result.iterations))
            chance_relaxations.append(0.0)
            constraint_violations.append(float(result.maximum_constraint_violation))
        else:
            result = controller.command(estimated, reference, previous_command, obstacles=obstacle)
            command = result.first_command_mps
            success = True
            fallback = False
            status = result.status
        elapsed_ms = (time.perf_counter_ns() - start_ns) * 1.0e-6
        if method not in {"mpc", "nmpc", "cca_nmpc"}:
            timings.append(float(elapsed_ms))
        controller_failures += int(not success)
        fallback_steps += int(fallback)
        state = advance_robot(state, command)
        path_length_m += float(np.linalg.norm(state[:2] - previous_position))
        previous_position = state[:2].copy()
        static_distance = float(np.linalg.norm(state[:2] - person_position))
        margin = static_distance - (ROBOT_RADIUS_M + policy.context_radius_m)
        min_margin = min(min_margin, margin)
        collisions += int(margin < 0.0)
        near_miss_count += int(0.0 <= margin < NEAR_MISS_MARGIN_M)
        goal_error = float(np.linalg.norm(state[:2] - global_path[-1]))
        path_error = path_cross_track_error(state[:2], path_state.local_path_xy)
        yaw_error = float(np.arctan2(np.sin(state[2] - reference[2, 0]), np.cos(state[2] - reference[2, 0])))
        command_variation = float(np.linalg.norm(np.asarray(command) - previous_command))
        path_tracking_errors.append(path_error)
        yaw_tracking_errors.append(yaw_error)
        command_variations.append(command_variation)
        progress_ratio = float(
            np.clip(
                path_distance(state[:2], global_path)
                / max(path_distance(global_path[-1], global_path), 1.0e-12),
                0.0,
                1.0,
            )
        )
        rows.append({
            "replicate": replicate,
            "scenario_id": scenario.scenario_id,
            "controller": method,
            "step": step,
            "time_s": float(time_s),
            "robot_x_m": float(state[0]),
            "robot_y_m": float(state[1]),
            "robot_theta_rad": float(state[2]),
            "robot_vx_mps": float(state[3]),
            "robot_vy_mps": float(state[4]),
            "robot_omega_radps": float(state[5]),
            "context_position_x_m": float(person_position[0]),
            "context_position_y_m": float(person_position[1]),
            "context_speed_mps": float(observation.speed_per_s),
            "context_direction": previous_direction,
            "context_clearance_m": static_distance,
            "context_margin_m": margin,
            "global_path_replanned": False,
            "local_path_generation_count": path_state.local_generation_count,
            "local_path_replanned": did_replan,
            "selected_side": selected_side,
            "replan_reasons": ";".join(decision.reasons),
            "controller_success": success,
            "fallback": fallback,
            "status": status,
            "controller_compute_ms": float(elapsed_ms),
            "goal_error_m": goal_error,
            "path_tracking_error_m": path_error,
            "yaw_error_rad": yaw_error,
            "path_length_m": path_length_m,
            "progress_ratio": progress_ratio,
            "command_vx_mps": float(command[0]),
            "command_vy_mps": float(command[1]),
            "command_wz_radps": float(command[2]),
            "command_variation_norm": command_variation,
            "command_slew_norm_per_s": command_variation / DT_S,
            "near_miss": 0.0 <= margin < NEAR_MISS_MARGIN_M,
            "risk_bound": float(risk_bounds[-1]) if risk_bounds else 0.0,
            "risk_slack_m": float(risk_slacks[-1]) if risk_slacks else 0.0,
            "solver_iterations": int(solver_iterations[-1]) if solver_iterations else 0,
            "chance_relaxation_m": float(chance_relaxations[-1]) if chance_relaxations else 0.0,
            "constraint_violation_m": float(constraint_violations[-1]) if constraint_violations else 0.0,
        })
        previous_command = np.asarray(command, dtype=np.float64)
        if collisions == 0 and goal_error < 0.35:
            break
    goal_error = float(np.linalg.norm(state[:2] - global_path[-1]))
    summary = {
        "replicate": replicate,
        "scenario_id": scenario.scenario_id,
        "controller": method,
        "seed": seed,
        "collision": bool(collisions > 0),
        "safe_completion": bool(collisions == 0 and goal_error < 0.35),
        "minimum_context_margin_m": float(min_margin),
        "final_goal_error_m": goal_error,
        "completion_time_s": float(rows[-1]["time_s"]) if rows else None,
        "path_length_m": float(path_length_m),
        "progress_ratio": float(
            np.clip(
                path_distance(state[:2], global_path)
                / max(path_distance(global_path[-1], global_path), 1.0e-12),
                0.0,
                1.0,
            )
        ),
        "tracking_rmse_m": float(np.sqrt(np.mean(np.square(path_tracking_errors)))) if path_tracking_errors else None,
        "yaw_rmse_rad": float(np.sqrt(np.mean(np.square(yaw_tracking_errors)))) if yaw_tracking_errors else None,
        "mean_command_variation_norm": float(np.mean(command_variations)) if command_variations else None,
        "total_command_variation_norm": float(np.sum(command_variations)) if command_variations else None,
        "mean_command_slew_norm_per_s": float(np.mean(command_variations) / DT_S) if command_variations else None,
        "near_miss_count": int(near_miss_count),
        "fallback_duration_s": float(fallback_steps * DT_S),
        "steps": len(rows),
        "local_path_generation_count": path_state.local_generation_count,
        "global_path_replan_count": 0,
        "global_path_held_fixed": bool(np.array_equal(path_state.global_path_xy, global_path)),
        "controller_failure_count": controller_failures,
        "deadline_miss_count": deadline_misses,
        "compute_p50_ms": float(np.percentile(timings, 50)) if timings else None,
        "compute_p95_ms": float(np.percentile(timings, 95)) if timings else None,
        "compute_max_ms": float(np.max(timings)) if timings else None,
        "maximum_risk_bound": float(max(risk_bounds)) if risk_bounds else 0.0,
        "maximum_risk_slack_m": float(max(risk_slacks)) if risk_slacks else 0.0,
        "mean_solver_iterations": float(np.mean(solver_iterations)) if solver_iterations else 0.0,
        "maximum_chance_relaxation_m": float(max(chance_relaxations)) if chance_relaxations else 0.0,
        "maximum_constraint_violation_m": float(max(constraint_violations)) if constraint_violations else 0.0,
        "policy_parameters": policy.as_dict(),
    }
    return summary, rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty table: {path}")
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def aggregate(summaries: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    intervals = paired_bootstrap_intervals(
        summaries,
        replicates=BOOTSTRAP_REPLICATES,
        seed=BOOTSTRAP_SEED,
    )
    output: dict[str, dict[str, object]] = {}
    for controller in CONTROLLERS:
        rows = [row for row in summaries if row["controller"] == controller]
        compute_p95 = [
            float(row["compute_p95_ms"])
            for row in rows
            if row["compute_p95_ms"] is not None
        ]
        output[controller] = {
            "episode_count": len(rows),
            "collision_count": int(sum(bool(row["collision"]) for row in rows)),
            "safe_completion_rate": float(np.mean([row["safe_completion"] for row in rows])),
            "minimum_context_margin_m": float(min(row["minimum_context_margin_m"] for row in rows)),
            "mean_local_path_generations": float(np.mean([row["local_path_generation_count"] for row in rows])),
            "mean_compute_p95_ms": float(np.mean(compute_p95)) if compute_p95 else None,
            "mean_path_length_m": float(np.mean([float(row["path_length_m"]) for row in rows])),
            "mean_progress_ratio": float(np.mean([float(row["progress_ratio"]) for row in rows])),
            "mean_tracking_rmse_m": float(np.mean([float(row["tracking_rmse_m"]) for row in rows])),
            "mean_yaw_rmse_rad": float(np.mean([float(row["yaw_rmse_rad"]) for row in rows])),
            "mean_command_variation_norm": float(np.mean([float(row["mean_command_variation_norm"]) for row in rows])),
            "mean_command_slew_norm_per_s": float(np.mean([float(row["mean_command_slew_norm_per_s"]) for row in rows])),
            "total_near_miss_count": int(sum(int(row["near_miss_count"]) for row in rows)),
            "mean_fallback_duration_s": float(np.mean([float(row["fallback_duration_s"]) for row in rows])),
            "total_controller_failures": int(sum(int(row["controller_failure_count"]) for row in rows)),
            "total_deadline_misses": int(sum(int(row["deadline_miss_count"]) for row in rows)),
            "bootstrap_95ci": intervals[controller],
        }
    return output


def paired_bootstrap_intervals(
    summaries: list[dict[str, object]],
    *,
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, dict[str, dict[str, float | int]]]:
    if replicates < 1:
        raise ValueError("bootstrap replicates must be positive")
    units = sorted({(int(row["replicate"]), str(row["scenario_id"])) for row in summaries})
    if not units:
        raise ValueError("bootstrap requires at least one paired unit")
    by_controller = {
        controller: {
            (int(row["replicate"]), str(row["scenario_id"])): row
            for row in summaries
            if row.get("controller") == controller
        }
        for controller in CONTROLLERS
    }
    if any(set(rows) != set(units) for rows in by_controller.values()):
        raise ValueError("bootstrap requires the same paired units for every controller")
    rng = np.random.default_rng(seed)
    optional_metrics = tuple(
        name
        for name in (
            "path_length_m",
            "progress_ratio",
            "tracking_rmse_m",
            "yaw_rmse_rad",
            "mean_command_variation_norm",
            "mean_command_slew_norm_per_s",
            "near_miss_count",
            "fallback_duration_s",
        )
        if all(name in row and row[name] is not None for row in summaries)
    )
    sampled_values: dict[str, dict[str, np.ndarray]] = {
        controller: {
            "collision_rate": np.empty(replicates, dtype=np.float64),
            "safe_completion_rate": np.empty(replicates, dtype=np.float64),
            "final_goal_error_m": np.empty(replicates, dtype=np.float64),
            "compute_p95_ms": np.empty(replicates, dtype=np.float64),
            **{name: np.empty(replicates, dtype=np.float64) for name in optional_metrics},
        }
        for controller in CONTROLLERS
    }
    for index in range(replicates):
        sampled = rng.integers(0, len(units), size=len(units))
        for controller in CONTROLLERS:
            rows = [by_controller[controller][units[item]] for item in sampled]
            sampled_values[controller]["collision_rate"][index] = float(
                np.mean([bool(row["collision"]) for row in rows])
            )
            sampled_values[controller]["safe_completion_rate"][index] = float(
                np.mean([bool(row["safe_completion"]) for row in rows])
            )
            sampled_values[controller]["final_goal_error_m"][index] = float(
                np.mean([float(row["final_goal_error_m"]) for row in rows])
            )
            timing = [float(row["compute_p95_ms"]) for row in rows if row["compute_p95_ms"] is not None]
            sampled_values[controller]["compute_p95_ms"][index] = (
                float(np.mean(timing)) if timing else np.nan
            )
            for name in optional_metrics:
                sampled_values[controller][name][index] = float(np.mean([float(row[name]) for row in rows]))
    output: dict[str, dict[str, dict[str, float | int]]] = {}
    for controller, metrics in sampled_values.items():
        output[controller] = {}
        for metric, values in metrics.items():
            finite = values[np.isfinite(values)]
            if len(finite) == 0:
                continue
            output[controller][metric] = {
                "lower": float(np.percentile(finite, 2.5)),
                "upper": float(np.percentile(finite, 97.5)),
                "replicates": int(replicates),
                "unit_count": int(len(units)),
                "confidence_level": CONFIDENCE_LEVEL,
            }
    return output


def paired_effect_intervals(
    summaries: list[dict[str, object]],
    *,
    reference: str = "cca_nmpc",
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED + 1,
) -> dict[str, dict[str, dict[str, float | int | bool | str]]]:
    if reference not in CONTROLLERS:
        raise ValueError(f"unsupported reference controller: {reference}")
    units = sorted({(int(row["replicate"]), str(row["scenario_id"])) for row in summaries})
    if not units or replicates < 1:
        raise ValueError("paired effects require positive bootstrap replicates and paired units")
    by_controller = {
        controller: {
            (int(row["replicate"]), str(row["scenario_id"])): row
            for row in summaries
            if row.get("controller") == controller
        }
        for controller in CONTROLLERS
    }
    if any(set(rows) != set(units) for rows in by_controller.values()):
        raise ValueError("paired effects require the same units for every controller")
    comparators = tuple(controller for controller in CONTROLLERS if controller != reference)
    metric_names = [
        "safe_completion_rate_gain",
        "collision_rate_reduction",
        "final_goal_error_reduction_m",
        "compute_p95_reduction_ms",
    ]
    optional_effects = {
        "path_length_reduction_m": "path_length_m",
        "tracking_rmse_reduction_m": "tracking_rmse_m",
        "yaw_rmse_reduction_rad": "yaw_rmse_rad",
        "command_variation_reduction_norm": "mean_command_variation_norm",
        "fallback_duration_reduction_s": "fallback_duration_s",
    }
    optional_effects = {
        name: source
        for name, source in optional_effects.items()
        if all(source in row and row[source] is not None for row in summaries)
    }
    metric_names.extend(optional_effects)
    samples = {
        comparator: {metric: np.empty(replicates, dtype=np.float64) for metric in metric_names}
        for comparator in comparators
    }
    rng = np.random.default_rng(seed)
    for index in range(replicates):
        sampled = rng.integers(0, len(units), size=len(units))
        for comparator in comparators:
            reference_rows = [by_controller[reference][units[item]] for item in sampled]
            comparator_rows = [by_controller[comparator][units[item]] for item in sampled]
            samples[comparator]["safe_completion_rate_gain"][index] = float(
                np.mean([bool(row["safe_completion"]) for row in reference_rows])
                - np.mean([bool(row["safe_completion"]) for row in comparator_rows])
            )
            samples[comparator]["collision_rate_reduction"][index] = float(
                np.mean([bool(row["collision"]) for row in comparator_rows])
                - np.mean([bool(row["collision"]) for row in reference_rows])
            )
            samples[comparator]["final_goal_error_reduction_m"][index] = float(
                np.mean([float(row["final_goal_error_m"]) for row in comparator_rows])
                - np.mean([float(row["final_goal_error_m"]) for row in reference_rows])
            )
            comparator_timing = [float(row["compute_p95_ms"]) for row in comparator_rows if row["compute_p95_ms"] is not None]
            reference_timing = [float(row["compute_p95_ms"]) for row in reference_rows if row["compute_p95_ms"] is not None]
            samples[comparator]["compute_p95_reduction_ms"][index] = (
                float(np.mean(comparator_timing) - np.mean(reference_timing))
                if comparator_timing and reference_timing
                else np.nan
            )
            for effect_name, source_name in optional_effects.items():
                comparator_values = [float(row[source_name]) for row in comparator_rows]
                reference_values = [float(row[source_name]) for row in reference_rows]
                samples[comparator][effect_name][index] = float(
                    np.mean(comparator_values) - np.mean(reference_values)
                )
    output: dict[str, dict[str, dict[str, float | int | bool | str]]] = {}
    for comparator, metrics in samples.items():
        output[comparator] = {}
        for metric, values in metrics.items():
            finite = values[np.isfinite(values)]
            if len(finite) == 0:
                continue
            output[comparator][metric] = {
                "lower": float(np.percentile(finite, 2.5)),
                "upper": float(np.percentile(finite, 97.5)),
                "replicates": int(replicates),
                "unit_count": int(len(units)),
                "confidence_level": CONFIDENCE_LEVEL,
                "positive_favors_reference": True,
                "reference_controller": reference,
            }
    return output


def validate_benchmark_pairs(
    summaries: list[dict[str, object]],
    traces: list[dict[str, object]],
    *,
    replicates: int,
) -> None:
    if replicates < 1:
        raise ValueError("benchmark replicates must be positive")
    expected = {
        (replicate, scenario.scenario_id, controller)
        for replicate in range(replicates)
        for scenario in SCENARIOS
        for controller in CONTROLLERS
    }
    observed: set[tuple[int, str, str]] = set()
    for row in summaries:
        try:
            key = (int(row["replicate"]), str(row["scenario_id"]), str(row["controller"]))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("episode summary is missing replicate/scenario/controller identity") from error
        if key in observed:
            raise ValueError(f"duplicate paired episode summary: {key}")
        observed.add(key)
        if key not in expected:
            raise ValueError(f"episode summary is outside the frozen benchmark design: {key}")
        if row.get("global_path_replan_count") != 0 or row.get("global_path_held_fixed") is not True:
            raise ValueError("benchmark summary violates the fixed-global-path contract")
        for name, value in row.items():
            if isinstance(value, float) and not np.isfinite(value):
                raise ValueError(f"episode summary contains non-finite metric: {name}")
    if observed != expected:
        missing = sorted(expected - observed)
        raise ValueError(f"benchmark is not fully paired; missing {missing[:3]}")
    trace_keys: set[tuple[int, str, str]] = set()
    for row in traces:
        try:
            trace_keys.add((int(row["replicate"]), str(row["scenario_id"]), str(row["controller"])))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("time series is missing replicate/scenario/controller identity") from error
        if row.get("global_path_replanned") is not False:
            raise ValueError("time series violates the fixed-global-path contract")
        if any("trajectory" in str(key).lower() or "human_path" in str(key).lower() for key in row):
            raise ValueError("time series contains a forbidden human trajectory field")
    if trace_keys != expected:
        missing = sorted(expected - trace_keys)
        raise ValueError(f"time series is not fully paired; missing {missing[:3]}")


def policy_candidates() -> tuple[ContextPolicyParameters, ...]:
    candidates: list[ContextPolicyParameters] = []
    for lateral in (1.10, 1.35, 1.60):
        for longitudinal in (0.65, 0.85, 1.05):
            candidates.append(
                ContextPolicyParameters(
                    safe_distance_m=SAFE_CONTEXT_CLEARANCE_M,
                    lateral_offset_m=lateral,
                    longitudinal_offset_m=longitudinal,
                    context_radius_m=CONTEXT_RADIUS_M,
                )
            )
    return tuple(candidates)


def load_rl_policy(path: Path) -> dict[str, object]:
    """Load a hash-bound development policy learned by the score/penalty loop."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != "cca-tabular-rl-policy-v1":
        raise ValueError("RL policy must use cca-tabular-rl-policy-v1")
    if payload.get("training_mode") != "tabular_q_learning_score_penalty":
        raise ValueError("RL policy was not produced by the score/penalty learner")
    parameters = payload.get("best_parameters")
    if not isinstance(parameters, dict):
        raise ValueError("RL policy lacks best_parameters")
    try:
        policy = ContextPolicyParameters(
            safe_distance_m=float(parameters["safe_distance_m"]),
            lateral_offset_m=float(parameters["lateral_offset_m"]),
            longitudinal_offset_m=float(parameters["longitudinal_offset_m"]),
            context_radius_m=float(parameters["context_radius_m"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("RL policy parameters are invalid") from error
    return {
        "path": path.as_posix(),
        "sha256": sha256_file(path),
        "training_mode": payload["training_mode"],
        "best_action": payload.get("best_action"),
        "best_parameters": policy.as_dict(),
        "score_target": payload.get("score_target"),
        "episodes_completed": payload.get("episodes_completed"),
    }


def tune_policy(seed: int, horizon: int, target_score: float) -> object:
    development_seeds = (seed + 7000, seed + 7001, seed + 7002)

    def evaluate(parameters: ContextPolicyParameters) -> list[dict[str, object]]:
        outcomes: list[dict[str, object]] = []
        for scenario, scenario_seed in zip(SCENARIOS, development_seeds, strict=True):
            summary, _ = run_episode(
                scenario,
                "mpc",
                scenario_seed,
                horizon,
                parameters,
            )
            outcomes.append(summary)
        return outcomes

    return score_policy_search(
        policy_candidates(),
        evaluate,
        target_score=target_score,
        patience=int(MAP_CONTRACT["score_patience"]),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Context-only Python map benchmark")
    parser.add_argument("--campaign", choices=("pilot", "confirmatory"), default="pilot")
    parser.add_argument("--replicates", type=int)
    parser.add_argument("--seed", type=int, default=int(MAP_CONTRACT["seed"]))
    parser.add_argument("--horizon", type=int, default=int(MAP_CONTRACT["horizon"]))
    parser.add_argument("--score-target", type=float, default=float(MAP_CONTRACT["score_target"]))
    parser.add_argument("--no-score-tune", action="store_true")
    parser.add_argument("--protocol-freeze", type=Path)
    parser.add_argument("--lstm-checkpoint", type=Path)
    parser.add_argument(
        "--rl-policy",
        type=Path,
        help="score/penalty Q-learning policy; disables score-grid tuning when supplied",
    )
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "experiments" / "runs" / "context-map-run-20260812")
    args = parser.parse_args()
    default_replicates = int(
        MAP_CONTRACT["confirmatory_replicates"]
        if args.campaign == "confirmatory"
        else MAP_CONTRACT["pilot_replicates"]
    )
    replicates = int(args.replicates) if args.replicates is not None else default_replicates
    minimum_replicates = (
        int(MAP_CONTRACT["confirmatory_replicates"])
        if args.campaign == "confirmatory"
        else 1
    )
    if replicates < minimum_replicates or args.horizon < 1:
        raise SystemExit("replicates and horizon must be positive")
    if not 0.0 < args.score_target <= 1.0:
        raise SystemExit("--score-target must lie in (0, 1]")
    if args.campaign == "confirmatory" and MAP_CONTRACT["confirmatory_requires_no_score_tuning"] and not args.no_score_tune:
        raise SystemExit("confirmatory campaign requires --no-score-tune")
    protocol_freeze_metadata = None
    if args.campaign == "confirmatory":
        if args.protocol_freeze is None:
            raise SystemExit("confirmatory campaign requires --protocol-freeze")
        protocol_freeze_path = args.protocol_freeze.resolve()
        try:
            protocol_freeze_path.relative_to(PROJECT_ROOT)
        except ValueError as error:
            raise SystemExit("protocol-freeze must be inside the project root") from error
        freeze_payload = load_protocol_freeze(protocol_freeze_path)
        protocol_freeze_metadata = {
            "path": protocol_freeze_path.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": sha256_file(protocol_freeze_path),
            "freeze_id": str(freeze_payload["freeze_id"]),
            "freeze_version": str(freeze_payload["freeze_version"]),
        }
        if args.lstm_checkpoint is None:
            raise SystemExit("confirmatory campaign requires --lstm-checkpoint")
    unknown_controllers = sorted(set(CONTROLLERS) - set(CONTROLLER_DEFINITIONS))
    if unknown_controllers:
        raise SystemExit(f"controller definitions missing: {', '.join(unknown_controllers)}")
    context_lstm = None
    lstm_capture_metadata: dict[str, str] | None = None
    lstm_metadata: dict[str, object] = {
        "mode": "direct_direction_speed_adapter",
        "lstm_inside_cca": False,
        "checkpoint": None,
    }
    if args.lstm_checkpoint is not None:
        checkpoint_path = args.lstm_checkpoint.resolve()
        if not checkpoint_path.is_file():
            raise SystemExit(f"LSTM checkpoint does not exist: {checkpoint_path}")
        try:
            context_lstm = ContextLstmAdapter(checkpoint_path)
        except (OSError, ValueError, RuntimeError) as error:
            raise SystemExit(f"invalid LSTM checkpoint: {error}") from error
        if args.campaign == "confirmatory":
            try:
                lstm_capture_metadata = validate_confirmatory_lstm_provenance(
                    context_lstm.metadata
                )
                require_fitted_calibration(context_lstm.metadata)
            except ValueError as error:
                raise SystemExit(str(error)) from error
        try:
            checkpoint_reference = checkpoint_path.relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            checkpoint_reference = checkpoint_path.name
        lstm_metadata = {
            "mode": "lstm_checkpoint",
            "lstm_inside_cca": True,
            "checkpoint": {
                "path": checkpoint_reference,
                "sha256": sha256_file(checkpoint_path),
                "observed_steps": context_lstm.observed_steps,
                **(lstm_capture_metadata or {}),
            },
        }
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    rl_policy_metadata = None
    if args.rl_policy is not None:
        rl_policy_path = args.rl_policy.resolve()
        if not rl_policy_path.is_file():
            raise SystemExit(f"RL policy does not exist: {rl_policy_path}")
        try:
            rl_policy_metadata = load_rl_policy(rl_policy_path)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            raise SystemExit(f"invalid RL policy: {error}") from error
        policy = ContextPolicyParameters(**rl_policy_metadata["best_parameters"])
        tuning = {
            "training_mode": "tabular_q_learning_score_penalty",
            "target_score": float(args.score_target),
            "best_score": None,
            "target_reached": bool(
                isinstance(rl_policy_metadata.get("score_target"), (int, float))
                and isinstance(rl_policy_metadata.get("episodes_completed"), int)
            ),
            "stop_reason": "policy_loaded_from_rl_campaign",
            "best_parameters": policy.as_dict(),
            "iterations": [],
            "training_targets_used": False,
            "rl_policy": rl_policy_metadata,
        }
    elif args.no_score_tune:
        policy = DEFAULT_POLICY
        tuning = {
            "training_mode": "score_tuning_disabled",
            "target_score": float(args.score_target),
            "best_score": None,
            "target_reached": False,
            "stop_reason": "disabled_by_flag",
            "best_parameters": policy.as_dict(),
            "iterations": [],
            "training_targets_used": False,
        }
    else:
        result = tune_policy(args.seed, args.horizon, args.score_target)
        policy = result.best_parameters
        tuning = {
            "training_mode": "environment_score_policy_search",
            "target_score": float(args.score_target),
            "best_score": float(result.best_score),
            "target_reached": bool(result.target_reached),
            "stop_reason": result.stop_reason,
            "best_parameters": policy.as_dict(),
            "iterations": list(result.iterations),
            "training_targets_used": False,
            "action_scope": "bounded local-path parameters only",
            "direct_command_policy_learned": False,
        }
    summaries: list[dict[str, object]] = []
    traces: list[dict[str, object]] = []
    for replicate in range(replicates):
        for scenario_index, scenario in enumerate(SCENARIOS):
            scenario_seed = args.seed + replicate * 100 + scenario_index
            for controller_index, controller in enumerate(CONTROLLERS):
                summary, rows = run_episode(
                    scenario,
                    controller,
                    scenario_seed + controller_index,
                    args.horizon,
                    policy,
                    replicate,
                    context_lstm,
                )
                summaries.append(summary)
                traces.extend(rows)
    validate_benchmark_pairs(summaries, traces, replicates=replicates)
    write_csv(output / "episode_metrics.csv", summaries)
    write_csv(output / "time_series.csv", traces)
    aggregate_metrics = aggregate(summaries)
    paired_effects = paired_effect_intervals(summaries)
    (output / "score_tuning.json").write_text(json.dumps(tuning, indent=2), encoding="utf-8")
    (output / "summary.json").write_text(
        json.dumps(
            {
                "campaign": args.campaign,
                "aggregate": aggregate_metrics,
                "episodes": summaries,
                "score_tuning": tuning,
                "context_predictor": lstm_metadata,
                "statistics": {
                    "unit": "replicate_x_scenario",
                    "method": "paired_nonparametric_bootstrap",
                    "confidence_level": CONFIDENCE_LEVEL,
                    "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                    "bootstrap_seed": BOOTSTRAP_SEED,
                    "descriptive_only": True,
                },
                "paired_effects_vs_cca_nmpc": paired_effects,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    figure, axes = plt.subplots(1, len(SCENARIOS), figsize=(15, 4), sharex=True, sharey=True)
    for axis, scenario in zip(np.atleast_1d(axes), SCENARIOS, strict=True):
        for controller, color in zip(CONTROLLERS, PLOT_COLORS, strict=True):
            subset = [row for row in traces if row["scenario_id"] == scenario.scenario_id and row["controller"] == controller]
            if not subset:
                continue
            times = sorted({float(row["time_s"]) for row in subset})
            representative = [
                (
                    float(np.median([row["robot_x_m"] for row in subset if float(row["time_s"]) == time])),
                    float(np.median([row["robot_y_m"] for row in subset if float(row["time_s"]) == time])),
                )
                for time in times
            ]
            axis.plot(
                [point[0] for point in representative],
                [point[1] for point in representative],
                color=color,
                linewidth=1.6,
                label=controller,
            )
        axis.scatter([scenario.person_position_xy[0]], [scenario.person_position_xy[1]], color="#ff7f0e", marker="x", s=60, label="context origin (no human path)")
        axis.plot([scenario.start_xy[0], scenario.goal_xy[0]], [scenario.start_xy[1], scenario.goal_xy[1]], "k--", alpha=0.5, label="fixed global path")
        axis.set_title(scenario.scenario_id)
        axis.set_xlabel("x (m)")
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("y (m)")
    axes[-1].legend(fontsize=7)
    figure.tight_layout()
    figure.savefig(output / "map_traces.png", dpi=180)
    plt.close(figure)
    artifacts = {
        path.name: sha256_file(path)
        for path in output.iterdir()
        if path.is_file() and path.name != "manifest.json"
    }
    manifest = {
        "schema": "cca-context-only-map-controller-benchmark-manifest-v1",
        "run_id": f"run-{output.name}",
        "status": (
            "completed-confirmatory-unreleased"
            if args.campaign == "confirmatory"
            else "completed-development-map-context"
        ),
        "paper_edit": False,
        "context_only": True,
        "human_trajectory_generated": False,
        "human_motion_model": "piecewise_constant_velocity_context_events",
        "cca_internal_human_prediction": True,
        "human_prediction_overlay": False,
        "human_trajectory_provided_to_controller": False,
        "ground_truth_human_trajectory_provided_to_controller": False,
        "cca_prediction_source": "causal_context_velocity",
        "map_built_in_python": True,
        "global_path_held_fixed": True,
        "global_path_replan_count": 0,
        "local_path_generated_on_context_conflict_or_direction_change": True,
        "scenarios": [scenario.scenario_id for scenario in SCENARIOS],
        "campaign": args.campaign,
        "replicates": replicates,
        "minimum_paired_replicates": minimum_replicates,
        "score_tuning_allowed": not args.no_score_tune and args.rl_policy is None,
        "protocol_freeze": protocol_freeze_metadata,
        "controllers": list(CONTROLLERS),
        "controller_definitions": {
            controller: CONTROLLER_DEFINITIONS[controller]
            for controller in CONTROLLERS
        },
        "deadline_ms": DEADLINE_MS,
        "robot_radius_m": ROBOT_RADIUS_M,
        "human_radius_m": HUMAN_RADIUS_M,
        "robot_geometry": ROBOT_GEOMETRY,
        "learning": tuning,
        "reinforcement_policy": rl_policy_metadata,
        "context_predictor": lstm_metadata,
        "state_definition": list(POSITION_STATE_FIELDS),
        "command_definition": list(POSITION_COMMAND_FIELDS),
        "control_mode": POSITION_CONTROL_MODE,
        "control_interface": POSITION_CONTROL_INTERFACE,
        "statistics": {
            "unit": "replicate_x_scenario",
            "method": "paired_nonparametric_bootstrap",
            "confidence_level": CONFIDENCE_LEVEL,
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "descriptive_only": True,
        },
        "paired_effects_vs_cca_nmpc": paired_effects,
        "context_fields": ["position", "speed", "direction"],
        "artifacts": artifacts,
        "source_files": {
            "scripts/python/tools/map_run.py": sha256_file(Path(__file__).resolve()),
            "simulations/python/model.py": sha256_file(
                PROJECT_ROOT / "simulations" / "python" / "model.py"
            ),
            "src/runtime/local_path.py": sha256_file(
                PROJECT_ROOT / "src" / "runtime" / "local_path.py"
            ),
            "src/ai/ctx_lstm.py": sha256_file(PROJECT_ROOT / "src" / "ai" / "ctx_lstm.py"),
            "configs/study_contract.json": sha256_file(CONTRACT_PATH),
        },
        "claim_scope": (
            "CONFIRMATORY_MAP_CONTEXT_CCA_INTERNAL_PREDICTION_NO_GROUND_TRUTH_PATH_OR_IMAGE_OVERLAY"
            if args.campaign == "confirmatory"
            else "DEVELOPMENT_MAP_CONTEXT_CCA_INTERNAL_PREDICTION_NO_GROUND_TRUTH_PATH_OR_IMAGE_OVERLAY"
        ),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "status": manifest["status"], "aggregate": aggregate_metrics}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
