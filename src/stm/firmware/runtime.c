#include "runtime.h"

#include "runtime_internal.h"

volatile CcaRuntimeState cca_runtime_state;

void CcaRuntime_StopWithFault(uint16_t fault)
{
    volatile CcaRuntimeState *state = &cca_runtime_state;
    state->faults |= fault;
    state->armed = 0u;
    state->command.vx_mmps = 0;
    state->command.vy_mmps = 0;
    state->command.wz_mradps = 0;
    state->applied.vx_mmps = 0;
    state->applied.vy_mmps = 0;
    state->applied.wz_mradps = 0;
}

void CcaRuntime_Init(uint8_t profile, uint8_t commissioned)
{
    volatile CcaRuntimeState *state = &cca_runtime_state;
    state->pending_header.mode = 0u;
    state->command.sequence = 0u;
    state->applied.sequence = 0u;
    state->faults = 0u;
    state->header_valid = 0u;
    state->authority = 0u;
    state->armed = 0u;
    state->have_sequence = 0u;
    state->active_profile = profile;
    state->commissioned = commissioned;
    state->age_ticks = 0u;
    state->active_deadline_ticks = 0u;
    CcaRuntime_StopWithFault(commissioned ? 0u :
                             CCA_FAULT_NOT_COMMISSIONED);
}

void CcaRuntime_Tick(void)
{
    volatile CcaRuntimeState *state = &cca_runtime_state;
    if ((state->authority != 0u) && (state->armed != 0u))
    {
        ++state->age_ticks;
        if (state->age_ticks >= state->active_deadline_ticks)
        {
            CcaRuntime_StopWithFault(CCA_FAULT_TIMEOUT);
        }
    }
}

uint8_t CcaRuntime_HasAuthority(void)
{
    return cca_runtime_state.authority;
}

uint8_t CcaRuntime_IsArmed(void)
{
    return cca_runtime_state.armed;
}

uint8_t CcaRuntime_IsSequenceArmed(uint8_t sequence)
{
    volatile CcaRuntimeState *state = &cca_runtime_state;
    return (uint8_t)((state->authority != 0u) &&
                     (state->armed != 0u) &&
                     (state->command.sequence == sequence));
}

void CcaRuntime_GetBodyCommand(float *vx_mps, float *vy_mps, float *wz_radps,
                               uint8_t *sequence)
{
    volatile CcaRuntimeState *state = &cca_runtime_state;
    *vx_mps = state->armed ? (float)state->command.vx_mmps / 1000.0f : 0.0f;
    *vy_mps = state->armed ? (float)state->command.vy_mmps / 1000.0f : 0.0f;
    *wz_radps = state->armed ?
        (float)state->command.wz_mradps / 1000.0f : 0.0f;
    *sequence = state->command.sequence;
}

void CcaRuntime_SetAppliedBody(float vx_mps, float vy_mps, float wz_radps,
                               uint8_t sequence)
{
    volatile CcaRuntimeState *state = &cca_runtime_state;
    state->applied.vx_mmps = (int16_t)(vx_mps * 1000.0f);
    state->applied.vy_mmps = (int16_t)(vy_mps * 1000.0f);
    state->applied.wz_mradps = (int16_t)(wz_radps * 1000.0f);
    state->applied.sequence = sequence;
}

void CcaRuntime_SetExternalStop(uint8_t stopped)
{
    if (stopped != 0u)
    {
        CcaRuntime_StopWithFault(CCA_FAULT_EXTERNAL_STOP);
    }
    else
    {
        cca_runtime_state.faults =
            (uint16_t)(cca_runtime_state.faults & 0xFBFFu);
    }
}

void CcaRuntime_GetSnapshot(CcaRuntimeSnapshot *snapshot)
{
    volatile CcaRuntimeState *state = &cca_runtime_state;
    uint16_t status = state->faults;
    if (state->authority != 0u) status |= CCA_STATE_AUTHORITY;
    if (state->armed != 0u) status |= CCA_STATE_ARMED;
    snapshot->status = status;
    snapshot->applied_vx_mmps = state->applied.vx_mmps;
    snapshot->applied_vy_mmps = state->applied.vy_mmps;
    snapshot->applied_wz_mradps = state->applied.wz_mradps;
    snapshot->applied_sequence = state->applied.sequence;
    snapshot->active_profile = state->active_profile;
    snapshot->remaining_ticks =
        (state->armed && (state->age_ticks < state->active_deadline_ticks)) ?
        (uint8_t)(state->active_deadline_ticks - state->age_ticks) : 0u;
}
