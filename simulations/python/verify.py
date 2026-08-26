from __future__ import annotations

import argparse
import json

import numpy as np

from model import (
    jacobian,
    position_step,
    reference_residual,
    rollout,
    wheel_speeds,
)


def run() -> dict[str, object]:
    dt_s = 0.05
    tau_s = 0.08
    command = np.asarray((0.3, 0.1, 0.2), dtype=np.float64)
    state = np.zeros(6, dtype=np.float64)
    next_state = position_step(state, command, dt_s, tau_s)
    commands = np.tile(command, (20, 1))
    states = rollout(state, commands, dt_s, tau_s)
    residual = reference_residual(states, commands, dt_s, tau_s)
    wheels = wheel_speeds(command, 0.05, 0.20, 0.20)
    state_matrix, input_matrix = jacobian(state, command, dt_s, tau_s)
    return {
        "finite_state": bool(np.isfinite(next_state).all()),
        "reference_residual": residual,
        "wheel_peak_radps": float(np.max(np.abs(wheels))),
        "state_order_ok": bool(next_state.shape == (6,)),
        "input_order_ok": bool(command.shape == (3,)),
        "jacobian_shape_ok": bool(
            state_matrix.shape == (6, 6) and input_matrix.shape == (6, 3)
        ),
    }


def parity_case(
    dt_s: float,
    tau_s: float,
    state: tuple[float, ...],
    command: tuple[float, ...],
) -> dict[str, object]:
    state_array = np.asarray(state, dtype=np.float64)
    command_array = np.asarray(command, dtype=np.float64)
    next_state = position_step(state_array, command_array, dt_s, tau_s)
    state_matrix, input_matrix = jacobian(
        state_array, command_array, dt_s, tau_s
    )
    wheels = wheel_speeds(command_array, 0.05, 0.20, 0.20)
    return {
        "dt": dt_s,
        "velocityTimeConstant": tau_s,
        "state": state_array.tolist(),
        "command": command_array.tolist(),
        "nextState": next_state.tolist(),
        "A": state_matrix.tolist(),
        "B": input_matrix.tolist(),
        "wheels": wheels.tolist(),
    }


def parity_vectors() -> dict[str, object]:
    cases = [
        parity_case(
            0.07,
            0.11,
            (0.31, -0.22, 0.47, 0.12, -0.08, 0.19),
            (-0.25, 0.34, -0.41),
        ),
        parity_case(
            0.13,
            0.08,
            (-0.14, 0.28, np.pi - 1.0e-7, -0.09, 0.16, -0.22),
            (0.42, -0.31, 0.37),
        ),
    ]
    return {"cases": cases}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vectors", action="store_true")
    args = parser.parse_args()
    if args.vectors:
        print(json.dumps(parity_vectors(), separators=(",", ":")))
        return 0
    result = run()
    passed = (
        result["finite_state"]
        and result["state_order_ok"]
        and result["input_order_ok"]
        and result["jacobian_shape_ok"]
        and result["reference_residual"] <= 1.0e-12
    )
    print(json.dumps({"passed": bool(passed), **result}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
