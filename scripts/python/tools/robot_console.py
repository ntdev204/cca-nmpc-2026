from __future__ import annotations

import argparse
import base64
import io
import json
import math
import os
import platform
import queue
import signal
import socket
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT


ZERO = (0.0, 0.0, 0.0)
APP_PORT = 8765
MAX_POINTS = 360
STATE_PERIOD_S = 0.10
SENSOR_PERIOD_S = 0.10
MAP_PERIOD_S = 1.0
# The camera is a monitoring stream, not the control loop. Keep it light enough
# for a Wi-Fi/VPN link and let Peer retain only the newest frame.
CAMERA_PERIOD_S = 0.33
CAMERA_MAX_SIZE = (480, 360)
CAMERA_JPEG_QUALITY = 55
STREAM_MESSAGE_TYPES = frozenset({"state", "lidar", "map", "camera"})
POSE_DISPLAY_TIME_CONSTANT_S = 0.18
DISPLAY_VIEW_SPAN_M = 6.0
MOVE_DIRECTIONS: dict[str, tuple[int, int, int]] = {
    "forward": (1, 0, 0),
    "backward": (-1, 0, 0),
    "left": (0, 1, 0),
    "right": (0, -1, 0),
    "forward_left": (1, 1, 0),
    "forward_right": (1, -1, 0),
    "backward_left": (-1, 1, 0),
    "backward_right": (-1, -1, 0),
    "rotate_left": (0, 0, 1),
    "rotate_right": (0, 0, -1),
    "stop": (0, 0, 0),
}


def now_ns() -> int:
    return time.time_ns()


def copy_pose_for_mapping(pose: Any) -> Any:
    """Copy live odometry before a mapper is allowed to correct it."""

    try:
        from manual_map import Pose
    except ModuleNotFoundError:
        from tools.manual_map import Pose

    return Pose(
        x_m=float(pose.x_m),
        y_m=float(pose.y_m),
        yaw_rad=float(pose.yaw_rad),
        last_t_ns=pose.last_t_ns,
    )


def openni_directory() -> Path | None:
    candidates: list[Path] = []
    override = os.environ.get("OPENNI2_REDIST", "").strip()
    if override:
        candidates.append(Path(override).expanduser())
    machine = platform.machine().lower()
    if "aarch64" in machine or "arm64" in machine:
        candidates.append(PROJECT_ROOT / "openni2_redist" / "arm64")
    elif os.name == "nt":
        candidates.append(PROJECT_ROOT / "openni2_redist" / "x64")
    candidates.extend(
        [
            PROJECT_ROOT / "openni2_redist" / "arm64",
            PROJECT_ROOT / "openni2_redist" / "x64",
        ]
    )
    for path in candidates:
        core = path / "libOpenNI2.so"
        astra_core = path / "libOpenNI2_astra.so"
        if os.name != "nt" and not core.exists() and astra_core.is_file():
            try:
                core.symlink_to(astra_core.name)
            except OSError:
                pass
        if (path / "OpenNI2").is_dir() and any(path.glob("libOpenNI2*.so")):
            return path
    return None


def serial_port(default: str, fallbacks: tuple[str, ...]) -> str:
    if default and (Path(default).exists() or default.startswith("COM")):
        return default
    for value in fallbacks:
        if Path(value).exists():
            return value
    return default


def compact_points(points: Any, limit: int = MAX_POINTS) -> list[list[float]]:
    if not points:
        return []
    step = max(1, math.ceil(len(points) / limit))
    result: list[list[float]] = []
    for point in points[::step]:
        try:
            angle = float(point.angle_rad)
            distance = float(point.range_m)
        except (AttributeError, TypeError, ValueError):
            continue
        if math.isfinite(angle) and math.isfinite(distance) and distance > 0.0:
            result.append([round(angle, 5), round(distance, 4)])
    return result


def encode_json(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def direction_velocity(direction: str, speed_mps: float, yaw_radps: float) -> tuple[float, float, float]:
    normalized = direction.strip().lower().replace("-", "_").replace(" ", "_")
    try:
        vx_sign, vy_sign, wz_sign = MOVE_DIRECTIONS[normalized]
    except KeyError as error:
        supported = ", ".join(sorted(MOVE_DIRECTIONS))
        raise ValueError(f"unknown move direction {direction!r}; use one of: {supported}") from error
    if not math.isfinite(speed_mps) or speed_mps < 0.0:
        raise ValueError("speed_mps must be finite and nonnegative")
    if not math.isfinite(yaw_radps) or yaw_radps < 0.0:
        raise ValueError("yaw_radps must be finite and nonnegative")
    return vx_sign * speed_mps, vy_sign * speed_mps, wz_sign * yaw_radps


def smooth_display_pose(
    previous: tuple[float, float, float] | None,
    target: tuple[float, float, float],
    dt_s: float,
    *,
    time_constant_s: float = POSE_DISPLAY_TIME_CONSTANT_S,
) -> tuple[float, float, float]:
    """Low-pass only the laptop rendering pose; control/state stay untouched."""

    target = tuple(float(value) for value in target)
    if not all(math.isfinite(value) for value in target):
        raise ValueError("display pose target must be finite")
    if previous is None:
        return target
    if not math.isfinite(dt_s) or dt_s < 0.0 or not math.isfinite(time_constant_s) or time_constant_s <= 0.0:
        raise ValueError("display pose timing must be finite and nonnegative")
    alpha = 1.0 if dt_s >= 1.0 else 1.0 - math.exp(-dt_s / time_constant_s)
    px, py, pyaw = (float(value) for value in previous)
    if not all(math.isfinite(value) for value in (px, py, pyaw)):
        raise ValueError("previous display pose must be finite")
    yaw_delta = math.atan2(math.sin(target[2] - pyaw), math.cos(target[2] - pyaw))
    yaw = math.atan2(math.sin(pyaw + alpha * yaw_delta), math.cos(pyaw + alpha * yaw_delta))
    return (
        px + alpha * (target[0] - px),
        py + alpha * (target[1] - py),
        yaw,
    )


def send_json(sock: socket.socket, lock: threading.Lock, payload: dict[str, Any]) -> None:
    encoded = encode_json(payload)
    with lock:
        sock.sendall(encoded)


@dataclass(eq=False)
class Peer:
    sock: socket.socket
    address: str
    lock: threading.Lock = field(default_factory=threading.Lock)
    outgoing_condition: threading.Condition = field(default_factory=lambda: threading.Condition(threading.Lock()))
    control_outgoing: deque[bytes] = field(default_factory=deque)
    latest_stream: dict[str, bytes] = field(default_factory=dict)
    writer_stop: threading.Event = field(default_factory=threading.Event)
    writer_thread: threading.Thread | None = None
    closed: bool = False

    def start_writer(self) -> None:
        self.writer_thread = threading.Thread(target=self._writer_loop, name=f"robot-console-writer-{self.address}", daemon=True)
        self.writer_thread.start()

    def enqueue(self, payload: dict[str, Any]) -> bool:
        packet = encode_json(payload)
        message_type = str(payload.get("type", "event"))
        with self.outgoing_condition:
            if self.closed:
                return False
            if message_type in STREAM_MESSAGE_TYPES:
                # Keep only the newest state/frame of each stream. A slow GUI
                # must never create a backlog that delays control events.
                self.latest_stream[message_type] = packet
            else:
                self.control_outgoing.append(packet)
            self.outgoing_condition.notify()
        return True

    def _next_packet(self) -> bytes | None:
        with self.outgoing_condition:
            while not self.closed and not self.writer_stop.is_set():
                if self.control_outgoing:
                    return self.control_outgoing.popleft()
                if self.latest_stream:
                    message_type = next(iter(self.latest_stream))
                    return self.latest_stream.pop(message_type)
                self.outgoing_condition.wait(timeout=0.25)
            return None

    def _writer_loop(self) -> None:
        while not self.writer_stop.is_set():
            packet = self._next_packet()
            if packet is None:
                return
            try:
                with self.lock:
                    self.sock.sendall(packet)
            except (ConnectionError, OSError):
                self.close()
                return

    def close(self) -> None:
        with self.outgoing_condition:
            if self.closed:
                return
            self.closed = True
            self.writer_stop.set()
            self.control_outgoing.clear()
            self.latest_stream.clear()
            self.outgoing_condition.notify_all()
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass


class RobotService:
    def __init__(self, bind: str, port: int) -> None:
        self.bind = bind
        self.port = port
        self.stop_event = threading.Event()
        self.state_lock = threading.RLock()
        self.peers: set[Peer] = set()
        self.server_socket: socket.socket | None = None
        self._closed = False
        self.stm: Any = None
        self.lidar: Any = None
        self.camera: Any = None
        self.camera_thread: threading.Thread | None = None
        self.pose: Any = None
        self.map_pose: Any = None
        self.mapper: Any = None
        self.files: Any = None
        self.run_root: Path | None = None
        self.scan_started_ns = 0
        self.scan_active = False
        self.scan_saved = False
        self.last_saved_root: Path | None = None
        self.armed = False
        self.last_command = ZERO
        self.last_command_mono = time.monotonic()
        self.watchdog_zero_sent = False
        self.command_sequence = 0
        self.last_telemetry_ns = 0
        self.last_scan_ns = 0
        self.last_state_mono = 0.0
        self.last_sensor_mono = 0.0
        self.last_map_mono = 0.0
        self.last_camera_mono = 0.0
        self.last_broadcast_map_signature = ""
        self.latest_lidar: list[list[float]] = []
        self.latest_camera: str | None = None
        self.camera_shape: list[int] | None = None
        self.camera_status = "disabled"
        # A* is a planning/visualisation layer.  It never sends a motion
        # command; the existing controller/actuation entry point consumes the
        # resulting global path only after its normal safety gates pass.
        self.plan_payload: dict[str, Any] | None = None
        self.status: dict[str, Any] = {
            "stm": "offline",
            "lidar": "offline",
            "camera": "disabled",
            "armed": False,
            "scan": "idle",
            "message": "starting",
        }

    def _set_status(self, key: str, value: str, message: str | None = None) -> None:
        with self.state_lock:
            self.status[key] = value
            if message:
                self.status["message"] = message
        self.broadcast({"type": "event", "event": "status", "status": self.status_payload()})

    def status_payload(self) -> dict[str, Any]:
        with self.state_lock:
            return {
                **self.status,
                "armed": self.armed,
                "scan_active": self.scan_active,
                "run": self.run_root.name if self.run_root else None,
            }

    def start_sources(self) -> None:
        from hardware import AstraSSource, N10PSerialSource, Stm32SerialSource, N10P_PROTOCOL_PROFILE

        stm_port = serial_port(os.environ.get("CCA_STM_PORT", "/dev/rai_controller"), ("/dev/ttyACM0", "COM5"))
        lidar_port = serial_port(os.environ.get("CCA_LIDAR_PORT", "/dev/rai_lidar"), ("/dev/ttyACM1", "COM6"))
        try:
            self.stm = Stm32SerialSource(stm_port, baudrate=115200, backend="auto")
            self.stm.start()
            self._set_status("stm", "online", f"STM {stm_port} / {self.stm.backend}")
        except Exception as error:
            self.stm = None
            self._set_status("stm", "error", str(error))
        try:
            self.lidar = N10PSerialSource(lidar_port, profile=N10P_PROTOCOL_PROFILE, baudrate=460800)
            self.lidar.start()
            self._set_status("lidar", "online", f"N10P {lidar_port} / 460800")
        except Exception as error:
            self.lidar = None
            self._set_status("lidar", "error", str(error))
        sdk_path = openni_directory()
        if sdk_path is None:
            self._set_status("camera", "missing", "OpenNI2 directory not found")
            return
        try:
            self.camera = AstraSSource(sdk_path=str(sdk_path), depth_scale_m=0.001)
            self.camera.start()
            self.camera_status = "online"
            self._set_status("camera", "online", f"Astra-S / {sdk_path}")
            self.camera_thread = threading.Thread(target=self._camera_loop, name="astra-reader", daemon=True)
            self.camera_thread.start()
        except Exception as error:
            self.camera = None
            self.camera_status = "error"
            self._set_status("camera", "error", str(error))

    def _camera_loop(self) -> None:
        while not self.stop_event.is_set() and self.camera is not None:
            try:
                with self.state_lock:
                    has_client = bool(self.peers)
                if not has_client:
                    # Do not spend CPU encoding frames while the console is
                    # disconnected; resume immediately when a client arrives.
                    self.stop_event.wait(0.10)
                    continue
                frame = self.camera.read()
                encoded = self._encode_camera(frame.color_bgr)
                with self.state_lock:
                    self.latest_camera = encoded
                    self.camera_shape = [int(frame.color_bgr.shape[1]), int(frame.color_bgr.shape[0])]
                time.sleep(CAMERA_PERIOD_S)
            except Exception as error:
                self._set_status("camera", "error", str(error))
                return

    @staticmethod
    def _encode_camera(color_bgr: Any) -> str:
        from PIL import Image

        rgb = color_bgr[:, :, ::-1]
        image = Image.fromarray(rgb)
        image.thumbnail(CAMERA_MAX_SIZE)
        stream = io.BytesIO()
        image.save(stream, format="JPEG", quality=CAMERA_JPEG_QUALITY, optimize=False)
        return base64.b64encode(stream.getvalue()).decode("ascii")

    def start_scan(self) -> None:
        from manual_map import OccupancyMap, Pose, RunFiles

        with self.state_lock:
            if self.scan_active:
                return
            if self.stm is None or self.lidar is None:
                self.broadcast({"type": "event", "event": "error", "message": "STM32 and N10P must be online before scanning"})
                return
            run_id = time.strftime("console-map-%Y%m%d-%H%M%S")
            root = PROJECT_ROOT / "experiments" / "runs" / run_id
            suffix = 1
            while root.exists():
                root = PROJECT_ROOT / "experiments" / "runs" / f"{run_id}-{suffix}"
                suffix += 1
            self.mapper = OccupancyMap(
                0.05,
                lidar_x_m=0.10,
                lidar_y_m=0.0,
                lidar_yaw_rad=0.0,
                min_range_m=0.05,
                max_range_m=8.0,
                padding_cells=5,
            )
            self.pose = Pose()
            self.map_pose = Pose()
            self.files = RunFiles(root)
            self.run_root = root
            self.scan_started_ns = now_ns()
            self.scan_active = True
            self.scan_saved = False
            self.plan_payload = None
            self.last_scan_ns = 0
            self.last_broadcast_map_signature = ""
            self.files.event("console_scan_started", "lidar=N10P; map=odom_seeded_local_scan_to_map")
            self.status["scan"] = "recording"
        self.broadcast({"type": "event", "event": "scan_started", "status": self.status_payload()})

    def save_scan(self, reason: str = "operator") -> None:
        with self.state_lock:
            if not self.scan_active or self.mapper is None or self.run_root is None:
                self.broadcast({"type": "event", "event": "error", "message": "no active scan"})
                return
            root = self.run_root
            mapper = self.mapper
            files = self.files
            try:
                mapper.save(root)
                if files is not None:
                    files.event("console_scan_saved", reason)
                    files.flush()
                    files.close()
                self._write_manifest(root, mapper, reason)
                self.scan_saved = True
                self.last_saved_root = root
                self.scan_active = False
                self.files = None
                self.status["scan"] = "saved"
            except Exception as error:
                self.broadcast({"type": "event", "event": "error", "message": str(error)})
                return
        self.broadcast({"type": "event", "event": "scan_saved", "path": str(root), "status": self.status_payload()})

    def load_saved_map(self, message: dict[str, Any] | None = None) -> None:
        """Stream a saved map package from Jetson to the laptop canvas.

        The laptop cannot open a Jetson filesystem path directly, so the map
        JSON is read by the service and sent through the existing map message.
        An optional run id is restricted to the experiments/runs directory.
        """

        requested_run = str((message or {}).get("run_id", "")).strip()
        runs_root = PROJECT_ROOT / "experiments" / "runs"
        with self.state_lock:
            candidate_roots: list[Path] = []
            if self.last_saved_root is not None:
                candidate_roots.append(self.last_saved_root)
            if self.run_root is not None:
                candidate_roots.append(self.run_root)
        if requested_run:
            if Path(requested_run).name != requested_run or requested_run in {".", ".."}:
                raise ValueError("run_id must be a single run-directory name")
            candidate_roots = [runs_root / requested_run]
        else:
            candidate_roots.extend(
                sorted(
                    (path for path in runs_root.glob("console-map-*") if path.is_dir()),
                    key=lambda path: path.stat().st_mtime,
                    reverse=True,
                )
            )

        map_path: Path | None = None
        for root in candidate_roots:
            path = root / "map.json"
            if path.is_file():
                map_path = path
                break
        if map_path is None:
            raise FileNotFoundError("no saved console map was found")
        payload = json.loads(map_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("saved map payload must be an object")
        width = int(payload.get("width", 0))
        height = int(payload.get("height", 0))
        occupancy = payload.get("occupancy")
        if width <= 0 or height <= 0 or not isinstance(occupancy, list) or len(occupancy) < width * height:
            raise ValueError("saved map dimensions or occupancy data are invalid")
        plan: dict[str, Any] | None = None
        plan_path = map_path.with_name("navigation_plan.json")
        if plan_path.is_file():
            candidate_plan = json.loads(plan_path.read_text(encoding="utf-8"))
            if isinstance(candidate_plan, dict):
                plan = candidate_plan
        with self.state_lock:
            self.plan_payload = plan
            self.last_saved_root = map_path.parent
            self.last_broadcast_map_signature = ""
        self.broadcast({"type": "map", "t_ns": now_ns(), "map": payload, "plan": plan})
        self.broadcast(
            {
                "type": "event",
                "event": "map_loaded",
                "path": str(map_path),
                "status": self.status_payload(),
            }
        )

    @staticmethod
    def _sha256(path: Path) -> str:
        import hashlib

        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def _write_manifest(self, root: Path, mapper: Any, reason: str) -> None:
        files = {
            path.name: {"bytes": path.stat().st_size, "sha256": self._sha256(path)}
            for path in root.iterdir()
            if path.is_file() and path.name != "manifest.json"
        }
        payload = {
            "schema": "cca-robot-console-capture-v1",
            "run_id": root.name,
            "capture_source": "hardware",
            "status": "completed",
            "paper_edit": False,
            "started_at_ns": self.scan_started_ns or now_ns(),
            "stopped_at_ns": now_ns(),
            "devices": {"stm": "STM32", "lidar": "N10P", "camera": "Astra-S"},
            "transport": getattr(self.stm, "backend", "unavailable"),
            "control_interface": "body_velocity",
            "state_definition": ["x_m", "y_m", "theta_rad", "vx_mps", "vy_mps", "omega_radps"],
            "map": {
                "resolution_m": mapper.resolution_m,
                "lidar_mount_m": [mapper.lidar_x_m, mapper.lidar_y_m],
                "scans": mapper.scans,
                "points": mapper.points,
            },
            "save_reason": reason,
            "files": files,
        }
        (root / "manifest.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _planning_inflation_m() -> float:
        """Read the already-frozen robot footprint radius for A* inflation."""

        try:
            from shared import load_contract

            value = float(load_contract()["map"]["robot_radius_m"])
        except (ImportError, KeyError, TypeError, ValueError, OSError):
            raise RuntimeError("study contract robot_radius_m is unavailable") from None
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError("map contract robot_radius_m must be positive and finite")
        return value

    def plan_route(self, message: dict[str, Any]) -> None:
        """Plan a map-frame A* route without changing the motion controller."""

        from runtime.navigation import plan_navigation_path

        with self.state_lock:
            if self.mapper is None:
                raise RuntimeError("start and save a scan before planning")
            map_payload = self.mapper.payload()
            pose = self.pose.as_tuple() if self.pose is not None else (0.0, 0.0, 0.0)
        raw_goal = message.get("goal_xy", message.get("goal"))
        if not isinstance(raw_goal, (list, tuple)) or len(raw_goal) < 2:
            raise ValueError("plan requires goal_xy: [x_m, y_m]")
        raw_start = message.get("start_xy", message.get("start", pose[:2]))
        if not isinstance(raw_start, (list, tuple)) or len(raw_start) < 2:
            raise ValueError("start_xy must contain [x_m, y_m]")
        navigation = plan_navigation_path(
            map_payload,
            raw_start,
            raw_goal,
            inflation_m=float(message.get("inflation_m", self._planning_inflation_m())),
            unknown_is_occupied=bool(message.get("unknown_is_occupied", True)),
        )
        plan = navigation.occupancy_result.as_dict()
        plan["global_path_held_fixed"] = True
        plan["local_path_generation_count"] = navigation.path_state.local_generation_count
        plan["created_at_ns"] = now_ns()
        plan["map_frame"] = str(map_payload.get("frame_id", "map"))
        with self.state_lock:
            self.plan_payload = plan
            root = self.run_root
            mapper = self.mapper
        if root is not None:
            (root / "navigation_plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
            if mapper is not None:
                self._write_manifest(root, mapper, "astar_plan")
        self.broadcast({"type": "event", "event": "plan_ready", "plan": plan, "status": self.status_payload()})

    def clear_plan(self) -> None:
        with self.state_lock:
            self.plan_payload = None
            root = self.run_root
            mapper = self.mapper
        if root is not None:
            path = root / "navigation_plan.json"
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            if mapper is not None:
                self._write_manifest(root, mapper, "astar_plan_cleared")
        self.broadcast({"type": "event", "event": "plan_cleared", "status": self.status_payload()})

    def _apply_velocity(self, values: tuple[float, float, float]) -> None:
        if not all(math.isfinite(value) for value in values):
            raise ValueError("velocity must be finite")
        limits = (0.30, 0.30, 0.90)
        bounded = tuple(max(-limit, min(limit, value)) for value, limit in zip(values, limits))
        with self.state_lock:
            active = self.armed and self.stm is not None
            self.last_command_mono = time.monotonic()
            self.watchdog_zero_sent = False
        if active:
            self.stm.send_velocity(*bounded)
            with self.state_lock:
                self.last_command = bounded
                self.command_sequence += 1
                if self.files is not None:
                    self.files.control(now_ns(), bounded, self.stm.latest, self.command_sequence, getattr(self.stm, "backend", "serial"))
        else:
            self.send_zero()

    def handle(self, peer: Peer, message: dict[str, Any]) -> None:
        command = str(message.get("command", "")).strip().lower()
        try:
            if command == "arm":
                enabled = bool(message.get("enabled", False))
                with self.state_lock:
                    self.armed = enabled and self.stm is not None
                    self.status["armed"] = self.armed
                    self.last_command_mono = time.monotonic()
                    self.watchdog_zero_sent = False
                if not self.armed:
                    self.send_zero()
                self.broadcast({"type": "event", "event": "armed", "enabled": self.armed, "status": self.status_payload()})
            elif command == "velocity":
                values = tuple(float(message.get(name, 0.0)) for name in ("vx", "vy", "wz"))
                self._apply_velocity(values)
            elif command in {"move", "direction"}:
                speed = float(message.get("speed_mps", message.get("speed", 0.0)))
                yaw_speed = float(message.get("yaw_radps", message.get("yaw_speed", 0.0)))
                values = direction_velocity(str(message.get("direction", "")), speed, yaw_speed)
                self._apply_velocity(values)
            elif command in {"stop", "emergency_stop"}:
                self.disarm(command)
            elif command == "scan_start":
                self.start_scan()
            elif command in {"scan_save", "scan_stop"}:
                self.save_scan(command)
            elif command == "map_load":
                self.load_saved_map(message)
            elif command == "plan":
                self.plan_route(message)
            elif command in {"plan_clear", "clear_plan"}:
                self.clear_plan()
            elif command == "ping":
                peer.enqueue({"type": "pong", "t_ns": now_ns()})
            else:
                peer.enqueue({"type": "event", "event": "error", "message": "unknown command"})
        except Exception as error:
            if command not in {"plan", "plan_clear", "clear_plan", "map_load"}:
                self.disarm("command_error")
            peer.enqueue({"type": "event", "event": "error", "message": str(error)})

    def send_zero(self) -> None:
        if self.stm is not None:
            try:
                self.stm.send_velocity(*ZERO)
            except Exception as error:
                self._set_status("stm", "error", str(error))
        with self.state_lock:
            self.last_command = ZERO

    def disarm(self, reason: str) -> None:
        self.send_zero()
        with self.state_lock:
            self.armed = False
            self.status["armed"] = False
            self.last_command_mono = time.monotonic()
        self.broadcast({"type": "event", "event": "stopped", "reason": reason, "status": self.status_payload()})

    def _client_loop(self, peer: Peer) -> None:
        try:
            peer.sock.settimeout(None)
            file = peer.sock.makefile("rb")
            for line in file:
                if self.stop_event.is_set():
                    break
                if not line.strip():
                    continue
                try:
                    message = json.loads(line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    peer.enqueue({"type": "event", "event": "error", "message": "invalid message"})
                    continue
                if isinstance(message, dict):
                    self.handle(peer, message)
        except (ConnectionError, OSError):
            pass
        finally:
            with self.state_lock:
                self.peers.discard(peer)
                no_peers = not self.peers
            peer.close()
            if no_peers:
                self.disarm("client_disconnected")

    def broadcast(self, payload: dict[str, Any]) -> None:
        for peer in tuple(self.peers):
            peer.enqueue(payload)

    def _state_payload(self) -> dict[str, Any]:
        with self.state_lock:
            telemetry = self.stm.latest if self.stm is not None else None
            if telemetry is not None and self.pose is not None and telemetry.t_ns != self.last_telemetry_ns:
                self.pose.update(telemetry)
                self.last_telemetry_ns = telemetry.t_ns
                if self.files is not None:
                    self.files.state(now_ns(), self.pose, telemetry, getattr(self.stm, "backend", "serial"))
            if self.pose is not None and self.map_pose is None:
                self.map_pose = copy_pose_for_mapping(self.pose)
            pose = [0.0, 0.0, 0.0] if self.pose is None else list(self.pose.as_tuple())
            map_pose = pose if self.map_pose is None else list(self.map_pose.as_tuple())
            telemetry_payload = None
            if telemetry is not None:
                telemetry_payload = {
                    "t_ns": telemetry.t_ns,
                    "vx_mps": telemetry.vx_mps,
                    "vy_mps": telemetry.vy_mps,
                    "wz_radps": telemetry.wz_radps,
                    "voltage_v": telemetry.voltage_v,
                    "flag_stop": telemetry.flag_stop,
                }
            return {
                "type": "state",
                "t_ns": now_ns(),
                "pose": pose,
                "map_pose": map_pose,
                "telemetry": telemetry_payload,
                "status": self.status_payload(),
                "command": list(self.last_command),
                "camera_shape": self.camera_shape,
            }

    def _sensor_payload(self) -> dict[str, Any]:
        with self.state_lock:
            if self.lidar is not None:
                scan = self.lidar.latest
                if scan is not None and scan.t_ns != self.last_scan_ns:
                    self.last_scan_ns = scan.t_ns
                    self.latest_lidar = compact_points(scan.points)
                    if self.scan_active and self.mapper is not None and self.pose is not None:
                        # Scan matching is allowed to correct the pose used to
                        # place this scan, but must not overwrite the live
                        # odometry pose that drives the robot marker and state
                        # telemetry.  Keep the existing matcher and formulas;
                        # pass it a per-scan copy instead of the controller
                        # pose object shared with _state_payload().
                        map_pose = copy_pose_for_mapping(self.pose)
                        self.mapper.update(scan, map_pose)
                        self.map_pose = map_pose
                        if self.files is not None:
                            self.files.scan(scan)
                            self.files.context(scan.t_ns, self.pose, scan)
            return {"type": "lidar", "t_ns": now_ns(), "points": self.latest_lidar}

    def _map_payload(self) -> dict[str, Any] | None:
        with self.state_lock:
            if self.mapper is None:
                return None
            payload = self.mapper.payload()
            signature = f"{payload['width']}:{payload['height']}:{payload['metadata']['scans']}:{payload['metadata']['points']}:{json.dumps(self.plan_payload, sort_keys=True, separators=(',', ':'))}"
            if signature == self.last_broadcast_map_signature:
                return None
            self.last_broadcast_map_signature = signature
            return {"type": "map", "t_ns": now_ns(), "map": payload, "plan": self.plan_payload}

    def _camera_payload(self) -> dict[str, Any] | None:
        with self.state_lock:
            if self.latest_camera is None:
                return None
            return {"type": "camera", "t_ns": now_ns(), "jpeg": self.latest_camera, "shape": self.camera_shape}

    def loop(self) -> None:
        while not self.stop_event.wait(0.02):
            now = time.monotonic()
            watchdog_expired = False
            with self.state_lock:
                if self.armed and now - self.last_command_mono > 0.7 and not self.watchdog_zero_sent:
                    self.watchdog_zero_sent = True
                    watchdog_expired = True
            if watchdog_expired:
                # Keep the keyboard session armed so a short GUI/network stall
                # does not force an operator to re-arm.  Motion is still
                # stopped immediately, and disconnect/emergency-stop paths
                # continue to disarm the service.
                self.send_zero()
                self.broadcast({"type": "event", "event": "watchdog_zero", "status": self.status_payload()})
            if now - self.last_state_mono >= STATE_PERIOD_S:
                self.last_state_mono = now
                self.broadcast(self._state_payload())
            if now - self.last_sensor_mono >= SENSOR_PERIOD_S:
                self.last_sensor_mono = now
                self.broadcast(self._sensor_payload())
            if now - self.last_map_mono >= MAP_PERIOD_S:
                self.last_map_mono = now
                payload = self._map_payload()
                if payload is not None:
                    self.broadcast(payload)
            if now - self.last_camera_mono >= CAMERA_PERIOD_S:
                self.last_camera_mono = now
                payload = self._camera_payload()
                if payload is not None:
                    self.broadcast(payload)

    def serve(self) -> None:
        self.start_sources()
        loop_thread = threading.Thread(target=self.loop, name="robot-console-state", daemon=True)
        loop_thread.start()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.bind, self.port))
        self.server_socket.listen(4)
        self.server_socket.settimeout(0.5)
        print(f"Robot console service listening on {self.bind}:{self.port}")

        def request_shutdown(_signum: int, _frame: Any) -> None:
            # Let the main serving thread run close(), which disarms the robot
            # and finalizes an in-progress map.  Closing accept() here only
            # wakes that thread; no hardware work is performed in the signal
            # handler itself.
            self.stop_event.set()
            if self.server_socket is not None:
                try:
                    self.server_socket.close()
                except OSError:
                    pass

        previous_sigterm = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGTERM, request_shutdown)
        try:
            while not self.stop_event.is_set():
                try:
                    connection, address = self.server_socket.accept()
                except socket.timeout:
                    continue
                except OSError:
                    if self.stop_event.is_set():
                        break
                    raise
                peer = Peer(connection, f"{address[0]}:{address[1]}")
                with self.state_lock:
                    busy = bool(self.peers)
                    if not busy:
                        self.peers.add(peer)
                        # A new laptop client must receive the current saved or
                        # in-progress map even when no scan cell changed since
                        # the previous client disconnected.
                        self.last_broadcast_map_signature = ""
                if busy:
                    send_json(
                        connection,
                        peer.lock,
                        {
                            "type": "event",
                            "event": "error",
                            "message": "another control client is already connected",
                        },
                    )
                    connection.close()
                    continue
                peer.start_writer()
                peer.enqueue({"type": "hello", "app": "robot-console", "status": self.status_payload()})
                threading.Thread(target=self._client_loop, args=(peer,), name="robot-console-client", daemon=True).start()
        except KeyboardInterrupt:
            pass
        finally:
            signal.signal(signal.SIGTERM, previous_sigterm)
            self.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.stop_event.set()
        self.disarm("service_shutdown")
        if self.scan_active:
            self.save_scan("service_shutdown")
        if self.camera is not None:
            try:
                self.camera.stop()
            except Exception:
                pass
        if self.lidar is not None:
            try:
                self.lidar.stop()
            except Exception:
                pass
        if self.stm is not None:
            try:
                self.stm.stop()
            except Exception:
                pass
        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except OSError:
                pass
        for peer in tuple(self.peers):
            peer.close()
        self.peers.clear()


class ConsoleApp:
    def __init__(self, host: str, port: int) -> None:
        import tkinter as tk
        from tkinter import filedialog, ttk

        self.tk = tk
        self.ttk = ttk
        self.filedialog = filedialog
        self.root = tk.Tk()
        self.root.title("Mecanum Robot Console")
        self.root.geometry("1480x900")
        self.root.minsize(1200, 760)
        self.host = tk.StringVar(value=host)
        self.port = tk.IntVar(value=port)
        self.connection_text = tk.StringVar(value="Disconnected")
        self.speed = tk.DoubleVar(value=0.20)
        self.yaw_speed = tk.DoubleVar(value=0.60)
        self.armed = False
        self.sock: socket.socket | None = None
        self.socket_lock = threading.Lock()
        self.reader_thread: threading.Thread | None = None
        self.reader_stop = threading.Event()
        self.messages: queue.Queue[dict[str, Any]] = queue.Queue()
        self.state: dict[str, Any] = {}
        self.lidar: list[list[float]] = []
        self.map_payload: dict[str, Any] | None = None
        self.saved_map_view = False
        self.map_view_initialized = False
        self.view_bounds: tuple[float, float, float, float] | None = None
        self.camera_image: Any = None
        self.last_saved_path: str | None = None
        self.map_goal_xy: tuple[float, float] | None = None
        self.planned_path: list[tuple[float, float]] = []
        self.plan_status = "No A* plan"
        self.follow_robot = tk.BooleanVar(value=True)
        self.map_view_text = tk.StringVar(value="LIVE MAP · MAP-FRAME ROBOT POSE")
        self.target_pose: tuple[float, float, float] | None = None
        self.target_map_pose: tuple[float, float, float] | None = None
        self.display_pose: tuple[float, float, float] | None = None
        self.last_display_mono = time.monotonic()
        self.keys: set[str] = set()
        self.button_keys: set[str] = set()
        self.trace: list[tuple[float, float]] = []
        self._build()
        self.root.bind_all("<KeyPress>", self._key_down)
        self.root.bind_all("<KeyRelease>", self._key_up)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(60, self._tick)
        if host.strip().lower() not in {"", "127.0.0.1", "localhost"}:
            self.root.after(300, self.connect)

    def _build(self) -> None:
        tk, ttk = self.tk, self.ttk
        outer = ttk.Frame(self.root, padding=8)
        outer.pack(fill="both", expand=True)
        control = ttk.Frame(outer, width=300)
        control.pack(side="left", fill="y", padx=(0, 8))
        control.pack_propagate(False)
        ttk.Label(control, text="MECANUM ROBOT", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 12))
        connection = ttk.LabelFrame(control, text="Connection", padding=8)
        connection.pack(fill="x", pady=(0, 8))
        ttk.Label(connection, text="Jetson host").grid(row=0, column=0, sticky="w")
        ttk.Entry(connection, textvariable=self.host, width=18).grid(row=1, column=0, sticky="ew", pady=(2, 5))
        ttk.Label(connection, text="Port").grid(row=2, column=0, sticky="w")
        ttk.Entry(connection, textvariable=self.port, width=8).grid(row=3, column=0, sticky="ew", pady=(2, 5))
        ttk.Button(connection, text="Connect", command=self.connect).grid(row=4, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(connection, text="Disconnect", command=self.disconnect).grid(row=4, column=1, sticky="ew", padx=(3, 0))
        connection.columnconfigure(0, weight=1)
        connection.columnconfigure(1, weight=1)
        ttk.Label(control, textvariable=self.connection_text, foreground="#2f80ed").pack(anchor="w", pady=(0, 8))
        safety = ttk.LabelFrame(control, text="Safety", padding=8)
        safety.pack(fill="x", pady=(0, 8))
        ttk.Button(safety, text="EMERGENCY STOP", command=self.emergency_stop).pack(fill="x")
        motion = ttk.LabelFrame(control, text="Teleoperation", padding=8)
        motion.pack(fill="x", pady=(0, 8))
        ttk.Label(motion, text="Speed (m/s)").pack(anchor="w")
        ttk.Scale(motion, variable=self.speed, from_=0.05, to=0.30, orient="horizontal").pack(fill="x")
        ttk.Label(motion, text="Yaw (rad/s)").pack(anchor="w", pady=(6, 0))
        ttk.Scale(motion, variable=self.yaw_speed, from_=0.10, to=0.90, orient="horizontal").pack(fill="x")
        ttk.Label(motion, text="Mecanum directions (hold)", foreground="#4f5b66").pack(anchor="w", pady=(8, 0))
        grid = ttk.Frame(motion)
        grid.pack(pady=(8, 0))
        buttons = (
            ("↖", frozenset({"w", "a"}), 0, 0),
            ("↑", frozenset({"w"}), 0, 1),
            ("↗", frozenset({"w", "d"}), 0, 2),
            ("←", frozenset({"a"}), 1, 0),
            ("■", frozenset({"x"}), 1, 1),
            ("→", frozenset({"d"}), 1, 2),
            ("↙", frozenset({"s", "a"}), 2, 0),
            ("↓", frozenset({"s"}), 2, 1),
            ("↘", frozenset({"s", "d"}), 2, 2),
        )
        for label, keys, row, column in buttons:
            button = ttk.Button(grid, text=label, width=5)
            button.grid(row=row, column=column, padx=2, pady=2)
            button.bind("<ButtonPress-1>", lambda _event, k=keys: self._button_down(k))
            button.bind("<ButtonRelease-1>", lambda _event, k=keys: self._button_up(k))
        rotation = ttk.Frame(motion)
        rotation.pack(fill="x", pady=(5, 0))
        rotate_left = ttk.Button(rotation, text="↺ Rotate left", width=13)
        rotate_left.pack(side="left", expand=True, fill="x", padx=(0, 2))
        rotate_left.bind("<ButtonPress-1>", lambda _event: self._button_down(frozenset({"q"})))
        rotate_left.bind("<ButtonRelease-1>", lambda _event: self._button_up(frozenset({"q"})))
        rotate_right = ttk.Button(rotation, text="↻ Rotate right", width=13)
        rotate_right.pack(side="left", expand=True, fill="x", padx=(2, 0))
        rotate_right.bind("<ButtonPress-1>", lambda _event: self._button_down(frozenset({"e"})))
        rotate_right.bind("<ButtonRelease-1>", lambda _event: self._button_up(frozenset({"e"})))
        ttk.Label(motion, text="Keyboard: W/S/A/D + diagonals; Q/E rotate; Space/X stop", wraplength=270).pack(anchor="w", pady=(6, 0))
        mapping = ttk.LabelFrame(control, text="Map capture", padding=8)
        mapping.pack(fill="x", pady=(0, 8))
        ttk.Button(mapping, text="Start scan", command=lambda: self.send({"command": "scan_start"})).pack(fill="x", pady=(0, 4))
        ttk.Button(mapping, text="Save map and data", command=lambda: self.send({"command": "scan_save"})).pack(fill="x", pady=(0, 4))
        ttk.Button(mapping, text="View last saved map", command=self.load_saved_map).pack(fill="x", pady=(0, 4))
        ttk.Button(mapping, text="Open local map.json", command=self.open_local_map).pack(fill="x", pady=(0, 4))
        ttk.Button(mapping, text="Stop scan", command=lambda: self.send({"command": "scan_stop"})).pack(fill="x")
        navigation = ttk.LabelFrame(control, text="Navigation (A*)", padding=8)
        navigation.pack(fill="x", pady=(0, 8))
        ttk.Label(
            navigation,
            text="Left-click the map to set a goal. Start = current robot pose.",
            wraplength=270,
        ).pack(anchor="w", pady=(0, 5))
        ttk.Button(navigation, text="Plan shortest path (A*)", command=self.plan_route).pack(fill="x", pady=(0, 4))
        ttk.Button(navigation, text="Clear planned path", command=self.clear_plan).pack(fill="x")
        self.plan_text = ttk.Label(navigation, textvariable=tk.StringVar(value=self.plan_status), foreground="#7b61ff", wraplength=270)
        self.plan_text.pack(anchor="w", pady=(5, 0))
        self.info = tk.Text(control, height=12, width=34, state="disabled", background="#f4f6f8", relief="flat")
        self.info.pack(fill="both", expand=True)
        views = ttk.Frame(outer)
        views.pack(side="left", fill="both", expand=True)
        view_toolbar = ttk.Frame(views)
        view_toolbar.pack(fill="x", pady=(0, 5))
        ttk.Label(view_toolbar, textvariable=self.map_view_text, font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Checkbutton(
            view_toolbar,
            text="Follow robot",
            variable=self.follow_robot,
            command=self._reset_map_view,
        ).pack(side="right")
        upper = ttk.Frame(views)
        upper.pack(fill="both", expand=True)
        map_frame = ttk.LabelFrame(upper, text="2D map / lidar / robot pose", padding=4)
        map_frame.pack(fill="both", expand=True)
        self.map_canvas = tk.Canvas(map_frame, background="#101820", highlightthickness=0)
        self.map_canvas.pack(fill="both", expand=True)
        self.map_canvas.bind("<Button-1>", self._map_click)
        self.map_canvas.bind("<Button-3>", lambda _event: self.clear_goal())
        camera_frame = ttk.LabelFrame(views, text="Astra-S camera", padding=4)
        camera_frame.pack(fill="x", pady=(5, 0))
        self.camera_label = ttk.Label(camera_frame, text="Camera stream unavailable", anchor="center")
        self.camera_label.pack(fill="x", ipady=4)

    def connect(self) -> None:
        self.disconnect()
        try:
            sock = socket.create_connection((self.host.get().strip(), int(self.port.get())), timeout=3.0)
            sock.settimeout(None)
            self.sock = sock
            self.reader_stop.clear()
            self.reader_thread = threading.Thread(target=self._reader, args=(sock,), name="console-reader", daemon=True)
            self.reader_thread.start()
            self.connection_text.set(f"Connected to {self.host.get().strip()}:{self.port.get()}")
            self.send({"command": "ping"})
        except Exception as error:
            self.connection_text.set(f"Connection failed: {error}")
            self.sock = None

    def disconnect(self) -> None:
        old_thread = self.reader_thread
        self.reader_stop.set()
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None
        self.reader_thread = None
        self.armed = False
        self.keys.clear()
        self.button_keys.clear()
        self.target_pose = None
        self.target_map_pose = None
        self.display_pose = None
        self.saved_map_view = False
        self.trace.clear()
        self.view_bounds = None
        self.map_view_initialized = False
        if old_thread is not None and old_thread is not threading.current_thread():
            old_thread.join(timeout=0.5)

    def _reader(self, sock: socket.socket) -> None:
        try:
            stream = sock.makefile("rb")
            for line in stream:
                if self.reader_stop.is_set():
                    break
                if line.strip():
                    try:
                        message = json.loads(line.decode("utf-8"))
                        if isinstance(message, dict):
                            self.messages.put(message)
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        self.messages.put({"type": "event", "event": "error", "message": "invalid server message"})
        except (ConnectionError, OSError):
            self.messages.put(
                {
                    "type": "event",
                    "event": "disconnect",
                    "message": "server disconnected",
                    "socket_id": id(sock),
                }
            )

    def send(self, payload: dict[str, Any]) -> None:
        if self.sock is None:
            return
        try:
            send_json(self.sock, self.socket_lock, payload)
        except (ConnectionError, OSError):
            self.connection_text.set("Disconnected")

    def plan_route(self) -> None:
        if self.map_goal_xy is None:
            self.plan_status = "Select a goal with left-click on the map"
            self.plan_text.configure(text=self.plan_status)
            return
        self.plan_status = f"Planning to ({self.map_goal_xy[0]:.2f}, {self.map_goal_xy[1]:.2f})..."
        self.plan_text.configure(text=self.plan_status)
        self.send({"command": "plan", "goal_xy": [self.map_goal_xy[0], self.map_goal_xy[1]]})

    def clear_plan(self) -> None:
        self.planned_path = []
        self.plan_status = "No A* plan"
        self.plan_text.configure(text=self.plan_status)
        self.send({"command": "plan_clear"})

    def clear_goal(self) -> None:
        self.map_goal_xy = None
        self.clear_plan()

    def _reset_map_view(self) -> None:
        self.map_view_initialized = False
        self.view_bounds = None

    def _screen_to_world(self, x: float, y: float) -> tuple[float, float]:
        canvas_width = max(10, self.map_canvas.winfo_width())
        canvas_height = max(10, self.map_canvas.winfo_height())
        xmin, ymin, xmax, ymax = self._world_bounds()
        scale = min(
            (canvas_width - 30) / max(xmax - xmin, 0.1),
            (canvas_height - 30) / max(ymax - ymin, 0.1),
        )
        return (
            float(xmin + (float(x) - 15.0) / max(scale, 1.0e-12)),
            float(ymin + (canvas_height - 15.0 - float(y)) / max(scale, 1.0e-12)),
        )

    def _map_click(self, event: Any) -> None:
        self.map_goal_xy = self._screen_to_world(event.x, event.y)
        self.plan_status = f"Goal: ({self.map_goal_xy[0]:.2f}, {self.map_goal_xy[1]:.2f})"
        self.plan_text.configure(text=self.plan_status)

    def emergency_stop(self) -> None:
        self.keys.clear()
        self.button_keys.clear()
        self.armed = False
        self.send({"command": "emergency_stop"})

    def load_saved_map(self) -> None:
        """Ask Jetson to stream its newest saved map package."""

        self.send({"command": "map_load"})

    @staticmethod
    def _validate_map_payload(payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("map.json must contain an object")
        width = int(payload.get("width", 0))
        height = int(payload.get("height", 0))
        occupancy = payload.get("occupancy")
        if width <= 0 or height <= 0 or not isinstance(occupancy, list) or len(occupancy) < width * height:
            raise ValueError("map dimensions or occupancy data are invalid")
        return payload

    def open_local_map(self) -> None:
        """Open a map.json copied from Jetson or another saved run."""

        path = self.filedialog.askopenfilename(
            title="Open saved map",
            filetypes=(("Map JSON", "map.json"), ("JSON files", "*.json"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            payload = self._validate_map_payload(json.loads(Path(path).read_text(encoding="utf-8")))
            self.map_payload = payload
            self.saved_map_view = True
            self.last_saved_path = path
            self.map_view_initialized = False
            self.view_bounds = None
            self.map_goal_xy = None
            self.planned_path = []
            self.trace.clear()
            self.plan_status = "Loaded map; select a goal for A*"
            self.plan_text.configure(text=self.plan_status)
            self.connection_text.set(f"Map loaded: {Path(path).name}")
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
            self.connection_text.set(f"Map open failed: {error}")

    @staticmethod
    def _normalize_input_keys(keys: str | set[str] | frozenset[str]) -> set[str]:
        return {keys} if isinstance(keys, str) else set(keys)

    def _active_keys(self) -> set[str]:
        return self.keys | self.button_keys

    def _button_down(self, keys: str | set[str] | frozenset[str]) -> None:
        pressed = self._normalize_input_keys(keys)
        if "x" in pressed:
            self.emergency_stop()
            return
        self.button_keys.update(pressed)

    def _button_up(self, keys: str | set[str] | frozenset[str]) -> None:
        self.button_keys.difference_update(self._normalize_input_keys(keys))
        if self.armed and not self._active_keys():
            self.send({"command": "velocity", "vx": 0.0, "vy": 0.0, "wz": 0.0})

    def _key_down(self, event: Any) -> None:
        if str(event.widget.winfo_class()).lower() in {"entry", "tentry", "scale", "tscale"}:
            return
        key = str(event.keysym).lower()
        aliases = {"up": "w", "down": "s", "left": "a", "right": "d", "space": "x"}
        key = aliases.get(key, key)
        if key == "x":
            self.emergency_stop()
        elif key in {"w", "s", "a", "d", "q", "e"}:
            self.keys.add(key)

    def _key_up(self, event: Any) -> None:
        if str(event.widget.winfo_class()).lower() in {"entry", "tentry", "scale", "tscale"}:
            return
        key = str(event.keysym).lower()
        aliases = {"up": "w", "down": "s", "left": "a", "right": "d"}
        key = aliases.get(key, key)
        self.keys.discard(key)

    def _command_from_keys(self, keys: set[str]) -> tuple[float, float, float]:
        speed = float(self.speed.get())
        yaw = float(self.yaw_speed.get())
        vx = speed * (int("w" in keys) - int("s" in keys))
        vy = speed * (int("a" in keys) - int("d" in keys))
        wz = yaw * (int("q" in keys) - int("e" in keys))
        return vx, vy, wz

    def _tick(self) -> None:
        while True:
            try:
                message = self.messages.get_nowait()
            except queue.Empty:
                break
            self._message(message)
        self._update_display_pose()
        self._update_info()
        active_keys = self._active_keys()
        if self.armed and active_keys:
            command = self._command_from_keys(active_keys)
            self.send({"command": "velocity", "vx": command[0], "vy": command[1], "wz": command[2]})
        elif self.armed and not active_keys:
            self.send({"command": "velocity", "vx": 0.0, "vy": 0.0, "wz": 0.0})
        self._draw_map()
        self.root.after(60, self._tick)

    def _update_display_pose(self) -> None:
        if self.target_pose is None:
            return
        now = time.monotonic()
        dt_s = max(0.0, min(now - self.last_display_mono, 1.0))
        self.last_display_mono = now
        self.display_pose = smooth_display_pose(self.display_pose, self.target_pose, dt_s)
        trace_pose = self.target_map_pose or self.display_pose
        if trace_pose is not None:
            if not self.trace or math.hypot(
                trace_pose[0] - self.trace[-1][0],
                trace_pose[1] - self.trace[-1][1],
            ) > 0.01:
                self.trace.append(trace_pose[:2])
                self.trace = self.trace[-1000:]

    def _update_info(self) -> None:
        status = self.state.get("status") or {}
        telemetry = self.state.get("telemetry") or {}
        pose = self.target_map_pose or self.display_pose or self.target_pose or (0.0, 0.0, 0.0)
        odom_pose = self.target_pose or pose
        self.map_view_text.set(
            f"{'SAVED MAP' if self.saved_map_view else 'LIVE MAP'} · "
            f"MAP POSE ({'follow' if self.follow_robot.get() else 'fixed view'})"
        )
        map_payload = self.map_payload or {}
        map_metadata = map_payload.get("metadata") or {}
        map_scans = map_metadata.get("scans")
        map_points = map_metadata.get("points")
        raw_command = self.state.get("command")
        try:
            command = tuple(float(raw_command[index]) for index in range(3))
        except (TypeError, ValueError, IndexError):
            command = ZERO
        if map_scans is not None and map_points is not None:
            map_summary = (
                f"Map: live ({int(map_scans)} scans, {int(map_points)} points, "
                f"{int(map_payload.get('width', 0))}x{int(map_payload.get('height', 0))})"
            )
        else:
            map_summary = f"Map: {Path(self.last_saved_path).name if self.last_saved_path else 'not saved'}"
        lines = [
            f"STM: {status.get('stm', 'offline')}",
            f"N10P: {status.get('lidar', 'offline')}",
            f"Astra-S: {status.get('camera', 'disabled')}",
            f"Motion: {'armed' if status.get('armed', self.armed) else 'disarmed'}",
            f"Scan: {status.get('scan', 'idle')}",
            f"Map pose: {float(pose[0]):.2f}, {float(pose[1]):.2f}, {float(pose[2]):.2f}",
            f"Odom pose: {float(odom_pose[0]):.2f}, {float(odom_pose[1]):.2f}, {float(odom_pose[2]):.2f}",
            f"Velocity: {float(telemetry.get('vx_mps', 0.0)):.2f}, {float(telemetry.get('vy_mps', 0.0)):.2f}, {float(telemetry.get('wz_radps', 0.0)):.2f}",
            f"Command: {command[0]:.2f}, {command[1]:.2f}, {command[2]:.2f}",
            f"Battery: {float(telemetry.get('voltage_v', 0.0)):.2f} V",
            f"Laser points: {len(self.lidar)}",
            f"View: {'saved map' if self.saved_map_view else 'live scan'}",
            map_summary,
            f"A*: {self.plan_status}",
        ]
        self.info.configure(state="normal")
        self.info.delete("1.0", "end")
        self.info.insert("1.0", "\n".join(lines))
        self.info.configure(state="disabled")

    def _message(self, message: dict[str, Any]) -> None:
        kind = message.get("type")
        if kind == "state":
            self.state = message
            pose = message.get("pose") or [0.0, 0.0, 0.0]
            if len(pose) >= 3:
                try:
                    self.target_pose = (float(pose[0]), float(pose[1]), float(pose[2]))
                except (TypeError, ValueError):
                    self.target_pose = None
            map_pose = message.get("map_pose") or pose
            if len(map_pose) >= 3:
                try:
                    self.target_map_pose = (float(map_pose[0]), float(map_pose[1]), float(map_pose[2]))
                except (TypeError, ValueError):
                    self.target_map_pose = self.target_pose
        elif kind == "lidar":
            self.lidar = message.get("points") or []
        elif kind == "map":
            incoming_map = message.get("map")
            if incoming_map is not self.map_payload:
                if self.map_payload is None and incoming_map is not None:
                    self.map_view_initialized = False
                self.map_payload = incoming_map
            self._set_plan(message.get("plan"))
        elif kind == "camera":
            self._show_camera(message.get("jpeg"))
        elif kind == "hello":
            self.connection_text.set("Connected")
            # The GUI has no separate motion-enable control.  The service
            # still gates actuation on a live STM connection and retains its
            # emergency-stop/disconnect interlocks.
            self.send({"command": "arm", "enabled": True})
        elif kind == "event":
            event = str(message.get("event", ""))
            if event == "disconnect":
                socket_id = message.get("socket_id")
                is_current_socket = socket_id is None or (self.sock is not None and socket_id == id(self.sock))
                if is_current_socket:
                    self.disconnect()
            if event == "armed":
                self.armed = bool(message.get("enabled"))
            elif event == "stopped":
                self.armed = False
            elif event == "scan_saved":
                path = str(message.get("path", ""))
                if path:
                    self.last_saved_path = path
                    self.connection_text.set(f"Map saved: {path}")
            elif event == "map_loaded":
                path = str(message.get("path", ""))
                if path:
                    self.last_saved_path = path
                self.saved_map_view = True
                self.map_view_initialized = False
                self.view_bounds = None
                self.trace.clear()
                self.connection_text.set(f"Saved map loaded: {Path(path).name if path else 'latest'}")
            elif event == "scan_started":
                self.map_payload = None
                self.saved_map_view = False
                self.map_view_initialized = False
                self.view_bounds = None
                self.planned_path = []
                self.map_goal_xy = None
                self.plan_status = "No A* plan"
                self.plan_text.configure(text=self.plan_status)
            elif event == "plan_ready":
                self._set_plan(message.get("plan"))
            elif event == "plan_cleared":
                self._set_plan(None)
            status = message.get("status")
            if status:
                self.state["status"] = status
            # Keep the connection indicator stable for internal arm/watchdog
            # events; those are no longer exposed as a user-facing control.
            if event not in {"armed", "watchdog_zero", "scan_saved", "plan_ready", "plan_cleared"}:
                self.connection_text.set(str(message.get("message", event)))

    def _set_plan(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            self.planned_path = []
            self.plan_status = "No A* plan"
            self.plan_text.configure(text=self.plan_status)
            return
        raw_path = payload.get("path_xy")
        if not isinstance(raw_path, list) or len(raw_path) < 2:
            self.planned_path = []
            self.plan_status = "A* returned no usable path"
            self.plan_text.configure(text=self.plan_status)
            return
        try:
            path = [(float(point[0]), float(point[1])) for point in raw_path if len(point) >= 2]
        except (TypeError, ValueError, IndexError):
            path = []
        if len(path) < 2 or not all(math.isfinite(x) and math.isfinite(y) for x, y in path):
            self.planned_path = []
            self.plan_status = "A* returned an invalid path"
            self.plan_text.configure(text=self.plan_status)
            return
        self.planned_path = path
        self.map_goal_xy = path[-1]
        self.plan_status = (
            f"A* ready: {len(path)} points, "
            f"expanded {int(payload.get('expanded_nodes', 0))}"
        )
        self.plan_text.configure(text=self.plan_status)

    def _show_camera(self, encoded: Any) -> None:
        if not encoded:
            return
        try:
            from PIL import Image, ImageTk

            image = Image.open(io.BytesIO(base64.b64decode(encoded)))
            image.thumbnail((560, 240))
            self.camera_image = ImageTk.PhotoImage(image)
            self.camera_label.configure(image=self.camera_image, text="")
        except Exception as error:
            self.camera_label.configure(text=f"Camera decode failed: {error}", image="")

    def _world_bounds(self) -> tuple[float, float, float, float]:
        def stable_bounds(bounds: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
            xmin, ymin, xmax, ymax = bounds
            # A freshly started scan contains a 1x1 unknown map. Without a
            # minimum view span the robot marker is scaled to fill the canvas.
            minimum_span = 2.0
            center_x = 0.5 * (xmin + xmax)
            center_y = 0.5 * (ymin + ymax)
            span_x = max(xmax - xmin, minimum_span)
            span_y = max(ymax - ymin, minimum_span)
            return (
                center_x - 0.5 * span_x,
                center_y - 0.5 * span_y,
                center_x + 0.5 * span_x,
                center_y + 0.5 * span_y,
            )

        pose = self.target_map_pose or self.display_pose or self.target_pose or (0.0, 0.0, 0.0)
        if self.follow_robot and pose is not None:
            self.map_view_initialized = False
            px, py = float(pose[0]), float(pose[1])
            span = DISPLAY_VIEW_SPAN_M
            return px - 0.5 * span, py - 0.5 * span, px + 0.5 * span, py + 0.5 * span

        if self.map_payload:
            width = int(self.map_payload.get("width", 1))
            height = int(self.map_payload.get("height", 1))
            resolution = float(self.map_payload.get("resolution_m", 0.05))
            origin = self.map_payload.get("origin", [0.0, 0.0, 0.0])
            if width > 0 and height > 0 and math.isfinite(resolution) and resolution > 0.0 and len(origin) >= 2:
                map_bounds = stable_bounds(
                    (
                        float(origin[0]),
                        float(origin[1]),
                        float(origin[0]) + width * resolution,
                        float(origin[1]) + height * resolution,
                    )
                )
                if not self.map_view_initialized or self.view_bounds is None:
                    self.view_bounds = map_bounds
                    self.map_view_initialized = True
                else:
                    xmin, ymin, xmax, ymax = self.view_bounds
                    self.view_bounds = stable_bounds(
                        (
                            min(xmin, map_bounds[0]),
                            min(ymin, map_bounds[1]),
                            max(xmax, map_bounds[2]),
                            max(ymax, map_bounds[3]),
                        )
                    )
                return self.view_bounds

        self.map_view_initialized = False
        px, py = float(pose[0]), float(pose[1])
        span = DISPLAY_VIEW_SPAN_M
        if self.view_bounds is None:
            self.view_bounds = (
                px - 0.5 * span,
                py - 0.5 * span,
                px + 0.5 * span,
                py + 0.5 * span,
            )
        else:
            xmin, ymin, xmax, ymax = self.view_bounds
            span_x = max(xmax - xmin, span)
            span_y = max(ymax - ymin, span)
            margin_x = 0.25 * span_x
            margin_y = 0.25 * span_y
            if px < xmin + margin_x or px > xmax - margin_x:
                xmin, xmax = px - 0.5 * span_x, px + 0.5 * span_x
            if py < ymin + margin_y or py > ymax - margin_y:
                ymin, ymax = py - 0.5 * span_y, py + 0.5 * span_y
            self.view_bounds = (xmin, ymin, xmax, ymax)
        return self.view_bounds

    def _draw_map(self) -> None:
        canvas = self.map_canvas
        canvas.delete("all")
        width = max(10, canvas.winfo_width())
        height = max(10, canvas.winfo_height())
        xmin, ymin, xmax, ymax = self._world_bounds()
        scale = min((width - 30) / max(xmax - xmin, 0.1), (height - 30) / max(ymax - ymin, 0.1))
        def point(x: float, y: float) -> tuple[float, float]:
            return 15.0 + (x - xmin) * scale, height - 15.0 - (y - ymin) * scale
        canvas.create_line(*point(xmin, 0.0), *point(xmax, 0.0), fill="#263746", tags="grid")
        canvas.create_line(*point(0.0, ymin), *point(0.0, ymax), fill="#263746", tags="grid")
        if self.map_payload:
            resolution = float(self.map_payload.get("resolution_m", 0.05))
            origin = self.map_payload.get("origin", [0.0, 0.0, 0.0])
            mw = int(self.map_payload.get("width", 0))
            mh = int(self.map_payload.get("height", 0))
            occupancy = self.map_payload.get("occupancy", [])
            if mw <= 0 or mh <= 0 or len(origin) < 2:
                occupancy = []
            for index, value in enumerate(occupancy[: max(0, mw * mh)]):
                if value == -1:
                    continue
                cell_x = index % mw
                cell_y = index // mw
                x0, y0 = point(float(origin[0]) + cell_x * resolution, float(origin[1]) + cell_y * resolution)
                x1, y1 = point(float(origin[0]) + (cell_x + 1) * resolution, float(origin[1]) + (cell_y + 1) * resolution)
                color = "#e05252" if value == 100 else "#263b49"
                canvas.create_rectangle(x0, y1, x1, y0, fill=color, outline="", tags="map")
        if len(self.trace) > 1:
            canvas.create_line([coordinate for xy in self.trace for coordinate in point(*xy)], fill="#f2c94c", width=2, tags="trace")
        if len(self.planned_path) > 1:
            canvas.create_line(
                [coordinate for xy in self.planned_path for coordinate in point(*xy)],
                fill="#b18cff",
                width=3,
                dash=(8, 3),
                tags="astar",
            )
        if self.map_goal_xy is not None:
            gx, gy = point(*self.map_goal_xy)
            canvas.create_oval(
                gx - 7,
                gy - 7,
                gx + 7,
                gy + 7,
                fill="#b18cff",
                outline="#ffffff",
                width=2,
                tags="goal",
            )
            canvas.create_text(gx + 10, gy - 10, anchor="sw", fill="#d9c9ff", text="A* goal", tags="goal")
        # The marker must use the same map-frame pose that placed the latest
        # lidar scan.  Using raw odometry here makes the marker disagree with
        # a scan-matched map and can make a moving robot appear stationary.
        pose = list(self.target_map_pose or self.display_pose or self.target_pose or self.state.get("pose", [0.0, 0.0, 0.0]))
        px, py, yaw = (float(value) for value in (pose + [0.0, 0.0, 0.0])[:3])
        rx, ry = point(px, py)
        corners = []
        for cx, cy in ((0.20, 0.20), (0.20, -0.20), (-0.20, -0.20), (-0.20, 0.20)):
            x = px + math.cos(yaw) * cx - math.sin(yaw) * cy
            y = py + math.sin(yaw) * cx + math.cos(yaw) * cy
            corners.extend(point(x, y))
        canvas.create_polygon(corners, fill="#2f80ed", outline="#b9dcff", tags="robot")
        canvas.create_line(rx, ry, *point(px + 0.35 * math.cos(yaw), py + 0.35 * math.sin(yaw)), fill="#ffffff", width=2, tags="robot")
        if not self.saved_map_view:
            for angle, distance in self.lidar:
                lx = px + 0.10 * math.cos(yaw) - 0.0 * math.sin(yaw) + distance * math.cos(yaw + angle)
                ly = py + 0.10 * math.sin(yaw) + distance * math.sin(yaw + angle)
                canvas.create_line(rx, ry, *point(lx, ly), fill="#48d597", width=1, tags="lidar")
        else:
            canvas.create_text(18, 38, anchor="nw", fill="#b9dcff", text="saved map · live pose overlay", tags="label")
        canvas.create_text(18, 16, anchor="nw", fill="#d6e4ef", text=f"map pose  x={px:.2f}  y={py:.2f}  yaw={yaw:.2f}", tags="label")

    def close(self) -> None:
        self.emergency_stop()
        self.disconnect()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def self_test() -> None:
    from hardware import LidarPoint, LidarScan, N10PDecoder, N10P_PROTOCOL_PROFILE
    from manual_map import OccupancyMap, Pose
    from simulation.occupancy_astar import plan_occupancy_map

    direction_cases = {
        "forward": (0.2, 0.0, 0.0),
        "backward": (-0.2, 0.0, 0.0),
        "left": (0.0, 0.2, 0.0),
        "right": (0.0, -0.2, 0.0),
        "forward_left": (0.2, 0.2, 0.0),
        "forward_right": (0.2, -0.2, 0.0),
        "backward_left": (-0.2, 0.2, 0.0),
        "backward_right": (-0.2, -0.2, 0.0),
        "rotate_left": (0.0, 0.0, 0.6),
        "rotate_right": (0.0, 0.0, -0.6),
        "stop": (0.0, 0.0, 0.0),
    }
    for direction, expected in direction_cases.items():
        if direction_velocity(direction, 0.2, 0.6) != expected:
            raise AssertionError(f"direction mapping failed for {direction}")

    mapper = OccupancyMap(0.05, lidar_x_m=0.10, lidar_y_m=0.0, lidar_yaw_rad=0.0, min_range_m=0.05, max_range_m=8.0, padding_cells=2)
    scan = LidarScan(1, (LidarPoint(1, 0.0, 1.0, 10, 0), LidarPoint(1, math.pi / 2.0, 0.5, 10, 0)))
    mapper.update(scan, Pose())
    payload = mapper.payload()
    if payload["width"] < 3 or payload["height"] < 3 or 100 not in payload["occupancy"]:
        raise AssertionError("map self-test failed")
    plan = plan_occupancy_map(
        {
            "width": 20,
            "height": 20,
            "resolution_m": 0.20,
            "origin": [-2.0, -2.0, 0.0],
            "occupancy": [0] * 400,
        },
        (-1.0, -1.0),
        (1.0, 1.0),
        inflation_m=0.10,
    )
    if plan.status != "ASTAR_SUCCESS" or len(plan.path_xy) < 2:
        raise AssertionError("A* map self-test failed")
    if N10PDecoder(N10P_PROTOCOL_PROFILE).packet_size != 108:
        raise AssertionError("N10P self-test failed")
    if openni_directory() is None:
        raise AssertionError("OpenNI2 redist self-test failed")
    print("robot_console self-test: PASS")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Mecanum robot monitor, teleoperation and mapping console")
    result.add_argument("--server", action="store_true", help="run the hardware service on the Jetson")
    result.add_argument("--self-test", action="store_true")
    result.add_argument("--host", default=os.environ.get("CCA_ROBOT_HOST", "127.0.0.1"))
    result.add_argument("--port", type=int, default=int(os.environ.get("CCA_ROBOT_PORT", APP_PORT)))
    result.add_argument("--bind", default=os.environ.get("CCA_ROBOT_BIND", "0.0.0.0"))
    return result


def main() -> int:
    args = parser().parse_args()
    if args.self_test:
        self_test()
        return 0
    if not 1024 <= args.port <= 65535:
        raise ValueError("port must be between 1024 and 65535")
    if args.server:
        RobotService(args.bind, args.port).serve()
    else:
        ConsoleApp(args.host, args.port).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
