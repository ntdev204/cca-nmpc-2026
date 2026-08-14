#pragma once

#include <array>
#include <cstddef>
#include <span>
#include <vector>

namespace cca::control {

enum class ControllerKind : int {
    mpc = 0,
    nmpc = 1,
    dwa = 2,
    mppi = 3,
    cca_nmpc = 4,
};

struct ControllerConfig {
    double dt_s{0.1};
    std::size_t horizon{6U};
    double deadline_ms{100.0};
    double robot_radius_m{0.1772541986};
    double human_radius_m{0.34};
    double max_speed_mps{0.85};
    double max_yaw_rate_radps{1.4};
    double human_clearance_m{0.5172541986};
};

struct ControllerInput {
    std::span<const double> state;
    std::span<const double> reference;
    std::span<const double> previous_command;
    std::span<const double> human_mean;
    std::span<const double> context;
    std::span<const double> covariance;
    std::span<const double> nominal_robot;
    std::span<const double> obstacles;
    bool context_aware{false};
};

struct ControllerOutput {
    std::array<double, 3U> first_command_mps{};
    std::vector<double> predicted_states;
    double solve_time_ms{0.0};
    double objective{0.0};
    double maximum_constraint_violation{0.0};
    int iterations{0};
    int status{0};
    bool deadline_missed{false};
    double risk_bound{0.0};
    double maximum_risk_slack_m{0.0};
};

class Controller {
public:
    Controller(ControllerKind kind, ControllerConfig config);

    void Reset() noexcept;
    ControllerOutput Command(const ControllerInput& input);

private:
    ControllerKind kind_;
    ControllerConfig config_;
    std::vector<double> rollout_;
};

}  // namespace cca::control
