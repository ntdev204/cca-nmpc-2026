from __future__ import annotations

import math

import pytest

from app.backend.manual_map import OccupancyMap, Pose, clean_saved_map_payload
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


def test_mapping_keeps_nearest_valid_return_per_angle() -> None:
    points = (
        LidarPoint(1, 0.5, 2.0, 100, 0),
        LidarPoint(1, 0.5, 0.0, 0, 1),
        LidarPoint(1, 0.5, 1.0, 20, 1),
    )
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
    mapper.update(LidarScan(1, points), Pose())

    assert mapper.points == 1
    assert mapper.cell(1.0 * math.cos(0.5), 1.0 * math.sin(0.5)) in mapper.occupied


def test_payload_removes_isolated_occupied_cells() -> None:
    mapper = OccupancyMap(
        0.05,
        lidar_x_m=0.0,
        lidar_y_m=0.0,
        lidar_yaw_rad=0.0,
        min_range_m=0.05,
        max_range_m=8.0,
        padding_cells=1,
        scan_matching=False,
    )
    mapper.occupied.update({(0, 0), (3, 3), (3, 4), (4, 3)})
    mapper.log_odds.update({cell: mapper.OCCUPIED_THRESHOLD for cell in mapper.occupied})

    payload = mapper.payload()
    cleaning = payload["metadata"]["cleaning"]

    assert cleaning["removed_occupied_cells"] == 1
    assert cleaning["clean_occupied_cells"] == 3


def test_saved_map_payload_is_cleaned_before_display() -> None:
    payload = {
        "width": 5,
        "height": 2,
        "occupancy": [100, -1, -1, -1, -1, -1, -1, 100, 100, 100],
        "metadata": {"scans": 1},
    }

    cleaned = clean_saved_map_payload(payload)

    assert cleaned["occupancy"] == [-1, -1, -1, -1, -1, -1, -1, 100, 100, 100]
    assert cleaned["metadata"]["cleaning"]["removed_occupied_cells"] == 1
