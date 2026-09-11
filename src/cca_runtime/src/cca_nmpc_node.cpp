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
#include "sensor_msgs/msg/laser_scan.hpp"
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
    robot_radius_m_ = declare_parameter<double>("robot_radius_m", 0.29);
    const double human_radius = declare_parameter<double>("human_radius_m", 0.34);
    const double human_clearance = declare_parameter<double>("human_clearance_m", 0.623);
    max_speed_mps_ = declare_parameter<double>("max_speed_mps", 0.30);
    max_linear_accel_mps2_ = declare_parameter<double>("max_linear_accel_mps2", 1.0);
    max_lateral_accel_mps2_ = declare_parameter<double>("max_lateral_accel_mps2", 1.0);
    max_yaw_accel_radps2_ = declare_parameter<double>("max_yaw_accel_radps2", 1.6);
    scan_topic_ = declare_parameter<std::string>("scan_topic", "/scan");
    lidar_timeout_s_ = declare_parameter<double>("lidar_timeout_s", 0.25);
    obstacle_stop_distance_m_ = declare_parameter<double>("obstacle_stop_distance_m", 0.29);
    obstacle_inflation_m_ = declare_parameter<double>("obstacle_inflation_m", 0.0);
    obstacle_inflation_min_m_ = declare_parameter<double>("obstacle_inflation_min_m", 0.0);
    obstacle_inflation_max_m_ = declare_parameter<double>("obstacle_inflation_max_m", 0.12);
    obstacle_reaction_time_s_ = declare_parameter<double>("obstacle_reaction_time_s", 0.25);
    obstacle_deceleration_mps2_ = declare_parameter<double>("obstacle_deceleration_mps2", 0.8);
    obstacle_narrow_corridor_m_ = declare_parameter<double>("obstacle_narrow_corridor_m", 0.90);
    obstacle_narrow_scale_min_ = declare_parameter<double>("obstacle_narrow_scale_min", 0.25);
    lidar_max_range_m_ = declare_parameter<double>("lidar_max_range_m", 3.0);
    state_timeout_s_ = declare_parameter<double>("state_timeout_s", 0.25);
    state_topic_ = declare_parameter<std::string>("state_topic", "/odometry/raw");
    reference_topic_ = declare_parameter<std::string>("reference_topic", "/cca/local_reference");
    context_topic_ = declare_parameter<std::string>("context_topic", "/cca/context_prediction");
    command_topic_ = declare_parameter<std::string>("command_topic", "/cmd_vel");
    predicted_topic_ = declare_parameter<std::string>("predicted_topic", "/cca/predicted_path");
    diagnostics_topic_ = declare_parameter<std::string>("diagnostics_topic", "/cca/controller_diagnostics");
    if (kind != "cca_nmpc" || !(period_s_ > 0.0) || horizon_ == 0U ||
        !(deadline_ms > 0.0) || !(state_timeout_s_ > 0.0) || !(max_speed_mps_ > 0.0) ||
        !(robot_radius_m_ > 0.0) || !(max_linear_accel_mps2_ > 0.0) ||
        !(max_lateral_accel_mps2_ > 0.0) || !(max_yaw_accel_radps2_ > 0.0) ||
        !(lidar_timeout_s_ > 0.0) || !(obstacle_stop_distance_m_ > 0.0) ||
        !(obstacle_inflation_m_ >= 0.0) || !(obstacle_inflation_min_m_ >= 0.0) ||
        !(obstacle_inflation_max_m_ >= obstacle_inflation_min_m_) ||
        !(obstacle_reaction_time_s_ >= 0.0) || !(obstacle_deceleration_mps2_ > 0.0) ||
        !(obstacle_narrow_corridor_m_ > robot_radius_m_) ||
        !(obstacle_narrow_scale_min_ > 0.0) || !(obstacle_narrow_scale_min_ <= 1.0) ||
        !(lidar_max_range_m_ > 0.0)) {
      throw std::invalid_argument("CA-NMPC parameters are invalid");
    }

    cca::control::ControllerConfig config{};
    config.dt_s = period_s_;
    config.horizon = horizon_;
    config.deadline_ms = deadline_ms;
    config.robot_radius_m = robot_radius_m_;
    config.human_radius_m = human_radius;
    config.human_clearance_m = human_clearance;
    config.max_speed_mps = max_speed_mps_;
    config.max_linear_accel_mps2 = max_linear_accel_mps2_;
    config.max_lateral_accel_mps2 = max_lateral_accel_mps2_;
    config.max_yaw_accel_radps2 = max_yaw_accel_radps2_;
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
    scan_sub_ = create_subscription<sensor_msgs::msg::LaserScan>(
        scan_topic_, rclcpp::SensorDataQoS(),
        [this](const sensor_msgs::msg::LaserScan::SharedPtr message) { onScan(*message); });
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

  void onScan(const sensor_msgs::msg::LaserScan& message) {
    if (!have_state_) {
      return;
    }
    const std::size_t stride = std::max<std::size_t>(1U, message.ranges.size() / 180U);
    std::vector<double> next_obstacles;
    next_obstacles.reserve((message.ranges.size() / stride + 1U) * 4U);
    double closest = std::numeric_limits<double>::infinity();
    double left_clearance = usable_max;
    double right_clearance = usable_max;
    bool have_measurement = false;
    const double yaw = state_[2];
    const double c = std::cos(yaw);
    const double s = std::sin(yaw);
    const double usable_max = std::min(lidar_max_range_m_, static_cast<double>(message.range_max));
    for (std::size_t index = 0U; index < message.ranges.size(); index += stride) {
      const double range = message.ranges[index];
      if (!std::isfinite(range) || range < message.range_min || range > usable_max) {
        continue;
      }
      have_measurement = true;
      closest = std::min(closest, range);
      const double angle = message.angle_min + static_cast<double>(index) * message.angle_increment;
      const double local_x = range * std::cos(angle);
      const double local_y = range * std::sin(angle);
      constexpr double quarter_pi = 0.78539816339744830962;
      constexpr double three_quarter_pi = 2.35619449019234492885;
      if (angle > quarter_pi && angle < three_quarter_pi) {
        left_clearance = std::min(left_clearance, range);
      } else if (angle < -quarter_pi && angle > -three_quarter_pi) {
        right_clearance = std::min(right_clearance, range);
      }
      next_obstacles.push_back(state_[0] + c * local_x - s * local_y);
      next_obstacles.push_back(state_[1] + s * local_x + c * local_y);
      next_obstacles.push_back(0.0);
      next_obstacles.push_back(0.0);
    }
    left_clearance_m_ = std::clamp(left_clearance, 0.05, lidar_max_range_m_);
    right_clearance_m_ = std::clamp(right_clearance, 0.05, lidar_max_range_m_);
    dynamic_inflation_m_ = dynamicObstacleInflation();
    for (std::size_t index = 2U; index + 1U < next_obstacles.size(); index += 4U) {
      next_obstacles[index] = dynamic_inflation_m_;
      next_obstacles[index + 1U] = dynamic_inflation_m_;
    }
    obstacles_ = std::move(next_obstacles);
    closest_lidar_range_m_ = closest;
    have_scan_measurement_ = have_measurement;
    last_scan_time_ = now();
  }

  bool stateFresh() const {
    return have_state_ && (now() - last_state_time_).seconds() <= state_timeout_s_;
  }

  bool scanFresh() const {
    return last_scan_time_.nanoseconds() > 0 &&
        have_scan_measurement_ && (now() - last_scan_time_).seconds() <= lidar_timeout_s_;
  }

  void publishZero() {
    command_pub_->publish(geometry_msgs::msg::Twist{});
    previous_command_ = {0.0, 0.0, 0.0};
  }

  void controlStep() {
    if (!stateFresh() || !have_reference_ || !scanFresh()) {
      controller_->Reset();
      publishZero();
      return;
    }
    try {
      const std::span<const double> empty;
      const std::span<const double> obstacles(obstacles_.data(), obstacles_.size());
      const cca::control::ControllerInput input{
          std::span<const double>(state_.data(), state_.size()),
          std::span<const double>(reference_.data(), reference_.size()),
          std::span<const double>(previous_command_.data(), previous_command_.size()),
          context_aware_ ? std::span<const double>(human_mean_.data(), human_mean_.size()) : empty,
          context_aware_ ? std::span<const double>(context_.data(), context_.size()) : empty,
          context_aware_ ? std::span<const double>(covariance_.data(), covariance_.size()) : empty,
          context_aware_ ? std::span<const double>(nominal_robot_.data(), nominal_robot_.size()) : empty,
          obstacles,
          context_aware_,
      };
      const auto output = controller_->Command(input);
      geometry_msgs::msg::Twist command;
      command.linear.x = output.first_command_mps[0];
      command.linear.y = output.first_command_mps[1];
      command.angular.z = output.first_command_mps[2];
      const double stop_distance = std::max(
          obstacle_stop_distance_m_, robot_radius_m_ + dynamic_inflation_m_);
      if (closest_lidar_range_m_ <= stop_distance) {
        command.linear.x = 0.0;
        command.linear.y = 0.0;
      }
      command_pub_->publish(command);
      previous_command_ = {command.linear.x, command.linear.y, command.angular.z};
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
          std::isfinite(closest_lidar_range_m_) ? closest_lidar_range_m_ : -1.0,
          static_cast<double>(obstacles_.size() / 4U),
          max_speed_mps_,
          dynamic_inflation_m_,
          stop_distance,
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

  double dynamicObstacleInflation() const {
    const double speed = std::hypot(state_[3], state_[4]);
    const double braking_margin = speed * obstacle_reaction_time_s_ +
        (speed * speed) / (2.0 * obstacle_deceleration_mps2_);
    double margin = std::clamp(
        obstacle_inflation_m_ + braking_margin,
        obstacle_inflation_min_m_, obstacle_inflation_max_m_);
    const double side_clearance = std::min(left_clearance_m_, right_clearance_m_);
    const double corridor_span = std::max(
        obstacle_narrow_corridor_m_ - robot_radius_m_, 1.0e-3);
    const double narrow_scale = std::clamp(
        (side_clearance - robot_radius_m_) / corridor_span,
        obstacle_narrow_scale_min_, 1.0);
    margin *= narrow_scale;
    return std::clamp(margin, obstacle_inflation_min_m_, obstacle_inflation_max_m_);
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
  double max_speed_mps_{0.30};
  double robot_radius_m_{0.29};
  double max_linear_accel_mps2_{1.0};
  double max_lateral_accel_mps2_{1.0};
  double max_yaw_accel_radps2_{1.6};
  double lidar_timeout_s_{0.25};
  double obstacle_stop_distance_m_{0.29};
  double obstacle_inflation_m_{0.0};
  double obstacle_inflation_min_m_{0.0};
  double obstacle_inflation_max_m_{0.12};
  double obstacle_reaction_time_s_{0.25};
  double obstacle_deceleration_mps2_{0.8};
  double obstacle_narrow_corridor_m_{0.90};
  double obstacle_narrow_scale_min_{0.25};
  double lidar_max_range_m_{3.0};
  double closest_lidar_range_m_{std::numeric_limits<double>::infinity()};
  double left_clearance_m_{3.0};
  double right_clearance_m_{3.0};
  double dynamic_inflation_m_{0.0};
  std::size_t horizon_{6U};
  std::string state_topic_;
  std::string reference_topic_;
  std::string context_topic_;
  std::string scan_topic_;
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
  std::vector<double> obstacles_;
  rclcpp::Time last_state_time_{0, 0, RCL_ROS_TIME};
  rclcpp::Time last_scan_time_{0, 0, RCL_ROS_TIME};
  bool have_state_{false};
  bool have_reference_{false};
  bool have_scan_measurement_{false};
  bool context_aware_{false};
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr state_sub_;
  rclcpp::Subscription<nav_msgs::msg::Path>::SharedPtr reference_sub_;
  rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr context_sub_;
  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr scan_sub_;
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
