#include "control/stm_serial.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <limits>
#include <stdexcept>

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <cerrno>
#include <fcntl.h>
#include <termios.h>
#include <unistd.h>
#endif

namespace cca::hardware {

namespace {

std::uint8_t XorChecksum(std::span<const std::uint8_t> bytes) {
    std::uint8_t checksum = 0U;
    for (const auto byte : bytes) {
        checksum = static_cast<std::uint8_t>(checksum ^ byte);
    }
    return checksum;
}

std::int16_t ReadI16(const std::uint8_t* bytes, std::size_t offset) {
    const auto value = static_cast<std::uint16_t>(
        (static_cast<std::uint16_t>(bytes[offset]) << 8U) | bytes[offset + 1U]
    );
    return static_cast<std::int16_t>(value);
}

std::uint16_t ReadU16(const std::uint8_t* bytes, std::size_t offset) {
    return static_cast<std::uint16_t>(
        (static_cast<std::uint16_t>(bytes[offset]) << 8U) | bytes[offset + 1U]
    );
}

std::int16_t Quantize(double value) {
    if (!std::isfinite(value)) {
        throw std::invalid_argument("STM32 command must be finite");
    }
    const double scaled = std::trunc(value * 1000.0);
    if (scaled < static_cast<double>(std::numeric_limits<std::int16_t>::min()) ||
        scaled > static_cast<double>(std::numeric_limits<std::int16_t>::max())) {
        throw std::out_of_range("STM32 command exceeds signed 16-bit millimetre range");
    }
    return static_cast<std::int16_t>(scaled);
}

void AppendI16(std::array<std::uint8_t, kCommandSize>& frame, std::size_t offset, std::int16_t value) {
    const auto raw = static_cast<std::uint16_t>(value);
    frame[offset] = static_cast<std::uint8_t>(raw >> 8U);
    frame[offset + 1U] = static_cast<std::uint8_t>(raw & 0xFFU);
}

#ifndef _WIN32
speed_t BaudConstant(int baudrate) {
    switch (baudrate) {
        case 9600: return B9600;
        case 19200: return B19200;
        case 38400: return B38400;
        case 57600: return B57600;
        case 115200: return B115200;
        case 230400: return B230400;
        case 460800: return B460800;
        case 921600: return B921600;
        default: throw std::invalid_argument("unsupported POSIX serial baudrate");
    }
}
#endif

}  // namespace

std::array<std::uint8_t, kCommandSize> EncodeVelocityCommand(const VelocityCommand& command) {
    const auto vx = Quantize(command.vx_mps);
    const auto vy = Quantize(command.vy_mps);
    const auto wz = Quantize(command.wz_radps);
    std::array<std::uint8_t, kCommandSize> frame{};
    frame[0] = kFrameHeader;
    frame[1] = command.mode;
    frame[2] = command.reserved;
    AppendI16(frame, 3U, vx);
    AppendI16(frame, 5U, vy);
    AppendI16(frame, 7U, wz);
    frame[9] = XorChecksum(std::span<const std::uint8_t>(frame.data(), 9U));
    frame[10] = kFrameTail;
    return frame;
}

std::vector<Telemetry> TelemetryDecoder::Feed(
    std::span<const std::uint8_t> bytes,
    std::uint64_t timestamp_ns
) {
    buffer_.insert(buffer_.end(), bytes.begin(), bytes.end());
    std::vector<Telemetry> decoded;
    while (true) {
        const auto header = std::find(buffer_.begin(), buffer_.end(), kFrameHeader);
        if (header == buffer_.end()) {
            if (!buffer_.empty() && buffer_.back() == kFrameHeader) {
                buffer_.erase(buffer_.begin(), buffer_.end() - 1);
            } else {
                buffer_.clear();
            }
            return decoded;
        }
        buffer_.erase(buffer_.begin(), header);
        if (buffer_.size() < kTelemetrySize) {
            return decoded;
        }
        const auto checksum = XorChecksum(std::span<const std::uint8_t>(buffer_.data(), 22U));
        if (buffer_[22] != checksum || buffer_[23] != kFrameTail) {
            buffer_.erase(buffer_.begin());
            continue;
        }
        const auto* packet = buffer_.data();
        decoded.push_back(Telemetry{
            timestamp_ns,
            packet[1],
            static_cast<double>(ReadI16(packet, 2U)) / 1000.0,
            static_cast<double>(ReadI16(packet, 4U)) / 1000.0,
            static_cast<double>(ReadI16(packet, 6U)) / 1000.0,
            static_cast<double>(ReadI16(packet, 8U)) / 1671.84,
            static_cast<double>(ReadI16(packet, 10U)) / 1671.84,
            static_cast<double>(ReadI16(packet, 12U)) / 1671.84,
            static_cast<double>(ReadI16(packet, 14U)) * 0.00026644,
            static_cast<double>(ReadI16(packet, 16U)) * 0.00026644,
            static_cast<double>(ReadI16(packet, 18U)) * 0.00026644,
            static_cast<double>(ReadU16(packet, 20U)) / 1000.0,
        });
        buffer_.erase(buffer_.begin(), buffer_.begin() + static_cast<std::ptrdiff_t>(kTelemetrySize));
    }
}

struct SerialPort::Impl {
#ifdef _WIN32
    HANDLE handle = INVALID_HANDLE_VALUE;
#else
    int fd = -1;
#endif
    int timeout_ms = 100;
};

SerialPort::SerialPort() : impl_(std::make_unique<Impl>()) {}

SerialPort::~SerialPort() { Close(); }

void SerialPort::Open(const std::string& port, int baudrate, int timeout_ms) {
    if (port.empty() || baudrate <= 0 || timeout_ms <= 0) {
        throw std::invalid_argument("serial port, baudrate and timeout must be valid");
    }
    Close();
    impl_->timeout_ms = timeout_ms;
#ifdef _WIN32
    const std::string device = port.rfind("\\\\.\\", 0U) == 0U ? port : "\\\\.\\" + port;
    impl_->handle = CreateFileA(
        device.c_str(), GENERIC_READ | GENERIC_WRITE, 0, nullptr, OPEN_EXISTING, 0, nullptr
    );
    if (impl_->handle == INVALID_HANDLE_VALUE) {
        throw std::runtime_error("unable to open STM32 serial port");
    }
    DCB state{};
    state.DCBlength = sizeof(DCB);
    if (!GetCommState(impl_->handle, &state)) {
        Close();
        throw std::runtime_error("unable to read STM32 serial configuration");
    }
    state.BaudRate = static_cast<DWORD>(baudrate);
    state.ByteSize = 8;
    state.Parity = NOPARITY;
    state.StopBits = ONESTOPBIT;
    state.fBinary = TRUE;
    state.fDtrControl = DTR_CONTROL_DISABLE;
    state.fRtsControl = RTS_CONTROL_DISABLE;
    if (!SetCommState(impl_->handle, &state)) {
        Close();
        throw std::runtime_error("unable to configure STM32 serial port");
    }
    COMMTIMEOUTS timeouts{};
    timeouts.ReadIntervalTimeout = static_cast<DWORD>(timeout_ms);
    timeouts.ReadTotalTimeoutConstant = static_cast<DWORD>(timeout_ms);
    timeouts.WriteTotalTimeoutConstant = static_cast<DWORD>(timeout_ms);
    if (!SetCommTimeouts(impl_->handle, &timeouts)) {
        Close();
        throw std::runtime_error("unable to configure STM32 serial timeouts");
    }
#else
    impl_->fd = ::open(port.c_str(), O_RDWR | O_NOCTTY);
    if (impl_->fd < 0) {
        throw std::runtime_error("unable to open STM32 serial port: " + std::string(std::strerror(errno)));
    }
    termios state{};
    if (tcgetattr(impl_->fd, &state) != 0) {
        Close();
        throw std::runtime_error("unable to read STM32 serial configuration");
    }
    cfmakeraw(&state);
    const auto speed = BaudConstant(baudrate);
    cfsetispeed(&state, speed);
    cfsetospeed(&state, speed);
    state.c_cflag |= CLOCAL | CREAD;
    state.c_cflag &= static_cast<tcflag_t>(~PARENB);
    state.c_cflag &= static_cast<tcflag_t>(~CSTOPB);
    state.c_cflag &= static_cast<tcflag_t>(~CSIZE);
    state.c_cflag |= CS8;
    state.c_cc[VMIN] = 0;
    state.c_cc[VTIME] = static_cast<cc_t>(std::clamp(timeout_ms / 100, 1, 255));
    if (tcsetattr(impl_->fd, TCSANOW, &state) != 0) {
        Close();
        throw std::runtime_error("unable to configure STM32 serial port");
    }
#endif
}

void SerialPort::Close() noexcept {
#ifdef _WIN32
    if (impl_ && impl_->handle != INVALID_HANDLE_VALUE) {
        CloseHandle(impl_->handle);
        impl_->handle = INVALID_HANDLE_VALUE;
    }
#else
    if (impl_ && impl_->fd >= 0) {
        ::close(impl_->fd);
        impl_->fd = -1;
    }
#endif
    decoder_ = TelemetryDecoder{};
}

bool SerialPort::IsOpen() const noexcept {
#ifdef _WIN32
    return impl_ && impl_->handle != INVALID_HANDLE_VALUE;
#else
    return impl_ && impl_->fd >= 0;
#endif
}

void SerialPort::SendVelocity(const VelocityCommand& command) {
    if (!IsOpen()) {
        throw std::runtime_error("STM32 serial port is not open");
    }
    const auto frame = EncodeVelocityCommand(command);
    std::size_t written = 0U;
    while (written < frame.size()) {
#ifdef _WIN32
        DWORD count = 0U;
        if (!WriteFile(impl_->handle, frame.data() + written, static_cast<DWORD>(frame.size() - written), &count, nullptr)) {
            throw std::runtime_error("STM32 serial write failed");
        }
#else
        const auto count = ::write(impl_->fd, frame.data() + written, frame.size() - written);
        if (count < 0) {
            if (errno == EINTR) {
                continue;
            }
            throw std::runtime_error("STM32 serial write failed: " + std::string(std::strerror(errno)));
        }
#endif
        if (count == 0U) {
            throw std::runtime_error("STM32 serial write made no progress");
        }
        written += static_cast<std::size_t>(count);
    }
}

std::vector<Telemetry> SerialPort::ReadAvailable(std::uint64_t timestamp_ns) {
    if (!IsOpen()) {
        throw std::runtime_error("STM32 serial port is not open");
    }
    std::array<std::uint8_t, 512> bytes{};
#ifdef _WIN32
    DWORD count = 0U;
    if (!ReadFile(impl_->handle, bytes.data(), static_cast<DWORD>(bytes.size()), &count, nullptr)) {
        throw std::runtime_error("STM32 serial read failed");
    }
#else
    const auto count = ::read(impl_->fd, bytes.data(), bytes.size());
    if (count < 0) {
        if (errno == EINTR || errno == EAGAIN || errno == EWOULDBLOCK) {
            return {};
        }
        throw std::runtime_error("STM32 serial read failed: " + std::string(std::strerror(errno)));
    }
#endif
    return decoder_.Feed(std::span<const std::uint8_t>(bytes.data(), static_cast<std::size_t>(count)), timestamp_ns);
}

void SerialPort::SendZero() noexcept {
    try {
        SendVelocity(VelocityCommand{});
    } catch (...) {
    }
}

}  // namespace cca::hardware
