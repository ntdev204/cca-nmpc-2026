from __future__ import annotations

import argparse
import base64
import io
import json
import math
import os
import platform
import queue
import socket
import threading
import time
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
CAMERA_PERIOD_S = 0.20


def now_ns() -> int:
    return time.time_ns()


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


def send_json(sock: socket.socket, lock: threading.Lock, payload: dict[str, Any]) -> None:
    encoded = (json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    with lock:
        sock.sendall(encoded)


@dataclass(eq=False)
class Peer:
    sock: socket.socket
    address: str
    lock: threading.Lock = field(default_factory=threading.Lock)


class RobotService:
    def __init__(self, bind: str, port: int) -> None:
        self.bind = bind
        self.port = port
        self.stop_event = threading.Event()
        self.state_lock = threading.RLock()
        self.peers: set[Peer] = set()
        self.server_socket: socket.socket | None = None
        self.stm: Any = None
        self.lidar: Any = None
        self.camera: Any = None
        self.camera_thread: threading.Thread | None = None
        self.pose: Any = None
        self.mapper: Any = None
        self.files: Any = None
        self.run_root: Path | None = None
        self.scan_started_ns = 0
        self.scan_active = False
        self.scan_saved = False
        self.armed = False
        self.last_command = ZERO
        self.last_command_mono = time.monotonic()
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
        image.thumbnail((640, 480))
        stream = io.BytesIO()
        image.save(stream, format="JPEG", quality=72, optimize=True)
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
            self.files = RunFiles(root)
            self.run_root = root
            self.scan_started_ns = now_ns()
            self.scan_active = True
            self.scan_saved = False
            self.last_scan_ns = 0
            self.last_broadcast_map_signature = ""
            self.files.event("console_scan_started", "lidar=N10P; map=dead_reckoned")
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
                self.scan_active = False
                self.files = None
                self.status["scan"] = "saved"
            except Exception as error:
                self.broadcast({"type": "event", "event": "error", "message": str(error)})
                return
        self.broadcast({"type": "event", "event": "scan_saved", "path": str(root), "status": self.status_payload()})

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

    def handle(self, peer: Peer, message: dict[str, Any]) -> None:
        command = str(message.get("command", "")).strip().lower()
        try:
            if command == "arm":
                enabled = bool(message.get("enabled", False))
                with self.state_lock:
                    self.armed = enabled and self.stm is not None
                    self.status["armed"] = self.armed
                    self.last_command_mono = time.monotonic()
                if not self.armed:
                    self.send_zero()
                self.broadcast({"type": "event", "event": "armed", "enabled": self.armed, "status": self.status_payload()})
            elif command == "velocity":
                values = tuple(float(message.get(name, 0.0)) for name in ("vx", "vy", "wz"))
                if not all(math.isfinite(value) for value in values):
                    raise ValueError("velocity must be finite")
                limits = (0.30, 0.30, 0.90)
                values = tuple(max(-limit, min(limit, value)) for value, limit in zip(values, limits))
                with self.state_lock:
                    active = self.armed and self.stm is not None
                    self.last_command_mono = time.monotonic()
                if active:
                    self.stm.send_velocity(*values)
                    with self.state_lock:
                        self.last_command = values
                        self.command_sequence += 1
                        if self.files is not None:
                            self.files.control(now_ns(), values, self.stm.latest, self.command_sequence, getattr(self.stm, "backend", "serial"))
                else:
                    self.send_zero()
            elif command in {"stop", "emergency_stop"}:
                self.disarm(command)
            elif command == "scan_start":
                self.start_scan()
            elif command in {"scan_save", "scan_stop"}:
                self.save_scan(command)
            elif command == "ping":
                send_json(peer.sock, peer.lock, {"type": "pong", "t_ns": now_ns()})
            else:
                send_json(peer.sock, peer.lock, {"type": "event", "event": "error", "message": "unknown command"})
        except Exception as error:
            self.disarm("command_error")
            send_json(peer.sock, peer.lock, {"type": "event", "event": "error", "message": str(error)})

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
                    send_json(peer.sock, peer.lock, {"type": "event", "event": "error", "message": "invalid message"})
                    continue
                if isinstance(message, dict):
                    self.handle(peer, message)
        except (ConnectionError, OSError):
            pass
        finally:
            with self.state_lock:
                self.peers.discard(peer)
                no_peers = not self.peers
            try:
                peer.sock.close()
            except OSError:
                pass
            if no_peers:
                self.disarm("client_disconnected")

    def broadcast(self, payload: dict[str, Any]) -> None:
        dead: list[Peer] = []
        for peer in tuple(self.peers):
            try:
                send_json(peer.sock, peer.lock, payload)
            except (ConnectionError, OSError):
                dead.append(peer)
        if dead:
            with self.state_lock:
                for peer in dead:
                    self.peers.discard(peer)

    def _state_payload(self) -> dict[str, Any]:
        with self.state_lock:
            telemetry = self.stm.latest if self.stm is not None else None
            if telemetry is not None and self.pose is not None and telemetry.t_ns != self.last_telemetry_ns:
                self.pose.update(telemetry)
                self.last_telemetry_ns = telemetry.t_ns
                if self.files is not None:
                    self.files.state(now_ns(), self.pose, telemetry, getattr(self.stm, "backend", "serial"))
            pose = [0.0, 0.0, 0.0] if self.pose is None else list(self.pose.as_tuple())
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
                        self.mapper.update(scan, self.pose)
                        if self.files is not None:
                            self.files.scan(scan)
                            self.files.context(scan.t_ns, self.pose, scan)
            return {"type": "lidar", "t_ns": now_ns(), "points": self.latest_lidar}

    def _map_payload(self) -> dict[str, Any] | None:
        with self.state_lock:
            if self.mapper is None:
                return None
            payload = self.mapper.payload()
            signature = f"{payload['width']}:{payload['height']}:{payload['metadata']['scans']}:{payload['metadata']['points']}"
            if signature == self.last_broadcast_map_signature:
                return None
            self.last_broadcast_map_signature = signature
            return {"type": "map", "t_ns": now_ns(), "map": payload}

    def _camera_payload(self) -> dict[str, Any] | None:
        with self.state_lock:
            if self.latest_camera is None:
                return None
            return {"type": "camera", "t_ns": now_ns(), "jpeg": self.latest_camera, "shape": self.camera_shape}

    def loop(self) -> None:
        while not self.stop_event.wait(0.02):
            now = time.monotonic()
            with self.state_lock:
                if self.armed and now - self.last_command_mono > 0.7:
                    self.disarm("watchdog")
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
                    self.peers.add(peer)
                send_json(connection, peer.lock, {"type": "hello", "app": "robot-console", "status": self.status_payload()})
                threading.Thread(target=self._client_loop, args=(peer,), name="robot-console-client", daemon=True).start()
        except KeyboardInterrupt:
            pass
        finally:
            self.close()

    def close(self) -> None:
        if self.stop_event.is_set():
            return
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
            try:
                peer.sock.close()
            except OSError:
                pass
        self.peers.clear()


class ConsoleApp:
    def __init__(self, host: str, port: int) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.root = tk.Tk()
        self.root.title("Mecanum Robot Console")
        self.root.geometry("1380x820")
        self.root.minsize(1100, 680)
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
        self.camera_image: Any = None
        self.keys: set[str] = set()
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
        control = ttk.Frame(outer, width=245)
        control.pack(side="left", fill="y", padx=(0, 8))
        control.pack_propagate(False)
        ttk.Label(control, text="MECANUM ROBOT", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 12))
        connection = ttk.LabelFrame(control, text="Connection", padding=8)
        connection.pack(fill="x", pady=(0, 8))
        ttk.Label(connection, text="Jetson host").grid(row=0, column=0, sticky="w")
        ttk.Entry(connection, textvariable=self.host, width=18).grid(row=1, column=0, sticky="ew", pady=(2, 5))
        ttk.Label(connection, text="Port").grid(row=2, column=0, sticky="w")
        ttk.Entry(connection, textvariable=self.port, width=8).grid(row=3, column=0, sticky="ew", pady=(2, 5))
        ttk.Button(connection, text="Connect", command=self.connect).grid(row=4, column=0, sticky="ew")
        connection.columnconfigure(0, weight=1)
        ttk.Label(control, textvariable=self.connection_text, foreground="#2f80ed").pack(anchor="w", pady=(0, 8))
        safety = ttk.LabelFrame(control, text="Safety", padding=8)
        safety.pack(fill="x", pady=(0, 8))
        self.arm_button = ttk.Button(safety, text="Enable motion", command=self.toggle_arm)
        self.arm_button.pack(fill="x", pady=(0, 5))
        ttk.Button(safety, text="EMERGENCY STOP", command=self.emergency_stop).pack(fill="x")
        motion = ttk.LabelFrame(control, text="Teleoperation", padding=8)
        motion.pack(fill="x", pady=(0, 8))
        ttk.Label(motion, text="Speed (m/s)").pack(anchor="w")
        ttk.Scale(motion, variable=self.speed, from_=0.05, to=0.30, orient="horizontal").pack(fill="x")
        ttk.Label(motion, text="Yaw (rad/s)").pack(anchor="w", pady=(6, 0))
        ttk.Scale(motion, variable=self.yaw_speed, from_=0.10, to=0.90, orient="horizontal").pack(fill="x")
        grid = ttk.Frame(motion)
        grid.pack(pady=(8, 0))
        buttons = (("↑", "w", 0, 1), ("←", "a", 1, 0), ("■", "x", 1, 1), ("→", "d", 1, 2), ("↓", "s", 2, 1))
        for label, key, row, column in buttons:
            button = ttk.Button(grid, text=label, width=4)
            button.grid(row=row, column=column, padx=2, pady=2)
            button.bind("<ButtonPress-1>", lambda _event, k=key: self._button_down(k))
            button.bind("<ButtonRelease-1>", lambda _event, k=key: self._button_up(k))
        ttk.Label(motion, text="Hold W/S/A/D or arrows; Q/E rotate").pack(anchor="w", pady=(6, 0))
        mapping = ttk.LabelFrame(control, text="Map capture", padding=8)
        mapping.pack(fill="x", pady=(0, 8))
        ttk.Button(mapping, text="Start scan", command=lambda: self.send({"command": "scan_start"})).pack(fill="x", pady=(0, 4))
        ttk.Button(mapping, text="Save map and data", command=lambda: self.send({"command": "scan_save"})).pack(fill="x", pady=(0, 4))
        ttk.Button(mapping, text="Stop scan", command=lambda: self.send({"command": "scan_stop"})).pack(fill="x")
        self.info = tk.Text(control, height=10, width=29, state="disabled", background="#f4f6f8", relief="flat")
        self.info.pack(fill="both", expand=True)
        views = ttk.Frame(outer)
        views.pack(side="left", fill="both", expand=True)
        upper = ttk.Frame(views)
        upper.pack(fill="both", expand=True)
        map_frame = ttk.LabelFrame(upper, text="2D map / lidar / robot pose", padding=4)
        map_frame.pack(fill="both", expand=True)
        self.map_canvas = tk.Canvas(map_frame, background="#101820", highlightthickness=0)
        self.map_canvas.pack(fill="both", expand=True)
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
            self.reader_thread = threading.Thread(target=self._reader, name="console-reader", daemon=True)
            self.reader_thread.start()
            self.connection_text.set(f"Connected to {self.host.get().strip()}:{self.port.get()}")
            self.send({"command": "ping"})
        except Exception as error:
            self.connection_text.set(f"Connection failed: {error}")
            self.sock = None

    def disconnect(self) -> None:
        self.reader_stop.set()
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None
        self.armed = False
        self.arm_button.configure(text="Enable motion")

    def _reader(self) -> None:
        sock = self.sock
        if sock is None:
            return
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
            self.messages.put({"type": "event", "event": "disconnect", "message": "server disconnected"})

    def send(self, payload: dict[str, Any]) -> None:
        if self.sock is None:
            return
        try:
            send_json(self.sock, self.socket_lock, payload)
        except (ConnectionError, OSError):
            self.connection_text.set("Disconnected")

    def toggle_arm(self) -> None:
        self.armed = not self.armed
        self.send({"command": "arm", "enabled": self.armed})
        self.arm_button.configure(text="Disable motion" if self.armed else "Enable motion")

    def emergency_stop(self) -> None:
        self.keys.clear()
        self.armed = False
        self.arm_button.configure(text="Enable motion")
        self.send({"command": "emergency_stop"})

    def _button_down(self, key: str) -> None:
        if key == "x":
            self.emergency_stop()
            return
        self.keys.add(key)

    def _button_up(self, key: str) -> None:
        self.keys.discard(key)
        if self.armed and not self.keys:
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
        self.keys.discard(aliases.get(key, key))

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
        self._update_info()
        if self.armed and self.keys:
            command = self._command_from_keys(self.keys)
            self.send({"command": "velocity", "vx": command[0], "vy": command[1], "wz": command[2]})
        elif self.armed and not self.keys:
            self.send({"command": "velocity", "vx": 0.0, "vy": 0.0, "wz": 0.0})
        self._draw_map()
        self.root.after(60, self._tick)

    def _update_info(self) -> None:
        status = self.state.get("status") or {}
        telemetry = self.state.get("telemetry") or {}
        pose = self.state.get("pose") or [0.0, 0.0, 0.0]
        lines = [
            f"STM: {status.get('stm', 'offline')}",
            f"N10P: {status.get('lidar', 'offline')}",
            f"Astra-S: {status.get('camera', 'disabled')}",
            f"Motion: {'ENABLED' if status.get('armed') else 'disabled'}",
            f"Scan: {status.get('scan', 'idle')}",
            f"Pose: {float(pose[0]):.2f}, {float(pose[1]):.2f}, {float(pose[2]):.2f}",
            f"Velocity: {float(telemetry.get('vx_mps', 0.0)):.2f}, {float(telemetry.get('vy_mps', 0.0)):.2f}, {float(telemetry.get('wz_radps', 0.0)):.2f}",
            f"Battery: {float(telemetry.get('voltage_v', 0.0)):.2f} V",
            f"Laser points: {len(self.lidar)}",
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
            if len(pose) >= 2:
                if not self.trace or math.hypot(pose[0] - self.trace[-1][0], pose[1] - self.trace[-1][1]) > 0.01:
                    self.trace.append((float(pose[0]), float(pose[1])))
                    self.trace = self.trace[-1000:]
        elif kind == "lidar":
            self.lidar = message.get("points") or []
        elif kind == "map":
            self.map_payload = message.get("map")
        elif kind == "camera":
            self._show_camera(message.get("jpeg"))
        elif kind == "hello":
            self.connection_text.set("Connected")
        elif kind == "event":
            event = str(message.get("event", ""))
            if event == "disconnect":
                self.disconnect()
            if event == "armed" and not bool(message.get("enabled")):
                self.armed = False
                self.arm_button.configure(text="Enable motion")
            status = message.get("status")
            if status:
                self.state["status"] = status
            self.connection_text.set(str(message.get("message", event)))

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
        if self.map_payload:
            width = int(self.map_payload.get("width", 1))
            height = int(self.map_payload.get("height", 1))
            resolution = float(self.map_payload.get("resolution_m", 0.05))
            origin = self.map_payload.get("origin", [0.0, 0.0, 0.0])
            return float(origin[0]), float(origin[1]), float(origin[0]) + width * resolution, float(origin[1]) + height * resolution
        points = [(r * math.cos(a), r * math.sin(a)) for a, r in self.lidar]
        points.extend(self.trace)
        if not points:
            return -3.0, -3.0, 3.0, 3.0
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return min(xs) - 1.0, min(ys) - 1.0, max(xs) + 1.0, max(ys) + 1.0

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
            occupancy = self.map_payload.get("occupancy", [])
            for index, value in enumerate(occupancy):
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
        pose = self.state.get("pose", [0.0, 0.0, 0.0])
        px, py, yaw = (float(value) for value in (pose + [0.0, 0.0, 0.0])[:3])
        rx, ry = point(px, py)
        corners = []
        for cx, cy in ((0.20, 0.20), (0.20, -0.20), (-0.20, -0.20), (-0.20, 0.20)):
            x = px + math.cos(yaw) * cx - math.sin(yaw) * cy
            y = py + math.sin(yaw) * cx + math.cos(yaw) * cy
            corners.extend(point(x, y))
        canvas.create_polygon(corners, fill="#2f80ed", outline="#b9dcff", tags="robot")
        canvas.create_line(rx, ry, *point(px + 0.35 * math.cos(yaw), py + 0.35 * math.sin(yaw)), fill="#ffffff", width=2, tags="robot")
        for angle, distance in self.lidar:
            lx = px + 0.10 * math.cos(yaw) - 0.0 * math.sin(yaw) + distance * math.cos(yaw + angle)
            ly = py + 0.10 * math.sin(yaw) + distance * math.sin(yaw + angle)
            canvas.create_line(rx, ry, *point(lx, ly), fill="#48d597", width=1, tags="lidar")
        canvas.create_text(18, 16, anchor="nw", fill="#d6e4ef", text=f"pose  x={px:.2f}  y={py:.2f}  yaw={yaw:.2f}", tags="label")

    def close(self) -> None:
        self.emergency_stop()
        self.disconnect()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def self_test() -> None:
    from hardware import LidarPoint, LidarScan, N10PDecoder, N10P_PROTOCOL_PROFILE
    from manual_map import OccupancyMap, Pose

    mapper = OccupancyMap(0.05, lidar_x_m=0.10, lidar_y_m=0.0, lidar_yaw_rad=0.0, min_range_m=0.05, max_range_m=8.0, padding_cells=2)
    scan = LidarScan(1, (LidarPoint(1, 0.0, 1.0, 10, 0), LidarPoint(1, math.pi / 2.0, 0.5, 10, 0)))
    mapper.update(scan, Pose())
    payload = mapper.payload()
    if payload["width"] < 3 or payload["height"] < 3 or 100 not in payload["occupancy"]:
        raise AssertionError("map self-test failed")
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
