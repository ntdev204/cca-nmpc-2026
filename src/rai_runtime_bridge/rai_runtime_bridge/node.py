from __future__ import annotations

import base64
import copy
from datetime import datetime
import math
from pathlib import Path as FilePath
import re
import threading
import time
import unicodedata
from typing import Any

import rclpy
from slam_toolbox.srv import Pause, SaveMap
from std_srvs.srv import Trigger
import tf2_ros
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import OccupancyGrid, Odometry, Path
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)
from rclpy.time import Time
from sensor_msgs.msg import Image, Imu, LaserScan
from std_msgs.msg import Bool, Empty, Float32, Float64, Float64MultiArray


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


class WebBridgeNode(Node):
    """Thread-safe ROS facade used by the HTTP and WebRTC endpoints.

    This node deliberately owns no process manager and does not open a raw
    socket. The bringup launch owns the robot, sensors and SLAM processes; the
    bridge only observes their ROS topics and publishes the control contracts.
    """

    def __init__(self) -> None:
        super().__init__("rai_runtime_bridge")
        self._lock = threading.RLock()

        self.manual_cmd_vel_topic = str(
            self.declare_parameter("manual_cmd_vel_topic", "/manual_cmd_vel").value
        )
        self.odom_topic = str(
            self.declare_parameter("odom_topic", "/odometry/raw").value
        )
        self.scan_topic = str(self.declare_parameter("scan_topic", "/scan").value)
        self.map_topic = str(self.declare_parameter("map_topic", "/map").value)
        self.camera_topic = str(
            self.declare_parameter(
                "camera_topic", "/camera/color/image_raw"
            ).value
        )
        self.global_path_topic = str(
            self.declare_parameter("global_path_topic", "/cca/global_path").value
        )
        self.goal_topic = str(
            self.declare_parameter("goal_topic", "/goal_pose").value
        )
        self.cancel_topic = str(
            self.declare_parameter("cancel_topic", "/navigation/cancel").value
        )
        self.slam_pause_service = str(
            self.declare_parameter(
                "slam_pause_service", "/slam_toolbox/pause_new_measurements"
            ).value
        )
        self.slam_start_service = str(
            self.declare_parameter("slam_start_service", "/slam_manager/start").value
        )
        self.slam_stop_service = str(
            self.declare_parameter("slam_stop_service", "/slam_manager/stop").value
        )
        self.slam_reset_service = str(
            self.declare_parameter("slam_reset_service", "/slam_manager/reset").value
        )
        self.slam_enabled = _as_bool(
            self.declare_parameter("slam_enabled", True).value
        )
        self.slam_save_service = str(
            self.declare_parameter("slam_save_service", "/slam_toolbox/save_map").value
        )
        self.map_save_root = FilePath(
            str(
                self.declare_parameter(
                    "map_save_root", "/home/rai/cca-nmpc-ros2/maps"
                ).value
            )
        ).expanduser()
        self.map_service_timeout_s = float(
            self.declare_parameter("map_service_timeout_s", 2.5).value
        )
        if self.map_service_timeout_s <= 0.0:
            raise ValueError("map_service_timeout_s must be positive")
        self.odom_frame = str(self.declare_parameter("odom_frame", "odom").value)
        self.map_frame = str(self.declare_parameter("map_frame", "map").value)
        self.control_frame = str(
            self.declare_parameter("control_frame", "base_link").value
        )
        self.odom_reset_service = str(
            self.declare_parameter("odom_reset_service", "/odometry/reset").value
        )
        self.watchdog_timeout_s = float(
            self.declare_parameter("cmd_watchdog_timeout_s", 0.75).value
        )
        if self.watchdog_timeout_s <= 0.0:
            raise ValueError("cmd_watchdog_timeout_s must be positive")
        self.manual_republish_hz = float(
            self.declare_parameter("manual_republish_hz", 20.0).value
        )
        if self.manual_republish_hz <= 0.0:
            raise ValueError("manual_republish_hz must be positive")

        self._telemetry: dict[str, Any] = {
            "odom": {
                "x": 0.0,
                "y": 0.0,
                "theta": 0.0,
                "linear_x": 0.0,
                "linear_y": 0.0,
                "angular_z": 0.0,
            },
            "battery": {"voltage": 0.0, "percentage": 0.0},
            "charging": False,
            "hardware_connected": False,
            "context": {
                "legacy_context": "OZ",
                "phi_h": 0.0,
                "d_h": None,
                "d_safe": 0.5,
                "vx_max": 0.45,
                "vy_max": 0.35,
                "omega_max": 1.0,
                "occlusion_flag": False,
                "navigation_mode": "idle",
                "human_count": 0,
                "tracking_quality": 0.0,
            },
            "humans": [],
            "solver": {},
            "lidar_rate_hz": 0.0,
            "camera_rate_hz": 0.0,
            "lidar_clearance": {"left": 5.0, "right": 5.0},
            "map_pose": None,
            "camera_capture_t_ns": None,
            "last_update": 0.0,
        }

        self._latest_map: dict[str, Any] | None = None
        self._latest_map_signature: tuple[Any, ...] | None = None
        self._latest_camera_frame: Image | None = None
        self._camera_sequence = 0
        self._camera_clients = 0
        self._camera_condition = threading.Condition(self._lock)
        self._last_scan_monotonic: float | None = None
        self._last_camera_monotonic: float | None = None
        self._last_command_monotonic = time.monotonic()
        self._last_command = (0.0, 0.0, 0.0)
        self._navigation_active = False
        self._slam_paused = _as_bool(
            self.declare_parameter("initial_slam_paused", False).value
        )
        self._map_control_lock = threading.Lock()
        self._last_map_save: dict[str, Any] | None = None
        self._map_ignore_before_ns = 0

        self._sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self._reliable_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self._map_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self._cmd_pub = self.create_publisher(
            Twist, self.manual_cmd_vel_topic, self._reliable_qos
        )
        self._path_pub = self.create_publisher(
            Path, self.global_path_topic, self._reliable_qos
        )
        self._goal_pub = self.create_publisher(
            PoseStamped, self.goal_topic, self._reliable_qos
        )
        self._cancel_pub = self.create_publisher(
            Empty, self.cancel_topic, self._reliable_qos
        )
        self._slam_pause_client = self.create_client(Pause, self.slam_pause_service)
        self._slam_start_client = self.create_client(Trigger, self.slam_start_service)
        self._slam_stop_client = self.create_client(Trigger, self.slam_stop_service)
        self._slam_reset_client = self.create_client(Trigger, self.slam_reset_service)
        self._odom_reset_client = self.create_client(Trigger, self.odom_reset_service)
        self._slam_save_client = self.create_client(SaveMap, self.slam_save_service)

        self._odom_sub = None
        self._scan_sub = None
        self._imu_sub = None
        self._connected_sub = None
        self._voltage_sub = None
        self._context_sub = None
        self._context_prediction_sub = None
        self._diagnostics_sub = None
        self._map_sub = None
        self._camera_sub = None

        self._tf_buffer = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)
        self._watchdog_timer = self.create_timer(
            1.0 / self.manual_republish_hz, self._watchdog
        )

    def ensure_telemetry_subscriptions(self) -> None:
        """Subscribe to lightweight telemetry topics once the dashboard asks."""
        with self._lock:
            if self._odom_sub is None:
                self._odom_sub = self.create_subscription(
                    Odometry, self.odom_topic, self._odom_callback, self._sensor_qos
                )
            if self._scan_sub is None:
                self._scan_sub = self.create_subscription(
                    LaserScan, self.scan_topic, self._scan_callback, self._sensor_qos
                )
            if self._imu_sub is None:
                self._imu_sub = self.create_subscription(
                    Imu, "/imu/data", self._imu_callback, self._sensor_qos
                )
            if self._connected_sub is None:
                self._connected_sub = self.create_subscription(
                    Bool,
                    "/hardware/connected",
                    self._connected_callback,
                    self._sensor_qos,
                )
            if self._voltage_sub is None:
                self._voltage_sub = self.create_subscription(
                    Float32,
                    "/battery/voltage",
                    self._voltage_callback,
                    self._sensor_qos,
                )
            if self._context_sub is None:
                self._context_sub = self.create_subscription(
                    Float64,
                    "/cca/context_score",
                    self._context_callback,
                    self._sensor_qos,
                )
            if self._context_prediction_sub is None:
                self._context_prediction_sub = self.create_subscription(
                    Float64MultiArray,
                    "/cca/context_prediction",
                    self._context_prediction_callback,
                    self._sensor_qos,
                )
            if self._diagnostics_sub is None:
                self._diagnostics_sub = self.create_subscription(
                    Float64MultiArray,
                    "/cca/controller_diagnostics",
                    self._diagnostics_callback,
                    self._sensor_qos,
                )

    def ensure_map_subscription(self) -> None:
        with self._lock:
            if self._map_sub is None:
                self._map_sub = self.create_subscription(
                    OccupancyGrid,
                    self.map_topic,
                    self._map_callback,
                    self._map_qos,
                )

    def register_camera_client(self) -> None:
        with self._lock:
            self._camera_clients += 1
            if self._camera_sub is None:
                self._camera_sub = self.create_subscription(
                    Image,
                    self.camera_topic,
                    self._camera_callback,
                    self._sensor_qos,
                )

    def unregister_camera_client(self) -> None:
        with self._camera_condition:
            self._camera_clients = max(0, self._camera_clients - 1)
            if self._camera_clients > 0:
                return
            if self._camera_sub is not None:
                self.destroy_subscription(self._camera_sub)
                self._camera_sub = None
            self._latest_camera_frame = None
            self._camera_sequence = 0
            self._last_camera_monotonic = None
            self._telemetry["camera_rate_hz"] = 0.0
            self._camera_condition.notify_all()

    def wait_for_camera_frame(
        self, sequence: int, timeout_s: float = 1.5
    ) -> tuple[int, Image | None]:
        with self._camera_condition:
            deadline = time.monotonic() + timeout_s
            while self._camera_sequence <= sequence:
                remaining = deadline - time.monotonic()
                if remaining <= 0.0:
                    return self._camera_sequence, None
                self._camera_condition.wait(timeout=remaining)
            return self._camera_sequence, self._latest_camera_frame

    def telemetry_snapshot(self) -> dict[str, Any]:
        self.update_map_pose()
        with self._lock:
            return copy.deepcopy(self._telemetry)

    def map_snapshot(self) -> dict[str, Any] | None:
        with self._lock:
            # The map payload contains a large immutable base64 string.  A
            # deep copy here duplicates that string on every dashboard poll
            # and can starve the ROS executor while SLAM is publishing.
            # Values are replaced atomically by _map_callback, so a shallow
            # copy gives the HTTP handler its own mapping without copying the
            # grid itself.
            return dict(self._latest_map) if self._latest_map is not None else None

    def mapping_status(self) -> dict[str, Any]:
        with self._lock:
            paused = self._slam_paused
            map_available = self._latest_map is not None
            last_save = copy.deepcopy(self._last_map_save)
        return {
            "slam_enabled": self.slam_enabled,
            "scanning": not paused,
            "paused": paused,
            "slam_running": self._has_publisher(self.map_topic),
            "map_available": map_available,
            "map_save_root": str(self.map_save_root),
            "last_saved": last_save,
        }

    def set_mapping_enabled(self, enabled: bool) -> dict[str, Any]:
        """Pause or resume measurements while preserving the active map."""
        if not self.slam_enabled:
            raise RuntimeError("SLAM is disabled in the current bringup")
        desired_paused = not bool(enabled)
        with self._map_control_lock:
            with self._lock:
                if self._slam_paused == desired_paused:
                    slam_running = self._has_publisher(self.map_topic)
                    if desired_paused or slam_running:
                        status = self.mapping_status()
                        status["changed"] = False
                        return status

            if not desired_paused and not self._has_publisher(self.map_topic):
                response = self._call_service(
                    self._slam_start_client,
                    Trigger.Request(),
                    self.slam_start_service,
                )
                if not bool(getattr(response, "success", False)):
                    raise RuntimeError(
                        "SLAM session manager could not start the launch: "
                        f"{getattr(response, 'message', '')}"
                    )
                with self._lock:
                    self._slam_paused = False
                status = self.mapping_status()
                status["changed"] = True
                return status

            response = self._call_service(
                self._slam_pause_client,
                Pause.Request(),
                self.slam_pause_service,
            )
            if not bool(getattr(response, "status", False)):
                raise RuntimeError(
                    "SLAM pause service rejected the requested toggle "
                    f"(paused={desired_paused})"
                )
            with self._lock:
                self._slam_paused = desired_paused
            status = self.mapping_status()
            status["changed"] = True
            return status

    def clear_map(self) -> dict[str, Any]:
        """Start a fresh SLAM map with odometry and TF reset at the robot."""
        if not self.slam_enabled:
            raise RuntimeError("SLAM is disabled in the current bringup")
        with self._map_control_lock:
            self.publish_cmd_vel(0.0, 0.0, 0.0)
            stopped = False
            try:
                stop_response = self._call_service(
                    self._slam_stop_client,
                    Trigger.Request(),
                    self.slam_stop_service,
                )
                if not bool(getattr(stop_response, "success", False)):
                    raise RuntimeError(
                        "SLAM session stop failed: "
                        f"{getattr(stop_response, 'message', '')}"
                    )
                stopped = True

                odom_response = self._call_service(
                    self._odom_reset_client,
                    Trigger.Request(),
                    self.odom_reset_service,
                )
                if not bool(getattr(odom_response, "success", False)):
                    raise RuntimeError(
                        "Odometry reset failed: "
                        f"{getattr(odom_response, 'message', '')}"
                    )

                with self._lock:
                    self._latest_map = None
                    self._latest_map_signature = None
                    self._map_ignore_before_ns = time.time_ns()
                    self._telemetry["map_pose"] = None
                try:
                    self._tf_buffer.clear()
                except AttributeError:
                    pass

                start_response = self._call_service(
                    self._slam_start_client,
                    Trigger.Request(),
                    self.slam_start_service,
                )
                if not bool(getattr(start_response, "success", False)):
                    raise RuntimeError(
                        "SLAM session start failed: "
                        f"{getattr(start_response, 'message', '')}"
                    )
                with self._lock:
                    self._slam_paused = False
            except Exception:
                if stopped:
                    try:
                        self._call_service(
                            self._slam_start_client,
                            Trigger.Request(),
                            self.slam_start_service,
                        )
                    except Exception:
                        pass
                raise
        status = self.mapping_status()
        status["cleared"] = True
        return status

    def save_map(self, requested_name: str | None = None) -> dict[str, Any]:
        """Save the active SLAM map as <name>.yaml and <name>.pgm in the root."""
        name = self._normalise_map_name(requested_name)
        root = self.map_save_root.resolve()
        base_path = (root / name).resolve()
        if base_path.parent != root:
            raise ValueError("map name resolves outside the configured map directory")
        if base_path.exists() and base_path.is_dir():
            raise ValueError(f"map base path is a directory: {base_path}")

        root.mkdir(parents=True, exist_ok=True)
        request = SaveMap.Request()
        request.name.data = str(base_path)
        response = self._call_service(
            self._slam_save_client,
            request,
            self.slam_save_service,
        )
        result = int(getattr(response, "result", 255))
        if result != 0:
            raise RuntimeError(f"SLAM save_map failed with result={result}")

        files = [
            str(root / f"{name}.yaml"),
            str(root / f"{name}.pgm"),
        ]
        saved = {
            "name": name,
            "directory": str(root),
            "base_path": str(base_path),
            "files": files,
            "result": result,
        }
        with self._lock:
            self._last_map_save = saved
        return {"accepted": True, **saved, "mapping": self.mapping_status()}

    def _call_service(self, client: Any, request: Any, service_name: str) -> Any:
        if not client.wait_for_service(timeout_sec=self.map_service_timeout_s):
            raise RuntimeError(f"ROS service is unavailable: {service_name}")
        future = client.call_async(request)
        completed = threading.Event()
        future.add_done_callback(lambda _: completed.set())
        if not completed.wait(timeout=self.map_service_timeout_s):
            raise TimeoutError(f"ROS service timed out: {service_name}")
        try:
            response = future.result()
        except Exception as error:
            raise RuntimeError(f"ROS service failed: {service_name}: {error}") from error
        if response is None:
            raise RuntimeError(f"ROS service returned no response: {service_name}")
        return response

    @staticmethod
    def _normalise_map_name(requested_name: str | None) -> str:
        raw = str(requested_name or "").strip()
        if not raw:
            return f"map-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        ascii_name = unicodedata.normalize("NFKD", raw).encode(
            "ascii", "ignore"
        ).decode("ascii")
        name = re.sub(r"[^A-Za-z0-9_-]+", "-", ascii_name).strip("-_")
        if not name:
            raise ValueError("map name must contain letters or numbers")
        if len(name) > 64:
            raise ValueError("map name must be at most 64 characters")
        return name

    def camera_status(self) -> dict[str, Any]:
        with self._lock:
            timestamp = self._telemetry.get("camera_capture_t_ns")
            age_s = None
            if timestamp is not None:
                age_s = max(0.0, time.time() - float(timestamp) / 1.0e9)
            return {
                "topic": self.camera_topic,
                "frames": self._camera_sequence,
                "last_frame_age_s": age_s,
            }

    def component_states(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "bridge",
                "label": "HTTP/WebRTC bridge",
                "host_device": "robot",
                "running": True,
                "description": "REST API and WebRTC camera endpoint in this bringup.",
            },
            {
                "id": "robot_base",
                "label": "CCA runtime + STM32",
                "host_device": "robot",
                "running": self._has_publisher(self.odom_topic)
                or self._has_subscriber(self.manual_cmd_vel_topic),
                "description": "cca_stm_bridge, reference and CCA-NMPC nodes.",
            },
            {
                "id": "lidar",
                "label": "LSLiDAR N10P",
                "host_device": "robot",
                "running": self._has_publisher(self.scan_topic),
                "description": "LaserScan source used by SLAM Toolbox.",
            },
            {
                "id": "camera",
                "label": "Astra-S camera",
                "host_device": "robot",
                "running": self._has_publisher(self.camera_topic),
                "description": "RGB image source for the WebRTC track.",
            },
            {
                "id": "slam",
                "label": "SLAM Toolbox",
                "host_device": "robot",
                "running": self._has_publisher(self.map_topic),
                "description": "Online map publisher on /map.",
            },
            {
                "id": "navigation",
                "label": "CCA path control",
                "host_device": "robot",
                "running": self._has_subscriber(self.global_path_topic),
                "description": "Global paths are consumed by cca_reference_node.",
            },
        ]

    def publish_cmd_vel(self, linear_x: float, linear_y: float, angular_z: float) -> None:
        values = (float(linear_x), float(linear_y), float(angular_z))
        if not all(math.isfinite(value) for value in values):
            raise ValueError("velocity values must be finite")
        bounded = (
            max(-1.5, min(1.5, values[0])),
            max(-1.5, min(1.5, values[1])),
            max(-3.0, min(3.0, values[2])),
        )
        with self._lock:
            self._last_command = bounded
            self._last_command_monotonic = time.monotonic()
            self._publish_velocity(bounded)

    def send_nav_goal(self, x: float, y: float, yaw: float) -> dict[str, Any]:
        values = (float(x), float(y), float(yaw))
        if not all(math.isfinite(value) for value in values):
            raise ValueError("navigation goal values must be finite")
        path_x, path_y, path_yaw = self._map_to_path_pose(*values)
        stamp = self.get_clock().now().to_msg()

        goal = PoseStamped()
        goal.header.stamp = stamp
        goal.header.frame_id = self.odom_frame
        goal.pose.position.x = path_x
        goal.pose.position.y = path_y
        goal.pose.orientation.z = math.sin(path_yaw / 2.0)
        goal.pose.orientation.w = math.cos(path_yaw / 2.0)
        self._goal_pub.publish(goal)

        path = Path()
        path.header = goal.header
        # The CCA reference node accepts a Path and repeats its last pose over
        # the controller horizon. Keeping the goal repeated makes the command
        # contract deterministic without inventing a second planner.
        path.poses = [copy.deepcopy(goal) for _ in range(8)]
        self._path_pub.publish(path)
        with self._lock:
            self._navigation_active = True
            self._telemetry["context"]["navigation_mode"] = "goal"
        return {
            "accepted": True,
            "frame_id": self.odom_frame,
            "x": path_x,
            "y": path_y,
            "yaw": path_yaw,
        }

    def cancel_navigation(self) -> dict[str, Any]:
        message = Path()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = self.odom_frame
        self._path_pub.publish(message)
        self._cancel_pub.publish(Empty())
        self.publish_cmd_vel(0.0, 0.0, 0.0)
        with self._lock:
            self._navigation_active = False
            self._telemetry["context"]["navigation_mode"] = "idle"
        return {"accepted": True, "navigation": "cancelled"}

    def _watchdog(self) -> None:
        now = time.monotonic()
        with self._lock:
            command = self._last_command
            stale = (
                now - self._last_command_monotonic > self.watchdog_timeout_s
                and any(abs(value) > 1.0e-9 for value in command)
            )
            if stale:
                self._last_command = (0.0, 0.0, 0.0)
                self._last_command_monotonic = now
            if stale:
                self._publish_velocity((0.0, 0.0, 0.0))
            elif any(abs(value) > 1.0e-9 for value in command):
                # HTTP delivery is bursty on a wireless link. Keep the last
                # operator command alive at a fixed rate so the STM watchdog
                # does not alternate between the requested velocity and zero.
                self._publish_velocity(command)

    def _publish_velocity(self, values: tuple[float, float, float]) -> None:
        message = Twist()
        message.linear.x, message.linear.y, message.angular.z = values
        self._cmd_pub.publish(message)

    def _odom_callback(self, message: Odometry) -> None:
        with self._lock:
            self._telemetry["odom"] = {
                "x": round(float(message.pose.pose.position.x), 4),
                "y": round(float(message.pose.pose.position.y), 4),
                "theta": round(self._yaw(message.pose.pose.orientation), 4),
                "linear_x": round(float(message.twist.twist.linear.x), 4),
                "linear_y": round(float(message.twist.twist.linear.y), 4),
                "angular_z": round(float(message.twist.twist.angular.z), 4),
            }
            self._telemetry["last_update"] = time.time()

    def _scan_callback(self, message: LaserScan) -> None:
        now = time.monotonic()
        with self._lock:
            if self._last_scan_monotonic is not None:
                delta = now - self._last_scan_monotonic
                if delta > 1.0e-4:
                    rate = min(100.0, 1.0 / delta)
                    old_rate = float(self._telemetry["lidar_rate_hz"])
                    self._telemetry["lidar_rate_hz"] = round(
                        rate if old_rate <= 0.0 else 0.75 * old_rate + 0.25 * rate,
                        2,
                    )
            self._last_scan_monotonic = now

            left = self._range_near_angle(message, math.pi / 2.0)
            right = self._range_near_angle(message, -math.pi / 2.0)
            self._telemetry["lidar_clearance"] = {
                "left": round(left, 3),
                "right": round(right, 3),
            }

    def _imu_callback(self, message: Imu) -> None:
        with self._lock:
            self._telemetry["odom"]["gyro_z"] = round(
                float(message.angular_velocity.z), 4
            )

    def _connected_callback(self, message: Bool) -> None:
        with self._lock:
            self._telemetry["hardware_connected"] = bool(message.data)

    def _voltage_callback(self, message: Float32) -> None:
        voltage = float(message.data)
        if not math.isfinite(voltage):
            return
        with self._lock:
            self._telemetry["battery"]["voltage"] = round(voltage, 3)

    def _context_callback(self, message: Float64) -> None:
        score = max(0.0, min(1.0, float(message.data)))
        with self._lock:
            context = self._telemetry["context"]
            context["phi_h"] = round(score, 4)
            context["legacy_context"] = (
                "OZ" if score < 0.2 else "CA" if score < 0.65 else "CONFLICT"
            )

    def _context_prediction_callback(self, message: Float64MultiArray) -> None:
        values = [float(value) for value in message.data if math.isfinite(float(value))]
        with self._lock:
            self._telemetry["context"]["prediction"] = values[:64]

    def _diagnostics_callback(self, message: Float64MultiArray) -> None:
        values = [float(value) for value in message.data]
        if len(values) < 7:
            return
        with self._lock:
            self._telemetry["solver"] = {
                "solve_time_ms": round(values[0], 4),
                "objective": round(values[1], 4),
                "maximum_constraint_violation": round(values[2], 4),
                "status": values[3],
                "deadline_missed": bool(values[4]),
                "risk_bound": round(values[5], 4),
                "risk_slack_m": round(values[6], 4),
            }

    def _map_callback(self, message: OccupancyGrid) -> None:
        data = bytes(int(value) & 0xFF for value in message.data)
        width = int(message.info.width)
        height = int(message.info.height)
        resolution = float(message.info.resolution)
        origin_x = float(message.info.origin.position.x)
        origin_y = float(message.info.origin.position.y)
        signature = (width, height, resolution, origin_x, origin_y, hash(data))
        stamp_ns = (
            int(message.header.stamp.sec) * 1_000_000_000
            + int(message.header.stamp.nanosec)
        )
        with self._lock:
            if (
                self._map_ignore_before_ns > 0
                and stamp_ns > 0
                and stamp_ns < self._map_ignore_before_ns
            ):
                return
            self._map_ignore_before_ns = 0
            if signature == self._latest_map_signature:
                return
            self._latest_map_signature = signature
            self._latest_map = {
                "width": width,
                "height": height,
                "resolution": resolution,
                "origin_x": origin_x,
                "origin_y": origin_y,
                "grid_data": base64.b64encode(data).decode("ascii"),
                "timestamp": time.time(),
                "frame_id": message.header.frame_id or self.map_frame,
            }

    def _camera_callback(self, message: Image) -> None:
        now = time.monotonic()
        with self._camera_condition:
            if self._last_camera_monotonic is not None:
                delta = now - self._last_camera_monotonic
                if delta > 1.0e-4:
                    rate = min(120.0, 1.0 / delta)
                    old_rate = float(self._telemetry["camera_rate_hz"])
                    self._telemetry["camera_rate_hz"] = round(
                        rate if old_rate <= 0.0 else 0.75 * old_rate + 0.25 * rate,
                        2,
                    )
            self._last_camera_monotonic = now
            self._latest_camera_frame = message
            self._camera_sequence += 1
            self._telemetry["camera_capture_t_ns"] = time.time_ns()
            self._camera_condition.notify_all()

    def update_map_pose(self) -> None:
        try:
            transform = self._tf_buffer.lookup_transform(
                self.map_frame, self.control_frame, Time()
            )
        except Exception:
            return
        with self._lock:
            translation = transform.transform.translation
            rotation = transform.transform.rotation
            self._telemetry["map_pose"] = {
                "x": round(float(translation.x), 4),
                "y": round(float(translation.y), 4),
                "yaw": round(self._yaw(rotation), 4),
            }

    def _map_to_path_pose(self, x: float, y: float, yaw: float) -> tuple[float, float, float]:
        if self.map_frame == self.odom_frame:
            return x, y, yaw
        try:
            transform = self._tf_buffer.lookup_transform(
                self.odom_frame, self.map_frame, Time()
            )
        except Exception:
            # A goal remains usable during the short period before SLAM
            # publishes map->odom; callers can retry after the map appears.
            return x, y, yaw
        tx = transform.transform.translation.x
        ty = transform.transform.translation.y
        transform_yaw = self._yaw(transform.transform.rotation)
        cos_yaw = math.cos(transform_yaw)
        sin_yaw = math.sin(transform_yaw)
        return (
            tx + cos_yaw * x - sin_yaw * y,
            ty + sin_yaw * x + cos_yaw * y,
            self._normalize_angle(transform_yaw + yaw),
        )

    @staticmethod
    def _yaw(quaternion: Any) -> float:
        siny_cosp = 2.0 * (quaternion.w * quaternion.z + quaternion.x * quaternion.y)
        cosy_cosp = 1.0 - 2.0 * (quaternion.y * quaternion.y + quaternion.z * quaternion.z)
        return math.atan2(siny_cosp, cosy_cosp)

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        return math.atan2(math.sin(angle), math.cos(angle))

    @staticmethod
    def _range_near_angle(message: LaserScan, target: float) -> float:
        best = 5.0
        best_error = math.inf
        for index, value in enumerate(message.ranges):
            if not math.isfinite(value):
                continue
            if value < message.range_min or value > message.range_max:
                continue
            angle = message.angle_min + index * message.angle_increment
            error = abs(math.atan2(math.sin(angle - target), math.cos(angle - target)))
            if error < best_error:
                best_error = error
                best = float(value)
        return best

    def _has_publisher(self, topic: str) -> bool:
        try:
            return self.count_publishers(topic) > 0
        except Exception:
            return False

    def _has_subscriber(self, topic: str) -> bool:
        try:
            return self.count_subscribers(topic) > 0
        except Exception:
            return False

    def destroy_node(self) -> bool:
        try:
            self._publish_velocity((0.0, 0.0, 0.0))
        except Exception:
            pass
        return super().destroy_node()
