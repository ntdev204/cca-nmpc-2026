#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "control/stm_serial.hpp"
#include "geometry_msgs/msg/transform_stamped.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "std_msgs/msg/bool.hpp"
#include "std_msgs/msg/float32.hpp"
#include "std_srvs/srv/trigger.hpp"
#include "tf2/LinearMath/Quaternion.h"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"
#include "tf2_ros/transform_broadcaster.h"

class StmBridgeNode final : public rclcpp::Node {
public:
  StmBridgeNode() : Node("cca_stm_bridge") {
    port_ = declare_parameter<std::string>("port", "/dev/rai_controller");
    baudrate_ = declare_parameter<int>("baudrate", 115200);
    timeout_ms_ = declare_parameter<int>("timeout_ms", 20);
    const double publish_rate_hz = declare_parameter<double>("publish_rate_hz", 50.0);
    command_timeout_s_ = declare_parameter<double>("command_timeout_s", 0.20);
    command_topic_ = declare_parameter<std::string>("command_topic", "/cmd_vel");
    manual_command_topic_ = declare_parameter<std::string>("manual_command_topic", "/manual_cmd_vel");
    manual_command_timeout_s_ = declare_parameter<double>("manual_command_timeout_s", 0.35);
    odom_frame_ = declare_parameter<std::string>("odom_frame", "odom");
    base_frame_ = declare_parameter<std::string>("base_frame", "base_link");
    odom_topic_ = declare_parameter<std::string>("odom_topic", "/odometry/raw");
    imu_topic_ = declare_parameter<std::string>("imu_topic", "/imu/data");
    connected_topic_ = declare_parameter<std::string>("connected_topic", "/hardware/connected");
    voltage_topic_ = declare_parameter<std::string>("voltage_topic", "/battery/voltage");
    odom_reset_service_ = declare_parameter<std::string>("odom_reset_service", "/odometry/reset");
    if (port_.empty() || baudrate_ <= 0 || timeout_ms_ <= 0 || !(publish_rate_hz > 0.0) ||
        !(command_timeout_s_ > 0.0) || command_topic_.empty() || manual_command_topic_.empty() ||
        !(manual_command_timeout_s_ > 0.0) || odom_reset_service_.empty()) {
      throw std::invalid_argument("STM bridge parameters are invalid");
    }

    command_sub_ = create_subscription<geometry_msgs::msg::Twist>(
        command_topic_, rclcpp::QoS(1).reliable().durability_volatile(),
        [this](const geometry_msgs::msg::Twist::SharedPtr message) { onControllerCommand(*message); });
    manual_command_sub_ = create_subscription<geometry_msgs::msg::Twist>(
        manual_command_topic_, rclcpp::QoS(1).reliable().durability_volatile(),
        [this](const geometry_msgs::msg::Twist::SharedPtr message) { onManualCommand(*message); });
    odom_pub_ = create_publisher<nav_msgs::msg::Odometry>(odom_topic_, rclcpp::SensorDataQoS());
    imu_pub_ = create_publisher<sensor_msgs::msg::Imu>(imu_topic_, rclcpp::SensorDataQoS());
    connected_pub_ = create_publisher<std_msgs::msg::Bool>(connected_topic_, rclcpp::QoS(1).best_effort());
    voltage_pub_ = create_publisher<std_msgs::msg::Float32>(voltage_topic_, rclcpp::SensorDataQoS());
    odom_reset_server_ = create_service<std_srvs::srv::Trigger>(
        odom_reset_service_,
        [this](const std_srvs::srv::Trigger::Request::SharedPtr,
               std_srvs::srv::Trigger::Response::SharedPtr response) {
          serial_.SendZero();
          last_command_ = {0.0, 0.0, 0.0};
          last_command_time_ = now();
          manual_override_active_ = false;
          x_ = 0.0;
          y_ = 0.0;
          theta_ = 0.0;
          last_sample_ns_ = 0U;
          response->success = true;
          response->message = "Odometry reset to the current robot position.";
        });
    tf_broadcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);
    last_command_time_ = now();
    timer_ = create_wall_timer(
        std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::duration<double>(1.0 / publish_rate_hz)),
        [this]() { poll(); });
  }

  ~StmBridgeNode() override {
    serial_.SendZero();
    serial_.Close();
  }

private:
  void tryOpen() {
    if (serial_.IsOpen()) {
      return;
    }
    try {
      serial_.Open(port_, baudrate_, timeout_ms_);
      RCLCPP_INFO(get_logger(), "STM32 connected on %s", port_.c_str());
    } catch (const std::exception& error) {
      RCLCPP_WARN_THROTTLE(
          get_logger(), *get_clock(), 3000, "STM32 connection pending: %s", error.what());
    }
  }

  void publishConnection(bool connected) {
    std_msgs::msg::Bool message;
    message.data = connected;
    connected_pub_->publish(message);
  }

  bool manualOverrideActive() {
    if (!manual_override_active_) {
      return false;
    }
    if ((now() - last_manual_command_time_).seconds() > manual_command_timeout_s_) {
      manual_override_active_ = false;
      return false;
    }
    return true;
  }

  void onControllerCommand(const geometry_msgs::msg::Twist& message) {
    if (manualOverrideActive()) {
      return;
    }
    applyCommand(message);
  }

  void onManualCommand(const geometry_msgs::msg::Twist& message) {
    manual_override_active_ = true;
    last_manual_command_time_ = now();
    applyCommand(message);
  }

  void applyCommand(const geometry_msgs::msg::Twist& message) {
    const std::array<double, 3U> command{
        message.linear.x, message.linear.y, message.angular.z};
    if (!std::all_of(command.begin(), command.end(), [](double value) {
          return std::isfinite(value);
        })) {
      serial_.SendZero();
      return;
    }
    last_command_time_ = now();
    last_command_ = command;
    if (!serial_.IsOpen()) {
      return;
    }
    try {
      serial_.SendVelocity({command[0], command[1], command[2], 0U, 0U});
    } catch (const std::exception& error) {
      RCLCPP_ERROR_THROTTLE(get_logger(), *get_clock(), 2000, "STM command failed: %s", error.what());
      serial_.Close();
    }
  }

  void poll() {
    tryOpen();
    if (!serial_.IsOpen()) {
      publishConnection(false);
      return;
    }
    manualOverrideActive();
    if ((now() - last_command_time_).seconds() > command_timeout_s_) {
      serial_.SendZero();
      last_command_ = {0.0, 0.0, 0.0};
    }
    try {
      const auto samples = serial_.ReadAvailable(static_cast<std::uint64_t>(now().nanoseconds()));
      for (const auto& sample : samples) {
        publishSample(sample);
      }
      publishConnection(true);
    } catch (const std::exception& error) {
      RCLCPP_ERROR_THROTTLE(get_logger(), *get_clock(), 2000, "STM telemetry failed: %s", error.what());
      serial_.Close();
      publishConnection(false);
    }
  }

  void publishSample(const cca::hardware::Telemetry& sample) {
    const rclcpp::Time stamp(static_cast<rcl_time_point_value_t>(sample.timestamp_ns), RCL_ROS_TIME);
    if (last_sample_ns_ != 0U && sample.timestamp_ns >= last_sample_ns_) {
      const double dt = std::min(
          0.25, static_cast<double>(sample.timestamp_ns - last_sample_ns_) * 1.0e-9);
      const double c = std::cos(theta_);
      const double s = std::sin(theta_);
      x_ += dt * (c * sample.vx_mps - s * sample.vy_mps);
      y_ += dt * (s * sample.vx_mps + c * sample.vy_mps);
      theta_ = std::atan2(std::sin(theta_ + dt * sample.wz_radps),
                          std::cos(theta_ + dt * sample.wz_radps));
    }
    last_sample_ns_ = sample.timestamp_ns;

    nav_msgs::msg::Odometry odom;
    odom.header.stamp = stamp;
    odom.header.frame_id = odom_frame_;
    odom.child_frame_id = base_frame_;
    odom.pose.pose.position.x = x_;
    odom.pose.pose.position.y = y_;
    tf2::Quaternion quaternion;
    quaternion.setRPY(0.0, 0.0, theta_);
    odom.pose.pose.orientation = tf2::toMsg(quaternion);
    odom.twist.twist.linear.x = sample.vx_mps;
    odom.twist.twist.linear.y = sample.vy_mps;
    odom.twist.twist.angular.z = sample.wz_radps;
    odom_pub_->publish(odom);

    std_msgs::msg::Float32 voltage;
    voltage.data = static_cast<float>(sample.voltage_v);
    voltage_pub_->publish(voltage);

    sensor_msgs::msg::Imu imu;
    imu.header.stamp = stamp;
    imu.header.frame_id = "imu_link";
    imu.linear_acceleration.x = sample.accel_x_mps2;
    imu.linear_acceleration.y = sample.accel_y_mps2;
    imu.linear_acceleration.z = sample.accel_z_mps2;
    imu.angular_velocity.x = sample.gyro_x_radps;
    imu.angular_velocity.y = sample.gyro_y_radps;
    imu.angular_velocity.z = sample.gyro_z_radps;
    imu_pub_->publish(imu);

    geometry_msgs::msg::TransformStamped transform;
    transform.header = odom.header;
    transform.child_frame_id = base_frame_;
    transform.transform.translation.x = x_;
    transform.transform.translation.y = y_;
    transform.transform.rotation = odom.pose.pose.orientation;
    tf_broadcaster_->sendTransform(transform);
  }

  std::string port_;
  int baudrate_{115200};
  int timeout_ms_{20};
  double command_timeout_s_{0.20};
  double manual_command_timeout_s_{0.35};
  std::string command_topic_;
  std::string manual_command_topic_;
  std::string odom_frame_;
  std::string base_frame_;
  std::string odom_topic_;
  std::string imu_topic_;
  std::string connected_topic_;
  std::string voltage_topic_;
  std::string odom_reset_service_;
  cca::hardware::SerialPort serial_;
  std::array<double, 3U> last_command_{};
  rclcpp::Time last_command_time_{0, 0, RCL_ROS_TIME};
  std::uint64_t last_sample_ns_{0U};
  double x_{0.0};
  double y_{0.0};
  double theta_{0.0};
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr command_sub_;
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr manual_command_sub_;
  rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
  rclcpp::Publisher<sensor_msgs::msg::Imu>::SharedPtr imu_pub_;
  rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr connected_pub_;
  rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr voltage_pub_;
  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr odom_reset_server_;
  std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Time last_manual_command_time_{0, 0, RCL_ROS_TIME};
  bool manual_override_active_{false};
};

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<StmBridgeNode>());
  rclcpp::shutdown();
  return 0;
}
