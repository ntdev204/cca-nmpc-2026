from __future__ import annotations

import ctypes
import hashlib
import json
import math
import os
import platform
import re
import struct
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "configs" / "study_contract.json"
_FORBIDDEN_CONTEXT_FIELDS = {
    "trajectory",
    "path",
    "future_positions",
    "future_path",
    "human_trajectory",
    "human_path",
    "predicted_trajectory",
    "predicted_path",
}

CCA_CAN_COMMAND_HEADER_ID = 0x190
CCA_CAN_COMMAND_PAYLOAD_ID = 0x191
CCA_CAN_STATUS_ID = 0x198
CCA_CAN_APPLIED_ID = 0x199
CCA_CAN_WHEELS_ABC_ID = 0x19A
CCA_CAN_WHEEL_D_ID = 0x19B
CCA_CAN_MAGIC = 0xCA
CCA_CAN_VERSION = 1
CALIBRATION_SCHEMA = "cca-capture-calibration-v1"


class _CcaCanFrame(ctypes.Structure):
    _fields_ = [
        ("arbitration_id", ctypes.c_uint32),
        ("data", ctypes.c_uint8 * 8),
    ]


class _CcaCanDecoded(ctypes.Structure):
    _fields_ = [
        ("kind", ctypes.c_int),
        ("mode", ctypes.c_uint8),
        ("sequence", ctypes.c_uint8),
        ("deadline_ticks", ctypes.c_uint8),
        ("profile", ctypes.c_uint8),
        ("flags", ctypes.c_uint8),
        ("status", ctypes.c_uint16),
        ("remaining_ticks", ctypes.c_uint8),
        ("vx_mps", ctypes.c_double),
        ("vy_mps", ctypes.c_double),
        ("wz_radps", ctypes.c_double),
        ("wheel_fl_radps", ctypes.c_double),
        ("wheel_fr_radps", ctypes.c_double),
        ("wheel_rl_radps", ctypes.c_double),
        ("wheel_rr_radps", ctypes.c_double),
        ("battery_mv", ctypes.c_uint16),
        ("pwm_mask", ctypes.c_uint8),
        ("external_faults", ctypes.c_uint8),
    ]


_CCA_CAN_KIND_NAMES = (
    "command_header",
    "command_payload",
    "applied_body",
    "status",
    "wheel_speeds_abc",
    "wheel_speed_d",
)
_CPP_CODEC_UNSET = object()
_CPP_CODEC: object = _CPP_CODEC_UNSET


def cpp_transport_library() -> Path | None:
    override = os.environ.get("CCA_CAN_CPP_LIB", "").strip() or os.environ.get("CCA_STM_CPP_LIB", "").strip()
    candidates = [Path(override)] if override else []
    build = PROJECT_ROOT / "src" / "control" / "build"
    names = {
        "Windows": ("control_transport.dll",),
        "Darwin": ("libcontrol_transport.dylib",),
    }.get(platform.system(), ("libcontrol_transport.so",))
    for name in names:
        candidates.extend(
            (
                build / name,
                build / "Release" / name,
                build / "Debug" / name,
                build / "lib" / name,
            )
        )
    return next((path.resolve() for path in candidates if path.is_file()), None)


class _CppCcaCanCodec:
    def __init__(self, library_path: Path) -> None:
        self.library_path = library_path
        self._library = ctypes.CDLL(str(library_path))
        byte_pointer = ctypes.POINTER(ctypes.c_uint8)
        error_args = [ctypes.c_char_p, ctypes.c_size_t]
        self._library.cca_can_crc8.argtypes = [byte_pointer, ctypes.c_size_t, byte_pointer, *error_args]
        self._library.cca_can_crc8.restype = ctypes.c_int
        header_args = [
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.POINTER(_CcaCanFrame),
            *error_args,
        ]
        self._library.cca_can_encode_header.argtypes = header_args
        self._library.cca_can_encode_header.restype = ctypes.c_int
        body_args = [
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_uint8,
            ctypes.c_uint32,
            ctypes.POINTER(_CcaCanFrame),
            *error_args,
        ]
        self._library.cca_can_encode_body.argtypes = body_args
        self._library.cca_can_encode_body.restype = ctypes.c_int
        self._library.cca_can_decode.argtypes = [
            ctypes.c_uint32,
            byte_pointer,
            ctypes.c_size_t,
            ctypes.POINTER(_CcaCanDecoded),
            *error_args,
        ]
        self._library.cca_can_decode.restype = ctypes.c_int

    @staticmethod
    def _error(buffer: ctypes.Array[ctypes.c_char]) -> str:
        return bytes(buffer).split(b"\0", 1)[0].decode("utf-8", errors="replace") or "C++ CCA CAN codec failed"

    @staticmethod
    def _bytes_pointer(payload: bytes) -> tuple[Any, Any]:
        if not payload:
            return None, None
        buffer = (ctypes.c_uint8 * len(payload)).from_buffer_copy(payload)
        return buffer, ctypes.cast(buffer, ctypes.POINTER(ctypes.c_uint8))

    def _check(self, result: int, error: ctypes.Array[ctypes.c_char]) -> None:
        if result != 0:
            raise ValueError(self._error(error))

    def crc8(self, payload: bytes) -> int:
        buffer, pointer = self._bytes_pointer(payload)
        output = ctypes.c_uint8()
        error = ctypes.create_string_buffer(256)
        self._check(
            self._library.cca_can_crc8(pointer, len(payload), ctypes.byref(output), error, len(error)),
            error,
        )
        del buffer
        return int(output.value)

    def encode_header(self, mode: int, sequence: int, deadline_ticks: int, profile: int, flags: int) -> bytes:
        frame = _CcaCanFrame()
        error = ctypes.create_string_buffer(256)
        self._check(
            self._library.cca_can_encode_header(
                mode,
                sequence,
                deadline_ticks,
                profile,
                flags,
                ctypes.byref(frame),
                error,
                len(error),
            ),
            error,
        )
        return bytes(frame.data)

    def encode_body(self, vx_mps: float, vy_mps: float, wz_radps: float, sequence: int, arbitration_id: int) -> bytes:
        frame = _CcaCanFrame()
        error = ctypes.create_string_buffer(256)
        self._check(
            self._library.cca_can_encode_body(
                vx_mps,
                vy_mps,
                wz_radps,
                sequence,
                arbitration_id,
                ctypes.byref(frame),
                error,
                len(error),
            ),
            error,
        )
        return bytes(frame.data)

    def decode(self, arbitration_id: int, payload: bytes) -> dict[str, Any]:
        buffer, pointer = self._bytes_pointer(payload)
        decoded = _CcaCanDecoded()
        error = ctypes.create_string_buffer(256)
        self._check(
            self._library.cca_can_decode(
                arbitration_id,
                pointer,
                len(payload),
                ctypes.byref(decoded),
                error,
                len(error),
            ),
            error,
        )
        del buffer
        kind = int(decoded.kind)
        if not 0 <= kind < len(_CCA_CAN_KIND_NAMES):
            raise ValueError("C++ CCA CAN codec returned an unsupported frame kind")
        result: dict[str, Any] = {"kind": _CCA_CAN_KIND_NAMES[kind]}
        if kind == 0:
            result.update(
                mode=int(decoded.mode),
                sequence=int(decoded.sequence),
                deadline_ticks=int(decoded.deadline_ticks),
                profile=int(decoded.profile),
                flags=int(decoded.flags),
            )
        elif kind in (1, 2):
            result.update(
                vx_mps=float(decoded.vx_mps),
                vy_mps=float(decoded.vy_mps),
                wz_radps=float(decoded.wz_radps),
                sequence=int(decoded.sequence),
            )
        elif kind == 3:
            result.update(
                sequence=int(decoded.sequence),
                profile=int(decoded.profile),
                status=int(decoded.status),
                remaining_ticks=int(decoded.remaining_ticks),
            )
        elif kind == 4:
            result.update(
                wheel_fl_radps=float(decoded.wheel_fl_radps),
                wheel_fr_radps=float(decoded.wheel_fr_radps),
                wheel_rl_radps=float(decoded.wheel_rl_radps),
                sequence=int(decoded.sequence),
            )
        else:
            result.update(
                wheel_rr_radps=float(decoded.wheel_rr_radps),
                battery_mv=int(decoded.battery_mv),
                pwm_mask=int(decoded.pwm_mask),
                external_faults=int(decoded.external_faults),
                sequence=int(decoded.sequence),
            )
        return result


def _cpp_cca_can_codec() -> _CppCcaCanCodec | None:
    global _CPP_CODEC
    if _CPP_CODEC is not _CPP_CODEC_UNSET:
        return _CPP_CODEC if isinstance(_CPP_CODEC, _CppCcaCanCodec) else None
    backend = os.environ.get("CCA_CAN_BACKEND", "auto").strip().lower()
    if backend not in {"auto", "cpp", "python"}:
        raise ValueError("CCA_CAN_BACKEND must be auto, cpp or python")
    if backend == "python":
        _CPP_CODEC = None
        return None
    library = cpp_transport_library()
    if library is None:
        if backend == "cpp":
            raise RuntimeError("CCA_CAN_BACKEND=cpp requires the built C++ transport library")
        _CPP_CODEC = None
        return None
    try:
        _CPP_CODEC = _CppCcaCanCodec(library)
    except OSError as error:
        if backend == "cpp":
            raise RuntimeError(f"unable to load C++ CCA CAN codec: {error}") from error
        _CPP_CODEC = None
    return _CPP_CODEC if isinstance(_CPP_CODEC, _CppCcaCanCodec) else None


def _quantized_i16(value: float, scale: float, name: str) -> int:
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite")
    quantized = int(round(float(value) * scale))
    if not -32768 <= quantized <= 32767:
        raise ValueError(f"{name} exceeds the signed 16-bit CAN range")
    return quantized


def encode_cca_command_header(
    *,
    mode: int,
    sequence: int,
    deadline_ticks: int,
    profile: int,
    flags: int,
) -> bytes:
    values = (mode, sequence, deadline_ticks, profile, flags)
    if any(not isinstance(value, int) or not 0 <= value <= 255 for value in values):
        raise ValueError("CCA header fields must be unsigned bytes")
    codec = _cpp_cca_can_codec()
    if codec is not None:
        return codec.encode_header(mode, sequence, deadline_ticks, profile, flags)
    payload = bytes((CCA_CAN_MAGIC, CCA_CAN_VERSION, mode, sequence, deadline_ticks, profile, flags))
    return payload + bytes((cca_crc8(payload),))


def encode_cca_body_velocity_payload(
    *,
    vx_mps: float,
    vy_mps: float,
    wz_radps: float,
    sequence: int,
) -> bytes:
    if not isinstance(sequence, int) or not 0 <= sequence <= 255:
        raise ValueError("CCA sequence must be an unsigned byte")
    vx = _quantized_i16(vx_mps, 1000.0, "vx_mps")
    vy = _quantized_i16(vy_mps, 1000.0, "vy_mps")
    wz = _quantized_i16(wz_radps, 1000.0, "wz_radps")
    codec = _cpp_cca_can_codec()
    if codec is not None:
        return codec.encode_body(vx_mps, vy_mps, wz_radps, sequence, CCA_CAN_COMMAND_PAYLOAD_ID)
    payload = struct.pack(">hhhB", vx, vy, wz, sequence)
    return payload + bytes((cca_crc8(payload),))


def cca_crc8(data: bytes) -> int:
    codec = _cpp_cca_can_codec()
    if codec is not None:
        return codec.crc8(bytes(data))
    crc = 0xFF
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1D) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc ^ 0xFF


def _cca_payload(data: bytes) -> bytes:
    payload = bytes(data)
    if len(payload) != 8:
        raise ValueError("CCA CAN payload must contain exactly eight bytes")
    if cca_crc8(payload[:7]) != payload[7]:
        raise ValueError("CCA CAN payload CRC mismatch")
    return payload


def _cca_i16(payload: bytes, offset: int) -> int:
    return int(struct.unpack_from(">h", payload, offset)[0])


def decode_cca_can_frame(arbitration_id: int, data: bytes) -> dict[str, Any]:
    codec = _cpp_cca_can_codec()
    if codec is not None:
        return codec.decode(int(arbitration_id), bytes(data))
    payload = _cca_payload(data)
    frame_id = int(arbitration_id)
    if frame_id == CCA_CAN_COMMAND_HEADER_ID:
        if payload[0] != CCA_CAN_MAGIC or payload[1] != CCA_CAN_VERSION:
            raise ValueError("CCA command header magic/version mismatch")
        return {
            "kind": "command_header",
            "mode": payload[2],
            "sequence": payload[3],
            "deadline_ticks": payload[4],
            "profile": payload[5],
            "flags": payload[6],
        }
    if frame_id in {CCA_CAN_COMMAND_PAYLOAD_ID, CCA_CAN_APPLIED_ID}:
        return {
            "kind": "command_payload" if frame_id == CCA_CAN_COMMAND_PAYLOAD_ID else "applied_body",
            "vx_mps": _cca_i16(payload, 0) / 1000.0,
            "vy_mps": _cca_i16(payload, 2) / 1000.0,
            "wz_radps": _cca_i16(payload, 4) / 1000.0,
            "sequence": payload[6],
        }
    if frame_id == CCA_CAN_STATUS_ID:
        if payload[0] != CCA_CAN_MAGIC or payload[1] != CCA_CAN_VERSION:
            raise ValueError("CCA status magic/version mismatch")
        return {
            "kind": "status",
            "sequence": payload[2],
            "profile": payload[3],
            "status": int.from_bytes(payload[4:6], "big"),
            "remaining_ticks": payload[6],
        }
    if frame_id == CCA_CAN_WHEELS_ABC_ID:
        return {
            "kind": "wheel_speeds_abc",
            "wheel_fl_radps": _cca_i16(payload, 0) / 100.0,
            "wheel_fr_radps": _cca_i16(payload, 2) / 100.0,
            "wheel_rl_radps": _cca_i16(payload, 4) / 100.0,
            "sequence": payload[6],
        }
    if frame_id == CCA_CAN_WHEEL_D_ID:
        return {
            "kind": "wheel_speed_d",
            "wheel_rr_radps": _cca_i16(payload, 0) / 100.0,
            "battery_mv": int.from_bytes(payload[2:4], "big"),
            "pwm_mask": payload[4],
            "external_faults": payload[5],
            "sequence": payload[6],
        }
    raise ValueError(f"unsupported CCA CAN arbitration ID: 0x{frame_id:03X}")


def is_forbidden_context_field(name: str) -> bool:
    normalized = str(name).strip().lower().replace("-", "_")
    return normalized in _FORBIDDEN_CONTEXT_FIELDS or normalized.startswith(
        ("future_", "trajectory_", "path_", "predicted_trajectory_", "predicted_path_")
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def validate_capture_calibration(
    payload: Any,
    *,
    camera: str | None = None,
    lidar: str | None = None,
) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") != CALIBRATION_SCHEMA:
        raise ValueError(f"calibration must use schema {CALIBRATION_SCHEMA}")
    calibration_id = payload.get("calibration_id")
    if not isinstance(calibration_id, str) or not re.fullmatch(r"cal-[a-z0-9]+(?:-[a-z0-9]+)*", calibration_id):
        raise ValueError("calibration_id must be a valid calibration identifier")
    for field in ("camera", "lidar", "robot_frame", "calibrated_at_utc"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            raise ValueError(f"calibration {field} must be nonempty")
    if camera and camera != "not-declared" and payload["camera"] != camera:
        raise ValueError("calibration camera does not match the declared sensor")
    if lidar and lidar != "not-declared" and payload["lidar"] != lidar:
        raise ValueError("calibration lidar does not match the declared sensor")
    intrinsics = payload.get("camera_intrinsics")
    if not isinstance(intrinsics, dict):
        raise ValueError("calibration camera_intrinsics must be an object")
    for field in ("fx", "fy", "cx", "cy"):
        value = intrinsics.get(field)
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError(f"calibration camera_intrinsics.{field} must be finite")
    if float(intrinsics["fx"]) <= 0.0 or float(intrinsics["fy"]) <= 0.0:
        raise ValueError("calibration focal lengths must be positive")
    for field in ("width", "height"):
        value = intrinsics.get(field)
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"calibration camera_intrinsics.{field} must be positive")
    for name in ("camera_to_robot", "lidar_to_robot"):
        transform = payload.get(name)
        if not isinstance(transform, dict):
            raise ValueError(f"calibration {name} must be an object")
        for field in ("translation_m", "rpy_rad"):
            values = transform.get(field)
            if not isinstance(values, list) or len(values) != 3 or not all(
                isinstance(value, (int, float)) and math.isfinite(float(value)) for value in values
            ):
                raise ValueError(f"calibration {name}.{field} must contain three finite values")
    quality = payload.get("quality")
    if not isinstance(quality, dict):
        raise ValueError("calibration quality must be an object")
    for field in ("camera_reprojection_rmse_px", "lidar_alignment_rmse_m"):
        value = quality.get(field)
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) < 0.0:
            raise ValueError(f"calibration quality.{field} must be finite and nonnegative")
    return payload


@lru_cache(maxsize=1)
def load_contract() -> dict[str, Any]:
    payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != "cca-nmpc-shared-study-contract-v1":
        raise ValueError("unsupported shared study contract")
    if payload.get("paper_edit") is not False:
        raise ValueError("shared study contract cannot authorize paper edits")
    return payload
