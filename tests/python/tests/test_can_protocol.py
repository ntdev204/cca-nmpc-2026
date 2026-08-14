import pytest

from shared import (
    CCA_CAN_APPLIED_ID,
    CCA_CAN_COMMAND_HEADER_ID,
    CCA_CAN_COMMAND_PAYLOAD_ID,
    CCA_CAN_MAGIC,
    CCA_CAN_STATUS_ID,
    CCA_CAN_WHEELS_ABC_ID,
    CCA_CAN_WHEEL_D_ID,
    cca_crc8,
    decode_cca_can_frame,
    encode_cca_body_velocity_payload,
    encode_cca_command_header,
)


def frame(payload: bytes) -> bytes:
    return payload + bytes((cca_crc8(payload),))


def test_decode_applied_body_matches_stm_big_endian_units() -> None:
    payload = bytes.fromhex("0064FFCE01F42A")
    decoded = decode_cca_can_frame(CCA_CAN_APPLIED_ID, frame(payload))
    assert decoded["kind"] == "applied_body"
    assert decoded["vx_mps"] == pytest.approx(0.1)
    assert decoded["vy_mps"] == pytest.approx(-0.05)
    assert decoded["wz_radps"] == pytest.approx(0.5)
    assert decoded["sequence"] == 0x2A


def test_decode_status_checks_magic_and_status_bits() -> None:
    payload = bytes((CCA_CAN_MAGIC, 1, 7, 3, 0x04, 0x08, 12))
    decoded = decode_cca_can_frame(CCA_CAN_STATUS_ID, frame(payload))
    assert decoded == {
        "kind": "status",
        "sequence": 7,
        "profile": 3,
        "status": 0x0408,
        "remaining_ticks": 12,
    }


def test_decode_wheels_and_battery_fields() -> None:
    abc = decode_cca_can_frame(CCA_CAN_WHEELS_ABC_ID, frame(bytes.fromhex("0064FFCE0000002A")[:7]))
    wheel_d = decode_cca_can_frame(CCA_CAN_WHEEL_D_ID, frame(bytes.fromhex("FF9C30390102002A")[:7]))
    assert abc["wheel_fl_radps"] == pytest.approx(1.0)
    assert abc["wheel_fr_radps"] == pytest.approx(-0.5)
    assert abc["sequence"] == 0
    assert wheel_d["wheel_rr_radps"] == pytest.approx(-1.0)
    assert wheel_d["battery_mv"] == 12345
    assert wheel_d["pwm_mask"] == 1
    assert wheel_d["external_faults"] == 2


def test_decode_rejects_crc_length_and_unknown_id() -> None:
    with pytest.raises(ValueError, match="exactly eight"):
        decode_cca_can_frame(CCA_CAN_COMMAND_HEADER_ID, b"\x00")
    with pytest.raises(ValueError, match="CRC"):
        decode_cca_can_frame(CCA_CAN_COMMAND_HEADER_ID, b"\xCA\x01\x01\x01\x0A\x01\x01\x00")
    with pytest.raises(ValueError, match="unsupported"):
        decode_cca_can_frame(0x123, frame(bytes(7)))


def test_encode_command_frames_round_trip_with_stm_contract() -> None:
    header = encode_cca_command_header(
        mode=1,
        sequence=9,
        deadline_ticks=10,
        profile=0,
        flags=0,
    )
    payload = encode_cca_body_velocity_payload(
        vx_mps=0.125,
        vy_mps=-0.050,
        wz_radps=0.75,
        sequence=9,
    )
    assert decode_cca_can_frame(CCA_CAN_COMMAND_HEADER_ID, header) == {
        "kind": "command_header",
        "mode": 1,
        "sequence": 9,
        "deadline_ticks": 10,
        "profile": 0,
        "flags": 0,
    }
    assert decode_cca_can_frame(CCA_CAN_COMMAND_PAYLOAD_ID, payload) == {
        "kind": "command_payload",
        "vx_mps": pytest.approx(0.125),
        "vy_mps": pytest.approx(-0.05),
        "wz_radps": pytest.approx(0.75),
        "sequence": 9,
    }


def test_encode_command_frames_reject_invalid_values() -> None:
    with pytest.raises(ValueError, match="unsigned byte"):
        encode_cca_command_header(mode=256, sequence=0, deadline_ticks=10, profile=0, flags=0)
    with pytest.raises(ValueError, match="signed 16-bit"):
        encode_cca_body_velocity_payload(vx_mps=40.0, vy_mps=0.0, wz_radps=0.0, sequence=0)
