import json

import numpy as np
import pytest

from shared import sha256_file
from ai.detection import PoseDetection2D, validate_engine_manifest


def test_engine_manifest_rejects_non_engine_and_hash_mismatch(tmp_path) -> None:
    weights = tmp_path / "model.pt"
    weights.write_bytes(b"weights")
    manifest = tmp_path / "model.manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="only a TensorRT"):
        validate_engine_manifest(weights, manifest)

    engine = tmp_path / "model.engine"
    engine.write_bytes(b"engine")
    payload = {
        "schema": "cca-yolo26s-pose-engine-v1",
        "model": "yolo26s-pose",
        "task": "pose",
        "trained": False,
        "engineSha256": "0" * 64,
        "buildPlatform": {"machine": "aarch64"},
        "export": {"imageSize": 640},
        "personClassId": 0,
        "keypointCount": 17,
        "smokeInferencePassed": True,
    }
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        validate_engine_manifest(engine, manifest)
    payload["engineSha256"] = sha256_file(engine)
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    assert validate_engine_manifest(engine, manifest)["trained"] is False


def test_pose_detection_requires_seventeen_joints_and_explicit_mask() -> None:
    valid = np.ones((17,), dtype=bool)
    detection = PoseDetection2D(
        timestamp_ns=100,
        xyxy=(10.0, 20.0, 40.0, 80.0),
        confidence=0.9,
        class_id=0,
        keypoints_xy=np.ones((17, 2), dtype=np.float64),
        keypoint_confidence=np.full(17, 0.8, dtype=np.float64),
        keypoint_valid=valid,
        model_artifact_id="model-yolo26s-pose",
        model_sha256="a" * 64,
        preprocessing_version="rgb-bgr-v1",
    )
    assert detection.keypoints_xy.shape == (17, 2)
    assert detection.keypoint_valid.all()
    with pytest.raises(ValueError, match="17"):
        PoseDetection2D(
            timestamp_ns=100,
            xyxy=(10.0, 20.0, 40.0, 80.0),
            confidence=0.9,
            class_id=0,
            keypoints_xy=np.ones((16, 2), dtype=np.float64),
            keypoint_confidence=np.full(16, 0.8, dtype=np.float64),
            keypoint_valid=np.ones(16, dtype=bool),
            model_artifact_id="model-yolo26s-pose",
            model_sha256="a" * 64,
            preprocessing_version="rgb-bgr-v1",
        )
