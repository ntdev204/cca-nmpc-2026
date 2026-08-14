#include "kinematics.h"

void CcaKinematics_BodyToFirmwareWheels(float vx_mps, float vy_mps,
                                        float wz_radps, float lever_arm_m,
                                        float wheel_linear_mps[4])
{
    float yaw = lever_arm_m * wz_radps;
    wheel_linear_mps[0] = vx_mps + vy_mps - yaw; /* channel A = RL */
    wheel_linear_mps[1] = vx_mps - vy_mps - yaw; /* channel B = FL */
    wheel_linear_mps[2] = vx_mps + vy_mps + yaw; /* channel C = FR */
    wheel_linear_mps[3] = vx_mps - vy_mps + yaw; /* channel D = RR */
}

void CcaKinematics_FirmwareToCanonical(const float firmware_values[4],
                                       float canonical_values[4])
{
    canonical_values[0] = firmware_values[1]; /* FL */
    canonical_values[1] = firmware_values[2]; /* FR */
    canonical_values[2] = firmware_values[0]; /* RL */
    canonical_values[3] = firmware_values[3]; /* RR */
}
