#include <algorithm>
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
#include "std_msgs/msg/float64.hpp"

namespace {

double DistanceSquared(const geometry_msgs::msg::Pose& pose, double x, double y) {
  const double dx = pose.position.x - x;
  const double dy = pose.position.y - y;
  return dx * dx + dy * dy;
}

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
    if (horizon_ == 0U || !(rate_hz > 0.0)) {
      throw std::invalid_argument("CCA reference parameters are invalid");
    }

    global_sub_ = create_subscription<nav_msgs::msg::Path>(
        global_topic_, rclcpp::QoS(1).reliable(),
        [this](const nav_msgs::msg::Path::SharedPtr message) { global_path_ = *message; });
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
    local_pub_ = create_publisher<nav_msgs::msg::Path>(local_topic_, rclcpp::QoS(1).reliable());
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
    const std::size_t active_count = std::max<std::size_t>(
        2U, static_cast<std::size_t>(std::llround(nominal_count * context_scale)));
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
  }

  std::size_t horizon_{6U};
  std::string global_topic_;
  std::string local_topic_;
  std::string state_topic_;
  std::string context_topic_;
  nav_msgs::msg::Path global_path_;
  double state_x_{0.0};
  double state_y_{0.0};
  double context_score_{0.0};
  bool have_state_{false};
  rclcpp::Subscription<nav_msgs::msg::Path>::SharedPtr global_sub_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr state_sub_;
  rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr context_sub_;
  rclcpp::Publisher<nav_msgs::msg::Path>::SharedPtr local_pub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<CcaReferenceNode>());
  rclcpp::shutdown();
  return 0;
}
