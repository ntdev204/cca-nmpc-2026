#ifndef CCA_KINEMATICS_H
#define CCA_KINEMATICS_H

void CcaKinematics_BodyToFirmwareWheels(float vx_mps, float vy_mps,
                                        float wz_radps, float lever_arm_m,
                                        float wheel_linear_mps[4]);
void CcaKinematics_FirmwareToCanonical(const float firmware_values[4],
                                       float canonical_values[4]);

#endif
