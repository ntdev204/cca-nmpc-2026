#include "protocol.h"

uint8_t CcaProtocol_Crc8(const uint8_t *data, uint8_t length)
{
    uint8_t crc = 0xFFu;
    uint8_t i;
    uint8_t bit;
    for (i = 0u; i < length; ++i)
    {
        crc ^= data[i];
        for (bit = 0u; bit < 8u; ++bit)
        {
            crc = (crc & 0x80u) ?
                (uint8_t)((crc << 1u) ^ 0x1Du) : (uint8_t)(crc << 1u);
        }
    }
    return (uint8_t)(crc ^ 0xFFu);
}

void CcaProtocol_WriteI16Be(int16_t value, uint8_t *output)
{
    uint16_t raw = (uint16_t)value;
    output[0] = (uint8_t)(raw >> 8u);
    output[1] = (uint8_t)raw;
}

int16_t CcaProtocol_ReadI16Be(const uint8_t *input)
{
    uint16_t raw = ((uint16_t)input[0] << 8u) | (uint16_t)input[1];
    return (int16_t)raw;
}

uint8_t CcaProtocol_DecodeHeader(const uint8_t data[8],
                                 CcaCommandHeader *header)
{
    if ((data[0] != CCA_PROTOCOL_MAGIC) ||
        (data[1] != CCA_PROTOCOL_VERSION) ||
        (data[7] != CcaProtocol_Crc8(data, 7u)))
    {
        return 0u;
    }
    header->mode = data[2];
    header->sequence = data[3];
    header->deadline_ticks = data[4];
    header->profile = data[5];
    header->flags = data[6];
    return 1u;
}

uint8_t CcaProtocol_DecodePayload(const uint8_t data[8],
                                  CcaCommandPayload *payload)
{
    if (data[7] != CcaProtocol_Crc8(data, 7u))
    {
        return 0u;
    }
    payload->vx_mmps = CcaProtocol_ReadI16Be(&data[0]);
    payload->vy_mmps = CcaProtocol_ReadI16Be(&data[2]);
    payload->wz_mradps = CcaProtocol_ReadI16Be(&data[4]);
    payload->sequence = data[6];
    return 1u;
}

void CcaProtocol_EncodeHeader(const CcaCommandHeader *header, uint8_t data[8])
{
    data[0] = CCA_PROTOCOL_MAGIC;
    data[1] = CCA_PROTOCOL_VERSION;
    data[2] = header->mode;
    data[3] = header->sequence;
    data[4] = header->deadline_ticks;
    data[5] = header->profile;
    data[6] = header->flags;
    data[7] = CcaProtocol_Crc8(data, 7u);
}

void CcaProtocol_EncodePayload(const CcaCommandPayload *payload,
                               uint8_t data[8])
{
    CcaProtocol_WriteI16Be(payload->vx_mmps, &data[0]);
    CcaProtocol_WriteI16Be(payload->vy_mmps, &data[2]);
    CcaProtocol_WriteI16Be(payload->wz_mradps, &data[4]);
    data[6] = payload->sequence;
    data[7] = CcaProtocol_Crc8(data, 7u);
}
