#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "geometry_msgs/msg/pose_stamped.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "nav_msgs/msg/path.hpp"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "std_msgs/msg/float64.hpp"
#include "std_msgs/msg/float64_multi_array.hpp"

namespace {

double DistanceSquared(const geometry_msgs::msg::Pose& pose, double x, double y) {
  const double dx = pose.position.x - x;
  const double dy = pose.position.y - y;
  return dx * dx + dy * dy;
}

// A compact recurrent inference block keeps trajectory adaptation in the
// runtime. Its fixed weights are deliberately small and deterministic; the
// LiDAR safety layer remains authoritative for collision avoidance.
class LstmPathFollower final {
public:
  static constexpr std::size_t kInputSize = 6U;
  static constexpr std::size_t kHiddenSize = 8U;

  LstmPathFollower() {
    for (std::size_t gate = 0U; gate < 4U; ++gate) {
      for (std::size_t unit = 0U; unit < kHiddenSize; ++unit) {
        bias_[gate * kHiddenSize + unit] = gate == 1U ? 1.0 : 0.0;
        for (std::size_t feature = 0U; feature < kInputSize; ++feature) {
          const int pattern = static_cast<int>((gate * 13U + unit * 7U + feature * 3U) % 7U) - 3;
          input_weights_[(gate * kHiddenSize + unit) * kInputSize + feature] =
              0.045 * static_cast<double>(pattern);
        }
        for (std::size_t previous = 0U; previous < kHiddenSize; ++previous) {
          const int pattern = static_cast<int>((gate * 5U + unit * 3U + previous * 11U) % 5U) - 2;
          hidden_weights_[(gate * kHiddenSize + unit) * kHiddenSize + previous] =
              0.035 * static_cast<double>(pattern);
        }
      }
    }
  }

  void reset() {
    hidden_.fill(0.0);
    cell_.fill(0.0);
    lookahead_scale_ = 1.0;
    speed_scale_ = 1.0;
  }

  void update(const std::array<double, kInputSize>& input) {
    const auto previous_hidden = hidden_;
    std::array<double, 4U * kHiddenSize> gates{};
    for (std::size_t gate = 0U; gate < 4U; ++gate) {
      for (std::size_t unit = 0U; unit < kHiddenSize; ++unit) {
        double value = bias_[gate * kHiddenSize + unit];
        for (std::size_t feature = 0U; feature < kInputSize; ++feature) {
          value += input_weights_[(gate * kHiddenSize + unit) * kInputSize + feature] * input[feature];
        }
        for (std::size_t previous = 0U; previous < kHiddenSize; ++previous) {
          value += hidden_weights_[(gate * kHiddenSize + unit) * kHiddenSize + previous] * previous_hidden[previous];
        }
        gates[gate * kHiddenSize + unit] = value;
      }
    }
    for (std::size_t unit = 0U; unit < kHiddenSize; ++unit) {
      const double input_gate = sigmoid(gates[unit]);
      const double forget_gate = sigmoid(gates[kHiddenSize + unit]);
      const double candidate = std::tanh(gates[2U * kHiddenSize + unit]);
      const double output_gate = sigmoid(gates[3U * kHiddenSize + unit]);
      cell_[unit] = forget_gate * cell_[unit] + input_gate * candidate;
      hidden_[unit] = output_gate * std::tanh(cell_[unit]);
    }
    lookahead_scale_ = std::clamp(0.78 + 0.25 * std::tanh(hidden_[0] - hidden_[1]), 0.45, 1.05);
    speed_scale_ = std::clamp(0.76 + 0.24 * std::tanh(hidden_[2] + hidden_[3]), 0.35, 1.0);
  }

  double lookaheadScale() const { return lookahead_scale_; }
  double speedScale() const { return speed_scale_; }

private:
  static double sigmoid(const double value) {
    if (value >= 0.0) {
      const double z = std::exp(-value);
      return 1.0 / (1.0 + z);
    }
    const double z = std::exp(value);
    return z / (1.0 + z);
  }

  std::array<double, 4U * kHiddenSize * kInputSize> input_weights_{};
  std::array<double, 4U * kHiddenSize * kHiddenSize> hidden_weights_{};
  std::array<double, 4U * kHiddenSize> bias_{};
  std::array<double, kHiddenSize> hidden_{};
  std::array<double, kHiddenSize> cell_{};
  double lookahead_scale_{1.0};
  double speed_scale_{1.0};
};

}  // namespace

class CcaReferenceNode final : public rclcpp::Node {
public:
  CcaReferenceNode() : Node("cca_reference_node") {
    horizon_ = static_cast<std::size_t>(declare_parameter<int64_t>("horizon", 6));
    const double rate_hz = declare_parameter<double>("publish_rate_hz", 20.0);
    global_topic_ = declare_parameter<std::string>("global_path_topic", "/cca/global_path");
    local_topic_ = declare_parameter<std::string>("local_reference_topic", "/cca/local_reference");
    state_topic_ = declare_parameter<std::string>("state_topic", "/odometry/raw");
    context_topic_ = declare_parameter<std::string>("context_topic", "/cca/context_score");
    scan_topic_ = declare_parameter<std::string>("scan_topic", "/scan");
    lstm_diagnostics_topic_ = declare_parameter<std::string>(
        "lstm_diagnostics_topic", "/cca/lstm_tracker_diagnostics");
    if (horizon_ == 0U || !(rate_hz > 0.0)) {
      throw std::invalid_argument("CCA reference parameters are invalid");
    }

    global_sub_ = create_subscription<nav_msgs::msg::Path>(
        global_topic_, rclcpp::QoS(1).reliable(),
        [this](const nav_msgs::msg::Path::SharedPtr message) {
          global_path_ = *message;
          lstm_.reset();
        });
    state_sub_ = create_subscription<nav_msgs::msg::Odometry>(
        state_topic_, rclcpp::SensorDataQoS(),
        [this](const nav_msgs::msg::Odometry::SharedPtr message) {
          state_x_ = message->pose.pose.position.x;
          state_y_ = message->pose.pose.position.y;
          have_state_ = std::isfinite(state_x_) && std::isfinite(state_y_);
        });
    context_sub_ = create_subscription<std_msgs::msg::Float64>(
        context_topic_, rclcpp::QoS(1).best_effort(),
        [this](const std_msgs::msg::Float64::SharedPtr message) {
          context_score_ = std::clamp(message->data, 0.0, 1.0);
        });
    scan_sub_ = create_subscription<sensor_msgs::msg::LaserScan>(
        scan_topic_, rclcpp::SensorDataQoS(),
        [this](const sensor_msgs::msg::LaserScan::SharedPtr message) { onScan(*message); });
    local_pub_ = create_publisher<nav_msgs::msg::Path>(local_topic_, rclcpp::QoS(1).reliable());
    lstm_diagnostics_pub_ = create_publisher<std_msgs::msg::Float64MultiArray>(
        lstm_diagnostics_topic_, rclcpp::QoS(1).best_effort());
    timer_ = create_wall_timer(
        std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::duration<double>(1.0 / rate_hz)),
        [this]() { publishLocalReference(); });
  }

private:
  void publishLocalReference() {
    if (global_path_.poses.empty()) {
      return;
    }

    std::size_t start = 0U;
    if (have_state_) {
      double best = std::numeric_limits<double>::infinity();
      for (std::size_t index = 0U; index < global_path_.poses.size(); ++index) {
        const double distance = DistanceSquared(
            global_path_.poses[index].pose, state_x_, state_y_);
        if (distance < best) {
          best = distance;
          start = index;
        }
      }
    }

    const std::size_t nominal_count = horizon_ + 1U;
    const double context_scale = 1.0 - 0.35 * context_score_;
    const std::size_t tangent_index = std::min(start + 1U, global_path_.poses.size() - 1U);
    const double error_x = global_path_.poses[start].pose.position.x - state_x_;
    const double error_y = global_path_.poses[start].pose.position.y - state_y_;
    const double tangent_x = global_path_.poses[tangent_index].pose.position.x -
        global_path_.poses[start].pose.position.x;
    const double tangent_y = global_path_.poses[tangent_index].pose.position.y -
        global_path_.poses[start].pose.position.y;
    const double tangent_norm = std::max(1.0e-6, std::hypot(tangent_x, tangent_y));
    const std::array<double, LstmPathFollower::kInputSize> features{
        std::clamp(error_x, -1.0, 1.0),
        std::clamp(error_y, -1.0, 1.0),
        tangent_x / tangent_norm,
        tangent_y / tangent_norm,
        std::clamp(front_clearance_ / 2.0, 0.0, 1.0),
        std::clamp((left_clearance_ - right_clearance_) / 2.0, -1.0, 1.0),
    };
    lstm_.update(features);
    const double obstacle_scale = std::clamp(front_clearance_ / 0.9, 0.25, 1.0);
    const double follower_scale = std::clamp(
        0.55 * lstm_.lookaheadScale() + 0.45 * lstm_.speedScale(), 0.30, 1.0);
    const std::size_t active_count = std::max<std::size_t>(
        2U, static_cast<std::size_t>(std::llround(
                  nominal_count * context_scale * follower_scale * obstacle_scale)));
    nav_msgs::msg::Path local;
    local.header = global_path_.header;
    local.header.stamp = now();
    local.poses.reserve(nominal_count);
    for (std::size_t step = 0U; step < nominal_count; ++step) {
      const std::size_t offset = std::min(step, active_count - 1U);
      const std::size_t index = std::min(start + offset, global_path_.poses.size() - 1U);
      auto pose = global_path_.poses[index];
      pose.header = local.header;
      local.poses.push_back(std::move(pose));
    }
    local_pub_->publish(local);
    std_msgs::msg::Float64MultiArray diagnostics;
    diagnostics.data = {
        lstm_.lookaheadScale(), lstm_.speedScale(), front_clearance_,
        left_clearance_, right_clearance_, static_cast<double>(active_count),
    };
    lstm_diagnostics_pub_->publish(diagnostics);
  }

  void onScan(const sensor_msgs::msg::LaserScan& message) {
    constexpr double half_pi = 1.57079632679489661923;
    double front = std::isfinite(message.range_max) ? message.range_max : 3.0;
    double left = front;
    double right = front;
    for (std::size_t index = 0U; index < message.ranges.size(); ++index) {
      const double range = message.ranges[index];
      if (!std::isfinite(range) || range < message.range_min || range > message.range_max) {
        continue;
      }
      const double angle = message.angle_min + static_cast<double>(index) * message.angle_increment;
      const double absolute = std::abs(angle);
      if (absolute <= half_pi / 2.0) {
        front = std::min(front, range);
      } else if (angle > 0.0) {
        left = std::min(left, range);
      } else {
        right = std::min(right, range);
      }
    }
    front_clearance_ = std::clamp(front, 0.05, 5.0);
    left_clearance_ = std::clamp(left, 0.05, 5.0);
    right_clearance_ = std::clamp(right, 0.05, 5.0);
  }

  std::size_t horizon_{6U};
  std::string global_topic_;
  std::string local_topic_;
  std::string state_topic_;
  std::string context_topic_;
  std::string scan_topic_;
  std::string lstm_diagnostics_topic_;
  nav_msgs::msg::Path global_path_;
  double state_x_{0.0};
  double state_y_{0.0};
  double context_score_{0.0};
  double front_clearance_{5.0};
  double left_clearance_{5.0};
  double right_clearance_{5.0};
  bool have_state_{false};
  LstmPathFollower lstm_;
  rclcpp::Subscription<nav_msgs::msg::Path>::SharedPtr global_sub_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr state_sub_;
  rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr context_sub_;
  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr scan_sub_;
  rclcpp::Publisher<nav_msgs::msg::Path>::SharedPtr local_pub_;
  rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr lstm_diagnostics_pub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<CcaReferenceNode>());
  rclcpp::shutdown();
  return 0;
}
