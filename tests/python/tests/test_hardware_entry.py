from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import pytest

from tools.hardware_entry import _capture_preflight, prepare, robot_spec, schedule
from ai.detection import POSE_ENGINE_SCHEMA
from shared import sha256_file
from hardware import RobotGeometry


def _physical_spec(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema": "cca-physical-robot-v1",
                "status": "measured",
                "robot_model": "mini_mec_robot",
                "measured_at_utc": "2026-08-14T00:00:00Z",
                "measured_by": "test",
                "method": "caliper_and_floor_trace",
                "wheel_radius_m": 0.036,
                "half_length_m": 0.12,
                "half_width_m": 0.10,
                "footprint_radius_m": 0.16,
                "wheel_signs": {"fl": 1, "fr": 1, "rl": 1, "rr": 1},
                "notes": "test fixture",
            }
        ),
        encoding="utf-8",
    )
    return path


def test_robot_spec_binds_mini_mec_wheels_and_sensor_mounts() -> None:
    spec = robot_spec()
    assert spec["model"] == "mini_mec_robot"
    assert spec["urdf_package"]["name"] == "rai_robot_urdf"
    assert "mini_mec_robot" in spec["urdf_package"]["available_urdf_models"]
    assert spec["urdf_package"]["install_directories"] == ["meshes", "rviz", "urdf"]
    assert spec["wheel_radius_m"] == 0.0363
    assert spec["half_length_m"] > 0.08
    assert spec["half_width_m"] > 0.09
    assert spec["footprint"]["footprint_radius_m"] == pytest.approx(0.1772541986)
    assert spec["camera_joint"]["xyz_m"][2] == 0.21
    assert spec["laser_joint"]["xyz_m"][2] > 0.09
    assert spec["urdf_package"]["urdf_catalog"]["count"] >= 30
    assert set(spec["components"]["wheels"]) == {"fl", "fr", "rl", "rr"}
    assert spec["components"]["wheels"]["fl"]["joint"] == "lf_wheel_joint"
    assert spec["components"]["sensors"]["camera"]["hardware_target"] == "Astra-S"
    assert spec["components"]["sensors"]["lidar"]["hardware_target"] == "N10P"
    assert spec["xacro_sensor_contract"]["lidar"]["horizontal_samples"] == 360
    assert spec["xacro_sensor_contract"]["camera"]["width_px"] == 640
    assert spec["xacro_sensor_contract"]["depth_camera"]["height_px"] == 480
    assert spec["xacro_sensor_contract"]["imu"]["update_rate_hz"] == 100.0
    assert set(spec["mesh_inventory"]["mini_mec_robot"]) >= {
        "base_link.STL",
        "controller_link.STL",
        "lf_wheel_link.STL",
        "rf_wheel_link.STL",
        "camera_link.STL",
        "laser.STL",
    }
    assert set(spec["mesh_inventory"]["sensor_library"]) == {"astra.dae", "lds.stl", "r200.dae"}


def test_prepare_config_is_geometry_resolvable(tmp_path: Path) -> None:
    output = tmp_path / "hardware.json"
    physical_spec = _physical_spec(tmp_path / "physical.json")
    prepare(
        argparse.Namespace(
            output=output,
            stm_port="/dev/rai_controller",
            lidar_port="/dev/rai_lidar",
            lidar_baud=460800,
            firmware="fw-2026-08-13",
            camera_uri=None,
            sdk_path=None,
            max_pair_skew_us=None,
            clock="system_time",
            physical_spec=physical_spec,
        )
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["transport"] == "stm32_serial"
    assert payload["lidar"]["protocol_profile"] == "n10p-108b-v1"
    assert payload["state_definition"] == ["x_m", "y_m", "theta_rad", "vx_mps", "vy_mps", "omega_radps"]
    assert payload["urdf_path"] is None
    assert payload["urdf_source"] == "mini_mec_robot"
    assert payload["footprint"]["footprint_radius_m"] == pytest.approx(0.16)
    assert payload["geometry_authority"] == "measured_physical_spec"
    geometry = RobotGeometry.from_json(output)
    assert geometry.wheel_radius_m == pytest.approx(0.036)
    assert geometry.half_length_m == pytest.approx(0.12)


def test_user_physical_spec_exports_sensor_mounts(tmp_path: Path) -> None:
    output = tmp_path / "hardware-user-spec.json"
    prepare(
        argparse.Namespace(
            output=output,
            stm_port="/dev/rai_controller",
            lidar_port="/dev/rai_lidar",
            lidar_baud=460800,
            firmware="fw-user-spec",
            camera_uri=None,
            sdk_path=None,
            max_pair_skew_us=None,
            clock="system_time",
            physical_spec=Path("configs/physical_robot.json"),
        )
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["wheel_radius_m"] == pytest.approx(0.05)
    assert payload["half_length_m"] == pytest.approx(0.2)
    assert payload["half_width_m"] == pytest.approx(0.2)
    assert payload["footprint"]["footprint_radius_m"] == pytest.approx(0.282842712474619)
    assert payload["sensor_mounts"]["lidar_height_m"] == pytest.approx(0.24)
    assert payload["sensor_mounts"]["camera_height_m"] == pytest.approx(0.2)
    assert payload["sensor_mounts"]["lidar_front_edge_distance_m"] == pytest.approx(0.1)
    assert payload["sensor_mounts"]["camera_front_edge_distance_m"] == pytest.approx(0.035)
    assert payload["sensor_mounts"]["lidar_position_x_m"] == pytest.approx(0.1)
    assert payload["sensor_mounts"]["camera_position_x_m"] == pytest.approx(0.165)
    assert payload["sensor_mounts"]["camera_pitch_deg"] == pytest.approx(-20.0)


def test_prepare_without_physical_spec_is_fail_closed(tmp_path: Path) -> None:
    output = tmp_path / "pending.json"
    prepare(
        argparse.Namespace(
            output=output,
            stm_port="COM0",
            lidar_port="COM1",
            lidar_baud=460800,
            firmware="fw-pending",
            camera_uri=None,
            sdk_path=None,
            max_pair_skew_us=None,
            clock="system_time",
            physical_spec=None,
        )
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["geometry_authority"] == "pending_physical_measurement"
    assert payload["wheel_radius_m"] is None
    with pytest.raises(ValueError, match="measured physical specification"):
        RobotGeometry.from_json(output)


def test_schedule_has_explicit_zero_tail(tmp_path: Path) -> None:
    output = tmp_path / "commands.csv"
    schedule(
        argparse.Namespace(
            output=output,
            kind="lateral",
            duration_s=0.3,
            step_s=0.1,
            speed_mps=0.05,
            angular_radps=0.2,
        )
    )
    with output.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert rows[-1]["t_s"] == "0.3"
    assert rows[-1]["vx_mps"] == "0.0"
    assert rows[-1]["vy_mps"] == "0.0"
    assert rows[-1]["wz_radps"] == "0.0"


def test_capture_preflight_validates_inputs_without_opening_devices(tmp_path: Path) -> None:
    config_path = tmp_path / "hardware.json"
    physical_spec = _physical_spec(tmp_path / "physical.json")
    prepare(
        argparse.Namespace(
            output=config_path,
            stm_port="/dev/rai_controller",
            lidar_port="/dev/rai_lidar",
            lidar_baud=460800,
            firmware="fw-2026-08-14",
            camera_uri=None,
            sdk_path=None,
            max_pair_skew_us=None,
            clock="system_time",
            physical_spec=physical_spec,
        )
    )
    calibration_path = tmp_path / "calibration.json"
    calibration_path.write_text(
        json.dumps(
            {
                "schema": "cca-capture-calibration-v1",
                "calibration_id": "cal-preflight-01",
                "camera": "Astra-S",
                "lidar": "N10P",
                "robot_frame": "base_link",
                "calibrated_at_utc": "2026-08-14T00:00:00Z",
                "camera_intrinsics": {"fx": 500.0, "fy": 500.0, "cx": 320.0, "cy": 240.0, "width": 640, "height": 480},
                "camera_to_robot": {"translation_m": [0.1, 0.0, 0.2], "rpy_rad": [0.0, 0.0, 0.0]},
                "lidar_to_robot": {"translation_m": [0.0, 0.0, 0.1], "rpy_rad": [0.0, 0.0, 0.0]},
                "quality": {"camera_reprojection_rmse_px": 0.5, "lidar_alignment_rmse_m": 0.01},
            }
        ),
        encoding="utf-8",
    )
    map_path = tmp_path / "map.json"
    map_path.write_text(
        json.dumps(
            {
                "frame_id": "map",
                "resolution_m": 0.05,
                "width": 2,
                "height": 2,
                "origin": [0.0, 0.0, 0.0],
                "occupancy": [0, 0, 100, -1],
            }
        ),
        encoding="utf-8",
    )
    engine_path = tmp_path / "yolo26s-pose.engine"
    engine_path.write_bytes(b"engine-preflight")
    pose_manifest_path = tmp_path / "pose-manifest.json"
    pose_manifest_path.write_text(
        json.dumps(
            {
                "schema": POSE_ENGINE_SCHEMA,
                "model": "yolo26s-pose",
                "task": "pose",
                "trained": False,
                "engineSha256": sha256_file(engine_path),
                "buildPlatform": {"machine": "aarch64"},
                "export": {"imageSize": 640},
                "personClassId": 0,
                "keypointCount": 17,
                "smokeInferencePassed": True,
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "run"
    report = _capture_preflight(
        argparse.Namespace(
            config=config_path,
            calibration=calibration_path,
            map_path=map_path,
            pose_engine=engine_path,
            pose_manifest=pose_manifest_path,
            lstm_checkpoint=None,
            output=output,
            frames_root=None,
            duration_s=1.0,
            sample_period_s=0.1,
            controller="external",
            command_csv=None,
            confirm_motion=False,
        )
    )
    assert report["status"] == "PASS"
    assert report["devices_opened"] is False
    assert report["motion_requested"] is False
    assert report["robot"]["footprint_radius_m"] == pytest.approx(0.16)
    assert not output.exists()
