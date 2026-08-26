from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

REFERENCE_FIELDS = (
    "time_s",
    "x_m",
    "y_m",
    "theta_rad",
    "vx_mps",
    "vy_mps",
    "omega_radps",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_reference(path: Path) -> np.ndarray:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or tuple(rows[0]) != REFERENCE_FIELDS:
        raise ValueError("CCA reference has an invalid column contract")
    values = np.asarray(
        [[float(row[field]) for field in REFERENCE_FIELDS] for row in rows],
        dtype=np.float64,
    )
    if values.ndim != 2 or values.shape[1] != 7 or not np.isfinite(values).all():
        raise ValueError("CCA reference contains invalid values")
    if np.any(np.diff(values[:, 0]) <= 0.0):
        raise ValueError("CCA reference time must be strictly increasing")
    return values


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_sil(
    reference_path: Path,
    output: Path,
    scenario: str,
    steps: int | None,
    *,
    dt_s: float = 0.10,
    horizon: int = 20,
) -> dict[str, object]:
    from hardware import encode_stm32_velocity_command
    from runtime.controller import CompiledController
    from simulations.python.model import position_step, wheel_speeds
    from simulations.python.study import scenario_package

    reference = _read_reference(reference_path)
    package = scenario_package(scenario)
    count = min(len(reference) - 1, len(package.observations))
    if steps is not None:
        count = min(count, steps)
    if count < 1:
        raise ValueError("SIL run requires at least one reference transition")
    output.mkdir(parents=True, exist_ok=True)
    controller = CompiledController(
        "nmpc",
        dt_s,
        horizon=horizon,
        deadline_ms=100.0,
        robot_radius_m=0.20,
        human_radius_m=0.34,
    )
    state = np.asarray(reference[0, 1:], dtype=np.float64)
    previous = np.zeros(3, dtype=np.float64)
    state_rows: list[dict[str, object]] = []
    reference_rows: list[dict[str, object]] = []
    control_rows: list[dict[str, object]] = []
    context_rows: list[dict[str, object]] = []
    constraint_rows: list[dict[str, object]] = []
    events: list[dict[str, object]] = []
    started = time.perf_counter()
    for index in range(count):
        window = np.zeros((6, horizon + 1), dtype=np.float64)
        stop = min(index + horizon + 1, len(reference))
        available = reference[index:stop, 1:]
        window[:, : len(available)] = available.T
        if len(available) < horizon + 1:
            window[:, len(available) :] = available[-1:, :].T
        current = reference[index]
        observation = package.observations[min(index, len(package.observations) - 1)]
        speed = float(np.linalg.norm(observation.feature))
        if not observation.valid or speed < 1.0e-6:
            direction = "unknown" if observation.valid else "invalid"
        elif abs(observation.feature[0]) >= abs(observation.feature[1]):
            direction = "forward" if observation.feature[0] >= 0.0 else "backward"
        else:
            direction = "right" if observation.feature[1] >= 0.0 else "left"
        result = controller.command(state, window, previous)
        command = result.first_command_mps.copy()
        wheels = wheel_speeds(command, 0.05, 0.20, 0.20)
        stm_frame = encode_stm32_velocity_command(*command)
        t_ns = int(round(float(current[0]) * 1.0e9))
        state_rows.append(
            {
                "t_ns": t_ns,
                "x_m": state[0],
                "y_m": state[1],
                "yaw_rad": state[2],
                "vx_mps": state[3],
                "vy_mps": state[4],
                "wz_radps": state[5],
            }
        )
        reference_rows.append(
            {
                "t_ns": t_ns,
                "x_m": current[1],
                "y_m": current[2],
                "theta_rad": current[3],
                "vx_mps": current[4],
                "vy_mps": current[5],
                "omega_radps": current[6],
                "local_path_id": "cca:P:0",
            }
        )
        control_rows.append(
            {
                "t_ns": t_ns,
                "vx_cmd_mps": command[0],
                "vy_cmd_mps": command[1],
                "wz_cmd_radps": command[2],
                "wheel_1_radps": wheels[0],
                "wheel_2_radps": wheels[1],
                "wheel_3_radps": wheels[2],
                "wheel_4_radps": wheels[3],
                "feasible": not result.deadline_missed,
                "solve_ms": result.solve_time_ms,
                "constraint_violation": result.maximum_constraint_violation,
                "fallback_source": "none",
                "stm_command_hex": stm_frame.hex(),
            }
        )
        context_rows.append(
            {
                "t_ns": t_ns,
                "position_x_m": observation.position[0],
                "position_y_m": observation.position[1],
                "speed_mps": speed,
                "direction": direction,
                "confidence": 1.0 if observation.valid else 0.0,
                "context_valid": observation.valid,
            }
        )
        constraint_rows.append(
            {
                "t_ns": t_ns,
                "maximum_constraint_violation": result.maximum_constraint_violation,
                "terminal_ratio": "",
                "lyapunov_residual": "",
                "deadline_missed": result.deadline_missed,
            }
        )
        events.append(
            {
                "t_ns": t_ns,
                "event_type": "sil_nmpc_step",
                "solve_ms": result.solve_time_ms,
                "status": result.status,
            }
        )
        state = position_step(state, command, dt_s)
        previous = command
    state_rows.append(
        {
            "t_ns": int(round(float(reference[count, 0]) * 1.0e9)),
            "x_m": state[0],
            "y_m": state[1],
            "yaw_rad": state[2],
            "vx_mps": state[3],
            "vy_mps": state[4],
            "wz_radps": state[5],
        }
    )
    _write_csv(output / "robot_state.csv", tuple(state_rows[0]), state_rows)
    _write_csv(output / "reference.csv", tuple(reference_rows[0]), reference_rows)
    _write_csv(output / "control.csv", tuple(control_rows[0]), control_rows)
    _write_csv(output / "context.csv", tuple(context_rows[0]), context_rows)
    _write_csv(output / "constraints.csv", tuple(constraint_rows[0]), constraint_rows)
    _write_csv(output / "events.csv", tuple(events[0]), events)
    (output / "map.json").write_text(
        json.dumps(
            {
                "schema": "cca-sil-map-v1",
                "frame_id": "map",
                "resolution_m": 0.02,
                "width": 1,
                "height": 1,
                "origin": [0.0, 0.0, 0.0],
                "occupancy": [0],
                "global_path_fixed": True,
                "obstacles": package.obstacles.tolist(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    manifest = {
        "schema": "cca-sil-run-v1",
        "status": "software-in-the-loop",
        "evidence_admissible": False,
        "capture_source": "sil",
        "hardware_run": False,
        "hardware_state": "inactive",
        "ros_enabled": False,
        "sensor_adapters": {"camera": "Astra-S adapter contract", "lidar": "N10P adapter contract"},
        "stm_transport": "encode_stm32_velocity_command; transmit disabled",
        "controller": "C++ NMPC runtime",
        "state_definition": ["x_m", "y_m", "theta_rad", "vx_mps", "vy_mps", "omega_radps"],
        "control_interface": "body_velocity",
        "scenario": scenario,
        "reference_sha256": _sha256(reference_path),
        "steps": count,
        "elapsed_s": time.perf_counter() - started,
        "files": [
            "robot_state.csv", "reference.csv", "control.csv", "context.csv",
            "constraints.csv", "events.csv", "map.json",
        ],
        "terminal_ratio_available": False,
        "lyapunov_residual_available": False,
    }
    (output / "run.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the non-hardware CCA--NMPC SIL harness")
    parser.add_argument(
        "--reference",
        type=Path,
        default=Path("simulations/results/cca_contract/cca_reference.csv"),
    )
    parser.add_argument("--output", type=Path, default=Path("experiments/runs/sil-latest"))
    parser.add_argument("--scenario", default="corridor")
    parser.add_argument("--steps", type=int)
    args = parser.parse_args()
    result = run_sil(args.reference, args.output, args.scenario, args.steps)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
