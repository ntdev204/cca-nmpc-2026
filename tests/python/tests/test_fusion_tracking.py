import numpy as np
import pytest

from ai.detection import Detection2D
from ai.fusion import CameraLidarFusion, FusionConfig, RigidTransform
from ai.contracts import HumanObservation
from ai.tracking import TrackManager, TrackerConfig


IDENTITY = RigidTransform(np.eye(3), np.zeros(3))


def _observation(timestamp_ns: int, x: float) -> HumanObservation:
    return HumanObservation(
        timestamp_ns=timestamp_ns,
        frame_id="odom",
        position_xy=np.array([x, 0.0]),
        covariance_xy=np.eye(2) * 0.01,
        detector_confidence=0.8,
        lidar_point_count=4,
    )


def test_fusion_requires_synchronized_lidar_support() -> None:
    fusion = CameraLidarFusion(
        FusionConfig(100.0, 100.0, 320.0, 240.0, minimum_points=3),
        IDENTITY,
    )
    detection = Detection2D(100, (300.0, 220.0, 340.0, 260.0), 0.9, 0)
    points = np.array(
        [[0.00, 0.00, 2.0], [0.02, 0.00, 2.0], [-0.02, 0.00, 2.0]]
    )
    observations = fusion.fuse((detection,), points, 100, IDENTITY, "odom")
    assert len(observations) == 1
    assert observations[0].lidar_point_count == 3
    assert fusion.fuse((detection,), points, 60_000_101, IDENTITY, "odom") == ()


def test_tracker_preserves_id_estimates_velocity_and_expires() -> None:
    tracker = TrackManager(
        TrackerConfig(association_gate_m=1.0, maximum_age_ns=150_000_000)
    )
    first = tracker.update((_observation(0, 0.0),), 0)
    second = tracker.update((_observation(100_000_000, 0.1),), 100_000_000)
    assert first[0].track_id == second[0].track_id
    assert second[0].velocity_xy[0] > 0.0
    assert tracker.update((), 300_000_000) == ()


def test_observation_rejects_asymmetric_covariance() -> None:
    with pytest.raises(ValueError, match="symmetric"):
        HumanObservation(
            0,
            "odom",
            np.zeros(2),
            np.array([[1.0, 0.5], [0.0, 1.0]]),
            0.8,
            3,
        )
