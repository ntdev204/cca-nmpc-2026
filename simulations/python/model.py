from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


POSITION_CONTROL_MODE = "position_state"
POSITION_CONTROL_INTERFACE = "body_velocity"
POSITION_STATE_SYMBOLS = ("x", "y", "theta", "vx", "vy", "omega")
POSITION_COMMAND_SYMBOLS = ("vx_cmd", "vy_cmd", "omega_cmd")
POSITION_STATE_FIELDS = (
    "x_m",
    "y_m",
    "theta_rad",
    "vx_mps",
    "vy_mps",
    "omega_radps",
)
POSITION_COMMAND_FIELDS = ("vx_cmd_mps", "vy_cmd_mps", "omega_cmd_radps")


def position_step(
    state: NDArray[np.float64],
    command: NDArray[np.float64],
    dt_s: float,
    velocity_time_constant_s: float = 0.08,
) -> NDArray[np.float64]:
    state = np.asarray(state, dtype=np.float64)
    command = np.asarray(command, dtype=np.float64)
    if state.shape != (6,) or command.shape != (3,):
        raise ValueError("state and command shapes must be (6,) and (3,)")
    if not np.isfinite(state).all() or not np.isfinite(command).all():
        raise ValueError("state and command must be finite")
    if dt_s <= 0.0 or velocity_time_constant_s <= 0.0:
        raise ValueError("time parameters must be positive")
    blend = float(np.clip(dt_s / velocity_time_constant_s, 0.0, 1.0))
    velocity = state[3:] + blend * (command - state[3:])
    cosine = float(np.cos(state[2]))
    sine = float(np.sin(state[2]))
    pose_rate = np.asarray(
        (
            cosine * velocity[0] - sine * velocity[1],
            sine * velocity[0] + cosine * velocity[1],
            velocity[2],
        ),
        dtype=np.float64,
    )
    result = state.copy()
    result[:3] += dt_s * pose_rate
    result[3:] = velocity
    result[2] = float(np.arctan2(np.sin(result[2]), np.cos(result[2])))
    return result


def wheel_speeds(
    command: NDArray[np.float64],
    wheel_radius_m: float,
    half_length_m: float,
    half_width_m: float,
) -> NDArray[np.float64]:
    command = np.asarray(command, dtype=np.float64)
    if command.shape != (3,):
        raise ValueError("command shape must be (3,)")
    if min(wheel_radius_m, half_length_m, half_width_m) <= 0.0:
        raise ValueError("Mecanum dimensions must be positive")
    arm = half_length_m + half_width_m
    mixer = np.asarray(
        (
            (1.0, -1.0, -arm),
            (1.0, 1.0, arm),
            (1.0, 1.0, -arm),
            (1.0, -1.0, arm),
        ),
        dtype=np.float64,
    )
    return mixer @ command / wheel_radius_m


def jacobian(
    state: NDArray[np.float64],
    command: NDArray[np.float64],
    dt_s: float,
    velocity_time_constant_s: float = 0.08,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    state = np.asarray(state, dtype=np.float64)
    command = np.asarray(command, dtype=np.float64)
    blend = float(np.clip(dt_s / velocity_time_constant_s, 0.0, 1.0))
    decay = 1.0 - blend
    cosine = float(np.cos(state[2]))
    sine = float(np.sin(state[2]))
    transform = np.asarray(
        ((cosine, -sine, 0.0), (sine, cosine, 0.0), (0.0, 0.0, 1.0)),
        dtype=np.float64,
    )
    derivative = np.asarray(
        ((-sine, -cosine, 0.0), (cosine, -sine, 0.0), (0.0, 0.0, 0.0)),
        dtype=np.float64,
    )
    next_velocity = decay * state[3:] + blend * command
    state_matrix = np.block(
        [
            [np.eye(3), dt_s * decay * transform],
            [np.zeros((3, 3)), decay * np.eye(3)],
        ]
    )
    state_matrix[:3, 2] += dt_s * derivative @ next_velocity
    input_matrix = np.vstack((dt_s * blend * transform, blend * np.eye(3)))
    return state_matrix, input_matrix


def rollout(
    initial_state: NDArray[np.float64],
    commands: NDArray[np.float64],
    dt_s: float,
    velocity_time_constant_s: float = 0.08,
) -> NDArray[np.float64]:
    commands = np.asarray(commands, dtype=np.float64)
    if commands.ndim != 2 or commands.shape[1] != 3:
        raise ValueError("commands must have shape [N,3]")
    states = np.empty((len(commands) + 1, 6), dtype=np.float64)
    states[0] = np.asarray(initial_state, dtype=np.float64)
    for index, command in enumerate(commands):
        states[index + 1] = position_step(
            states[index], command, dt_s, velocity_time_constant_s
        )
    return states


def reference_residual(
    states: NDArray[np.float64],
    commands: NDArray[np.float64],
    dt_s: float,
    velocity_time_constant_s: float = 0.08,
) -> float:
    states = np.asarray(states, dtype=np.float64)
    commands = np.asarray(commands, dtype=np.float64)
    if states.shape != (len(commands) + 1, 6):
        raise ValueError("reference dimensions are inconsistent")
    predicted = rollout(states[0], commands, dt_s, velocity_time_constant_s)
    return float(np.max(np.abs(predicted - states)))
