"""No-ROS 2D LiDAR SLAM: scan-to-map matching, pose graph, and occupancy replay."""
from __future__ import annotations

import json
import math
from array import array
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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


@dataclass
class _ScanFrame:
    anchor: int
    relative_pose: tuple[float, float, float]
    data: array
    t_ns: int
    vx: float
    vy: float
    wz: float


@dataclass(frozen=True)
class _MatchResult:
    accepted: bool
    score: float
    inliers: int
    point_count: int
    correction_m: float
    correction_yaw_rad: float
    reason: str


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
    MAX_KEYFRAME_POINTS = 240
    LOOP_MIN_SEPARATION = 18
    LOOP_SEARCH_RADIUS_M = 0.45
    LOOP_SEARCH_YAW_RAD = math.radians(12.0)
    LOOP_MIN_SCORE = 0.38

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
        self.poses: list[tuple[float, float, float]] = []
        self.history: list[dict[str, Any]] = []
        self.keyframes: list[_Keyframe] = []
        self.scan_frames: list[_ScanFrame] = []
        self.graph_edges: list[tuple[int, int, tuple[float, float, float], str]] = []
        self.scans = 0
        self.points = 0
        self.scan_match_attempts = 0
        self.scan_match_accepted = 0
        self.loop_closures = 0
        self.graph_optimizations = 0
        self.revision = 0
        self.last_scan_match = self._match_result(False, "not_run")
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

    def _score(self, endpoints: tuple[tuple[float, float], ...], pose: tuple[float, float, float]) -> float:
        if not endpoints or len(self.occupied) < 12:
            return 0.0
        cosine, sine = math.cos(pose[2]), math.sin(pose[2])
        hits = 0
        for local_x, local_y in endpoints:
            x = pose[0] + cosine * local_x - sine * local_y
            y = pose[1] + sine * local_x + cosine * local_y
            cx, cy = self.cell(x, y)
            if any((cx + dx, cy + dy) in self.occupied for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                hits += 1
        return hits / len(endpoints)

    def _match(self, points: tuple[tuple[float, float, int], ...], base: tuple[float, float, float],
               scan_t_ns: int, vx: float, vy: float, wz: float, *, radius: float = 0.15,
               yaw_radius: float = math.radians(7.0),
               require_improvement: bool = True) -> tuple[_MatchResult, tuple[float, float, float]]:
        if not self.scan_matching_enabled:
            return self._match_result(False, "disabled"), base
        if len(self.occupied) < 12 or len(points) < 16:
            return self._match_result(False, "insufficient_features", count=len(points)), base
        self.scan_match_attempts += 1
        endpoints = self._local_endpoints(points, scan_t_ns, vx, vy, wz)
        best = base
        base_score = self._score(endpoints, base)
        best_score = base_score
        # Coarse-to-fine correlative scan matching, bounded around odometry.
        for step_xy, step_yaw, factor in (
            (0.05, math.radians(3.0), 1.0),
            (0.02, math.radians(1.0), 0.5),
        ):
            center = best
            radius_xy = radius if factor == 1.0 else 0.04
            radius_yaw_now = yaw_radius if factor == 1.0 else math.radians(2.0)
            nx = max(1, int(math.ceil(radius_xy / step_xy)))
            nyaw = max(1, int(math.ceil(radius_yaw_now / step_yaw)))
            for ix in range(-nx, nx + 1):
                for iy in range(-nx, nx + 1):
                    for it in range(-nyaw, nyaw + 1):
                        candidate = (center[0] + ix * step_xy, center[1] + iy * step_xy,
                                     _wrap(center[2] + it * step_yaw))
                        score = self._score(endpoints, candidate)
                        movement_penalty = 0.0005 * (ix * ix + iy * iy + it * it)
                        if score - movement_penalty > best_score:
                            best, best_score = candidate, score
        correction = _relative(base, best)
        accepted = best_score >= 0.22 and (not require_improvement or best_score >= base_score + 0.015)
        if not accepted:
            return self._match_result(False, "weak_match", best_score, len(points)), base
        return self._match_result(True, "matched", best_score, len(points), correction), best

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
                   scan_t_ns: int, vx: float, vy: float, wz: float) -> None:
        for point in points:
            sx, sy, ex, ey = self._world_endpoint(point, pose, scan_t_ns, vx, vy, wz)
            start = self.cell(sx, sy)
            ray = bresenham(start, self.cell(ex, ey))
            for cell in ray[:-1]:
                wx, wy = (cell[0] + 0.5) * self.resolution_m, (cell[1] + 0.5) * self.resolution_m
                if math.hypot(wx - pose[0], wy - pose[1]) > self.robot_radius_m:
                    self._apply_evidence(cell, self.FREE_EVIDENCE)
            self._apply_evidence(ray[-1], self.OCCUPIED_EVIDENCE)

    def _new_keyframe(self, points: tuple[tuple[float, float, int], ...], pose: tuple[float, float, float],
                      scan_t_ns: int, vx: float, vy: float, wz: float) -> bool:
        if not self.keyframes:
            self.keyframes.append(_Keyframe(pose, points, scan_t_ns, vx, vy, wz))
            return True
        previous = self.keyframes[-1]
        distance = math.hypot(pose[0] - previous.pose[0], pose[1] - previous.pose[1])
        turn = abs(_wrap(pose[2] - previous.pose[2]))
        if distance < self.KEYFRAME_DISTANCE_M and turn < self.KEYFRAME_YAW_RAD and scan_t_ns - previous.t_ns < self.KEYFRAME_MAX_PERIOD_NS:
            return False
        index = len(self.keyframes)
        self.graph_edges.append((index - 1, index, _relative(previous.pose, pose), "odometry"))
        self.keyframes.append(_Keyframe(pose, points, scan_t_ns, vx, vy, wz))
        return True

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
                          current: _Keyframe) -> bool:
        if current_index < self.LOOP_MIN_SEPARATION:
            self.last_loop_closure = {"accepted": False, "reason": "insufficient_keyframes"}
            return False
        candidates = []
        for index, frame in enumerate(self.keyframes[:-self.LOOP_MIN_SEPARATION]):
            distance = math.hypot(current.pose[0] - frame.pose[0], current.pose[1] - frame.pose[1])
            if distance < 1.5:
                candidates.append((distance, index, frame))
        if not candidates:
            self.last_loop_closure = {"accepted": False, "reason": "no_nearby_old_keyframe"}
            return False
        for _, index, frame in sorted(candidates)[:3]:
            match, corrected = self._match(points, frame.pose, current.t_ns, current.vx, current.vy, current.wz,
                                           radius=self.LOOP_SEARCH_RADIUS_M, yaw_radius=self.LOOP_SEARCH_YAW_RAD,
                                           require_improvement=False)
            if match.accepted and match.score >= self.LOOP_MIN_SCORE:
                measurement = _relative(frame.pose, corrected)
                self.graph_edges.append((index, current_index, measurement, "loop_closure"))
                self.loop_closures += 1
                self.last_loop_closure = {"accepted": True, "from_keyframe": index,
                                          "to_keyframe": current_index, "score": match.score}
                self._optimize_graph()
                return True
        self.last_loop_closure = {"accepted": False, "reason": "no_consistent_scan_match"}
        return False

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
            _Keyframe(tuple(float(v) for v in optimized[i]), frame.scan, frame.t_ns, frame.vx, frame.vy, frame.wz)
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
        corrected_poses = []
        for frame in self.scan_frames:
            anchor_pose = self.keyframes[frame.anchor].pose
            pose = _compose(anchor_pose, frame.relative_pose)
            corrected_poses.append(pose)
            self._integrate(self._unpack_scan(frame), pose, frame.t_ns, frame.vx, frame.vy, frame.wz)
        self.poses = corrected_poses[-5000:]

    def update(self, scan: LidarScan, pose: Any) -> None:
        points = self._scan_points(scan)
        base = pose.as_tuple()
        match, corrected = self._match(points, base, scan.t_ns, pose.last_vx_mps,
                                       pose.last_vy_mps, pose.last_yaw_rate_radps)
        self.last_scan_match = match
        if match.accepted:
            self.scan_match_accepted += 1
            pose.x_m, pose.y_m, pose.yaw_rad = corrected
        current_pose = pose.as_tuple()
        self._integrate(points, current_pose, scan.t_ns, pose.last_vx_mps,
                        pose.last_vy_mps, pose.last_yaw_rate_radps)
        self.scans += 1
        self.points += len(points)
        added = self._new_keyframe(points, current_pose, scan.t_ns, pose.last_vx_mps,
                                   pose.last_vy_mps, pose.last_yaw_rate_radps)
        anchor = len(self.keyframes) - 1
        anchor_pose = self.keyframes[anchor].pose
        self.scan_frames.append(_ScanFrame(anchor, _relative(anchor_pose, current_pose),
                                          self._pack_scan(points, scan.t_ns), scan.t_ns,
                                          pose.last_vx_mps, pose.last_vy_mps,
                                          pose.last_yaw_rate_radps))
        if added:
            index = len(self.keyframes) - 1
            closed = self._try_loop_closure(index, points, self.keyframes[index])
            if not closed and index == 0:
                self.last_loop_closure = {"accepted": False, "reason": "first_keyframe"}
            if closed:
                pose.x_m, pose.y_m, pose.yaw_rad = self.keyframes[index].pose
        self.revision += 1
        self.poses.append(pose.as_tuple())
        if len(self.poses) > 5000:
            del self.poses[:-5000]
        self.history.append({
            "scan_index": self.scans,
            "t_ns": scan.t_ns,
            "pose": [round(v, 6) for v in pose.as_tuple()],
            "occupied_cells": len(self.occupied),
            "free_cells": len(self.free),
            "keyframes": len(self.keyframes),
            "loop_closures": self.loop_closures,
            "scan_match": {"accepted": match.accepted, "score": round(match.score, 6),
                           "correction_m": round(match.correction_m, 6),
                           "correction_yaw_rad": round(match.correction_yaw_rad, 6),
                           "reason": match.reason},
        })
        if len(self.history) > 5000:
            del self.history[:-5000]

    def _bounds(self) -> tuple[int, int, int, int]:
        if not self.log_odds:
            return -1, 1, -1, 1
        cells = self.log_odds.keys()
        return (min(x for x, _ in cells) - self.padding_cells,
                max(x for x, _ in cells) + self.padding_cells,
                min(y for _, y in cells) - self.padding_cells,
                max(y for _, y in cells) + self.padding_cells)

    def _payload_for(self, occupied: set[tuple[int, int]], cleaning: dict[str, Any]) -> dict[str, Any]:
        min_x, max_x, min_y, max_y = self._bounds()
        width, height = max_x - min_x + 1, max_y - min_y + 1
        occupancy = [100 if (x, y) in occupied else 0 if (x, y) in self.free else -1
                     for y in range(min_y, max_y + 1) for x in range(min_x, max_x + 1)]
        return {
            "frame_id": "map", "resolution_m": self.resolution_m, "width": width, "height": height,
            "origin": [min_x * self.resolution_m, min_y * self.resolution_m, 0.0],
            "occupancy": occupancy,
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
                               "loop_closures": self.loop_closures,
                               "optimizations": self.graph_optimizations,
                               "last_loop_closure": self.last_loop_closure},
                "deskew": {"method": "packet_timestamp_twist_interpolation",
                           "limitation": "N10P does not expose per_beam acquisition timestamps"},
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

    def payload(self) -> dict[str, Any]:
        cleaned = self._clean_occupied()
        return self._payload_for(cleaned, {"enabled": False, "method": "preserve_slam_occupied_cells",
                                           "raw_occupied_cells": len(self.occupied),
                                           "clean_occupied_cells": len(cleaned),
                                           "removed_occupied_cells": 0})

    def raw_payload(self) -> dict[str, Any]:
        return self._payload_for(set(self.occupied), {"enabled": False, "method": "raw_log_odds_threshold",
                                                      "raw_occupied_cells": len(self.occupied),
                                                      "clean_occupied_cells": len(self.occupied),
                                                      "removed_occupied_cells": 0})

    def wire_payload(self) -> dict[str, Any]:
        from app.backend.manual_map import compact_map_payload
        return compact_map_payload(self.payload())

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
