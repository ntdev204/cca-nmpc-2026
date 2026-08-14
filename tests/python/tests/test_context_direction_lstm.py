import numpy as np
import pytest
import torch

from ai.ctx_lstm import (
    CHECKPOINT_SCHEMA,
    ContextDirectionPrediction,
    direction_context_to_heading_observation,
    load_context_lstm,
    prediction_to_heading_observation,
    require_fitted_calibration,
)
from ai.ctx_lstm import (
    DIRECTION_CLASSES,
    ContextDirectionLstm,
)


def test_context_direction_lstm_returns_direction_and_speed_only() -> None:
    model = ContextDirectionLstm()
    history = torch.zeros((2, 20, 5), dtype=torch.float32)
    prediction = model(history)
    assert prediction.direction_logits.shape == (2, 4)
    assert prediction.direction_probabilities.shape == (2, 4)
    assert prediction.speed_mps.shape == (2,)
    assert torch.isfinite(prediction.speed_mps).all()
    assert not hasattr(prediction, "mean_xy")


def test_direction_scores_are_derived_from_context_velocity() -> None:
    model = ContextDirectionLstm()
    history = torch.randn((3, 20, 5), dtype=torch.float32)
    prediction = model(history)
    assert prediction.context_velocity_xy.shape == (3, 2)
    assert hasattr(model, "velocity_head")
    assert not hasattr(model, "direction_head")
    torch.testing.assert_close(
        prediction.speed_mps,
        torch.linalg.vector_norm(prediction.context_velocity_xy, dim=-1),
    )
    torch.testing.assert_close(
        prediction.direction_probabilities.sum(dim=-1),
        torch.ones(3),
    )


def test_context_lstm_checkpoint_loader_preserves_inference(tmp_path) -> None:
    model = ContextDirectionLstm()
    checkpoint_path = tmp_path / "ctx_lstm.pt"
    torch.save(
        {
            "schema": CHECKPOINT_SCHEMA,
            "model_config": model.config.__dict__,
            "state_dict": model.state_dict(),
            "training_mode": "self_supervised_score_loop",
            "direction_labels_used_for_training": False,
        },
        checkpoint_path,
    )
    loaded, metadata = load_context_lstm(checkpoint_path)
    history = torch.randn((2, 20, 5), dtype=torch.float32)
    torch.testing.assert_close(model(history).context_velocity_xy, loaded(history).context_velocity_xy)
    assert metadata["schema"] == CHECKPOINT_SCHEMA


def test_context_lstm_loader_applies_fitted_calibration_temperature(tmp_path) -> None:
    model = ContextDirectionLstm()
    checkpoint_path = tmp_path / "calibrated_ctx_lstm.pt"
    torch.save(
        {
            "schema": CHECKPOINT_SCHEMA,
            "model_config": model.config.__dict__,
            "state_dict": model.state_dict(),
            "training_mode": "self_supervised_score_loop",
            "direction_labels_used_for_training": False,
            "calibration": {
                "status": "fit",
                "method": "temperature_scaling_grid",
                "temperature": 0.5,
                "source_split": "calibration",
                "valid_sample_count": 30,
                "minimum_sample_count": 30,
                "nll_before": 1.0,
                "nll_after": 0.5,
                "independent_from_training_validation_and_test": True,
            },
        },
        checkpoint_path,
    )
    loaded, _ = load_context_lstm(checkpoint_path)
    assert loaded.calibration_temperature == pytest.approx(0.5)
    prediction = loaded(torch.randn((2, 20, 5), dtype=torch.float32))
    torch.testing.assert_close(
        prediction.direction_probabilities,
        torch.softmax(prediction.direction_logits / 0.5, dim=-1),
    )


def test_control_gate_rejects_unfitted_calibration() -> None:
    with pytest.raises(ValueError, match="status=fit"):
        require_fitted_calibration(
            {
                "calibration": {
                    "status": "not_fit",
                    "method": "none",
                    "temperature": 1.0,
                    "source_split": None,
                    "independent_from_training_validation_and_test": False,
                }
            }
        )


def test_control_gate_accepts_independent_fitted_calibration() -> None:
    calibration = require_fitted_calibration(
        {
            "calibration": {
                "status": "fit",
                "method": "temperature_scaling_grid",
                "temperature": 0.8,
                "source_split": "calibration",
                "valid_sample_count": 30,
                "minimum_sample_count": 30,
                "nll_before": 1.0,
                "nll_after": 0.9,
                "independent_from_training_validation_and_test": True,
            }
        }
    )
    assert calibration["status"] == "fit"


def test_context_lstm_loader_rejects_calibration_from_test_partition(tmp_path) -> None:
    model = ContextDirectionLstm()
    checkpoint_path = tmp_path / "invalid_calibration_ctx_lstm.pt"
    torch.save(
        {
            "schema": CHECKPOINT_SCHEMA,
            "model_config": model.config.__dict__,
            "state_dict": model.state_dict(),
            "training_mode": "self_supervised_score_loop",
            "direction_labels_used_for_training": False,
            "calibration": {
                "status": "fit",
                "method": "temperature_scaling_grid",
                "temperature": 0.5,
                "source_split": "test_id",
                "valid_sample_count": 30,
                "minimum_sample_count": 30,
                "nll_before": 1.0,
                "nll_after": 0.5,
                "independent_from_training_validation_and_test": True,
            },
        },
        checkpoint_path,
    )
    with pytest.raises(ValueError, match="calibration split"):
        load_context_lstm(checkpoint_path)


def test_lstm_prediction_becomes_current_heading_only() -> None:
    prediction = ContextDirectionPrediction(
        direction_logits=torch.tensor([[0.0, 1.0, 0.0, 0.0]]),
        speed_mps=torch.tensor([0.5]),
        context_velocity_xy=torch.tensor([[0.3, 0.4]]),
    )
    observation = prediction_to_heading_observation(
        prediction,
        position_xy=np.asarray((1.0, 2.0)),
        timestamp_ns=100,
        frame_id="map",
        track_id=2,
        source_sha256="b" * 64,
        coordinate_units="map_m",
    )
    assert observation.heading_valid
    np.testing.assert_allclose(observation.heading_unit, (0.6, 0.8))
    np.testing.assert_allclose(observation.speed_per_s, 0.5)
    assert observation.sample_count == 1


def test_context_lstm_loader_rejects_non_score_checkpoint(tmp_path) -> None:
    path = tmp_path / "invalid.pt"
    torch.save(
        {
            "schema": CHECKPOINT_SCHEMA,
            "model_config": ContextDirectionLstm().config.__dict__,
            "state_dict": ContextDirectionLstm().state_dict(),
            "training_mode": "supervised_direction",
            "direction_labels_used_for_training": True,
        },
        path,
    )
    with pytest.raises(ValueError, match="self-supervised score loop"):
        load_context_lstm(path)


def test_direction_context_adapter_does_not_construct_a_path() -> None:
    observation = direction_context_to_heading_observation(
        "forward",
        position_xy=np.asarray((1.0, 2.0)),
        speed_mps=0.4,
        direction_confidence=0.8,
        timestamp_ns=100,
        frame_id="frame-1",
        track_id=1,
        source_sha256="a" * 64,
        coordinate_units="map_m",
    )
    assert observation.heading_valid
    np.testing.assert_allclose(observation.position_xy, (1.0, 2.0))
    np.testing.assert_allclose(observation.heading_unit, (0.0, 1.0))
    assert DIRECTION_CLASSES[2] == "forward"
