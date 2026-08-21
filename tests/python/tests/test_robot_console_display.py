from __future__ import annotations

import math

import pytest

from tools.robot_console import ConsoleApp, copy_pose_for_mapping, smooth_display_pose
from tools.manual_map import Pose


def test_display_pose_filter_does_not_jump_to_a_new_sample() -> None:
    previous = (0.0, 0.0, 0.0)
    filtered = smooth_display_pose(previous, (1.0, -1.0, 1.0), 0.06)
    assert 0.0 < filtered[0] < 1.0
    assert -1.0 < filtered[1] < 0.0
    assert 0.0 < filtered[2] < 1.0


def test_display_pose_filter_wraps_yaw_on_the_short_arc() -> None:
    filtered = smooth_display_pose((0.0, 0.0, math.pi - 0.02), (-0.1, 0.0, -math.pi + 0.02), 0.06)
    assert abs(abs(filtered[2]) - math.pi) < 0.02


def test_display_pose_filter_rejects_invalid_timing() -> None:
    with pytest.raises(ValueError, match="display pose timing"):
        smooth_display_pose((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), -0.1)


def test_saved_map_payload_validation_accepts_grid() -> None:
    payload = ConsoleApp._validate_map_payload(
        {
            "width": 2,
            "height": 2,
            "resolution_m": 0.05,
            "origin": [0.0, 0.0, 0.0],
            "occupancy": [0, 100, -1, 0],
        }
    )
    assert payload["width"] == 2


def test_saved_map_payload_validation_rejects_short_grid() -> None:
    with pytest.raises(ValueError, match="map dimensions"):
        ConsoleApp._validate_map_payload({"width": 2, "height": 2, "occupancy": [0, 100]})


def test_mapping_pose_copy_keeps_live_odometry_independent() -> None:
    live_pose = Pose(x_m=1.0, y_m=-0.5, yaw_rad=0.2, last_t_ns=42)
    map_pose = copy_pose_for_mapping(live_pose)
    map_pose.x_m = 0.0
    map_pose.y_m = 0.0
    map_pose.yaw_rad = 0.0
    assert live_pose.as_tuple() == (1.0, -0.5, 0.2)
    assert map_pose.last_t_ns == live_pose.last_t_ns
