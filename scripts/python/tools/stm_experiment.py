from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import time
from bisect import bisect_right
from pathlib import Path
from typing import Any

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT

from hardware import (
    POSITION_STATE_FIELDS,
    STM32_ACCELERATOR_RATIO,
    STM32_COMMAND_SIZE,
    STM32_FRAME_HEADER,
    STM32_FRAME_TAIL,
    STM32_GYROSCOPE_RATIO,
    STM32_TELEMETRY_SIZE,
    Odometry,
    Stm32SerialSource,
    encode_stm32_velocity_command,
    utc_ns,
)
from shared import sha256_file


BRIDGE_CPP = PROJECT_ROOT / "reference" / "robot" / "turn_on_rai_robot" / "src" / "rai_robot.cpp"
BRIDGE_HEADER = (
    PROJECT_ROOT
    / "reference"
    / "robot"
    / "turn_on_rai_robot"
    / "include"
    / "turn_on_rai_robot"
    / "rai_robot.h"
)
CPP_TRANSPORT_SOURCE = PROJECT_ROOT / "src" / "control" / "src" / "stm_c_api.cpp"
CPP_TRANSPORT_HEADER = PROJECT_ROOT / "src" / "control" / "include" / "control" / "stm_c_api.h"
CONTROL_FIELDS = ("t_ns", "vx_cmd_mps", "vy_cmd_mps", "wz_cmd_radps", "transport", "command_sequence")
STATE_FIELDS = (
    "t_ns",
    "x_m",
    "y_m",
    "theta_rad",
    "vx_mps",
    "vy_mps",
    "omega_radps",
    "flag_stop",
    "accel_x_mps2",
    "accel_y_mps2",
    "accel_z_mps2",
    "gyro_x_radps",
    "gyro_y_radps",
    "gyro_z_radps",
    "voltage_v",
    "transport",
)
EVENT_FIELDS = ("t_ns", "event", "detail")
REQUIRED_SAFETY_FIELDS = (
    "approved",
    "emergency_stop_verified",
    "remote_disable_verified",
    "watchdog_verified",
)


def finite(value: Any, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be numeric") from error
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def validate_output(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.exists() and (not resolved.is_dir() or any(resolved.iterdir())):
        raise ValueError(f"output directory must be absent or empty: {resolved}")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def load_structured(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml
        except ImportError as error:
            raise ValueError(f"{path} is not JSON and PyYAML is unavailable") from error
        payload = yaml.safe_load(text)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain an object")
    return payload


def validate_safety_record(path: Path) -> dict[str, Any]:
    payload = load_structured(path)
    record = payload.get("safety") if isinstance(payload.get("safety"), dict) else payload
    missing = [field for field in REQUIRED_SAFETY_FIELDS if record.get(field) is not True]
    if missing:
        raise ValueError("safety record must set true: " + ", ".join(missing))
    return payload


def validate_command(values: tuple[float, float, float]) -> tuple[float, float, float]:
    result = tuple(finite(value, name) for value, name in zip(values, ("vx_mps", "vy_mps", "wz_radps")))
    encode_stm32_velocity_command(*result)
    return result


def validate_schedule(rows: list[tuple[float, float, float, float]]) -> list[tuple[float, float, float, float]]:
    if not rows:
        raise ValueError("command schedule must contain at least one row")
    previous = -math.inf
    normalized: list[tuple[float, float, float, float]] = []
    for timestamp, vx, vy, wz in rows:
        timestamp_value = finite(timestamp, "schedule timestamp")
        if timestamp_value < 0.0 or timestamp_value <= previous:
            raise ValueError("schedule timestamps must be strictly increasing and nonnegative")
        command = validate_command((vx, vy, wz))
        normalized.append((timestamp_value, *command))
        previous = timestamp_value
    if any(abs(value) > 1.0e-12 for value in normalized[-1][1:]):
        raise ValueError("command schedule must end with an explicit zero-velocity row")
    return normalized


def load_schedule(path: Path) -> list[tuple[float, float, float, float]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or ())
        required = {"t_s", "vx_mps", "vy_mps", "wz_radps"}
        if not required.issubset(fields):
            raise ValueError("schedule CSV requires t_s,vx_mps,vy_mps,wz_radps")
        rows: list[tuple[float, float, float, float]] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    (
                        float(row["t_s"]),
                        float(row["vx_mps"]),
                        float(row["vy_mps"]),
                        float(row["wz_radps"]),
                    )
                )
            except (TypeError, ValueError) as error:
                raise ValueError(f"schedule row {row_number} contains invalid numeric data") from error
    return validate_schedule(rows)


def make_pattern(
    duration_s: float,
    period_s: float,
    pattern: str,
    speed_mps: float,
    angular_radps: float,
) -> list[tuple[float, float, float, float]]:
    duration = finite(duration_s, "duration_s")
    period = finite(period_s, "period_s")
    speed = finite(speed_mps, "speed_mps")
    angular = finite(angular_radps, "angular_radps")
    if duration <= 0.0 or period <= 0.0:
        raise ValueError("duration_s and period_s must be positive")
    if pattern not in {"observe", "forward", "lateral", "rotate", "square"}:
        raise ValueError("unknown pattern")
    rows: list[tuple[float, float, float, float]] = []
    count = max(1, int(math.ceil(duration / period)))
    for index in range(count):
        timestamp = min(index * period, duration)
        if pattern == "forward":
            command = (speed, 0.0, 0.0)
        elif pattern == "lateral":
            command = (0.0, speed, 0.0)
        elif pattern == "rotate":
            command = (0.0, 0.0, angular)
        elif pattern == "square":
            phase = min(3, int((timestamp / duration) * 4.0))
            command = ((speed, 0.0, 0.0), (0.0, speed, 0.0), (0.0, 0.0, angular), (-speed, 0.0, 0.0))[phase]
        else:
            command = (0.0, 0.0, 0.0)
        rows.append((timestamp, *validate_command(command)))
    if rows[-1][0] >= duration:
        rows.pop()
    rows.append((duration, 0.0, 0.0, 0.0))
    return validate_schedule(rows)


def command_at(schedule: list[tuple[float, float, float, float]], elapsed_s: float) -> tuple[float, float, float]:
    index = bisect_right([row[0] for row in schedule], elapsed_s) - 1
    if index < 0 or elapsed_s >= schedule[-1][0]:
        return (0.0, 0.0, 0.0)
    return tuple(schedule[index][1:])


def write_schedule(path: Path, rows: list[tuple[float, float, float, float]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("t_s", "vx_mps", "vy_mps", "wz_radps"))
        writer.writerows(rows)


def writer(path: Path, fields: tuple[str, ...]) -> csv.DictWriter:
    stream = path.open("w", encoding="utf-8", newline="")
    result = csv.DictWriter(stream, fieldnames=fields)
    result.writeheader()
    result._cca_stream = stream
    return result


def close_writer(value: csv.DictWriter) -> None:
    stream = getattr(value, "_cca_stream", None)
    if stream is not None:
        stream.flush()
        stream.close()


def write_event(events: csv.DictWriter, event: str, detail: str) -> None:
    events.writerow({"t_ns": utc_ns(), "event": event, "detail": detail})
    getattr(events, "_cca_stream").flush()


def file_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.iterdir())
        if path.is_file() and path.name not in {"manifest.json"}
    }


def source_metadata() -> dict[str, Any]:
    if not BRIDGE_CPP.is_file() or not BRIDGE_HEADER.is_file():
        raise FileNotFoundError("STM bridge source/header is unavailable")
    if not CPP_TRANSPORT_SOURCE.is_file() or not CPP_TRANSPORT_HEADER.is_file():
        raise FileNotFoundError("C++ STM transport source/header is unavailable")
    return {
        "bridge_cpp": BRIDGE_CPP.relative_to(PROJECT_ROOT).as_posix(),
        "bridge_header": BRIDGE_HEADER.relative_to(PROJECT_ROOT).as_posix(),
        "bridge_cpp_sha256": sha256_file(BRIDGE_CPP),
        "bridge_header_sha256": sha256_file(BRIDGE_HEADER),
        "cpp_transport_source": CPP_TRANSPORT_SOURCE.relative_to(PROJECT_ROOT).as_posix(),
        "cpp_transport_header": CPP_TRANSPORT_HEADER.relative_to(PROJECT_ROOT).as_posix(),
        "cpp_transport_source_sha256": sha256_file(CPP_TRANSPORT_SOURCE),
        "cpp_transport_header_sha256": sha256_file(CPP_TRANSPORT_HEADER),
    }


def copy_map(map_path: Path | None, output: Path) -> dict[str, Any] | None:
    if map_path is None:
        return None
    source = map_path.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    target = output / "map.json"
    shutil.copy2(source, target)
    return {"file": target.name, "source": source.as_posix(), "sha256": sha256_file(target)}


def run(args: argparse.Namespace) -> int:
    output = validate_output(args.output)
    duration = finite(args.duration_s, "duration_s")
    period = finite(args.period_s, "period_s")
    if duration <= 0.0 or period <= 0.0:
        raise ValueError("duration_s and period_s must be positive")
    if not args.operator.strip() or not args.firmware_id.strip():
        raise ValueError("operator and firmware_id are required")
    schedule = load_schedule(args.schedule) if args.schedule else make_pattern(
        duration, period, args.pattern, args.speed_mps, args.angular_radps
    )
    if schedule[-1][0] > duration + 1.0e-9:
        raise ValueError("schedule ends after duration_s")
    motion_requested = any(abs(value) > 1.0e-12 for row in schedule for value in row[1:])
    safety = None
    if motion_requested:
        if not args.allow_actuation:
            raise ValueError("nonzero commands require --allow-actuation")
        if args.safety_record is None:
            raise ValueError("nonzero commands require --safety-record")
        safety = validate_safety_record(args.safety_record)
    schedule_path = output / "command_schedule.csv"
    write_schedule(schedule_path, schedule)
    schedule_source = (
        {"path": args.schedule.resolve().as_posix(), "sha256": sha256_file(args.schedule)}
        if args.schedule
        else {"pattern": args.pattern, "period_s": period, "duration_s": duration}
    )
    map_metadata = copy_map(args.map_json, output)
    controls = writer(output / "control.csv", CONTROL_FIELDS)
    states = writer(output / "robot_state.csv", STATE_FIELDS)
    events = writer(output / "events.csv", EVENT_FIELDS)
    source = Stm32SerialSource(
        args.port,
        baudrate=args.baud,
        timeout_s=args.timeout_s,
        mode=args.mode,
    )
    odometry = Odometry()
    sequence = 0
    last_telemetry_ns: int | None = None
    last_missing_ns = 0
    started = False
    exit_code = 0
    run_start_ns = utc_ns()
    monotonic_start = time.monotonic_ns()
    telemetry_samples = 0
    stop_latched = False
    try:
        source.start()
        started = True
        write_event(events, "start", json.dumps({"port": args.port, "baudrate": args.baud}, sort_keys=True))
        while True:
            now_mono = time.monotonic_ns()
            elapsed_s = (now_mono - monotonic_start) * 1.0e-9
            if elapsed_s >= duration:
                break
            latest = source.latest
            if latest is not None and latest.flag_stop:
                if not stop_latched:
                    write_event(events, "stm_stop_latched", "STM32 stop flag asserted; motion command forced to zero")
                stop_latched = True
            command = (0.0, 0.0, 0.0) if stop_latched else command_at(schedule, elapsed_s)
            source.send_velocity(*command)
            controls.writerow(
                {
                    "t_ns": utc_ns(),
                    "vx_cmd_mps": command[0],
                    "vy_cmd_mps": command[1],
                    "wz_cmd_radps": command[2],
                    "transport": "stm32_serial",
                    "command_sequence": sequence,
                }
            )
            controls._cca_stream.flush()
            write_event(events, "command", json.dumps({"sequence": sequence, "vx": command[0], "vy": command[1], "wz": command[2]}, separators=(",", ":")))
            sequence += 1
            latest = source.latest
            if latest is not None and latest.t_ns != last_telemetry_ns:
                odometry.update(latest.t_ns, (latest.vx_mps, latest.vy_mps, latest.wz_radps))
                state = odometry.state
                states.writerow(
                    {
                        "t_ns": latest.t_ns,
                        "x_m": state[0],
                        "y_m": state[1],
                        "theta_rad": state[2],
                        "vx_mps": state[3],
                        "vy_mps": state[4],
                        "omega_radps": state[5],
                        "flag_stop": latest.flag_stop,
                        "accel_x_mps2": latest.accel_x_mps2,
                        "accel_y_mps2": latest.accel_y_mps2,
                        "accel_z_mps2": latest.accel_z_mps2,
                        "gyro_x_radps": latest.gyro_x_radps,
                        "gyro_y_radps": latest.gyro_y_radps,
                        "gyro_z_radps": latest.gyro_z_radps,
                        "voltage_v": latest.voltage_v,
                        "transport": "stm32_serial",
                    }
                )
                states._cca_stream.flush()
                last_telemetry_ns = latest.t_ns
                telemetry_samples += 1
            elif now_mono - last_missing_ns >= 1_000_000_000:
                write_event(events, "telemetry_missing", "no new 24-byte STM32 telemetry frame")
                last_missing_ns = now_mono
            if stop_latched:
                break
            next_deadline = monotonic_start + int((sequence + 1) * period * 1.0e9)
            wait_s = (next_deadline - time.monotonic_ns()) * 1.0e-9
            if wait_s > 0.0:
                time.sleep(wait_s)
        source.send_velocity(0.0, 0.0, 0.0)
        controls.writerow(
            {
                "t_ns": utc_ns(),
                "vx_cmd_mps": 0.0,
                "vy_cmd_mps": 0.0,
                "wz_cmd_radps": 0.0,
                "transport": "stm32_serial",
                "command_sequence": sequence,
            }
        )
        controls._cca_stream.flush()
        write_event(events, "stop", "explicit zero-velocity command")
    except KeyboardInterrupt:
        exit_code = 130
        write_event(events, "error", "operator_interrupt")
    except Exception as error:
        exit_code = 1
        write_event(events, "error", f"{type(error).__name__}: {error}")
    finally:
        if started:
            try:
                source.send_velocity(0.0, 0.0, 0.0)
            except Exception as error:
                write_event(events, "error", f"zero_command_failed: {type(error).__name__}: {error}")
            source.stop()
        close_writer(controls)
        close_writer(states)
        close_writer(events)
    metadata = {
        "schema": "cca-direct-stm-capture-v1",
        "capture_id": output.name,
        "capture_started_at_utc_ns": run_start_ns,
        "capture_finished_at_utc_ns": utc_ns(),
        "capture_status": "completed" if exit_code == 0 else "failed",
        "data_status": "telemetry_observed" if telemetry_samples else "no_telemetry_observed",
        "operator": args.operator,
        "firmware_id": args.firmware_id,
        "runtime": {"middleware": "direct_serial", "ros_runtime": False},
        "transport": "stm32_serial",
        "transport_backend": getattr(source, "backend", "python"),
        "transport_library": (
            source.transport_library.as_posix()
            if getattr(source, "transport_library", None) is not None
            else None
        ),
        "control_interface": "body_velocity",
        "state_definition": list(POSITION_STATE_FIELDS),
        "physical_geometry_status": "pending_measurement",
        "protocol": {
            "frame_header": f"0x{STM32_FRAME_HEADER:02X}",
            "frame_tail": f"0x{STM32_FRAME_TAIL:02X}",
            "checksum": "xor",
            "command_bytes": STM32_COMMAND_SIZE,
            "telemetry_bytes": STM32_TELEMETRY_SIZE,
            "command_quantization_mps_radps": 1.0e-3,
            "accel_ratio": STM32_ACCELERATOR_RATIO,
            "gyro_ratio": STM32_GYROSCOPE_RATIO,
            "baudrate": args.baud,
        },
        "schedule": {
            "file": schedule_path.name,
            "sha256": sha256_file(schedule_path),
            "motion_requested": motion_requested,
            "source": schedule_source,
        },
        "map": map_metadata,
        "safety_record": {
            "file": args.safety_record.resolve().as_posix(),
            "sha256": sha256_file(args.safety_record.resolve()),
        }
        if safety
        else None,
        "source": source_metadata(),
        "samples": {
            "telemetry": telemetry_samples,
            "commands": sequence + 1,
            "decoder_errors": int(getattr(source, "errors", 0)),
        },
        "files": file_hashes(output),
    }
    capture_path = output / "capture.json"
    capture_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest = {
        **metadata,
        "schema": "cca-direct-stm-manifest-v1",
        "capture_json_sha256": sha256_file(capture_path),
        "files": {**file_hashes(output), capture_path.name: sha256_file(capture_path)},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": output.as_posix(), "status": metadata["capture_status"], "telemetry_samples": telemetry_samples}, indent=2))
    return exit_code


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Direct no-ROS STM32 body-velocity experiment recorder")
    root.add_argument("--port", required=True)
    root.add_argument("--baud", type=int, default=115200)
    root.add_argument("--timeout-s", type=float, default=0.1)
    root.add_argument("--mode", type=int, default=0)
    root.add_argument("--output", type=Path, required=True)
    root.add_argument("--duration-s", type=float, required=True)
    root.add_argument("--period-s", type=float, default=0.05)
    root.add_argument("--schedule", type=Path)
    root.add_argument("--pattern", choices=("observe", "forward", "lateral", "rotate", "square"), default="observe")
    root.add_argument("--speed-mps", type=float, default=0.03)
    root.add_argument("--angular-radps", type=float, default=0.15)
    root.add_argument("--allow-actuation", action="store_true")
    root.add_argument("--safety-record", type=Path)
    root.add_argument("--operator", required=True)
    root.add_argument("--firmware-id", required=True)
    root.add_argument("--map-json", type=Path)
    root.set_defaults(handler=run)
    return root


def main() -> int:
    args = parser().parse_args()
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
