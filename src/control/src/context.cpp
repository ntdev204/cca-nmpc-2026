#include "control/context.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace cca::ai {

ContextEvent ScoreContext(
    const std::uint64_t track_id,
    const std::uint64_t timestamp_ns,
    const Point2 position,
    const Point2 velocity,
    const double density,
    const double confidence,
    const Point2 robot_velocity,
    const Point2 human_velocity,
    const ContextConfig& config
) {
    if (!(confidence >= 0.0 && confidence <= 1.0) ||
        config.distance_scale_m <= 0.0 ||
        config.closing_scale_mps <= 0.0 ||
        config.cpa_time_scale_s <= 0.0 ||
        !std::isfinite(confidence) || !std::isfinite(density)) {
        throw std::invalid_argument("invalid context input or configuration");
    }
    const double distance = std::hypot(position.x, position.y);
    const double radial =
        (position.x * velocity.x + position.y * velocity.y) /
        std::max(distance, 1e-9);
    const double closing = std::max(0.0, -radial);
    const double proximity = std::clamp(
        1.0 - distance / config.distance_scale_m, 0.0, 1.0
    );
    const double closing_feature = std::clamp(
        closing / config.closing_scale_mps, 0.0, 1.0
    );
    const double velocity_squared =
        velocity.x * velocity.x + velocity.y * velocity.y;
    const double cpa_time = velocity_squared > 1e-9
        ? std::max(
              0.0,
              -(position.x * velocity.x + position.y * velocity.y) /
                  velocity_squared
          )
        : 0.0;
    const double cpa_feature =
        std::exp(-cpa_time / config.cpa_time_scale_s);
    const double robot_speed = std::hypot(robot_velocity.x, robot_velocity.y);
    const double human_speed = std::hypot(human_velocity.x, human_velocity.y);
    const double crossing_denominator = robot_speed * human_speed;
    const double crossing_feature = crossing_denominator > 1e-18
        ? std::clamp(
              std::abs(
                  robot_velocity.x * human_velocity.y -
                  robot_velocity.y * human_velocity.x
              ) /
                  crossing_denominator,
              0.0,
              1.0
          )
        : 0.0;
    const double density_feature =
        std::clamp(std::max(0.0, density) / 3.0, 0.0, 1.0);
    const std::array features{
        proximity,
        closing_feature,
        cpa_feature,
        crossing_feature,
        density_feature,
    };
    double logit = config.bias;
    for (std::size_t index = 0; index < features.size(); ++index) {
        logit += config.weights[index] * features[index];
    }
    return ContextEvent{
        track_id,
        timestamp_ns,
        1.0 / (1.0 + std::exp(-logit)),
        confidence,
        false,
        features,
    };
}

}  // namespace cca::ai
