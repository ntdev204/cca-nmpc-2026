from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT

from shared import is_forbidden_context_field, validate_capture_calibration

ROOT = PROJECT_ROOT


REQUIRED = {
    "robot_state.csv": ["t_ns", "x_m", "y_m", "yaw_rad", "vx_mps", "vy_mps", "wz_radps"],
    "control.csv": ["t_ns"],
    "context.csv": [
        "t_ns",
        "position_x_m",
        "position_y_m",
        "speed_mps",
        "direction",
        "confidence",
        "context_valid",
    ],
    "events.csv": ["t_ns", "event_type"],
}
OPTIONAL = (
    "reference.csv",
    "constraints.csv",
    "map.yaml",
    "map.pgm",
    "calibration.json",
    "lidar.csv",
)
PACKAGE_META = ("manifest.json", "checksums.sha256")
CONTROL_SIGNAL_GROUPS = (
    ("vx_cmd_mps", "vy_cmd_mps", "wz_cmd_radps"),
    ("wheel_1_cmd", "wheel_2_cmd", "wheel_3_cmd", "wheel_4_cmd"),
    ("torque_1_nm", "torque_2_nm", "torque_3_nm", "torque_4_nm"),
)
CONTEXT_DIRECTIONS = {"left", "right", "forward", "backward", "unknown", "invalid"}
CAPTURE_SOURCES = {"hardware", "hardware_in_loop", "real_offline", "unknown"}
CONTROL_INTERFACES = {"body_velocity", "wheel_speed", "wheel_torque", "unknown"}
LIDAR_FIELDS = ("t_ns", "point_count", "points_json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_run_id(value: str) -> str:
    result = re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")
    return result or "final-run"


def read_csv(
    path: Path,
    required: list[str],
    numeric: tuple[str, ...] = (),
) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        missing = [field for field in required if field not in fields]
        if missing:
            raise ValueError(f"{path.name}: missing columns {', '.join(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path.name}: no data rows")
    previous: int | None = None
    for index, row in enumerate(rows, start=2):
        try:
            timestamp = int(row["t_ns"])
        except (TypeError, ValueError) as error:
            raise ValueError(f"{path.name}:{index}: t_ns must be an integer") from error
        for field in numeric:
            try:
                value = float(row[field])
            except (TypeError, ValueError) as error:
                raise ValueError(f"{path.name}:{index}: {field} must be numeric") from error
            if not math.isfinite(value):
                raise ValueError(f"{path.name}:{index}: {field} must be finite")
        if previous is not None and timestamp <= previous:
            raise ValueError(f"{path.name}:{index}: t_ns must be strictly increasing")
        previous = timestamp
    return rows, fields


def read_control(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    rows, fields = read_csv(path, REQUIRED["control.csv"])
    signal_group = next((group for group in CONTROL_SIGNAL_GROUPS if set(group).issubset(fields)), None)
    if signal_group is None:
        expected = " or ".join("{" + ", ".join(group) + "}" for group in CONTROL_SIGNAL_GROUPS)
        raise ValueError(f"{path.name}: one complete control signal group is required: {expected}")
    numeric = tuple(field for field in signal_group if field in fields)
    read_csv(path, REQUIRED["control.csv"], numeric)
    return rows, fields


def validate_control_interface(fields: list[str], control_interface: str) -> None:
    if control_interface not in CONTROL_INTERFACES:
        raise ValueError(f"unsupported control interface: {control_interface}")
    required = {
        "body_velocity": CONTROL_SIGNAL_GROUPS[0],
        "wheel_speed": CONTROL_SIGNAL_GROUPS[1],
        "wheel_torque": CONTROL_SIGNAL_GROUPS[2],
    }.get(control_interface)
    if required is not None and not set(required).issubset(fields):
        raise ValueError(
            f"control interface {control_interface} requires columns: {', '.join(required)}"
        )


def read_context(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    numeric = ("position_x_m", "position_y_m", "speed_mps", "confidence")
    rows, fields = read_csv(path, REQUIRED["context.csv"], numeric)
    forbidden = [field for field in fields if is_forbidden_context_field(field)]
    if forbidden:
        raise ValueError(f"{path.name}: human trajectory fields are forbidden: {', '.join(forbidden)}")
    for index, row in enumerate(rows, start=2):
        if row["direction"].strip().lower() not in CONTEXT_DIRECTIONS:
            raise ValueError(f"{path.name}:{index}: unsupported direction")
        valid = row["context_valid"].strip().lower()
        if valid not in {"0", "1", "true", "false", "yes", "no", "valid", "invalid"}:
            raise ValueError(f"{path.name}:{index}: context_valid must be boolean")
        confidence = float(row["confidence"])
        speed = float(row["speed_mps"])
        if not 0.0 <= confidence <= 1.0 or speed < 0.0:
            raise ValueError(f"{path.name}:{index}: invalid confidence or speed")
        device_timestamp = row.get("camera_device_t_ns", "").strip()
        if device_timestamp:
            try:
                if int(device_timestamp) < 0:
                    raise ValueError
            except ValueError as error:
                raise ValueError(
                    f"{path.name}:{index}: camera_device_t_ns must be a nonnegative integer"
                ) from error
    return rows, fields


def read_events(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    rows, fields = read_csv(path, REQUIRED["events.csv"])
    for index, row in enumerate(rows, start=2):
        if not row["event_type"].strip():
            raise ValueError(f"{path.name}:{index}: event_type must not be empty")
        for field in ("solve_ms", "minimum_clearance_m"):
            value = row.get(field, "").strip()
            if value:
                try:
                    parsed = float(value)
                except ValueError as error:
                    raise ValueError(f"{path.name}:{index}: {field} must be numeric") from error
                if not math.isfinite(parsed):
                    raise ValueError(f"{path.name}:{index}: {field} must be finite")
    return rows, fields


def read_lidar(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    rows, fields = read_csv(path, list(LIDAR_FIELDS))
    total_points = 0
    for index, row in enumerate(rows, start=2):
        try:
            point_count = int(row["point_count"])
            points = json.loads(row["points_json"])
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"{path.name}:{index}: invalid scan payload") from error
        if point_count < 0 or not isinstance(points, list) or point_count != len(points):
            raise ValueError(f"{path.name}:{index}: point_count does not match points_json")
        for point_index, point in enumerate(points):
            if not isinstance(point, list) or len(point) != 4:
                raise ValueError(f"{path.name}:{index}: point {point_index} must be [angle,range,intensity,return]")
            angle, distance, intensity, return_id = point
            if (
                not isinstance(angle, (int, float))
                or not isinstance(distance, (int, float))
                or not math.isfinite(float(angle))
                or not math.isfinite(float(distance))
                or float(distance) < 0.0
                or not isinstance(intensity, int)
                or not isinstance(return_id, int)
                or intensity < 0
                or return_id < 0
            ):
                raise ValueError(f"{path.name}:{index}: point {point_index} contains invalid values")
        total_points += point_count
    if total_points == 0:
        raise ValueError(f"{path.name}: no lidar points were recorded")
    return rows, fields


def read_map(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path.name}: invalid JSON") from error
    required = ("frame_id", "resolution_m", "width", "height", "origin", "occupancy")
    missing = [field for field in required if field not in payload]
    if missing:
        raise ValueError(f"{path.name}: missing fields {', '.join(missing)}")
    if not isinstance(payload["frame_id"], str) or not payload["frame_id"].strip():
        raise ValueError(f"{path.name}: frame_id must be a nonempty string")
    width = payload["width"]
    height = payload["height"]
    if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
        raise ValueError(f"{path.name}: width and height must be positive integers")
    if not isinstance(payload["origin"], list) or len(payload["origin"]) != 3:
        raise ValueError(f"{path.name}: origin must be [x_m, y_m, yaw_rad]")
    try:
        resolution = float(payload["resolution_m"])
    except (TypeError, ValueError) as error:
        raise ValueError(f"{path.name}: resolution_m must be numeric") from error
    if not math.isfinite(resolution) or resolution <= 0.0:
        raise ValueError(f"{path.name}: resolution_m must be positive and finite")
    try:
        origin = [float(value) for value in payload["origin"]]
    except (TypeError, ValueError) as error:
        raise ValueError(f"{path.name}: origin values must be numeric") from error
    if not all(math.isfinite(value) for value in origin):
        raise ValueError(f"{path.name}: origin values must be finite")
    occupancy = payload["occupancy"]
    if not isinstance(occupancy, list) or len(occupancy) != width * height:
        raise ValueError(f"{path.name}: occupancy length must equal width*height")
    if any(not isinstance(value, int) or value not in (-1, 0, 100) for value in occupancy):
        raise ValueError(f"{path.name}: occupancy values must be -1, 0, or 100")
    return payload


def copy_payload(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name in (*REQUIRED, "map.json", *OPTIONAL):
        candidate = source / name
        if candidate.is_file():
            shutil.copy2(candidate, destination / name)


def package(
    source: Path,
    output: Path,
    run_id: str | None,
    robot: str,
    controller: str,
    clock: str,
    capture_source: str = "unknown",
    camera: str = "not-declared",
    lidar: str = "not-declared",
    firmware: str = "not-declared",
    control_interface: str = "unknown",
) -> Path:
    source = source.resolve()
    output = output.resolve()
    if capture_source not in CAPTURE_SOURCES:
        raise ValueError(f"unsupported capture source: {capture_source}")
    if control_interface not in CONTROL_INTERFACES:
        raise ValueError(f"unsupported control interface: {control_interface}")
    if capture_source in {"hardware", "hardware_in_loop", "real_offline"} and control_interface == "wheel_torque":
        raise ValueError(
            "physical position_state packages require the body_velocity interface; "
            "wheel_torque is legacy-only"
        )
    if not source.is_dir():
        raise ValueError(f"input directory does not exist: {source}")
    if source != output:
        if output.exists() and any(output.iterdir()):
            raise ValueError(f"output directory must be empty: {output}")
        copy_payload(source, output)
    allowed = set((*REQUIRED, "map.json", *OPTIONAL, *PACKAGE_META))
    unexpected = sorted(
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_dir() or (path.is_file() and path.name not in allowed)
    )
    if unexpected:
        raise ValueError(f"unexpected files in final package: {', '.join(unexpected)}")
    for name, columns in REQUIRED.items():
        if not (output / name).is_file():
            raise ValueError(f"missing required file: {name}")
        if name == "control.csv":
            _, control_fields = read_control(output / name)
            validate_control_interface(control_fields, control_interface)
        elif name == "context.csv":
            read_context(output / name)
        elif name == "events.csv":
            read_events(output / name)
        elif name == "robot_state.csv":
            read_csv(output / name, columns, tuple(field for field in columns if field != "t_ns"))
        else:
            read_csv(output / name, columns)
    lidar_path = output / "lidar.csv"
    if lidar_path.is_file():
        read_lidar(lidar_path)
    elif capture_source != "unknown":
        raise ValueError("lidar.csv is required for a non-unknown capture source")
    map_payload = read_map(output / "map.json")
    calibration_path = output / "calibration.json"
    calibration_payload: dict[str, Any] | None = None
    if calibration_path.is_file():
        try:
            calibration_payload = json.loads(calibration_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("calibration.json: invalid JSON") from error
        validate_capture_calibration(calibration_payload, camera=camera, lidar=lidar)
    elif capture_source != "unknown":
        raise ValueError("calibration.json is required for a non-unknown capture source")
    package_id = safe_run_id(run_id or output.name)
    files: dict[str, dict[str, Any]] = {}
    for name in (*REQUIRED, "map.json", *OPTIONAL):
        path = output / name
        if path.is_file():
            rows = None
            if path.suffix == ".csv":
                with path.open("r", encoding="utf-8-sig", newline="") as stream:
                    rows = max(sum(1 for _ in stream) - 1, 0)
            files[name] = {"bytes": path.stat().st_size, "sha256": sha256_file(path), **({"rows": rows} if rows is not None else {})}
    manifest = {
        "schema_version": "1.0.0",
        "run_id": package_id,
        "status": "verified",
        "integrity_status": "verified",
        "evidence_status": "captured-unverified" if capture_source != "unknown" else "source-unverified",
        "capture_source": capture_source,
        "captured_at": utc_now(),
        "sealed_at": utc_now(),
        "robot": robot,
        "controller": controller,
        "control_interface": control_interface,
        "control_mode": "position_state",
        "state_definition": ["x_m", "y_m", "theta_rad", "vx_mps", "vy_mps", "omega_radps"],
        "state_csv_mapping": {"theta_rad": "yaw_rad", "omega_radps": "wz_radps"},
        "firmware": firmware,
        "sensors": {"camera": camera, "lidar": lidar},
        "frame_id": str(map_payload["frame_id"]),
        "map_sha256": sha256_file(output / "map.json"),
        "calibration": (
            {
                "path": "calibration.json",
                "sha256": sha256_file(calibration_path),
                "calibration_id": calibration_payload["calibration_id"],
            }
            if calibration_payload is not None
            else None
        ),
        "clock": clock,
        "units": "si",
        "context_only": True,
        "human_trajectory_generated": False,
        "replay_file_included": False,
        "files": files,
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    checksums = [(sha256_file(output / name), name) for name in files]
    checksums.append((sha256_file(manifest_path), "manifest.json"))
    (output / "checksums.sha256").write_text(
        "".join(f"{digest}  {name}\n" for digest, name in sorted(checksums, key=lambda item: item[1])),
        encoding="utf-8",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and seal a final robot CSV/map package")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--robot", default="mecanum")
    parser.add_argument("--controller", default="cca_nmpc")
    parser.add_argument("--clock", choices=("robot_time", "system_time"), default="robot_time")
    parser.add_argument(
        "--capture-source",
        choices=tuple(sorted(CAPTURE_SOURCES)),
        default="unknown",
        help="source of the raw capture; this does not promote scientific evidence",
    )
    parser.add_argument("--camera", default="not-declared")
    parser.add_argument("--lidar", default="not-declared")
    parser.add_argument("--firmware", default="not-declared")
    parser.add_argument(
        "--control-interface",
        choices=tuple(sorted(CONTROL_INTERFACES)),
        default="unknown",
        help="physical command interface represented by control.csv",
    )
    arguments = parser.parse_args()
    output = arguments.output or arguments.input
    try:
        package(
            arguments.input,
            output,
            arguments.run_id,
            arguments.robot,
            arguments.controller,
            arguments.clock,
            arguments.capture_source,
            arguments.camera,
            arguments.lidar,
            arguments.firmware,
            arguments.control_interface,
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
