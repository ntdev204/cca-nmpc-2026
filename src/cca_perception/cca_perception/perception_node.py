"""Fuse camera person recognition with the planar LiDAR stream.

The node deliberately keeps the safety contract small and deterministic:
YOLO supplies a person observation and confidence, while LiDAR supplies the
range used by the controller.  A camera-only detection is reported in the
diagnostics stream but is not injected into the motion controller without a
matching range measurement.
"""

from __future__ import annotations

import math
import time
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np
import rclpy
from geometry_msgs.msg import Pose, PoseArray
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan
from std_msgs.msg import Float64, Float64MultiArray


def _stamp_ns(message: Any) -> int:
    stamp = message.header.stamp
    return int(stamp.sec) * 1_000_000_000 + int(stamp.nanosec)


def _yaw_from_quaternion(quaternion: Any) -> float:
    return math.atan2(
        2.0 * (quaternion.w * quaternion.z + quaternion.x * quaternion.y),
        1.0 - 2.0 * (quaternion.y * quaternion.y + quaternion.z * quaternion.z),
    )


def _tensor_numpy(value: Any) -> np.ndarray:
    if value is None:
        return np.empty((0,), dtype=np.float32)
    detach = getattr(value, "detach", None)
    if callable(detach):
        value = detach()
    cpu = getattr(value, "cpu", None)
    if callable(cpu):
        value = cpu()
    numpy = getattr(value, "numpy", None)
    if callable(numpy):
        value = numpy()
    return np.asarray(value)


class CcaPerceptionNode(Node):
    """Publish camera/LiDAR context in the format consumed by CCA-NMPC."""

    def __init__(self) -> None:
        super().__init__("cca_perception_node")
        self.image_topic = str(
            self.declare_parameter("image_topic", "/camera/color/image_raw").value
        )
        self.scan_topic = str(self.declare_parameter("scan_topic", "/scan").value)
        self.odom_topic = str(
            self.declare_parameter("odom_topic", "/odometry/raw").value
        )
        self.context_topic = str(
            self.declare_parameter("context_topic", "/cca/context_score").value
        )
        self.context_prediction_topic = str(
            self.declare_parameter(
                "context_prediction_topic", "/cca/context_prediction"
            ).value
        )
        self.people_topic = str(
            self.declare_parameter("people_topic", "/cca/perception/people").value
        )
        self.diagnostics_topic = str(
            self.declare_parameter(
                "diagnostics_topic", "/cca/perception_diagnostics"
            ).value
        )
        self.model_path = str(
            self.declare_parameter(
                "model_path", "/home/rai/cca-nmpc-ros2/models/yolo26s-pose.pt"
            ).value
        )
        self.device = str(self.declare_parameter("device", "auto").value)
        self.image_size = int(self.declare_parameter("image_size", 640).value)
        self.confidence = float(
            self.declare_parameter("confidence", 0.45).value
        )
        self.inference_rate_hz = float(
            self.declare_parameter("inference_rate_hz", 5.0).value
        )
        self.horizon = int(self.declare_parameter("horizon", 6).value)
        self.period_s = float(self.declare_parameter("period_s", 0.05).value)
        self.camera_fov_rad = float(
            self.declare_parameter("camera_horizontal_fov_rad", 1.0472).value
        )
        self.camera_yaw_offset_rad = float(
            self.declare_parameter("camera_yaw_offset_rad", 0.0).value
        )
        self.lidar_x_m = float(self.declare_parameter("lidar_x_m", 0.0).value)
        self.lidar_y_m = float(self.declare_parameter("lidar_y_m", 0.0).value)
        self.lidar_yaw_rad = float(
            self.declare_parameter("lidar_yaw_rad", 0.0).value
        )
        self.lidar_association_window_rad = float(
            self.declare_parameter("lidar_association_window_rad", 0.08).value
        )
        self.person_max_range_m = float(
            self.declare_parameter("person_max_range_m", 4.0).value
        )
        if (
            self.horizon <= 0
            or self.period_s <= 0.0
            or self.inference_rate_hz <= 0.0
            or self.camera_fov_rad <= 0.0
            or self.person_max_range_m <= 0.0
        ):
            raise ValueError("cca perception parameters are invalid")

        self._lock = Lock()
        self._latest_image: np.ndarray | None = None
        self._latest_image_stamp_ns = 0
        self._latest_scan: tuple[int, float, float, float, float, np.ndarray] | None = None
        self._latest_odom: tuple[int, float, float, float, float, float, float] | None = None
        self._model: Any | None = None
        self._model_status = "not_loaded"
        self._last_inference_error = ""
        self._last_inference_error_time = 0.0

        self._load_model()

        self.image_sub = self.create_subscription(
            Image, self.image_topic, self._image_callback, 10
        )
        self.scan_sub = self.create_subscription(
            LaserScan, self.scan_topic, self._scan_callback, 10
        )
        self.odom_sub = self.create_subscription(
            Odometry, self.odom_topic, self._odom_callback, 10
        )
        self.context_pub = self.create_publisher(Float64, self.context_topic, 10)
        self.context_prediction_pub = self.create_publisher(
            Float64MultiArray, self.context_prediction_topic, 10
        )
        self.people_pub = self.create_publisher(PoseArray, self.people_topic, 10)
        self.diagnostics_pub = self.create_publisher(
            Float64MultiArray, self.diagnostics_topic, 10
        )
        self.timer = self.create_timer(
            1.0 / self.inference_rate_hz, self._inference_step
        )

    def _load_model(self) -> None:
        path = Path(self.model_path).expanduser()
        if not path.is_file():
            self._model_status = "missing"
            self.get_logger().error(
                "YOLO model is missing at %s; camera is subscribed but recognition is disabled",
                path,
            )
            return
        try:
            from ultralytics import YOLO

            self._model = YOLO(str(path))
            self._model_status = "loaded"
            self.get_logger().info(
                "Loaded camera model %s on device=%s", path, self.device
            )
        except Exception as error:  # pragma: no cover - depends on Jetson runtime
            self._model_status = "load_error"
            self.get_logger().error("Could not load YOLO model: %s", error)

    @staticmethod
    def _decode_image(message: Image) -> np.ndarray | None:
        width = int(message.width)
        height = int(message.height)
        if width <= 0 or height <= 0:
            return None
        encoding = str(message.encoding).lower()
        if encoding in {"mono8", "8uc1"}:
            channels = 1
        elif encoding in {"rgb8", "bgr8", "rgba8", "bgra8", "8uc3", "8uc4"}:
            channels = 4 if encoding in {"rgba8", "bgra8", "8uc4"} else 3
        else:
            return None
        step = int(message.step) or width * channels
        raw = np.frombuffer(message.data, dtype=np.uint8)
        if raw.size < height * step:
            return None
        rows = raw[: height * step].reshape(height, step)
        image = rows[:, : width * channels].reshape(height, width, channels)
        if channels == 1:
            return np.repeat(image, 3, axis=2)
        if encoding in {"rgb8", "rgba8"}:
            image = image[:, :, ::-1]
        return np.ascontiguousarray(image[:, :, :3])

    def _image_callback(self, message: Image) -> None:
        image = self._decode_image(message)
        if image is None:
            return
        with self._lock:
            self._latest_image = image
            self._latest_image_stamp_ns = _stamp_ns(message)

    def _scan_callback(self, message: LaserScan) -> None:
        ranges = np.asarray(message.ranges, dtype=np.float32).copy()
        with self._lock:
            self._latest_scan = (
                _stamp_ns(message),
                float(message.angle_min),
                float(message.angle_increment),
                float(message.range_min),
                float(message.range_max),
                ranges,
            )

    def _odom_callback(self, message: Odometry) -> None:
        pose = message.pose.pose
        twist = message.twist.twist
        with self._lock:
            self._latest_odom = (
                _stamp_ns(message),
                float(pose.position.x),
                float(pose.position.y),
                _yaw_from_quaternion(pose.orientation),
                float(twist.linear.x),
                float(twist.linear.y),
                float(twist.angular.z),
            )

    @staticmethod
    def _angle_delta(first: np.ndarray, second: float) -> np.ndarray:
        return np.arctan2(np.sin(first - second), np.cos(first - second))

    def _range_for_angle(
        self,
        scan: tuple[int, float, float, float, float, np.ndarray],
        base_angle: float,
    ) -> float | None:
        _, angle_min, angle_increment, range_min, range_max, ranges = scan
        if ranges.size == 0 or abs(angle_increment) <= 1.0e-9:
            return None
        scan_angle = base_angle - self.lidar_yaw_rad
        indexes = np.arange(ranges.size, dtype=np.float32)
        angles = angle_min + indexes * angle_increment
        delta = self._angle_delta(angles, scan_angle)
        window = max(self.lidar_association_window_rad, abs(angle_increment) * 2.0)
        valid = (
            (np.abs(delta) <= window)
            & np.isfinite(ranges)
            & (ranges >= max(0.05, range_min))
            & (ranges <= min(self.person_max_range_m, range_max))
        )
        values = ranges[valid]
        if values.size == 0:
            return None
        # The lower quartile is more stable than the single nearest beam and
        # still keeps a person in front of a farther wall observable.
        return float(np.percentile(values, 25.0))

    def _detect(self, image: np.ndarray) -> list[tuple[float, float, float]]:
        if self._model is None:
            return []
        kwargs: dict[str, Any] = {
            "imgsz": self.image_size,
            "conf": self.confidence,
            "classes": [0],
            "max_det": 12,
            "verbose": False,
        }
        if self.device and self.device != "auto":
            kwargs["device"] = self.device
        results = self._model.predict(image, **kwargs)
        if not results:
            return []
        boxes = getattr(results[0], "boxes", None)
        if boxes is None:
            return []
        xyxy = _tensor_numpy(getattr(boxes, "xyxy", None))
        confidence = _tensor_numpy(getattr(boxes, "conf", None)).reshape(-1)
        classes = _tensor_numpy(getattr(boxes, "cls", None)).reshape(-1)
        detections: list[tuple[float, float, float]] = []
        for index, box in enumerate(xyxy):
            if len(box) < 4 or index >= len(confidence):
                continue
            if index < len(classes) and int(round(float(classes[index]))) != 0:
                continue
            if float(confidence[index]) < self.confidence:
                continue
            detections.append(
                (
                    float((float(box[0]) + float(box[2])) * 0.5),
                    float((float(box[1]) + float(box[3])) * 0.5),
                    float(confidence[index]),
                )
            )
        return detections

    def _publish_empty_context(
        self,
        odom: tuple[int, float, float, float, float, float, float] | None,
        detection_count: int,
        scan_age_s: float,
        image_age_s: float,
    ) -> None:
        context = Float64()
        context.data = 0.0
        self.context_pub.publish(context)
        nominal_x = float(odom[1]) if odom is not None else 0.0
        nominal_y = float(odom[2]) if odom is not None else 0.0
        mean = [1000.0, 1000.0] * self.horizon
        scores = [0.0] * self.horizon
        covariance = [4.0, 0.0, 0.0, 4.0] * self.horizon
        nominal = []
        for step in range(self.horizon):
            nominal.extend([nominal_x, nominal_y])
        prediction = Float64MultiArray()
        prediction.data = mean + scores + covariance + nominal
        self.context_prediction_pub.publish(prediction)
        self._publish_diagnostics(
            detection_count,
            0,
            0.0,
            scan_age_s,
            image_age_s,
        )

    def _publish_diagnostics(
        self,
        detection_count: int,
        fused_count: int,
        score: float,
        scan_age_s: float,
        image_age_s: float,
    ) -> None:
        message = Float64MultiArray()
        message.data = [
            1.0 if self._model_status == "loaded" else 0.0,
            float(detection_count),
            float(fused_count),
            float(score),
            float(scan_age_s) if math.isfinite(scan_age_s) else -1.0,
            float(image_age_s) if math.isfinite(image_age_s) else -1.0,
        ]
        self.diagnostics_pub.publish(message)

    def _inference_step(self) -> None:
        with self._lock:
            image = None if self._latest_image is None else self._latest_image.copy()
            image_stamp_ns = self._latest_image_stamp_ns
            scan = self._latest_scan
            odom = self._latest_odom
        now_ns = self.get_clock().now().nanoseconds
        scan_age_s = (
            max(0.0, (now_ns - scan[0]) * 1.0e-9)
            if scan is not None and scan[0] > 0
            else math.inf
        )
        image_age_s = (
            max(0.0, (now_ns - image_stamp_ns) * 1.0e-9)
            if image_stamp_ns > 0
            else math.inf
        )
        if image is None or scan is None or odom is None:
            self._publish_empty_context(odom, 0, scan_age_s, image_age_s)
            return

        if self._model is None:
            self._publish_empty_context(odom, 0, scan_age_s, image_age_s)
            return

        try:
            detections = self._detect(image)
        except Exception as error:  # pragma: no cover - depends on model runtime
            message = str(error)
            if message != self._last_inference_error or time.monotonic() - self._last_inference_error_time > 5.0:
                self.get_logger().error("YOLO inference failed: %s", error)
                self._last_inference_error = message
                self._last_inference_error_time = time.monotonic()
            self._publish_empty_context(odom, 0, scan_age_s, image_age_s)
            return

        fused: list[tuple[float, float, float]] = []
        image_height, image_width = image.shape[:2]
        for center_x, _, detection_confidence in detections:
            normalized = (center_x - image_width * 0.5) / max(image_width * 0.5, 1.0)
            base_angle = self.camera_yaw_offset_rad + normalized * self.camera_fov_rad * 0.5
            distance = self._range_for_angle(scan, base_angle)
            if distance is None:
                continue
            lidar_angle = base_angle - self.lidar_yaw_rad
            sensor_x = self.lidar_x_m + distance * math.cos(lidar_angle)
            sensor_y = self.lidar_y_m + distance * math.sin(lidar_angle)
            base_x = math.cos(self.lidar_yaw_rad) * sensor_x - math.sin(self.lidar_yaw_rad) * sensor_y
            base_y = math.sin(self.lidar_yaw_rad) * sensor_x + math.cos(self.lidar_yaw_rad) * sensor_y
            world_x = odom[1] + math.cos(odom[3]) * base_x - math.sin(odom[3]) * base_y
            world_y = odom[2] + math.sin(odom[3]) * base_x + math.cos(odom[3]) * base_y
            fused.append((world_x, world_y, detection_confidence))

        if not fused:
            self._publish_empty_context(odom, len(detections), scan_age_s, image_age_s)
            return

        # Only the most relevant fused person enters the compact NMPC context
        # vector.  The full fused set remains visible on /cca/perception/people.
        distances = [math.hypot(item[0] - odom[1], item[1] - odom[2]) for item in fused]
        selected = min(range(len(fused)), key=lambda index: distances[index])
        person_x, person_y, person_confidence = fused[selected]
        person_distance = distances[selected]
        score = float(
            np.clip(
                person_confidence
                * math.exp(-max(0.0, person_distance - 0.30) / 1.50),
                0.0,
                1.0,
            )
        )

        people = PoseArray()
        people.header.stamp = self.get_clock().now().to_msg()
        people.header.frame_id = "odom"
        for x, y, _ in fused:
            pose = Pose()
            pose.position.x = x
            pose.position.y = y
            pose.orientation.w = 1.0
            people.poses.append(pose)
        self.people_pub.publish(people)

        context = Float64()
        context.data = score
        self.context_pub.publish(context)
        mean: list[float] = []
        scores: list[float] = []
        covariance: list[float] = []
        nominal: list[float] = []
        for step in range(self.horizon):
            seconds = (step + 1) * self.period_s
            mean.extend([person_x, person_y])
            scores.append(score)
            variance = max(0.04, min(0.50, 0.04 + 0.04 * person_distance))
            covariance.extend([variance, 0.0, 0.0, variance])
            nominal_x = odom[1] + seconds * (
                math.cos(odom[3]) * odom[4] - math.sin(odom[3]) * odom[5]
            )
            nominal_y = odom[2] + seconds * (
                math.sin(odom[3]) * odom[4] + math.cos(odom[3]) * odom[5]
            )
            nominal.extend([nominal_x, nominal_y])
        prediction = Float64MultiArray()
        prediction.data = mean + scores + covariance + nominal
        self.context_prediction_pub.publish(prediction)
        self._publish_diagnostics(
            len(detections), len(fused), score, scan_age_s, image_age_s
        )


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = CcaPerceptionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
