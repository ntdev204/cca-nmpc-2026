#ifndef CCA_RUNTIME_H
#define CCA_RUNTIME_H

#include <stdint.h>

typedef struct
{
    uint16_t status;
    int16_t applied_vx_mmps;
    int16_t applied_vy_mmps;
    int16_t applied_wz_mradps;
    uint8_t applied_sequence;
    uint8_t active_profile;
    uint8_t remaining_ticks;
} CcaRuntimeSnapshot;

void CcaRuntime_Init(uint8_t active_profile, uint8_t commissioned);
uint8_t CcaRuntime_OnCanFrame(uint32_t id, const uint8_t *data, uint8_t length);
void CcaRuntime_Tick(void);
uint8_t CcaRuntime_HasAuthority(void);
uint8_t CcaRuntime_IsArmed(void);
uint8_t CcaRuntime_IsSequenceArmed(uint8_t sequence);
void CcaRuntime_GetBodyCommand(float *vx_mps, float *vy_mps,
                               float *wz_radps, uint8_t *sequence);
void CcaRuntime_SetAppliedBody(float vx_mps, float vy_mps, float wz_radps,
                               uint8_t sequence);
void CcaRuntime_SetExternalStop(uint8_t stopped);
void CcaRuntime_GetSnapshot(CcaRuntimeSnapshot *snapshot);

#endif
