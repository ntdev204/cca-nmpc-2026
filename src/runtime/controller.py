from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np


_ROOT = Path(__file__).resolve().parents[2]
_KINDS = {"mpc": 0, "nmpc": 1, "dwa": 2, "mppi": 3, "cca_nmpc": 4}


class _Input(ctypes.Structure):
    _fields_ = [
        ("state", ctypes.POINTER(ctypes.c_double)), ("state_size", ctypes.c_size_t),
        ("reference", ctypes.POINTER(ctypes.c_double)), ("reference_size", ctypes.c_size_t),
        ("previous_command", ctypes.POINTER(ctypes.c_double)), ("previous_command_size", ctypes.c_size_t),
        ("human_mean", ctypes.POINTER(ctypes.c_double)), ("human_mean_size", ctypes.c_size_t),
        ("context", ctypes.POINTER(ctypes.c_double)), ("context_size", ctypes.c_size_t),
        ("covariance", ctypes.POINTER(ctypes.c_double)), ("covariance_size", ctypes.c_size_t),
        ("nominal_robot", ctypes.POINTER(ctypes.c_double)), ("nominal_robot_size", ctypes.c_size_t),
        ("obstacles", ctypes.POINTER(ctypes.c_double)), ("obstacles_size", ctypes.c_size_t),
        ("context_aware", ctypes.c_int),
    ]


class _Output(ctypes.Structure):
    _fields_ = [
        ("first_command_mps", ctypes.c_double * 3),
        ("predicted_states", ctypes.POINTER(ctypes.c_double)),
        ("predicted_state_capacity", ctypes.c_size_t),
        ("predicted_state_count", ctypes.c_size_t),
        ("solve_time_ms", ctypes.c_double), ("objective", ctypes.c_double),
        ("maximum_constraint_violation", ctypes.c_double), ("iterations", ctypes.c_int),
        ("status", ctypes.c_int), ("deadline_missed", ctypes.c_int),
        ("risk_bound", ctypes.c_double), ("maximum_risk_slack_m", ctypes.c_double),
    ]


@dataclass(frozen=True)
class ControllerResult:
    first_command_mps: np.ndarray
    predicted_states: np.ndarray
    solve_time_ms: float
    objective: float
    maximum_constraint_violation: float
    iterations: int
    status: str
    deadline_missed: bool
    risk_bound: float
    maximum_risk_slack_m: float


def _library_path() -> Path:
    override = os.environ.get("CCA_RUNTIME_LIBRARY", "").strip()
    candidates = [Path(override)] if override else []
    build = _ROOT / "src" / "control" / "build"
    names = ("control_transport.dll",) if os.name == "nt" else ("libcontrol_transport.so",)
    candidates.extend(build / name for name in names)
    candidates.extend(build / config / name for config in ("Release", "Debug") for name in names)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise RuntimeError("compiled CCA runtime library is unavailable")


def _array(values: np.ndarray | list[float] | tuple[float, ...], *, size: int | None = None) -> tuple[np.ndarray, ctypes.POINTER(ctypes.c_double), int]:
    array = np.ascontiguousarray(np.asarray(values, dtype=np.float64).reshape(-1))
    if size is not None and len(array) != size:
        raise ValueError("controller input has an invalid size")
    pointer = array.ctypes.data_as(ctypes.POINTER(ctypes.c_double)) if len(array) else ctypes.POINTER(ctypes.c_double)()
    return array, pointer, int(len(array))


def _reference_array(values: np.ndarray | list[float] | tuple[float, ...], horizon: int) -> tuple[np.ndarray, ctypes.POINTER(ctypes.c_double), int]:
    raw = np.asarray(values, dtype=np.float64)
    expected = (horizon + 1) * 6
    if raw.shape == (6, horizon + 1):
        array = np.ascontiguousarray(raw.T.reshape(-1))
    elif raw.shape == (horizon + 1, 6):
        array = np.ascontiguousarray(raw.reshape(-1))
    elif raw.ndim == 1 and raw.size == expected:
        array = np.ascontiguousarray(raw.reshape(-1))
    else:
        raise ValueError("controller reference must have interleaved state rows")
    pointer = array.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    return array, pointer, int(len(array))


class CompiledController:
    def __init__(self, kind: str, dt_s: float, horizon: int, deadline_ms: float, robot_radius_m: float, human_radius_m: float) -> None:
        if kind not in _KINDS:
            raise ValueError(f"unsupported controller kind: {kind}")
        self.kind = kind
        self.dt_s = float(dt_s)
        self.horizon = int(horizon)
        self.deadline_ms = float(deadline_ms)
        self.robot_radius_m = float(robot_radius_m)
        self.human_radius_m = float(human_radius_m)
        self.human_clearance_m = self.robot_radius_m + 0.60
        self._library = ctypes.CDLL(str(_library_path()))
        self._library.cca_controller_create.argtypes = [ctypes.c_int, ctypes.c_double, ctypes.c_size_t, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.POINTER(ctypes.c_void_p), ctypes.c_char_p, ctypes.c_size_t]
        self._library.cca_controller_create.restype = ctypes.c_int
        self._library.cca_controller_command.argtypes = [ctypes.c_void_p, ctypes.POINTER(_Input), ctypes.POINTER(_Output), ctypes.c_char_p, ctypes.c_size_t]
        self._library.cca_controller_command.restype = ctypes.c_int
        self._library.cca_controller_reset.argtypes = [ctypes.c_void_p]
        self._library.cca_controller_destroy.argtypes = [ctypes.c_void_p]
        self._handle = ctypes.c_void_p()
        error = ctypes.create_string_buffer(512)
        code = self._library.cca_controller_create(_KINDS[kind], self.dt_s, self.horizon, self.deadline_ms, self.robot_radius_m, self.human_radius_m, self.human_clearance_m, ctypes.byref(self._handle), error, len(error))
        if code != 0:
            raise RuntimeError(bytes(error).split(b"\0", 1)[0].decode(errors="replace"))

    def __del__(self) -> None:
        handle = getattr(self, "_handle", None)
        library = getattr(self, "_library", None)
        if handle and handle.value and library is not None:
            library.cca_controller_destroy(handle)
            self._handle = ctypes.c_void_p()

    def reset(self) -> None:
        self._library.cca_controller_reset(self._handle)

    def command(self, state, reference, previous_command, prediction=None, obstacles=None) -> ControllerResult:
        state_array, state_ptr, state_size = _array(state, size=6)
        reference_array, reference_ptr, reference_size = _reference_array(reference, self.horizon)
        previous_array, previous_ptr, previous_size = _array(previous_command, size=3)
        human = context = covariance = nominal = np.empty(0, dtype=np.float64)
        if prediction is not None and self.kind == "cca_nmpc":
            mean = np.asarray(prediction.mean_xy, dtype=np.float64)
            context_values = np.asarray(prediction.context, dtype=np.float64)
            covariance_values = np.asarray(prediction.relative_covariance_xy, dtype=np.float64)
            nominal_values = np.asarray(prediction.nominal_robot_xy, dtype=np.float64)
            expected_mean = (1, 1, self.horizon, 2)
            expected_context = (1, self.horizon)
            expected_covariance = (1, 1, self.horizon, 2, 2)
            expected_nominal = (self.horizon, 2)
            if mean.shape != expected_mean or context_values.shape != expected_context:
                raise ValueError("controller prediction dimensions are invalid")
            if covariance_values.shape != expected_covariance or nominal_values.shape != expected_nominal:
                raise ValueError("controller prediction dimensions are invalid")
            human = mean.reshape(-1)
            context = context_values.reshape(-1)
            covariance = covariance_values.reshape(-1)
            nominal = nominal_values.reshape(-1)
        obstacles_array, obstacles_ptr, obstacles_size = _array(np.empty(0) if obstacles is None else obstacles)
        arrays = [_array(human), _array(context), _array(covariance), _array(nominal)]
        payload = _Input(state_ptr, state_size, reference_ptr, reference_size, previous_ptr, previous_size, arrays[0][1], arrays[0][2], arrays[1][1], arrays[1][2], arrays[2][1], arrays[2][2], arrays[3][1], arrays[3][2], obstacles_ptr, obstacles_size, int(self.kind == "cca_nmpc" and prediction is not None))
        predicted = np.empty(6 * self.horizon, dtype=np.float64)
        output = _Output()
        output.predicted_states = predicted.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        output.predicted_state_capacity = len(predicted)
        error = ctypes.create_string_buffer(512)
        code = self._library.cca_controller_command(self._handle, ctypes.byref(payload), ctypes.byref(output), error, len(error))
        if code != 0:
            raise RuntimeError(bytes(error).split(b"\0", 1)[0].decode(errors="replace"))
        return ControllerResult(np.asarray(output.first_command_mps, dtype=np.float64), predicted.reshape(self.horizon, 6).copy(), float(output.solve_time_ms), float(output.objective), float(output.maximum_constraint_violation), int(output.iterations), f"{self.kind.upper()}_SUCCESS", bool(output.deadline_missed), float(output.risk_bound), float(output.maximum_risk_slack_m))
