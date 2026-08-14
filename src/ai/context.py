from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from shared import cpp_transport_library

from .contracts import ContextEvent


CONTEXT_FEATURE_NAMES = (
    "proximity",
    "closing",
    "cpa_time",
    "crossing_geometry",
    "density",
)


@dataclass(frozen=True)
class ContextConfig:
    distance_scale_m: float = 2.0
    closing_scale_mps: float = 1.0
    cpa_time_scale_s: float = 3.0
    bias: float = -2.0
    weights: tuple[float, float, float, float, float] = (2.0, 1.5, 1.0, 0.8, 0.6)


class _CcaContextScoreInput(ctypes.Structure):
    _fields_ = [
        ("track_id", ctypes.c_uint64),
        ("timestamp_ns", ctypes.c_uint64),
        ("relative_position_x_m", ctypes.c_double),
        ("relative_position_y_m", ctypes.c_double),
        ("relative_velocity_x_mps", ctypes.c_double),
        ("relative_velocity_y_mps", ctypes.c_double),
        ("robot_velocity_x_mps", ctypes.c_double),
        ("robot_velocity_y_mps", ctypes.c_double),
        ("human_velocity_x_mps", ctypes.c_double),
        ("human_velocity_y_mps", ctypes.c_double),
        ("local_density", ctypes.c_double),
        ("detector_confidence", ctypes.c_double),
        ("distance_scale_m", ctypes.c_double),
        ("closing_scale_mps", ctypes.c_double),
        ("cpa_time_scale_s", ctypes.c_double),
        ("bias", ctypes.c_double),
        ("weights", ctypes.c_double * 5),
    ]


class _CcaContextScoreOutput(ctypes.Structure):
    _fields_ = [
        ("track_id", ctypes.c_uint64),
        ("timestamp_ns", ctypes.c_uint64),
        ("phi", ctypes.c_double),
        ("detector_confidence", ctypes.c_double),
        ("calibration_valid", ctypes.c_uint8),
        ("features", ctypes.c_double * 5),
    ]


class _CppContextBackend:
    def __init__(self, library_path) -> None:
        self.library_path = library_path
        self._library = ctypes.CDLL(str(library_path))
        self._library.cca_context_score.argtypes = [
            ctypes.POINTER(_CcaContextScoreInput),
            ctypes.POINTER(_CcaContextScoreOutput),
            ctypes.c_char_p,
            ctypes.c_size_t,
        ]
        self._library.cca_context_score.restype = ctypes.c_int

    @staticmethod
    def _error(buffer: ctypes.Array[ctypes.c_char]) -> str:
        return (
            bytes(buffer).split(b"\0", 1)[0].decode("utf-8", errors="replace")
            or "C++ context scorer failed"
        )

    def score(
        self,
        track_id: int,
        timestamp_ns: int,
        position: NDArray[np.float64],
        velocity: NDArray[np.float64],
        robot_velocity: NDArray[np.float64],
        human_velocity: NDArray[np.float64],
        normalized_density: float,
        detector_confidence: float,
        config: ContextConfig,
    ) -> tuple[dict[str, float], float]:
        payload = _CcaContextScoreInput(
            track_id=int(track_id),
            timestamp_ns=int(timestamp_ns),
            relative_position_x_m=float(position[0]),
            relative_position_y_m=float(position[1]),
            relative_velocity_x_mps=float(velocity[0]),
            relative_velocity_y_mps=float(velocity[1]),
            robot_velocity_x_mps=float(robot_velocity[0]),
            robot_velocity_y_mps=float(robot_velocity[1]),
            human_velocity_x_mps=float(human_velocity[0]),
            human_velocity_y_mps=float(human_velocity[1]),
            local_density=float(normalized_density) * 3.0,
            detector_confidence=float(detector_confidence),
            distance_scale_m=float(config.distance_scale_m),
            closing_scale_mps=float(config.closing_scale_mps),
            cpa_time_scale_s=float(config.cpa_time_scale_s),
            bias=float(config.bias),
            weights=(ctypes.c_double * 5)(*map(float, config.weights)),
        )
        output = _CcaContextScoreOutput()
        error = ctypes.create_string_buffer(256)
        result = self._library.cca_context_score(
            ctypes.byref(payload), ctypes.byref(output), error, len(error)
        )
        if result != 0:
            raise ValueError(self._error(error))
        features = {
            name: float(output.features[index])
            for index, name in enumerate(CONTEXT_FEATURE_NAMES)
        }
        return features, float(output.phi)


_CPP_CONTEXT_UNSET = object()
_CPP_CONTEXT: object = _CPP_CONTEXT_UNSET


def _cpp_context_backend() -> _CppContextBackend | None:
    global _CPP_CONTEXT
    if _CPP_CONTEXT is not _CPP_CONTEXT_UNSET:
        return _CPP_CONTEXT if isinstance(_CPP_CONTEXT, _CppContextBackend) else None
    backend = os.environ.get("CCA_CONTEXT_BACKEND", "auto").strip().lower()
    if backend not in {"auto", "cpp", "python"}:
        raise ValueError("CCA_CONTEXT_BACKEND must be auto, cpp or python")
    if backend == "python":
        _CPP_CONTEXT = None
        return None
    library = cpp_transport_library()
    if library is None:
        if backend == "cpp":
            raise RuntimeError("CCA_CONTEXT_BACKEND=cpp requires the built C++ transport library")
        _CPP_CONTEXT = None
        return None
    try:
        _CPP_CONTEXT = _CppContextBackend(library)
    except (OSError, AttributeError) as error:
        if backend == "cpp":
            raise RuntimeError(f"unable to load C++ context scorer: {error}") from error
        _CPP_CONTEXT = None
    return _CPP_CONTEXT if isinstance(_CPP_CONTEXT, _CppContextBackend) else None


def _validate_config(config: ContextConfig) -> None:
    if min(
        config.distance_scale_m,
        config.closing_scale_mps,
        config.cpa_time_scale_s,
    ) <= 0.0:
        raise ValueError("context scales must be positive")
    if len(config.weights) != len(CONTEXT_FEATURE_NAMES) or not np.isfinite(
        [config.bias, *config.weights]
    ).all():
        raise ValueError("context coefficients must be finite")


def _validated_vectors(
    relative_position_xy: NDArray[np.float64],
    relative_velocity_xy: NDArray[np.float64],
    robot_velocity_xy: NDArray[np.float64],
    human_velocity_xy: NDArray[np.float64],
    normalized_density: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    vectors = tuple(
        np.asarray(value, dtype=np.float64)
        for value in (
            relative_position_xy,
            relative_velocity_xy,
            robot_velocity_xy,
            human_velocity_xy,
        )
    )
    if any(value.shape != (2,) for value in vectors):
        raise ValueError("context position and velocity inputs require shape [2]")
    if not np.isfinite(
        [*vectors[0], *vectors[1], *vectors[2], *vectors[3], normalized_density]
    ).all():
        raise ValueError("context inputs must be finite")
    return vectors


def _python_context_features(
    position: NDArray[np.float64],
    velocity: NDArray[np.float64],
    robot_velocity: NDArray[np.float64],
    human_velocity: NDArray[np.float64],
    normalized_density: float,
    config: ContextConfig,
) -> dict[str, float]:
    distance = float(np.linalg.norm(position))
    radial_speed = float(np.dot(position, velocity) / max(distance, 1.0e-9))
    closing = max(0.0, -radial_speed)
    velocity_squared = float(np.dot(velocity, velocity))
    cpa_time = max(0.0, -float(np.dot(position, velocity)) / max(velocity_squared, 1.0e-9))
    crossing_denominator = float(np.linalg.norm(robot_velocity) * np.linalg.norm(human_velocity))
    crossing = (
        0.0
        if crossing_denominator < 1.0e-9
        else abs(robot_velocity[0] * human_velocity[1] - robot_velocity[1] * human_velocity[0])
        / crossing_denominator
    )
    return {
        "proximity": max(0.0, 1.0 - distance / config.distance_scale_m),
        "closing": min(1.0, closing / config.closing_scale_mps),
        "cpa_time": float(np.exp(-cpa_time / config.cpa_time_scale_s)),
        "crossing_geometry": float(np.clip(crossing, 0.0, 1.0)),
        "density": float(np.clip(normalized_density, 0.0, 1.0)),
    }


def context_features(
    relative_position_xy: NDArray[np.float64],
    relative_velocity_xy: NDArray[np.float64],
    robot_velocity_xy: NDArray[np.float64],
    human_velocity_xy: NDArray[np.float64],
    normalized_density: float,
    config: ContextConfig = ContextConfig(),
) -> dict[str, float]:
    _validate_config(config)
    position, velocity, robot_velocity, human_velocity = _validated_vectors(
        relative_position_xy,
        relative_velocity_xy,
        robot_velocity_xy,
        human_velocity_xy,
        normalized_density,
    )
    backend = _cpp_context_backend()
    if backend is not None:
        features, _ = backend.score(
            0,
            0,
            position,
            velocity,
            robot_velocity,
            human_velocity,
            float(normalized_density),
            0.0,
            config,
        )
        return features
    return _python_context_features(
        position, velocity, robot_velocity, human_velocity, normalized_density, config
    )


def context_score(
    relative_position_xy: NDArray[np.float64],
    relative_velocity_xy: NDArray[np.float64],
    robot_velocity_xy: NDArray[np.float64],
    human_velocity_xy: NDArray[np.float64],
    normalized_density: float,
    config: ContextConfig = ContextConfig(),
) -> float:
    _validate_config(config)
    position, velocity, robot_velocity, human_velocity = _validated_vectors(
        relative_position_xy,
        relative_velocity_xy,
        robot_velocity_xy,
        human_velocity_xy,
        normalized_density,
    )
    backend = _cpp_context_backend()
    if backend is not None:
        _, phi = backend.score(
            0,
            0,
            position,
            velocity,
            robot_velocity,
            human_velocity,
            float(normalized_density),
            0.0,
            config,
        )
        return phi
    features = _python_context_features(
        position, velocity, robot_velocity, human_velocity, normalized_density, config
    )
    vector = np.fromiter((features[name] for name in CONTEXT_FEATURE_NAMES), dtype=np.float64)
    logit = config.bias + float(np.dot(config.weights, vector))
    return float(1.0 / (1.0 + np.exp(-logit)))


class ContextScorer:
    def __init__(self, config: ContextConfig = ContextConfig()) -> None:
        _validate_config(config)
        self._config = config

    @property
    def calibration_valid(self) -> bool:
        return False

    def score(
        self,
        track_id: int,
        timestamp_ns: int,
        relative_position_xy: NDArray[np.float64],
        relative_velocity_xy: NDArray[np.float64],
        local_density: float,
        detector_confidence: float,
        robot_velocity_xy: NDArray[np.float64] | None = None,
        human_velocity_xy: NDArray[np.float64] | None = None,
    ) -> ContextEvent:
        robot_velocity = (
            np.zeros(2)
            if robot_velocity_xy is None
            else np.asarray(robot_velocity_xy, dtype=np.float64)
        )
        relative_velocity = np.asarray(relative_velocity_xy, dtype=np.float64)
        human_velocity = (
            robot_velocity + relative_velocity
            if human_velocity_xy is None
            else np.asarray(human_velocity_xy, dtype=np.float64)
        )
        normalized_density = float(np.clip(max(0.0, local_density) / 3.0, 0.0, 1.0))
        position, velocity, robot_velocity, human_velocity = _validated_vectors(
            relative_position_xy,
            relative_velocity,
            robot_velocity,
            human_velocity,
            normalized_density,
        )
        backend = _cpp_context_backend()
        if backend is not None:
            features, phi = backend.score(
                track_id,
                timestamp_ns,
                position,
                velocity,
                robot_velocity,
                human_velocity,
                normalized_density,
                detector_confidence,
                self._config,
            )
        else:
            features = _python_context_features(
                position,
                velocity,
                robot_velocity,
                human_velocity,
                normalized_density,
                self._config,
            )
            vector = np.fromiter(
                (features[name] for name in CONTEXT_FEATURE_NAMES),
                dtype=np.float64,
            )
            logit = self._config.bias + float(np.dot(self._config.weights, vector))
            phi = float(1.0 / (1.0 + np.exp(-logit)))
        return ContextEvent(
            track_id=track_id,
            timestamp_ns=timestamp_ns,
            phi=phi,
            features=features,
            detector_confidence=detector_confidence,
            calibration_valid=False,
        )
