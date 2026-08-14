#ifndef CCA_TELEMETRY_H
#define CCA_TELEMETRY_H

#include <stdint.h>

void CcaTelemetry_EncodeStatus(uint8_t data[8]);
void CcaTelemetry_EncodeApplied(uint8_t data[8]);
void CcaTelemetry_EncodeWheelsAbc(const float firmware_wheel_mps[4],
                                  float wheel_radius_m, uint8_t data[8]);
void CcaTelemetry_EncodeWheelD(const float firmware_wheel_mps[4],
                              float wheel_radius_m, uint16_t battery_mv,
                              uint8_t pwm_active_mask,
                              uint8_t external_faults, uint8_t data[8]);

#endif
