#include "control/can.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <string>

namespace cca::hardware {

namespace {

std::int16_t QuantizedI16(double value, const char* name) {
    if (!std::isfinite(value)) {
        throw std::invalid_argument(std::string(name) + " must be finite");
    }
    const double scaled = std::nearbyint(value * 1000.0);
    if (scaled < static_cast<double>(std::numeric_limits<std::int16_t>::min()) ||
        scaled > static_cast<double>(std::numeric_limits<std::int16_t>::max())) {
        throw std::out_of_range(std::string(name) + " exceeds signed 16-bit CAN range");
    }
    return static_cast<std::int16_t>(scaled);
}

std::int16_t ReadI16(const std::array<std::uint8_t, 8U>& data, std::size_t offset) {
    const auto value = static_cast<std::uint16_t>(
        (static_cast<std::uint16_t>(data[offset]) << 8U) | data[offset + 1U]
    );
    return static_cast<std::int16_t>(value);
}

std::uint16_t ReadU16(const std::array<std::uint8_t, 8U>& data, std::size_t offset) {
    return static_cast<std::uint16_t>(
        (static_cast<std::uint16_t>(data[offset]) << 8U) | data[offset + 1U]
    );
}

void WriteI16(std::array<std::uint8_t, 8U>& data, std::size_t offset, std::int16_t value) {
    const auto raw = static_cast<std::uint16_t>(value);
    data[offset] = static_cast<std::uint8_t>(raw >> 8U);
    data[offset + 1U] = static_cast<std::uint8_t>(raw & 0xFFU);
}

std::array<std::uint8_t, 8U> CheckedPayload(std::span<const std::uint8_t> bytes) {
    if (bytes.size() != 8U) {
        throw std::invalid_argument("CCA CAN payload must contain exactly eight bytes");
    }
    std::array<std::uint8_t, 8U> payload{};
    std::copy(bytes.begin(), bytes.end(), payload.begin());
    if (CcaCanCrc8(std::span<const std::uint8_t>(payload.data(), 7U)) != payload[7]) {
        throw std::invalid_argument("CCA CAN payload CRC mismatch");
    }
    return payload;
}

}  // namespace

std::uint8_t CcaCanCrc8(std::span<const std::uint8_t> bytes) {
    std::uint8_t crc = 0xFFU;
    for (const auto value : bytes) {
        crc = static_cast<std::uint8_t>(crc ^ value);
        for (int bit = 0; bit < 8; ++bit) {
            crc = static_cast<std::uint8_t>(
                (crc & 0x80U) != 0U ? ((crc << 1U) ^ 0x1DU) : (crc << 1U)
            );
        }
    }
    return static_cast<std::uint8_t>(crc ^ 0xFFU);
}

CanFrame EncodeCcaCommandHeader(
    std::uint8_t mode,
    std::uint8_t sequence,
    std::uint8_t deadline_ticks,
    std::uint8_t profile,
    std::uint8_t flags
) {
    CanFrame frame{kCanCommandHeaderId, {kCanMagic, kCanVersion, mode, sequence, deadline_ticks, profile, flags, 0U}};
    frame.data[7] = CcaCanCrc8(std::span<const std::uint8_t>(frame.data.data(), 7U));
    return frame;
}

CanFrame EncodeCcaBodyVelocityPayload(
    double vx_mps,
    double vy_mps,
    double wz_radps,
    std::uint8_t sequence,
    std::uint32_t arbitration_id
) {
    if (arbitration_id != kCanCommandPayloadId && arbitration_id != kCanAppliedId) {
        throw std::invalid_argument("CCA body payload arbitration ID is invalid");
    }
    CanFrame frame{arbitration_id, {}};
    WriteI16(frame.data, 0U, QuantizedI16(vx_mps, "vx_mps"));
    WriteI16(frame.data, 2U, QuantizedI16(vy_mps, "vy_mps"));
    WriteI16(frame.data, 4U, QuantizedI16(wz_radps, "wz_radps"));
    frame.data[6] = sequence;
    frame.data[7] = CcaCanCrc8(std::span<const std::uint8_t>(frame.data.data(), 7U));
    return frame;
}

DecodedCanFrame DecodeCcaCanFrame(std::uint32_t arbitration_id, std::span<const std::uint8_t> data) {
    const auto payload = CheckedPayload(data);
    if (arbitration_id == kCanCommandHeaderId) {
        if (payload[0] != kCanMagic || payload[1] != kCanVersion) {
            throw std::invalid_argument("CCA command header magic/version mismatch");
        }
        return DecodedCanFrame{CanKind::command_header, payload[2], payload[3], payload[4], payload[5], payload[6]};
    }
    if (arbitration_id == kCanCommandPayloadId || arbitration_id == kCanAppliedId) {
        return DecodedCanFrame{
            arbitration_id == kCanCommandPayloadId ? CanKind::command_payload : CanKind::applied_body,
            0U,
            payload[6],
            0U,
            0U,
            0U,
            0U,
            0U,
            static_cast<double>(ReadI16(payload, 0U)) / 1000.0,
            static_cast<double>(ReadI16(payload, 2U)) / 1000.0,
            static_cast<double>(ReadI16(payload, 4U)) / 1000.0,
        };
    }
    if (arbitration_id == kCanStatusId) {
        if (payload[0] != kCanMagic || payload[1] != kCanVersion) {
            throw std::invalid_argument("CCA status magic/version mismatch");
        }
        DecodedCanFrame frame{};
        frame.kind = CanKind::status;
        frame.sequence = payload[2];
        frame.profile = payload[3];
        frame.status = ReadU16(payload, 4U);
        frame.remaining_ticks = payload[6];
        return frame;
    }
    if (arbitration_id == kCanWheelsAbcId) {
        DecodedCanFrame frame{};
        frame.kind = CanKind::wheel_speeds_abc;
        frame.wheel_fl_radps = static_cast<double>(ReadI16(payload, 0U)) / 100.0;
        frame.wheel_fr_radps = static_cast<double>(ReadI16(payload, 2U)) / 100.0;
        frame.wheel_rl_radps = static_cast<double>(ReadI16(payload, 4U)) / 100.0;
        frame.sequence = payload[6];
        return frame;
    }
    if (arbitration_id == kCanWheelDId) {
        DecodedCanFrame frame{};
        frame.kind = CanKind::wheel_speed_d;
        frame.wheel_rr_radps = static_cast<double>(ReadI16(payload, 0U)) / 100.0;
        frame.battery_mv = ReadU16(payload, 2U);
        frame.pwm_mask = payload[4];
        frame.external_faults = payload[5];
        frame.sequence = payload[6];
        return frame;
    }
    throw std::invalid_argument("unsupported CCA CAN arbitration ID");
}

}  // namespace cca::hardware
