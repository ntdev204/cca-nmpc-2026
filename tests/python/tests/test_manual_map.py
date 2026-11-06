from __future__ import annotations

import csv
import json
import math
import random

import pytest

from app.backend.manual_map import OccupancyMap, Pose, RunFiles
from hardware import LidarPoint, LidarScan


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
    for i in range(mapper.LOOP_MIN_SEPARATION):
        mapper._new_keyframe(old, (3.0 + i, 0.0, 0.0), i + 2, 0.0, 0.0, 0.0)
    mapper._new_keyframe(query, origin, 50, 0.0, 0.0, 0.0)
    # Give the live map every query hit. This map must not validate its own scan.
    mapper.occupied = {mapper.cell(x, y) for x, y in query_xy}
    mapper._try_loop_closure(len(mapper.keyframes) - 1, query, mapper.keyframes[-1])

    assert mapper.last_loop_closure["accepted"] is expected
    assert mapper.graph_optimization_pending is expected
    if scenario == "corridor":
        assert mapper.last_loop_closure["reason"] == "ambiguous_loop_match"
