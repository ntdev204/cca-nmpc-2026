#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <span>
#include <string>
#include <vector>

namespace cca::hardware {

inline constexpr std::uint8_t kFrameHeader = 0x7BU;
inline constexpr std::uint8_t kFrameTail = 0x7DU;
inline constexpr std::size_t kCommandSize = 11U;
inline constexpr std::size_t kTelemetrySize = 24U;

struct VelocityCommand {
    double vx_mps{};
    double vy_mps{};
    double wz_radps{};
    std::uint8_t mode{};
    std::uint8_t reserved{};
};

struct Telemetry {
    std::uint64_t timestamp_ns{};
    std::uint8_t flag_stop{};
    double vx_mps{};
    double vy_mps{};
    double wz_radps{};
    double accel_x_mps2{};
    double accel_y_mps2{};
    double accel_z_mps2{};
    double gyro_x_radps{};
    double gyro_y_radps{};
    double gyro_z_radps{};
    double voltage_v{};
};

std::array<std::uint8_t, kCommandSize> EncodeVelocityCommand(
    const VelocityCommand& command
);

class TelemetryDecoder {
public:
    std::vector<Telemetry> Feed(std::span<const std::uint8_t> bytes, std::uint64_t timestamp_ns);

private:
    std::vector<std::uint8_t> buffer_;
};

class SerialPort {
public:
    SerialPort();
    ~SerialPort();
    SerialPort(const SerialPort&) = delete;
    SerialPort& operator=(const SerialPort&) = delete;
    SerialPort(SerialPort&&) = delete;
    SerialPort& operator=(SerialPort&&) = delete;

    void Open(const std::string& port, int baudrate, int timeout_ms = 100);
    void Close() noexcept;
    bool IsOpen() const noexcept;
    void SendVelocity(const VelocityCommand& command);
    std::vector<Telemetry> ReadAvailable(std::uint64_t timestamp_ns);
    void SendZero() noexcept;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
    TelemetryDecoder decoder_;
};

}  // namespace cca::hardware
