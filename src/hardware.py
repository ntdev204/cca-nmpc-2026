from __future__ import annotations

import csv
import ctypes
import json
import math
import os
import struct
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

try:
    from ai.ctx_lstm import MAX_CONTEXT_SPEED_MPS
except ImportError:
    MAX_CONTEXT_SPEED_MPS = 2.0
from shared import (
    CCA_CAN_APPLIED_ID,
    CCA_CAN_COMMAND_PAYLOAD_ID,
    CCA_CAN_STATUS_ID,
    CCA_CAN_WHEEL_D_ID,
    CCA_CAN_WHEELS_ABC_ID,
    cpp_transport_library,
    decode_cca_can_frame,
)


def monotonic_ns() -> int:
    return time.monotonic_ns()


def utc_ns() -> int:
    return time.time_ns()


N10P_PROTOCOL_PROFILE = "n10p-108b-v1"
N10P_PROTOCOL_PROFILES = frozenset({N10P_PROTOCOL_PROFILE})

POSITION_STATE_FIELDS = (
    "x_m",
    "y_m",
    "theta_rad",
    "vx_mps",
    "vy_mps",
    "omega_radps",
)

STM32_FRAME_HEADER = 0x7B
STM32_FRAME_TAIL = 0x7D
STM32_COMMAND_SIZE = 11
STM32_TELEMETRY_SIZE = 24
STM32_AUX_HEADER = 0x7C
STM32_AUX_TAIL = 0x7F
STM32_AUX_SIZE = 8
STM32_ACCELERATOR_RATIO = 1671.84
STM32_GYROSCOPE_RATIO = 0.00026644


def stm32_xor_checksum(data: bytes) -> int:
    value = 0
    for byte in data:
        value ^= byte
    return value


def encode_stm32_velocity_command(
    vx_mps: float,
    vy_mps: float,
    wz_radps: float,
    *,
    mode: int = 0,
    reserved: int = 0,
) -> bytes:
    values = (vx_mps, vy_mps, wz_radps)
    if not all(isinstance(value, (int, float)) and math.isfinite(float(value)) for value in values):
        raise ValueError("STM32 velocity command values must be finite")
    if not isinstance(mode, int) or not 0 <= mode <= 255:
        raise ValueError("STM32 command mode must be an unsigned byte")
    if not isinstance(reserved, int) or not 0 <= reserved <= 255:
        raise ValueError("STM32 reserved command byte must be an unsigned byte")
    quantized = tuple(int(float(value) * 1000.0) for value in values)
    if not all(-32768 <= value <= 32767 for value in quantized):
        raise ValueError("STM32 velocity command exceeds signed 16-bit millimetre range")
    frame = bytearray((STM32_FRAME_HEADER, mode, reserved))
    frame.extend(struct.pack(">hhh", *quantized))
    frame.append(stm32_xor_checksum(bytes(frame)))
    frame.append(STM32_FRAME_TAIL)
    return bytes(frame)


@dataclass(frozen=True)
class Stm32Telemetry:
    t_ns: int
    flag_stop: int
    vx_mps: float
    vy_mps: float
    wz_radps: float
    accel_x_mps2: float
    accel_y_mps2: float
    accel_z_mps2: float
    gyro_x_radps: float
    gyro_y_radps: float
    gyro_z_radps: float
    voltage_v: float


@dataclass(frozen=True)
class Stm32AuxTelemetry:
    t_ns: int
    charging_current_a: float
    red: int
    charging: bool
    charge_set_state: int


class Stm32FrameDecoder:
    def __init__(self) -> None:
        self._buffer = bytearray()

    @staticmethod
    def _signed_i16(data: bytes, offset: int) -> int:
        return int(struct.unpack_from(">h", data, offset)[0])

    def feed(self, data: bytes, timestamp_ns: int) -> tuple[Stm32Telemetry, ...]:
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("STM32 serial data must be bytes-like")
        if timestamp_ns < 0:
            raise ValueError("STM32 telemetry timestamp must be nonnegative")
        self._buffer.extend(data)
        decoded: list[Stm32Telemetry] = []
        while True:
            candidates = [index for index in (self._buffer.find(bytes((STM32_FRAME_HEADER,))), self._buffer.find(bytes((STM32_AUX_HEADER,)))) if index >= 0]
            if not candidates:
                self._buffer[:] = self._buffer[-1:] if self._buffer[-1:] in (bytes((STM32_FRAME_HEADER,)), bytes((STM32_AUX_HEADER,))) else b""
                return tuple(decoded)
            index = min(candidates)
            if index:
                del self._buffer[:index]
            if self._buffer[0] == STM32_AUX_HEADER:
                if len(self._buffer) < STM32_AUX_SIZE:
                    return tuple(decoded)
                packet = bytes(self._buffer[:STM32_AUX_SIZE])
                if packet[-1] == STM32_AUX_TAIL and packet[-2] == stm32_xor_checksum(packet[:6]):
                    del self._buffer[:STM32_AUX_SIZE]
                    continue
                del self._buffer[0]
                continue
            if len(self._buffer) < STM32_TELEMETRY_SIZE:
                return tuple(decoded)
            packet = bytes(self._buffer[:STM32_TELEMETRY_SIZE])
            if packet[-1] != STM32_FRAME_TAIL or packet[-2] != stm32_xor_checksum(packet[:22]):
                del self._buffer[0]
                continue
            del self._buffer[:STM32_TELEMETRY_SIZE]
            decoded.append(
                Stm32Telemetry(
                    t_ns=timestamp_ns,
                    flag_stop=packet[1],
                    vx_mps=self._signed_i16(packet, 2) / 1000.0,
                    vy_mps=self._signed_i16(packet, 4) / 1000.0,
                    wz_radps=self._signed_i16(packet, 6) / 1000.0,
                    accel_x_mps2=self._signed_i16(packet, 8) / STM32_ACCELERATOR_RATIO,
                    accel_y_mps2=self._signed_i16(packet, 10) / STM32_ACCELERATOR_RATIO,
                    accel_z_mps2=self._signed_i16(packet, 12) / STM32_ACCELERATOR_RATIO,
                    gyro_x_radps=self._signed_i16(packet, 14) * STM32_GYROSCOPE_RATIO,
                    gyro_y_radps=self._signed_i16(packet, 16) * STM32_GYROSCOPE_RATIO,
                    gyro_z_radps=self._signed_i16(packet, 18) * STM32_GYROSCOPE_RATIO,
                    voltage_v=int.from_bytes(packet[20:22], "big") / 1000.0,
                )
            )


class _PythonStm32SerialSource:
    def __init__(
        self,
        port: str,
        *,
        baudrate: int = 115200,
        timeout_s: float = 0.1,
        mode: int = 0,
    ) -> None:
        if not isinstance(port, str) or not port.strip():
            raise ValueError("STM32 serial port must be nonempty")
        if not isinstance(baudrate, int) or baudrate <= 0:
            raise ValueError("STM32 baudrate must be a positive integer")
        if not math.isfinite(timeout_s) or timeout_s <= 0.0:
            raise ValueError("STM32 serial timeout must be positive and finite")
        if not isinstance(mode, int) or not 0 <= mode <= 255:
            raise ValueError("STM32 mode must be an unsigned byte")
        self.port = port
        self.baudrate = baudrate
        self.timeout_s = timeout_s
        self.mode = mode
        self._serial: Any = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._latest: Stm32Telemetry | None = None
        self._latest_aux: Stm32AuxTelemetry | None = None
        self._decoder = Stm32FrameDecoder()
        self.errors = 0
        self.last_command: tuple[int, float, float, float] | None = None

    @property
    def latest(self) -> Stm32Telemetry | None:
        with self._lock:
            return self._latest

    @property
    def latest_aux(self) -> Stm32AuxTelemetry | None:
        with self._lock:
            return self._latest_aux

    def start(self) -> None:
        try:
            import serial
        except ImportError as error:
            raise RuntimeError("pyserial is required for STM32 capture") from error
        self._stop.clear()
        self._decoder = Stm32FrameDecoder()
        self._latest = None
        self._latest_aux = None
        self.errors = 0
        self._serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout_s)
        self._serial.reset_input_buffer()
        self._thread = threading.Thread(target=self._run, name="stm32-reader", daemon=True)
        self._thread.start()

    def send_velocity(self, vx_mps: float, vy_mps: float, wz_radps: float) -> None:
        if self._serial is None or not self._serial.is_open:
            raise RuntimeError("STM32 serial source is not started")
        frame = encode_stm32_velocity_command(vx_mps, vy_mps, wz_radps, mode=self.mode)
        with self._write_lock:
            self._serial.write(frame)
        self.last_command = (utc_ns(), float(vx_mps), float(vy_mps), float(wz_radps))

    def stop(self) -> None:
        if self._serial is not None and self._serial.is_open:
            try:
                self.send_velocity(0.0, 0.0, 0.0)
            except (OSError, RuntimeError, ValueError):
                self.errors += 1
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        if self._serial is not None:
            self._serial.close()
        self._serial = None
        self._thread = None

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                payload = self._serial.read(128)
                if not payload:
                    continue
                timestamp = utc_ns()
                frames = self._decoder.feed(payload, timestamp)
                if frames:
                    with self._lock:
                        self._latest = frames[-1]
            except Exception:
                self.errors += 1
                if self._stop.wait(0.05):
                    return


class _CppStmTelemetry(ctypes.Structure):
    _fields_ = [
        ("timestamp_ns", ctypes.c_uint64),
        ("flag_stop", ctypes.c_uint8),
        ("vx_mps", ctypes.c_double),
        ("vy_mps", ctypes.c_double),
        ("wz_radps", ctypes.c_double),
        ("accel_x_mps2", ctypes.c_double),
        ("accel_y_mps2", ctypes.c_double),
        ("accel_z_mps2", ctypes.c_double),
        ("gyro_x_radps", ctypes.c_double),
        ("gyro_y_radps", ctypes.c_double),
        ("gyro_z_radps", ctypes.c_double),
        ("voltage_v", ctypes.c_double),
    ]


class _CppStm32SerialSource:
    def __init__(
        self,
        port: str,
        *,
        baudrate: int = 115200,
        timeout_s: float = 0.1,
        mode: int = 0,
        library_path: Path,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout_s = timeout_s
        self.mode = mode
        self.library_path = library_path
        self._library = ctypes.CDLL(str(library_path))
        self._configure_api()
        self._handle = ctypes.c_void_p()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._latest: Stm32Telemetry | None = None
        self.errors = 0
        self.last_command: tuple[int, float, float, float] | None = None

    def _configure_api(self) -> None:
        self._library.cca_stm_open.argtypes = [
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_char_p,
            ctypes.c_size_t,
        ]
        self._library.cca_stm_open.restype = ctypes.c_int
        self._library.cca_stm_send_velocity.argtypes = [
            ctypes.c_void_p,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_char_p,
            ctypes.c_size_t,
        ]
        self._library.cca_stm_send_velocity.restype = ctypes.c_int
        self._library.cca_stm_read.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint64,
            ctypes.POINTER(_CppStmTelemetry),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.c_char_p,
            ctypes.c_size_t,
        ]
        self._library.cca_stm_read.restype = ctypes.c_int
        self._library.cca_stm_send_zero.argtypes = [ctypes.c_void_p]
        self._library.cca_stm_send_zero.restype = None
        self._library.cca_stm_close.argtypes = [ctypes.c_void_p]
        self._library.cca_stm_close.restype = None

    @staticmethod
    def _error(buffer: ctypes.Array[ctypes.c_char]) -> str:
        return bytes(buffer).split(b"\0", 1)[0].decode("utf-8", errors="replace") or "C++ STM transport failed"

    def start(self) -> None:
        error = ctypes.create_string_buffer(512)
        handle = ctypes.c_void_p()
        result = self._library.cca_stm_open(
            self.port.encode("utf-8"),
            int(self.baudrate),
            max(1, int(round(self.timeout_s * 1000.0))),
            ctypes.byref(handle),
            error,
            len(error),
        )
        if result != 0:
            raise RuntimeError(self._error(error))
        self._handle = handle
        self._stop.clear()
        self._latest = None
        self.errors = 0
        self._thread = threading.Thread(target=self._run, name="stm32-cpp-reader", daemon=True)
        self._thread.start()

    @property
    def latest(self) -> Stm32Telemetry | None:
        with self._lock:
            return self._latest

    @property
    def latest_aux(self) -> Stm32AuxTelemetry | None:
        return None

    def send_velocity(self, vx_mps: float, vy_mps: float, wz_radps: float) -> None:
        if not self._handle:
            raise RuntimeError("C++ STM serial source is not started")
        error = ctypes.create_string_buffer(512)
        result = self._library.cca_stm_send_velocity(
            self._handle,
            float(vx_mps),
            float(vy_mps),
            float(wz_radps),
            error,
            len(error),
        )
        if result != 0:
            raise RuntimeError(self._error(error))
        self.last_command = (utc_ns(), float(vx_mps), float(vy_mps), float(wz_radps))

    def _run(self) -> None:
        samples = (_CppStmTelemetry * 64)()
        while not self._stop.is_set():
            count = ctypes.c_size_t()
            error = ctypes.create_string_buffer(512)
            result = self._library.cca_stm_read(
                self._handle,
                utc_ns(),
                samples,
                len(samples),
                ctypes.byref(count),
                error,
                len(error),
            )
            if result != 0:
                self.errors += 1
                if self._stop.wait(0.05):
                    return
                continue
            if count.value:
                decoded = [
                    Stm32Telemetry(
                        t_ns=int(samples[index].timestamp_ns),
                        flag_stop=int(samples[index].flag_stop),
                        vx_mps=float(samples[index].vx_mps),
                        vy_mps=float(samples[index].vy_mps),
                        wz_radps=float(samples[index].wz_radps),
                        accel_x_mps2=float(samples[index].accel_x_mps2),
                        accel_y_mps2=float(samples[index].accel_y_mps2),
                        accel_z_mps2=float(samples[index].accel_z_mps2),
                        gyro_x_radps=float(samples[index].gyro_x_radps),
                        gyro_y_radps=float(samples[index].gyro_y_radps),
                        gyro_z_radps=float(samples[index].gyro_z_radps),
                        voltage_v=float(samples[index].voltage_v),
                    )
                    for index in range(count.value)
                ]
                with self._lock:
                    self._latest = decoded[-1]

    def stop(self) -> None:
        if self._handle:
            self._library.cca_stm_send_zero(self._handle)
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        if self._handle:
            self._library.cca_stm_close(self._handle)
        self._handle = ctypes.c_void_p()
        self._thread = None


class Stm32SerialSource:
    def __init__(
        self,
        port: str,
        *,
        baudrate: int = 115200,
        timeout_s: float = 0.1,
        mode: int = 0,
        backend: str | None = None,
    ) -> None:
        selected = (backend or os.environ.get("CCA_STM_BACKEND", "auto")).strip().lower()
        if selected not in {"auto", "cpp", "python"}:
            raise ValueError("STM backend must be auto, cpp or python")
        library = cpp_transport_library()
        if selected == "cpp" and library is None:
            raise RuntimeError("CCA_STM_BACKEND=cpp requires the built C++ transport library")
        if selected == "cpp" or (selected == "auto" and library is not None):
            self.backend = "cpp"
            self._impl: Any = _CppStm32SerialSource(
                port,
                baudrate=baudrate,
                timeout_s=timeout_s,
                mode=mode,
                library_path=library,
            )
        else:
            self.backend = "python"
            self._impl = _PythonStm32SerialSource(
                port,
                baudrate=baudrate,
                timeout_s=timeout_s,
                mode=mode,
            )

    @property
    def latest(self) -> Stm32Telemetry | None:
        return self._impl.latest

    @property
    def latest_aux(self) -> Stm32AuxTelemetry | None:
        return self._impl.latest_aux

    @property
    def errors(self) -> int:
        return int(self._impl.errors)

    @property
    def last_command(self) -> tuple[int, float, float, float] | None:
        return self._impl.last_command

    @property
    def transport_library(self) -> Path | None:
        return getattr(self._impl, "library_path", None)

    def start(self) -> None:
        self._impl.start()

    def send_velocity(self, vx_mps: float, vy_mps: float, wz_radps: float) -> None:
        self._impl.send_velocity(vx_mps, vy_mps, wz_radps)

    def stop(self) -> None:
        self._impl.stop()


@dataclass(frozen=True)
class N10PProtocolSpec:
    packet_size: int
    point_count: int
    point_offset: int
    start_angle_offset: int
    end_angle_offset: int


N10P_PROTOCOL_SPECS = {
    N10P_PROTOCOL_PROFILE: N10PProtocolSpec(
        packet_size=108,
        point_count=16,
        point_offset=7,
        start_angle_offset=5,
        end_angle_offset=105,
    )
}


def validate_n10p_protocol_profile(profile: str) -> str:
    if not isinstance(profile, str) or profile not in N10P_PROTOCOL_SPECS:
        supported = ", ".join(sorted(N10P_PROTOCOL_PROFILES))
        raise ValueError(f"unsupported N10P protocol profile; expected one of: {supported}")
    return profile


@dataclass(frozen=True)
class LidarPoint:
    t_ns: int
    angle_rad: float
    range_m: float
    intensity: int
    return_id: int


@dataclass(frozen=True)
class LidarScan:
    t_ns: int
    points: tuple[LidarPoint, ...]

    @property
    def minimum_range_m(self) -> float:
        ranges = [point.range_m for point in self.points if point.range_m > 0.0]
        return min(ranges) if ranges else math.nan


class N10PDecoder:
    @staticmethod
    def crc(packet: bytes) -> int:
        return sum(packet) & 0xFF

    def __init__(self, profile: str) -> None:
        self.profile = validate_n10p_protocol_profile(profile)
        spec = N10P_PROTOCOL_SPECS[self.profile]
        self.packet_size = spec.packet_size
        self.point_count = spec.point_count
        self.point_offset = spec.point_offset
        self.start_angle_offset = spec.start_angle_offset
        self.end_angle_offset = spec.end_angle_offset
        self._buffer = bytearray()

    def _next_packet(self, timestamp_ns: int) -> tuple[LidarPoint, ...] | None:
        while True:
            index = self._buffer.find(b"\xA5\x5A")
            if index < 0:
                self._buffer[:] = self._buffer[-1:] if self._buffer[-1:] == b"\xA5" else b""
                return None
            if index:
                del self._buffer[:index]
            if len(self._buffer) < self.packet_size:
                return None
            packet = bytes(self._buffer[: self.packet_size])
            if packet[-1] != self.crc(packet[:-1]):
                del self._buffer[0]
                continue
            del self._buffer[: self.packet_size]
            return self.decode(packet, timestamp_ns)

    def feed_all(self, data: bytes, timestamp_ns: int) -> tuple[tuple[LidarPoint, ...], ...]:
        self._buffer.extend(data)
        packets: list[tuple[LidarPoint, ...]] = []
        while True:
            decoded = self._next_packet(timestamp_ns)
            if decoded is None:
                return tuple(packets)
            packets.append(decoded)

    def feed(self, data: bytes, timestamp_ns: int) -> tuple[LidarPoint, ...]:
        self._buffer.extend(data)
        return self._next_packet(timestamp_ns) or ()

    def decode(self, packet: bytes, timestamp_ns: int) -> tuple[LidarPoint, ...]:
        if len(packet) != self.packet_size or packet[:2] != b"\xA5\x5A":
            raise ValueError("N10P packet header or size is invalid")
        if packet[-1] != self.crc(packet[:-1]):
            raise ValueError("N10P packet CRC mismatch")
        start = int.from_bytes(packet[self.start_angle_offset : self.start_angle_offset + 2], "big") / 100.0
        end = int.from_bytes(packet[self.end_angle_offset : self.end_angle_offset + 2], "big") / 100.0
        interval = (end - start) % 360.0
        entries: list[tuple[int, int, int, int]] = []
        for index in range(self.point_count):
            offset = self.point_offset + index * 6
            for return_id, distance_offset in enumerate((0, 3)):
                distance = int.from_bytes(packet[offset + distance_offset : offset + distance_offset + 2], "big")
                if distance not in (0, 0xFFFF):
                    intensity = packet[offset + distance_offset + 2]
                    entries.append((index, return_id, distance, intensity))
        valid_slots = max(1, self.point_count - 1)
        points: list[LidarPoint] = []
        for index, return_id, distance, intensity in entries:
            angle = math.radians((start + interval * index / valid_slots) % 360.0)
            points.append(LidarPoint(timestamp_ns, angle, distance / 1000.0, intensity, return_id))
        return tuple(points)


class N10PSerialSource:
    def __init__(
        self,
        port: str,
        *,
        profile: str,
        baudrate: int = 460800,
        timeout_s: float = 0.1,
    ) -> None:
        self.port = port
        self.protocol_profile = validate_n10p_protocol_profile(profile)
        self.baudrate = baudrate
        self.timeout_s = timeout_s
        self._serial: Any = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._latest: LidarScan | None = None
        self._decoder = N10PDecoder(self.protocol_profile)
        self._scan_times = deque(maxlen=24)

    @property
    def latest(self) -> LidarScan | None:
        with self._lock:
            return self._latest

    @property
    def scan_rate_hz(self) -> float:
        with self._lock:
            if len(self._scan_times) < 2:
                return 0.0
            elapsed = self._scan_times[-1] - self._scan_times[0]
            return (len(self._scan_times) - 1) / elapsed if elapsed > 0.0 else 0.0

    def start(self) -> None:
        try:
            import serial
        except ImportError as error:
            raise RuntimeError("pyserial is required for N10P capture") from error
        self._stop.clear()
        self._decoder = N10PDecoder(self.protocol_profile)
        self._latest = None
        with self._lock:
            self._scan_times.clear()
        try:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout_s)
            self._serial.write(self.start_command())
            self._thread = threading.Thread(target=self._run, name="n10p-reader", daemon=True)
            self._thread.start()
        except Exception:
            if self._serial is not None:
                self._serial.close()
            self._serial = None
            raise

    def stop(self) -> None:
        self._stop.set()
        if self._serial is not None:
            try:
                self._serial.write(self.stop_command())
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        if self._serial is not None:
            self._serial.close()
        self._serial = None
        self._thread = None

    @staticmethod
    def start_command() -> bytes:
        command = bytearray(188)
        command[0:3] = b"\xA5\x5A\x55"
        command[184:188] = b"\x01\x01\xFA\xFB"
        return bytes(command)

    @staticmethod
    def stop_command() -> bytes:
        command = bytearray(188)
        command[0:3] = b"\xA5\x5A\x55"
        command[184:188] = b"\x01\x00\xFA\xFB"
        return bytes(command)

    def _run(self) -> None:
        last_angle: float | None = None
        points: list[LidarPoint] = []
        while not self._stop.is_set():
            waiting = int(getattr(self._serial, "in_waiting", 0) or 0)
            payload = self._serial.read(max(256, min(waiting, 4096)))
            if not payload:
                continue
            timestamp = utc_ns()
            for decoded in self._decoder.feed_all(payload, timestamp):
                for point in decoded:
                    angle = math.degrees(point.angle_rad)
                    wrapped = last_angle is not None and last_angle > 355.0 and angle < 5.0
                    if wrapped and points:
                        with self._lock:
                            self._latest = LidarScan(timestamp, tuple(points))
                            self._scan_times.append(time.monotonic())
                        points = []
                    points.append(point)
                    last_angle = angle


@dataclass
class CcaSnapshot:
    t_ns: int = 0
    command_t_ns: int = 0
    applied_t_ns: int = 0
    wheels_t_ns: int = 0
    applied: dict[str, Any] | None = None
    status: dict[str, Any] | None = None
    command: dict[str, Any] | None = None
    wheels: dict[str, Any] | None = None
    battery_mv: int | None = None
    pwm_mask: int | None = None
    external_faults: int | None = None


class CcaCanSource:
    def __init__(self, channel: str, interface: str = "socketcan", bitrate: int = 500000) -> None:
        self.channel = channel
        self.interface = interface
        self.bitrate = bitrate
        self._bus: Any = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._snapshot = CcaSnapshot()
        self.errors = 0

    @property
    def latest(self) -> CcaSnapshot:
        with self._lock:
            return CcaSnapshot(
                t_ns=self._snapshot.t_ns,
                command_t_ns=self._snapshot.command_t_ns,
                applied_t_ns=self._snapshot.applied_t_ns,
                wheels_t_ns=self._snapshot.wheels_t_ns,
                applied=self._snapshot.applied.copy() if self._snapshot.applied else None,
                status=self._snapshot.status.copy() if self._snapshot.status else None,
                command=self._snapshot.command.copy() if self._snapshot.command else None,
                wheels=self._snapshot.wheels.copy() if self._snapshot.wheels else None,
                battery_mv=self._snapshot.battery_mv,
                pwm_mask=self._snapshot.pwm_mask,
                external_faults=self._snapshot.external_faults,
            )

    def start(self) -> None:
        try:
            import can
        except ImportError as error:
            raise RuntimeError("python-can is required for CCA CAN capture") from error
        self._stop.clear()
        with self._lock:
            self._snapshot = CcaSnapshot()
        self.errors = 0
        self._bus = can.Bus(interface=self.interface, channel=self.channel, bitrate=self.bitrate)
        self._thread = threading.Thread(target=self._run, name="cca-can-reader", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        if self._bus is not None:
            self._bus.shutdown()
        self._bus = None
        self._thread = None

    def _run(self) -> None:
        while not self._stop.is_set():
            message = self._bus.recv(timeout=0.1)
            if message is None:
                continue
            try:
                decoded = decode_cca_can_frame(message.arbitration_id, bytes(message.data))
            except ValueError:
                self.errors += 1
                continue
            with self._lock:
                timestamp = utc_ns()
                self._snapshot.t_ns = timestamp
                if message.arbitration_id == CCA_CAN_APPLIED_ID:
                    self._snapshot.applied = decoded
                    self._snapshot.applied_t_ns = timestamp
                elif message.arbitration_id == CCA_CAN_COMMAND_PAYLOAD_ID:
                    self._snapshot.command = decoded
                    self._snapshot.command_t_ns = timestamp
                elif message.arbitration_id == CCA_CAN_STATUS_ID:
                    self._snapshot.status = decoded
                elif message.arbitration_id == CCA_CAN_WHEELS_ABC_ID:
                    self._snapshot.wheels_t_ns = timestamp
                    self._snapshot.wheels = {
                        **(self._snapshot.wheels or {}),
                        **decoded,
                    }
                elif message.arbitration_id == CCA_CAN_WHEEL_D_ID:
                    self._snapshot.wheels_t_ns = timestamp
                    self._snapshot.wheels = {
                        **(self._snapshot.wheels or {}),
                        **decoded,
                    }
                    self._snapshot.battery_mv = decoded["battery_mv"]
                    self._snapshot.pwm_mask = decoded["pwm_mask"]
                    self._snapshot.external_faults = decoded["external_faults"]


@dataclass(frozen=True)
class RobotGeometry:
    wheel_radius_m: float
    half_length_m: float
    half_width_m: float
    wheel_signs: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)

    @classmethod
    def from_json(cls, path: Path) -> "RobotGeometry":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema") != "cca-hardware-runtime-v1":
            raise ValueError("robot config must use schema cca-hardware-runtime-v1")
        values = [payload.get(name) for name in ("wheel_radius_m", "half_length_m", "half_width_m")]
        urdf_value = payload.get("urdf_path")
        if isinstance(urdf_value, str) and urdf_value.strip():
            urdf_path = Path(urdf_value)
            if not urdf_path.is_absolute():
                local_path = path.parent / urdf_path
                urdf_path = local_path if local_path.is_file() else Path(urdf_value)
            if not urdf_path.is_file():
                raise ValueError(f"hardware geometry URDF does not exist: {urdf_value}")
            if any(value is None for value in values):
                raise ValueError("measured robot geometry dimensions are required; URDF is reference-only")
        if any(value is None for value in values):
            raise ValueError("measured physical specification dimensions are required")
        if not all(isinstance(value, (int, float)) and math.isfinite(float(value)) and value > 0 for value in values):
            raise ValueError("robot geometry dimensions must be positive finite numbers")
        if payload.get("geometry_authority") != "measured_physical_spec":
            raise ValueError("robot geometry must come from a measured physical specification")
        signs_payload = payload.get("wheel_signs", {})
        signs = tuple(float(signs_payload.get(name, 1.0)) for name in ("fl", "fr", "rl", "rr"))
        if not all(sign in (-1.0, 1.0) for sign in signs):
            raise ValueError("wheel_signs must be either -1 or 1")
        return cls(float(values[0]), float(values[1]), float(values[2]), signs)

    @classmethod
    def from_urdf(cls, path: Path, *, wheel_radius_m: float) -> "RobotGeometry":
        if not math.isfinite(wheel_radius_m) or wheel_radius_m <= 0.0:
            raise ValueError("URDF wheel radius must be positive and finite")
        try:
            root = ElementTree.parse(path).getroot()
        except (OSError, ElementTree.ParseError) as error:
            raise ValueError(f"invalid robot URDF: {path}") from error
        wheel_links = {
            "lf": "lf_wheel_link",
            "fr": "rf_wheel_link",
            "rl": "lb_wheel_link",
            "rr": "rb_wheel_link",
        }
        positions: dict[str, tuple[float, float]] = {}
        for joint in root.findall("joint"):
            child = joint.find("child")
            origin = joint.find("origin")
            if child is None or origin is None:
                continue
            link_name = child.attrib.get("link")
            key = next((name for name, link in wheel_links.items() if link == link_name), None)
            if key is None:
                continue
            values = [float(value) for value in origin.attrib.get("xyz", "").split()]
            if len(values) != 3 or not all(math.isfinite(value) for value in values):
                raise ValueError(f"URDF wheel origin is invalid for {link_name}")
            positions[key] = (values[0], values[1])
        if set(positions) != set(wheel_links):
            missing = sorted(set(wheel_links) - set(positions))
            raise ValueError(f"URDF does not define all Mecanum wheel origins: {', '.join(missing)}")
        x_values = [value[0] for value in positions.values()]
        y_values = [value[1] for value in positions.values()]
        half_length = (max(x_values) - min(x_values)) / 2.0
        half_width = (max(y_values) - min(y_values)) / 2.0
        if half_length <= 0.0 or half_width <= 0.0:
            raise ValueError("URDF Mecanum wheel spans must be positive")
        return cls(float(wheel_radius_m), float(half_length), float(half_width))

    def body_velocity(self, wheels: dict[str, Any]) -> tuple[float, float, float]:
        values = [
            float(wheels[key]) * sign
            for key, sign in zip(("wheel_fl_radps", "wheel_fr_radps", "wheel_rl_radps", "wheel_rr_radps"), self.wheel_signs)
        ]
        radius = self.wheel_radius_m
        vx = radius * sum(values) / 4.0
        vy = radius * (-values[0] + values[1] + values[2] - values[3]) / 4.0
        wz = radius * (-values[0] + values[1] - values[2] + values[3]) / (4.0 * (self.half_length_m + self.half_width_m))
        return vx, vy, wz


@dataclass
class Odometry:
    x_m: float = 0.0
    y_m: float = 0.0
    yaw_rad: float = 0.0
    vx_mps: float = 0.0
    vy_mps: float = 0.0
    omega_radps: float = 0.0
    t_ns: int | None = None

    def update(self, t_ns: int, velocity: tuple[float, float, float]) -> None:
        vx, vy, wz = (float(value) for value in velocity)
        if not all(math.isfinite(value) for value in (vx, vy, wz)):
            raise ValueError("odometry velocity must be finite")
        if self.t_ns is not None:
            dt = max(0.0, min((t_ns - self.t_ns) * 1e-9, 0.25))
            c = math.cos(self.yaw_rad)
            s = math.sin(self.yaw_rad)
            self.x_m += (c * vx - s * vy) * dt
            self.y_m += (s * vx + c * vy) * dt
            self.yaw_rad = math.atan2(math.sin(self.yaw_rad + wz * dt), math.cos(self.yaw_rad + wz * dt))
        self.vx_mps = vx
        self.vy_mps = vy
        self.omega_radps = wz
        self.t_ns = t_ns

    @property
    def state(self) -> tuple[float, float, float, float, float, float]:
        return (
            self.x_m,
            self.y_m,
            self.yaw_rad,
            self.vx_mps,
            self.vy_mps,
            self.omega_radps,
        )


def apply_transform(position: tuple[float, float, float], transform: dict[str, Any]) -> tuple[float, float, float]:
    tx, ty, tz = (float(value) for value in transform["translation_m"])
    roll, pitch, yaw = (float(value) for value in transform["rpy_rad"])
    x, y, z = position
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    r00, r01, r02 = cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr
    r10, r11, r12 = sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr
    r20, r21, r22 = -sp, cp * sr, cp * cr
    return (r00 * x + r01 * y + r02 * z + tx, r10 * x + r11 * y + r12 * z + ty, r20 * x + r21 * y + r22 * z + tz)


@dataclass(frozen=True)
class AstraFrame:
    t_ns: int
    color_bgr: Any
    depth_raw: Any
    depth_scale_m: float
    device_timestamp_ns: int | None = None
    timestamp_source: str = "host_receive_time"

    def __post_init__(self) -> None:
        if self.t_ns < 0 or not math.isfinite(self.depth_scale_m) or self.depth_scale_m <= 0.0:
            raise ValueError("Astra frame timestamp and depth scale must be valid")
        if self.device_timestamp_ns is not None and self.device_timestamp_ns < 0:
            raise ValueError("Astra device timestamp must be nonnegative")
        if not isinstance(self.timestamp_source, str) or not self.timestamp_source.strip():
            raise ValueError("Astra timestamp source must be nonempty")


def openni_frame_timestamp_ns(frame: Any) -> int | None:
    accessors: list[Any] = []
    for name in ("get_timestamp", "timestamp"):
        try:
            accessors.append(getattr(frame, name))
        except Exception:
            continue
    for accessor in accessors:
        try:
            value = accessor() if callable(accessor) else accessor
        except Exception:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        try:
            numeric_value = float(value)
        except (OverflowError, TypeError, ValueError):
            continue
        if not math.isfinite(numeric_value) or numeric_value < 0.0:
            continue
        return int(round(numeric_value * 1000.0))
    return None


class AstraSSource:
    def __init__(
        self,
        *,
        uri: str | None = None,
        sdk_path: str | None = None,
        depth_scale_m: float = 0.001,
        max_pair_skew_us: float | None = None,
    ) -> None:
        if not math.isfinite(depth_scale_m) or depth_scale_m <= 0.0:
            raise ValueError("Astra depth scale must be positive and finite")
        if max_pair_skew_us is not None and (
            not math.isfinite(max_pair_skew_us) or max_pair_skew_us <= 0.0
        ):
            raise ValueError("Astra pair skew limit must be positive and finite")
        self.uri = uri
        self.sdk_path = sdk_path
        self.depth_scale_m = depth_scale_m
        self.max_pair_skew_us = max_pair_skew_us
        self._openni: Any = None
        self._device: Any = None
        self._color_stream: Any = None
        self._depth_stream: Any = None
        self._last_capture_t_ns = 0
        self._frames_read = 0
        self._device_timestamp_frames = 0
        self._paired_timestamp_frames = 0
        self._max_pair_skew_ns = 0

    def start(self) -> None:
        try:
            from openni import openni2
        except ImportError:
            try:
                import openni2
            except ImportError:
                try:
                    # Orbbec's legacy SDK commonly ships the same bindings
                    # under the ``primesense`` package name.
                    from primesense import openni2
                except ImportError as primesense_error:
                    raise RuntimeError(
                        "OpenNI2 Python bindings are required for Astra-S capture"
                    ) from primesense_error
        self._openni = openni2
        try:
            self._openni.initialize(self.sdk_path) if self.sdk_path else self._openni.initialize()
            if self.uri:
                self._device = self._openni.Device.open_file(self.uri)
            else:
                self._device = self._openni.Device.open_any()
            self._depth_stream = self._device.create_depth_stream()
            self._color_stream = self._device.create_color_stream()
            # Ask the Astra driver for depth-to-colour registration and
            # hardware timestamp synchronisation when those capabilities are
            # exposed.  Older firmware may not implement either method, so
            # keep the acquisition path compatible and let timing metadata
            # report the observed result.
            self._depth_stream.start()
            self._color_stream.start()
            try:
                registration = self._openni.IMAGE_REGISTRATION_DEPTH_TO_COLOR
                if self._device.is_image_registration_mode_supported(registration):
                    self._device.set_image_registration_mode(registration)
            except (AttributeError, RuntimeError, TypeError):
                pass
            try:
                self._device.set_depth_color_sync_enabled(True)
            except (AttributeError, RuntimeError, TypeError):
                pass
        except Exception:
            self.stop()
            raise

    def read(self) -> AstraFrame:
        if self._depth_stream is None or self._color_stream is None:
            raise RuntimeError("Astra-S source is not started")
        try:
            import numpy as np
        except ImportError as error:
            raise RuntimeError("numpy is required for Astra-S capture") from error
        color_frame = self._color_stream.read_frame()
        depth_frame = self._depth_stream.read_frame()
        color_device_timestamp_ns = openni_frame_timestamp_ns(color_frame)
        depth_device_timestamp_ns = openni_frame_timestamp_ns(depth_frame)
        if color_device_timestamp_ns is not None and depth_device_timestamp_ns is not None:
            pair_skew_ns = abs(color_device_timestamp_ns - depth_device_timestamp_ns)
            self._paired_timestamp_frames += 1
            self._max_pair_skew_ns = max(self._max_pair_skew_ns, pair_skew_ns)
            if self.max_pair_skew_us is not None and pair_skew_ns > self.max_pair_skew_us * 1000.0:
                raise RuntimeError("Astra color/depth device timestamps exceed the configured pair skew")
        if color_device_timestamp_ns is not None or depth_device_timestamp_ns is not None:
            self._device_timestamp_frames += 1
        color_width = int(color_frame.width)
        color_height = int(color_frame.height)
        color = np.frombuffer(color_frame.get_buffer_as_uint8(), dtype=np.uint8)
        if color.size != color_width * color_height * 3:
            raise RuntimeError("Astra color frame is not RGB888")
        color = color.reshape((color_height, color_width, 3))[:, :, ::-1].copy()
        depth_width = int(depth_frame.width)
        depth_height = int(depth_frame.height)
        depth = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16)
        if depth.size != depth_width * depth_height:
            raise RuntimeError("Astra depth frame is not uint16")
        capture_t_ns = max(utc_ns(), self._last_capture_t_ns + 1)
        self._last_capture_t_ns = capture_t_ns
        self._frames_read += 1
        return AstraFrame(
            capture_t_ns,
            color,
            depth.reshape((depth_height, depth_width)).copy(),
            self.depth_scale_m,
            color_device_timestamp_ns if color_device_timestamp_ns is not None else depth_device_timestamp_ns,
            "host_receive_time",
        )

    def timing_metadata(self) -> dict[str, Any]:
        return {
            "canonical_timestamp": "host_receive_time",
            "device_timestamp_unit": "microseconds_converted_to_nanoseconds",
            "device_timestamp_frames": self._device_timestamp_frames,
            "paired_timestamp_frames": self._paired_timestamp_frames,
            "frames_read": self._frames_read,
            "max_observed_pair_skew_us": self._max_pair_skew_ns / 1000.0,
            "pair_skew_limit_us": self.max_pair_skew_us,
        }

    def stop(self) -> None:
        for stream in (self._color_stream, self._depth_stream):
            if stream is not None:
                try:
                    stream.stop()
                except Exception:
                    pass
        if self._device is not None:
            try:
                self._device.close()
            except Exception:
                pass
        if self._openni is not None:
            try:
                self._openni.unload()
            except Exception:
                pass
        self._color_stream = None
        self._depth_stream = None
        self._device = None
        self._openni = None


@dataclass(frozen=True)
class PoseContextRecord:
    t_ns: int
    position_x_m: float
    position_y_m: float
    speed_mps: float
    direction: str
    confidence: float
    context_valid: bool
    frame_path: str
    camera_device_timestamp_ns: int | None = None
    lstm_active: bool = False
    lstm_configured: bool = False
    lstm_path: str = ""


def _direction_from_velocity(velocity: tuple[float, float], minimum_speed_mps: float) -> str:
    vx, vy = velocity
    speed = math.hypot(vx, vy)
    if speed < minimum_speed_mps:
        return "unknown"
    if abs(vx) >= abs(vy):
        return "right" if vx >= 0.0 else "left"
    return "forward" if vy >= 0.0 else "backward"


def _lstm_history(positions: list[tuple[float, float]], valid: list[bool], dt_s: float) -> Any:
    import numpy as np

    values = np.asarray(positions, dtype=np.float32)
    mask = np.asarray(valid, dtype=np.float32)
    anchor = values[-1]
    relative = values - anchor
    velocity = np.zeros_like(relative)
    if len(values) > 1:
        velocity[1:] = np.diff(values, axis=0) / max(dt_s, 1.0e-6)
        velocity[0] = velocity[1]
    return np.concatenate((relative, velocity, mask[:, None]), axis=1).astype(np.float32)[None, ...]


class PoseContextProcessor:
    def __init__(
        self,
        detector: Any,
        calibration: dict[str, Any],
        *,
        lstm: Any = None,
        lstm_path: str | None = None,
        observed_steps: int = 20,
        dt_s: float = 0.1,
        minimum_speed_mps: float = 0.02,
    ) -> None:
        import numpy as np

        intrinsics = calibration["camera_intrinsics"]
        self.fx = float(intrinsics["fx"])
        self.fy = float(intrinsics["fy"])
        self.cx = float(intrinsics["cx"])
        self.cy = float(intrinsics["cy"])
        if min(self.fx, self.fy) <= 0.0 or observed_steps < 2 or dt_s <= 0.0:
            raise ValueError("invalid camera or LSTM context configuration")
        self.detector = detector
        self.calibration = calibration
        self.lstm = lstm
        self.lstm_path = str(lstm_path or "")
        self.observed_steps = observed_steps
        self.dt_s = dt_s
        self.minimum_speed_mps = minimum_speed_mps
        self._positions: deque[tuple[float, float]] = deque(maxlen=observed_steps)
        self._valid: deque[bool] = deque(maxlen=observed_steps)
        self._last_position: tuple[float, float] | None = None
        self._last_t_ns: int | None = None
        self._np = np

    def process(self, frame: AstraFrame, frame_path: str) -> tuple[PoseContextRecord, tuple[Any, ...]]:
        detections = tuple(self.detector.detect(frame.color_bgr, frame.t_ns))
        detection = max(detections, key=lambda item: item.confidence, default=None)
        if detection is None:
            self._positions.append(self._last_position or (0.0, 0.0))
            self._valid.append(False)
            return PoseContextRecord(
                t_ns=frame.t_ns,
                position_x_m=0.0,
                position_y_m=0.0,
                speed_mps=0.0,
                direction="unknown",
                confidence=0.0,
                context_valid=False,
                frame_path=frame_path,
                camera_device_timestamp_ns=frame.device_timestamp_ns,
                lstm_configured=self.lstm is not None,
                lstm_path=self.lstm_path,
            ), detections
        x1, y1, x2, y2 = detection.xyxy
        center_x = int(round((x1 + x2) / 2.0))
        center_y = int(round((y1 + y2) / 2.0))
        color_height, color_width = frame.color_bgr.shape[:2]
        height, width = frame.depth_raw.shape[:2]
        if (color_height, color_width) != (height, width):
            raise RuntimeError("Astra color/depth frames must be pixel-aligned before metric fusion")
        center_x = max(0, min(width - 1, center_x))
        center_y = max(0, min(height - 1, center_y))
        x_low, x_high = max(0, center_x - 2), min(width, center_x + 3)
        y_low, y_high = max(0, center_y - 2), min(height, center_y + 3)
        depths = self._np.asarray(frame.depth_raw[y_low:y_high, x_low:x_high], dtype=self._np.float64) * frame.depth_scale_m
        valid_depth = depths[self._np.isfinite(depths) & (depths > 0.0)]
        if valid_depth.size == 0:
            self._positions.append(self._last_position or (0.0, 0.0))
            self._valid.append(False)
            return PoseContextRecord(
                t_ns=frame.t_ns,
                position_x_m=0.0,
                position_y_m=0.0,
                speed_mps=0.0,
                direction="unknown",
                confidence=float(detection.confidence),
                context_valid=False,
                frame_path=frame_path,
                camera_device_timestamp_ns=frame.device_timestamp_ns,
                lstm_configured=self.lstm is not None,
                lstm_path=self.lstm_path,
            ), detections
        depth = float(self._np.median(valid_depth))
        camera_position = ((center_x - self.cx) * depth / self.fx, (center_y - self.cy) * depth / self.fy, depth)
        robot_position = apply_transform(camera_position, self.calibration["camera_to_robot"])
        position = (float(robot_position[0]), float(robot_position[1]))
        self._positions.append(position)
        self._valid.append(True)
        measured_velocity = (0.0, 0.0)
        if self._last_position is not None and self._last_t_ns is not None and frame.t_ns > self._last_t_ns:
            elapsed = (frame.t_ns - self._last_t_ns) * 1.0e-9
            measured_velocity = ((position[0] - self._last_position[0]) / elapsed, (position[1] - self._last_position[1]) / elapsed)
        self._last_position = position
        self._last_t_ns = frame.t_ns
        velocity = measured_velocity
        lstm_active = False
        confidence = float(detection.confidence)
        context_valid = True
        if self.lstm is not None and len(self._positions) == self.observed_steps:
            import torch

            history = _lstm_history(list(self._positions), list(self._valid), self.dt_s)
            with torch.no_grad():
                prediction = self.lstm(torch.from_numpy(history))
            vector = prediction.context_velocity_xy[0].detach().cpu().numpy().astype(float)
            predicted_speed = float(self._np.linalg.norm(vector))
            if not self._np.isfinite(vector).all() or predicted_speed > MAX_CONTEXT_SPEED_MPS:
                velocity = (0.0, 0.0)
                confidence = 0.0
                context_valid = False
            else:
                velocity = (float(vector[0]), float(vector[1]))
                probabilities = prediction.direction_probabilities[0].detach().cpu().numpy().astype(float)
                confidence = min(confidence, float(self._np.max(probabilities)))
                lstm_active = True
        speed = math.hypot(*velocity)
        direction = _direction_from_velocity(velocity, self.minimum_speed_mps)
        return PoseContextRecord(
            t_ns=frame.t_ns,
            position_x_m=position[0],
            position_y_m=position[1],
            speed_mps=speed,
            direction=direction,
            confidence=max(0.0, min(1.0, confidence)),
            context_valid=context_valid,
            frame_path=frame_path,
            camera_device_timestamp_ns=frame.device_timestamp_ns,
            lstm_active=lstm_active,
            lstm_configured=self.lstm is not None,
            lstm_path=self.lstm_path,
        ), detections


def write_pose_overlay(image_bgr: Any, detections: tuple[Any, ...], record: PoseContextRecord, path: Path) -> None:
    try:
        import cv2
    except ImportError as error:
        raise RuntimeError("opencv-python is required to write Astra overlays") from error
    image = image_bgr.copy()
    for detection in detections:
        x1, y1, x2, y2 = (int(round(value)) for value in detection.xyxy)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 220, 0), 2)
        keypoints = getattr(detection, "keypoints_xy", ())
        valid = getattr(detection, "keypoint_valid", ())
        for point, is_valid in zip(keypoints, valid, strict=False):
            if bool(is_valid):
                cv2.circle(image, (int(round(point[0])), int(round(point[1]))), 2, (0, 180, 255), -1)
    if not record.lstm_configured:
        status = "disabled"
    elif record.lstm_active:
        status = "active"
    else:
        status = "warmup" if record.context_valid else "invalid"
    text = f"LSTM={status} {record.direction} v={record.speed_mps:.2f}m/s p=({record.position_x_m:.2f},{record.position_y_m:.2f}) valid={int(record.context_valid)}"
    cv2.putText(image, text, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2, cv2.LINE_AA)
    path_text = record.lstm_path or "<not-configured>"
    path_lines = [path_text[index : index + 96] for index in range(0, len(path_text), 96)] or [path_text]
    for line_index, path_line in enumerate(path_lines):
        prefix = "LSTM_PATH=" if line_index == 0 else "           "
        cv2.putText(
            image,
            prefix + path_line,
            (12, 52 + 22 * line_index),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )
    if not cv2.imwrite(str(path), image):
        raise RuntimeError(f"failed to write Astra overlay: {path}")


class CsvWriters:
    def __init__(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=False)
        self.root = root
        self._files: dict[str, Any] = {}
        self._writers: dict[str, csv.DictWriter] = {}
        self._open("robot_state.csv", ["t_ns", "x_m", "y_m", "yaw_rad", "vx_mps", "vy_mps", "wz_radps", "wheel_fl_radps", "wheel_fr_radps", "wheel_rl_radps", "wheel_rr_radps", "battery_mv", "pwm_mask", "external_faults", "accel_x_mps2", "accel_y_mps2", "accel_z_mps2", "gyro_x_radps", "gyro_y_radps", "gyro_z_radps", "voltage_v", "flag_stop", "state_estimator", "kalman_cov_trace", "kalman_position_std_m", "kalman_heading_std_rad", "kalman_velocity_std_mps", "transport"])
        self._open("control.csv", ["t_ns", "vx_cmd_mps", "vy_cmd_mps", "wz_cmd_radps", "vx_applied_mps", "vy_applied_mps", "wz_applied_radps", "sequence", "transport"])
        self._open("context.csv", ["t_ns", "position_x_m", "position_y_m", "speed_mps", "direction", "confidence", "context_valid", "lstm_active", "lstm_configured", "frame_path", "camera_device_t_ns", "lidar_min_range_m", "lidar_valid"])
        self._open("lidar.csv", ["t_ns", "point_count", "points_json"])
        self._open("events.csv", ["t_ns", "event_type", "solve_ms", "status_code", "sequence", "detail"])

    def _open(self, name: str, fields: list[str]) -> None:
        stream = (self.root / name).open("w", encoding="utf-8", newline="")
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        self._files[name] = stream
        self._writers[name] = writer

    def write(self, name: str, row: dict[str, Any]) -> None:
        self._writers[name].writerow(row)

    def flush(self) -> None:
        for stream in self._files.values():
            stream.flush()

    def close(self) -> None:
        for stream in self._files.values():
            stream.flush()
            stream.close()


def latest_lidar_context(scan: LidarScan | None) -> tuple[float, bool]:
    if scan is None:
        return 0.0, False
    minimum = scan.minimum_range_m
    return (minimum if math.isfinite(minimum) else 0.0), math.isfinite(minimum)


def write_runtime_metadata(
    root: Path,
    *,
    camera: str,
    lidar: str,
    firmware: str,
    clock: str,
    robot_config: Path,
    extra: dict[str, Any] | None = None,
) -> None:
    payload = {
        "schema": "cca-hardware-capture-v1",
        "camera": camera,
        "lidar": lidar,
        "firmware": firmware,
        "clock": clock,
        "robot_config": robot_config.as_posix(),
        "started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "actuation": "external_controller_only",
        "control_mode": "position_state",
        "state_definition": list(POSITION_STATE_FIELDS),
        "state_csv_mapping": {
            "theta_rad": "yaw_rad",
            "omega_radps": "wz_radps",
        },
        "state_estimator": "six_state_ekf",
        "kalman": {
            "state_definition": list(POSITION_STATE_FIELDS),
            "measurement": ["vx_mps", "vy_mps", "omega_radps"],
            "position_source": "dead_reckoning_from_body_velocity",
        },
        "ros": False,
        "ros" + "2": False,
    }
    if extra:
        payload.update(extra)
    (root / "capture.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
