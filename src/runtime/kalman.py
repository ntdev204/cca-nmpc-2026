from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


STATE_SIZE = 6
VELOCITY_MEASUREMENT_SIZE = 3
STATE_FIELDS = ("x_m", "y_m", "theta_rad", "vx_mps", "vy_mps", "omega_radps")


def wrap_angle(value: float) -> float:
    return math.atan2(math.sin(float(value)), math.cos(float(value)))


@dataclass(frozen=True)
class KalmanConfig:
    position_process_std_m: float = 0.01
    heading_process_std_rad: float = 0.02
    velocity_process_std_mps: float = 0.20
    omega_process_std_radps: float = 0.20
    velocity_measurement_std_mps: float = 0.03
    omega_measurement_std_radps: float = 0.04
    initial_position_std_m: float = 0.05
    initial_heading_std_rad: float = 0.10
    initial_velocity_std_mps: float = 0.20
    initial_omega_std_radps: float = 0.20
    max_dt_s: float = 0.25

    def __post_init__(self) -> None:
        values = (
            self.position_process_std_m,
            self.heading_process_std_rad,
            self.velocity_process_std_mps,
            self.omega_process_std_radps,
            self.velocity_measurement_std_mps,
            self.omega_measurement_std_radps,
            self.initial_position_std_m,
            self.initial_heading_std_rad,
            self.initial_velocity_std_mps,
            self.initial_omega_std_radps,
            self.max_dt_s,
        )
        if not all(math.isfinite(float(value)) and float(value) > 0.0 for value in values):
            raise ValueError("Kalman noise and max_dt_s must be positive and finite")


class SixStateKalman:
    """Extended Kalman filter for the position-state robot contract."""

    measurement_indices = np.array((3, 4, 5), dtype=np.int64)

    def __init__(
        self,
        state: np.ndarray | list[float] | tuple[float, ...] | None = None,
        covariance: np.ndarray | None = None,
        config: KalmanConfig | None = None,
    ) -> None:
        self.config = config or KalmanConfig()
        self._state = np.zeros(STATE_SIZE, dtype=np.float64)
        self._covariance = np.zeros((STATE_SIZE, STATE_SIZE), dtype=np.float64)
        self._last_t_ns: int | None = None
        self._samples = 0
        self.reset(state=state, covariance=covariance)

    @property
    def state(self) -> np.ndarray:
        return self._state.copy()

    @property
    def covariance(self) -> np.ndarray:
        return self._covariance.copy()

    @property
    def last_t_ns(self) -> int | None:
        return self._last_t_ns

    @property
    def samples(self) -> int:
        return self._samples

    @property
    def covariance_trace(self) -> float:
        return float(np.trace(self._covariance))

    @property
    def position_std_m(self) -> float:
        return float(math.sqrt(max(0.0, self._covariance[0, 0] + self._covariance[1, 1])))

    @property
    def heading_std_rad(self) -> float:
        return float(math.sqrt(max(0.0, self._covariance[2, 2])))

    @property
    def velocity_std_mps(self) -> float:
        return float(
            math.sqrt(max(0.0, self._covariance[3, 3] + self._covariance[4, 4]))
        )

    def diagnostics(self) -> dict[str, float | int]:
        return {
            "state_estimator": "six_state_ekf",
            "kalman_cov_trace": self.covariance_trace,
            "kalman_position_std_m": self.position_std_m,
            "kalman_heading_std_rad": self.heading_std_rad,
            "kalman_velocity_std_mps": self.velocity_std_mps,
        }

    def reset(
        self,
        *,
        state: np.ndarray | list[float] | tuple[float, ...] | None = None,
        covariance: np.ndarray | None = None,
        t_ns: int | None = None,
    ) -> None:
        values = np.zeros(STATE_SIZE, dtype=np.float64) if state is None else np.asarray(state, dtype=np.float64)
        if values.shape != (STATE_SIZE,) or not np.isfinite(values).all():
            raise ValueError("Kalman state must have six finite values")
        values = values.copy()
        values[2] = wrap_angle(values[2])
        if covariance is None:
            diagonal = np.array(
                (
                    self.config.initial_position_std_m**2,
                    self.config.initial_position_std_m**2,
                    self.config.initial_heading_std_rad**2,
                    self.config.initial_velocity_std_mps**2,
                    self.config.initial_velocity_std_mps**2,
                    self.config.initial_omega_std_radps**2,
                ),
                dtype=np.float64,
            )
            matrix = np.diag(diagonal)
        else:
            matrix = np.asarray(covariance, dtype=np.float64)
            if matrix.shape != (STATE_SIZE, STATE_SIZE) or not np.isfinite(matrix).all():
                raise ValueError("Kalman covariance must be a finite 6 by 6 matrix")
            matrix = (matrix + matrix.T) * 0.5
            if np.min(np.linalg.eigvalsh(matrix)) < -1.0e-10:
                raise ValueError("Kalman covariance must be positive semidefinite")
        self._state = values
        self._covariance = matrix
        self._last_t_ns = None if t_ns is None else self._timestamp(t_ns)
        self._samples = 0

    @staticmethod
    def _timestamp(t_ns: int) -> int:
        if isinstance(t_ns, bool) or not isinstance(t_ns, (int, np.integer)) or int(t_ns) < 0:
            raise ValueError("Kalman timestamp must be a nonnegative integer")
        return int(t_ns)

    @staticmethod
    def _vector(values: np.ndarray | list[float] | tuple[float, ...], size: int, name: str) -> np.ndarray:
        result = np.asarray(values, dtype=np.float64)
        if result.shape != (size,) or not np.isfinite(result).all():
            raise ValueError(f"Kalman {name} must have {size} finite values")
        return result.copy()

    def _dt(self, t_ns: int) -> float:
        timestamp = self._timestamp(t_ns)
        if self._last_t_ns is None:
            self._last_t_ns = timestamp
            return 0.0
        if timestamp < self._last_t_ns:
            raise ValueError("Kalman timestamps must be monotonic")
        dt = min((timestamp - self._last_t_ns) * 1.0e-9, self.config.max_dt_s)
        self._last_t_ns = timestamp
        return max(0.0, dt)

    def predict(
        self,
        t_ns: int,
        *,
        acceleration_body_mps2: np.ndarray | list[float] | tuple[float, float] | None = None,
        gyro_z_radps: float | None = None,
    ) -> np.ndarray:
        dt = self._dt(t_ns)
        acceleration = None
        if acceleration_body_mps2 is not None:
            acceleration = self._vector(acceleration_body_mps2, 2, "body acceleration")
        gyro = None
        if gyro_z_radps is not None:
            gyro = float(gyro_z_radps)
            if not math.isfinite(gyro):
                raise ValueError("Kalman gyro_z must be finite")
        if dt <= 0.0:
            return self.state
        x, y, theta, vx, vy, omega = self._state
        c, s = math.cos(theta), math.sin(theta)
        self._state[0] = x + dt * (c * vx - s * vy)
        self._state[1] = y + dt * (s * vx + c * vy)
        self._state[2] = wrap_angle(theta + dt * omega)
        if acceleration is not None:
            self._state[3] = vx + dt * float(acceleration[0])
            self._state[4] = vy + dt * float(acceleration[1])
        if gyro is not None:
            self._state[5] = gyro
        jacobian = np.eye(STATE_SIZE, dtype=np.float64)
        jacobian[0, 2] = dt * (-s * vx - c * vy)
        jacobian[0, 3] = dt * c
        jacobian[0, 4] = -dt * s
        jacobian[1, 2] = dt * (c * vx - s * vy)
        jacobian[1, 3] = dt * s
        jacobian[1, 4] = dt * c
        jacobian[2, 5] = dt
        q = np.diag(
            (
                (self.config.position_process_std_m * dt) ** 2,
                (self.config.position_process_std_m * dt) ** 2,
                (self.config.heading_process_std_rad * dt) ** 2,
                (self.config.velocity_process_std_mps * dt) ** 2,
                (self.config.velocity_process_std_mps * dt) ** 2,
                (self.config.omega_process_std_radps * dt) ** 2,
            )
        )
        self._covariance = jacobian @ self._covariance @ jacobian.T + q
        self._covariance = (self._covariance + self._covariance.T) * 0.5
        return self.state

    def update_velocity(
        self,
        velocity_body_mps: np.ndarray | list[float] | tuple[float, float, float],
    ) -> np.ndarray:
        measurement = self._vector(velocity_body_mps, VELOCITY_MEASUREMENT_SIZE, "velocity measurement")
        h = np.zeros((VELOCITY_MEASUREMENT_SIZE, STATE_SIZE), dtype=np.float64)
        h[:, self.measurement_indices] = np.eye(VELOCITY_MEASUREMENT_SIZE)
        innovation = measurement - h @ self._state
        r = np.diag(
            (
                self.config.velocity_measurement_std_mps**2,
                self.config.velocity_measurement_std_mps**2,
                self.config.omega_measurement_std_radps**2,
            )
        )
        innovation_covariance = h @ self._covariance @ h.T + r
        gain = np.linalg.solve(innovation_covariance, h @ self._covariance).T
        identity = np.eye(STATE_SIZE, dtype=np.float64)
        residual = identity - gain @ h
        self._state = self._state + gain @ innovation
        self._state[2] = wrap_angle(self._state[2])
        self._covariance = (
            residual @ self._covariance @ residual.T + gain @ r @ gain.T
        )
        self._covariance = (self._covariance + self._covariance.T) * 0.5
        self._samples += 1
        return self.state

    def step(
        self,
        t_ns: int,
        velocity_body_mps: np.ndarray | list[float] | tuple[float, float, float],
        *,
        acceleration_body_mps2: np.ndarray | list[float] | tuple[float, float] | None = None,
        gyro_z_radps: float | None = None,
    ) -> np.ndarray:
        self.predict(
            t_ns,
            acceleration_body_mps2=acceleration_body_mps2,
            gyro_z_radps=gyro_z_radps,
        )
        return self.update_velocity(velocity_body_mps)


__all__ = ["STATE_FIELDS", "KalmanConfig", "SixStateKalman", "wrap_angle"]
