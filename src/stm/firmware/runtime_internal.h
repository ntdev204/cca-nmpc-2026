#ifndef CCA_RUNTIME_INTERNAL_H
#define CCA_RUNTIME_INTERNAL_H

#include "protocol.h"

typedef struct
{
    CcaCommandHeader pending_header;
    CcaCommandPayload command;
    CcaCommandPayload applied;
    uint16_t faults;
    uint8_t header_valid;
    uint8_t authority;
    uint8_t armed;
    uint8_t have_sequence;
    uint8_t active_profile;
    uint8_t commissioned;
    uint8_t age_ticks;
    uint8_t active_deadline_ticks;
} CcaRuntimeState;

extern volatile CcaRuntimeState cca_runtime_state;

void CcaRuntime_StopWithFault(uint16_t fault);
void CcaRuntime_ApplyReceived(const CcaCommandPayload *payload);

#endif
