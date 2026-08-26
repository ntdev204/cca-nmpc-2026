#include "control/snapshot_gate.hpp"

#include <algorithm>
#include <unordered_set>
#include <utility>

namespace cca::ai {
namespace {

bool IsAligned(const Snapshot& snapshot) {
    std::unordered_set<std::uint64_t> identifiers;
    for (const auto& context : snapshot.context) {
        if (context.timestamp_ns != snapshot.timestamp_ns ||
            !identifiers.insert(context.track_id).second ||
            !(context.phi >= 0.0 && context.phi <= 1.0) ||
            !(context.detector_confidence >= 0.0 &&
              context.detector_confidence <= 1.0)) {
            return false;
        }
    }
    return !snapshot.frame_id.empty() && !snapshot.context.empty();
}

}  // namespace

SnapshotStatus EvaluateSnapshot(
    const Snapshot& snapshot,
    const std::uint64_t now_ns,
    const SnapshotGateConfig& config
) {
    if (!IsAligned(snapshot) || config.maximum_age_ns == 0U) {
        return SnapshotStatus::invalid_contract;
    }
    if (snapshot.detector_model != config.expected_detector) {
        return SnapshotStatus::detector_mismatch;
    }
    if (snapshot.timestamp_ns > now_ns) {
        return SnapshotStatus::future_timestamp;
    }
    if (now_ns - snapshot.timestamp_ns > config.maximum_age_ns) {
        return SnapshotStatus::stale;
    }
    const bool calibrated = std::ranges::all_of(
        snapshot.context,
        [](const ContextEvent& item) { return item.calibration_valid; }
    );
    return calibrated ? SnapshotStatus::accepted : SnapshotStatus::uncalibrated;
}

const char* ToString(const SnapshotStatus status) {
    switch (status) {
        case SnapshotStatus::accepted: return "accepted";
        case SnapshotStatus::invalid_contract: return "invalid_contract";
        case SnapshotStatus::stale: return "stale";
        case SnapshotStatus::future_timestamp: return "future_timestamp";
        case SnapshotStatus::replayed: return "replayed";
        case SnapshotStatus::uncalibrated: return "uncalibrated";
        case SnapshotStatus::detector_mismatch: return "detector_mismatch";
    }
    return "invalid_contract";
}

SnapshotGate::SnapshotGate(SnapshotGateConfig config)
    : config_(std::move(config)) {}

SnapshotStatus SnapshotGate::Evaluate(
    const Snapshot& snapshot, const std::uint64_t now_ns
) {
    const auto status = EvaluateSnapshot(snapshot, now_ns, config_);
    if ((status == SnapshotStatus::accepted ||
         status == SnapshotStatus::uncalibrated) &&
        has_timestamp_ && snapshot.timestamp_ns <= last_timestamp_ns_) {
        return SnapshotStatus::replayed;
    }
    if (status == SnapshotStatus::accepted ||
        status == SnapshotStatus::uncalibrated) {
        last_timestamp_ns_ = snapshot.timestamp_ns;
        has_timestamp_ = true;
    }
    return status;
}

void SnapshotGate::Reset() {
    last_timestamp_ns_ = 0U;
    has_timestamp_ = false;
}

}  // namespace cca::ai
