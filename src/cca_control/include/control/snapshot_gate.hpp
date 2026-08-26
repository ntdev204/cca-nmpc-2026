#pragma once

#include <cstdint>
#include <string>

#include "control/contracts.hpp"

namespace cca::ai {

enum class SnapshotStatus {
    accepted,
    invalid_contract,
    stale,
    future_timestamp,
    replayed,
    uncalibrated,
    detector_mismatch,
};

struct SnapshotGateConfig {
    std::uint64_t maximum_age_ns{250'000'000};
    std::string expected_detector{"yolo26s-pose.engine"};
};

SnapshotStatus EvaluateSnapshot(
    const Snapshot& snapshot,
    std::uint64_t now_ns,
    const SnapshotGateConfig& config = {}
);

const char* ToString(SnapshotStatus status);

class SnapshotGate {
public:
    explicit SnapshotGate(SnapshotGateConfig config = {});
    SnapshotStatus Evaluate(const Snapshot& snapshot, std::uint64_t now_ns);
    void Reset();

private:
    SnapshotGateConfig config_;
    std::uint64_t last_timestamp_ns_{};
    bool has_timestamp_{};
};

}  // namespace cca::ai
