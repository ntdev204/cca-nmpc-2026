#pragma once

#include <array>
#include <cstdint>

#include "control/contracts.hpp"

namespace cca::ai {

struct ContextConfig {
    double distance_scale_m{2.0};
    double closing_scale_mps{1.0};
    double cpa_time_scale_s{3.0};
    double bias{-2.0};
    std::array<double, 5> weights{2.0, 1.5, 1.0, 0.8, 0.6};
};

ContextEvent ScoreContext(
    std::uint64_t track_id,
    std::uint64_t timestamp_ns,
    Point2 relative_position,
    Point2 relative_velocity,
    double local_density,
    double detector_confidence,
    Point2 robot_velocity = {},
    Point2 human_velocity = {},
    const ContextConfig& config = {}
);

}  // namespace cca::ai
