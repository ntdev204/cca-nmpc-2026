from __future__ import annotations

import csv
import json
import math
import random

import numpy as np
import pytest

from app.backend.manual_map import OccupancyMap, Pose, RunFiles
from hardware import LidarPoint, LidarScan
from runtime.kalman import SixStateKalman
from scripts.python.tools.calibrate_lidar_time_offset import evaluate


def reference_scan() -> LidarScan:
    points = tuple(
        LidarPoint(
            1,
            math.atan2(y_m, x_m),
            math.hypot(x_m, y_m),
            20,
            0,
        )
        for x_m in (0.8, 1.2, 1.6, 2.0)
        for y_m in (-1.0, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1.0)
    )
    return LidarScan(1, points)


def test_scan_to_map_corrects_bounded_local_drift() -> None:
    mapper = OccupancyMap(
        0.05,
        lidar_x_m=0.0,
        lidar_y_m=0.0,
        lidar_yaw_rad=0.0,
        min_range_m=0.05,
        max_range_m=8.0,
        padding_cells=2,
    )
    scan = reference_scan()
    mapper.update(scan, Pose())
    drifted_pose = Pose(x_m=0.10)

    mapper.update(scan, drifted_pose)

    assert mapper.last_scan_match.accepted
    assert mapper.last_scan_match.score >= 0.20
    assert mapper.scan_match_attempts == 1
    assert mapper.scan_match_accepted == 1
    assert drifted_pose.x_m == pytest.approx(0.0, abs=0.051)
    assert mapper.payload()["metadata"]["scan_matching"]["accepted"] == 1


def test_scan_matching_can_be_disabled_without_changing_pose() -> None:
    mapper = OccupancyMap(
        0.05,
        lidar_x_m=0.0,
        lidar_y_m=0.0,
        lidar_yaw_rad=0.0,
        min_range_m=0.05,
        max_range_m=8.0,
        padding_cells=2,
        scan_matching=False,
    )
    pose = Pose()
    mapper.update(reference_scan(), pose)

    assert pose.as_tuple() == (0.0, 0.0, 0.0)
    assert mapper.last_scan_match.reason == "disabled"
    assert mapper.scan_match_attempts == 0


def make_mapper() -> OccupancyMap:
    return OccupancyMap(
        0.025, lidar_x_m=0.0, lidar_y_m=0.0, lidar_yaw_rad=0.0,
        min_range_m=0.05, max_range_m=8.0, padding_cells=2,
        defer_graph_optimization=True,
    )


def make_scan(xy: list[tuple[float, float]], stamp: int = 1) -> LidarScan:
    return LidarScan(stamp, tuple(
        LidarPoint(stamp, math.atan2(y, x), math.hypot(x, y), 20, 0) for x, y in xy
    ))


def distinctive_points() -> list[tuple[float, float]]:
    rng = random.Random(88)
    return [(rng.uniform(0.8, 2.4), rng.uniform(-1.4, 1.4)) for _ in range(60)]


def test_weak_match_keeps_grid_pose_and_graph_unchanged() -> None:
    mapper = make_mapper()
    mapper.update(make_scan(distinctive_points()), Pose())
    prior = dict(mapper.log_odds)
    revision = mapper.revision
    pose = Pose(x_m=10.0)

    assert mapper.update(make_scan(distinctive_points(), 200_000_001), pose)

    assert mapper.history[-1]["map_update"] == "held"
    assert mapper.log_odds == prior
    assert mapper.revision == revision
    assert len(mapper.scan_frames) == len(mapper.keyframes) == 1
    assert pose.as_tuple() == (10.0, 0.0, 0.0)


def test_strong_wall_requires_consecutive_scans_and_one_vote_per_scan() -> None:
    mapper = make_mapper()
    wall = mapper.cell(1.0, 0.0)
    mapper._apply_evidence(wall, 3.0)
    passing_rays = ((0.0, 2.0, 1),) * 10
    pose = (0.0, 0.0, 0.0)

    mapper._integrate(passing_rays, pose, 1, 0.0, 0.0, 0.0)
    assert mapper.log_odds[wall] == 3.0
    mapper._integrate(passing_rays, pose, 2, 0.0, 0.0, 0.0, clear_free=False)
    mapper._integrate(passing_rays, pose, 3, 0.0, 0.0, 0.0)
    assert mapper.log_odds[wall] == 3.0
    mapper._integrate(passing_rays, pose, 4, 0.0, 0.0, 0.0)
    assert mapper.log_odds[wall] == pytest.approx(2.65)


def test_capture_preserves_point_timing_without_changing_lidar_csv(tmp_path) -> None:
    scan = LidarScan(100, (LidarPoint(80, 0.0, 1.0, 20, 0), LidarPoint(96, 0.1, 1.2, 20, 0)))
    root = tmp_path / "run"
    files = RunFiles(root)
    try:
        files.scan(scan)
        files.write_map_history({"t_ns": scan.t_ns}, scan)
    finally:
        files.close()
    history = json.loads((root / "map_history.jsonl").read_text())
    assert history["lidar_point_offsets_ns"] == [-20, -4]
    with (root / "lidar.csv").open(newline="") as stream:
        row = next(csv.DictReader(stream))
    assert tuple(row) == ("t_ns", "point_count", "points_json")
    assert len(json.loads(row["points_json"])[0]) == 4


@pytest.mark.parametrize("scenario,expected", [
    ("same_place", True), ("self_match", False), ("corridor", False),
])
def test_loop_closure_uses_historical_geometry(scenario: str, expected: bool) -> None:
    mapper = make_mapper()
    if scenario == "corridor":
        old_xy = [(x * 0.05, y) for x in range(-20, 21) for y in (-1.0, 1.0)]
    else:
        old_xy = distinctive_points()
    query_xy = [(-x, y) for x, y in old_xy] if scenario == "self_match" else old_xy
    old = mapper._scan_points(make_scan(old_xy))
    query = mapper._scan_points(make_scan(query_xy))
    origin = (0.0, 0.0, 0.0)
    mapper._new_keyframe(old, origin, 1, 0.0, 0.0, 0.0)
    for i in range(mapper.LOOP_MIN_SEPARATION + mapper.SUBMAP_KEYFRAMES):
        mapper._new_keyframe(old, (3.0 + i, 0.0, 0.0), i + 2, 0.0, 0.0, 0.0)
    mapper._new_keyframe(query, origin, 50, 0.0, 0.0, 0.0)
    # Give the live map every query hit. This map must not validate its own scan.
    mapper.occupied = {mapper.cell(x, y) for x, y in query_xy}
    mapper._try_loop_closure(len(mapper.keyframes) - 1, query, mapper.keyframes[-1])

    assert mapper.last_loop_closure["accepted"] is expected
    assert mapper.graph_optimization_pending is expected
    if scenario == "corridor":
        assert mapper.last_loop_closure["reason"] == "ambiguous_loop_match"


@pytest.mark.parametrize("direction", [1, -1])
def test_deskew_combined_motion_both_scan_directions(direction: int) -> None:
    mapper = make_mapper()
    mapper.lidar_time_offset_ns = 20_000_000
    reference = 1_000_000_000
    period = 100_000_000
    points = []
    for i in range(120):
        dt = -0.1 + 0.1 * i / 120
        x, y, yaw = 0.45 * dt, -0.20 * dt, 0.8 * dt
        angle = (direction * i * math.tau / 120) % math.tau
        dx, dy = math.cos(yaw + angle), math.sin(yaw + angle)
        distance = min((math.copysign(2, dx) - x) / dx, (math.copysign(2, dy) - y) / dy)
        points.append(LidarPoint(reference, angle, distance, 20, 0))
    scan = LidarScan(reference + mapper.lidar_time_offset_ns, tuple(points), period)
    samples = tuple((reference + i * 20_000_000, 0.45 * i * 0.02, -0.20 * i * 0.02, 0.8 * i * 0.02)
                    for i in range(-6, 2))
    rays = mapper._deskew_rays(scan, mapper._scan_points(scan), samples)
    assert rays is not None
    assert max(abs(max(abs(ex), abs(ey)) - 2) for _, _, ex, ey in rays) < 1e-8
    assert mapper._deskew_rays(scan, mapper._scan_points(scan), samples[-2:]) is None


def test_continuous_refinement_improves_subcell_alignment() -> None:
    mapper = make_mapper()
    res = mapper.resolution_m
    cells = ({(40, y) for y in range(-31, 31)} |
             {(x, 32) for x in range(45, 88)} |
             {(x, -33) for x in range(40, 68)})
    endpoints = np.asarray([((x+0.5)*res, (y+0.5)*res) for x, y in sorted(cells)])
    tile = mapper._match_grid((0, 0, 0), 3, cells, dilation=0)
    seed = (0.009, -0.006, math.radians(0.2))
    result, observability = mapper._refine_pose(endpoints, seed, seed, tile)
    assert observability >= 0.025
    assert math.hypot(*result[:2]) < math.hypot(*seed[:2])
    assert abs(result[2]) < abs(seed[2])


def test_continuous_refinement_preserves_prior_along_unobservable_wall() -> None:
    mapper = make_mapper()
    res = mapper.resolution_m
    cells = {(x, 40) for x in range(-95, 96)}
    endpoints = np.asarray([((x+0.5)*res, 40.5*res) for x in range(-40, 41)])
    tile = mapper._match_grid((0, 0, 0), 3, cells, dilation=0)
    result, observability = mapper._refine_pose(endpoints, (0.08, 0.008, 0), (0, 0, 0), tile)
    assert observability < 0.025
    assert result[0] == pytest.approx(0, abs=1e-8)


def test_graph_snapshot_install_keeps_new_scans() -> None:
    mapper = make_mapper()
    mapper.scan_matching_enabled = False
    for i in range(3):
        stamp = 1 + i * 200_000_000
        mapper.update(make_scan(distinctive_points(), stamp), Pose(x_m=i * 0.2))
    mapper.graph_edges.append((0, 2, (0.3, 0.0, 0.0), "loop_closure"))
    mapper.loop_closures = 1
    mapper.graph_optimization_pending = True
    original = dict(mapper.log_odds)
    snapshot = mapper.optimization_snapshot()
    snapshot.optimize_pending_graph()
    assert mapper.log_odds == original
    mapper.update(make_scan(distinctive_points(), 600_000_001), Pose(x_m=0.6))
    assert mapper.install_optimized_snapshot(snapshot)
    assert len(mapper.poses) == len(mapper.scan_frames) == 4
    assert mapper.poses[-1][0] == pytest.approx(mapper.poses[-2][0] + 0.2)
    assert not mapper.graph_optimization_pending


def test_calibration_recovers_synthetic_receive_delay(tmp_path) -> None:
    root = tmp_path / "turn"
    files = RunFiles(root)
    delay_ns = 40_000_000
    origin = 1_000_000_000

    def yaw_at(dt: float) -> float:
        return max(0.0, dt - 0.9) * 0.8

    try:
        for i in range(180):
            dt = i * 0.02
            files.write("robot_state.csv", {
                "t_ns": origin + i * 20_000_000, "x_m": 0, "y_m": 0, "yaw_rad": yaw_at(dt),
                "vx_mps": 0, "vy_mps": 0, "wz_radps": 0.8 if dt > 0.9 else 0,
            })
        for i in range(2, 34):
            stamp = origin + i * 100_000_000 + delay_ns
            points = []
            for j in range(180):
                angle = j * math.tau / 180
                yaw = yaw_at(i * 0.1 - 0.1 + 0.1 * j / 180)
                x, y = 0.1 * math.cos(yaw), 0.1 * math.sin(yaw)
                dx, dy = math.cos(yaw + angle), math.sin(yaw + angle)
                distance = min((math.copysign(2, d) - p) / d
                               for d, p in ((dx, x), (dy, y)) if abs(d) > 1e-12)
                points.append(LidarPoint(stamp, angle, distance, 20, 0))
            scan = LidarScan(stamp, tuple(points), 100_000_000)
            files.scan(scan)
            files.write_map_history({"t_ns": stamp}, scan)
    finally:
        files.close()
    scores = evaluate(root, [0, 40, 80])
    assert min(scores, key=lambda row: row["mean_clipped_distance_m"])["offset_ms"] == 40


def test_stationary_update_keeps_pose_fixed_with_imu_bias() -> None:
    ekf = SixStateKalman(state=[1.0, 2.0, 0.5, -0.06, 0.01, -0.006])
    for i in range(200):
        state = ekf.step(1 + i * 50_000_000, (0, 0, 0), acceleration_body_mps2=(-0.55, 0.09),
                         gyro_z_radps=-0.03, stationary=True)
    assert state.tolist() == pytest.approx([1.0, 2.0, 0.5, 0.0, 0.0, 0.0])
    assert ekf.motion_mode == "stationary_zero_velocity"


def test_relocalization_requires_two_consistent_matches_before_pose_change() -> None:
    mapper = make_mapper()
    rng = random.Random(80)
    geometry = [(rng.uniform(0.6, 2.8), rng.uniform(-2, 2)) for _ in range(120)]
    mapper.update(make_scan(geometry), Pose())
    previous_grid = dict(mapper.log_odds)
    for i in range(1, 9):
        pose = Pose(x_m=0.4)
        mapper.update(make_scan(geometry, 1 + i * 200_000_000), pose)
        if i < 8:
            assert pose.x_m == pytest.approx(0.4)
    assert mapper.last_scan_match.reason == "relocalized"
    assert pose.x_m == pytest.approx(0.0, abs=0.025)
    assert mapper.log_odds == previous_grid
    mapper.update(make_scan(geometry, 1_800_000_001), Pose())
    assert len(mapper.scan_frames) == 2


def test_turn_with_competing_wall_matches_holds_map_until_confirmed() -> None:
    mapper = make_mapper()
    geometry = distinctive_points()
    mapper.update(make_scan(geometry), Pose())
    original_occupied = mapper.occupied.copy()
    mapper.occupied.update(mapper.cell(x + 0.10, y) for x, y in geometry)
    before = dict(mapper.log_odds)
    turning = Pose(x_m=0.05, last_yaw_rate_radps=0.35)

    mapper.update(make_scan(geometry, 200_000_001), turning)

    assert mapper.last_scan_match.reason == "ambiguous_local_match"
    assert len(mapper.history[-1]["scan_match"]["competing_poses"]) == 2
    assert mapper.history[-1]["map_update"] == "held"
    assert turning.x_m == pytest.approx(0.05)
    assert mapper.log_odds == before

    mapper.occupied = original_occupied
    mapper.update(make_scan(geometry, 400_000_001), Pose())
    assert mapper.last_scan_match.reason == "confirming_local_match"
    assert mapper.history[-1]["map_update"] == "held"
    mapper.update(make_scan(geometry, 600_000_001), Pose())
    assert mapper.history[-1]["localization"] == "tracking"
    assert len(mapper.scan_frames) == 2
