from __future__ import annotations

import json
import platform
from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np
from numpy.typing import NDArray

from shared import sha256_file


POSE_ENGINE_SCHEMA = "cca-yolo26s-pose-engine-v1"
POSE_MODEL_NAME = "yolo26s-pose"
POSE_KEYPOINT_COUNT = 17


@dataclass(frozen=True)
class Detection2D:
    timestamp_ns: int
    xyxy: tuple[float, float, float, float]
    confidence: float
    class_id: int

    def __post_init__(self) -> None:
        x1, y1, x2, y2 = self.xyxy
        if self.timestamp_ns < 0 or x2 <= x1 or y2 <= y1:
            raise ValueError("invalid detection timestamp or box")
        if not 0.0 <= self.confidence <= 1.0 or self.class_id < 0:
            raise ValueError("invalid detection confidence or class")


@dataclass(frozen=True)
class PoseDetection2D(Detection2D):
    """A person box plus the pose output kept in image coordinates.

    The fusion layer deliberately consumes the base ``Detection2D`` contract;
    pose is carried as optional measurement metadata for overlays and later
    feature extraction.  Invalid joints are represented by ``keypoint_valid``
    rather than by a zero coordinate being treated as an observation.
    """

    keypoints_xy: NDArray[np.float64]
    keypoint_confidence: NDArray[np.float64]
    keypoint_valid: NDArray[np.bool_]
    model_artifact_id: str
    model_sha256: str
    preprocessing_version: str

    def __post_init__(self) -> None:
        Detection2D.__post_init__(self)
        xy = np.asarray(self.keypoints_xy, dtype=np.float64)
        confidence = np.asarray(self.keypoint_confidence, dtype=np.float64)
        valid = np.asarray(self.keypoint_valid, dtype=bool)
        if xy.shape != (POSE_KEYPOINT_COUNT, 2):
            raise ValueError("pose keypoints must have shape [17, 2]")
        if confidence.shape != (POSE_KEYPOINT_COUNT,) or valid.shape != (
            POSE_KEYPOINT_COUNT,
        ):
            raise ValueError("pose confidence and validity must have length 17")
        if not np.isfinite(xy).all() or not np.isfinite(confidence).all():
            raise ValueError("pose keypoints and confidence must be finite")
        if np.any((confidence < 0.0) | (confidence > 1.0)):
            raise ValueError("pose keypoint confidence must lie in [0, 1]")
        if not self.model_artifact_id or not self.preprocessing_version:
            raise ValueError("pose model identity and preprocessing are required")
        if re.fullmatch(r"[A-Fa-f0-9]{64}", self.model_sha256) is None:
            raise ValueError("pose model hash must be a SHA-256 digest")
        object.__setattr__(self, "keypoints_xy", xy)
        object.__setattr__(self, "keypoint_confidence", confidence)
        object.__setattr__(self, "keypoint_valid", valid)


class YoloEngineDetector:
    """Strict TensorRT-only YOLO26s-pose adapter; training APIs are not exposed."""

    def __init__(self, engine_path: Path, manifest_path: Path) -> None:
        self._manifest = validate_engine_manifest(engine_path, manifest_path)
        validate_runtime_fingerprint(self._manifest)
        from ultralytics import YOLO

        self._model = YOLO(str(engine_path), task="pose")

    def detect(
        self, image_bgr: NDArray[np.uint8], timestamp_ns: int
    ) -> tuple[PoseDetection2D, ...]:
        image = np.asarray(image_bgr)
        if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("image_bgr must be uint8 [height, width, 3]")
        if min(image.shape[:2]) < 1 or timestamp_ns < 0:
            raise ValueError("image dimensions and timestamp must be valid")
        results = self._model.predict(
            source=image,
            imgsz=int(self._manifest["export"]["imageSize"]),
            device=0,
            verbose=False,
        )
        person_id = int(self._manifest["personClassId"])
        keypoint_threshold = float(
            self._manifest.get("keypointConfidenceThreshold", 0.25)
        )
        result = results[0]
        if result.boxes is None or result.keypoints is None:
            return ()
        box_rows = result.boxes.data.detach().cpu().numpy()
        keypoint_xy = result.keypoints.xy.detach().cpu().numpy()
        if result.keypoints.conf is not None:
            keypoint_confidence = result.keypoints.conf.detach().cpu().numpy()
        else:
            keypoint_data = result.keypoints.data.detach().cpu().numpy()
            keypoint_confidence = keypoint_data[..., 2]
        if (
            keypoint_xy.ndim != 3
            or keypoint_xy.shape[1:] != (POSE_KEYPOINT_COUNT, 2)
            or keypoint_confidence.shape != keypoint_xy.shape[:2]
            or len(box_rows) != len(keypoint_xy)
        ):
            raise RuntimeError("YOLO26s-pose output does not match the 17-joint contract")
        detections = []
        for index, row in enumerate(box_rows):
            class_id = int(row[5])
            if class_id == person_id:
                xy = np.asarray(keypoint_xy[index], dtype=np.float64)
                confidence = np.asarray(keypoint_confidence[index], dtype=np.float64)
                valid = np.isfinite(xy).all(axis=1) & (
                    confidence >= keypoint_threshold
                )
                xy = np.where(np.isfinite(xy), xy, 0.0)
                detections.append(
                    PoseDetection2D(
                        timestamp_ns=timestamp_ns,
                        xyxy=tuple(float(value) for value in row[:4]),
                        confidence=float(row[4]),
                        class_id=class_id,
                        keypoints_xy=xy,
                        keypoint_confidence=np.clip(confidence, 0.0, 1.0),
                        keypoint_valid=valid,
                        model_artifact_id=str(
                            self._manifest.get("artifactId", POSE_MODEL_NAME)
                        ),
                        model_sha256=str(self._manifest["engineSha256"]),
                        preprocessing_version=str(
                            self._manifest.get("preprocessingVersion", "rgb-bgr-v1")
                        ),
                    )
                )
        return tuple(detections)


def validate_engine_manifest(
    engine_path: Path, manifest_path: Path
) -> dict[str, object]:
    if engine_path.suffix.lower() != ".engine":
        raise ValueError("YOLO runtime accepts only a TensorRT .engine file")
    if not engine_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("engine and manifest must both exist")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != POSE_ENGINE_SCHEMA:
        raise ValueError("unsupported YOLO engine manifest schema")
    if (
        manifest.get("model") != POSE_MODEL_NAME
        or manifest.get("task") != "pose"
        or manifest.get("trained") is not False
    ):
        raise ValueError("manifest must describe inference-only yolo26s-pose")
    if manifest.get("engineSha256") != sha256_file(engine_path):
        raise ValueError("YOLO engine hash does not match manifest")
    build = manifest.get("buildPlatform")
    if not isinstance(build, dict) or build.get("machine") not in {
        "aarch64",
        "arm64",
    }:
        raise ValueError("engine was not built on an ARM64 Jetson target")
    export = manifest.get("export")
    if (
        not isinstance(export, dict)
        or int(export.get("imageSize", 0)) < 32
        or manifest.get("personClassId") != 0
        or manifest.get("keypointCount") != POSE_KEYPOINT_COUNT
        or manifest.get("smokeInferencePassed") is not True
    ):
        raise ValueError("engine manifest lacks locked export/smoke metadata")
    return manifest


def validate_runtime_fingerprint(manifest: dict[str, object]) -> None:
    import tensorrt
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable for the TensorRT engine")
    build = manifest["buildPlatform"]
    if not isinstance(build, dict):
        raise ValueError("invalid engine build platform")
    properties = torch.cuda.get_device_properties(0)
    runtime = {
        "machine": platform.machine().lower(),
        "gpu": torch.cuda.get_device_name(0),
        "computeCapability": f"{properties.major}.{properties.minor}",
        "tensorrt": tensorrt.__version__,
    }
    for key, value in runtime.items():
        if build.get(key) != value:
            raise RuntimeError(f"TensorRT runtime fingerprint mismatch: {key}")
    if manifest.get("smokeInferencePassed") is not True:
        raise RuntimeError("engine manifest lacks a passing target smoke inference")
