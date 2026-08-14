import json
import csv

import numpy as np
import pytest

from tools.ctx_run import (
    OBSERVED_STEPS,
    SPLIT_SCHEMA,
    build_split_windows,
    contiguous_context_windows,
    load_split_manifest,
    load_confirmatory_capture_manifest,
    make_history,
    read_context,
    sha256_file,
    validate_context_group_metadata,
    validate_confirmatory_split_support,
)


def test_bounded_missingness_is_explicit_and_does_not_create_a_path() -> None:
    frames = list(range(OBSERVED_STEPS + 2))
    selected = {
        frame: (np.asarray((float(frame), 2.0)) if frame not in {3, 11} else None)
        for frame in frames
    }
    windows = contiguous_context_windows(selected, frames, minimum_valid_fraction=0.80)
    assert windows
    _, positions, valid = windows[0]
    assert positions.shape == (OBSERVED_STEPS, 2)
    assert valid.shape == (OBSERVED_STEPS,)
    assert int(np.sum(valid < 0.5)) >= 1
    history = make_history(positions, valid)
    np.testing.assert_array_equal(history[:, -1], valid)
    assert not any("path" in key.lower() for key in ("position_proxy", "history_valid_fraction"))


def test_missing_current_reference_is_not_emitted() -> None:
    frames = list(range(OBSERVED_STEPS))
    selected = {frame: np.asarray((float(frame), 2.0)) for frame in frames}
    selected[frames[-1]] = None
    assert contiguous_context_windows(selected, frames) == []


def test_frozen_group_split_keeps_recordings_disjoint(tmp_path) -> None:
    manifest_path = tmp_path / "split.json"
    assignments = [
        {"group_id": f"recording-{index}", "split": split}
        for index, split in enumerate(("train", "validation", "calibration", "test_id", "test_ood"))
    ]
    manifest_path.write_text(
        json.dumps(
            {
                "schema": SPLIT_SCHEMA,
                "group_key": "recording_id",
                "purposes": ["train", "validation", "calibration", "test_id", "test_ood"],
                "frozen_before_training": True,
                "group_intersections_empty": True,
                "assignments": assignments,
            }
        ),
        encoding="utf-8",
    )
    rows = []
    for group_index in range(5):
        for frame in range(100):
            rows.append(
                {
                    "t_ns": frame * 100_000_000,
                    "position": np.asarray((float(frame) * 0.01, 0.0)),
                    "speed_mps": 0.1,
                    "direction": "right",
                    "confidence": 1.0,
                    "valid": True,
                    "groups": {"recording_id": f"recording-{group_index}"},
                    "declared_split": "",
                }
            )
    split_manifest = load_split_manifest(manifest_path)
    split_windows, audit = build_split_windows(rows, split_manifest)
    assert set(split_windows) == {"train", "validation", "calibration", "test_id", "test_ood"}
    assert all(len(history) > 0 for history, _ in split_windows.values())
    assert set(item["split"] for item in audit["groups"].values()) == set(split_windows)


def test_frozen_group_split_rejects_declared_split_mismatch(tmp_path) -> None:
    manifest_path = tmp_path / "split.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema": SPLIT_SCHEMA,
                "group_key": "recording_id",
                "purposes": ["train", "validation", "calibration", "test_id", "test_ood"],
                "frozen_before_training": True,
                "group_intersections_empty": True,
                "assignments": [
                    {"group_id": "recording-1", "split": "train"},
                    {"group_id": "recording-2", "split": "validation"},
                    {"group_id": "recording-3", "split": "calibration"},
                    {"group_id": "recording-4", "split": "test_id"},
                    {"group_id": "recording-5", "split": "test_ood"},
                ],
            }
        ),
        encoding="utf-8",
    )
    rows = [
        {
            "t_ns": 0,
            "position": np.zeros(2),
            "speed_mps": 0.0,
            "direction": "unknown",
            "confidence": 0.0,
            "valid": False,
            "groups": {"recording_id": "recording-1"},
            "declared_split": "test_ood",
        }
    ]
    with pytest.raises(ValueError, match="declared split disagrees"):
        build_split_windows(rows, load_split_manifest(manifest_path))


def test_frozen_group_split_rejects_unknown_manifest_field(tmp_path) -> None:
    manifest_path = tmp_path / "split.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema": SPLIT_SCHEMA,
                "group_key": "recording_id",
                "purposes": ["train", "validation", "calibration", "test_id", "test_ood"],
                "frozen_before_training": True,
                "group_intersections_empty": True,
                "assignments": [
                    {"group_id": "recording-1", "split": "train"},
                    {"group_id": "recording-2", "split": "validation"},
                    {"group_id": "recording-3", "split": "calibration"},
                    {"group_id": "recording-4", "split": "test_id"},
                    {"group_id": "recording-5", "split": "test_ood"},
                ],
                "unexpected": True,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="invalid context split manifest"):
        load_split_manifest(manifest_path)


def test_confirmatory_context_requires_all_leakage_group_keys() -> None:
    rows = [{"groups": {"recording_id": "recording-1"}}]
    with pytest.raises(ValueError, match="leakage-group metadata: episode_id, source_id, scene_id"):
        validate_context_group_metadata(rows)


def test_context_csv_rejects_unknown_direction_class(tmp_path) -> None:
    path = tmp_path / "context.csv"
    path.write_text(
        "t_ns,position_x_m,position_y_m,speed_mps,direction,confidence,context_valid\n"
        "0,0.0,0.0,0.0,diagonal,0.0,false\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unsupported direction"):
        read_context(path)


def test_confirmatory_split_requires_calibration_and_id_ood_support() -> None:
    small = (np.zeros((29, 20, 5), dtype=np.float32), np.zeros((29, 2), dtype=np.float32))
    enough = (np.zeros((30, 20, 5), dtype=np.float32), np.zeros((30, 2), dtype=np.float32))
    with pytest.raises(ValueError, match="at least 30 windows"):
        validate_confirmatory_split_support(
            {"calibration": enough, "test_id": small, "test_ood": enough}
        )
    validate_confirmatory_split_support(
        {"calibration": enough, "test_id": enough, "test_ood": enough}
    )


def test_context_csv_rejects_future_position_field(tmp_path) -> None:
    path = tmp_path / "context.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "t_ns",
                "position_x_m",
                "position_y_m",
                "speed_mps",
                "direction",
                "confidence",
                "context_valid",
                "future_position_x_m",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "t_ns": 0,
                "position_x_m": 0.0,
                "position_y_m": 0.0,
                "speed_mps": 0.0,
                "direction": "unknown",
                "confidence": 0.0,
                "context_valid": "false",
                "future_position_x_m": 1.0,
            }
        )
    with pytest.raises(ValueError, match="trajectory fields are forbidden"):
        read_context(path)


def test_context_csv_rejects_duplicate_timestamps(tmp_path) -> None:
    path = tmp_path / "context.csv"
    path.write_text(
        "t_ns,position_x_m,position_y_m,speed_mps,direction,confidence,context_valid\n"
        "0,0.0,0.0,0.0,unknown,0.0,false\n"
        "0,0.1,0.0,0.1,right,0.5,true\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="strictly increasing"):
        read_context(path)


def test_confirmatory_context_requires_sealed_real_capture_manifest(tmp_path) -> None:
    context_path = tmp_path / "context.csv"
    context_path.write_text(
        "t_ns,position_x_m,position_y_m,speed_mps,direction,confidence,context_valid\n"
        "0,0.0,0.0,0.0,unknown,0.0,false\n",
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.json"
    calibration_path = tmp_path / "calibration.json"
    calibration_path.write_text(
        json.dumps(
            {
                "schema": "cca-capture-calibration-v1",
                "calibration_id": "cal-test-01",
                "camera": "Astra S",
                "lidar": "N10P",
                "robot_frame": "base_link",
                "calibrated_at_utc": "2026-08-13T00:00:00Z",
                "camera_intrinsics": {"fx": 500.0, "fy": 500.0, "cx": 320.0, "cy": 240.0, "width": 640, "height": 480},
                "camera_to_robot": {"translation_m": [0.1, 0.0, 0.2], "rpy_rad": [0.0, 0.0, 0.0]},
                "lidar_to_robot": {"translation_m": [0.0, 0.0, 0.3], "rpy_rad": [0.0, 0.0, 0.0]},
                "quality": {"camera_reprojection_rmse_px": 0.5, "lidar_alignment_rmse_m": 0.01},
            }
        ),
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(
            {
                "status": "verified",
                "integrity_status": "verified",
                "capture_source": "hardware",
                "context_only": True,
                "human_trajectory_generated": False,
                "sensors": {"camera": "Astra S", "lidar": "N10P"},
                "calibration": {"path": "calibration.json", "sha256": sha256_file(calibration_path), "calibration_id": "cal-test-01"},
                "files": {
                    "context.csv": {"sha256": sha256_file(context_path)},
                    "calibration.json": {"sha256": sha256_file(calibration_path)},
                },
            }
        ),
        encoding="utf-8",
    )
    metadata = load_confirmatory_capture_manifest(tmp_path, context_path)
    assert metadata["capture_source"] == "hardware"
    assert metadata["context_sha256"] == sha256_file(context_path)
    assert metadata["calibration_sha256"] == sha256_file(calibration_path)


def test_confirmatory_context_rejects_simulation_source(tmp_path) -> None:
    context_path = tmp_path / "context.csv"
    context_path.write_text("context\n", encoding="utf-8")
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "status": "verified",
                "integrity_status": "verified",
                "capture_source": "simulation",
                "context_only": True,
                "human_trajectory_generated": False,
                "files": {"context.csv": {"sha256": sha256_file(context_path)}},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="declared real capture source"):
        load_confirmatory_capture_manifest(tmp_path, context_path)


def test_simulation_context_requires_explicit_simulation_only_admission(tmp_path) -> None:
    context_path = tmp_path / "context.csv"
    context_path.write_text("context\n", encoding="utf-8")
    calibration_path = tmp_path / "calibration.json"
    calibration_path.write_text(
        json.dumps(
            {
                "schema": "cca-capture-calibration-v1",
                "calibration_id": "cal-simulation-01",
                "camera": "simulation-camera",
                "lidar": "simulation-lidar",
                "robot_frame": "base_link",
                "calibrated_at_utc": "2026-08-14T00:00:00Z",
                "camera_intrinsics": {"fx": 500.0, "fy": 500.0, "cx": 320.0, "cy": 240.0, "width": 640, "height": 480},
                "camera_to_robot": {"translation_m": [0.0, 0.0, 0.0], "rpy_rad": [0.0, 0.0, 0.0]},
                "lidar_to_robot": {"translation_m": [0.0, 0.0, 0.0], "rpy_rad": [0.0, 0.0, 0.0]},
                "quality": {"camera_reprojection_rmse_px": 0.0, "lidar_alignment_rmse_m": 0.0},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "status": "verified",
                "integrity_status": "verified",
                "capture_source": "simulation",
                "simulation_only": True,
                "context_only": True,
                "human_trajectory_generated": False,
                "sensors": {"camera": "simulation-camera", "lidar": "simulation-lidar"},
                "calibration": {"path": "calibration.json", "sha256": sha256_file(calibration_path)},
                "files": {
                    "context.csv": {"sha256": sha256_file(context_path)},
                    "calibration.json": {"sha256": sha256_file(calibration_path)},
                },
            }
        ),
        encoding="utf-8",
    )
    metadata = load_confirmatory_capture_manifest(tmp_path, context_path, allow_simulation=True)
    assert metadata["capture_source"] == "simulation"
    assert metadata["calibration_sha256"] == sha256_file(calibration_path)
