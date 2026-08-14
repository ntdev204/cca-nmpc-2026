import json
from pathlib import Path

import numpy as np
import pytest

from tools.validate_hardware_entry import ROOT, run_preflight
from tools.record_hardware import (
    OnlineCcaNmpc,
    command_at,
    load_command_schedule,
    load_controller_map,
    runtime_robot_geometry,
    select_stm_command,
    validate_safety_record,
    validate_robot_source,
    validate_config,
)
from hardware import PoseContextRecord


def test_stm_stop_flag_is_seen_before_command_selection() -> None:
    class Source:
        latest = type("Telemetry", (), {"flag_stop": 1})()

    command, latched = select_stm_command(Source(), (0.2, 0.0, 0.0), False)
    assert command == (0.0, 0.0, 0.0)
    assert latched is True


def test_motion_safety_record_requires_all_stop_checks(tmp_path: Path) -> None:
    path = tmp_path / "safety.json"
    path.write_text(
        json.dumps(
            {
                "approved": True,
                "emergency_stop_verified": True,
                "remote_disable_verified": True,
                "watchdog_verified": True,
            }
        ),
        encoding="utf-8",
    )
    assert validate_safety_record(path)["approved"] is True
    path.write_text(json.dumps({"approved": True}), encoding="utf-8")
    with pytest.raises(ValueError, match="safety record"):
        validate_safety_record(path)


def test_pr30_hardware_entry_static_contract_passes_and_admission_stays_blocked() -> None:
    report = run_preflight(ROOT)
    assert report["status"] == "PASS"
    assert report["admission_status"] == "BLOCKED"
    assert report["hardware_packages"] == []
    assert report["checks"]["no_ros_runtime_dependency"] is True
    assert report["checks"]["commissioning_lock_zero"] is True
    assert report["checks"]["direct_csv_json_mapping"] is True
    assert report["checks"]["runtime_urdf_geometry_metadata_present"] is True
    assert report["checks"]["physical_spec_recorded"] is True
    assert any("independent dimensional verification" in reason for reason in report["admission_reasons"])
    assert not any("physical specifications ... are absent" in reason for reason in report["admission_reasons"])


def test_runtime_capture_metadata_binds_urdf_geometry() -> None:
    payload = {
        "urdf_source": "mini_mec_robot",
        "urdf_path": None,
        "source": {"urdf_sha256": "a" * 64, "xacro_sha256": "b" * 64},
        "wheel_radius_m": 0.0363,
        "half_length_m": 0.08595,
        "half_width_m": 0.099012,
        "footprint": {"footprint_radius_m": 0.1772541986},
    }
    metadata = runtime_robot_geometry(payload)
    assert metadata["model"] == "mini_mec_robot"
    assert metadata["urdf_sha256"] == "a" * 64
    assert metadata["xacro_sha256"] == "b" * 64
    assert metadata["wheel_radius_m"] == pytest.approx(0.0363)
    assert metadata["footprint"]["footprint_radius_m"] == pytest.approx(0.1772541986)


def test_runtime_config_hashes_bind_loaded_urdf_and_xacro() -> None:
    intake = json.loads(
        (ROOT / "research/metadata/hardware/mini_mec_intake_20260814.json").read_text(encoding="utf-8")
    )["robot"]
    config = {
        "urdf_source": "mini_mec_robot",
        "source": {
            "urdf_sha256": intake["urdf_sha256"],
            "xacro_sha256": intake["xacro_sha256"],
        },
    }
    hashes = validate_robot_source(config, ROOT / "configs/runtime.json")
    assert hashes["urdf_sha256"] == intake["urdf_sha256"]
    assert hashes["xacro_sha256"] == intake["xacro_sha256"]


def test_runtime_config_rejects_stale_urdf_hash() -> None:
    config = {
        "urdf_source": "mini_mec_robot",
        "source": {"urdf_sha256": "0" * 64, "xacro_sha256": "1" * 64},
    }
    with pytest.raises(ValueError, match="URDF hash"):
        validate_robot_source(config, ROOT / "configs/runtime.json")


def test_direct_config_requires_explicit_n10p_profile() -> None:
    config = {
        "schema": "cca-hardware-runtime-v1",
        "camera": {"model": "Astra-S", "sdk": "OpenNI2", "depth_scale_m": 0.001},
        "lidar": {"model": "N10P", "port": "COM1", "baudrate": 460800},
        "can": {"channel": "can0", "interface": "socketcan", "bitrate": 500000},
        "firmware": "fw-test",
        "clock": "system_time",
    }
    try:
        validate_config(config)
    except ValueError as error:
        assert "protocol_profile" in str(error)
    else:
        raise AssertionError("N10P profile must be declared before capture")


def test_direct_config_rejects_unmeasured_lidar_baudrate() -> None:
    config = {
        "schema": "cca-hardware-runtime-v1",
        "camera": {"model": "Astra-S", "sdk": "OpenNI2", "depth_scale_m": 0.001},
        "lidar": {
            "model": "N10P",
            "port": "COM1",
            "baudrate": None,
            "protocol_profile": "n10p-108b-v1",
        },
        "can": {"channel": "can0", "interface": "socketcan", "bitrate": 500000},
        "firmware": "fw-test",
        "clock": "system_time",
    }
    with pytest.raises(ValueError, match="baudrate"):
        validate_config(config)


def test_direct_stm32_transport_does_not_require_can_channel() -> None:
    config = {
        "schema": "cca-hardware-runtime-v1",
        "transport": "stm32_serial",
        "stm32": {"port": "/dev/rai_controller", "baudrate": 115200},
        "camera": {"model": "Astra-S", "sdk": "OpenNI2", "depth_scale_m": 0.001},
        "lidar": {
            "model": "N10P",
            "port": "/dev/rai_lidar",
            "baudrate": 460800,
            "protocol_profile": "n10p-108b-v1",
        },
        "firmware": "fw-test",
        "clock": "system_time",
    }
    validate_config(config)


def test_direct_runtime_uses_position_state_scope() -> None:
    config = {
        "schema": "cca-hardware-runtime-v1",
        "transport": "stm32_serial",
        "control_mode": "position_state",
        "state_definition": ["x_m", "y_m", "theta_rad", "vx_mps", "vy_mps", "omega_radps"],
        "stm32": {"port": "/dev/rai_controller", "baudrate": 115200},
        "camera": {"model": "Astra-S", "sdk": "OpenNI2", "depth_scale_m": 0.001},
        "lidar": {
            "model": "N10P",
            "port": "/dev/rai_lidar",
            "baudrate": 460800,
            "protocol_profile": "n10p-108b-v1",
        },
        "firmware": "fw-test",
        "clock": "system_time",
    }
    validate_config(config)


def test_direct_runtime_rejects_non_position_control_scope() -> None:
    config = {
        "schema": "cca-hardware-runtime-v1",
        "control_mode": "wheel_torque",
        "camera": {"model": "Astra-S", "sdk": "OpenNI2", "depth_scale_m": 0.001},
        "lidar": {
            "model": "N10P",
            "port": "/dev/rai_lidar",
            "baudrate": 460800,
            "protocol_profile": "n10p-108b-v1",
        },
        "can": {"channel": "can0", "interface": "socketcan", "bitrate": 500000},
        "firmware": "fw-test",
        "clock": "system_time",
    }
    with pytest.raises(ValueError, match="control_mode"):
        validate_config(config)


def test_command_schedule_requires_actuation_and_selects_latest_point(tmp_path) -> None:
    path = tmp_path / "commands.csv"
    path.write_text(
        "t_s,vx_mps,vy_mps,wz_radps\n0,0.1,0,0\n0.2,0,0.1,0\n0.3,0,0,0\n",
        encoding="utf-8",
    )
    schedule = load_command_schedule(path)
    assert command_at(schedule, 0.1) == (0.1, 0.0, 0.0)
    assert command_at(schedule, 0.2) == (0.0, 0.1, 0.0)
    assert command_at(schedule, 0.4) == (0.0, 0.0, 0.0)


def test_controller_map_requires_explicit_cca_settings(tmp_path: Path) -> None:
    path = tmp_path / "map.json"
    path.write_text(json.dumps({"global_path_xy": [[0.0, 0.0], [2.0, 0.0]]}), encoding="utf-8")
    with pytest.raises(ValueError, match="cca_nmpc settings"):
        load_controller_map(path)


def test_online_cca_keeps_prediction_internal_and_returns_body_velocity() -> None:
    controller = OnlineCcaNmpc(
        np.asarray(((0.0, 0.0), (2.0, 0.0)), dtype=np.float64),
        {
            "horizon": 6,
            "cruise_speed_mps": 0.3,
            "human_std_m": 0.04,
            "safe_distance_m": 0.2,
            "lateral_offset_m": 1.0,
            "longitudinal_offset_m": 0.8,
        },
        0.1,
    )
    record = PoseContextRecord(
        t_ns=1_000_000_000,
        position_x_m=0.8,
        position_y_m=0.0,
        speed_mps=0.2,
        direction="right",
        confidence=0.9,
        context_valid=True,
        frame_path="frames/frame.jpg",
        lstm_active=True,
        lstm_configured=True,
    )
    command, details = controller.step(np.zeros(6, dtype=np.float64), record)
    assert len(command) == 3
    assert all(np.isfinite(command))
    assert details["status"] == "CCA_NMPC_SUCCESS"
    assert "predicted_states" not in details
    assert controller.path.global_path_xy.tolist() == [[0.0, 0.0], [2.0, 0.0]]
    assert controller.human_clearance_m == pytest.approx(0.1772541986 + 0.60)


def test_online_cca_rejects_clearance_from_the_superseded_robot_radius() -> None:
    with pytest.raises(ValueError, match="URDF robot radius"):
        OnlineCcaNmpc(
            np.asarray(((0.0, 0.0), (2.0, 0.0)), dtype=np.float64),
            {
                "horizon": 6,
                "cruise_speed_mps": 0.3,
                "human_std_m": 0.04,
                "safe_distance_m": 0.2,
                "lateral_offset_m": 1.0,
                "longitudinal_offset_m": 0.8,
                "human_clearance_m": 0.92,
            },
            0.1,
        )


def test_online_cca_replans_only_local_path_after_direction_change() -> None:
    controller = OnlineCcaNmpc(
        np.asarray(((0.0, 5.0), (10.0, 5.0)), dtype=np.float64),
        {
            "horizon": 6,
            "cruise_speed_mps": 0.3,
            "human_std_m": 0.04,
            "safe_distance_m": 0.2,
            "lateral_offset_m": 1.0,
            "longitudinal_offset_m": 0.8,
        },
        0.1,
    )
    first = PoseContextRecord(
        t_ns=1_000_000_000,
        position_x_m=5.0,
        position_y_m=0.0,
        speed_mps=0.2,
        direction="forward",
        confidence=0.9,
        context_valid=True,
        frame_path="frames/first.jpg",
        lstm_active=True,
        lstm_configured=True,
    )
    second = PoseContextRecord(
        t_ns=1_100_000_000,
        position_x_m=5.0,
        position_y_m=0.0,
        speed_mps=0.2,
        direction="backward",
        confidence=0.9,
        context_valid=True,
        frame_path="frames/second.jpg",
        lstm_active=True,
        lstm_configured=True,
    )
    state = np.zeros(6, dtype=np.float64)
    controller.step(state, first)
    first_generation = controller.path.local_generation_count
    global_path = controller.path.global_path_xy.copy()
    command, details = controller.step(state, second)
    assert all(np.isfinite(command))
    assert details["local_generation_count"] == first_generation + 1
    assert details["local_replanned"]
    assert "direction_change" in details["replan_reasons"]
    np.testing.assert_array_equal(controller.path.global_path_xy, global_path)
