from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from hardware import (
    AstraFrame,
    AstraSSource,
    CsvWriters,
    N10P_PROTOCOL_PROFILE,
    N10PDecoder,
    Odometry,
    PoseContextProcessor,
    RobotGeometry,
    Stm32FrameDecoder,
    encode_stm32_velocity_command,
    openni_frame_timestamp_ns,
    stm32_xor_checksum,
    write_runtime_metadata,
)


def n10p_packet() -> bytes:
    packet = bytearray(108)
    packet[0:2] = b"\xA5\x5A"
    packet[5:7] = (10000).to_bytes(2, "big")
    packet[105:107] = (11000).to_bytes(2, "big")
    packet[7:9] = (1500).to_bytes(2, "big")
    packet[9] = 12
    packet[10:12] = (2500).to_bytes(2, "big")
    packet[12] = 34
    packet[-1] = sum(packet[:-1]) & 0xFF
    return bytes(packet)


def test_n10p_decoder_stream_and_crc() -> None:
    decoder = N10PDecoder(N10P_PROTOCOL_PROFILE)
    packet = n10p_packet()
    assert decoder.feed(packet[:30], 10) == ()
    points = decoder.feed(packet[30:], 10)
    assert len(points) == 2
    assert points[0].range_m == pytest.approx(1.5)
    assert points[0].intensity == 12
    assert points[1].range_m == pytest.approx(2.5)
    assert points[1].return_id == 1
    broken = bytearray(packet)
    broken[20] ^= 0x01
    with pytest.raises(ValueError, match="CRC"):
        decoder.decode(bytes(broken), 10)


def test_n10p_decoder_requires_declared_protocol_profile() -> None:
    with pytest.raises(ValueError, match="protocol profile"):
        N10PDecoder("unverified-profile")


def test_stm32_command_frame_matches_ros2_serial_contract() -> None:
    frame = encode_stm32_velocity_command(1.234, -0.5, 2.0)
    assert len(frame) == 11
    assert frame[:3] == bytes((0x7B, 0, 0))
    assert frame[3:9] == bytes.fromhex("04d2fe0c07d0")
    assert frame[9] == stm32_xor_checksum(frame[:9])
    assert frame[10] == 0x7D


def test_stm32_quantization_truncates_like_bridge_cast() -> None:
    frame = encode_stm32_velocity_command(0.0009, -0.0009, 0.0019)
    assert frame[3:9] == bytes.fromhex("000000000001")


def test_stm32_telemetry_decoder_handles_fragmented_signed_frame() -> None:
    packet = bytearray(24)
    packet[0] = 0x7B
    packet[1] = 1
    packet[2:4] = (1000).to_bytes(2, "big", signed=True)
    packet[4:6] = (-2000).to_bytes(2, "big", signed=True)
    packet[6:8] = (3000).to_bytes(2, "big", signed=True)
    packet[8:10] = (1672).to_bytes(2, "big", signed=True)
    packet[10:12] = (-1672).to_bytes(2, "big", signed=True)
    packet[12:14] = (0).to_bytes(2, "big", signed=True)
    packet[14:16] = (1000).to_bytes(2, "big", signed=True)
    packet[16:18] = (-1000).to_bytes(2, "big", signed=True)
    packet[18:20] = (0).to_bytes(2, "big", signed=True)
    packet[20:22] = (12000).to_bytes(2, "big")
    packet[22] = stm32_xor_checksum(packet[:22])
    packet[23] = 0x7D
    decoder = Stm32FrameDecoder()
    assert decoder.feed(b"noise" + bytes(packet[:9]), 11) == ()
    decoded = decoder.feed(bytes(packet[9:]), 12)
    assert len(decoded) == 1
    frame = decoded[0]
    assert frame.flag_stop == 1
    assert frame.vx_mps == pytest.approx(1.0)
    assert frame.vy_mps == pytest.approx(-2.0)
    assert frame.wz_radps == pytest.approx(3.0)
    assert frame.accel_x_mps2 == pytest.approx(1.0, rel=2.0e-3)
    assert frame.gyro_y_radps == pytest.approx(-0.26644)
    assert frame.voltage_v == pytest.approx(12.0)


def test_openni_timestamp_is_converted_from_microseconds() -> None:
    class Frame:
        def get_timestamp(self):
            return 1234

    assert openni_frame_timestamp_ns(Frame()) == 1_234_000
    assert openni_frame_timestamp_ns(object()) is None


def test_astra_source_keeps_host_clock_and_records_device_timing() -> None:
    class Frame:
        width = 2
        height = 1

        def __init__(self, timestamp_us: int) -> None:
            self._timestamp_us = timestamp_us

        def get_timestamp(self) -> int:
            return self._timestamp_us

        def get_buffer_as_uint8(self) -> bytes:
            return bytes((1, 2, 3, 4, 5, 6))

        def get_buffer_as_uint16(self) -> bytes:
            return (1000).to_bytes(2, "little") * 2

    class Stream:
        def __init__(self, frame: Frame) -> None:
            self.frame = frame

        def read_frame(self) -> Frame:
            return self.frame

    source = AstraSSource(max_pair_skew_us=2.0)
    source._color_stream = Stream(Frame(1000))
    source._depth_stream = Stream(Frame(1001))
    frame = source.read()
    assert frame.timestamp_source == "host_receive_time"
    assert frame.device_timestamp_ns == 1_000_000
    assert source.timing_metadata()["paired_timestamp_frames"] == 1
    assert source.timing_metadata()["max_observed_pair_skew_us"] == pytest.approx(1.0)


def test_astra_source_rejects_excessive_pair_skew() -> None:
    class Frame:
        width = 1
        height = 1

        def __init__(self, timestamp_us: int) -> None:
            self.timestamp = timestamp_us

        def get_buffer_as_uint8(self) -> bytes:
            return bytes((1, 2, 3))

        def get_buffer_as_uint16(self) -> bytes:
            return (1000).to_bytes(2, "little")

    class Stream:
        def __init__(self, frame: Frame) -> None:
            self.frame = frame

        def read_frame(self) -> Frame:
            return self.frame

    source = AstraSSource(max_pair_skew_us=1.0)
    source._color_stream = Stream(Frame(1000))
    source._depth_stream = Stream(Frame(1003))
    with pytest.raises(RuntimeError, match="pair skew"):
        source.read()


def test_robot_geometry_requires_physical_dimensions(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    missing.write_text(json.dumps({"schema": "cca-hardware-runtime-v1"}), encoding="utf-8")
    with pytest.raises(ValueError, match="dimensions"):
        RobotGeometry.from_json(missing)
    config = {
        "schema": "cca-hardware-runtime-v1",
        "wheel_radius_m": 0.05,
        "half_length_m": 0.2,
        "half_width_m": 0.18,
        "geometry_authority": "measured_physical_spec",
        "wheel_signs": {"fl": 1, "fr": -1, "rl": 1, "rr": -1},
    }
    valid = tmp_path / "valid.json"
    valid.write_text(json.dumps(config), encoding="utf-8")
    geometry = RobotGeometry.from_json(valid)
    velocity = geometry.body_velocity(
        {
            "wheel_fl_radps": 2,
            "wheel_fr_radps": -2,
            "wheel_rl_radps": 2,
            "wheel_rr_radps": -2,
        }
    )
    assert velocity == pytest.approx((0.1, 0.0, 0.0))


def test_robot_geometry_rejects_unlabelled_numeric_dimensions(tmp_path: Path) -> None:
    path = tmp_path / "unlabelled.json"
    path.write_text(
        json.dumps(
            {
                "schema": "cca-hardware-runtime-v1",
                "wheel_radius_m": 0.05,
                "half_length_m": 0.2,
                "half_width_m": 0.18,
                "wheel_signs": {"fl": 1, "fr": 1, "rl": 1, "rr": 1},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="measured physical specification"):
        RobotGeometry.from_json(path)


def test_robot_geometry_reads_mini_mec_urdf_wheel_spans() -> None:
    root = Path(__file__).resolve().parents[3]
    urdf = root / "reference" / "robot" / "rai_robot_urdf" / "rai_robot_urdf" / "urdf" / "mini_mec_robot.urdf"
    geometry = RobotGeometry.from_urdf(urdf, wheel_radius_m=0.0363)
    assert geometry.wheel_radius_m == pytest.approx(0.0363)
    assert geometry.half_length_m == pytest.approx(0.08595, abs=1.0e-6)
    assert geometry.half_width_m == pytest.approx(0.099012, abs=1.0e-6)


def test_odometry_and_direct_csv_contract(tmp_path: Path) -> None:
    odometry = Odometry()
    odometry.update(1_000_000_000, (0.0, 0.0, 0.0))
    odometry.update(2_000_000_000, (1.0, 0.0, 0.0))
    assert odometry.x_m == pytest.approx(0.25)
    assert odometry.state == pytest.approx((0.25, 0.0, 0.0, 1.0, 0.0, 0.0))
    root = tmp_path / "capture"
    writers = CsvWriters(root)
    writers.write("events.csv", {"t_ns": 1, "event_type": "capture_started"})
    writers.close()
    assert (root / "robot_state.csv").is_file()
    assert (root / "lidar.csv").is_file()
    context_header = (root / "context.csv").read_text(encoding="utf-8").splitlines()[0]
    assert context_header.startswith("t_ns,")
    assert "lstm_configured" in context_header
    write_runtime_metadata(
        root,
        camera="Astra-S",
        lidar="N10P",
        firmware="fw-test",
        clock="system_time",
        robot_config=Path("config.json"),
    )
    metadata = json.loads((root / "capture.json").read_text(encoding="utf-8"))
    assert metadata["ros"] is False
    assert metadata["ros2"] is False
    assert metadata["control_mode"] == "position_state"
    assert metadata["state_definition"] == ["x_m", "y_m", "theta_rad", "vx_mps", "vy_mps", "omega_radps"]


def test_pose_context_is_measurement_only() -> None:
    class Detection:
        xyxy = (1.0, 1.0, 3.0, 3.0)
        confidence = 0.8

    class Detector:
        def detect(self, image, timestamp_ns):
            return (Detection(),)

    calibration = {
        "camera_intrinsics": {"fx": 100.0, "fy": 100.0, "cx": 2.0, "cy": 2.0},
        "camera_to_robot": {"translation_m": [0.0, 0.0, 0.0], "rpy_rad": [0.0, 0.0, 0.0]},
    }
    frame = AstraFrame(
        1,
        np.zeros((4, 4, 3), dtype=np.uint8),
        np.full((4, 4), 1000, dtype=np.uint16),
        0.001,
        device_timestamp_ns=2_000,
    )
    record, detections = PoseContextProcessor(Detector(), calibration).process(frame, "frames/frame.jpg")
    assert detections
    assert record.context_valid is True
    assert record.frame_path == "frames/frame.jpg"
    assert record.camera_device_timestamp_ns == 2_000
    assert record.lstm_configured is False
    assert not hasattr(record, "trajectory")


def test_pose_context_marks_lstm_active_only_after_history_window() -> None:
    class Detection:
        xyxy = (1.0, 1.0, 3.0, 3.0)
        confidence = 0.8

    class Detector:
        def detect(self, image, timestamp_ns):
            return (Detection(),)

    class Lstm:
        def __call__(self, history):
            assert tuple(history.shape) == (1, 2, 5)
            return SimpleNamespace(
                context_velocity_xy=torch.tensor([[0.1, 0.0]], dtype=torch.float32),
                direction_probabilities=torch.tensor([[0.0, 1.0, 0.0, 0.0]], dtype=torch.float32),
            )

    calibration = {
        "camera_intrinsics": {"fx": 100.0, "fy": 100.0, "cx": 2.0, "cy": 2.0},
        "camera_to_robot": {"translation_m": [0.0, 0.0, 0.0], "rpy_rad": [0.0, 0.0, 0.0]},
    }
    processor = PoseContextProcessor(
        Detector(),
        calibration,
        lstm=Lstm(),
        lstm_path="/tmp/checkpoints/context.pt",
        observed_steps=2,
        dt_s=0.1,
    )
    frame = AstraFrame(
        1,
        np.zeros((4, 4, 3), dtype=np.uint8),
        np.full((4, 4), 1000, dtype=np.uint16),
        0.001,
    )
    warmup, _ = processor.process(frame, "frames/frame-1.jpg")
    active, _ = processor.process(
        AstraFrame(
            100_000_001,
            np.zeros((4, 4, 3), dtype=np.uint8),
            np.full((4, 4), 1000, dtype=np.uint16),
            0.001,
        ),
        "frames/frame-2.jpg",
    )
    assert warmup.context_valid is True
    assert warmup.lstm_active is False
    assert warmup.lstm_configured is True
    assert active.lstm_active is True
    assert active.lstm_configured is True
    assert active.lstm_path == "/tmp/checkpoints/context.pt"
    assert active.direction == "right"


def test_pose_context_fails_closed_on_out_of_range_lstm_speed() -> None:
    class Detection:
        xyxy = (1.0, 1.0, 3.0, 3.0)
        confidence = 0.8

    class Detector:
        def detect(self, image, timestamp_ns):
            return (Detection(),)

    class Lstm:
        def __call__(self, history):
            return SimpleNamespace(
                context_velocity_xy=torch.tensor([[3.0, 0.0]], dtype=torch.float32),
                direction_probabilities=torch.tensor([[0.0, 1.0, 0.0, 0.0]], dtype=torch.float32),
            )

    calibration = {
        "camera_intrinsics": {"fx": 100.0, "fy": 100.0, "cx": 2.0, "cy": 2.0},
        "camera_to_robot": {"translation_m": [0.0, 0.0, 0.0], "rpy_rad": [0.0, 0.0, 0.0]},
    }
    processor = PoseContextProcessor(Detector(), calibration, lstm=Lstm(), observed_steps=2, dt_s=0.1)
    processor.process(
        AstraFrame(1, np.zeros((4, 4, 3), dtype=np.uint8), np.full((4, 4), 1000, dtype=np.uint16), 0.001),
        "frames/frame-1.jpg",
    )
    invalid, _ = processor.process(
        AstraFrame(100_000_001, np.zeros((4, 4, 3), dtype=np.uint8), np.full((4, 4), 1000, dtype=np.uint16), 0.001),
        "frames/frame-2.jpg",
    )
    assert invalid.context_valid is False
    assert invalid.lstm_active is False
    assert invalid.direction == "unknown"
    assert invalid.speed_mps == pytest.approx(0.0)


def test_pose_context_rejects_unaligned_color_and_depth() -> None:
    class Detection:
        xyxy = (1.0, 1.0, 3.0, 3.0)
        confidence = 0.8

    class Detector:
        def detect(self, image, timestamp_ns):
            return (Detection(),)

    calibration = {
        "camera_intrinsics": {"fx": 100.0, "fy": 100.0, "cx": 2.0, "cy": 2.0},
        "camera_to_robot": {"translation_m": [0.0, 0.0, 0.0], "rpy_rad": [0.0, 0.0, 0.0]},
    }
    frame = AstraFrame(1, np.zeros((4, 4, 3), dtype=np.uint8), np.full((2, 2), 1000, dtype=np.uint16), 0.001)
    with pytest.raises(RuntimeError, match="pixel-aligned"):
        PoseContextProcessor(Detector(), calibration).process(frame, "frames/frame.jpg")
