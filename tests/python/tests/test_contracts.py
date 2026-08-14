import json
from pathlib import Path

import numpy as np
import pytest

from ai.contracts import ContextEvent, HumanObservation, TrackState
from ai.ctx_lstm import ContextDirectionLstm
from tools.ctx_run import (
    constant_velocity_predictions,
    direction_probabilities,
    evaluate_predictions,
    evaluate_baselines,
    fit_temperature,
    kalman_velocity_predictions,
    select_training_seed,
)
from tools.det_eval import (
    ANNOTATION_SCHEMA,
    CONTEXT_SCHEMA,
    PRESENCE_SCHEMA,
    aggregate_bbox_metrics,
    aggregate_presence_metrics,
    bootstrap_bbox_intervals,
    bootstrap_presence_intervals,
    bbox_iou,
    detector_predictions,
    draw_context_overlay,
    draw_lstm_provenance_overlay,
    load_bbox_annotations,
    load_context_overlay,
    load_presence_annotations,
    sha256_file,
)


def test_context_keeps_confidence_separate_from_phi() -> None:
    event = ContextEvent(3, 50, 0.2, {"proximity": 0.7}, 0.9, False)
    assert event.phi == 0.2
    assert event.detector_confidence == 0.9


def test_observation_requires_positive_covariance_and_lidar_support() -> None:
    observation = HumanObservation(
        100,
        "base_link",
        np.array((1.0, 2.0)),
        0.01 * np.eye(2),
        0.8,
        4,
    )
    assert observation.position_xy.shape == (2,)
    with pytest.raises(ValueError, match="positive definite"):
        HumanObservation(
            100,
            "base_link",
            np.zeros(2),
            np.zeros((2, 2)),
            0.8,
            4,
        )


def test_track_state_requires_monotonic_measurement_metadata() -> None:
    track = TrackState(
        1,
        100,
        "base_link",
        np.array((1.0, 2.0)),
        np.array((0.1, 0.0)),
        0.01 * np.eye(2),
        0.8,
        0,
        2,
    )
    assert track.hits == 2
    with pytest.raises(ValueError, match="hit count"):
        TrackState(
            1,
            100,
            "base_link",
            np.zeros(2),
            np.zeros(2),
            0.01 * np.eye(2),
            0.8,
            0,
            0,
        )


def test_context_overlay_is_a_current_snapshot_with_direction_provenance(tmp_path) -> None:
    payload = {
        "schema": CONTEXT_SCHEMA,
        "records": [
            {
                "asset_id": "asset-1",
                "position_xy": [0.2, 0.4],
                "heading_unit": [0.0, 1.0],
                "speed_mps": 0.3,
                "direction": "forward",
                "context_valid": True,
                "confidence": 0.91,
                "timestamp_ns": 10,
                "frame_id": "frame-1",
                "track_id": 4,
                "coordinate_units": "image_norm",
                "source_sha256": "a" * 64,
                "model_sha256": "b" * 64,
            }
        ],
    }
    path = tmp_path / "context.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    records = load_context_overlay(path)
    assert records["asset-1"]["direction"] == "forward"
    assert records["asset-1"]["model_sha256"] == "b" * 64


def test_context_overlay_draws_lstm_snapshot_without_path_geometry(tmp_path) -> None:
    payload = {
        "schema": CONTEXT_SCHEMA,
        "records": [
            {
                "asset_id": "asset-1",
                "position_xy": [0.2, 0.4],
                "heading_unit": [0.0, 1.0],
                "speed_mps": 0.3,
                "direction": "forward",
                "context_valid": True,
                "confidence": 0.91,
                "timestamp_ns": 10,
                "frame_id": "frame-1",
                "track_id": 4,
                "coordinate_units": "image_norm",
                "source_sha256": "a" * 64,
                "model_sha256": "b" * 64,
            }
        ],
    }
    path = tmp_path / "context.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    context = load_context_overlay(path)["asset-1"]
    image = np.zeros((180, 320, 3), dtype=np.uint8)
    overlay = draw_context_overlay(image, context, "/tmp/context/ctx_lstm.pt")
    assert overlay.shape == image.shape
    assert overlay.dtype == image.dtype
    assert np.any(overlay != image)
    assert not any(key in context for key in ("trajectory", "path", "future_positions", "future_path"))


def test_static_image_overlay_draws_lstm_path_without_fabricating_context() -> None:
    image = np.zeros((180, 320, 3), dtype=np.uint8)
    overlay = draw_lstm_provenance_overlay(image, "D:/models/ctx_lstm.pt")
    assert overlay.shape == image.shape
    assert overlay.dtype == image.dtype
    assert np.any(overlay != image)


def test_context_overlay_rejects_a_human_trajectory(tmp_path) -> None:
    payload = {
        "schema": CONTEXT_SCHEMA,
        "records": [{"asset_id": "asset-1", "path": [[0.0, 0.0]]}],
    }
    path = tmp_path / "context.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="current snapshot"):
        load_context_overlay(path)


def test_context_overlay_rejects_future_position_variant(tmp_path) -> None:
    payload = {
        "schema": CONTEXT_SCHEMA,
        "records": [{"asset_id": "asset-1", "future_position_x_m": 1.0}],
    }
    path = tmp_path / "context.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="current snapshot"):
        load_context_overlay(path)


def test_context_overlay_rejects_unknown_nontrajectory_field(tmp_path) -> None:
    payload = {
        "schema": CONTEXT_SCHEMA,
        "records": [
            {
                "asset_id": "asset-1",
                "position_xy": [0.2, 0.4],
                "heading_unit": [0.0, 1.0],
                "speed_mps": 0.3,
                "direction": "forward",
                "context_valid": True,
                "confidence": 0.91,
                "timestamp_ns": 10,
                "frame_id": "frame-1",
                "track_id": 4,
                "coordinate_units": "image_norm",
                "source_sha256": "a" * 64,
                "model_sha256": "b" * 64,
                "unregistered_note": "must be rejected",
            }
        ],
    }
    path = tmp_path / "context.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported context overlay fields"):
        load_context_overlay(path)


def test_pose_detector_predictions_keep_seventeen_keypoints() -> None:
    class Tensor:
        def __init__(self, value):
            self.value = np.asarray(value)

        def detach(self):
            return self

        def cpu(self):
            return self

        def numpy(self):
            return self.value

    class Boxes:
        xyxy = Tensor([[1.0, 2.0, 30.0, 60.0]])
        conf = Tensor([0.9])
        cls = Tensor([0])

    class Keypoints:
        xy = Tensor(np.ones((1, 17, 2)))
        conf = Tensor(np.full((1, 17), 0.8))

    rows = detector_predictions(type("Result", (), {"boxes": Boxes(), "keypoints": Keypoints()})())
    assert len(rows) == 1
    assert len(rows[0]["keypoints_xy"]) == 17
    assert rows[0]["keypoint_valid"] == [True] * 17


def test_pose_detector_predictions_fail_closed_without_keypoints() -> None:
    class Tensor:
        def __init__(self, value):
            self.value = np.asarray(value)

        def detach(self):
            return self

        def cpu(self):
            return self

        def numpy(self):
            return self.value

    class Boxes:
        xyxy = Tensor([[1.0, 2.0, 30.0, 60.0]])
        conf = Tensor([0.9])
        cls = Tensor([0])

    with pytest.raises(RuntimeError, match="missing keypoints"):
        detector_predictions(type("Result", (), {"boxes": Boxes(), "keypoints": None})())


def test_context_overlay_rejects_nonunit_valid_heading(tmp_path) -> None:
    payload = {
        "schema": CONTEXT_SCHEMA,
        "records": [
            {
                "asset_id": "asset-1",
                "position_xy": [0.2, 0.4],
                "heading_unit": [0.0, 2.0],
                "speed_mps": 0.3,
                "direction": "forward",
                "context_valid": True,
                "confidence": 0.91,
                "timestamp_ns": 10,
                "frame_id": "frame-1",
                "track_id": 4,
                "coordinate_units": "image_norm",
                "source_sha256": "a" * 64,
                "model_sha256": "b" * 64,
            }
        ],
    }
    path = tmp_path / "context.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="unit heading"):
        load_context_overlay(path)


def test_bbox_iou_and_candidate_metrics_are_deterministic() -> None:
    assert bbox_iou([0.0, 0.0, 10.0, 10.0], [5.0, 5.0, 15.0, 15.0]) == pytest.approx(1.0 / 7.0)
    assert bbox_iou([0.0, 0.0, 1.0, 1.0], [2.0, 2.0, 3.0, 3.0]) == 0.0
    evaluated = [
        {
            "asset_id": "asset-1",
            "predictions": [
                {"confidence": 0.9, "xyxy": [0.0, 0.0, 10.0, 10.0]},
                {"confidence": 0.2, "xyxy": [20.0, 20.0, 30.0, 30.0]},
            ],
        }
    ]
    metrics = aggregate_bbox_metrics(evaluated, {"asset-1": [[0.0, 0.0, 10.0, 10.0]]}, 0.5)
    assert metrics["tp"] == 1
    assert metrics["fp"] == 1
    assert metrics["fn"] == 0
    assert metrics["average_precision"] == pytest.approx(1.0)


def test_presence_sweep_uses_the_declared_confidence_threshold() -> None:
    evaluated = [
        {
            "ground_truth_person_present": True,
            "predictions": [{"confidence": 0.4}],
        },
        {
            "ground_truth_person_present": False,
            "predictions": [{"confidence": 0.2}],
        },
    ]
    low = aggregate_presence_metrics(evaluated, 0.1)
    high = aggregate_presence_metrics(evaluated, 0.5)
    assert low["confusion_matrix"]["rows_ground_truth_columns_prediction"] == [[0, 1], [0, 1]]
    assert high["confusion_matrix"]["rows_ground_truth_columns_prediction"] == [[1, 0], [1, 0]]


def test_presence_bootstrap_intervals_are_deterministic() -> None:
    evaluated = [
        {"ground_truth_person_present": True, "predictions": [{"confidence": 0.9}]},
        {"ground_truth_person_present": True, "predictions": []},
        {"ground_truth_person_present": False, "predictions": [{"confidence": 0.8}]},
        {"ground_truth_person_present": False, "predictions": []},
    ]
    first = bootstrap_presence_intervals(evaluated, 0.5, replicates=30, seed=4)
    second = bootstrap_presence_intervals(evaluated, 0.5, replicates=30, seed=4)
    assert first == second
    assert first["f1"]["image_count"] == 4
    assert first["precision"]["confidence_level"] == pytest.approx(0.95)


def test_bbox_bootstrap_intervals_use_image_units() -> None:
    evaluated = [
        {
            "asset_id": "asset-1",
            "predictions": [{"confidence": 0.9, "xyxy": [0.0, 0.0, 10.0, 10.0]}],
        },
        {
            "asset_id": "asset-2",
            "predictions": [{"confidence": 0.2, "xyxy": [20.0, 20.0, 30.0, 30.0]}],
        },
    ]
    annotations = {"asset-1": [[0.0, 0.0, 10.0, 10.0]], "asset-2": []}
    intervals = bootstrap_bbox_intervals(evaluated, annotations, 0.5, 0.1, replicates=30, seed=5)
    assert intervals["precision"]["image_count"] == 2
    assert intervals["recall"]["replicates"] == 30


def test_blind_bbox_annotations_bind_to_manifest_and_cover_each_asset(tmp_path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"records": [{"asset_id": "asset-1"}]}), encoding="utf-8")
    annotation = tmp_path / "annotations.json"
    annotation.write_text(
        json.dumps(
            {
                "schema": ANNOTATION_SCHEMA,
                "blinded_to_predictions": True,
                "source_manifest": {"path": "manifest.json", "sha256": sha256_file(manifest)},
                "records": [
                    {
                        "asset_id": "asset-1",
                        "image_width": 100,
                        "image_height": 80,
                        "persons": [{"bbox_xyxy": [10.0, 5.0, 40.0, 50.0]}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    loaded = load_bbox_annotations(annotation, manifest, "manifest.json", [{"asset_id": "asset-1"}])
    assert loaded == {"asset-1": [[10.0, 5.0, 40.0, 50.0]]}


def test_blind_bbox_annotations_reject_unknown_asset(tmp_path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"records": [{"asset_id": "asset-1"}]}), encoding="utf-8")
    annotation = tmp_path / "annotations.json"
    annotation.write_text(
        json.dumps(
            {
                "schema": ANNOTATION_SCHEMA,
                "blinded_to_predictions": True,
                "source_manifest": {"path": "manifest.json", "sha256": sha256_file(manifest)},
                "records": [
                    {
                        "asset_id": "asset-2",
                        "image_width": 100,
                        "image_height": 80,
                        "persons": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="exactly one record per image"):
        load_bbox_annotations(annotation, manifest, "manifest.json", [{"asset_id": "asset-1"}])


def test_presence_annotations_bind_to_manifest_and_preserve_blind_status(tmp_path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"records": [{"asset_id": "asset-1"}, {"asset_id": "asset-2"}]}),
        encoding="utf-8",
    )
    annotation = tmp_path / "presence.json"
    annotation.write_text(
        json.dumps(
            {
                "schema": PRESENCE_SCHEMA,
                "annotation_status": "candidate-single-annotator",
                "annotator_id": "internal-candidate",
                "guideline_version": "presence-v1",
                "blinded_to_predictions": True,
                "source_manifest": {"path": "manifest.json", "sha256": sha256_file(manifest)},
                "records": [
                    {"asset_id": "asset-1", "person_present": True},
                    {"asset_id": "asset-2", "person_present": False},
                ],
            }
        ),
        encoding="utf-8",
    )
    loaded = load_presence_annotations(
        annotation,
        manifest,
        "manifest.json",
        [{"asset_id": "asset-1"}, {"asset_id": "asset-2"}],
    )
    assert loaded == {"asset-1": True, "asset-2": False}


def test_context_baselines_use_only_observed_velocity_history() -> None:
    history = np.asarray(
        [
            [[-0.2, 0.0, 0.4, 0.0, 1.0], [-0.1, 0.0, 0.4, 0.0, 1.0], [0.0, 0.0, 0.4, 0.0, 1.0]],
            [[-0.2, 0.0, 0.4, 0.0, 1.0], [-0.1, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 1.0]],
        ],
        dtype=np.float32,
    )
    target = np.asarray([[0.4, 0.0], [0.0, 0.0]], dtype=np.float32)
    assert np.allclose(constant_velocity_predictions(history), target)
    kalman = kalman_velocity_predictions(history)
    assert kalman.shape == target.shape
    assert np.all(np.isfinite(kalman))
    baselines = evaluate_baselines(history, target)
    assert set(baselines) == {"constant_velocity", "kalman_velocity"}
    assert baselines["constant_velocity"]["speed_mae_mps"] == pytest.approx(0.0)


def test_context_metrics_report_calibration_and_bootstrap_without_labels_for_training() -> None:
    target = np.asarray([[0.4, 0.0], [0.0, 0.4], [-0.4, 0.0], [0.0, -0.4]], dtype=np.float32)
    metrics = evaluate_predictions(target, target)
    assert np.allclose(direction_probabilities(target).sum(axis=1), 1.0)
    assert metrics["direction_calibration"]["moving_target_count"] == 4
    assert metrics["direction_calibration"]["valid_prediction_count"] == 4
    assert 0.0 <= metrics["direction_calibration"]["ece_10_bin"] <= 1.0
    assert metrics["bootstrap_95ci"]["direction_macro_f1"]["replicates"] == 400
    assert [item["class"] for item in metrics["direction_class_metrics"]] == [
        "left",
        "right",
        "forward",
        "backward",
    ]
    assert all(item["support"] == 1 for item in metrics["direction_class_metrics"])
    assert all(item["precision"] == pytest.approx(1.0) for item in metrics["direction_class_metrics"])
    assert all(item["recall"] == pytest.approx(1.0) for item in metrics["direction_class_metrics"])
    assert metrics["direction_labels_used_for_training"] is False


def test_temperature_calibration_is_deterministic_and_uses_valid_moving_samples() -> None:
    target = np.asarray(
        [[0.4, 0.0], [0.0, 0.4], [-0.4, 0.0], [0.0, -0.4]] * 2,
        dtype=np.float32,
    )
    predicted = np.asarray(
        [[0.4, 0.08], [0.08, 0.4], [-0.4, -0.08], [-0.08, -0.4]] * 2,
        dtype=np.float32,
    )
    first = fit_temperature(predicted, target, minimum_samples=4)
    second = fit_temperature(predicted, target, minimum_samples=4)
    assert first["status"] == "fit"
    assert first["source_split"] == "calibration"
    assert first["valid_sample_count"] == 8
    assert first["temperature"] == pytest.approx(second["temperature"])
    assert first["nll_after"] <= first["nll_before"] + 1.0e-12


def test_evaluation_records_calibration_temperature_and_source() -> None:
    target = np.asarray([[0.4, 0.0], [0.0, 0.4], [-0.4, 0.0], [0.0, -0.4]], dtype=np.float32)
    metrics = evaluate_predictions(
        target,
        target,
        temperature=0.5,
        calibration_method="temperature_scaling_grid",
        calibration_source_split="calibration",
    )
    calibration = metrics["direction_calibration"]
    assert calibration["temperature"] == pytest.approx(0.5)
    assert calibration["method"] == "temperature_scaling_grid"
    assert calibration["source_split"] == "calibration"


def test_score_loop_seed_selection_retains_failures_and_tie_break() -> None:
    def candidate(seed: int):
        if seed == 1:
            raise RuntimeError("deliberate candidate failure")
        model = ContextDirectionLstm()
        score = 0.8 if seed in {2, 3} else 0.7
        return model, {"best_validation_score": score, "seed": seed}, [{"epoch": 1}]

    _, training, _, selection = select_training_seed([3, 1, 2], candidate)
    assert training["seed"] == 2
    assert selection["requested_seed_count"] == 3
    assert selection["completed_seed_count"] == 2
    assert selection["failed_seed_count"] == 1
    assert selection["selected_seed"] == 2
    assert [row["status"] for row in selection["ledger"]] == ["completed", "failed", "completed"]


def test_position_state_entrypoints_use_compiled_controller_boundary() -> None:
    root = Path(__file__).resolve().parents[3]
    for relative in ("scripts/python/tools/map_run.py", "scripts/python/tools/record_hardware.py"):
        source = (root / relative).read_text(encoding="utf-8")
        assert "simulation.realtime_nmpc" not in source
        assert "CompiledController" in source
    assert "class NmpcPrediction" in (root / "src/simulation/model.py").read_text(encoding="utf-8")
