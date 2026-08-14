"""Score-trained LSTM interface for directional human context.

The network learns a two-dimensional context-velocity vector from an observed
history.  Training is self-supervised: the target is the next observed
velocity, not a human-provided direction label.  Direction probabilities are
derived from cosine scores against four fixed axes.  The model never decodes
or returns a human position sequence; robot path generation remains separate
from the image branch.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor, nn
from torch.nn import functional as functional
from numpy.typing import NDArray

from shared import load_contract
from .heading import HumanHeadingObservation


DIRECTION_CLASSES: tuple[str, ...] = ("left", "right", "forward", "backward")
CHECKPOINT_SCHEMA = "cca-context-direction-lstm-score-trained-checkpoint-v2"
MAX_CONTEXT_SPEED_MPS = float(load_contract()["context"].get("max_speed_mps", 2.0))


@dataclass(frozen=True)
class ContextDirectionConfig:
    input_size: int = 5
    hidden_size: int = 48
    num_layers: int = 1
    direction_classes: tuple[str, ...] = DIRECTION_CLASSES
    input_mean: tuple[float, ...] = ()
    input_std: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        if min(self.input_size, self.hidden_size, self.num_layers) < 1:
            raise ValueError("LSTM dimensions must be positive")
        if tuple(self.direction_classes) != DIRECTION_CLASSES:
            raise ValueError("direction class order is fixed by the interface")
        if bool(self.input_mean) != bool(self.input_std):
            raise ValueError("input normalization requires mean and std")
        if self.input_mean and (
            len(self.input_mean) != self.input_size
            or len(self.input_std) != self.input_size
            or min(self.input_std) <= 0.0
        ):
            raise ValueError("input normalization does not match input size")


@dataclass(frozen=True)
class ContextDirectionPrediction:
    direction_logits: Tensor
    speed_mps: Tensor
    context_velocity_xy: Tensor
    calibration_temperature: float = 1.0

    @property
    def direction_probabilities(self) -> Tensor:
        if not np.isfinite(self.calibration_temperature) or self.calibration_temperature <= 0.0:
            raise ValueError("calibration temperature must be finite and positive")
        return torch.softmax(self.direction_logits / self.calibration_temperature, dim=-1)


def prediction_to_heading_observation(
    prediction: ContextDirectionPrediction,
    *,
    position_xy: NDArray[np.floating],
    timestamp_ns: int,
    frame_id: str,
    track_id: int,
    source_sha256: str,
    coordinate_units: str,
    minimum_speed_per_s: float = 1.0e-3,
) -> HumanHeadingObservation:
    velocity = prediction.context_velocity_xy.detach().cpu().numpy()
    probabilities = prediction.direction_probabilities.detach().cpu().numpy()
    if velocity.shape != (1, 2) or probabilities.shape != (1, len(DIRECTION_CLASSES)):
        raise ValueError("prediction must contain exactly one context sample")
    vector = np.asarray(velocity[0], dtype=np.float64)
    if not np.isfinite(vector).all() or minimum_speed_per_s < 0.0:
        raise ValueError("prediction velocity and minimum speed must be finite")
    speed = float(np.linalg.norm(vector))
    if speed > MAX_CONTEXT_SPEED_MPS:
        raise ValueError("predicted context speed exceeds the physical context bound")
    valid = speed >= minimum_speed_per_s
    heading = vector / speed if valid else np.zeros(2, dtype=np.float64)
    confidence = float(np.max(probabilities[0])) if valid else 0.0
    return HumanHeadingObservation(
        timestamp_ns=int(timestamp_ns),
        frame_id=frame_id,
        track_id=int(track_id),
        position_xy=np.asarray(position_xy, dtype=np.float64),
        heading_unit=heading,
        speed_per_s=speed if valid else 0.0,
        heading_valid=valid,
        confidence=float(np.clip(confidence, 0.0, 1.0)),
        sample_count=1,
        coordinate_units=coordinate_units,
        source_sha256=source_sha256,
    )


class ContextDirectionLstm(nn.Module):
    """Predict context velocity and score its four axis-aligned directions."""

    def __init__(self, config: ContextDirectionConfig = ContextDirectionConfig()) -> None:
        super().__init__()
        self.config = config
        self.encoder = nn.LSTM(
            input_size=config.input_size,
            hidden_size=config.hidden_size,
            num_layers=config.num_layers,
            batch_first=True,
        )
        self.velocity_head = nn.Linear(config.hidden_size, 2)
        mean = (
            torch.tensor(config.input_mean, dtype=torch.float32)
            if config.input_mean
            else torch.zeros(config.input_size)
        )
        std = (
            torch.tensor(config.input_std, dtype=torch.float32)
            if config.input_std
            else torch.ones(config.input_size)
        )
        self.register_buffer("_input_mean", mean, persistent=False)
        self.register_buffer("_input_std", std, persistent=False)
        self.calibration_temperature = 1.0

    def forward(self, history: Tensor) -> ContextDirectionPrediction:
        if history.ndim != 3 or history.shape[-1] != self.config.input_size:
            raise ValueError("history must have shape [batch, time, input_size]")
        normalized = (history - self._input_mean) / self._input_std
        encoded, _ = self.encoder(normalized)
        representation = encoded[:, -1]
        context_velocity_xy = self.velocity_head(representation)
        speed_mps = torch.linalg.vector_norm(context_velocity_xy, dim=-1)
        direction_axes = context_velocity_xy.new_tensor(
            ((-1.0, 0.0), (1.0, 0.0), (0.0, 1.0), (0.0, -1.0))
        )
        normalized_velocity = functional.normalize(context_velocity_xy, dim=-1, eps=1.0e-8)
        direction_logits = normalized_velocity @ direction_axes.T
        return ContextDirectionPrediction(
            direction_logits,
            speed_mps,
            context_velocity_xy,
            self.calibration_temperature,
        )


def _validate_calibration_metadata(metadata: Any) -> float:
    if metadata is None:
        return 1.0
    if not isinstance(metadata, dict):
        raise ValueError("checkpoint calibration metadata must be an object")
    status = metadata.get("status")
    method = metadata.get("method")
    temperature = metadata.get("temperature")
    if not isinstance(temperature, (int, float)) or not np.isfinite(float(temperature)):
        raise ValueError("checkpoint calibration temperature must be finite")
    if float(temperature) <= 0.0:
        raise ValueError("checkpoint calibration temperature must be positive")
    if status == "not_fit":
        if method != "none" or metadata.get("source_split") is not None:
            raise ValueError("unfitted calibration metadata must use method=none and no source split")
        if metadata.get("independent_from_training_validation_and_test") is not False:
            raise ValueError("unfitted calibration metadata cannot claim independent calibration")
        return float(temperature)
    if status != "fit":
        raise ValueError("checkpoint calibration status must be fit or not_fit")
    if method != "temperature_scaling_grid" or metadata.get("source_split") != "calibration":
        raise ValueError("fitted calibration must use temperature scaling from the calibration split")
    if metadata.get("independent_from_training_validation_and_test") is not True:
        raise ValueError("fitted calibration must be independent from training, validation and test")
    valid_count = metadata.get("valid_sample_count")
    minimum_count = metadata.get("minimum_sample_count")
    if (
        not isinstance(valid_count, int)
        or not isinstance(minimum_count, int)
        or valid_count < minimum_count
        or minimum_count < 1
    ):
        raise ValueError("fitted calibration sample support is invalid")
    for name in ("nll_before", "nll_after"):
        value = metadata.get(name)
        if not isinstance(value, (int, float)) or not np.isfinite(float(value)):
            raise ValueError(f"checkpoint calibration {name} must be finite")
    return float(temperature)


def load_context_lstm(
    checkpoint_path: Path,
    *,
    map_location: str | torch.device = "cpu",
) -> tuple[ContextDirectionLstm, dict[str, Any]]:
    path = Path(checkpoint_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    try:
        checkpoint = torch.load(path, map_location=map_location, weights_only=True)
    except TypeError:
        checkpoint = torch.load(path, map_location=map_location)
    if not isinstance(checkpoint, dict) or checkpoint.get("schema") != CHECKPOINT_SCHEMA:
        raise ValueError("unsupported context LSTM checkpoint schema")
    if checkpoint.get("training_mode") != "self_supervised_score_loop":
        raise ValueError("checkpoint was not produced by the self-supervised score loop")
    if checkpoint.get("direction_labels_used_for_training") is not False:
        raise ValueError("direction labels must not be used for LSTM training")
    calibration_temperature = _validate_calibration_metadata(checkpoint.get("calibration"))
    raw_config = checkpoint.get("model_config")
    if not isinstance(raw_config, dict):
        raise ValueError("checkpoint model_config is required")
    config_values = dict(raw_config)
    for name in ("direction_classes", "input_mean", "input_std"):
        if name in config_values and isinstance(config_values[name], list):
            config_values[name] = tuple(config_values[name])
    config = ContextDirectionConfig(**config_values)
    state_dict = checkpoint.get("state_dict")
    if not isinstance(state_dict, dict):
        raise ValueError("checkpoint state_dict is required")
    model = ContextDirectionLstm(config)
    model.calibration_temperature = calibration_temperature
    try:
        model.load_state_dict(state_dict, strict=True)
    except (RuntimeError, TypeError) as error:
        raise ValueError("checkpoint state_dict does not match model_config") from error
    model.eval()
    return model, checkpoint


def require_fitted_calibration(metadata: dict[str, Any]) -> dict[str, Any]:
    """Reject a checkpoint without independent calibration for control use."""

    calibration = metadata.get("calibration")
    if not isinstance(calibration, dict):
        raise ValueError("CCA control requires a fitted calibration record")
    if calibration.get("status") != "fit":
        raise ValueError("CCA control requires calibration status=fit")
    _validate_calibration_metadata(calibration)
    if calibration.get("independent_from_training_validation_and_test") is not True:
        raise ValueError("CCA control requires calibration independent of training, validation and test")
    return calibration


_DIRECTION_UNIT = {
    "left": np.asarray((-1.0, 0.0), dtype=np.float64),
    "right": np.asarray((1.0, 0.0), dtype=np.float64),
    "forward": np.asarray((0.0, 1.0), dtype=np.float64),
    "backward": np.asarray((0.0, -1.0), dtype=np.float64),
}


def direction_context_to_heading_observation(
    direction: str,
    *,
    position_xy: NDArray[np.floating],
    speed_mps: float,
    direction_confidence: float,
    timestamp_ns: int,
    frame_id: str,
    track_id: int,
    source_sha256: str,
    coordinate_units: str,
    minimum_speed_per_s: float = 1.0e-3,
) -> HumanHeadingObservation:
    if direction not in DIRECTION_CLASSES:
        raise ValueError(f"unsupported direction: {direction}")
    position = np.asarray(position_xy, dtype=np.float64)
    if position.shape != (2,) or not np.isfinite(position).all():
        raise ValueError("position_xy must have shape (2,) and be finite")
    if not np.isfinite(speed_mps) or speed_mps < 0.0:
        raise ValueError("speed_mps must be finite and nonnegative")
    if speed_mps > MAX_CONTEXT_SPEED_MPS:
        raise ValueError("context speed exceeds the physical context bound")
    if not np.isfinite(direction_confidence):
        raise ValueError("direction_confidence must be finite")
    speed = float(speed_mps)
    valid = speed >= minimum_speed_per_s
    return HumanHeadingObservation(
        timestamp_ns=int(timestamp_ns),
        frame_id=frame_id,
        track_id=int(track_id),
        position_xy=position,
        heading_unit=_DIRECTION_UNIT[direction] if valid else np.zeros(2),
        speed_per_s=speed if valid else 0.0,
        heading_valid=valid,
        confidence=float(np.clip(direction_confidence, 0.0, 1.0)) if valid else 0.0,
        sample_count=1,
        coordinate_units=coordinate_units,
        source_sha256=source_sha256,
    )
