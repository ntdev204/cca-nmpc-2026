#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <limits>
#include <memory>
#include <span>
#include <stdexcept>
#include <string>
#include <vector>

#include "control/controller.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "nav_msgs/msg/path.hpp"
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float64_multi_array.hpp"
#include "tf2/utils.h"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"

class CcaNmpcNode final : public rclcpp::Node {
public:
  CcaNmpcNode() : Node("cca_nmpc_node") {
    const std::string kind = declare_parameter<std::string>("controller_kind", "cca_nmpc");
    period_s_ = declare_parameter<double>("period_s", 0.05);
    horizon_ = static_cast<std::size_t>(declare_parameter<int64_t>("horizon", 6));
    const double deadline_ms = declare_parameter<double>("deadline_ms", 40.0);
    const double robot_radius = declare_parameter<double>("robot_radius_m", 0.283);
    const double human_radius = declare_parameter<double>("human_radius_m", 0.34);
    const double human_clearance = declare_parameter<double>("human_clearance_m", 0.623);
    state_timeout_s_ = declare_parameter<double>("state_timeout_s", 0.25);
    state_topic_ = declare_parameter<std::string>("state_topic", "/odometry/raw");
    reference_topic_ = declare_parameter<std::string>("reference_topic", "/cca/local_reference");
    context_topic_ = declare_parameter<std::string>("context_topic", "/cca/context_prediction");
    command_topic_ = declare_parameter<std::string>("command_topic", "/cmd_vel");
    predicted_topic_ = declare_parameter<std::string>("predicted_topic", "/cca/predicted_path");
    diagnostics_topic_ = declare_parameter<std::string>("diagnostics_topic", "/cca/controller_diagnostics");
    if (kind != "cca_nmpc" || !(period_s_ > 0.0) || horizon_ == 0U ||
        !(deadline_ms > 0.0) || !(state_timeout_s_ > 0.0)) {
      throw std::invalid_argument("CA-NMPC parameters are invalid");
    }

    cca::control::ControllerConfig config{};
    config.dt_s = period_s_;
    config.horizon = horizon_;
    config.deadline_ms = deadline_ms;
    config.robot_radius_m = robot_radius;
    config.human_radius_m = human_radius;
    config.human_clearance_m = human_clearance;
    controller_ = std::make_unique<cca::control::Controller>(
        cca::control::ControllerKind::cca_nmpc, config);
    reference_.assign((horizon_ + 1U) * 6U, 0.0);

    state_sub_ = create_subscription<nav_msgs::msg::Odometry>(
        state_topic_, rclcpp::SensorDataQoS(),
        [this](const nav_msgs::msg::Odometry::SharedPtr message) { onState(*message); });
    reference_sub_ = create_subscription<nav_msgs::msg::Path>(
        reference_topic_, rclcpp::QoS(1).reliable(),
        [this](const nav_msgs::msg::Path::SharedPtr message) { onReference(*message); });
    context_sub_ = create_subscription<std_msgs::msg::Float64MultiArray>(
        context_topic_, rclcpp::QoS(1).best_effort(),
        [this](const std_msgs::msg::Float64MultiArray::SharedPtr message) { onContext(*message); });
    command_pub_ = create_publisher<geometry_msgs::msg::Twist>(
        command_topic_, rclcpp::QoS(1).reliable().durability_volatile());
    predicted_pub_ = create_publisher<nav_msgs::msg::Path>(predicted_topic_, rclcpp::QoS(1).best_effort());
    diagnostics_pub_ = create_publisher<std_msgs::msg::Float64MultiArray>(
        diagnostics_topic_, rclcpp::QoS(1).best_effort());
    timer_ = create_wall_timer(
        std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::duration<double>(period_s_)),
        [this]() { controlStep(); });
  }

private:
  void onState(const nav_msgs::msg::Odometry& message) {
    state_[0] = message.pose.pose.position.x;
    state_[1] = message.pose.pose.position.y;
    state_[2] = tf2::getYaw(message.pose.pose.orientation);
    state_[3] = message.twist.twist.linear.x;
    state_[4] = message.twist.twist.linear.y;
    state_[5] = message.twist.twist.angular.z;
    have_state_ = std::all_of(state_.begin(), state_.end(), [](double value) {
      return std::isfinite(value);
    });
    last_state_time_ = now();
  }

  void onReference(const nav_msgs::msg::Path& message) {
    if (message.poses.empty()) {
      have_reference_ = false;
      return;
    }
    reference_.assign((horizon_ + 1U) * 6U, 0.0);
    for (std::size_t step = 0U; step <= horizon_; ++step) {
      const std::size_t index = std::min(step, message.poses.size() - 1U);
      const auto& pose = message.poses[index].pose;
      const double yaw = tf2::getYaw(pose.orientation);
      reference_[6U * step] = pose.position.x;
      reference_[6U * step + 1U] = pose.position.y;
      reference_[6U * step + 2U] = yaw;
      if (step > 0U) {
        const auto& previous = message.poses[std::min(step - 1U, message.poses.size() - 1U)].pose;
        const double dt = std::max(period_s_, 1.0e-3);
        reference_[6U * step + 3U] = (pose.position.x - previous.position.x) / dt;
        reference_[6U * step + 4U] = (pose.position.y - previous.position.y) / dt;
        reference_[6U * step + 5U] = (yaw - tf2::getYaw(previous.orientation)) / dt;
      }
    }
    have_reference_ = true;
  }

  void onContext(const std_msgs::msg::Float64MultiArray& message) {
    const std::size_t expected = 9U * horizon_;
    if (message.data.size() != expected) {
      context_aware_ = false;
      return;
    }
    human_mean_.assign(message.data.begin(), message.data.begin() + static_cast<std::ptrdiff_t>(2U * horizon_));
    context_.assign(
        message.data.begin() + static_cast<std::ptrdiff_t>(2U * horizon_),
        message.data.begin() + static_cast<std::ptrdiff_t>(3U * horizon_));
    covariance_.assign(
        message.data.begin() + static_cast<std::ptrdiff_t>(3U * horizon_),
        message.data.begin() + static_cast<std::ptrdiff_t>(7U * horizon_));
    nominal_robot_.assign(
        message.data.begin() + static_cast<std::ptrdiff_t>(7U * horizon_), message.data.end());
    context_aware_ = std::all_of(message.data.begin(), message.data.end(), [](double value) {
      return std::isfinite(value);
    });
  }

  bool stateFresh() const {
    return have_state_ && (now() - last_state_time_).seconds() <= state_timeout_s_;
  }

  void publishZero() {
    command_pub_->publish(geometry_msgs::msg::Twist{});
    previous_command_ = {0.0, 0.0, 0.0};
  }

  void controlStep() {
    if (!stateFresh() || !have_reference_) {
      controller_->Reset();
      publishZero();
      return;
    }
    try {
      const std::span<const double> empty;
      const cca::control::ControllerInput input{
          std::span<const double>(state_.data(), state_.size()),
          std::span<const double>(reference_.data(), reference_.size()),
          std::span<const double>(previous_command_.data(), previous_command_.size()),
          context_aware_ ? std::span<const double>(human_mean_.data(), human_mean_.size()) : empty,
          context_aware_ ? std::span<const double>(context_.data(), context_.size()) : empty,
          context_aware_ ? std::span<const double>(covariance_.data(), covariance_.size()) : empty,
          context_aware_ ? std::span<const double>(nominal_robot_.data(), nominal_robot_.size()) : empty,
          empty,
          context_aware_,
      };
      const auto output = controller_->Command(input);
      geometry_msgs::msg::Twist command;
      command.linear.x = output.first_command_mps[0];
      command.linear.y = output.first_command_mps[1];
      command.angular.z = output.first_command_mps[2];
      command_pub_->publish(command);
      previous_command_ = output.first_command_mps;
      publishPrediction(output.predicted_states);
      std_msgs::msg::Float64MultiArray diagnostics;
      diagnostics.data = {
          output.solve_time_ms,
          output.objective,
          output.maximum_constraint_violation,
          static_cast<double>(output.status),
          output.deadline_missed ? 1.0 : 0.0,
          output.risk_bound,
          output.maximum_risk_slack_m,
      };
      diagnostics_pub_->publish(diagnostics);
      if (output.deadline_missed) {
        RCLCPP_WARN_THROTTLE(
            get_logger(), *get_clock(), 2000,
            "CA-NMPC deadline missed: %.3f ms", output.solve_time_ms);
      }
    } catch (const std::exception& error) {
      RCLCPP_ERROR_THROTTLE(get_logger(), *get_clock(), 2000, "CA-NMPC failed: %s", error.what());
      controller_->Reset();
      publishZero();
    }
  }

  void publishPrediction(const std::vector<double>& predicted) {
    nav_msgs::msg::Path path;
    path.header.stamp = now();
    path.header.frame_id = "odom";
    for (std::size_t step = 0U; step < horizon_; ++step) {
      if (predicted.size() < 6U * (step + 1U)) {
        break;
      }
      geometry_msgs::msg::PoseStamped pose;
      pose.header = path.header;
      pose.pose.position.x = predicted[6U * step];
      pose.pose.position.y = predicted[6U * step + 1U];
      tf2::Quaternion quaternion;
      quaternion.setRPY(0.0, 0.0, predicted[6U * step + 2U]);
      pose.pose.orientation = tf2::toMsg(quaternion);
      path.poses.push_back(pose);
    }
    predicted_pub_->publish(path);
  }

  double period_s_{0.05};
  double state_timeout_s_{0.25};
  std::size_t horizon_{6U};
  std::string state_topic_;
  std::string reference_topic_;
  std::string context_topic_;
  std::string command_topic_;
  std::string predicted_topic_;
  std::string diagnostics_topic_;
  std::unique_ptr<cca::control::Controller> controller_;
  std::array<double, 6U> state_{};
  std::array<double, 3U> previous_command_{};
  std::vector<double> reference_;
  std::vector<double> human_mean_;
  std::vector<double> context_;
  std::vector<double> covariance_;
  std::vector<double> nominal_robot_;
  rclcpp::Time last_state_time_{0, 0, RCL_ROS_TIME};
  bool have_state_{false};
  bool have_reference_{false};
  bool context_aware_{false};
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr state_sub_;
  rclcpp::Subscription<nav_msgs::msg::Path>::SharedPtr reference_sub_;
  rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr context_sub_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr command_pub_;
  rclcpp::Publisher<nav_msgs::msg::Path>::SharedPtr predicted_pub_;
  rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr diagnostics_pub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<CcaNmpcNode>());
  rclcpp::shutdown();
  return 0;
}
