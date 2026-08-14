#include "control/stm_c_api.h"

#include "control/can.hpp"
#include "control/context.hpp"
#include "control/stm_serial.hpp"

#include <algorithm>
#include <cstring>
#include <exception>
#include <memory>
#include <mutex>
#include <span>
#include <string>
#include <vector>

struct cca_stm_handle {
    cca::hardware::SerialPort port;
    std::mutex mutex;
};

namespace {

void SetError(char* buffer, size_t capacity, const std::string& message) noexcept {
    if (buffer == nullptr || capacity == 0U) {
        return;
    }
    const auto count = std::min(capacity - 1U, message.size());
    std::memcpy(buffer, message.data(), count);
    buffer[count] = '\0';
}

}  // namespace

extern "C" int cca_stm_open(
    const char* port,
    const int baudrate,
    const int timeout_ms,
    cca_stm_handle** output,
    char* error_text,
    const size_t error_capacity
) {
    if (output == nullptr || port == nullptr) {
        SetError(error_text, error_capacity, "output and port are required");
        return 1;
    }
    try {
        auto handle = std::make_unique<cca_stm_handle>();
        handle->port.Open(port, baudrate, timeout_ms);
        *output = handle.release();
        return 0;
    } catch (const std::exception& error) {
        SetError(error_text, error_capacity, error.what());
        *output = nullptr;
        return 1;
    }
}

extern "C" int cca_stm_send_velocity(
    cca_stm_handle* handle,
    const double vx_mps,
    const double vy_mps,
    const double wz_radps,
    char* error_text,
    const size_t error_capacity
) {
    if (handle == nullptr) {
        SetError(error_text, error_capacity, "STM handle is null");
        return 1;
    }
    try {
        std::lock_guard lock(handle->mutex);
        handle->port.SendVelocity({vx_mps, vy_mps, wz_radps, 0U, 0U});
        return 0;
    } catch (const std::exception& error) {
        SetError(error_text, error_capacity, error.what());
        return 1;
    }
}

extern "C" int cca_stm_read(
    cca_stm_handle* handle,
    const uint64_t timestamp_ns,
    cca_stm_telemetry* output,
    const size_t capacity,
    size_t* count,
    char* error_text,
    const size_t error_capacity
) {
    if (handle == nullptr || output == nullptr || count == nullptr) {
        SetError(error_text, error_capacity, "STM read arguments are invalid");
        return 1;
    }
    try {
        std::lock_guard lock(handle->mutex);
        const auto samples = handle->port.ReadAvailable(timestamp_ns);
        if (samples.size() > capacity) {
            SetError(error_text, error_capacity, "STM telemetry output capacity is too small");
            *count = 0U;
            return 1;
        }
        for (size_t index = 0U; index < samples.size(); ++index) {
            const auto& sample = samples[index];
            output[index] = cca_stm_telemetry{
                sample.timestamp_ns,
                sample.flag_stop,
                sample.vx_mps,
                sample.vy_mps,
                sample.wz_radps,
                sample.accel_x_mps2,
                sample.accel_y_mps2,
                sample.accel_z_mps2,
                sample.gyro_x_radps,
                sample.gyro_y_radps,
                sample.gyro_z_radps,
                sample.voltage_v,
            };
        }
        *count = samples.size();
        return 0;
    } catch (const std::exception& error) {
        SetError(error_text, error_capacity, error.what());
        *count = 0U;
        return 1;
    }
}

extern "C" void cca_stm_send_zero(cca_stm_handle* handle) {
    if (handle != nullptr) {
        std::lock_guard lock(handle->mutex);
        handle->port.SendZero();
    }
}

extern "C" void cca_stm_close(cca_stm_handle* handle) {
    if (handle != nullptr) {
        {
            std::lock_guard lock(handle->mutex);
            handle->port.Close();
        }
        delete handle;
    }
}

extern "C" int cca_can_crc8(
    const uint8_t* data,
    const size_t size,
    uint8_t* output,
    char* error_text,
    const size_t error_capacity
) {
    if (output == nullptr || (data == nullptr && size != 0U)) {
        SetError(error_text, error_capacity, "CCA CAN CRC arguments are invalid");
        return 1;
    }
    try {
        *output = cca::hardware::CcaCanCrc8(std::span<const uint8_t>(data, size));
        return 0;
    } catch (const std::exception& error) {
        SetError(error_text, error_capacity, error.what());
        return 1;
    }
}

extern "C" int cca_can_encode_header(
    const uint8_t mode,
    const uint8_t sequence,
    const uint8_t deadline_ticks,
    const uint8_t profile,
    const uint8_t flags,
    cca_can_frame* output,
    char* error_text,
    const size_t error_capacity
) {
    if (output == nullptr) {
        SetError(error_text, error_capacity, "CCA CAN output is null");
        return 1;
    }
    try {
        const auto frame = cca::hardware::EncodeCcaCommandHeader(
            mode, sequence, deadline_ticks, profile, flags
        );
        output->arbitration_id = frame.arbitration_id;
        std::memcpy(output->data, frame.data.data(), frame.data.size());
        return 0;
    } catch (const std::exception& error) {
        SetError(error_text, error_capacity, error.what());
        return 1;
    }
}

extern "C" int cca_can_encode_body(
    const double vx_mps,
    const double vy_mps,
    const double wz_radps,
    const uint8_t sequence,
    const uint32_t arbitration_id,
    cca_can_frame* output,
    char* error_text,
    const size_t error_capacity
) {
    if (output == nullptr) {
        SetError(error_text, error_capacity, "CCA CAN output is null");
        return 1;
    }
    try {
        const auto frame = cca::hardware::EncodeCcaBodyVelocityPayload(
            vx_mps, vy_mps, wz_radps, sequence, arbitration_id
        );
        output->arbitration_id = frame.arbitration_id;
        std::memcpy(output->data, frame.data.data(), frame.data.size());
        return 0;
    } catch (const std::exception& error) {
        SetError(error_text, error_capacity, error.what());
        return 1;
    }
}

extern "C" int cca_can_decode(
    const uint32_t arbitration_id,
    const uint8_t* data,
    const size_t size,
    cca_can_decoded* output,
    char* error_text,
    const size_t error_capacity
) {
    if (data == nullptr || output == nullptr) {
        SetError(error_text, error_capacity, "CCA CAN decode arguments are invalid");
        return 1;
    }
    try {
        const auto frame = cca::hardware::DecodeCcaCanFrame(
            arbitration_id, std::span<const uint8_t>(data, size)
        );
        *output = cca_can_decoded{};
        output->kind = static_cast<int>(frame.kind);
        output->mode = frame.mode;
        output->sequence = frame.sequence;
        output->deadline_ticks = frame.deadline_ticks;
        output->profile = frame.profile;
        output->flags = frame.flags;
        output->status = frame.status;
        output->remaining_ticks = frame.remaining_ticks;
        output->vx_mps = frame.vx_mps;
        output->vy_mps = frame.vy_mps;
        output->wz_radps = frame.wz_radps;
        output->wheel_fl_radps = frame.wheel_fl_radps;
        output->wheel_fr_radps = frame.wheel_fr_radps;
        output->wheel_rl_radps = frame.wheel_rl_radps;
        output->wheel_rr_radps = frame.wheel_rr_radps;
        output->battery_mv = frame.battery_mv;
        output->pwm_mask = frame.pwm_mask;
        output->external_faults = frame.external_faults;
        return 0;
    } catch (const std::exception& error) {
        SetError(error_text, error_capacity, error.what());
        return 1;
    }
}

extern "C" int cca_context_score(
    const cca_context_score_input* input,
    cca_context_score_output* output,
    char* error_text,
    const size_t error_capacity
) {
    if (input == nullptr || output == nullptr) {
        SetError(error_text, error_capacity, "CCA context score arguments are invalid");
        return 1;
    }
    try {
        cca::ai::ContextConfig config{};
        config.distance_scale_m = input->distance_scale_m;
        config.closing_scale_mps = input->closing_scale_mps;
        config.cpa_time_scale_s = input->cpa_time_scale_s;
        config.bias = input->bias;
        for (size_t index = 0U; index < config.weights.size(); ++index) {
            config.weights[index] = input->weights[index];
        }
        const auto event = cca::ai::ScoreContext(
            input->track_id,
            input->timestamp_ns,
            {input->relative_position_x_m, input->relative_position_y_m},
            {input->relative_velocity_x_mps, input->relative_velocity_y_mps},
            input->local_density,
            input->detector_confidence,
            {input->robot_velocity_x_mps, input->robot_velocity_y_mps},
            {input->human_velocity_x_mps, input->human_velocity_y_mps},
            config
        );
        *output = cca_context_score_output{};
        output->track_id = event.track_id;
        output->timestamp_ns = event.timestamp_ns;
        output->phi = event.phi;
        output->detector_confidence = event.detector_confidence;
        output->calibration_valid = event.calibration_valid ? 1U : 0U;
        for (size_t index = 0U; index < event.features.size(); ++index) {
            output->features[index] = event.features[index];
        }
        return 0;
    } catch (const std::exception& error) {
        SetError(error_text, error_capacity, error.what());
        return 1;
    }
}
