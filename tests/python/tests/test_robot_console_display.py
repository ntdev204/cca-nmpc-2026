from __future__ import annotations

import math
import json
from types import SimpleNamespace

import pytest

from hardware import Stm32Telemetry
from app.backend.robot_console import ConsoleApp, RobotService, copy_pose_for_mapping, decode_json_line, encode_json, smooth_display_pose
from app.backend.manual_map import Pose, pose_yaw_rate


def telemetry(*, t_ns: int, wz: float, gyro_z: float, vx: float = 0.0, vy: float = 0.0) -> Stm32Telemetry:
    return Stm32Telemetry(
        t_ns=t_ns,
        flag_stop=0,
        vx_mps=vx,
        vy_mps=vy,
        wz_radps=wz,
        accel_x_mps2=0.0,
        accel_y_mps2=0.0,
        accel_z_mps2=9.81,
        gyro_x_radps=0.0,
        gyro_y_radps=0.0,
        gyro_z_radps=gyro_z,
        voltage_v=24.0,
    )


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


def test_pose_uses_gyro_when_encoder_yaw_is_half_rate() -> None:
    yaw_rate, source = pose_yaw_rate(telemetry(t_ns=1, wz=0.30, gyro_z=0.60))
    assert yaw_rate == pytest.approx(0.60)
    assert source == "gyro_z_disagreement"
    pose = Pose(last_t_ns=1)
    pose.update(telemetry(t_ns=1, wz=0.30, gyro_z=0.60))
    pose.update(telemetry(t_ns=1_000_000_001, wz=0.30, gyro_z=0.60))
    assert pose.yaw_rad == pytest.approx(0.15, abs=1e-9)
    assert pose.last_yaw_rate_source == "gyro_z_disagreement"


def test_pose_integrates_a_half_turn_from_selected_rate() -> None:
    pose = Pose(last_t_ns=1)
    pose.update(telemetry(t_ns=1, wz=1.0, gyro_z=1.0))
    for index in range(1, 13):
        pose.update(telemetry(t_ns=1 + index * 250_000_000, wz=1.0, gyro_z=1.0))
    pose.update(telemetry(t_ns=1 + int(math.pi * 1e9), wz=1.0, gyro_z=1.0))
    assert pose.yaw_rad == pytest.approx(math.pi, abs=1e-9)


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


def test_state_payload_exposes_map_frame_pose_separately() -> None:
    service = RobotService("127.0.0.1", 0)
    service.pose = Pose(x_m=0.20, y_m=-0.10, yaw_rad=0.10)
    service.map_pose = Pose(x_m=0.35, y_m=-0.05, yaw_rad=0.08)
    service.mapper = SimpleNamespace(scan_matching_enabled=True, scans=0, points=0)
    service.stm = SimpleNamespace(
        backend="python",
        latest=Stm32Telemetry(
            t_ns=1,
            flag_stop=0,
            vx_mps=0.0,
            vy_mps=0.0,
            wz_radps=0.0,
            accel_x_mps2=0.0,
            accel_y_mps2=0.0,
            accel_z_mps2=9.81,
            gyro_x_radps=0.0,
            gyro_y_radps=0.0,
            gyro_z_radps=0.0,
            voltage_v=24.0,
        ),
    )

    payload = service._state_payload()

    assert payload["pose"] == pytest.approx([0.20, -0.10, 0.10])
    assert payload["map_pose"] == pytest.approx([0.35, -0.05, 0.08])


def test_active_odometry_scan_moves_map_marker_with_live_pose() -> None:
    service = RobotService("127.0.0.1", 0)
    service.pose = Pose(last_t_ns=1)
    service.map_pose = Pose()
    service.scan_active = True
    service.mapper = SimpleNamespace(scan_matching_enabled=False, scans=0, points=0)
    service.stm = SimpleNamespace(
        backend="python",
        latest=Stm32Telemetry(
            t_ns=1_000_000_001,
            flag_stop=0,
            vx_mps=0.4,
            vy_mps=0.0,
            wz_radps=0.0,
            accel_x_mps2=0.0,
            accel_y_mps2=0.0,
            accel_z_mps2=9.81,
            gyro_x_radps=0.0,
            gyro_y_radps=0.0,
            gyro_z_radps=0.0,
            voltage_v=24.0,
        ),
    )

    payload = service._state_payload()

    assert payload["map_pose"] == pytest.approx(payload["pose"])
    assert payload["map_pose"][0] > 0.0


def test_stream_wire_compression_round_trips_and_reduces_repetitive_map() -> None:
    payload = {"type": "map", "map": {"width": 120, "height": 80, "occupancy": [0] * 9600}}
    raw_size = len(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")) + 1
    packet = encode_json(payload)
    assert len(packet) < raw_size
    assert decode_json_line(packet) == payload
