"""Short-history human heading contracts and estimation.

The estimator deliberately returns a local direction, not a long-horizon human
trajectory.  It is usable with image-plane or calibrated robot-local positions;
the caller records the coordinate frame and units in the observation.
"""

from __future__ import annotations

from dataclasses import dataclass
import string

import numpy as np
from numpy.typing import NDArray

from .contracts import FloatArray, _finite


@dataclass(frozen=True)
class HumanHeadingObservation:
    """One immutable heading observation consumed by CCA and local replanning."""

    timestamp_ns: int
    frame_id: str
    track_id: int
    position_xy: FloatArray
    heading_unit: FloatArray
    speed_per_s: float
    heading_valid: bool
    confidence: float
    sample_count: int
    coordinate_units: str
    source_sha256: str

    def __post_init__(self) -> None:
        position = np.asarray(self.position_xy, dtype=np.float64)
        heading = np.asarray(self.heading_unit, dtype=np.float64)
        if self.timestamp_ns < 0 or self.track_id < 0 or self.sample_count < 1:
            raise ValueError("invalid heading identity, timestamp or sample count")
        if not self.frame_id or not self.coordinate_units:
            raise ValueError("frame_id and coordinate_units are required")
        if position.shape != (2,) or heading.shape != (2,):
            raise ValueError("position_xy and heading_unit must have shape (2,)")
        _finite("heading position", position)
        _finite("heading vector", heading)
        if not np.isfinite(self.speed_per_s) or self.speed_per_s < 0.0:
            raise ValueError("speed_per_s must be finite and nonnegative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("heading confidence must lie in [0, 1]")
        if len(self.source_sha256) != 64 or any(
            character not in string.hexdigits for character in self.source_sha256
        ):
            raise ValueError("source_sha256 must be a SHA-256 hex digest")
        heading_norm = float(np.linalg.norm(heading))
        if self.heading_valid:
            if self.speed_per_s <= 0.0 or not np.isclose(heading_norm, 1.0, atol=1e-6):
                raise ValueError("valid heading requires positive speed and unit vector")
        elif heading_norm > 1e-9 or self.speed_per_s > 1e-9:
            raise ValueError("invalid heading must not carry a nonzero direction or speed")
        object.__setattr__(self, "position_xy", position)
        object.__setattr__(self, "heading_unit", heading)


def estimate_heading_observation(
    positions_xy: NDArray[np.floating],
    timestamps_ns: NDArray[np.integer],
    *,
    track_id: int,
    frame_id: str,
    source_sha256: str,
    detector_confidence: float,
    coordinate_units: str = "unknown",
    smoothing_window: int = 4,
    min_speed_per_s: float = 1.0e-3,
    max_gap_ns: int = 500_000_000,
) -> HumanHeadingObservation:
    """Estimate the current direction from a short, causal history.

    A median of the most recent finite-difference velocities suppresses one
    noisy detection.  Stationary, undersampled and stale histories return an
    explicit invalid observation rather than an invented heading.
    """

    positions = np.asarray(positions_xy, dtype=np.float64)
    timestamps = np.asarray(timestamps_ns, dtype=np.int64)
    if positions.ndim != 2 or positions.shape[1:] != (2,) or len(positions) < 2:
        raise ValueError("positions_xy must have shape [N, 2] with N >= 2")
    if timestamps.shape != (len(positions),):
        raise ValueError("timestamps_ns must have shape [N]")
    if not np.isfinite(positions).all() or np.any(np.diff(timestamps) <= 0):
        raise ValueError("positions must be finite and timestamps strictly increasing")
    if smoothing_window < 1 or min_speed_per_s < 0.0 or max_gap_ns <= 0:
        raise ValueError("invalid heading estimator settings")
    gaps = np.diff(timestamps)
    velocities = np.diff(positions, axis=0) / (gaps[:, None] / 1.0e9)
    count = min(int(smoothing_window), len(velocities))
    velocity = np.median(velocities[-count:], axis=0)
    speed = float(np.linalg.norm(velocity))
    current_position = positions[-1]
    current_timestamp = int(timestamps[-1])
    valid = bool(gaps[-1] <= max_gap_ns and speed >= min_speed_per_s)
    if valid:
        heading = velocity / speed
        confidence = float(
            np.clip(detector_confidence, 0.0, 1.0)
            * min(1.0, count / max(1.0, float(smoothing_window)))
        )
        reported_speed = speed
    else:
        heading = np.zeros(2, dtype=np.float64)
        confidence = 0.0
        reported_speed = 0.0
    return HumanHeadingObservation(
        timestamp_ns=current_timestamp,
        frame_id=frame_id,
        track_id=track_id,
        position_xy=current_position,
        heading_unit=heading,
        speed_per_s=reported_speed,
        heading_valid=valid,
        confidence=confidence,
        sample_count=len(positions),
        coordinate_units=coordinate_units,
        source_sha256=source_sha256,
    )
