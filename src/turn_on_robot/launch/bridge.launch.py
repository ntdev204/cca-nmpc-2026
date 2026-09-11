from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("enabled", default_value="true"),
            DeclareLaunchArgument("role", default_value="robot"),
            DeclareLaunchArgument("label", default_value="cca_robot"),
            DeclareLaunchArgument("host", default_value="0.0.0.0"),
            DeclareLaunchArgument("port", default_value="8000"),
            DeclareLaunchArgument("manual_cmd_vel_topic", default_value="/manual_cmd_vel"),
            DeclareLaunchArgument("manual_republish_hz", default_value="20.0"),
            DeclareLaunchArgument("odom_topic", default_value="/odometry/raw"),
            DeclareLaunchArgument("scan_topic", default_value="/scan"),
            DeclareLaunchArgument("map_topic", default_value="/map"),
            DeclareLaunchArgument("camera_topic", default_value="/camera/color/image_raw"),
            DeclareLaunchArgument(
                "slam_pause_service",
                default_value="/slam_toolbox/pause_new_measurements",
            ),
            DeclareLaunchArgument(
                "slam_start_service", default_value="/slam_manager/start"
            ),
            DeclareLaunchArgument(
                "slam_stop_service", default_value="/slam_manager/stop"
            ),
            DeclareLaunchArgument(
                "slam_reset_service", default_value="/slam_manager/reset"
            ),
            DeclareLaunchArgument(
                "odom_reset_service", default_value="/odometry/reset"
            ),
            DeclareLaunchArgument("slam_enabled", default_value="true"),
            DeclareLaunchArgument(
                "slam_save_service", default_value="/slam_toolbox/save_map"
            ),
            DeclareLaunchArgument(
                "localization_map_topic", default_value="/slam_manager/localize_map"
            ),
            DeclareLaunchArgument(
                "map_save_root", default_value="/home/rai/cca-nmpc-ros2/maps"
            ),
            DeclareLaunchArgument("map_cleanup_enabled", default_value="true"),
            DeclareLaunchArgument("map_cleanup_min_component_cells", default_value="3"),
            DeclareLaunchArgument("navigation_inflation_m", default_value="0.38"),
            DeclareLaunchArgument("navigation_snap_radius_m", default_value="0.45"),
            SetEnvironmentVariable("RAI_DEVICE_ROLE", LaunchConfiguration("role")),
            SetEnvironmentVariable("RAI_DEVICE_LABEL", LaunchConfiguration("label")),
            SetEnvironmentVariable("RAI_BRIDGE_HOST", LaunchConfiguration("host")),
            SetEnvironmentVariable("RAI_BRIDGE_PORT", LaunchConfiguration("port")),
            Node(
                package="rai_runtime_bridge",
                executable="runtime_bridge",
                name="rai_runtime_bridge",
                output="screen",
                parameters=[
                    {
                        "manual_cmd_vel_topic": LaunchConfiguration("manual_cmd_vel_topic"),
                        "manual_republish_hz": LaunchConfiguration("manual_republish_hz"),
                        "odom_topic": LaunchConfiguration("odom_topic"),
                        "scan_topic": LaunchConfiguration("scan_topic"),
                        "map_topic": LaunchConfiguration("map_topic"),
                        "camera_topic": LaunchConfiguration("camera_topic"),
                        "slam_pause_service": LaunchConfiguration("slam_pause_service"),
                        "slam_start_service": LaunchConfiguration("slam_start_service"),
                        "slam_stop_service": LaunchConfiguration("slam_stop_service"),
                        "slam_reset_service": LaunchConfiguration("slam_reset_service"),
                        "odom_reset_service": LaunchConfiguration("odom_reset_service"),
                        "slam_enabled": LaunchConfiguration("slam_enabled"),
                        "slam_save_service": LaunchConfiguration("slam_save_service"),
                        "localization_map_topic": LaunchConfiguration(
                            "localization_map_topic"
                        ),
                        "map_save_root": LaunchConfiguration("map_save_root"),
                        "map_cleanup_enabled": LaunchConfiguration("map_cleanup_enabled"),
                        "map_cleanup_min_component_cells": LaunchConfiguration(
                            "map_cleanup_min_component_cells"
                        ),
                        "navigation_inflation_m": LaunchConfiguration("navigation_inflation_m"),
                        "navigation_snap_radius_m": LaunchConfiguration("navigation_snap_radius_m"),
                    }
                ],
                condition=IfCondition(LaunchConfiguration("enabled")),
            ),
        ]
    )
