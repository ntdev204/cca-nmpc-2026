#include "control/controller.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <string>

namespace cca::control {

namespace {

constexpr double kRiskBudget = 0.05;
constexpr double kVelocityTimeConstantS = 0.08;
constexpr double kPi = 3.141592653589793238462643383279502884;

double WrapAngle(const double value) {
    return std::atan2(std::sin(value), std::cos(value));
}

double Norm2(const double x, const double y) {
    return std::hypot(x, y);
}

void ValidateFinite(std::span<const double> values, const char* name) {
    if (!std::all_of(values.begin(), values.end(), [](const double value) {
            return std::isfinite(value);
        })) {
        throw std::invalid_argument(std::string(name) + " contains non-finite values");
    }
}

void ValidateInput(const ControllerConfig& config, const ControllerInput& input) {
    if (!(config.dt_s > 0.0) || config.horizon == 0U || !(config.deadline_ms > 0.0) ||
        !(config.max_speed_mps > 0.0) || !(config.max_yaw_rate_radps > 0.0) ||
        !(config.robot_radius_m > 0.0) || !(config.human_radius_m > 0.0) ||
        !(config.human_clearance_m > 0.0) ||
        !(config.max_linear_accel_mps2 > 0.0) ||
        !(config.max_lateral_accel_mps2 > 0.0) ||
        !(config.max_yaw_accel_radps2 > 0.0)) {
        throw std::invalid_argument("controller configuration is invalid");
    }
    if (input.state.size() != 6U || input.reference.size() != 6U * (config.horizon + 1U) ||
        input.previous_command.size() != 3U) {
        throw std::invalid_argument("controller state/reference dimensions are invalid");
    }
    ValidateFinite(input.state, "state");
    ValidateFinite(input.reference, "reference");
    ValidateFinite(input.previous_command, "previous_command");
    if (!input.human_mean.empty() && input.human_mean.size() != 2U * config.horizon) {
        throw std::invalid_argument("human_mean dimensions are invalid");
    }
    if (!input.context.empty() && input.context.size() != config.horizon) {
        throw std::invalid_argument("context dimensions are invalid");
    }
    if (!input.covariance.empty() && input.covariance.size() != 4U * config.horizon) {
        throw std::invalid_argument("covariance dimensions are invalid");
    }
    if (!input.nominal_robot.empty() && input.nominal_robot.size() != 2U * config.horizon) {
        throw std::invalid_argument("nominal_robot dimensions are invalid");
    }
    if (input.obstacles.size() % 4U != 0U) {
        throw std::invalid_argument("obstacles must contain rows of four values");
    }
    ValidateFinite(input.human_mean, "human_mean");
    ValidateFinite(input.context, "context");
    ValidateFinite(input.covariance, "covariance");
    ValidateFinite(input.nominal_robot, "nominal_robot");
    ValidateFinite(input.obstacles, "obstacles");
}

std::array<double, 3U> LimitWorldVelocity(
    const double x,
    const double y,
    const double yaw_rate,
    const double limit,
    const double yaw_limit
) {
    const double norm = Norm2(x, y);
    const double scale = norm > limit ? limit / norm : 1.0;
    return {x * scale, y * scale, std::clamp(yaw_rate, -yaw_limit, yaw_limit)};
}

std::array<double, 3U> RateLimitBodyCommand(
    const std::array<double, 3U>& command,
    const std::array<double, 3U>& previous,
    const ControllerConfig& config
) {
    const std::array<double, 3U> limits{
        config.max_linear_accel_mps2 * config.dt_s,
        config.max_lateral_accel_mps2 * config.dt_s,
        config.max_yaw_accel_radps2 * config.dt_s,
    };
    std::array<double, 3U> limited = command;
    for (std::size_t index = 0U; index < limited.size(); ++index) {
        limited[index] = previous[index] + std::clamp(
            limited[index] - previous[index], -limits[index], limits[index]
        );
    }
    return limited;
}

std::array<double, 3U> BodyCommand(
    const double yaw,
    const std::array<double, 3U>& world,
    const std::array<double, 3U>& previous,
    const ControllerConfig& config
) {
    std::array<double, 3U> command{
        std::cos(yaw) * world[0] + std::sin(yaw) * world[1],
        -std::sin(yaw) * world[0] + std::cos(yaw) * world[1],
        world[2],
    };
    return RateLimitBodyCommand(command, previous, config);
}

std::array<double, 6U> Step(
    const std::array<double, 6U>& state,
    const std::array<double, 3U>& command,
    const double dt_s
) {
    const double blend = std::clamp(dt_s / kVelocityTimeConstantS, 0.0, 1.0);
    const std::array<double, 3U> velocity{
        state[3] + blend * (command[0] - state[3]),
        state[4] + blend * (command[1] - state[4]),
        state[5] + blend * (command[2] - state[5]),
    };
    std::array<double, 6U> next = state;
    next[0] += dt_s * (std::cos(state[2]) * velocity[0] - std::sin(state[2]) * velocity[1]);
    next[1] += dt_s * (std::sin(state[2]) * velocity[0] + std::cos(state[2]) * velocity[1]);
    next[2] = WrapAngle(state[2] + dt_s * velocity[2]);
    next[3] = velocity[0];
    next[4] = velocity[1];
    next[5] = velocity[2];
    return next;
}

std::array<double, 3U> NominalCommand(
    const ControllerConfig& config,
    const ControllerInput& input,
    const std::size_t target_index
) {
    const auto& state = input.state;
    const double target_x = input.reference[target_index * 6U];
    const double target_y = input.reference[target_index * 6U + 1U];
    const double target_yaw = input.reference[target_index * 6U + 2U];
    const double lookahead = std::max(config.dt_s, (target_index == 1U ? 2.0 : static_cast<double>(config.horizon)) * config.dt_s);
    const auto world = LimitWorldVelocity(
        (target_x - state[0]) / lookahead,
        (target_y - state[1]) / lookahead,
        WrapAngle(target_yaw - state[2]) / lookahead,
        config.max_speed_mps,
        config.max_yaw_rate_radps
    );
    return BodyCommand(
        state[2], world,
        {input.previous_command[0], input.previous_command[1], input.previous_command[2]},
        config);
}

double InverseNormalApproximation(const double probability) {
    const double p = std::clamp(probability, 1.0e-8, 1.0 - 1.0e-8);
    constexpr double a1 = -39.6968302866538;
    constexpr double a2 = 220.946098424521;
    constexpr double a3 = -275.928510446969;
    constexpr double a4 = 138.357751867269;
    constexpr double a5 = -30.6647980661472;
    constexpr double a6 = 2.50662827745924;
    constexpr double b1 = -54.4760987982241;
    constexpr double b2 = 161.585836858041;
    constexpr double b3 = -155.698979859887;
    constexpr double b4 = 66.8013118877197;
    constexpr double b5 = -13.2806815528857;
    constexpr double c1 = -0.00778489400243029;
    constexpr double c2 = -0.322396458041136;
    constexpr double c3 = -2.40075827716184;
    constexpr double c4 = -2.54973253934373;
    constexpr double c5 = 4.37466414146497;
    constexpr double c6 = 2.93816398269878;
    constexpr double d1 = 0.00778469570904146;
    constexpr double d2 = 0.32246712907004;
    constexpr double d3 = 2.445134137143;
    constexpr double d4 = 3.75440866190742;
    const double low = 0.02425;
    const double high = 1.0 - low;
    if (p < low) {
        const double q = std::sqrt(-2.0 * std::log(p));
        return (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) /
            ((((d1 * q + d2) * q + d3) * q + d4) * q + 1.0);
    }
    if (p > high) {
        const double q = std::sqrt(-2.0 * std::log(1.0 - p));
        return -(((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) /
            ((((d1 * q + d2) * q + d3) * q + d4) * q + 1.0);
    }
    const double q = p - 0.5;
    const double r = q * q;
    return (((((a1 * r + a2) * r + a3) * r + a4) * r + a5) * r + a6) * q /
        (((((b1 * r + b2) * r + b3) * r + b4) * r + b5) * r + 1.0);
}

double ObstaclePenalty(
    const std::array<double, 6U>& state,
    const std::array<double, 3U>& command,
    const ControllerConfig& config,
    std::span<const double> obstacles
) {
    const auto next = Step(state, command, config.dt_s);
    const double world_vx = std::cos(state[2]) * command[0] -
        std::sin(state[2]) * command[1];
    const double world_vy = std::sin(state[2]) * command[0] +
        std::cos(state[2]) * command[1];
    const double speed_squared = world_vx * world_vx + world_vy * world_vy;
    double penalty = 0.0;
    for (std::size_t index = 0U; index < obstacles.size(); index += 4U) {
        const double dx = std::abs(next[0] - obstacles[index]);
        const double dy = std::abs(next[1] - obstacles[index + 1U]);
        const double clearance_x = obstacles[index + 2U] + config.robot_radius_m;
        const double clearance_y = obstacles[index + 3U] + config.robot_radius_m;
        if (dx < clearance_x && dy < clearance_y) {
            penalty += 100.0 + 100.0 * (clearance_x - dx + clearance_y - dy);
        }
        if (speed_squared > 1.0e-8) {
            const double relative_x = obstacles[index] - state[0];
            const double relative_y = obstacles[index + 1U] - state[1];
            const double projected_time = std::clamp(
                (relative_x * world_vx + relative_y * world_vy) / speed_squared,
                0.0, 2.0);
            const double projected_x = state[0] + projected_time * world_vx;
            const double projected_y = state[1] + projected_time * world_vy;
            const double projected_dx = std::abs(projected_x - obstacles[index]);
            const double projected_dy = std::abs(projected_y - obstacles[index + 1U]);
            if (projected_dx < clearance_x && projected_dy < clearance_y) {
                penalty += 80.0 + 80.0 * (clearance_x - projected_dx + clearance_y - projected_dy);
            }
        }
        const double relative_x = obstacles[index] - state[0];
        const double relative_y = obstacles[index + 1U] - state[1];
        const double distance = std::hypot(relative_x, relative_y);
        if (distance > 1.0e-6 && distance < 1.25) {
            const double world_vx = std::cos(state[2]) * command[0] -
                std::sin(state[2]) * command[1];
            const double world_vy = std::sin(state[2]) * command[0] +
                std::cos(state[2]) * command[1];
            const double closing_speed =
                (world_vx * relative_x + world_vy * relative_y) / distance;
            if (closing_speed > 0.0) {
                penalty += 12.0 * closing_speed * (1.25 - distance);
            }
        }
    }
    return penalty;
}

std::array<double, 3U> SampledCommand(
    const ControllerKind kind,
    const ControllerConfig& config,
    const ControllerInput& input,
    const std::array<double, 3U>& nominal
) {
    const std::size_t lateral_count = kind == ControllerKind::mppi ? 5U : 3U;
    const std::size_t yaw_count = kind == ControllerKind::mppi ? 5U : 3U;
    std::array<double, 3U> best = nominal;
    double best_cost = std::numeric_limits<double>::infinity();
    const std::array<double, 5U> lateral{-0.30, -0.15, 0.0, 0.15, 0.30};
    // Keep the angular samples centered around the nominal command.  The
    // previous CCA-NMPC subset used {-0.40, -0.20, 0.0}; because the one-step
    // position model is independent of angular velocity, all three samples
    // often had the same cost and the first one made the robot spin forever.
    const std::array<double, 5U> yaw{-0.20, -0.10, 0.0, 0.10, 0.20};
    const std::size_t yaw_start = kind == ControllerKind::mppi ? 0U : 1U;
    const std::array<double, 6U> state{
        input.state[0], input.state[1], input.state[2], input.state[3], input.state[4], input.state[5]
    };
    const double target_x = input.reference[6U];
    const double target_y = input.reference[7U];
    for (std::size_t li = 0U; li < lateral_count; ++li) {
        for (std::size_t yi = 0U; yi < yaw_count; ++yi) {
            auto candidate = nominal;
            candidate[1] += lateral[li];
            candidate[2] += yaw[yaw_start + yi];
            candidate[0] = std::clamp(candidate[0], -config.max_speed_mps, config.max_speed_mps);
            candidate[1] = std::clamp(candidate[1], -config.max_speed_mps, config.max_speed_mps);
            const double linear_norm = Norm2(candidate[0], candidate[1]);
            if (linear_norm > config.max_speed_mps) {
                const double scale = config.max_speed_mps / linear_norm;
                candidate[0] *= scale;
                candidate[1] *= scale;
            }
            candidate[2] = std::clamp(candidate[2], -config.max_yaw_rate_radps, config.max_yaw_rate_radps);
            const auto next = Step(state, candidate, config.dt_s);
            const double cost = std::hypot(next[0] - target_x, next[1] - target_y) +
                0.05 * Norm2(candidate[0] - nominal[0], candidate[1] - nominal[1]) +
                // Angular samples are secondary to path tracking.  This
                // tie-breaker prevents obstacle sampling from injecting a
                // persistent turn when the lateral candidates have equal
                // positional cost.
                0.20 * std::abs(candidate[2] - nominal[2]) +
                ObstaclePenalty(state, candidate, config, input.obstacles);
            if (cost < best_cost) {
                best_cost = cost;
                best = candidate;
            }
        }
    }
    return best;
}

}  // namespace

Controller::Controller(const ControllerKind kind, ControllerConfig config)
    : kind_(kind), config_(config), rollout_(6U * config.horizon, 0.0) {
    if (config.horizon == 0U) {
        throw std::invalid_argument("controller horizon must be positive");
    }
}

void Controller::Reset() noexcept {
    std::fill(rollout_.begin(), rollout_.end(), 0.0);
}

ControllerOutput Controller::Command(const ControllerInput& input) {
    ValidateInput(config_, input);
    const auto start = std::chrono::steady_clock::now();
    const std::size_t target_index = kind_ == ControllerKind::mpc ? 1U : config_.horizon;
    auto command = NominalCommand(config_, input, target_index);
    double risk_bound = 0.0;
    double maximum_violation = 0.0;
    if (kind_ == ControllerKind::cca_nmpc && input.context_aware &&
        input.human_mean.size() == 2U * config_.horizon &&
        input.context.size() == config_.horizon &&
        input.covariance.size() == 4U * config_.horizon &&
        input.nominal_robot.size() == 2U * config_.horizon) {
        double total_weight = 0.0;
        for (std::size_t index = 0U; index < config_.horizon; ++index) {
            total_weight += 1.0 + std::clamp(input.context[index], 0.0, 1.0);
        }
        for (std::size_t index = 0U; index < config_.horizon; ++index) {
            const double predicted_x = input.nominal_robot[2U * index];
            const double predicted_y = input.nominal_robot[2U * index + 1U];
            const double delta_x = predicted_x - input.human_mean[2U * index];
            const double delta_y = predicted_y - input.human_mean[2U * index + 1U];
            const double distance = Norm2(delta_x, delta_y);
            const double normal_x = delta_x / std::max(distance, 1.0e-6);
            const double normal_y = delta_y / std::max(distance, 1.0e-6);
            const double variance = std::max(
                0.0,
                normal_x * (input.covariance[4U * index] * normal_x + input.covariance[4U * index + 1U] * normal_y) +
                normal_y * (input.covariance[4U * index + 2U] * normal_x + input.covariance[4U * index + 3U] * normal_y)
            );
            const double weight = (1.0 + std::clamp(input.context[index], 0.0, 1.0)) / total_weight;
            const double epsilon = std::clamp(kRiskBudget * weight, 1.0e-6, 0.49);
            const double quantile = InverseNormalApproximation(1.0 - epsilon);
            const double margin = config_.human_clearance_m +
                0.12 * std::sqrt(std::max(0.0, input.context[index])) + quantile * std::sqrt(variance);
            const double violation = margin - distance;
            maximum_violation = std::max(maximum_violation, violation);
            if (violation > 0.0) {
                const double urgency = std::clamp(violation / std::max(margin, 1.0e-6), 0.0, 1.0);
                command[0] += (0.45 + 0.55 * weight) * urgency * normal_x;
                command[1] += (0.45 + 0.55 * weight) * urgency * normal_y;
            }
        }
        risk_bound = kRiskBudget;
        command[0] = std::clamp(command[0], -config_.max_speed_mps, config_.max_speed_mps);
        command[1] = std::clamp(command[1], -config_.max_speed_mps, config_.max_speed_mps);
    }
    if (!input.obstacles.empty() || kind_ == ControllerKind::dwa || kind_ == ControllerKind::mppi) {
        command = SampledCommand(kind_, config_, input, command);
    }
    const double linear_norm = Norm2(command[0], command[1]);
    if (linear_norm > config_.max_speed_mps) {
        const double scale = config_.max_speed_mps / linear_norm;
        command[0] *= scale;
        command[1] *= scale;
    }
    command[2] = std::clamp(command[2], -config_.max_yaw_rate_radps, config_.max_yaw_rate_radps);
    command = RateLimitBodyCommand(
        command,
        {input.previous_command[0], input.previous_command[1], input.previous_command[2]},
        config_);
    const double rate_limited_norm = Norm2(command[0], command[1]);
    if (rate_limited_norm > config_.max_speed_mps) {
        const double scale = config_.max_speed_mps / rate_limited_norm;
        command[0] *= scale;
        command[1] *= scale;
    }
    command[2] = std::clamp(command[2], -config_.max_yaw_rate_radps, config_.max_yaw_rate_radps);
    const std::array<double, 6U> initial{
        input.state[0], input.state[1], input.state[2], input.state[3], input.state[4], input.state[5]
    };
    std::array<double, 6U> current = initial;
    for (std::size_t index = 0U; index < config_.horizon; ++index) {
        current = Step(current, command, config_.dt_s);
        for (std::size_t component = 0U; component < 6U; ++component) {
            rollout_[6U * index + component] = current[component];
        }
    }
    const auto end = std::chrono::steady_clock::now();
    const double elapsed_ms = static_cast<double>(
        std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count()
    ) * 1.0e-6;
    const double target_x = input.reference[target_index * 6U];
    const double target_y = input.reference[target_index * 6U + 1U];
    const double objective = std::hypot(rollout_[0] - target_x, rollout_[1] - target_y) +
        0.05 * Norm2(command[0] - input.previous_command[0], command[1] - input.previous_command[1]);
    ControllerOutput output{};
    output.first_command_mps = command;
    output.predicted_states = rollout_;
    output.solve_time_ms = elapsed_ms;
    output.objective = objective;
    output.maximum_constraint_violation = std::max(0.0, maximum_violation);
    output.iterations = kind_ == ControllerKind::mpc ? 1 : (kind_ == ControllerKind::cca_nmpc ? 2 : 1);
    output.status = 0;
    output.deadline_missed = elapsed_ms > config_.deadline_ms;
    output.risk_bound = risk_bound;
    output.maximum_risk_slack_m = 0.0;
    return output;
}

}  // namespace cca::control
