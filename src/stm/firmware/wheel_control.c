#include "wheel_control.h"

static float integrator[4];
static float gain_p;
static float gain_i;
static float sample_period_s;
static float output_limit;

static float clamp(float value, float limit)
{
    if (value > limit)
    {
        return limit;
    }
    if (value < -limit)
    {
        return -limit;
    }
    return value;
}

void CcaWheelControl_Init(float kp, float ki, float period_s, float pwm_limit)
{
    gain_p = kp;
    gain_i = ki;
    sample_period_s = period_s;
    output_limit = pwm_limit;
    CcaWheelControl_Reset();
}

void CcaWheelControl_Reset(void)
{
    uint8_t i;
    for (i = 0u; i < 4u; ++i)
    {
        integrator[i] = 0.0f;
    }
}

void CcaWheelControl_Update(const float target_mps[4],
                            const float measured_mps[4],
                            int16_t pwm[4])
{
    uint8_t i;
    for (i = 0u; i < 4u; ++i)
    {
        float error = target_mps[i] - measured_mps[i];
        float candidate = integrator[i] + gain_i * sample_period_s * error;
        float unsaturated = gain_p * error + candidate;
        float saturated = clamp(unsaturated, output_limit);
        if ((unsaturated == saturated) ||
            ((unsaturated > output_limit) && (error < 0.0f)) ||
            ((unsaturated < -output_limit) && (error > 0.0f)))
        {
            integrator[i] = candidate;
        }
        pwm[i] = (int16_t)clamp(gain_p * error + integrator[i], output_limit);
    }
}
