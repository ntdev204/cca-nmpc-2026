#ifndef CCA_PROTOCOL_H
#define CCA_PROTOCOL_H

#include <stdint.h>

#define CCA_CAN_COMMAND_HEADER_ID  0x190u
#define CCA_CAN_COMMAND_PAYLOAD_ID 0x191u
#define CCA_CAN_STATUS_ID          0x198u
#define CCA_CAN_APPLIED_ID         0x199u
#define CCA_CAN_WHEELS_ABC_ID      0x19Au
#define CCA_CAN_WHEEL_D_ID         0x19Bu

#define CCA_PROTOCOL_MAGIC         0xCAu
#define CCA_PROTOCOL_VERSION       1u
#define CCA_MODE_BODY_VELOCITY     1u
#define CCA_MODE_WHEEL_TORQUE      2u
#define CCA_COMMAND_ARM            0x01u

#define CCA_STATE_AUTHORITY        0x0001u
#define CCA_STATE_ARMED            0x0002u
#define CCA_STATE_SATURATED        0x0004u
#define CCA_FAULT_TIMEOUT          0x0008u
#define CCA_FAULT_CRC              0x0010u
#define CCA_FAULT_SEQUENCE         0x0020u
#define CCA_FAULT_PROFILE          0x0040u
#define CCA_FAULT_MODE             0x0080u
#define CCA_FAULT_DEADLINE         0x0100u
#define CCA_FAULT_NOT_COMMISSIONED 0x0200u
#define CCA_FAULT_EXTERNAL_STOP    0x0400u
#define CCA_FAULT_INCOMPLETE       0x0800u

typedef struct
{
    uint8_t mode;
    uint8_t sequence;
    uint8_t deadline_ticks;
    uint8_t profile;
    uint8_t flags;
} CcaCommandHeader;

typedef struct
{
    int16_t vx_mmps;
    int16_t vy_mmps;
    int16_t wz_mradps;
    uint8_t sequence;
} CcaCommandPayload;

uint8_t CcaProtocol_Crc8(const uint8_t *data, uint8_t length);
uint8_t CcaProtocol_DecodeHeader(const uint8_t data[8],
                                 CcaCommandHeader *header);
uint8_t CcaProtocol_DecodePayload(const uint8_t data[8],
                                  CcaCommandPayload *payload);
void CcaProtocol_EncodeHeader(const CcaCommandHeader *header, uint8_t data[8]);
void CcaProtocol_EncodePayload(const CcaCommandPayload *payload,
                               uint8_t data[8]);
void CcaProtocol_WriteI16Be(int16_t value, uint8_t *output);
int16_t CcaProtocol_ReadI16Be(const uint8_t *input);

#endif
