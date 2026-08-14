#pragma once

#include <stddef.h>
#include <stdint.h>

#if defined(_WIN32)
#define CCA_STM_API __declspec(dllexport)
#else
#define CCA_STM_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct cca_stm_handle cca_stm_handle;

typedef struct {
    uint64_t timestamp_ns;
    uint8_t flag_stop;
    double vx_mps;
    double vy_mps;
    double wz_radps;
    double accel_x_mps2;
    double accel_y_mps2;
    double accel_z_mps2;
    double gyro_x_radps;
    double gyro_y_radps;
    double gyro_z_radps;
    double voltage_v;
} cca_stm_telemetry;

typedef struct {
    uint32_t arbitration_id;
    uint8_t data[8];
} cca_can_frame;

typedef struct {
    int kind;
    uint8_t mode;
    uint8_t sequence;
    uint8_t deadline_ticks;
    uint8_t profile;
    uint8_t flags;
    uint16_t status;
    uint8_t remaining_ticks;
    double vx_mps;
    double vy_mps;
    double wz_radps;
    double wheel_fl_radps;
    double wheel_fr_radps;
    double wheel_rl_radps;
    double wheel_rr_radps;
    uint16_t battery_mv;
    uint8_t pwm_mask;
    uint8_t external_faults;
} cca_can_decoded;

typedef struct {
    uint64_t track_id;
    uint64_t timestamp_ns;
    double relative_position_x_m;
    double relative_position_y_m;
    double relative_velocity_x_mps;
    double relative_velocity_y_mps;
    double robot_velocity_x_mps;
    double robot_velocity_y_mps;
    double human_velocity_x_mps;
    double human_velocity_y_mps;
    double local_density;
    double detector_confidence;
    double distance_scale_m;
    double closing_scale_mps;
    double cpa_time_scale_s;
    double bias;
    double weights[5];
} cca_context_score_input;

typedef struct {
    uint64_t track_id;
    uint64_t timestamp_ns;
    double phi;
    double detector_confidence;
    uint8_t calibration_valid;
    double features[5];
} cca_context_score_output;

CCA_STM_API int cca_stm_open(
    const char* port,
    int baudrate,
    int timeout_ms,
    cca_stm_handle** output,
    char* error_text,
    size_t error_capacity
);
CCA_STM_API int cca_stm_send_velocity(
    cca_stm_handle* handle,
    double vx_mps,
    double vy_mps,
    double wz_radps,
    char* error_text,
    size_t error_capacity
);
CCA_STM_API int cca_stm_read(
    cca_stm_handle* handle,
    uint64_t timestamp_ns,
    cca_stm_telemetry* output,
    size_t capacity,
    size_t* count,
    char* error_text,
    size_t error_capacity
);
CCA_STM_API void cca_stm_send_zero(cca_stm_handle* handle);
CCA_STM_API void cca_stm_close(cca_stm_handle* handle);

CCA_STM_API int cca_can_crc8(
    const uint8_t* data,
    size_t size,
    uint8_t* output,
    char* error_text,
    size_t error_capacity
);
CCA_STM_API int cca_can_encode_header(
    uint8_t mode,
    uint8_t sequence,
    uint8_t deadline_ticks,
    uint8_t profile,
    uint8_t flags,
    cca_can_frame* output,
    char* error_text,
    size_t error_capacity
);
CCA_STM_API int cca_can_encode_body(
    double vx_mps,
    double vy_mps,
    double wz_radps,
    uint8_t sequence,
    uint32_t arbitration_id,
    cca_can_frame* output,
    char* error_text,
    size_t error_capacity
);
CCA_STM_API int cca_can_decode(
    uint32_t arbitration_id,
    const uint8_t* data,
    size_t size,
    cca_can_decoded* output,
    char* error_text,
    size_t error_capacity
);

CCA_STM_API int cca_context_score(
    const cca_context_score_input* input,
    cca_context_score_output* output,
    char* error_text,
    size_t error_capacity
);

#ifdef __cplusplus
}
#endif
