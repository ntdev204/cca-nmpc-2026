#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace cca::ai {

struct Point2 {
    double x{};
    double y{};
};

struct ContextEvent {
    std::uint64_t track_id{};
    std::uint64_t timestamp_ns{};
    double phi{};
    double detector_confidence{};
    bool calibration_valid{};
    std::array<double, 5U> features{};
};

struct Snapshot {
    std::uint64_t timestamp_ns{};
    std::string frame_id;
    std::string detector_model;
    std::vector<ContextEvent> context;
};

}  // namespace cca::ai
