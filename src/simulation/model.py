from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class NmpcPrediction:
    mean_xy: NDArray[np.float64]
    velocity_xy: NDArray[np.float64]
    relative_covariance_xy: NDArray[np.float64]
    probability: NDArray[np.float64]
    context: NDArray[np.float64]
    nominal_robot_xy: NDArray[np.float64]
    omitted_probability_mass: NDArray[np.float64] = field(default_factory=lambda: np.empty(0, dtype=np.float64))
    human_yaw_rad: NDArray[np.float64] = field(default_factory=lambda: np.empty(0, dtype=np.float64))
    calibration_provenance_sha256: str = ""
    calibration_domain: str = ""
    calibration_tail_verified: bool = False
    frame_time_age_verified: bool = False
    mode_partition_verified: bool = False
    covariance_provenance_verified: bool = False
    geometry_containment_verified: bool = False


POSITION_CONTROL_MODE = "position_state"
POSITION_CONTROL_INTERFACE = "body_velocity"
POSITION_STATE_SYMBOLS = ("x", "y", "theta", "vx", "vy", "omega")
POSITION_COMMAND_SYMBOLS = ("vx_cmd", "vy_cmd", "wz_cmd")
POSITION_STATE_FIELDS = ("x_m", "y_m", "theta_rad", "vx_mps", "vy_mps", "omega_radps")
POSITION_COMMAND_FIELDS = ("vx_cmd_mps", "vy_cmd_mps", "wz_cmd_radps")


def position_state_step(
    state: NDArray[np.float64],
    command: NDArray[np.float64],
    dt_s: float,
    velocity_time_constant_s: float = 0.08,
) -> NDArray[np.float64]:
    state = np.asarray(state, dtype=np.float64)
    command = np.asarray(command, dtype=np.float64)
    if state.shape != (6,) or command.shape != (3,):
        raise ValueError("position-state input must have shapes (6,) and (3,)")
    if not np.isfinite(state).all() or not np.isfinite(command).all():
        raise ValueError("position-state values must be finite")
    if dt_s <= 0.0 or velocity_time_constant_s <= 0.0:
        raise ValueError("sample time and velocity time constant must be positive")
    blend = float(np.clip(dt_s / velocity_time_constant_s, 0.0, 1.0))
    velocity = state[3:6] + blend * (command - state[3:6])
    yaw = float(state[2])
    cosine = float(np.cos(yaw))
    sine = float(np.sin(yaw))
    pose_rate = np.asarray(
        (
            cosine * velocity[0] - sine * velocity[1],
            sine * velocity[0] + cosine * velocity[1],
            velocity[2],
        ),
        dtype=np.float64,
    )
    next_state = state.copy()
    next_state[:3] += dt_s * pose_rate
    next_state[3:] = velocity
    next_state[2] = float(np.arctan2(np.sin(next_state[2]), np.cos(next_state[2])))
    return next_state
