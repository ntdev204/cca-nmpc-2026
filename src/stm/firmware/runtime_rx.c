#include "runtime.h"

#include "firmware_config.h"
#include "runtime_internal.h"

static int16_t clampValue(int16_t value, int16_t limit, uint8_t *saturated)
{
    if (value > limit)
    {
        *saturated = 1u;
        return limit;
    }
    if (value < -limit)
    {
        *saturated = 1u;
        return (int16_t)-limit;
    }
    return value;
}

static uint8_t sequenceIsFresh(uint8_t sequence)
{
    volatile CcaRuntimeState *state = &cca_runtime_state;
    uint8_t delta = (uint8_t)(sequence - state->command.sequence);
    return (uint8_t)((state->have_sequence == 0u) ||
                     ((delta > 0u) && (delta < 128u)));
}

void CcaRuntime_ApplyReceived(const CcaCommandPayload *payload)
{
    volatile CcaRuntimeState *state = &cca_runtime_state;
    uint8_t saturated = 0u;
    uint16_t clear_mask = CCA_FAULT_TIMEOUT | CCA_FAULT_CRC |
        CCA_FAULT_SEQUENCE | CCA_FAULT_PROFILE | CCA_FAULT_MODE |
        CCA_FAULT_DEADLINE | CCA_FAULT_INCOMPLETE | CCA_STATE_SATURATED;
    state->faults &= (uint16_t)~clear_mask;
    state->command = *payload;
    state->command.vx_mmps = clampValue(state->command.vx_mmps,
                                        CCA_MAX_VX_MMPS, &saturated);
    state->command.vy_mmps = clampValue(state->command.vy_mmps,
                                        CCA_MAX_VY_MMPS, &saturated);
    state->command.wz_mradps = clampValue(state->command.wz_mradps,
                                          CCA_MAX_WZ_MRADPS, &saturated);
    if (saturated != 0u) state->faults |= CCA_STATE_SATURATED;
    state->authority = 1u;
    state->have_sequence = 1u;
    state->age_ticks = 0u;
    state->active_deadline_ticks = state->pending_header.deadline_ticks;
    state->armed =
        (uint8_t)((state->pending_header.flags & CCA_COMMAND_ARM) != 0u);
    if ((state->armed != 0u) && (state->commissioned == 0u))
    {
        CcaRuntime_StopWithFault(CCA_FAULT_NOT_COMMISSIONED);
    }
}

static uint16_t validate(const CcaCommandPayload *payload)
{
    volatile CcaRuntimeState *state = &cca_runtime_state;
    if ((state->header_valid == 0u) ||
        (payload->sequence != state->pending_header.sequence))
        return CCA_FAULT_INCOMPLETE;
    if (state->pending_header.profile != state->active_profile)
        return CCA_FAULT_PROFILE;
    if (state->pending_header.mode != CCA_MODE_BODY_VELOCITY)
        return CCA_FAULT_MODE;
    if ((state->pending_header.deadline_ticks == 0u) ||
        (state->pending_header.deadline_ticks > CCA_MAX_DEADLINE_TICKS))
        return CCA_FAULT_DEADLINE;
    if (sequenceIsFresh(payload->sequence) == 0u)
        return CCA_FAULT_SEQUENCE;
    return 0u;
}

uint8_t CcaRuntime_OnCanFrame(uint32_t id, const uint8_t *data, uint8_t length)
{
    volatile CcaRuntimeState *state = &cca_runtime_state;
    CcaCommandHeader header;
    CcaCommandPayload payload;
    uint16_t fault;
    if ((id != CCA_CAN_COMMAND_HEADER_ID) &&
        (id != CCA_CAN_COMMAND_PAYLOAD_ID))
        return 0u;
    if (length != 8u)
    {
        CcaRuntime_StopWithFault(CCA_FAULT_INCOMPLETE);
        return 1u;
    }
    if (id == CCA_CAN_COMMAND_HEADER_ID)
    {
        state->header_valid = CcaProtocol_DecodeHeader(data, &header);
        if (state->header_valid != 0u) state->pending_header = header;
        if (state->header_valid == 0u)
            CcaRuntime_StopWithFault(CCA_FAULT_CRC);
        return 1u;
    }
    if (CcaProtocol_DecodePayload(data, &payload) == 0u)
        fault = CCA_FAULT_CRC;
    else
        fault = validate(&payload);
    if (fault != 0u)
        CcaRuntime_StopWithFault(fault);
    else
        CcaRuntime_ApplyReceived(&payload);
    state->header_valid = 0u;
    return 1u;
}
