#ifndef CCA_FIRMWARE_CONFIG_H
#define CCA_FIRMWARE_CONFIG_H

/*
 * Commissioning lock: keep zero until wheel-speed gains, signs, bandwidth,
 * saturation and stop behavior have been measured on the active robot.
 */
#define CCA_WHEEL_LOOP_COMMISSIONED 0u
#define CCA_WHEEL_KP_PWM_PER_MPS    0.0f
#define CCA_WHEEL_KI_PWM_PER_M      0.0f
#define CCA_WHEEL_PWM_LIMIT         16000.0f
#define CCA_CONTROL_PERIOD_S        0.01f

#define CCA_MAX_VX_MMPS             500
#define CCA_MAX_VY_MMPS             500
#define CCA_MAX_WZ_MRADPS           1000
#define CCA_MAX_DEADLINE_TICKS      50u

#endif
