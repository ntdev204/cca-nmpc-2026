from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def _finite(name: str, value: NDArray[np.generic]) -> None:
    if not np.isfinite(value).all():
        raise ValueError(f"{name} must contain only finite values")


@dataclass(frozen=True)
class ContextEvent:
    track_id: int
    timestamp_ns: int
    phi: float
    features: Mapping[str, float]
    detector_confidence: float
    calibration_valid: bool

    def __post_init__(self) -> None:
        if self.track_id < 0 or self.timestamp_ns < 0:
            raise ValueError("invalid context identity or timestamp")
        if not 0.0 <= self.phi <= 1.0:
            raise ValueError("phi must lie in [0, 1]")
        if not 0.0 <= self.detector_confidence <= 1.0:
            raise ValueError("detector confidence must lie in [0, 1]")
        if any(not np.isfinite(value) for value in self.features.values()):
            raise ValueError("context features must be finite")


@dataclass(frozen=True)
class HumanObservation:
    timestamp_ns: int
    frame_id: str
    position_xy: FloatArray
    covariance_xy: FloatArray
    detector_confidence: float
    lidar_point_count: int

    def __post_init__(self) -> None:
        position = np.asarray(self.position_xy, dtype=np.float64)
        covariance = np.asarray(self.covariance_xy, dtype=np.float64)
        if self.timestamp_ns < 0 or not self.frame_id or position.shape != (2,):
            raise ValueError("invalid observation timestamp or position")
        if covariance.shape != (2, 2) or self.lidar_point_count < 1:
            raise ValueError("invalid observation covariance or LiDAR support")
        if not 0.0 <= self.detector_confidence <= 1.0:
            raise ValueError("invalid detector confidence")
        _finite("observation position", position)
        _finite("observation covariance", covariance)
        if not np.allclose(covariance, covariance.T, atol=1e-10):
            raise ValueError("observation covariance must be symmetric")
        if np.linalg.eigvalsh(covariance).min() <= 0.0:
            raise ValueError("observation covariance must be positive definite")
        object.__setattr__(self, "position_xy", position)
        object.__setattr__(self, "covariance_xy", covariance)


@dataclass(frozen=True)
class TrackState:
    track_id: int
    timestamp_ns: int
    frame_id: str
    position_xy: FloatArray
    velocity_xy: FloatArray
    covariance_xy: FloatArray
    detector_confidence: float
    measurement_age_ns: int
    hits: int

    def __post_init__(self) -> None:
        position = np.asarray(self.position_xy, dtype=np.float64)
        velocity = np.asarray(self.velocity_xy, dtype=np.float64)
        covariance = np.asarray(self.covariance_xy, dtype=np.float64)
        if min(self.track_id, self.timestamp_ns, self.measurement_age_ns) < 0:
            raise ValueError("invalid track identity or timing")
        if not self.frame_id or position.shape != (2,) or velocity.shape != (2,):
            raise ValueError("invalid track frame, position or velocity")
        if covariance.shape != (2, 2) or self.hits < 1:
            raise ValueError("invalid track covariance or hit count")
        if not 0.0 <= self.detector_confidence <= 1.0:
            raise ValueError("invalid track confidence")
        _finite("track position", position)
        _finite("track velocity", velocity)
        _finite("track covariance", covariance)
        if not np.allclose(covariance, covariance.T, atol=1e-10):
            raise ValueError("track covariance must be symmetric")
        if np.linalg.eigvalsh(covariance).min() <= 0.0:
            raise ValueError("track covariance must be positive definite")
        object.__setattr__(self, "position_xy", position)
        object.__setattr__(self, "velocity_xy", velocity)
        object.__setattr__(self, "covariance_xy", covariance)
