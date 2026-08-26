from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

from hardware import (
    CsvWriters,
    N10P_PROTOCOL_PROFILE,
    N10PSerialSource,
    Stm32SerialSource,
    utc_ns,
    write_runtime_metadata,
)
from runtime.kalman import SixStateKalman


ZERO_COMMAND = (0.0, 0.0, 0.0)
REQUIRED_SAFETY_FIELDS = (
    "approved",
    "emergency_stop_verified",
    "remote_disable_verified",
    "watchdog_verified",
)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _validate_safety(path: Path) -> None:
    payload = _read_json(path)
    record = payload.get("safety") if isinstance(payload.get("safety"), dict) else payload
    missing = [name for name in REQUIRED_SAFETY_FIELDS if record.get(name) is not True]
    if missing:
        raise ValueError("safety record must set true: " + ", ".join(missing))


def _finite(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _write_lidar(writers: CsvWriters, scan: Any, last_t_ns: int) -> int:
    if scan is None or scan.t_ns <= last_t_ns:
        return last_t_ns
    points = [
        [float(point.angle_rad), float(point.range_m), int(point.intensity), int(point.return_id)]
        for point in scan.points
    ]
    writers.write(
        "lidar.csv",
        {"t_ns": scan.t_ns, "point_count": len(points), "points_json": json.dumps(points, separators=(",", ":"))},
    )
    return int(scan.t_ns)


class StmExperiment:
    def __init__(
        self,
        port: str,
        *,
        baudrate: int = 115200,
        timeout_s: float = 0.1,
        mode: int = 0,
        lidar_port: str | None = None,
        lidar_baudrate: int = 460800,
        lidar_timeout_s: float = 0.1,
    ) -> None:
        self.stm = Stm32SerialSource(
            port,
            baudrate=int(baudrate),
            timeout_s=float(timeout_s),
            mode=int(mode),
        )
        self.lidar = (
            N10PSerialSource(
                lidar_port,
                profile=N10P_PROTOCOL_PROFILE,
                baudrate=int(lidar_baudrate),
                timeout_s=float(lidar_timeout_s),
            )
            if lidar_port
            else None
        )
        self.estimator = SixStateKalman()

    def run(
        self,
        *,
        output: Path,
        duration_s: float,
        period_s: float,
        command: tuple[float, float, float] = ZERO_COMMAND,
        allow_actuation: bool = False,
        safety_record: Path | None = None,
        robot_config: Path = Path("configs/hardware_runtime.json"),
        firmware: str = "unspecified",
    ) -> int:
        duration = _finite(duration_s, "duration_s")
        period = _finite(period_s, "period_s")
        if duration <= 0.0 or period <= 0.0:
            raise ValueError("duration_s and period_s must be positive")
        command = tuple(_finite(value, name) for value, name in zip(command, ("vx_mps", "vy_mps", "wz_radps")))
        motion_requested = any(abs(value) > 1.0e-12 for value in command)
        if motion_requested and not allow_actuation:
            raise ValueError("nonzero command requires --allow-actuation")
        if motion_requested:
            if safety_record is None:
                raise ValueError("nonzero command requires --safety-record")
            _validate_safety(safety_record)
        output = output.resolve()
        writers = CsvWriters(output)
        write_runtime_metadata(
            output,
            camera="not_started",
            lidar="N10P" if self.lidar is not None else "not_started",
            firmware=firmware,
            clock="system_time",
            robot_config=robot_config,
            extra={
                "capture_interface": "direct_stm_runtime",
                "transport": "stm32_serial",
                "actuation": "constant_body_velocity" if motion_requested else "zero_velocity_only",
                "lidar_started": self.lidar is not None,
                "safety_record": safety_record.resolve().as_posix() if safety_record else None,
            },
        )
        started_stm = False
        started_lidar = False
        stop_latched = False
        last_state_ns = -1
        last_lidar_ns = -1
        state_samples = 0
        lidar_samples = 0
        command_samples = 0
        event_last = 0
        status = "completed"

        def event(event_type: str, detail: str) -> None:
            nonlocal event_last
            timestamp = max(utc_ns(), event_last + 1)
            event_last = timestamp
            writers.write(
                "events.csv",
                {
                    "t_ns": timestamp,
                    "event_type": event_type,
                    "solve_ms": "",
                    "status_code": "",
                    "sequence": "",
                    "detail": detail,
                },
            )

        start = time.monotonic()
        try:
            event("capture_started", "direct_stm_runtime")
            self.stm.start()
            started_stm = True
            if self.lidar is not None:
                self.lidar.start()
                started_lidar = True
            while time.monotonic() - start < duration:
                telemetry = self.stm.latest
                if telemetry is not None and telemetry.flag_stop:
                    if not stop_latched:
                        event("stm32_stop_flag", "STM32 stop flag asserted")
                    stop_latched = True
                selected = ZERO_COMMAND if stop_latched else command
                self.stm.send_velocity(*selected)
                command_samples += 1
                command_time = self.stm.last_command[0] if self.stm.last_command else utc_ns()
                writers.write(
                    "control.csv",
                    {
                        "t_ns": command_time,
                        "vx_cmd_mps": selected[0],
                        "vy_cmd_mps": selected[1],
                        "wz_cmd_radps": selected[2],
                        "vx_applied_mps": telemetry.vx_mps if telemetry else "",
                        "vy_applied_mps": telemetry.vy_mps if telemetry else "",
                        "wz_applied_radps": telemetry.wz_radps if telemetry else "",
                        "sequence": "",
                        "transport": "stm32_serial",
                    },
                )
                if telemetry is not None and telemetry.t_ns > last_state_ns:
                    state = self.estimator.step(
                        telemetry.t_ns,
                        (telemetry.vx_mps, telemetry.vy_mps, telemetry.wz_radps),
                        acceleration_body_mps2=(telemetry.accel_x_mps2, telemetry.accel_y_mps2),
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
                            **self.estimator.diagnostics(),
                            "transport": "stm32_serial",
                        },
                    )
                    last_state_ns = int(telemetry.t_ns)
                    state_samples += 1
                if self.lidar is not None:
                    previous_lidar_ns = last_lidar_ns
                    last_lidar_ns = _write_lidar(writers, self.lidar.latest, last_lidar_ns)
                    if last_lidar_ns != previous_lidar_ns:
                        lidar_samples += 1
                writers.flush()
                time.sleep(period)
            event("capture_completed", f"states={state_samples},lidar={lidar_samples}")
            return 0
        except KeyboardInterrupt:
            status = "interrupted"
            event("operator_stop", "keyboard interrupt")
            return 130
        except Exception as error:
            status = "failed"
            event("capture_error", f"{type(error).__name__}: {error}")
            raise
        finally:
            if started_stm:
                try:
                    self.stm.send_velocity(*ZERO_COMMAND)
                finally:
                    self.stm.stop()
            if started_lidar:
                self.lidar.stop()
            writers.close()
            metadata_path = output / "capture.json"
            try:
                metadata = _read_json(metadata_path)
                metadata.update(
                    {
                        "capture_status": status,
                        "samples": {
                            "state": state_samples,
                            "lidar": lidar_samples,
                            "commands": command_samples,
                            "decoder_errors": int(getattr(self.stm, "errors", 0)),
                        },
                        "transport_backend": getattr(self.stm, "backend", "unknown"),
                        "transport_library": (
                            self.stm.transport_library.as_posix()
                            if getattr(self.stm, "transport_library", None) is not None
                            else None
                        ),
                    }
                )
                if self.lidar is not None:
                    metadata["lidar_scan_rate_hz"] = self.lidar.scan_rate_hz
                metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            except (OSError, TypeError, ValueError, json.JSONDecodeError):
                pass


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Direct no-ROS STM32 experiment with six-state EKF")
    parser.add_argument("--port", required=True)
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--timeout-s", type=float, default=0.1)
    parser.add_argument("--mode", type=int, default=0)
    parser.add_argument("--lidar-port")
    parser.add_argument("--lidar-baudrate", type=int, default=460800)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration-s", type=float, required=True)
    parser.add_argument("--period-s", type=float, default=0.05)
    parser.add_argument("--vx-mps", type=float, default=0.0)
    parser.add_argument("--vy-mps", type=float, default=0.0)
    parser.add_argument("--wz-radps", type=float, default=0.0)
    parser.add_argument("--allow-actuation", action="store_true")
    parser.add_argument("--safety-record", type=Path)
    parser.add_argument("--robot-config", type=Path, default=Path("configs/hardware_runtime.json"))
    parser.add_argument("--firmware", default="unspecified")
    return parser


def main() -> int:
    args = parser().parse_args()
    runner = StmExperiment(
        args.port,
        baudrate=args.baudrate,
        timeout_s=args.timeout_s,
        mode=args.mode,
        lidar_port=args.lidar_port,
        lidar_baudrate=args.lidar_baudrate,
    )
    return runner.run(
        output=args.output,
        duration_s=args.duration_s,
        period_s=args.period_s,
        command=(args.vx_mps, args.vy_mps, args.wz_radps),
        allow_actuation=args.allow_actuation,
        safety_record=args.safety_record,
        robot_config=args.robot_config,
        firmware=args.firmware,
    )


if __name__ == "__main__":
    raise SystemExit(main())
