import csv
import json

import pytest

from tools.analyze_run import analyze, summarize_controller_events
from tools.final_pack import package, sha256_file


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def make_input(root, control_fields=("t_ns", "vx_cmd_mps", "vy_cmd_mps", "wz_cmd_radps")):
    write_csv(root / "robot_state.csv", ["t_ns", "x_m", "y_m", "yaw_rad", "vx_mps", "vy_mps", "wz_radps"], [{"t_ns": 1, "x_m": 0, "y_m": 0, "yaw_rad": 0, "vx_mps": 0, "vy_mps": 0, "wz_radps": 0}])
    write_csv(root / "control.csv", list(control_fields), [{field: 0 for field in control_fields} | {"t_ns": 1}])
    write_csv(root / "context.csv", ["t_ns", "position_x_m", "position_y_m", "speed_mps", "direction", "confidence", "context_valid"], [{"t_ns": 1, "position_x_m": 1, "position_y_m": 1, "speed_mps": 0.2, "direction": "forward", "confidence": 0.8, "context_valid": "true"}])
    write_csv(root / "lidar.csv", ["t_ns", "point_count", "points_json"], [{"t_ns": 1, "point_count": 1, "points_json": "[[0.0,1.0,10,0]]"}])
    write_csv(root / "events.csv", ["t_ns", "event_type", "solve_ms"], [{"t_ns": 1, "event_type": "stop", "solve_ms": 1.0}])
    (root / "map.json").write_text(json.dumps({"frame_id": "map", "resolution_m": 0.05, "width": 2, "height": 2, "origin": [0, 0, 0], "occupancy": [0, 0, 100, -1]}), encoding="utf-8")


def make_calibration(root, camera="Astra S", lidar="N10P"):
    (root / "calibration.json").write_text(
        json.dumps(
            {
                "schema": "cca-capture-calibration-v1",
                "calibration_id": "cal-test-01",
                "camera": camera,
                "lidar": lidar,
                "robot_frame": "base_link",
                "calibrated_at_utc": "2026-08-13T00:00:00Z",
                "camera_intrinsics": {
                    "fx": 500.0,
                    "fy": 500.0,
                    "cx": 320.0,
                    "cy": 240.0,
                    "width": 640,
                    "height": 480,
                },
                "camera_to_robot": {"translation_m": [0.1, 0.0, 0.2], "rpy_rad": [0.0, 0.0, 0.0]},
                "lidar_to_robot": {"translation_m": [0.0, 0.0, 0.3], "rpy_rad": [0.0, 0.0, 0.0]},
                "quality": {"camera_reprojection_rmse_px": 0.5, "lidar_alignment_rmse_m": 0.01},
            }
        ),
        encoding="utf-8",
    )


def test_final_package_seals_required_data(tmp_path):
    source = tmp_path / "input"
    output = tmp_path / "sealed"
    source.mkdir()
    make_input(source)
    package(source, output, "final-run-1", "mecanum", "cca_nmpc", "robot_time")
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "verified"
    assert manifest["integrity_status"] == "verified"
    assert manifest["capture_source"] == "unknown"
    assert manifest["control_interface"] == "unknown"
    assert manifest["evidence_status"] == "source-unverified"
    assert manifest["sensors"] == {"camera": "not-declared", "lidar": "not-declared"}
    assert manifest["firmware"] == "not-declared"
    assert manifest["map_sha256"] == manifest["files"]["map.json"]["sha256"]
    assert manifest["files"]["lidar.csv"]["rows"] == 1
    assert (output / "checksums.sha256").is_file()


def test_final_package_records_declared_hardware_identity(tmp_path):
    source = tmp_path / "input"
    output = tmp_path / "sealed"
    source.mkdir()
    make_input(source)
    make_calibration(source)
    package(
        source,
        output,
        "final-run-hardware",
        "mecanum",
        "cca_nmpc",
        "robot_time",
        "hardware",
        "Astra S",
        "N10P",
        "fw-1.2.3",
    )
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["capture_source"] == "hardware"
    assert manifest["sensors"] == {"camera": "Astra S", "lidar": "N10P"}
    assert manifest["firmware"] == "fw-1.2.3"
    assert manifest["calibration"]["path"] == "calibration.json"
    assert manifest["calibration"]["calibration_id"] == "cal-test-01"


def test_final_package_rejects_real_capture_without_calibration(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    make_input(source)
    with pytest.raises(ValueError, match="calibration.json is required"):
        package(
            source,
            tmp_path / "sealed",
            "final-run-hardware-no-calibration",
            "mecanum",
            "cca_nmpc",
            "robot_time",
            "hardware",
            "Astra S",
            "N10P",
            "fw-1.2.3",
        )


def test_final_package_rejects_real_capture_without_lidar_scan(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    make_input(source)
    (source / "lidar.csv").unlink()
    make_calibration(source)
    with pytest.raises(ValueError, match="lidar.csv is required"):
        package(
            source,
            tmp_path / "sealed",
            "final-run-hardware-no-lidar",
            "mecanum",
            "cca_nmpc",
            "robot_time",
            "hardware",
            "Astra S",
            "N10P",
            "fw-1.2.3",
        )


def test_final_package_rejects_malformed_lidar_points(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    make_input(source)
    (source / "lidar.csv").write_text(
        't_ns,point_count,points_json\n1,1,"[[0.0,-1.0,10,0]]"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="invalid values"):
        package(source, tmp_path / "sealed", "final-run-bad-lidar", "mecanum", "cca_nmpc", "robot_time")


def test_final_package_rejects_sensor_mismatched_calibration(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    make_input(source)
    make_calibration(source, camera="other-camera")
    with pytest.raises(ValueError, match="calibration camera does not match"):
        package(
            source,
            tmp_path / "sealed",
            "final-run-calibration-mismatch",
            "mecanum",
            "cca_nmpc",
            "robot_time",
            "hardware",
            "Astra S",
            "N10P",
            "fw-1.2.3",
        )


def test_final_package_records_body_velocity_interface(tmp_path):
    source = tmp_path / "input"
    output = tmp_path / "sealed"
    source.mkdir()
    make_input(source)
    package(
        source,
        output,
        "final-run-body-velocity",
        "mecanum",
        "cca_nmpc",
        "robot_time",
        control_interface="body_velocity",
    )
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["control_interface"] == "body_velocity"
    assert manifest["control_mode"] == "position_state"
    assert manifest["state_definition"] == ["x_m", "y_m", "theta_rad", "vx_mps", "vy_mps", "omega_radps"]


def test_final_package_rejects_torque_interface_without_torque_columns(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    make_input(source)
    with pytest.raises(ValueError, match="control interface wheel_torque requires columns"):
        package(
            source,
            tmp_path / "sealed",
            "final-run-torque",
            "mecanum",
            "cca_nmpc",
            "robot_time",
            control_interface="wheel_torque",
        )


def test_final_package_rejects_torque_interface_for_physical_capture(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    make_input(source)
    with pytest.raises(ValueError, match="physical position_state packages require the body_velocity interface"):
        package(
            source,
            tmp_path / "sealed",
            "final-run-physical-torque",
            "mecanum",
            "cca_nmpc",
            "robot_time",
            capture_source="hardware",
            control_interface="wheel_torque",
        )


def test_final_package_rejects_control_without_signal(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    make_input(source, ("t_ns",))
    with pytest.raises(ValueError, match="control signal group"):
        package(source, tmp_path / "sealed", "final-run-1", "mecanum", "cca_nmpc", "robot_time")


def test_final_package_rejects_duplicate_timestamps(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    make_input(source)
    write_csv(
        source / "context.csv",
        ["t_ns", "position_x_m", "position_y_m", "speed_mps", "direction", "confidence", "context_valid"],
        [
            {"t_ns": 1, "position_x_m": 1, "position_y_m": 1, "speed_mps": 0.2, "direction": "forward", "confidence": 0.8, "context_valid": "true"},
            {"t_ns": 1, "position_x_m": 1, "position_y_m": 1, "speed_mps": 0.2, "direction": "forward", "confidence": 0.8, "context_valid": "true"},
        ],
    )
    with pytest.raises(ValueError, match="t_ns must be strictly increasing"):
        package(source, tmp_path / "sealed", "final-run-duplicate-time", "mecanum", "cca_nmpc", "robot_time")


def test_final_package_validates_optional_camera_device_timestamp(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    make_input(source)
    write_csv(
        source / "context.csv",
        [
            "t_ns",
            "position_x_m",
            "position_y_m",
            "speed_mps",
            "direction",
            "confidence",
            "context_valid",
            "camera_device_t_ns",
        ],
        [{
            "t_ns": 1,
            "position_x_m": 1,
            "position_y_m": 1,
            "speed_mps": 0.2,
            "direction": "forward",
            "confidence": 0.8,
            "context_valid": "true",
            "camera_device_t_ns": "not-a-timestamp",
        }],
    )
    with pytest.raises(ValueError, match="camera_device_t_ns"):
        package(source, tmp_path / "sealed", "final-run-bad-camera-time", "mecanum", "cca_nmpc", "robot_time")


def test_final_package_rejects_human_trajectory_context_field(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    make_input(source)
    write_csv(
        source / "context.csv",
        [
            "t_ns",
            "position_x_m",
            "position_y_m",
            "speed_mps",
            "direction",
            "confidence",
            "context_valid",
            "future_position_x_m",
        ],
        [{
            "t_ns": 1,
            "position_x_m": 1,
            "position_y_m": 1,
            "speed_mps": 0.2,
            "direction": "forward",
            "confidence": 0.8,
            "context_valid": "true",
            "future_position_x_m": 2,
        }],
    )
    with pytest.raises(ValueError, match="trajectory fields are forbidden"):
        package(source, tmp_path / "sealed", "final-run-1", "mecanum", "cca_nmpc", "robot_time")


def test_final_package_analysis_is_external_and_provenance_linked(tmp_path):
    source = tmp_path / "input"
    sealed = tmp_path / "sealed"
    analysis_output = tmp_path / "analysis"
    source.mkdir()
    make_input(source)
    package(source, sealed, "final-run-1", "mecanum", "cca_nmpc", "robot_time")
    analyze(sealed, analysis_output)
    analysis = json.loads((analysis_output / "analysis.json").read_text(encoding="utf-8"))
    assert analysis["status"] == "candidate-analysis"
    assert analysis["source"]["run_id"] == "final-run-1"
    assert analysis["source"]["capture_source"] == "unknown"
    assert analysis["source"]["control_interface"] == "unknown"
    assert analysis["source"]["evidence_status"] == "source-unverified"
    assert analysis["context"]["confusion_matrix"] == "not_available_without_independent_direction_labels"
    assert analysis["lidar"] == {
        "scan_count": 1,
        "total_point_count": 1,
        "scan_timestamps_strictly_increasing": True,
    }
    assert (analysis_output / "checksums.sha256").is_file()
    with pytest.raises(ValueError, match="separate"):
        analyze(sealed, sealed)


def test_controller_event_summary_preserves_cca_replan_and_parse_failures() -> None:
    summary, failures = summarize_controller_events(
        [
            {
                "event_type": "cca_nmpc_step",
                "detail": json.dumps(
                    {
                        "status": "CCA_POSITION_SUCCESS",
                        "local_replanned": True,
                        "local_generation_count": 1,
                        "deadline_missed": False,
                        "solve_ms": 4.5,
                        "risk_bound": 0.05,
                        "constraint_violation": 0.0,
                    }
                ),
            },
            {"event_type": "cca_nmpc_step", "detail": "not-json"},
            {"event_type": "capture_started", "detail": "{}"},
        ]
    )
    assert failures == 1
    assert summary["cca_nmpc_step_count"] == 2
    assert summary["local_replan_count"] == 1
    assert summary["deadline_miss_count"] == 0
    assert summary["future_human_path_exported"] is False
    assert summary["status_counts"] == {"CCA_POSITION_SUCCESS": 1}
    assert summary["solve_ms"]["p95"] == pytest.approx(4.5)


def test_final_package_analysis_accepts_hash_bound_calibration(tmp_path):
    source = tmp_path / "input"
    sealed = tmp_path / "sealed"
    analysis_output = tmp_path / "analysis"
    source.mkdir()
    make_input(source)
    make_calibration(source)
    package(
        source,
        sealed,
        "final-run-calibration",
        "mecanum",
        "cca_nmpc",
        "robot_time",
        "hardware",
        "Astra S",
        "N10P",
        "fw-1.2.3",
    )
    analyze(sealed, analysis_output)
    report = json.loads((analysis_output / "analysis.json").read_text(encoding="utf-8"))
    assert report["source"]["capture_source"] == "hardware"


def refresh_manifest_checksum(root):
    lines = []
    for line in (root / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        digest, name = line.split(maxsplit=1)
        if name == "manifest.json":
            digest = sha256_file(root / name)
        lines.append(f"{digest}  {name}")
    (root / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_analysis_rejects_duplicate_checksum_records(tmp_path):
    source = tmp_path / "input"
    sealed = tmp_path / "sealed"
    source.mkdir()
    make_input(source)
    package(source, sealed, "final-run-duplicate", "mecanum", "cca_nmpc", "robot_time")
    checksum = (sealed / "checksums.sha256").read_text(encoding="utf-8")
    first = checksum.splitlines()[0]
    (sealed / "checksums.sha256").write_text(checksum + first + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate record"):
        analyze(sealed, tmp_path / "analysis")


def test_analysis_rejects_manifest_payload_omission(tmp_path):
    source = tmp_path / "input"
    sealed = tmp_path / "sealed"
    source.mkdir()
    make_input(source)
    package(source, sealed, "final-run-manifest", "mecanum", "cca_nmpc", "robot_time")
    manifest_path = sealed / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"].pop("map.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    refresh_manifest_checksum(sealed)
    with pytest.raises(ValueError, match="manifest.files"):
        analyze(sealed, tmp_path / "analysis")


def test_analysis_rejects_missing_sensor_identity(tmp_path):
    source = tmp_path / "input"
    sealed = tmp_path / "sealed"
    source.mkdir()
    make_input(source)
    package(source, sealed, "final-run-sensor", "mecanum", "cca_nmpc", "robot_time")
    manifest_path = sealed / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sensors"].pop("lidar")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    refresh_manifest_checksum(sealed)
    with pytest.raises(ValueError, match="camera, lidar and firmware"):
        analyze(sealed, tmp_path / "analysis")


def test_analysis_rejects_missing_control_interface(tmp_path):
    source = tmp_path / "input"
    sealed = tmp_path / "sealed"
    source.mkdir()
    make_input(source)
    package(source, sealed, "final-run-interface", "mecanum", "cca_nmpc", "robot_time")
    manifest_path = sealed / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("control_interface")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    refresh_manifest_checksum(sealed)
    with pytest.raises(ValueError, match="manifest.control_interface is unsupported"):
        analyze(sealed, tmp_path / "analysis")
