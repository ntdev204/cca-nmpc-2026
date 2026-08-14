#include <math.h>
#include <stdio.h>
#include <string.h>

#include "kinematics.h"
#include "protocol.h"
#include "runtime.h"
#include "telemetry.h"
#include "wheel_control.h"

static int failures;

#define CHECK(condition) do { \
    if (!(condition)) { \
        printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #condition); \
        ++failures; \
    } \
} while (0)

static void sendCommand(uint8_t profile, uint8_t mode, uint8_t sequence,
                        uint8_t deadline, uint8_t flags,
                        int16_t vx, int16_t vy, int16_t wz)
{
    CcaCommandHeader header = {mode, sequence, deadline, profile, flags};
    CcaCommandPayload payload = {vx, vy, wz, sequence};
    uint8_t frame[8];
    CcaProtocol_EncodeHeader(&header, frame);
    CHECK(CcaRuntime_OnCanFrame(CCA_CAN_COMMAND_HEADER_ID, frame, 8u) == 1u);
    CcaProtocol_EncodePayload(&payload, frame);
    CHECK(CcaRuntime_OnCanFrame(CCA_CAN_COMMAND_PAYLOAD_ID, frame, 8u) == 1u);
}

static void testCrcAndCodec(void)
{
    const uint8_t check[] = "123456789";
    CcaCommandPayload input = {-123, 456, -789, 42u};
    CcaCommandPayload output;
    uint8_t frame[8];
    CHECK(CcaProtocol_Crc8(check, 9u) == 0x4Bu);
    CcaProtocol_EncodePayload(&input, frame);
    CHECK(CcaProtocol_DecodePayload(frame, &output) == 1u);
    CHECK(memcmp(&input, &output, sizeof(input)) == 0);
    frame[2] ^= 0x01u;
    CHECK(CcaProtocol_DecodePayload(frame, &output) == 0u);
}

static void testRuntimeAcceptanceAndTimeout(void)
{
    CcaRuntimeSnapshot snapshot;
    float vx;
    float vy;
    float wz;
    uint8_t sequence;
    CcaRuntime_Init(0u, 1u);
    sendCommand(0u, CCA_MODE_BODY_VELOCITY, 7u, 3u, CCA_COMMAND_ARM,
                300, -200, 500);
    CHECK(CcaRuntime_HasAuthority() == 1u);
    CHECK(CcaRuntime_IsArmed() == 1u);
    CcaRuntime_GetBodyCommand(&vx, &vy, &wz, &sequence);
    CHECK(fabsf(vx - 0.3f) < 1e-6f);
    CHECK(fabsf(vy + 0.2f) < 1e-6f);
    CHECK(fabsf(wz - 0.5f) < 1e-6f);
    CHECK(sequence == 7u);
    CHECK(CcaRuntime_IsSequenceArmed(sequence) == 1u);
    CcaRuntime_Tick();
    CcaRuntime_Tick();
    CHECK(CcaRuntime_IsArmed() == 1u);
    CcaRuntime_Tick();
    CHECK(CcaRuntime_IsArmed() == 0u);
    CcaRuntime_GetSnapshot(&snapshot);
    CHECK((snapshot.status & CCA_FAULT_TIMEOUT) != 0u);
    CHECK((snapshot.status & CCA_STATE_AUTHORITY) != 0u);
}

static void testRejectionAndCommissioningLock(void)
{
    CcaRuntimeSnapshot snapshot;
    CcaRuntime_Init(0u, 1u);
    sendCommand(1u, CCA_MODE_BODY_VELOCITY, 1u, 5u, CCA_COMMAND_ARM,
                1, 2, 3);
    CcaRuntime_GetSnapshot(&snapshot);
    CHECK((snapshot.status & CCA_FAULT_PROFILE) != 0u);
    CHECK(CcaRuntime_HasAuthority() == 0u);

    CcaRuntime_Init(0u, 1u);
    sendCommand(0u, CCA_MODE_WHEEL_TORQUE, 1u, 5u, CCA_COMMAND_ARM,
                1, 2, 3);
    CcaRuntime_GetSnapshot(&snapshot);
    CHECK((snapshot.status & CCA_FAULT_MODE) != 0u);
    CHECK(CcaRuntime_IsArmed() == 0u);

    CcaRuntime_Init(0u, 0u);
    sendCommand(0u, CCA_MODE_BODY_VELOCITY, 1u, 5u, CCA_COMMAND_ARM,
                1, 2, 3);
    CcaRuntime_GetSnapshot(&snapshot);
    CHECK((snapshot.status & CCA_FAULT_NOT_COMMISSIONED) != 0u);
    CHECK((snapshot.status & CCA_STATE_AUTHORITY) != 0u);
    CHECK(CcaRuntime_IsArmed() == 0u);
}

static void testIncompleteHeaderCannotExtendDeadline(void)
{
    CcaCommandHeader header = {
        CCA_MODE_BODY_VELOCITY, 2u, 50u, 0u, CCA_COMMAND_ARM
    };
    uint8_t frame[8];
    CcaRuntime_Init(0u, 1u);
    sendCommand(0u, CCA_MODE_BODY_VELOCITY, 1u, 3u, CCA_COMMAND_ARM,
                100, 0, 0);
    CcaRuntime_Tick();
    CcaProtocol_EncodeHeader(&header, frame);
    CcaRuntime_OnCanFrame(CCA_CAN_COMMAND_HEADER_ID, frame, 8u);
    CcaRuntime_Tick();
    CHECK(CcaRuntime_IsArmed() == 1u);
    CcaRuntime_Tick();
    CHECK(CcaRuntime_IsArmed() == 0u);
}

static void testSaturationAndSequence(void)
{
    CcaRuntimeSnapshot snapshot;
    float vx;
    float vy;
    float wz;
    uint8_t sequence;
    CcaRuntime_Init(0u, 1u);
    sendCommand(0u, CCA_MODE_BODY_VELOCITY, 10u, 5u, CCA_COMMAND_ARM,
                2000, -2000, 3000);
    CcaRuntime_GetBodyCommand(&vx, &vy, &wz, &sequence);
    CHECK(fabsf(vx - 0.5f) < 1e-6f);
    CHECK(fabsf(vy + 0.5f) < 1e-6f);
    CHECK(fabsf(wz - 1.0f) < 1e-6f);
    CHECK(sequence == 10u);
    CcaRuntime_GetSnapshot(&snapshot);
    CHECK((snapshot.status & CCA_STATE_SATURATED) != 0u);

    sendCommand(0u, CCA_MODE_BODY_VELOCITY, 10u, 5u, CCA_COMMAND_ARM,
                100, 0, 0);
    CcaRuntime_GetSnapshot(&snapshot);
    CHECK((snapshot.status & CCA_FAULT_SEQUENCE) != 0u);
    CHECK(CcaRuntime_IsArmed() == 0u);
    CHECK(CcaRuntime_IsSequenceArmed(10u) == 0u);
}

static void testKinematicsAndWheelController(void)
{
    float firmware[4];
    float canonical[4];
    float measured[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    int16_t pwm[4];
    CcaKinematics_BodyToFirmwareWheels(1.0f, 0.2f, 0.3f, 0.332f,
                                       firmware);
    CcaKinematics_FirmwareToCanonical(firmware, canonical);
    CHECK(fabsf(canonical[0] - 0.7004f) < 1e-5f);
    CHECK(fabsf(canonical[1] - 1.2996f) < 1e-5f);
    CHECK(fabsf(canonical[2] - 1.1004f) < 1e-5f);
    CHECK(fabsf(canonical[3] - 0.8996f) < 1e-5f);

    CcaWheelControl_Init(100.0f, 10.0f, 0.01f, 1000.0f);
    CcaWheelControl_Update(firmware, measured, pwm);
    CHECK((pwm[0] > 0) && (pwm[1] > 0) &&
          (pwm[2] > 0) && (pwm[3] > 0));
    CcaWheelControl_Reset();
}

static void testTelemetryCrc(void)
{
    uint8_t frame[8];
    float wheels[4] = {0.1f, 0.2f, 0.3f, 0.4f};
    CcaRuntime_Init(0u, 1u);
    sendCommand(0u, CCA_MODE_BODY_VELOCITY, 4u, 5u, CCA_COMMAND_ARM,
                100, 0, 0);
    CcaRuntime_SetAppliedBody(0.08f, 0.0f, 0.0f, 9u);
    CcaTelemetry_EncodeStatus(frame);
    CHECK(frame[7] == CcaProtocol_Crc8(frame, 7u));
    CHECK(frame[2] == 9u);
    CcaTelemetry_EncodeApplied(frame);
    CHECK(frame[7] == CcaProtocol_Crc8(frame, 7u));
    CHECK(frame[6] == 9u);
    CcaTelemetry_EncodeWheelsAbc(wheels, 0.05f, frame);
    CHECK(frame[7] == CcaProtocol_Crc8(frame, 7u));
    CcaTelemetry_EncodeWheelD(wheels, 0.05f, 24000u, 0x0Fu, 0u, frame);
    CHECK(frame[7] == CcaProtocol_Crc8(frame, 7u));
}

int main(void)
{
    testCrcAndCodec();
    testRuntimeAcceptanceAndTimeout();
    testRejectionAndCommissioningLock();
    testIncompleteHeaderCannotExtendDeadline();
    testSaturationAndSequence();
    testKinematicsAndWheelController();
    testTelemetryCrc();
    if (failures == 0)
    {
        puts("CCA STM host tests: PASS");
    }
    return failures == 0 ? 0 : 1;
}
