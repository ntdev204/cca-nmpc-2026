from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .detection import Detection2D
from .contracts import HumanObservation
from .tracking import assign_projected_points


@dataclass(frozen=True)
class RigidTransform:
    rotation: NDArray[np.float64]
    translation: NDArray[np.float64]

    def __post_init__(self) -> None:
        rotation = np.asarray(self.rotation, dtype=np.float64)
        translation = np.asarray(self.translation, dtype=np.float64)
        if rotation.shape != (3, 3) or translation.shape != (3,):
            raise ValueError("rigid transform requires 3x3 rotation and 3-vector")
        if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-6):
            raise ValueError("rotation must be orthonormal")
        if not np.isclose(np.linalg.det(rotation), 1.0, atol=1e-6):
            raise ValueError("rotation determinant must be +1")
        object.__setattr__(self, "rotation", rotation)
        object.__setattr__(self, "translation", translation)

    def apply(self, points: NDArray[np.float64]) -> NDArray[np.float64]:
        values = np.asarray(points, dtype=np.float64)
        if values.ndim != 2 or values.shape[1] != 3:
            raise ValueError("transform input must have shape [point, 3]")
        if not np.isfinite(values).all():
            raise ValueError("transform input must be finite")
        return values @ self.rotation.T + self.translation


@dataclass(frozen=True)
class FusionConfig:
    fx: float
    fy: float
    cx: float
    cy: float
    max_sync_ns: int = 50_000_000
    minimum_points: int = 3
    minimum_depth_m: float = 0.15
    maximum_depth_m: float = 20.0
    covariance_floor_m2: float = 4e-4


class CameraLidarFusion:
    def __init__(
        self,
        config: FusionConfig,
        camera_from_lidar: RigidTransform,
    ) -> None:
        if min(config.fx, config.fy) <= 0.0 or config.minimum_points < 1:
            raise ValueError("invalid fusion calibration/configuration")
        self._config = config
        self._camera_from_lidar = camera_from_lidar

    def fuse(
        self,
        detections: tuple[Detection2D, ...],
        lidar_xyz: NDArray[np.float64],
        lidar_timestamp_ns: int,
        tracking_from_lidar: RigidTransform,
        tracking_frame_id: str,
    ) -> tuple[HumanObservation, ...]:
        points = np.asarray(lidar_xyz, dtype=np.float64)
        if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
            raise ValueError("lidar_xyz must be finite [point, 3]")
        if not detections:
            return ()
        timestamp = detections[0].timestamp_ns
        if any(item.timestamp_ns != timestamp for item in detections):
            raise ValueError("all detections must share one camera timestamp")
        if abs(timestamp - lidar_timestamp_ns) > self._config.max_sync_ns:
            return ()
        camera_points = self._camera_from_lidar.apply(points)
        depth = camera_points[:, 2]
        valid = (depth >= self._config.minimum_depth_m) & (
            depth <= self._config.maximum_depth_m
        )
        pixel = np.full((len(points), 2), np.nan, dtype=np.float64)
        pixel[valid, 0] = (
            self._config.fx * camera_points[valid, 0] / depth[valid]
            + self._config.cx
        )
        pixel[valid, 1] = (
            self._config.fy * camera_points[valid, 1] / depth[valid]
            + self._config.cy
        )
        assignments = assign_projected_points(pixel, valid, detections)
        tracking_points = tracking_from_lidar.apply(points)
        observations = []
        for index, detection in enumerate(detections):
            selected = tracking_points[assignments == index, :2]
            if len(selected) < self._config.minimum_points:
                continue
            center = np.median(selected, axis=0)
            residual = selected - center
            covariance = residual.T @ residual / max(len(selected) - 1, 1)
            covariance += np.eye(2) * self._config.covariance_floor_m2
            observations.append(
                HumanObservation(
                    timestamp_ns=timestamp,
                    frame_id=tracking_frame_id,
                    position_xy=center,
                    covariance_xy=covariance,
                    detector_confidence=detection.confidence,
                    lidar_point_count=len(selected),
                )
            )
        return tuple(observations)
