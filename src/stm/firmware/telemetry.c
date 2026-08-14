#include "telemetry.h"

#include "kinematics.h"
#include "protocol.h"
#include "runtime.h"

static int16_t wheelCentirad(float linear_mps, float radius_m)
{
    float scaled = (radius_m > 0.0f) ? (linear_mps / radius_m) * 100.0f : 0.0f;
    if (scaled > 32767.0f) return 32767;
    if (scaled < -32768.0f) return -32768;
    return (int16_t)scaled;
}

void CcaTelemetry_EncodeStatus(uint8_t data[8])
{
    CcaRuntimeSnapshot snapshot;
    CcaRuntime_GetSnapshot(&snapshot);
    data[0] = CCA_PROTOCOL_MAGIC;
    data[1] = CCA_PROTOCOL_VERSION;
    data[2] = snapshot.applied_sequence;
    data[3] = snapshot.active_profile;
    data[4] = (uint8_t)(snapshot.status >> 8u);
    data[5] = (uint8_t)snapshot.status;
    data[6] = snapshot.remaining_ticks;
    data[7] = CcaProtocol_Crc8(data, 7u);
}

void CcaTelemetry_EncodeApplied(uint8_t data[8])
{
    CcaRuntimeSnapshot snapshot;
    CcaCommandPayload payload;
    CcaRuntime_GetSnapshot(&snapshot);
    payload.vx_mmps = snapshot.applied_vx_mmps;
    payload.vy_mmps = snapshot.applied_vy_mmps;
    payload.wz_mradps = snapshot.applied_wz_mradps;
    payload.sequence = snapshot.applied_sequence;
    CcaProtocol_EncodePayload(&payload, data);
}

void CcaTelemetry_EncodeWheelsAbc(const float firmware_wheel_mps[4],
                                  float radius_m, uint8_t data[8])
{
    float canonical[4];
    CcaRuntimeSnapshot snapshot;
    CcaKinematics_FirmwareToCanonical(firmware_wheel_mps, canonical);
    CcaRuntime_GetSnapshot(&snapshot);
    CcaProtocol_WriteI16Be(wheelCentirad(canonical[0], radius_m), &data[0]);
    CcaProtocol_WriteI16Be(wheelCentirad(canonical[1], radius_m), &data[2]);
    CcaProtocol_WriteI16Be(wheelCentirad(canonical[2], radius_m), &data[4]);
    data[6] = snapshot.applied_sequence;
    data[7] = CcaProtocol_Crc8(data, 7u);
}

void CcaTelemetry_EncodeWheelD(const float firmware_wheel_mps[4],
                              float radius_m, uint16_t battery_mv,
                              uint8_t pwm_mask, uint8_t external_faults,
                              uint8_t data[8])
{
    float canonical[4];
    CcaRuntimeSnapshot snapshot;
    CcaKinematics_FirmwareToCanonical(firmware_wheel_mps, canonical);
    CcaRuntime_GetSnapshot(&snapshot);
    CcaProtocol_WriteI16Be(wheelCentirad(canonical[3], radius_m), &data[0]);
    data[2] = (uint8_t)(battery_mv >> 8u);
    data[3] = (uint8_t)battery_mv;
    data[4] = pwm_mask;
    data[5] = external_faults;
    data[6] = snapshot.applied_sequence;
    data[7] = CcaProtocol_Crc8(data, 7u);
}
