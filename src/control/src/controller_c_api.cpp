#include "control/controller_c_api.h"

#include "control/controller.hpp"

#include <algorithm>
#include <cstring>
#include <exception>
#include <memory>
#include <mutex>
#include <span>
#include <stdexcept>
#include <string>

struct cca_controller_handle {
    cca::control::Controller controller;
    std::mutex mutex;

    cca_controller_handle(cca::control::ControllerKind kind, cca::control::ControllerConfig config)
        : controller(kind, config) {}
};

namespace {

void SetError(char* buffer, const size_t capacity, const std::string& message) noexcept {
    if (buffer == nullptr || capacity == 0U) {
        return;
    }
    const auto count = std::min(capacity - 1U, message.size());
    std::memcpy(buffer, message.data(), count);
    buffer[count] = '\0';
}

std::span<const double> Span(const double* values, const size_t size) {
    if (values == nullptr && size != 0U) {
        throw std::invalid_argument("controller input pointer is null");
    }
    return {values, size};
}

cca::control::ControllerKind Kind(const int value) {
    if (value < 0 || value > 4) {
        throw std::invalid_argument("controller kind is invalid");
    }
    return static_cast<cca::control::ControllerKind>(value);
}

}  // namespace

extern "C" size_t cca_controller_prediction_size(const size_t horizon) {
    return 6U * horizon;
}

extern "C" int cca_controller_create(
    const int kind,
    const double dt_s,
    const size_t horizon,
    const double deadline_ms,
    const double robot_radius_m,
    const double human_radius_m,
    const double human_clearance_m,
    cca_controller_handle** output,
    char* error_text,
    const size_t error_capacity
) {
    if (output == nullptr) {
        SetError(error_text, error_capacity, "controller output is null");
        return 1;
    }
    try {
        cca::control::ControllerConfig config{};
        config.dt_s = dt_s;
        config.horizon = horizon;
        config.deadline_ms = deadline_ms;
        config.robot_radius_m = robot_radius_m;
        config.human_radius_m = human_radius_m;
        config.human_clearance_m = human_clearance_m;
        auto handle = std::make_unique<cca_controller_handle>(Kind(kind), config);
        *output = handle.release();
        return 0;
    } catch (const std::exception& error) {
        *output = nullptr;
        SetError(error_text, error_capacity, error.what());
        return 1;
    }
}

extern "C" int cca_controller_command(
    cca_controller_handle* handle,
    const cca_controller_input* input,
    cca_controller_output* output,
    char* error_text,
    const size_t error_capacity
) {
    if (handle == nullptr || input == nullptr || output == nullptr) {
        SetError(error_text, error_capacity, "controller command arguments are invalid");
        return 1;
    }
    try {
        std::lock_guard lock(handle->mutex);
        const cca::control::ControllerInput controller_input{
            Span(input->state, input->state_size),
            Span(input->reference, input->reference_size),
            Span(input->previous_command, input->previous_command_size),
            Span(input->human_mean, input->human_mean_size),
            Span(input->context, input->context_size),
            Span(input->covariance, input->covariance_size),
            Span(input->nominal_robot, input->nominal_robot_size),
            Span(input->obstacles, input->obstacles_size),
            input->context_aware != 0,
        };
        const auto result = handle->controller.Command(controller_input);
        if (output->predicted_states == nullptr ||
            output->predicted_state_capacity < result.predicted_states.size()) {
            throw std::invalid_argument("controller predicted-state output capacity is too small");
        }
        std::copy(result.predicted_states.begin(), result.predicted_states.end(), output->predicted_states);
        for (size_t index = 0U; index < result.first_command_mps.size(); ++index) {
            output->first_command_mps[index] = result.first_command_mps[index];
        }
        output->predicted_state_count = result.predicted_states.size();
        output->solve_time_ms = result.solve_time_ms;
        output->objective = result.objective;
        output->maximum_constraint_violation = result.maximum_constraint_violation;
        output->iterations = result.iterations;
        output->status = result.status;
        output->deadline_missed = result.deadline_missed ? 1 : 0;
        output->risk_bound = result.risk_bound;
        output->maximum_risk_slack_m = result.maximum_risk_slack_m;
        return 0;
    } catch (const std::exception& error) {
        SetError(error_text, error_capacity, error.what());
        return 1;
    }
}

extern "C" void cca_controller_reset(cca_controller_handle* handle) {
    if (handle != nullptr) {
        std::lock_guard lock(handle->mutex);
        handle->controller.Reset();
    }
}

extern "C" void cca_controller_destroy(cca_controller_handle* handle) {
    delete handle;
}
