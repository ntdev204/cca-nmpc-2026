#pragma once

#include <array>
#include <cstdint>
#include <span>

namespace cca::hardware {

inline constexpr std::uint32_t kCanCommandHeaderId = 0x190U;
inline constexpr std::uint32_t kCanCommandPayloadId = 0x191U;
inline constexpr std::uint32_t kCanStatusId = 0x198U;
inline constexpr std::uint32_t kCanAppliedId = 0x199U;
inline constexpr std::uint32_t kCanWheelsAbcId = 0x19AU;
inline constexpr std::uint32_t kCanWheelDId = 0x19BU;
inline constexpr std::uint8_t kCanMagic = 0xCAU;
inline constexpr std::uint8_t kCanVersion = 1U;

struct CanFrame {
    std::uint32_t arbitration_id{};
    std::array<std::uint8_t, 8U> data{};
};

enum class CanKind {
    command_header,
    command_payload,
    applied_body,
    status,
    wheel_speeds_abc,
    wheel_speed_d,
};

struct DecodedCanFrame {
    CanKind kind{};
    std::uint8_t mode{};
    std::uint8_t sequence{};
    std::uint8_t deadline_ticks{};
    std::uint8_t profile{};
    std::uint8_t flags{};
    std::uint16_t status{};
    std::uint8_t remaining_ticks{};
    double vx_mps{};
    double vy_mps{};
    double wz_radps{};
    double wheel_fl_radps{};
    double wheel_fr_radps{};
    double wheel_rl_radps{};
    double wheel_rr_radps{};
    std::uint16_t battery_mv{};
    std::uint8_t pwm_mask{};
    std::uint8_t external_faults{};
};

std::uint8_t CcaCanCrc8(std::span<const std::uint8_t> bytes);
CanFrame EncodeCcaCommandHeader(
    std::uint8_t mode,
    std::uint8_t sequence,
    std::uint8_t deadline_ticks,
    std::uint8_t profile,
    std::uint8_t flags
);
CanFrame EncodeCcaBodyVelocityPayload(
    double vx_mps,
    double vy_mps,
    double wz_radps,
    std::uint8_t sequence,
    std::uint32_t arbitration_id = kCanCommandPayloadId
);
DecodedCanFrame DecodeCcaCanFrame(std::uint32_t arbitration_id, std::span<const std::uint8_t> data);

}  // namespace cca::hardware
