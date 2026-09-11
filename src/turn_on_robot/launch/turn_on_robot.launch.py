from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Backward-compatible entrypoint for the canonical bringup launch."""
    launch_names = (
        "use_slam",
        "use_nav2",
        "use_bridge",
        "use_lidar",
        "use_camera",
        "use_sim_time",
        "port",
        "map",
        "slam_params_file",
        "lidar_package",
        "lidar_launch_file",
        "camera_package",
        "camera_launch_file",
        "laser_frame",
        "laser_x",
        "laser_y",
        "laser_z",
        "laser_yaw",
        "laser_pitch",
        "laser_roll",
        "bridge_role",
        "bridge_label",
        "bridge_host",
        "bridge_port",
        "manual_cmd_vel_topic",
        "manual_republish_hz",
        "odom_topic",
        "scan_topic",
        "map_topic",
        "camera_topic",
        "slam_pause_service",
        "slam_start_service",
        "slam_stop_service",
        "slam_reset_service",
        "odom_reset_service",
        "slam_save_service",
        "map_save_root",
        "navigation_inflation_m",
        "navigation_snap_radius_m",
        "ros_domain_id",
        "rmw_implementation",
        "ros_localhost_only",
    )
    defaults = {
        "use_slam": "true",
        "use_nav2": "false",
        "use_bridge": "true",
        "use_lidar": "true",
        "use_camera": "true",
        "use_sim_time": "false",
        "port": "/dev/rai_controller",
        "map": "",
        "slam_params_file": PathJoinSubstitution(
            [FindPackageShare("cca_slam"), "config", "slam_toolbox.yaml"]
        ),
        "lidar_package": "lslidar_driver",
        "lidar_launch_file": "lsn10p_launch.py",
        "camera_package": "astra_camera",
        "camera_launch_file": "astra.launch.xml",
        "laser_frame": "laser",
        "laser_x": "0.0",
        "laser_y": "0.0",
        "laser_z": "0.18",
        "laser_yaw": "0.0",
        "laser_pitch": "0.0",
        "laser_roll": "0.0",
        "bridge_role": "robot",
        "bridge_label": "cca_robot",
        "bridge_host": "0.0.0.0",
        "bridge_port": "8000",
        "manual_cmd_vel_topic": "/manual_cmd_vel",
        "manual_republish_hz": "20.0",
        "odom_topic": "/odometry/raw",
        "scan_topic": "/scan",
        "map_topic": "/map",
        "camera_topic": "/camera/color/image_raw",
        "slam_pause_service": "/slam_toolbox/pause_new_measurements",
        "slam_start_service": "/slam_manager/start",
        "slam_stop_service": "/slam_manager/stop",
        "slam_reset_service": "/slam_manager/reset",
        "odom_reset_service": "/odometry/reset",
        "slam_save_service": "/slam_toolbox/save_map",
        "map_save_root": "/home/rai/cca-nmpc-ros2/maps",
        "navigation_inflation_m": "0.38",
        "navigation_snap_radius_m": "0.45",
        "ros_domain_id": "0",
        "rmw_implementation": "rmw_fastrtps_cpp",
        "ros_localhost_only": "0",
    }

    bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("turn_on_robot"), "launch", "bringup.launch.py"]
            )
        ),
        launch_arguments={name: LaunchConfiguration(name) for name in launch_names}.items(),
    )

    return LaunchDescription(
        [DeclareLaunchArgument(name, default_value=defaults[name]) for name in launch_names]
        + [bringup]
    )
