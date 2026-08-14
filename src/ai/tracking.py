from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .detection import Detection2D
from .contracts import HumanObservation, TrackState


def assign_projected_points(
    pixel: NDArray[np.float64],
    valid: NDArray[np.bool_],
    detections: tuple[Detection2D, ...],
) -> NDArray[np.int64]:
    scores = np.full((len(pixel), len(detections)), np.inf)
    for index, item in enumerate(detections):
        x1, y1, x2, y2 = item.xyxy
        inside = (
            valid
            & (pixel[:, 0] >= x1)
            & (pixel[:, 0] <= x2)
            & (pixel[:, 1] >= y1)
            & (pixel[:, 1] <= y2)
        )
        center = np.array([(x1 + x2) / 2.0, (y1 + y2) / 2.0])
        scale = np.array([x2 - x1, y2 - y1])
        scores[inside, index] = np.linalg.norm(
            (pixel[inside] - center) / scale, axis=1
        )
    best = np.argmin(scores, axis=1)
    best[np.isinf(scores[np.arange(len(pixel)), best])] = -1
    return best.astype(np.int64)


def associate_tracks(
    predicted: dict[int, TrackState],
    observations: tuple[HumanObservation, ...],
    gate_m: float,
) -> tuple[tuple[int, int], ...]:
    candidates = []
    for track_id, state in predicted.items():
        for index, observation in enumerate(observations):
            distance = float(np.linalg.norm(state.position_xy - observation.position_xy))
            if distance <= gate_m:
                candidates.append((distance, track_id, index))
    assigned_tracks, assigned_observations, pairs = set(), set(), []
    for _, track_id, index in sorted(candidates):
        if track_id not in assigned_tracks and index not in assigned_observations:
            pairs.append((track_id, index))
            assigned_tracks.add(track_id)
            assigned_observations.add(index)
    return tuple(pairs)


def predict_tracks(
    tracks: dict[int, TrackState],
    last_measurement_ns: dict[int, int],
    timestamp_ns: int,
    process_variance_m2_per_s: float,
) -> dict[int, TrackState]:
    result = {}
    for track_id, state in tracks.items():
        if timestamp_ns < state.timestamp_ns:
            raise ValueError("tracker timestamps must be monotonic")
        dt = (timestamp_ns - state.timestamp_ns) * 1e-9
        covariance = state.covariance_xy + np.eye(2) * (
            process_variance_m2_per_s * dt
        )
        result[track_id] = TrackState(
            track_id=track_id,
            timestamp_ns=timestamp_ns,
            frame_id=state.frame_id,
            position_xy=state.position_xy + dt * state.velocity_xy,
            velocity_xy=state.velocity_xy,
            covariance_xy=covariance,
            detector_confidence=state.detector_confidence,
            measurement_age_ns=timestamp_ns - last_measurement_ns[track_id],
            hits=state.hits,
        )
    return result


def correct_track(
    prediction: TrackState,
    observation: HumanObservation,
    last_measurement_ns: int,
    alpha: float,
    beta: float,
) -> TrackState:
    dt = max((observation.timestamp_ns - last_measurement_ns) * 1e-9, 1e-6)
    residual = observation.position_xy - prediction.position_xy
    covariance = (1.0 - alpha) * prediction.covariance_xy
    covariance += alpha * observation.covariance_xy
    return TrackState(
        track_id=prediction.track_id,
        timestamp_ns=observation.timestamp_ns,
        frame_id=observation.frame_id,
        position_xy=prediction.position_xy + alpha * residual,
        velocity_xy=prediction.velocity_xy + beta * residual / dt,
        covariance_xy=covariance,
        detector_confidence=observation.detector_confidence,
        measurement_age_ns=0,
        hits=prediction.hits + 1,
    )


@dataclass(frozen=True)
class TrackerConfig:
    association_gate_m: float = 1.0
    maximum_age_ns: int = 500_000_000
    alpha: float = 0.65
    beta: float = 0.20
    process_variance_m2_per_s: float = 0.04


class TrackManager:
    """Deterministic alpha-beta tracker with explicit stale-track expiry."""

    def __init__(self, config: TrackerConfig = TrackerConfig()) -> None:
        if config.association_gate_m <= 0.0 or config.maximum_age_ns <= 0:
            raise ValueError("invalid tracker gate or age")
        if not 0.0 < config.alpha <= 1.0 or not 0.0 <= config.beta <= 1.0:
            raise ValueError("invalid alpha-beta gains")
        self._config = config
        self._tracks: dict[int, TrackState] = {}
        self._last_measurement_ns: dict[int, int] = {}
        self._next_id = 1

    def update(
        self, observations: tuple[HumanObservation, ...], timestamp_ns: int
    ) -> tuple[TrackState, ...]:
        if timestamp_ns < 0:
            raise ValueError("timestamp must be nonnegative")
        if any(item.timestamp_ns != timestamp_ns for item in observations):
            raise ValueError("observations must match update timestamp")
        frames = {item.frame_id for item in observations}
        if len(frames) > 1:
            raise ValueError("all observations must use one tracking frame")
        if self._tracks and frames:
            active_frame = next(iter(self._tracks.values())).frame_id
            if next(iter(frames)) != active_frame:
                raise ValueError("tracking frame cannot change while tracks are active")
        predicted = predict_tracks(
            self._tracks,
            self._last_measurement_ns,
            timestamp_ns,
            self._config.process_variance_m2_per_s,
        )
        pairs = associate_tracks(
            predicted, observations, self._config.association_gate_m
        )
        matched_tracks = {track_id for track_id, _ in pairs}
        matched_observations = {index for _, index in pairs}
        for track_id, index in pairs:
            self._tracks[track_id] = correct_track(
                predicted[track_id],
                observations[index],
                self._last_measurement_ns[track_id],
                self._config.alpha,
                self._config.beta,
            )
            self._last_measurement_ns[track_id] = timestamp_ns
        for track_id, state in predicted.items():
            if track_id not in matched_tracks:
                self._tracks[track_id] = state
        for index, observation in enumerate(observations):
            if index not in matched_observations:
                self._create(observation)
        self._expire(timestamp_ns)
        return tuple(self._tracks[key] for key in sorted(self._tracks))

    def _create(self, observation: HumanObservation) -> None:
        track_id = self._next_id
        self._next_id += 1
        self._tracks[track_id] = TrackState(
            track_id=track_id,
            timestamp_ns=observation.timestamp_ns,
            frame_id=observation.frame_id,
            position_xy=observation.position_xy,
            velocity_xy=np.zeros(2),
            covariance_xy=observation.covariance_xy,
            detector_confidence=observation.detector_confidence,
            measurement_age_ns=0,
            hits=1,
        )
        self._last_measurement_ns[track_id] = observation.timestamp_ns

    def _expire(self, timestamp_ns: int) -> None:
        expired = [
            track_id
            for track_id, measured_ns in self._last_measurement_ns.items()
            if timestamp_ns - measured_ns > self._config.maximum_age_ns
        ]
        for track_id in expired:
            del self._tracks[track_id]
            del self._last_measurement_ns[track_id]
