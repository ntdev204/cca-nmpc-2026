"""Generate context-aware local robot paths without changing the global path.

This module evaluates the person's current footprint on the map. The direction
label selects the footprint orientation; CCA-NMPC's internal future prediction
is kept in its chance-row interface and is not generated or drawn here. The
global path is owned by ``FixedGlobalLocalPath`` and remains immutable.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from numpy.typing import NDArray

from ai.heading import HumanHeadingObservation



@dataclass(frozen=True)
class ContextReplanDecision:
    replan: bool
    reasons: tuple[str, ...]
    footprint_clearance_m: float
    heading_change_rad: float


def _dense_path(path_xy: NDArray[np.floating], spacing_m: float = 0.05) -> np.ndarray:
    path = np.asarray(path_xy, dtype=np.float64)
    points = [path[0]]
    for start, end in zip(path[:-1], path[1:], strict=True):
        delta = end - start
        length = float(np.linalg.norm(delta))
        count = max(1, int(np.ceil(length / spacing_m)))
        points.extend(start + delta * fraction for fraction in np.linspace(0.0, 1.0, count + 1)[1:])
    return np.asarray(points, dtype=np.float64)


def context_footprint_points(
    observation: HumanHeadingObservation,
    *,
    lateral_radius_m: float = 0.60,
    longitudinal_radius_m: float = 0.95,
    samples: int = 32,
) -> NDArray[np.float64]:
    """Return the latest observed oriented footprint for map scoring."""

    if not observation.heading_valid:
        return np.empty((0, 2), dtype=np.float64)
    if min(lateral_radius_m, longitudinal_radius_m, samples) <= 0:
        raise ValueError("footprint dimensions and sample count must be positive")
    heading = np.asarray(observation.heading_unit, dtype=np.float64)
    norm = float(np.linalg.norm(heading))
    if norm <= 1.0e-12:
        return np.empty((0, 2), dtype=np.float64)
    heading = heading / norm
    normal = np.asarray((-heading[1], heading[0]), dtype=np.float64)
    angles = np.linspace(0.0, 2.0 * math.pi, int(samples), endpoint=False)
    boundary = observation.position_xy[None, :] + (
        np.cos(angles)[:, None] * longitudinal_radius_m * heading[None, :]
        + np.sin(angles)[:, None] * lateral_radius_m * normal[None, :]
    )
    return np.vstack((observation.position_xy[None, :], boundary))


def path_clearance_to_footprint(
    path_xy: NDArray[np.floating], footprint_xy: NDArray[np.floating]
) -> float:
    if len(footprint_xy) == 0:
        return float("inf")
    dense = _dense_path(path_xy)
    return float(np.linalg.norm(dense[:, None, :] - footprint_xy[None, :, :], axis=2).min())


def evaluate_context_replan(
    current_path_xy: NDArray[np.floating],
    observation: HumanHeadingObservation,
    *,
    now_ns: int,
    previous_heading_unit: NDArray[np.floating] | None = None,
    safe_distance_m: float = 0.20,
    heading_change_threshold_rad: float = 0.60,
) -> ContextReplanDecision:
    """Trigger local replacement from the latest observed context footprint."""

    if now_ns < observation.timestamp_ns:
        raise ValueError("now_ns precedes context observation")
    if safe_distance_m < 0.0 or heading_change_threshold_rad < 0.0:
        raise ValueError("replan thresholds must be nonnegative")
    reasons: list[str] = []
    footprint = context_footprint_points(observation)
    clearance = path_clearance_to_footprint(current_path_xy, footprint)
    if not observation.heading_valid:
        reasons.append("invalid_direction_context")
    if clearance < safe_distance_m:
        reasons.append("context_conflict")
    heading_change = 0.0
    if previous_heading_unit is not None and observation.heading_valid:
        previous = np.asarray(previous_heading_unit, dtype=np.float64)
        if previous.shape != (2,) or not np.isfinite(previous).all():
            raise ValueError("previous_heading_unit must have shape (2,) and be finite")
        previous_norm = float(np.linalg.norm(previous))
        if previous_norm > 1.0e-9:
            current = observation.heading_unit / max(float(np.linalg.norm(observation.heading_unit)), 1.0e-12)
            heading_change = float(math.acos(np.clip(np.dot(previous / previous_norm, current), -1.0, 1.0)))
            if heading_change >= heading_change_threshold_rad:
                reasons.append("direction_change")
    return ContextReplanDecision(
        replan=bool(reasons) and observation.heading_valid,
        reasons=tuple(dict.fromkeys(reasons)),
        footprint_clearance_m=clearance,
        heading_change_rad=heading_change,
    )


def generate_context_local_detour(
    robot_position_xy: NDArray[np.floating],
    global_goal_xy: NDArray[np.floating],
    observation: HumanHeadingObservation,
    *,
    side: int,
    lateral_offset_m: float = 1.10,
    longitudinal_offset_m: float = 0.85,
) -> NDArray[np.float64]:
    """Generate a robot local path around the latest observed context footprint."""

    base = np.asarray((robot_position_xy, global_goal_xy), dtype=np.float64)
    return replan_around_heading(
        base,
        observation,
        side=side,
        lateral_offset=lateral_offset_m,
        longitudinal_offset=longitudinal_offset_m,
    )


@dataclass(frozen=True)
class FixedGlobalLocalPath:
    global_path_xy: NDArray[np.float64]
    local_path_xy: NDArray[np.float64]
    local_generation_count: int = 0

    def __post_init__(self) -> None:
        global_path = np.asarray(self.global_path_xy, dtype=np.float64)
        local_path = np.asarray(self.local_path_xy, dtype=np.float64)
        if global_path.ndim != 2 or global_path.shape[1:] != (2,) or len(global_path) < 2:
            raise ValueError("global_path_xy must have shape [N,2] with N >= 2")
        if local_path.ndim != 2 or local_path.shape[1:] != (2,) or len(local_path) < 2:
            raise ValueError("local_path_xy must have shape [N,2] with N >= 2")
        if not np.isfinite(global_path).all() or not np.isfinite(local_path).all():
            raise ValueError("global and local paths must be finite")
        if self.local_generation_count < 0:
            raise ValueError("local_generation_count must be nonnegative")
        object.__setattr__(self, "global_path_xy", global_path.copy())
        object.__setattr__(self, "local_path_xy", local_path.copy())

    @classmethod
    def from_global(cls, global_path_xy: NDArray[np.floating]) -> "FixedGlobalLocalPath":
        path = np.asarray(global_path_xy, dtype=np.float64)
        return cls(path, path, 0)

    def generate_local_detour(
        self,
        robot_position_xy: NDArray[np.floating],
        observation: HumanHeadingObservation,
        *,
        side: int,
        lateral_offset: float = 1.0,
        longitudinal_offset: float = 0.9,
    ) -> "FixedGlobalLocalPath":
        robot = np.asarray(robot_position_xy, dtype=np.float64)
        if robot.shape != (2,) or not np.isfinite(robot).all():
            raise ValueError("robot_position_xy must have shape (2,) and be finite")
        local_base = np.asarray((robot, self.global_path_xy[-1]), dtype=np.float64)
        local_path = replan_around_heading(
            local_base,
            observation,
            side=side,
            lateral_offset=lateral_offset,
            longitudinal_offset=longitudinal_offset,
        )
        return FixedGlobalLocalPath(
            self.global_path_xy,
            local_path,
            self.local_generation_count + 1,
        )


def replan_around_heading(
    current_path_xy: NDArray[np.floating],
    observation: HumanHeadingObservation,
    *,
    side: int,
    lateral_offset: float = 1.0,
    longitudinal_offset: float = 0.9,
) -> NDArray[np.float64]:
    path = np.asarray(current_path_xy, dtype=np.float64)
    if path.ndim != 2 or path.shape[1:] != (2,) or len(path) < 2:
        raise ValueError("current_path_xy must have shape [N, 2] with N >= 2")
    if (
        not observation.heading_valid
        or side not in (-1, 1)
        or lateral_offset <= 0.0
        or longitudinal_offset <= 0.0
    ):
        raise ValueError("valid heading, side in {-1,+1}, and positive offsets are required")
    nearest = int(np.argmin(np.linalg.norm(path - observation.position_xy[None, :], axis=1)))
    if nearest == 0:
        tangent = path[1] - path[0]
    elif nearest == len(path) - 1:
        tangent = path[-1] - path[-2]
    else:
        tangent = path[nearest + 1] - path[nearest - 1]
    tangent_norm = float(np.linalg.norm(tangent))
    if tangent_norm <= 1.0e-12:
        tangent = observation.heading_unit
        tangent_norm = float(np.linalg.norm(tangent))
    tangent = tangent / tangent_norm
    normal = np.asarray((-tangent[1], tangent[0]))
    lateral = float(side) * lateral_offset * normal
    before = observation.position_xy - longitudinal_offset * tangent + lateral
    after = observation.position_xy + longitudinal_offset * tangent + lateral
    insert_at = min(len(path), nearest + 1)
    return np.insert(path, insert_at, np.vstack((before, after)), axis=0)
