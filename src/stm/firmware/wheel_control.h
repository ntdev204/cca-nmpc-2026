#ifndef CCA_WHEEL_CONTROL_H
#define CCA_WHEEL_CONTROL_H

#include <stdint.h>

void CcaWheelControl_Init(float kp, float ki, float period_s, float pwm_limit);
void CcaWheelControl_Reset(void);
void CcaWheelControl_Update(const float target_mps[4],
                            const float measured_mps[4],
                            int16_t pwm[4]);

#endif
