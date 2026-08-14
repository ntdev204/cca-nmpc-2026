#pragma once

#include <stddef.h>

#if defined(_WIN32)
#define CCA_CONTROLLER_API __declspec(dllexport)
#else
#define CCA_CONTROLLER_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct cca_controller_handle cca_controller_handle;

typedef struct {
    const double* state;
    size_t state_size;
    const double* reference;
    size_t reference_size;
    const double* previous_command;
    size_t previous_command_size;
    const double* human_mean;
    size_t human_mean_size;
    const double* context;
    size_t context_size;
    const double* covariance;
    size_t covariance_size;
    const double* nominal_robot;
    size_t nominal_robot_size;
    const double* obstacles;
    size_t obstacles_size;
    int context_aware;
} cca_controller_input;

typedef struct {
    double first_command_mps[3];
    double* predicted_states;
    size_t predicted_state_capacity;
    size_t predicted_state_count;
    double solve_time_ms;
    double objective;
    double maximum_constraint_violation;
    int iterations;
    int status;
    int deadline_missed;
    double risk_bound;
    double maximum_risk_slack_m;
} cca_controller_output;

CCA_CONTROLLER_API size_t cca_controller_prediction_size(size_t horizon);

CCA_CONTROLLER_API int cca_controller_create(
    int kind,
    double dt_s,
    size_t horizon,
    double deadline_ms,
    double robot_radius_m,
    double human_radius_m,
    double human_clearance_m,
    cca_controller_handle** output,
    char* error_text,
    size_t error_capacity
);

CCA_CONTROLLER_API int cca_controller_command(
    cca_controller_handle* handle,
    const cca_controller_input* input,
    cca_controller_output* output,
    char* error_text,
    size_t error_capacity
);

CCA_CONTROLLER_API void cca_controller_reset(cca_controller_handle* handle);
CCA_CONTROLLER_API void cca_controller_destroy(cca_controller_handle* handle);

#ifdef __cplusplus
}
#endif
