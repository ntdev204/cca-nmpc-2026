#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <span>

#include "control/context.hpp"
#include "control/can.hpp"
#include "control/snapshot_gate.hpp"
#include "control/stm_c_api.h"
#include "control/stm_serial.hpp"

namespace {

void Check(const bool condition, const char* expression) {
    if (!condition) {
        std::cerr << "FAIL: " << expression << '\n';
        std::exit(EXIT_FAILURE);
    }
}

cca::ai::Snapshot MakeSnapshot(const bool calibrated) {
    using namespace cca::ai;
    ContextEvent context{7U, 1'000U, 0.5, 0.9, calibrated};
    return Snapshot{1'000U, "robot_base", "yolo26s-pose.engine", {context}};
}

}  // namespace

int main() {
    using namespace cca::ai;
    const auto approaching = ScoreContext(
        1U, 10U, {1.0, 0.0}, {-1.0, 0.0}, 0.0, 0.8
    );
    const auto receding = ScoreContext(
        1U, 10U, {1.0, 0.0}, {1.0, 0.0}, 0.0, 0.8
    );
    Check(approaching.phi > receding.phi, "approaching context must rank higher");
    Check(
        std::abs(approaching.phi - 0.7714525485270759) < 1e-14,
        "C++ context must match the Python reference"
    );
    Check(!approaching.calibration_valid, "default context is uncalibrated");

    Check(
        EvaluateSnapshot(MakeSnapshot(false), 1'100U) ==
            SnapshotStatus::uncalibrated,
        "uncalibrated snapshot must be rejected"
    );
    Check(
        EvaluateSnapshot(MakeSnapshot(true), 1'100U) == SnapshotStatus::accepted,
        "fresh calibrated snapshot must pass"
    );
    Check(
        EvaluateSnapshot(MakeSnapshot(true), 300'001'001U) ==
            SnapshotStatus::stale,
        "stale snapshot must be rejected"
    );
    auto wrong_detector = MakeSnapshot(true);
    wrong_detector.detector_model = "other.engine";
    Check(
        EvaluateSnapshot(wrong_detector, 1'100U) ==
            SnapshotStatus::detector_mismatch,
        "wrong detector must be rejected"
    );
    Check(
        EvaluateSnapshot(MakeSnapshot(true), 999U) ==
            SnapshotStatus::future_timestamp,
        "future-timestamp snapshot must be rejected"
    );
    auto malformed_frame = MakeSnapshot(true);
    malformed_frame.frame_id.clear();
    Check(
        EvaluateSnapshot(malformed_frame, 1'100U) ==
            SnapshotStatus::invalid_contract,
        "malformed snapshot with empty frame must be rejected"
    );
    auto misaligned = MakeSnapshot(true);
    misaligned.context.clear();
    Check(
        EvaluateSnapshot(misaligned, 1'100U) ==
            SnapshotStatus::invalid_contract,
        "empty context must be rejected"
    );
    SnapshotGate stateful_gate;
    Check(
        stateful_gate.Evaluate(MakeSnapshot(true), 1'100U) ==
            SnapshotStatus::accepted,
        "first snapshot must pass"
    );
    Check(
        stateful_gate.Evaluate(MakeSnapshot(true), 1'100U) ==
            SnapshotStatus::replayed,
        "replayed snapshot must be rejected"
    );
    const auto command = cca::hardware::EncodeVelocityCommand({1.234, -0.5, 2.0, 0U, 0U});
    Check(command[0] == 0x7BU && command[10] == 0x7DU, "STM32 command boundary must match bridge");
    Check(command[3] == 0x04U && command[4] == 0xD2U, "STM32 vx quantization must match bridge");
    Check(command[5] == 0xFEU && command[6] == 0x0CU, "STM32 vy quantization must match bridge");
    Check(command[7] == 0x07U && command[8] == 0xD0U, "STM32 wz quantization must match bridge");
    std::array<std::uint8_t, cca::hardware::kTelemetrySize> packet{};
    packet[0] = 0x7BU;
    packet[1] = 1U;
    packet[2] = 0xFFU;
    packet[3] = 0x9CU;
    packet[4] = 0x00U;
    packet[5] = 0x64U;
    packet[6] = 0x00U;
    packet[7] = 0x32U;
    packet[20] = 0x5DU;
    packet[21] = 0xC0U;
    std::uint8_t checksum = 0U;
    for (std::size_t index = 0U; index < 22U; ++index) {
        checksum = static_cast<std::uint8_t>(checksum ^ packet[index]);
    }
    packet[22] = checksum;
    packet[23] = 0x7DU;
    cca::hardware::TelemetryDecoder decoder;
    Check(
        decoder.Feed(std::span<const std::uint8_t>(packet.data(), 10U), 5'000U).empty(),
        "fragmented STM32 telemetry must wait for the tail"
    );
    const auto samples = decoder.Feed(
        std::span<const std::uint8_t>(packet.data() + 10U, packet.size() - 10U),
        5'000U
    );
    Check(samples.size() == 1U, "STM32 telemetry frame must decode once");
    Check(samples.front().flag_stop == 1U, "STM32 stop flag must be preserved");
    Check(std::abs(samples.front().vx_mps + 0.1) < 1e-12, "STM32 signed vx must decode");
    Check(std::abs(samples.front().voltage_v - 24.0) < 1e-12, "STM32 voltage must decode");
    const auto can_header = cca::hardware::EncodeCcaCommandHeader(2U, 7U, 10U, 1U, 3U);
    const auto decoded_header = cca::hardware::DecodeCcaCanFrame(
        can_header.arbitration_id,
        std::span<const std::uint8_t>(can_header.data.data(), can_header.data.size())
    );
    Check(decoded_header.kind == cca::hardware::CanKind::command_header, "CCA CAN header kind must decode");
    Check(decoded_header.sequence == 7U && decoded_header.deadline_ticks == 10U, "CCA CAN header fields must decode");
    const auto can_body = cca::hardware::EncodeCcaBodyVelocityPayload(0.12, -0.04, 0.5, 9U);
    const auto decoded_body = cca::hardware::DecodeCcaCanFrame(
        can_body.arbitration_id,
        std::span<const std::uint8_t>(can_body.data.data(), can_body.data.size())
    );
    Check(decoded_body.kind == cca::hardware::CanKind::command_payload, "CCA CAN body kind must decode");
    Check(std::abs(decoded_body.vx_mps - 0.12) < 1e-12, "CCA CAN vx must round-trip");
    Check(std::abs(decoded_body.wz_radps - 0.5) < 1e-12, "CCA CAN wz must round-trip");
    cca_can_frame c_header{};
    char error_text[256]{};
    Check(
        cca_can_encode_header(2U, 7U, 10U, 1U, 3U, &c_header, error_text, sizeof(error_text)) == 0,
        "CCA CAN C ABI header must encode"
    );
    cca_can_decoded c_decoded{};
    Check(
        cca_can_decode(
            c_header.arbitration_id,
            c_header.data,
            sizeof(c_header.data),
            &c_decoded,
            error_text,
            sizeof(error_text)
        ) == 0,
        "CCA CAN C ABI header must decode"
    );
    Check(c_decoded.kind == 0 && c_decoded.sequence == 7U, "CCA CAN C ABI fields must round-trip");
    cca_context_score_input context_input{};
    context_input.track_id = 7U;
    context_input.timestamp_ns = 1'000U;
    context_input.relative_position_x_m = 1.0;
    context_input.relative_velocity_x_mps = -1.0;
    context_input.detector_confidence = 0.8;
    context_input.distance_scale_m = 2.0;
    context_input.closing_scale_mps = 1.0;
    context_input.cpa_time_scale_s = 3.0;
    context_input.bias = -2.0;
    context_input.weights[0] = 2.0;
    context_input.weights[1] = 1.5;
    context_input.weights[2] = 1.0;
    context_input.weights[3] = 0.8;
    context_input.weights[4] = 0.6;
    cca_context_score_output context_output{};
    Check(
        cca_context_score(&context_input, &context_output, error_text, sizeof(error_text)) == 0,
        "CCA context C ABI must score"
    );
    Check(
        std::abs(context_output.phi - approaching.phi) < 1e-14 &&
            std::abs(context_output.features[0] - 0.5) < 1e-14,
        "CCA context C ABI must match the C++ core"
    );
    std::cout << "CCA C++ AI core tests: PASS\n";
    return EXIT_SUCCESS;
}
