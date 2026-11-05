from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import select
import sys
import threading
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

try:
    import termios
    import tty
except ImportError:
    termios = None
    tty = None

try:
    from app.backend.bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from bootstrap import PROJECT_ROOT

from hardware import (
    N10P_PROTOCOL_PROFILE,
    N10PSerialSource,
    N10PDecoder,
    LidarPoint,
    LidarScan,
    Stm32SerialSource,
    Stm32Telemetry,
    utc_ns,
)
from app.backend.slam import OccupancyMap
from runtime.kalman import SixStateKalman, configured_yaw_signs


ZERO = (0.0, 0.0, 0.0)


def load_yaw_measurement_sign() -> float:
    return configured_yaw_signs(PROJECT_ROOT / "configs" / "physical_robot.json")[1]


def load_yaw_command_sign() -> float:
    return configured_yaw_signs(PROJECT_ROOT / "configs" / "physical_robot.json")[0]


CONTROL_FIELDS = (
    "t_ns",
    "vx_cmd_mps",
    "vy_cmd_mps",
    "wz_cmd_radps",
    "vx_applied_mps",
    "vy_applied_mps",
    "wz_applied_radps",
    "sequence",
    "transport",
)
STATE_FIELDS = (
    "t_ns",
    "x_m",
    "y_m",
    "yaw_rad",
    "vx_mps",
    "vy_mps",
    "wz_radps",
    "wheel_fl_radps",
    "wheel_fr_radps",
    "wheel_rl_radps",
    "wheel_rr_radps",
    "battery_mv",
    "pwm_mask",
    "external_faults",
    "accel_x_mps2",
    "accel_y_mps2",
    "accel_z_mps2",
    "gyro_x_radps",
    "gyro_y_radps",
    "gyro_z_radps",
    "voltage_v",
    "flag_stop",
    "yaw_rate_used_radps",
    "yaw_rate_source",
    "integration_dt_s",
    "speed_mps",
    "transport",
    "state_estimator",
    "kalman_cov_trace",
    "kalman_position_std_m",
    "kalman_heading_std_rad",
    "kalman_velocity_std_mps",
    "kalman_pose_updates",
    "kalman_pose_update_rejections",
    "kalman_motion_mode",
)
LIDAR_FIELDS = ("t_ns", "point_count", "points_json")
CAMERA_FIELDS = (
    "t_ns",
    "device_t_ns",
    "color_path",
    "color_bytes",
    "depth_path",
    "depth_bytes",
    "width_px",
    "height_px",
    "depth_scale_m",
    "encoding",
)
CONTEXT_FIELDS = (
    "t_ns",
    "position_x_m",
    "position_y_m",
    "speed_mps",
    "direction",
    "confidence",
    "context_valid",
    "lstm_active",
    "lstm_configured",
    "frame_path",
    "camera_device_t_ns",
    "lidar_min_range_m",
    "lidar_valid",
)
EVENT_FIELDS = ("t_ns", "event_type", "solve_ms", "status_code", "sequence", "detail")
DEFAULT_MAP_RESOLUTION_M = 0.025
MAX_MAP_POINTS = 240
YAW_RATE_MIN_RADPS = 0.08
YAW_RATE_RATIO_LOW = 0.72
YAW_RATE_RATIO_HIGH = 1.40


def finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def filter_occupied_components(
    occupied: set[tuple[int, int]], min_component_cells: int,
) -> set[tuple[int, int]]:
    remaining = set(occupied)
    cleaned: set[tuple[int, int]] = set()
    while remaining:
        seed = remaining.pop()
        component = [seed]
        stack = [seed]
        while stack:
            cell_x, cell_y = stack.pop()
            for delta_y in (-1, 0, 1):
                for delta_x in (-1, 0, 1):
                    if delta_x == 0 and delta_y == 0:
                        continue
                    neighbour = (cell_x + delta_x, cell_y + delta_y)
                    if neighbour in remaining:
                        remaining.remove(neighbour)
                        component.append(neighbour)
                        stack.append(neighbour)
        if len(component) >= min_component_cells:
            cleaned.update(component)
    return cleaned


def clean_saved_map_payload(payload: dict[str, Any], min_component_cells: int = 3) -> dict[str, Any]:
    width = int(payload.get("width", 0))
    height = int(payload.get("height", 0))
    values = payload.get("occupancy")
    if width <= 0 or height <= 0 or not isinstance(values, list) or len(values) < width * height:
        raise ValueError("saved map dimensions or occupancy data are invalid")
    occupied = {
        (index % width, index // width)
        for index, value in enumerate(values[: width * height])
        if value == 100
    }
    cleaned = filter_occupied_components(occupied, min_component_cells)
    result = dict(payload)
    result["occupancy"] = [
        100 if (index % width, index // width) in cleaned
        else -1 if value == 100
        else value
        for index, value in enumerate(values[: width * height])
    ]
    metadata = dict(payload.get("metadata") or {})
    metadata["cleaning"] = {
        "enabled": True,
        "method": "occupied_connected_components",
        "source": "saved_map_payload",
        "min_component_cells": min_component_cells,
        "raw_occupied_cells": len(occupied),
        "clean_occupied_cells": len(cleaned),
        "removed_occupied_cells": len(occupied) - len(cleaned),
    }
    result["metadata"] = metadata
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pose_yaw_rate(telemetry: Stm32Telemetry) -> tuple[float, str]:
    """Select a measured yaw rate when encoder and gyro disagree."""

    body = finite(telemetry.wz_radps) or 0.0
    gyro = finite(telemetry.gyro_z_radps) or 0.0
    if abs(gyro) >= YAW_RATE_MIN_RADPS:
        if abs(body) < YAW_RATE_MIN_RADPS:
            return gyro, "gyro_z_dropout_recovery"
        if body * gyro > 0.0:
            ratio = abs(gyro) / abs(body)
            if ratio < YAW_RATE_RATIO_LOW or ratio > YAW_RATE_RATIO_HIGH:
                return gyro, "gyro_z_disagreement"
    return body, "body_velocity"


@dataclass
class Pose:
    x_m: float = 0.0
    y_m: float = 0.0
    yaw_rad: float = 0.0
    last_t_ns: int | None = None
    last_dt_s: float = 0.0
    last_yaw_rate_radps: float = 0.0
    last_yaw_rate_source: str = "body_velocity"
    last_vx_mps: float = 0.0
    last_vy_mps: float = 0.0

    def _integrate(self, vx_mps: float, vy_mps: float, yaw_rate: float, dt: float) -> None:
        half_yaw = self.yaw_rad + 0.5 * yaw_rate * dt
        cosine = math.cos(half_yaw)
        sine = math.sin(half_yaw)
        self.x_m += (cosine * vx_mps - sine * vy_mps) * dt
        self.y_m += (sine * vx_mps + cosine * vy_mps) * dt
        self.yaw_rad = math.atan2(
            math.sin(self.yaw_rad + yaw_rate * dt),
            math.cos(self.yaw_rad + yaw_rate * dt),
        )

    def update(self, telemetry: Stm32Telemetry | None) -> None:
        if telemetry is None:
            return
        self.last_vx_mps = finite(telemetry.vx_mps) or 0.0
        self.last_vy_mps = finite(telemetry.vy_mps) or 0.0
        yaw_rate, source = pose_yaw_rate(telemetry)
        self.last_yaw_rate_radps = yaw_rate
        self.last_yaw_rate_source = source
        if self.last_t_ns is None:
            self.last_t_ns = telemetry.t_ns
            return
        if telemetry.t_ns <= self.last_t_ns:
            return
        dt = min((telemetry.t_ns - self.last_t_ns) / 1e9, 0.25)
        self.last_t_ns = telemetry.t_ns
        self.last_dt_s = dt
        self._integrate(telemetry.vx_mps, telemetry.vy_mps, yaw_rate, dt)

    def project_to(self, target_t_ns: int, telemetry: Stm32Telemetry | None) -> None:
        if telemetry is None or self.last_t_ns is None or target_t_ns <= self.last_t_ns:
            return
        dt = min((target_t_ns - self.last_t_ns) / 1e9, 0.25)
        yaw_rate, source = pose_yaw_rate(telemetry)
        self.last_vx_mps = finite(telemetry.vx_mps) or 0.0
        self.last_vy_mps = finite(telemetry.vy_mps) or 0.0
        self.last_yaw_rate_radps = yaw_rate
        self.last_yaw_rate_source = source
        self._integrate(telemetry.vx_mps, telemetry.vy_mps, yaw_rate, dt)
        self.last_t_ns = target_t_ns
        self.last_dt_s = dt

    def as_tuple(self) -> tuple[float, float, float]:
        return self.x_m, self.y_m, self.yaw_rad


def apply_estimator_state(pose: Pose, state: Any, *, t_ns: int | None = None,
                          dt_s: float | None = None, source: str = "six_state_ekf") -> None:
    pose.x_m, pose.y_m, pose.yaw_rad = (float(state[index]) for index in range(3))
    pose.last_vx_mps = float(state[3])
    pose.last_vy_mps = float(state[4])
    pose.last_yaw_rate_radps = float(state[5])
    pose.last_yaw_rate_source = source
    if t_ns is not None:
        pose.last_t_ns = int(t_ns)
    if dt_s is not None:
        pose.last_dt_s = max(0.0, float(dt_s))


def update_pose_with_ekf(pose: Pose, estimator: Any, telemetry: Stm32Telemetry,
                         *, yaw_measurement_sign: float = 1.0) -> Any:
    previous_t_ns = estimator.last_t_ns
    state = estimator.step(
        telemetry.t_ns,
        (telemetry.vx_mps, telemetry.vy_mps, telemetry.wz_radps * yaw_measurement_sign),
        acceleration_body_mps2=(telemetry.accel_x_mps2, telemetry.accel_y_mps2),
        gyro_z_radps=telemetry.gyro_z_radps * yaw_measurement_sign,
    )
    dt_s = 0.0 if previous_t_ns is None else min(max(0.0, (telemetry.t_ns - previous_t_ns) / 1e9), 0.25)
    apply_estimator_state(pose, state, t_ns=telemetry.t_ns, dt_s=dt_s,
                          source=f"six_state_ekf_{estimator.motion_mode}")
    return state


def bresenham(start: tuple[int, int], end: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    x0, y0 = start
    x1, y1 = end
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    error = dx + dy
    cells: list[tuple[int, int]] = []
    while True:
        cells.append((x0, y0))
        if x0 == x1 and y0 == y1:
            return tuple(cells)
        double = 2 * error
        if double >= dy:
            error += dy
            x0 += sx
        if double <= dx:
            error += dx
            y0 += sy


def compact_map_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep saved maps lossless while reducing live map messages."""

    compact = dict(payload)
    occupancy = compact.pop("occupancy", None)
    if isinstance(occupancy, list):
        runs: list[list[int]] = []
        for value in occupancy:
            code = int(value)
            if runs and runs[-1][0] == code:
                runs[-1][1] += 1
            else:
                runs.append([code, 1])
        compact["occupancy_encoding"] = "rle-v1"
        compact["occupancy_length"] = len(occupancy)
        compact["occupancy_rle"] = runs
    metadata = compact.get("metadata")
    if isinstance(metadata, dict):
        metadata = dict(metadata)
        history = metadata.get("history")
        if isinstance(history, dict):
            history = dict(history)
            records = history.get("records")
            trajectory = history.get("trajectory")
            if isinstance(records, list):
                history["records"] = records[-24:]
            if isinstance(trajectory, list):
                history["trajectory"] = trajectory[-1000:]
            metadata["history"] = history
        compact["metadata"] = metadata
    return compact


class Keyboard:
    def __init__(self) -> None:
        if os.name != "posix" or not sys.stdin.isatty():
            raise RuntimeError("manual teleop requires a POSIX terminal with stdin attached")
        self._settings: list[Any] | None = None

    def __enter__(self) -> "Keyboard":
        if termios is None or tty is None:
            raise RuntimeError("manual teleop requires termios support")
        self._settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        return self

    def __exit__(self, *_: Any) -> None:
        if self._settings is not None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._settings)

    def read(self) -> tuple[str, ...]:
        keys: list[str] = []
        while select.select([sys.stdin], [], [], 0.0)[0]:
            character = sys.stdin.read(1)
            if character != "\x1b":
                keys.append(character.lower())
                continue
            sequence = ""
            deadline = time.monotonic() + 0.01
            while len(sequence) < 2 and time.monotonic() < deadline:
                if select.select([sys.stdin], [], [], 0.001)[0]:
                    sequence += sys.stdin.read(1)
            keys.append({"[A": "up", "[B": "down", "[C": "right", "[D": "left"}.get(sequence, "escape"))
        return tuple(keys)


class RunFiles:
    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True, exist_ok=False)
        self.camera_root = root / "camera"
        self.depth_root = root / "depth"
        self.camera_root.mkdir()
        self.depth_root.mkdir()
        self.io_lock = threading.RLock()
        self.closed = False
        self.streams: dict[str, Any] = {}
        self.writers: dict[str, csv.DictWriter] = {}
        for name, fields in (
            ("control.csv", CONTROL_FIELDS),
            ("robot_state.csv", STATE_FIELDS),
            ("lidar.csv", LIDAR_FIELDS),
            ("camera.csv", CAMERA_FIELDS),
            ("context.csv", CONTEXT_FIELDS),
            ("events.csv", EVENT_FIELDS),
        ):
            stream = (root / name).open("w", encoding="utf-8", newline="")
            self.streams[name] = stream
            self.writers[name] = csv.DictWriter(stream, fieldnames=fields)
            self.writers[name].writeheader()
        self.history_stream = (root / "map_history.jsonl").open("w", encoding="utf-8")

    def write(self, name: str, row: dict[str, Any]) -> None:
        with self.io_lock:
            if not self.closed:
                self.writers[name].writerow(row)

    def write_map_history(self, record: dict[str, Any]) -> None:
        with self.io_lock:
            if not self.closed:
                self.history_stream.write(json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n")

    def event(self, kind: str, detail: str, sequence: int = 0) -> None:
        self.write("events.csv", {"t_ns": utc_ns(), "event_type": kind, "solve_ms": "", "status_code": 0, "sequence": sequence, "detail": detail})

    def state(self, t_ns: int, pose: Pose, telemetry: Stm32Telemetry | None, transport: str,
              estimator: Any = None) -> None:
        values = {
            "t_ns": t_ns,
            "x_m": pose.x_m,
            "y_m": pose.y_m,
            "yaw_rad": pose.yaw_rad,
            "vx_mps": "",
            "vy_mps": "",
            "wz_radps": "",
            "wheel_fl_radps": "",
            "wheel_fr_radps": "",
            "wheel_rl_radps": "",
            "wheel_rr_radps": "",
            "battery_mv": "",
            "pwm_mask": "",
            "external_faults": "",
            "accel_x_mps2": "",
            "accel_y_mps2": "",
            "accel_z_mps2": "",
            "gyro_x_radps": "",
            "gyro_y_radps": "",
            "gyro_z_radps": "",
            "voltage_v": "",
            "flag_stop": "",
            "yaw_rate_used_radps": pose.last_yaw_rate_radps,
            "yaw_rate_source": pose.last_yaw_rate_source,
            "integration_dt_s": pose.last_dt_s,
            "speed_mps": "",
            "transport": transport,
            "state_estimator": "six_state_ekf" if estimator is not None else "odometry",
        }
        if estimator is not None:
            values.update(estimator.diagnostics())
        if telemetry is not None:
            values.update(
                {
                    "vx_mps": telemetry.vx_mps,
                    "vy_mps": telemetry.vy_mps,
                    "wz_radps": telemetry.wz_radps,
                    "accel_x_mps2": telemetry.accel_x_mps2,
                    "accel_y_mps2": telemetry.accel_y_mps2,
                    "accel_z_mps2": telemetry.accel_z_mps2,
                    "gyro_x_radps": telemetry.gyro_x_radps,
                    "gyro_y_radps": telemetry.gyro_y_radps,
                    "gyro_z_radps": telemetry.gyro_z_radps,
                    "voltage_v": telemetry.voltage_v,
                    "flag_stop": telemetry.flag_stop,
                    "speed_mps": math.hypot(telemetry.vx_mps, telemetry.vy_mps),
                }
            )
        self.write("robot_state.csv", values)

    def control(self, t_ns: int, command: tuple[float, float, float], telemetry: Stm32Telemetry | None, sequence: int, transport: str) -> None:
        self.write(
            "control.csv",
            {
                "t_ns": t_ns,
                "vx_cmd_mps": command[0],
                "vy_cmd_mps": command[1],
                "wz_cmd_radps": command[2],
                "vx_applied_mps": "" if telemetry is None else telemetry.vx_mps,
                "vy_applied_mps": "" if telemetry is None else telemetry.vy_mps,
                "wz_applied_radps": "" if telemetry is None else telemetry.wz_radps,
                "sequence": sequence,
                "transport": transport,
            },
        )

    def scan(self, scan: LidarScan) -> None:
        points = [[round(point.angle_rad, 7), round(point.range_m, 4), int(point.intensity), int(point.return_id)] for point in scan.points]
        self.write("lidar.csv", {"t_ns": scan.t_ns, "point_count": len(points), "points_json": json.dumps(points, separators=(",", ":"))})

    def camera_frame(
        self,
        t_ns: int,
        device_t_ns: int | None,
        color_jpeg: bytes,
        depth_png: bytes | None,
        width_px: int,
        height_px: int,
        depth_scale_m: float,
    ) -> str:
        with self.io_lock:
            if self.closed:
                return ""
            stem = str(int(t_ns))
            color_path = self.camera_root / f"{stem}.jpg"
            color_path.write_bytes(color_jpeg)
            depth_path = ""
            depth_bytes = 0
            if depth_png:
                depth_file = self.depth_root / f"{stem}.png"
                depth_file.write_bytes(depth_png)
                depth_path = depth_file.relative_to(self.root).as_posix()
                depth_bytes = len(depth_png)
            color_relative = color_path.relative_to(self.root).as_posix()
            self.writers["camera.csv"].writerow(
                {
                    "t_ns": int(t_ns),
                    "device_t_ns": "" if device_t_ns is None else int(device_t_ns),
                    "color_path": color_relative,
                    "color_bytes": len(color_jpeg),
                    "depth_path": depth_path,
                    "depth_bytes": depth_bytes,
                    "width_px": int(width_px),
                    "height_px": int(height_px),
                    "depth_scale_m": float(depth_scale_m),
                    "encoding": "jpeg+png16" if depth_png else "jpeg",
                }
            )
            return color_relative

    def context(self, t_ns: int, pose: Pose, scan: LidarScan | None) -> None:
        minimum = "" if scan is None or not math.isfinite(scan.minimum_range_m) else scan.minimum_range_m
        self.write("context.csv", {"t_ns": t_ns, "position_x_m": "", "position_y_m": "", "speed_mps": "", "direction": "", "confidence": "", "context_valid": 0, "lstm_active": 0, "lstm_configured": 0, "frame_path": "", "camera_device_t_ns": "", "lidar_min_range_m": minimum, "lidar_valid": int(scan is not None)})

    def flush(self) -> None:
        with self.io_lock:
            if self.closed:
                return
            for stream in self.streams.values():
                stream.flush()
            self.history_stream.flush()

    def close(self) -> None:
        with self.io_lock:
            if self.closed:
                return
            for stream in self.streams.values():
                stream.flush()
                stream.close()
            self.history_stream.flush()
            self.history_stream.close()
            self.closed = True


def command_for_key(key: str, speed: float, yaw_speed: float) -> tuple[float, float, float] | None:
    return {
        "w": (speed, 0.0, 0.0),
        "up": (speed, 0.0, 0.0),
        "s": (-speed, 0.0, 0.0),
        "down": (-speed, 0.0, 0.0),
        "a": (0.0, speed, 0.0),
        "left": (0.0, speed, 0.0),
        "d": (0.0, -speed, 0.0),
        "right": (0.0, -speed, 0.0),
        "q": (0.0, 0.0, yaw_speed),
        "e": (0.0, 0.0, -yaw_speed),
    }.get(key)


def write_manifest(root: Path, args: argparse.Namespace, mapper: OccupancyMap, transport: str, started_ns: int, stopped_ns: int, status: str) -> None:
    files = {
        path.relative_to(root).as_posix(): {"bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in root.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    payload = {
        "schema": "cca-manual-teleop-lidar-map-v1",
        "run_id": root.name,
        "status": status,
        "paper_edit": False,
        "ros": False,
        "ros" + "2": False,
        "capture_source": "manual_hardware",
        "started_at_ns": started_ns,
        "stopped_at_ns": stopped_ns,
        "devices": {"stm": args.stm, "lidar": args.lidar},
        "baudrate": {"stm": args.stm_baud, "lidar": args.lidar_baud},
        "transport": transport,
        "lidar_protocol_profile": N10P_PROTOCOL_PROFILE,
        "map": {
            "resolution_m": args.resolution,
            "lidar_mount_m": [args.lidar_x, args.lidar_y],
            "lidar_yaw_rad": math.radians(args.lidar_yaw_deg),
            "scans": mapper.scans,
            "points": mapper.points,
            "scan_matching": mapper.scan_matching_enabled,
            "scan_match_attempts": mapper.scan_match_attempts,
            "scan_match_accepted": mapper.scan_match_accepted,
        },
        "control": {"keyboard": "w/s/a/d or arrows; q/e rotate; x/space stop; escape exit", "max_speed_mps": args.speed, "max_yaw_speed_radps": args.yaw_speed, "command_timeout_s": args.command_timeout},
        "files": files,
    }
    (root / "manifest.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def self_test() -> None:
    mapper = OccupancyMap(DEFAULT_MAP_RESOLUTION_M, lidar_x_m=0.1, lidar_y_m=0.0, lidar_yaw_rad=0.0, min_range_m=0.05, max_range_m=8.0, padding_cells=2)
    scan = LidarScan(1, (LidarPoint(1, 0.0, 1.0, 10, 0), LidarPoint(1, math.pi / 2, 0.5, 10, 0)))
    for _ in range(3):
        mapper.update(scan, Pose())
    payload = mapper.raw_payload()
    if payload["width"] < 3 or payload["height"] < 3 or 100 not in payload["occupancy"] or 0 not in payload["occupancy"]:
        raise AssertionError("occupancy map self-test failed")
    landmarks = tuple(
        LidarPoint(
            2,
            math.atan2(y_m, x_m),
            math.hypot(x_m, y_m),
            20,
            0,
        )
        for x_m in (0.8, 1.2, 1.6, 2.0)
        for y_m in (-1.0, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1.0)
    )
    reference_scan = LidarScan(2, landmarks)
    matcher = OccupancyMap(DEFAULT_MAP_RESOLUTION_M, lidar_x_m=0.0, lidar_y_m=0.0, lidar_yaw_rad=0.0, min_range_m=0.05, max_range_m=8.0, padding_cells=2)
    matcher.update(reference_scan, Pose())
    drifted_pose = Pose(x_m=0.10)
    matcher.update(reference_scan, drifted_pose)
    if not matcher.last_scan_match.accepted or drifted_pose.x_m > 0.05:
        raise AssertionError(f"scan-to-map self-test failed: {matcher.last_scan_match}")
    if N10PDecoder(N10P_PROTOCOL_PROFILE).packet_size != 108:
        raise AssertionError("N10P profile self-test failed")
    print("manual_map self-test: PASS")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Manual keyboard teleoperation with N10P 2D occupancy-map capture")
    result.add_argument("--stm", default="/dev/rai_controller")
    result.add_argument("--lidar", default="/dev/rai_lidar")
    result.add_argument("--stm-baud", type=int, default=115200)
    result.add_argument("--lidar-baud", type=int, default=460800)
    result.add_argument("--stm-backend", choices=("auto", "cpp", "python"), default="auto")
    result.add_argument("--output", type=Path, default=None)
    result.add_argument("--duration", type=float, default=0.0)
    result.add_argument("--speed", type=float, default=0.20)
    result.add_argument("--yaw-speed", type=float, default=0.60)
    result.add_argument("--command-timeout", type=float, default=1.0)
    result.add_argument("--send-rate", type=float, default=20.0)
    result.add_argument("--resolution", type=float, default=DEFAULT_MAP_RESOLUTION_M)
    result.add_argument("--max-range", type=float, default=8.0)
    result.add_argument("--min-range", type=float, default=0.05)
    result.add_argument("--padding-cells", type=int, default=5)
    result.add_argument("--lidar-x", type=float, default=0.10)
    result.add_argument("--lidar-y", type=float, default=0.0)
    result.add_argument("--lidar-yaw-deg", type=float, default=0.0)
    result.add_argument("--self-test", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.speed <= 0.0 or args.yaw_speed <= 0.0 or args.command_timeout <= 0.0 or args.send_rate <= 0.0:
        raise ValueError("speed, yaw speed, command timeout and send rate must be positive")
    output = args.output or PROJECT_ROOT / "experiments" / "runs" / f"manual-map-{time.strftime('%Y%m%d-%H%M%S')}"
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"output already exists; choose a new path: {output}")
    mapper = OccupancyMap(args.resolution, lidar_x_m=args.lidar_x, lidar_y_m=args.lidar_y, lidar_yaw_rad=math.radians(args.lidar_yaw_deg), min_range_m=args.min_range, max_range_m=args.max_range, padding_cells=args.padding_cells)
    files = RunFiles(output)
    pose = Pose()
    estimator = SixStateKalman()
    yaw_measurement_sign = load_yaw_measurement_sign()
    yaw_command_sign = load_yaw_command_sign()
    stm: Stm32SerialSource | None = None
    lidar: N10PSerialSource | None = None
    stm_started = False
    lidar_started = False
    sequence = 0
    command = ZERO
    last_input = time.monotonic()
    last_scan_ns: int | None = None
    started_ns = utc_ns()
    started_mono = time.monotonic()
    status = "stopped"
    try:
        stm = Stm32SerialSource(args.stm, baudrate=args.stm_baud, backend=args.stm_backend)
        lidar = N10PSerialSource(args.lidar, profile=N10P_PROTOCOL_PROFILE, baudrate=args.lidar_baud)
        stm.start()
        stm_started = True
        lidar.start()
        lidar_started = True
        files.event("start", f"stm_backend={stm.backend}; lidar_profile={N10P_PROTOCOL_PROFILE}")
        print("Manual map capture started. w/s/a/d or arrows move; q/e rotate; x/space stop; escape exits.")
        print(f"Output: {output}")
        print("Keep the area clear. The command watchdog stops after the keyboard timeout.")
        next_send = time.monotonic()
        next_state = next_send
        next_report = next_send
        with Keyboard() as keyboard:
            while True:
                now = time.monotonic()
                for key in keyboard.read():
                    if key == "escape":
                        files.event("exit_key", "escape")
                        status = "completed"
                        raise StopIteration
                    if key in {"x", " "}:
                        command = ZERO
                        last_input = now
                        files.event("stop_key", repr(key), sequence)
                        continue
                    selected = command_for_key(key, args.speed, args.yaw_speed)
                    if selected is not None:
                        command = selected
                        last_input = now
                        files.event("command_key", key, sequence)
                if now - last_input > args.command_timeout:
                    command = ZERO
                telemetry = stm.latest
                calibrated_telemetry = None
                if telemetry is not None:
                    if pose.last_t_ns is None or telemetry.t_ns > pose.last_t_ns:
                        update_pose_with_ekf(pose, estimator, telemetry, yaw_measurement_sign=yaw_measurement_sign)
                    calibrated_telemetry = replace(
                        telemetry,
                        wz_radps=telemetry.wz_radps * yaw_measurement_sign,
                        gyro_z_radps=telemetry.gyro_z_radps * yaw_measurement_sign,
                    )
                if lidar.latest is not None and lidar.latest.t_ns != last_scan_ns:
                    scan = lidar.latest
                    scan_pose_before = pose.as_tuple()
                    mapper.update(scan, pose)
                    scan_pose_after = pose.as_tuple()
                    if scan_pose_after != scan_pose_before:
                        estimator.update_pose(scan_pose_after, position_std_m=0.05,
                                              heading_std_rad=math.radians(3.0))
                        apply_estimator_state(pose, estimator.state, t_ns=pose.last_t_ns,
                                              dt_s=pose.last_dt_s,
                                              source="six_state_ekf_encoder_imu_lidar")
                    files.scan(scan)
                    files.write_map_history(mapper.history[-1])
                    files.context(scan.t_ns, pose, scan)
                    last_scan_ns = scan.t_ns
                if now >= next_send:
                    stm.send_velocity(command[0], command[1], command[2] * yaw_command_sign)
                    sequence += 1
                    files.control(utc_ns(), command, calibrated_telemetry, sequence, stm.backend)
                    next_send = now + 1.0 / args.send_rate
                if now >= next_state:
                    files.state(utc_ns(), pose, calibrated_telemetry, stm.backend, estimator)
                    next_state = now + 1.0 / args.send_rate
                if now >= next_report:
                    scan_count = mapper.scans
                    print(f"\rpose=({pose.x_m:+.2f},{pose.y_m:+.2f},{math.degrees(pose.yaw_rad):+.1f}deg) cmd=({command[0]:+.2f},{command[1]:+.2f},{command[2]:+.2f}) scans={scan_count}", end="", flush=True)
                    next_report = now + 1.0
                if args.duration > 0.0 and now - started_mono >= args.duration:
                    status = "completed_duration"
                    break
                files.flush()
                time.sleep(0.005)
    except StopIteration:
        pass
    except KeyboardInterrupt:
        status = "interrupted"
        files.event("keyboard_interrupt", "ctrl-c", sequence)
    except Exception as error:
        status = "failed"
        files.event("error", f"{type(error).__name__}: {error}", sequence)
        raise
    finally:
        if stm is not None and stm_started:
            try:
                stm.send_velocity(*ZERO)
            except Exception:
                pass
        if lidar is not None and lidar_started:
            lidar.stop()
        if stm is not None and stm_started:
            stm.stop()
        stopped_ns = utc_ns()
        map_summary = mapper.save(output)
        files.event("stop", f"status={status}; scans={mapper.scans}; points={mapper.points}", sequence)
        files.close()
        write_manifest(output, args, mapper, "unknown" if stm is None else stm.backend, started_ns, stopped_ns, status)
        print(f"\nSaved map: {output / 'map.json'} ({map_summary['width']}x{map_summary['height']}, scans={mapper.scans})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
