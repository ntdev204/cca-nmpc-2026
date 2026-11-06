"""No-ROS 2D LiDAR SLAM: scan-to-map matching, pose graph, and occupancy replay."""
from __future__ import annotations

import json
import math
import time
from array import array
from copy import copy
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np

from hardware import LidarScan


def bresenham(start: tuple[int, int], end: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    x0, y0 = start
    x1, y1 = end
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    error = dx + dy
    cells = []
    while True:
        cells.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return tuple(cells)
        double = 2 * error
        if double >= dy:
            error += dy
            x0 += sx
        if double <= dx:
            error += dx
            y0 += sy


def _wrap(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def _relative(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    c, s = math.cos(a[2]), math.sin(a[2])
    dx, dy = b[0] - a[0], b[1] - a[1]
    return c * dx + s * dy, -s * dx + c * dy, _wrap(b[2] - a[2])


def _compose(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    c, s = math.cos(a[2]), math.sin(a[2])
    return a[0] + c * b[0] - s * b[1], a[1] + s * b[0] + c * b[1], _wrap(a[2] + b[2])


@dataclass
class _Keyframe:
    pose: tuple[float, float, float]
    scan: tuple[tuple[float, float, int], ...]
    t_ns: int
    vx: float
    vy: float
    wz: float
    rays: tuple[tuple[float, float, float, float], ...] | None = None


@dataclass
class _ScanFrame:
    anchor: int
    relative_pose: tuple[float, float, float]
    data: array
    t_ns: int
    vx: float
    vy: float
    wz: float
    scan_index: int
    clear_free: bool = True
    rays: tuple[tuple[float, float, float, float], ...] | None = None


@dataclass(frozen=True)
class _FrozenSubmap:
    anchor: int
    end: int
    hits: frozenset[tuple[int, int]]


@dataclass(frozen=True)
class _MatchResult:
    accepted: bool
    score: float
    inliers: int
    point_count: int
    correction_m: float
    correction_yaw_rad: float
    reason: str
    observability: float | None = None
    competing_poses: tuple[tuple[tuple[float, float, float], float], ...] = ()


class OccupancyMap:
    """Online 2D SLAM kept API-compatible with the existing console.

    Every scan is matched against the current occupancy submap. Keyframes add
    odometry/scan constraints to a pose graph; accepted loop closures trigger
    sparse graph optimization and a complete occupancy replay at corrected poses.
    """

    LOG_ODDS_MIN = -4.0
    LOG_ODDS_MAX = 4.0
    FREE_THRESHOLD = -0.7
    OCCUPIED_THRESHOLD = 0.75
    FREE_EVIDENCE = -0.35
    OCCUPIED_EVIDENCE = 0.85
    KEYFRAME_DISTANCE_M = 0.18
    KEYFRAME_YAW_RAD = math.radians(8.0)
    KEYFRAME_MAX_PERIOD_NS = 1_000_000_000
    MAX_KEYFRAME_POINTS = 180
    LOOP_MIN_SEPARATION = 18
    SUBMAP_KEYFRAMES = 6
    LOOP_SEARCH_RADIUS_M = 0.70
    LOOP_SEARCH_YAW_RAD = math.radians(18.0)
    LOOP_MIN_SCORE = 0.65
    LOOP_MIN_INLIERS = 24
    LOOP_AMBIGUITY_MARGIN = 0.08
    LOCAL_AMBIGUITY_MARGIN = 0.05
    LOCAL_AMBIGUITY_TURN_RADPS = 0.20
    MIN_MAP_MATCH_SCORE = 0.55
    MIN_CLEAR_MATCH_SCORE = 0.60
    STRONG_OCCUPIED_THRESHOLD = 2.0
    OCCLUSION_MIN_SEPARATION_M = 0.075

    def __init__(
        self,
        resolution_m: float,
        *,
        lidar_x_m: float,
        lidar_y_m: float,
        lidar_yaw_rad: float,
        min_range_m: float,
        max_range_m: float,
        padding_cells: int,
        robot_radius_m: float = math.sqrt(0.2**2 + 0.2**2),
        scan_matching: bool = True,
        scan_match_interval: int = 1,
        map_id: str = "",
        defer_graph_optimization: bool = False,
        lidar_time_offset_s: float = 0.0,
    ) -> None:
        if not math.isfinite(resolution_m) or resolution_m <= 0:
            raise ValueError("map resolution must be positive and finite")
        if max_range_m <= min_range_m or padding_cells < 0 or robot_radius_m <= 0:
            raise ValueError("invalid map sensor or footprint settings")
        self.resolution_m = float(resolution_m)
        self.lidar_x_m = float(lidar_x_m)
        self.lidar_y_m = float(lidar_y_m)
        self.lidar_yaw_rad = float(lidar_yaw_rad)
        self.min_range_m = float(min_range_m)
        self.max_range_m = float(max_range_m)
        self.padding_cells = int(padding_cells)
        self.robot_radius_m = float(robot_radius_m)
        self.scan_matching_enabled = bool(scan_matching)
        # Retained for old callers; matching now runs for every accepted scan.
        self.scan_match_interval = 1
        self.map_id = str(map_id)
        self.free: set[tuple[int, int]] = set()
        self.occupied: set[tuple[int, int]] = set()
        self.log_odds: dict[tuple[int, int], float] = {}
        self._pending_wall_clears: set[tuple[int, int]] = set()
        self.last_blocked_returns = 0
        self.poses: list[tuple[float, float, float]] = []
        self.history: list[dict[str, Any]] = []
        self.keyframes: list[_Keyframe] = []
        self.submaps: list[_FrozenSubmap] = []
        self.scan_frames: list[_ScanFrame] = []
        self.graph_edges: list[tuple[int, int, tuple[float, float, float], str]] = []
        self.scans = 0
        self.points = 0
        self.scan_match_attempts = 0
        self.scan_match_accepted = 0
        self.loop_closures = 0
        self.graph_optimizations = 0
        self.defer_graph_optimization = defer_graph_optimization
        self.lidar_time_offset_ns = round(lidar_time_offset_s * 1e9)
        self.graph_optimization_pending = False
        self.revision = 0
        self.last_scan_match = self._match_result(False, "not_run")
        self._held_streak = 0
        self._recovery_candidate: tuple[int, tuple[float, float, float], tuple[float, float, float]] | None = None
        self._corner_ambiguous = False
        self._corner_candidate: tuple[int, tuple[float, float, float], tuple[float, float, float]] | None = None
        self._map_write_needs_confirmation = False
        self._last_stable_map_stamp: int | None = None
        self.last_loop_closure: dict[str, Any] = {"accepted": False, "reason": "not_run"}

    @staticmethod
    def _match_result(accepted: bool, reason: str, score: float = 0.0, count: int = 0,
                      correction: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> _MatchResult:
        return _MatchResult(accepted, score, int(round(score * count)), count,
                            math.hypot(correction[0], correction[1]),
                            correction[2], reason)

    def cell(self, x_m: float, y_m: float) -> tuple[int, int]:
        return math.floor(x_m / self.resolution_m), math.floor(y_m / self.resolution_m)

    def _scan_points(self, scan: LidarScan) -> tuple[tuple[float, float, int], ...]:
        nearest: dict[int, tuple[float, float, int]] = {}
        for point in scan.points:
            angle, distance = float(point.angle_rad), float(point.range_m)
            if not math.isfinite(angle) or not math.isfinite(distance) or not self.min_range_m <= distance < self.max_range_m:
                continue
            sensor_local_x = self.lidar_x_m + distance * math.cos(self.lidar_yaw_rad + angle)
            sensor_local_y = self.lidar_y_m + distance * math.sin(self.lidar_yaw_rad + angle)
            if math.hypot(sensor_local_x, sensor_local_y) <= self.robot_radius_m + self.resolution_m:
                continue
            key = round(angle * 10000)
            old = nearest.get(key)
            if old is None or distance < old[1]:
                nearest[key] = (angle, distance, int(point.t_ns))
        points = sorted(nearest.values(), key=lambda item: item[0])
        if len(points) > self.MAX_KEYFRAME_POINTS:
            stride = len(points) / self.MAX_KEYFRAME_POINTS
            points = [points[min(len(points) - 1, int(i * stride))] for i in range(self.MAX_KEYFRAME_POINTS)]
        return tuple(points)

    def scan_reference_ns(self, scan: LidarScan) -> int:
        # A positive offset represents delay between acquisition and receipt.
        return scan.t_ns - self.lidar_time_offset_ns

    def _deskew_rays(self, scan: LidarScan, points: tuple[tuple[float, float, int], ...],
                     pose_samples: tuple[tuple[int, float, float, float], ...]
                     ) -> tuple[tuple[float, float, float, float], ...] | None:
        if len(scan.points) < 2 or not points or len(pose_samples) < 2:
            return None
        raw_angles = np.unwrap([point.angle_rad for point in scan.points])
        sweep = float(raw_angles[-1] - raw_angles[0])
        if not math.isfinite(sweep) or abs(sweep) < math.pi:
            return None
        direction = math.copysign(1.0, sweep)
        angles = np.asarray([point[0] for point in points])
        phase = np.mod(direction * angles, math.tau)
        remaining = np.mod(-phase, math.tau)
        # A zero-degree point at the start of the revolution is one period old.
        remaining[phase < 1e-9] = math.tau
        period = scan.period_ns or 100_000_000
        reference = self.scan_reference_ns(scan)
        sample_t = np.asarray([row[0] - reference for row in pose_samples], dtype=float)
        beam_t = -remaining * period / math.tau
        if sample_t[0] > beam_t.min() or sample_t[-1] < -50_000_000:
            return None
        values = np.asarray([row[1:] for row in pose_samples])
        values[:, 2] = np.unwrap(values[:, 2])
        if sample_t[-1] < 0:
            delta = sample_t[-1] - sample_t[-2]
            if delta <= 0:
                return None
            values = np.vstack((values, values[-1] - sample_t[-1] * (values[-1] - values[-2]) / delta))
            sample_t = np.append(sample_t, 0)
        ref = tuple(float(np.interp(0, sample_t, values[:, k])) for k in range(3))
        poses = np.column_stack([np.interp(beam_t, sample_t, values[:, k]) for k in range(3)])
        rays = []
        for (angle, distance, _), beam_pose in zip(points, poses):
            dx, dy, yaw = _relative(ref, tuple(beam_pose))
            c, s = math.cos(yaw), math.sin(yaw)
            sx = dx + c * self.lidar_x_m - s * self.lidar_y_m
            sy = dy + s * self.lidar_x_m + c * self.lidar_y_m
            ray_yaw = yaw + self.lidar_yaw_rad + angle
            rays.append((sx, sy, sx + distance * math.cos(ray_yaw), sy + distance * math.sin(ray_yaw)))
        return tuple(rays)

    def _pose_at_point(self, pose: tuple[float, float, float], point_t_ns: int,
                       scan_t_ns: int, vx: float, vy: float, wz: float) -> tuple[float, float, float]:
        # N10P timestamps are packet-time stamps, so this compensates packet-level
        # motion distortion. It is not per-beam deskew because the device driver
        # does not expose an acquisition time for each individual beam.
        dt = max(-0.15, min(0.0, (point_t_ns - scan_t_ns) / 1e9))
        if abs(dt) < 1e-6:
            return pose
        half = pose[2] + 0.5 * wz * dt
        return (pose[0] + (math.cos(half) * vx - math.sin(half) * vy) * dt,
                pose[1] + (math.sin(half) * vx + math.cos(half) * vy) * dt,
                _wrap(pose[2] + wz * dt))

    def _world_endpoint(self, point: tuple[float, float, int], pose: tuple[float, float, float],
                        scan_t_ns: int, vx: float, vy: float, wz: float) -> tuple[float, float, float, float]:
        point_pose = self._pose_at_point(pose, point[2], scan_t_ns, vx, vy, wz)
        yaw = point_pose[2] + self.lidar_yaw_rad + point[0]
        sx = point_pose[0] + math.cos(point_pose[2]) * self.lidar_x_m - math.sin(point_pose[2]) * self.lidar_y_m
        sy = point_pose[1] + math.sin(point_pose[2]) * self.lidar_x_m + math.cos(point_pose[2]) * self.lidar_y_m
        return sx, sy, sx + point[1] * math.cos(yaw), sy + point[1] * math.sin(yaw)

    def _local_endpoints(self, points: tuple[tuple[float, float, int], ...], scan_t_ns: int,
                         vx: float, vy: float, wz: float) -> tuple[tuple[float, float], ...]:
        endpoints = []
        for angle, distance, point_t_ns in points:
            dt = max(-0.15, min(0.0, (point_t_ns - scan_t_ns) / 1e9))
            dyaw = wz * dt
            half = 0.5 * dyaw
            dx = (math.cos(half) * vx - math.sin(half) * vy) * dt
            dy = (math.sin(half) * vx + math.cos(half) * vy) * dt
            sx = dx + math.cos(dyaw) * self.lidar_x_m - math.sin(dyaw) * self.lidar_y_m
            sy = dy + math.sin(dyaw) * self.lidar_x_m + math.cos(dyaw) * self.lidar_y_m
            ray_yaw = dyaw + self.lidar_yaw_rad + angle
            endpoints.append((sx + distance * math.cos(ray_yaw), sy + distance * math.sin(ray_yaw)))
        return tuple(endpoints)

    def _score(
        self,
        endpoints: tuple[tuple[float, float], ...],
        pose: tuple[float, float, float],
        occupied_neighbourhood: set[tuple[int, int]] | None = None,
    ) -> float:
        if not endpoints:
            return 0.0
        if occupied_neighbourhood is None:
            occupied_neighbourhood = {
                (x + dx, y + dy)
                for x, y in self.occupied
                for dx in (-1, 0, 1)
                for dy in (-1, 0, 1)
            }
        cosine, sine = math.cos(pose[2]), math.sin(pose[2])
        hits = 0
        for local_x, local_y in endpoints:
            x = pose[0] + cosine * local_x - sine * local_y
            y = pose[1] + sine * local_x + cosine * local_y
            if self.cell(x, y) in occupied_neighbourhood:
                hits += 1
        return hits / len(endpoints)

    def _match_grid(self, base: tuple[float, float, float], reach_m: float,
                    reference_cells: set[tuple[int, int]], *, dilation: int = 1
                    ) -> tuple[np.ndarray, int, int] | None:
        min_x, min_y = self.cell(base[0] - reach_m, base[1] - reach_m)
        max_x, max_y = self.cell(base[0] + reach_m, base[1] + reach_m)
        width, height = max_x - min_x + 3, max_y - min_y + 3
        if width * height > 2_000_000:
            return None
        grid = np.zeros((height + 2, width + 2), dtype=np.bool_)
        occupied = [(x - min_x + 2, y - min_y + 2) for x, y in reference_cells
                    if min_x - 1 <= x <= max_x + 1 and min_y - 1 <= y <= max_y + 1]
        if occupied:
            xs, ys = np.asarray(occupied, dtype=np.intp).T
            for dx in range(-dilation, dilation + 1):
                for dy in range(-dilation, dilation + 1):
                    grid[ys + dy, xs + dx] = True
        return grid, min_x - 2, min_y - 2

    def _score_candidates(
        self, endpoints: np.ndarray, candidates: list[tuple[float, float, float]],
        tile: tuple[np.ndarray, int, int],
    ) -> np.ndarray:
        return self._candidate_hits(endpoints, candidates, tile).mean(axis=1)

    def _candidate_hits(
        self, endpoints: np.ndarray, candidates: list[tuple[float, float, float]],
        tile: tuple[np.ndarray, int, int],
    ) -> np.ndarray:
        grid, min_x, min_y = tile
        x, y, yaw = np.asarray(candidates).T[:, :, None]
        ex, ey = endpoints.T
        c, s = np.cos(yaw), np.sin(yaw)
        xs = np.floor((x + c * ex - s * ey) / self.resolution_m).astype(np.intp) - min_x
        ys = np.floor((y + s * ex + c * ey) / self.resolution_m).astype(np.intp) - min_y
        valid = (xs >= 0) & (xs < grid.shape[1]) & (ys >= 0) & (ys < grid.shape[0])
        return grid[ys.clip(0, grid.shape[0] - 1), xs.clip(0, grid.shape[1] - 1)] & valid

    def _refine_pose(self, endpoints: np.ndarray, seed: tuple[float, float, float],
                     prior: tuple[float, float, float], tile: tuple[np.ndarray, int, int]
                     ) -> tuple[tuple[float, float, float], float]:
        grid, min_x, min_y = tile
        field = grid.astype(np.float32)
        for axis in (0, 1):
            padding = [(0, 0), (0, 0)]
            padding[axis] = (2, 2)
            padded = np.moveaxis(np.pad(field, padding), axis, 0)
            n = field.shape[axis]
            field = np.moveaxis(
                (padded[:n] + 4*padded[1:n+1] + 6*padded[2:n+2]
                 + 4*padded[3:n+3] + padded[4:n+4]) / 16, 0, axis,
            )
        peak = float(field.max())
        if peak <= 0:
            return seed, 0.0
        field /= peak
        ex, ey = endpoints.T
        lever = max(1.0, float(np.median(np.hypot(ex, ey))))

        def sample(p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            c, s = math.cos(p[2]), math.sin(p[2])
            rx, ry = c * ex - s * ey, s * ex + c * ey
            x = (p[0] + rx) / self.resolution_m - min_x - 0.5
            y = (p[1] + ry) / self.resolution_m - min_y - 0.5
            ix, iy = np.floor(x).astype(np.intp), np.floor(y).astype(np.intp)
            tx, ty = x - ix, y - iy
            valid = (ix >= 0) & (iy >= 0) & (ix < field.shape[1]-1) & (iy < field.shape[0]-1)
            ix, iy = ix.clip(0, field.shape[1]-2), iy.clip(0, field.shape[0]-2)
            a, b, c0, d = field[iy, ix], field[iy, ix+1], field[iy+1, ix], field[iy+1, ix+1]
            value = ((a*(1-tx) + b*tx)*(1-ty) + (c0*(1-tx) + d*tx)*ty) * valid
            gx = ((b-a)*(1-ty) + (d-c0)*ty) * valid / self.resolution_m
            gy = ((c0-a)*(1-tx) + (d-b)*tx) * valid / self.resolution_m
            return 1-value, np.column_stack((gx, gy, (-gx*ry + gy*rx)/lever))

        pose = np.asarray(seed)
        ratio = 0.0
        for _ in range(4):
            residual, jac = sample(pose)
            eig, axes = np.linalg.eigh(jac.T @ jac)
            if eig[-1] <= 1e-8:
                break
            ratio = max(0.0, float(eig[0] / eig[-1]))
            observed = eig >= 0.025 * eig[-1]
            delta = axes @ (np.where(observed, 1 / np.maximum(eig, 1e-8), 0) * (axes.T @ jac.T @ residual))
            delta[2] /= lever
            if np.linalg.norm(delta[:2]) > 0.06 or abs(delta[2]) > math.radians(3):
                break
            trial = pose + delta
            if sample(trial)[0] @ sample(trial)[0] >= residual @ residual:
                break
            pose = trial
        if ratio < 0.025:
            _, jac = sample(pose)
            eig, axes = np.linalg.eigh(jac.T @ jac)
            observed = eig >= max(1e-8, 0.025 * eig[-1])
            displacement = pose - np.asarray(prior)
            displacement[2] = _wrap(displacement[2]) * lever
            displacement = axes @ ((axes.T @ displacement) * observed)
            displacement[2] /= lever
            pose = np.asarray(prior) + displacement
        return (float(pose[0]), float(pose[1]), _wrap(float(pose[2]))), ratio

    def _match(self, points: tuple[tuple[float, float, int], ...], base: tuple[float, float, float],
               scan_t_ns: int, vx: float, vy: float, wz: float, *, radius: float = 0.06,
               yaw_radius: float = math.radians(3.5),
               require_improvement: bool = True,
               reference_cells: set[tuple[int, int]] | None = None,
               loop_search: bool = False,
               rays: tuple[tuple[float, float, float, float], ...] | None = None,
               deadline_mono: float | None = None) -> tuple[_MatchResult, tuple[float, float, float]]:
        if not self.scan_matching_enabled:
            return self._match_result(False, "disabled"), base
        reference = self.occupied if reference_cells is None else reference_cells
        if len(reference) < 12 or len(points) < 16:
            return self._match_result(False, "insufficient_features", count=len(points)), base
        self.scan_match_attempts += 1
        endpoints = (tuple((ray[2], ray[3]) for ray in rays) if rays is not None
                     else self._local_endpoints(points, scan_t_ns, vx, vy, wz))
        coarse_xy_step = 0.10 if loop_search else 0.05
        coarse_yaw_step = math.radians(6.0 if loop_search else 3.0)
        reach = max(math.hypot(x, y) for x, y in endpoints) + math.ceil(radius / coarse_xy_step) * coarse_xy_step + 0.02
        tile = self._match_grid(base, reach, reference)
        if tile is None:
            occupied_neighbourhood = {
                (x + dx, y + dy) for x, y in reference
                for dx in (-1, 0, 1) for dy in (-1, 0, 1)
            }

            def scores(candidates: list[tuple[float, float, float]]) -> list[float]:
                return [self._score(endpoints, candidate, occupied_neighbourhood) for candidate in candidates]
        else:
            endpoint_array = np.asarray(endpoints)

            def scores(candidates: list[tuple[float, float, float]]) -> np.ndarray:
                return self._score_candidates(endpoint_array, candidates, tile)

        best = base
        base_score = float(scores([base])[0])
        best_score = base_score
        loop_candidates = [(base, base_score)] if loop_search else []
        check_corner = not loop_search and (abs(wz) >= self.LOCAL_AMBIGUITY_TURN_RADPS or self._corner_ambiguous)
        local_candidates = [] if loop_search else [(base, base_score)]
        # Coarse-to-fine correlative scan matching, bounded around odometry.
        for step_xy, step_yaw, factor in (
            (coarse_xy_step, coarse_yaw_step, 1.0),
            (0.02, math.radians(1.0), 0.5),
        ):
            center = best
            radius_xy = radius if factor == 1.0 else 0.02
            radius_yaw_now = yaw_radius if factor == 1.0 else math.radians(1.0)
            nx = max(1, int(math.ceil(radius_xy / step_xy)))
            nyaw = max(1, int(math.ceil(radius_yaw_now / step_yaw)))
            offsets = [(ix, iy, it) for ix in range(-nx, nx + 1)
                       for iy in range(-nx, nx + 1) for it in range(-nyaw, nyaw + 1)]
            candidates = [(center[0] + ix * step_xy, center[1] + iy * step_xy,
                           _wrap(center[2] + it * step_yaw)) for ix, iy, it in offsets]
            for (ix, iy, it), candidate, score in zip(offsets, candidates, scores(candidates)):
                if loop_search:
                    loop_candidates.append((candidate, float(score)))
                if not loop_search:
                    local_candidates.append((candidate, float(score)))
                movement_penalty = 0.0005 * (ix * ix + iy * iy + it * it)
                if score - movement_penalty > best_score:
                    best, best_score = candidate, float(score)
            if deadline_mono is not None and time.monotonic() >= deadline_mono:
                return self._match_result(False, "match_deadline", best_score, len(points)), base
        observability = None
        if not loop_search and best_score >= 0.45 and tile is not None:
            raw_tile = self._match_grid(base, reach, reference, dilation=0)
            refined, observability = self._refine_pose(np.asarray(endpoints), best, base, raw_tile)
            refined_score = float(scores([refined])[0])
            if refined_score >= max(0.45, best_score - 0.05):
                best, best_score = refined, refined_score
            elif observability < 0.025:
                best, best_score = base, base_score
        large_shift = math.hypot(best[0] - base[0], best[1] - base[1]) >= 0.08
        if not loop_search and (check_corner or large_shift) and best_score >= self.MIN_MAP_MATCH_SCORE:
            # Compare distinct poses before the odometry-aligned fallback.
            rivals = [
                (candidate, score) for candidate, score in local_candidates
                if (math.hypot(candidate[0] - best[0], candidate[1] - best[1]) >= 0.075
                    or abs(_wrap(candidate[2] - best[2])) >= math.radians(4.5))
            ]
            rival = max(rivals, key=lambda item: item[1], default=None)
            ambiguous = rival is not None and rival[1] >= best_score - self.LOCAL_AMBIGUITY_MARGIN
            if rival is not None and not ambiguous and tile is not None and rival[1] >= best_score - 0.10:
                # Give each sufficiently observed direction one vote, so a
                # long wall cannot mask evidence from an opening or side wall.
                hits = self._candidate_hits(np.asarray(endpoints), [best, rival[0]], tile)
                sectors = np.floor(np.mod([point[0] for point in points], math.tau) / (math.tau / 8)).astype(int)
                votes = [hits[:, sectors == k].mean(axis=1) for k in range(8)
                         if np.count_nonzero(sectors == k) >= 5]
                if len(votes) >= 3:
                    sector_scores = np.mean(votes, axis=0)
                    ambiguous = bool(sector_scores[1] >= sector_scores[0] - self.LOCAL_AMBIGUITY_MARGIN)
            if ambiguous and rival is not None:
                result = self._match_result(False, "ambiguous_local_match", best_score, len(points), _relative(base, best))
                return replace(result, competing_poses=((best, best_score), rival)), base
        correction = _relative(base, best)
        # The coarse grid uses ceil(radius / step), then the fine pass searches
        # around the coarse winner. Derive the admissible correction from that
        # actual search window; fixed 6 cm / 3 degree gates rejected valid grid
        # results (and made larger loop-closure corrections impossible).
        fine_xy_step = 0.02
        fine_yaw_step = math.radians(1.0)
        max_axis_correction = math.ceil(radius / coarse_xy_step) * coarse_xy_step + fine_xy_step
        max_translation_correction = math.sqrt(2.0) * max_axis_correction
        max_yaw_correction = math.ceil(yaw_radius / coarse_yaw_step) * coarse_yaw_step + fine_yaw_step
        if (math.hypot(correction[0], correction[1]) > max_translation_correction
                or abs(correction[2]) > max_yaw_correction):
            return self._match_result(False, "correction_out_of_bounds", best_score, len(points), correction), base
        accepted = best_score >= 0.45 and (not require_improvement or best_score >= base_score + 0.015)
        if not accepted:
            if base_score >= 0.55:
                return replace(self._match_result(True, "aligned_odometry", base_score, len(points)),
                               observability=observability), base
            return self._match_result(False, "weak_match", best_score, len(points), correction), base
        if loop_search:
            alternatives = [
                (best[0] + 0.12 * math.cos(k * math.pi / 4),
                 best[1] + 0.12 * math.sin(k * math.pi / 4), best[2])
                for k in range(8)
            ]
            alternatives += [(best[0], best[1], _wrap(best[2] + math.radians(deg))) for deg in (-5, 5)]
            if max(scores(alternatives)) >= best_score - self.LOOP_AMBIGUITY_MARGIN:
                return self._match_result(False, "ambiguous_loop_match", best_score, len(points), correction), base
        if any(score >= best_score - self.LOOP_AMBIGUITY_MARGIN and
               (math.hypot(candidate[0] - best[0], candidate[1] - best[1]) >= 0.12 or
                abs(_wrap(candidate[2] - best[2])) >= math.radians(5.0))
               for candidate, score in loop_candidates):
            return self._match_result(False, "ambiguous_loop_match", best_score, len(points), correction), base
        return replace(self._match_result(True, "matched", best_score, len(points), correction),
                       observability=observability), best

    def _apply_evidence(self, cell: tuple[int, int], evidence: float) -> None:
        score = max(self.LOG_ODDS_MIN, min(self.LOG_ODDS_MAX, self.log_odds.get(cell, 0.0) + evidence))
        self.log_odds[cell] = score
        if score >= self.OCCUPIED_THRESHOLD:
            self.occupied.add(cell)
            self.free.discard(cell)
        elif score <= self.FREE_THRESHOLD:
            self.free.add(cell)
            self.occupied.discard(cell)
        else:
            self.occupied.discard(cell)
            self.free.discard(cell)

    def _integrate(self, points: tuple[tuple[float, float, int], ...], pose: tuple[float, float, float],
                   scan_t_ns: int, vx: float, vy: float, wz: float, *, clear_free: bool = True,
                   rays: tuple[tuple[float, float, float, float], ...] | None = None,
                   deadline_mono: float | None = None) -> bool:
        pose_x, pose_y = pose[0] / self.resolution_m, pose[1] / self.resolution_m
        radius_sq = (self.robot_radius_m / self.resolution_m) ** 2
        separation_cells = max(1, math.ceil(self.OCCLUSION_MIN_SEPARATION_M / self.resolution_m))
        blocked_returns = 0
        hits: set[tuple[int, int]] = set()
        misses: set[tuple[int, int]] = set()
        world_rays = (self._world_endpoint(point, pose, scan_t_ns, vx, vy, wz) for point in points)
        if rays is not None:
            x, y, yaw = pose
            c, s = math.cos(yaw), math.sin(yaw)
            world_rays = ((x + c*sx - s*sy, y + s*sx + c*sy, x + c*ex - s*ey, y + s*ex + c*ey)
                          for sx, sy, ex, ey in rays)
        for sx, sy, ex, ey in world_rays:
            end = self.cell(ex, ey)
            occluded = False
            if clear_free or self.occupied:
                for cell in bresenham(self.cell(sx, sy), end)[:-1]:
                    dx, dy = cell[0] + 0.5 - pose_x, cell[1] + 0.5 - pose_y
                    if dx * dx + dy * dy <= radius_sq:
                        continue
                    if clear_free:
                        misses.add(cell)
                    if (cell in self.occupied and
                            max(abs(cell[0] - end[0]), abs(cell[1] - end[1])) >= separation_cells):
                        # A return behind a mapped wall conflicts with the old
                        # geometry. Collect clearing evidence at the wall first.
                        occluded = True
                        break
            if not occluded:
                hits.add(end)
            else:
                blocked_returns += 1
        pending = set()
        free_votes = misses - hits
        if deadline_mono is not None and time.monotonic() >= deadline_mono:
            return False
        for cell in free_votes:
            if self.log_odds.get(cell, 0.0) > self.STRONG_OCCUPIED_THRESHOLD:
                pending.add(cell)
                if cell not in self._pending_wall_clears:
                    continue
            self._apply_evidence(cell, self.FREE_EVIDENCE)
        for end in hits:
            self._apply_evidence(end, self.OCCUPIED_EVIDENCE)
        self._pending_wall_clears = pending
        self.last_blocked_returns = blocked_returns
        return True

    def _corner_write_reason(self, stamp: int, yaw_rate: float, match: _MatchResult, reliable: bool) -> str | None:
        turning = abs(yaw_rate) >= self.LOCAL_AMBIGUITY_TURN_RADPS
        small_correction = match.correction_m <= 0.06 and abs(match.correction_yaw_rad) <= math.radians(2.5)
        large_correction = match.correction_m >= 0.08 or abs(match.correction_yaw_rad) > math.radians(4)
        risky = reliable and (large_correction or (turning and (abs(yaw_rate) >= 0.8 or not small_correction)))
        if risky:
            self._map_write_needs_confirmation = True
            self._last_stable_map_stamp = None
            return "turn_pose_change" if turning else "large_pose_change"
        if self._map_write_needs_confirmation:
            prior = self._last_stable_map_stamp
            stable = reliable and small_correction
            self._last_stable_map_stamp = stamp if stable else None
            if not stable or prior is None or not 0 < stamp - prior <= 1_000_000_000:
                return "confirming_map_pose"
            self._map_write_needs_confirmation = False
            self._last_stable_map_stamp = None
        return None

    def _new_keyframe(self, points: tuple[tuple[float, float, int], ...], pose: tuple[float, float, float],
                      scan_t_ns: int, vx: float, vy: float, wz: float,
                      rays: tuple[tuple[float, float, float, float], ...] | None = None) -> bool:
        if not self.keyframes:
            self.keyframes.append(_Keyframe(pose, points, scan_t_ns, vx, vy, wz, rays))
            return True
        previous = self.keyframes[-1]
        distance = math.hypot(pose[0] - previous.pose[0], pose[1] - previous.pose[1])
        turn = abs(_wrap(pose[2] - previous.pose[2]))
        if distance < self.KEYFRAME_DISTANCE_M and turn < self.KEYFRAME_YAW_RAD and scan_t_ns - previous.t_ns < self.KEYFRAME_MAX_PERIOD_NS:
            return False
        index = len(self.keyframes)
        self.graph_edges.append((index - 1, index, _relative(previous.pose, pose), "odometry"))
        self.keyframes.append(_Keyframe(pose, points, scan_t_ns, vx, vy, wz, rays))
        if len(self.keyframes) % self.SUBMAP_KEYFRAMES == 0:
            end = len(self.keyframes)
            start = end - self.SUBMAP_KEYFRAMES
            anchor = self.keyframes[start].pose
            hits = set()
            for frame in self.keyframes[start:end]:
                hits.update(self._keyframe_hits(frame, _relative(anchor, frame.pose)))
            self.submaps.append(_FrozenSubmap(start, end, frozenset(hits)))
        return True

    def _keyframe_hits(self, frame: _Keyframe, pose: tuple[float, float, float]) -> set[tuple[int, int]]:
        endpoints = (self._local_endpoints(frame.scan, frame.t_ns, frame.vx, frame.vy, frame.wz)
                     if frame.rays is None else tuple((ray[2], ray[3]) for ray in frame.rays))
        c, s = math.cos(pose[2]), math.sin(pose[2])
        return {self.cell(pose[0] + c*x - s*y, pose[1] + s*x + c*y) for x, y in endpoints}

    def _submap_hits(self, submap: _FrozenSubmap) -> set[tuple[int, int]]:
        px, py, yaw = self.keyframes[submap.anchor].pose
        c, s = math.cos(yaw), math.sin(yaw)
        res = self.resolution_m
        return {self.cell(px + res*(c*(x+0.5) - s*(y+0.5)), py + res*(s*(x+0.5) + c*(y+0.5)))
                for x, y in submap.hits}

    def _active_reference(self) -> set[tuple[int, int]] | None:
        if not self.submaps:
            return None
        previous = self.submaps[-1]
        hits = self._submap_hits(previous)
        for frame in self.keyframes[previous.end:]:
            hits.update(self._keyframe_hits(frame, frame.pose))
        return hits

    @staticmethod
    def _pack_scan(points: tuple[tuple[float, float, int], ...], scan_t_ns: int) -> array:
        values = array("f")
        for angle, distance, point_t_ns in points:
            values.extend((angle, distance, (point_t_ns - scan_t_ns) / 1e9))
        return values

    @staticmethod
    def _unpack_scan(frame: _ScanFrame) -> tuple[tuple[float, float, int], ...]:
        data = frame.data
        return tuple((float(data[i]), float(data[i + 1]), frame.t_ns + int(data[i + 2] * 1e9))
                     for i in range(0, len(data), 3))

    def _try_loop_closure(self, current_index: int, points: tuple[tuple[float, float, int], ...],
                          current: _Keyframe, deadline_mono: float | None = None) -> bool:
        if current_index < self.LOOP_MIN_SEPARATION:
            self.last_loop_closure = {"accepted": False, "reason": "insufficient_keyframes"}
            return False
        candidates = []
        for submap in self.submaps:
            if submap.end > current_index - self.LOOP_MIN_SEPARATION + 1:
                continue
            distance, index = min(
                (math.hypot(current.pose[0] - self.keyframes[i].pose[0],
                            current.pose[1] - self.keyframes[i].pose[1]), i)
                for i in range(submap.anchor, submap.end)
            )
            if distance < 3.0:
                candidates.append((distance, index, submap))
        if not candidates:
            self.last_loop_closure = {"accepted": False, "reason": "no_nearby_old_keyframe"}
            return False
        validated = []
        rejection = "no_consistent_scan_match"
        for _, index, submap in sorted(candidates)[:3]:
            if deadline_mono is not None and time.monotonic() >= deadline_mono:
                self.last_loop_closure = {"accepted": False, "reason": "loop_search_budget"}
                return False
            frame = self.keyframes[index]
            reference = self._submap_hits(submap)
            match, corrected = self._match(points, frame.pose, current.t_ns, current.vx, current.vy, current.wz,
                                           radius=self.LOOP_SEARCH_RADIUS_M, yaw_radius=self.LOOP_SEARCH_YAW_RAD,
                                           require_improvement=False, reference_cells=reference, loop_search=True,
                                           rays=current.rays, deadline_mono=deadline_mono)
            if match.reason == "match_deadline":
                self.last_loop_closure = {"accepted": False, "reason": "loop_search_budget"}
                return False
            if match.accepted and match.score >= self.LOOP_MIN_SCORE and match.inliers >= self.LOOP_MIN_INLIERS:
                validated.append((match.score, index, corrected))
            elif match.reason == "ambiguous_loop_match":
                rejection = match.reason
        if not validated:
            self.last_loop_closure = {"accepted": False, "reason": rejection}
            return False
        validated.sort(reverse=True)
        score, index, corrected = validated[0]
        for other_score, _, other_pose in validated[1:]:
            dx, dy, dyaw = _relative(corrected, other_pose)
            if (other_score >= score - self.LOOP_AMBIGUITY_MARGIN
                    and (math.hypot(dx, dy) >= 0.12 or abs(dyaw) >= math.radians(5))):
                self.last_loop_closure = {"accepted": False, "reason": "competing_loop_matches"}
                return False
        measurement = _relative(self.keyframes[index].pose, corrected)
        self.graph_edges.append((index, current_index, measurement, "loop_closure"))
        self.loop_closures += 1
        self.last_loop_closure = {"accepted": True, "from_keyframe": index,
                                  "to_keyframe": current_index, "score": score}
        if self.defer_graph_optimization:
            self.graph_optimization_pending = True
            return False
        self._optimize_graph()
        return True

    def optimize_pending_graph(self) -> None:
        if self.graph_optimization_pending:
            self._optimize_graph()
            self.graph_optimization_pending = False

    def optimization_snapshot(self) -> OccupancyMap:
        snapshot = copy(self)
        snapshot.keyframes = self.keyframes.copy()
        snapshot.graph_edges = self.graph_edges.copy()
        snapshot.scan_frames = self.scan_frames.copy()
        snapshot.submaps = self.submaps.copy()
        snapshot.free = set()
        snapshot.occupied = set()
        snapshot.log_odds = {}
        snapshot._pending_wall_clears = set()
        return snapshot

    def install_optimized_snapshot(self, snapshot: OccupancyMap) -> bool:
        """Install a solved prefix and replay only the small tail that arrived during optimization."""
        if snapshot.graph_optimizations != self.graph_optimizations + 1:
            return False
        prefix = len(snapshot.scan_frames)
        tail = self.scan_frames[prefix:]
        if not prefix or len(tail) > 5 or not snapshot.keyframes:
            return False
        last = len(snapshot.keyframes) - 1
        old_anchor = self.keyframes[last].pose
        new_anchor = snapshot.keyframes[last].pose
        snapshot.keyframes.extend(
            replace(frame, pose=_compose(new_anchor, _relative(old_anchor, frame.pose)))
            for frame in self.keyframes[last + 1:]
        )
        previous = snapshot.scan_frames[-1].scan_index
        for frame in tail:
            if frame.scan_index != previous + 1:
                snapshot._pending_wall_clears.clear()
            previous = frame.scan_index
            pose = _compose(snapshot.keyframes[frame.anchor].pose, frame.relative_pose)
            snapshot._integrate(snapshot._unpack_scan(frame), pose, frame.t_ns, frame.vx, frame.vy, frame.wz,
                                clear_free=frame.clear_free, rays=frame.rays)
            snapshot.poses.append(pose)
        self.keyframes = snapshot.keyframes
        self.poses = snapshot.poses[-5000:]
        self.free, self.occupied, self.log_odds = snapshot.free, snapshot.occupied, snapshot.log_odds
        self._pending_wall_clears = snapshot._pending_wall_clears if previous == self.scans else set()
        self.graph_optimizations = snapshot.graph_optimizations
        self.graph_optimization_pending = self.loop_closures > snapshot.loop_closures
        self.revision += 1
        return True

    def _optimize_graph(self) -> None:
        if len(self.keyframes) < 3 or not self.graph_edges:
            return
        try:
            import numpy as np
            from scipy.optimize import least_squares
            from scipy.sparse import lil_matrix
        except ImportError:
            self.last_loop_closure = {**self.last_loop_closure, "optimized": False,
                                      "reason": "scipy_unavailable"}
            return
        old = [frame.pose for frame in self.keyframes]
        initial = np.asarray(old, dtype=float)
        count = len(old)
        edges = self.graph_edges
        x0 = initial[1:].reshape(-1)
        sparsity = lil_matrix((3 * len(edges), 3 * (count - 1)), dtype=int)
        for row, (i, j, _, _) in enumerate(edges):
            for node in (i, j):
                if node:
                    sparsity[3 * row:3 * row + 3, 3 * (node - 1):3 * node] = 1

        def residual(vector: Any) -> Any:
            poses = np.vstack((initial[0], np.asarray(vector).reshape((-1, 3))))
            values = []
            for i, j, measurement, kind in edges:
                predicted = _relative(tuple(poses[i]), tuple(poses[j]))
                sigma_xy, sigma_yaw = ((0.10, 0.12) if kind == "odometry" else (0.035, 0.045))
                values.extend(((predicted[0] - measurement[0]) / sigma_xy,
                               (predicted[1] - measurement[1]) / sigma_xy,
                               _wrap(predicted[2] - measurement[2]) / sigma_yaw))
            return np.asarray(values)

        result = least_squares(residual, x0, jac_sparsity=sparsity.tocsr(), tr_solver="lsmr",
                               loss="huber", f_scale=1.0, max_nfev=20)
        optimized = np.vstack((initial[0], result.x.reshape((-1, 3))))
        if not np.isfinite(optimized).all():
            self.last_loop_closure = {**self.last_loop_closure, "optimized": False,
                                      "reason": "non_finite_solution"}
            return
        self.keyframes = [
            replace(frame, pose=tuple(float(v) for v in optimized[i]))
            for i, frame in enumerate(self.keyframes)
        ]
        self.graph_optimizations += 1
        self.revision += 1
        self._rebuild_map()
        self.last_loop_closure = {**self.last_loop_closure, "optimized": True,
                                  "keyframes": len(self.keyframes)}

    def _rebuild_map(self) -> None:
        self.free.clear()
        self.occupied.clear()
        self.log_odds.clear()
        self._pending_wall_clears.clear()
        corrected_poses = []
        previous_index = 0
        for frame in self.scan_frames:
            if frame.scan_index != previous_index + 1:
                self._pending_wall_clears.clear()
            previous_index = frame.scan_index
            anchor_pose = self.keyframes[frame.anchor].pose
            pose = _compose(anchor_pose, frame.relative_pose)
            corrected_poses.append(pose)
            self._integrate(
                self._unpack_scan(frame), pose, frame.t_ns, frame.vx, frame.vy, frame.wz,
                clear_free=frame.clear_free, rays=frame.rays,
            )
        self.poses = corrected_poses[-5000:]

    def _recover_pose(self, points, scan, pose, base, rays, deadline_mono):
        if self._held_streak < 4 or self._held_streak % 4 != 0 or not self.scan_frames:
            return None
        if deadline_mono is not None and deadline_mono - time.monotonic() < 0.10:
            return None
        match, corrected = self._match(
            points[::2], base, scan.t_ns, pose.last_vx_mps, pose.last_vy_mps, pose.last_yaw_rate_radps,
            radius=0.60, yaw_radius=math.radians(24), require_improvement=False, loop_search=True,
            reference_cells=self.occupied, rays=rays[::2] if rays is not None else None,
            deadline_mono=deadline_mono,
        )
        if not match.accepted or match.score < 0.68 or match.inliers < 32:
            self._recovery_candidate = None
            return None
        prior = self._recovery_candidate
        self._recovery_candidate = (scan.t_ns, base, corrected)
        if prior is None or not 0 < scan.t_ns - prior[0] <= 3_000_000_000:
            return None
        expected = _compose(prior[2], _relative(prior[1], base))
        dx, dy, dyaw = _relative(expected, corrected)
        if math.hypot(dx, dy) > 0.08 or abs(dyaw) > math.radians(4):
            return None
        self._recovery_candidate = None
        return replace(match, reason="relocalized"), corrected

    def _confirm_corner_match(self, stamp: int, base: tuple[float, float, float],
                              corrected: tuple[float, float, float]) -> bool:
        prior = self._corner_candidate
        self._corner_candidate = (stamp, base, corrected)
        if prior is None or not 0 < stamp - prior[0] <= 1_500_000_000:
            return False
        expected = _compose(prior[2], _relative(prior[1], base))
        dx, dy, dyaw = _relative(expected, corrected)
        if math.hypot(dx, dy) > 0.06 or abs(dyaw) > math.radians(3):
            return False
        self._corner_candidate = None
        self._corner_ambiguous = False
        return True

    def update(self, scan: LidarScan, pose: Any, *, deadline_mono: float | None = None,
               pose_samples: tuple[tuple[int, float, float, float], ...] = ()) -> bool:
        started_mono = time.monotonic()
        points = self._scan_points(scan)
        rays = self._deskew_rays(scan, points, pose_samples)
        base = pose.as_tuple()
        dt = min(0.35, max(0.0, (scan.t_ns - self.history[-1]["t_ns"]) / 1e9)) if self.history else 0.0
        radius = min(0.16, 0.06 + 0.25 * math.hypot(pose.last_vx_mps, pose.last_vy_mps) * dt)
        yaw_radius = min(math.radians(10), math.radians(3.5) + 0.35 * abs(pose.last_yaw_rate_radps) * dt)
        match, corrected = self._match(points, base, scan.t_ns, pose.last_vx_mps,
                                       pose.last_vy_mps, pose.last_yaw_rate_radps, radius=radius,
                                       yaw_radius=yaw_radius, rays=rays, deadline_mono=deadline_mono,
                                       reference_cells=self._active_reference())
        if self.submaps and match.reason != "ambiguous_local_match" and match.score < self.MIN_MAP_MATCH_SCORE and (
            deadline_mono is None or deadline_mono - time.monotonic() >= 0.04
        ):
            match, corrected = self._match(
                points, base, scan.t_ns, pose.last_vx_mps, pose.last_vy_mps, pose.last_yaw_rate_radps,
                radius=radius, yaw_radius=yaw_radius, rays=rays, deadline_mono=deadline_mono,
            )
        matched_mono = time.monotonic()
        if deadline_mono is not None and matched_mono >= deadline_mono:
            return False
        reliable = (match.accepted and match.score >= self.MIN_MAP_MATCH_SCORE
                    and match.correction_m <= 0.15 and abs(match.correction_yaw_rad) <= math.radians(7))
        if match.reason == "ambiguous_local_match":
            self._corner_ambiguous = True
            self._corner_candidate = None
            self._recovery_candidate = None
        elif self._corner_ambiguous:
            if not reliable:
                self._corner_candidate = None
            elif not self._confirm_corner_match(scan.t_ns, base, corrected):
                match = replace(match, accepted=False, reason="confirming_local_match")
                reliable = False
        self.last_scan_match = match
        self._held_streak = 0 if reliable or not self.scan_frames else self._held_streak + 1
        if reliable:
            self._recovery_candidate = None
        recovered = None
        if not reliable and match.reason not in {"ambiguous_local_match", "confirming_local_match"}:
            recovered = self._recover_pose(points, scan, pose, base, rays, deadline_mono)
        matched_mono = time.monotonic()
        if deadline_mono is not None and matched_mono >= deadline_mono:
            return False
        if recovered is not None:
            match, corrected = recovered
            self.last_scan_match = match
            self._held_streak = 0
            self._corner_ambiguous = False
            self._corner_candidate = None
        if match.accepted:
            self.scan_match_accepted += 1
        if reliable or recovered is not None:
            pose.x_m, pose.y_m, pose.yaw_rad = corrected
        current_pose = pose.as_tuple()
        self.scans += 1
        bootstrap = not self.scan_frames and len(points) >= 16
        map_write_reason = self._corner_write_reason(scan.t_ns, pose.last_yaw_rate_radps, match, reliable)
        integrated = bool(points) and (
            bootstrap or not self.scan_matching_enabled or (reliable and map_write_reason is None)
        )
        clear_free = integrated and (bootstrap or not self.scan_matching_enabled or
                                      (match.score >= self.MIN_CLEAR_MATCH_SCORE
                                       and (match.observability is None or match.observability >= 0.025)
                                       and abs(pose.last_yaw_rate_radps) < 0.8))
        if integrated:
            integrated = self._integrate(
                points, current_pose, scan.t_ns, pose.last_vx_mps, pose.last_vy_mps,
                pose.last_yaw_rate_radps, clear_free=clear_free, rays=rays, deadline_mono=deadline_mono,
            )
            if not integrated:
                map_write_reason = "stale_before_map_write"
                clear_free = False
        if not integrated:
            self._pending_wall_clears.clear()
        integrated_mono = time.monotonic()
        map_blocked_returns = self.last_blocked_returns if integrated else None
        map_write_age_s = round((time.time_ns() - scan.t_ns) / 1e9, 4) if integrated and deadline_mono else None
        loop_closure = None
        if integrated:
            self.points += len(points)
            added = self._new_keyframe(points, current_pose, scan.t_ns, pose.last_vx_mps,
                                       pose.last_vy_mps, pose.last_yaw_rate_radps, rays)
            anchor = len(self.keyframes) - 1
            self.scan_frames.append(_ScanFrame(anchor, _relative(self.keyframes[anchor].pose, current_pose),
                                              self._pack_scan(points, scan.t_ns), scan.t_ns,
                                              pose.last_vx_mps, pose.last_vy_mps, pose.last_yaw_rate_radps,
                                              self.scans, clear_free, rays))
            if added:
                loop_deadline = min(deadline_mono, time.monotonic() + 0.05) if deadline_mono is not None else None
                if self._try_loop_closure(anchor, points, self.keyframes[anchor], loop_deadline):
                    pose.x_m, pose.y_m, pose.yaw_rad = self.keyframes[anchor].pose
                elif anchor == 0:
                    self.last_loop_closure = {"accepted": False, "reason": "first_keyframe"}
                loop_closure = dict(self.last_loop_closure)
            self.revision += 1
            self.poses.append(pose.as_tuple())
            if len(self.poses) > 5000:
                del self.poses[:-5000]
        self.history.append({
            "scan_index": self.scans,
            "t_ns": scan.t_ns,
            "pose": [round(v, 6) for v in pose.as_tuple()],
            "predicted_pose": list(base),
            "matched_pose": list(corrected),
            "body_twist": [pose.last_vx_mps, pose.last_vy_mps, pose.last_yaw_rate_radps],
            "deskew": "angle_history" if rays is not None else "packet_twist",
            "search_radius_m": radius,
            "search_yaw_radius_rad": yaw_radius,
            "map_update": "full" if clear_free else "hits_only" if integrated else "held",
            "map_write_reason": map_write_reason,
            "map_blocked_returns": map_blocked_returns,
            "map_write_age_s": map_write_age_s,
            "localization": (
                "relocalized" if recovered is not None else "tracking" if reliable
                else "ambiguous" if self._corner_ambiguous else "unconfirmed"
            ),
            "loop_closure": loop_closure,
            "occupied_cells": len(self.occupied),
            "free_cells": len(self.free),
            "keyframes": len(self.keyframes),
            "loop_closures": self.loop_closures,
            "match_ms": round((matched_mono - started_mono) * 1000, 2),
            "occupancy_ms": round((integrated_mono - matched_mono) * 1000, 2),
            "scan_match": {"accepted": match.accepted, "score": round(match.score, 6),
                           "correction_m": round(match.correction_m, 6),
                           "correction_yaw_rad": round(match.correction_yaw_rad, 6),
                           "observability": match.observability,
                           "competing_poses": [
                               {"pose": list(candidate), "score": round(score, 6),
                                "yaw_delta_from_prediction_rad": round(_wrap(candidate[2] - base[2]), 6)}
                               for candidate, score in match.competing_poses
                           ],
                           "reason": match.reason},
        })
        if len(self.history) > 5000:
            del self.history[:-5000]
        return True

    def _bounds(self) -> tuple[int, int, int, int]:
        if not self.log_odds:
            return -1, 1, -1, 1
        cells = self.log_odds.keys()
        return (min(x for x, _ in cells) - self.padding_cells,
                max(x for x, _ in cells) + self.padding_cells,
                min(y for _, y in cells) - self.padding_cells,
                max(y for _, y in cells) + self.padding_cells)

    def _payload_for(self, occupied: set[tuple[int, int]], cleaning: dict[str, Any],
                     *, wire: bool = False) -> dict[str, Any]:
        min_x, max_x, min_y, max_y = self._bounds()
        width, height = max_x - min_x + 1, max_y - min_y + 1
        grid = np.full(width * height, -1, dtype=np.int8)
        for cells, value in ((self.free, 0), (occupied, 100)):
            indices = np.fromiter(((y - min_y) * width + x - min_x for x, y in cells),
                                  dtype=np.intp, count=len(cells))
            grid[indices] = value
        if wire:
            starts = np.r_[0, np.flatnonzero(grid[1:] != grid[:-1]) + 1]
            lengths = np.diff(starts, append=grid.size)
            occupancy = {
                "occupancy_encoding": "rle-v1",
                "occupancy_length": grid.size,
                "occupancy_rle": np.column_stack((grid[starts], lengths)).tolist(),
            }
        else:
            occupancy = {"occupancy": grid.tolist()}
        return {
            "frame_id": "map", "resolution_m": self.resolution_m, "width": width, "height": height,
            "origin": [min_x * self.resolution_m, min_y * self.resolution_m, 0.0],
            **occupancy,
            "metadata": {
                "map_source": "no_ros_pose_graph_2d_lidar_slam", "map_id": self.map_id or None,
                "scans": self.scans, "points": self.points, "keyframes": len(self.keyframes),
                "row_order": "y_increasing_from_origin", "lidar_mount_m": [self.lidar_x_m, self.lidar_y_m],
                "robot_radius_m": self.robot_radius_m, "lidar_yaw_rad": self.lidar_yaw_rad,
                "scan_matching": {"enabled": self.scan_matching_enabled,
                                  "method": "coarse_to_fine_correlative_scan_to_map_every_scan",
                                  "attempts": self.scan_match_attempts, "accepted": self.scan_match_accepted,
                                  "last_score": self.last_scan_match.score,
                                  "last_reason": self.last_scan_match.reason},
                "pose_graph": {"method": "sparse_se2_least_squares_huber", "edges": len(self.graph_edges),
                               "frozen_submaps": len(self.submaps),
                               "loop_closures": self.loop_closures,
                               "optimizations": self.graph_optimizations,
                               "optimization_pending": self.graph_optimization_pending,
                               "last_loop_closure": self.last_loop_closure},
                "deskew": {"method": "angle_history_with_packet_twist_fallback",
                           "time_offset_ns": self.lidar_time_offset_ns},
                "fusion": {"method": "log_odds_replay_from_all_optimized_scan_poses",
                           "free_threshold": self.FREE_THRESHOLD,
                           "occupied_threshold": self.OCCUPIED_THRESHOLD},
                "cleaning": cleaning,
                "history": {"scan_count": self.scans, "records": self.history[-200:],
                            "trajectory": [[round(x, 6), round(y, 6), round(yaw, 6)]
                                           for x, y, yaw in self.poses[-2000:]]},
            },
        }

    def _clean_occupied(self) -> set[tuple[int, int]]:
        # Sparse N10P returns often occupy isolated 2.5 cm cells, especially
        # at longer range. Filtering connected components here erased valid
        # walls and made live maps appear blank, so SLAM hit cells are retained.
        return set(self.occupied)

    def payload(self, *, wire: bool = False) -> dict[str, Any]:
        cleaned = self._clean_occupied()
        return self._payload_for(cleaned, {"enabled": False, "method": "preserve_slam_occupied_cells",
                                           "raw_occupied_cells": len(self.occupied),
                                           "clean_occupied_cells": len(cleaned),
                                           "removed_occupied_cells": 0}, wire=wire)

    def raw_payload(self) -> dict[str, Any]:
        return self._payload_for(set(self.occupied), {"enabled": False, "method": "raw_log_odds_threshold",
                                                      "raw_occupied_cells": len(self.occupied),
                                                      "clean_occupied_cells": len(self.occupied),
                                                      "removed_occupied_cells": 0})

    def wire_payload(self) -> dict[str, Any]:
        from app.backend.manual_map import compact_map_payload
        return compact_map_payload(self.payload(wire=True))

    def save(self, root: Path) -> dict[str, Any]:
        payload, raw = self.payload(), self.raw_payload()
        (root / "map.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        (root / "map_raw.json").write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
        graph = {
            "schema": "cca-no-ros-pose-graph-slam-v1",
            "nodes": [{"pose": list(frame.pose), "t_ns": frame.t_ns,
                       "vx_mps": frame.vx, "vy_mps": frame.vy, "wz_radps": frame.wz,
                       "scan": [[angle, distance, stamp] for angle, distance, stamp in frame.scan]}
                      for frame in self.keyframes],
            "edges": [{"from": i, "to": j, "relative_pose": list(measurement), "type": kind}
                      for i, j, measurement, kind in self.graph_edges],
            "loop_closures": self.loop_closures,
            "optimizations": self.graph_optimizations,
        }
        (root / "slam_pose_graph.json").write_text(json.dumps(graph, separators=(",", ":")) + "\n",
                                                    encoding="utf-8")
        origin_x, origin_y, _ = payload["origin"]
        width, height, occupancy = payload["width"], payload["height"], payload["occupancy"]
        image = bytearray()
        for y in range(height - 1, -1, -1):
            image.extend(0 if value == 100 else 254 if value == 0 else 205
                         for value in occupancy[y * width:(y + 1) * width])
        (root / "map.pgm").write_bytes(f"P5\n{width} {height}\n255\n".encode("ascii") + bytes(image))
        (root / "map.yaml").write_text(
            "image: map.pgm\n" + f"resolution: {self.resolution_m:.6f}\n"
            + f"origin: [{origin_x:.6f}, {origin_y:.6f}, 0.0]\nnegate: 0\n"
            + "occupied_thresh: 0.65\nfree_thresh: 0.196\n", encoding="utf-8")
        return {"width": width, "height": height, "min_cell": [round(origin_x / self.resolution_m),
                round(origin_y / self.resolution_m)], "scans": self.scans, "points": self.points,
                "keyframes": len(self.keyframes), "loop_closures": self.loop_closures}
