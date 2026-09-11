from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_slam = LaunchConfiguration("use_slam")
    use_nav2 = LaunchConfiguration("use_nav2")
    use_bridge = LaunchConfiguration("use_bridge")
    use_lidar = LaunchConfiguration("use_lidar")
    use_camera = LaunchConfiguration("use_camera")
    use_perception = LaunchConfiguration("use_perception")
    use_sim_time = LaunchConfiguration("use_sim_time")
    port = LaunchConfiguration("port")
    map_file = LaunchConfiguration("map")
    slam_params_file = LaunchConfiguration("slam_params_file")
    lidar_package = LaunchConfiguration("lidar_package")
    lidar_launch_file = LaunchConfiguration("lidar_launch_file")
    camera_package = LaunchConfiguration("camera_package")
    camera_launch_file = LaunchConfiguration("camera_launch_file")
    perception_model_path = LaunchConfiguration("perception_model_path")
    perception_device = LaunchConfiguration("perception_device")
    perception_confidence = LaunchConfiguration("perception_confidence")
    perception_rate_hz = LaunchConfiguration("perception_rate_hz")
    camera_horizontal_fov_rad = LaunchConfiguration("camera_horizontal_fov_rad")
    camera_yaw_offset_rad = LaunchConfiguration("camera_yaw_offset_rad")

    declarations = [
        DeclareLaunchArgument("use_slam", default_value="true"),
        DeclareLaunchArgument("use_nav2", default_value="false"),
        DeclareLaunchArgument("use_bridge", default_value="true"),
        DeclareLaunchArgument("use_lidar", default_value="true"),
        DeclareLaunchArgument("use_camera", default_value="true"),
        DeclareLaunchArgument("use_perception", default_value="true"),
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        DeclareLaunchArgument("port", default_value="/dev/rai_controller"),
        DeclareLaunchArgument("map", default_value=""),
        DeclareLaunchArgument(
            "slam_params_file",
            default_value=PathJoinSubstitution(
                [FindPackageShare("cca_slam"), "config", "slam_toolbox.yaml"]
            ),
        ),
        DeclareLaunchArgument("lidar_package", default_value="lslidar_driver"),
        DeclareLaunchArgument("lidar_launch_file", default_value="lsn10p_launch.py"),
        DeclareLaunchArgument("camera_package", default_value="astra_camera"),
        DeclareLaunchArgument("camera_launch_file", default_value="astra.launch.xml"),
        DeclareLaunchArgument(
            "perception_model_path",
            default_value="/home/rai/cca-nmpc-ros2/models/yolo26s-pose.pt",
        ),
        DeclareLaunchArgument("perception_device", default_value="auto"),
        DeclareLaunchArgument("perception_confidence", default_value="0.45"),
        DeclareLaunchArgument("perception_rate_hz", default_value="5.0"),
        DeclareLaunchArgument("camera_horizontal_fov_rad", default_value="1.0472"),
        DeclareLaunchArgument("camera_yaw_offset_rad", default_value="0.0"),
        DeclareLaunchArgument("laser_frame", default_value="laser"),
        DeclareLaunchArgument("laser_x", default_value="0.0"),
        DeclareLaunchArgument("laser_y", default_value="0.0"),
        DeclareLaunchArgument("laser_z", default_value="0.18"),
        DeclareLaunchArgument("laser_yaw", default_value="0.0"),
        DeclareLaunchArgument("laser_pitch", default_value="0.0"),
        DeclareLaunchArgument("laser_roll", default_value="0.0"),
        DeclareLaunchArgument("bridge_role", default_value="robot"),
        DeclareLaunchArgument("bridge_label", default_value="cca_robot"),
        DeclareLaunchArgument("bridge_host", default_value="0.0.0.0"),
        DeclareLaunchArgument("bridge_port", default_value="8000"),
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
        DeclareLaunchArgument(
            "slam_save_service", default_value="/slam_toolbox/save_map"
        ),
        DeclareLaunchArgument(
            "localization_map_topic", default_value="/slam_manager/localize_map"
        ),
        DeclareLaunchArgument(
            "map_save_root", default_value="/home/rai/cca-nmpc-ros2/maps"
        ),
        DeclareLaunchArgument("navigation_inflation_m", default_value="0.29"),
        DeclareLaunchArgument("navigation_snap_radius_m", default_value="0.45"),
        DeclareLaunchArgument("ros_domain_id", default_value="0"),
        DeclareLaunchArgument("rmw_implementation", default_value="rmw_fastrtps_cpp"),
        DeclareLaunchArgument("ros_localhost_only", default_value="0"),
    ]

    runtime = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("cca_runtime"), "launch", "cca_runtime.launch.py"]
            )
        ),
        launch_arguments={
            "port": port,
            "manual_command_topic": LaunchConfiguration("manual_cmd_vel_topic"),
            "odom_reset_service": LaunchConfiguration("odom_reset_service"),
        }.items(),
    )

    sensors = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("turn_on_robot"), "launch", "sensor.launch.py"]
            )
        ),
        launch_arguments={
            "use_lidar": use_lidar,
            "use_camera": use_camera,
            "lidar_package": lidar_package,
            "lidar_launch_file": lidar_launch_file,
            "camera_package": camera_package,
            "camera_launch_file": camera_launch_file,
            "laser_frame": LaunchConfiguration("laser_frame"),
            "laser_x": LaunchConfiguration("laser_x"),
            "laser_y": LaunchConfiguration("laser_y"),
            "laser_z": LaunchConfiguration("laser_z"),
            "laser_yaw": LaunchConfiguration("laser_yaw"),
            "laser_pitch": LaunchConfiguration("laser_pitch"),
            "laser_roll": LaunchConfiguration("laser_roll"),
        }.items(),
    )

    slam_supervisor = Node(
        package="rai_runtime_bridge",
        executable="slam_supervisor",
        name="slam_session_manager",
        output="screen",
        parameters=[
            {
                "slam_package": "cca_slam",
                "slam_launch_file": "online_async_launch.py",
                "slam_params_file": slam_params_file,
                "localization_launch_file": "localization_launch.py",
                "localization_map_topic": LaunchConfiguration(
                    "localization_map_topic"
                ),
                "use_sim_time": use_sim_time,
                "start_on_launch": True,
                "stop_service": LaunchConfiguration("slam_stop_service"),
                "reset_service": LaunchConfiguration("slam_reset_service"),
            }
        ],
        condition=IfCondition(use_slam),
    )

    perception = Node(
        package="cca_perception",
        executable="cca_perception_node",
        name="cca_perception_node",
        output="screen",
        parameters=[
            {
                "image_topic": LaunchConfiguration("camera_topic"),
                "scan_topic": LaunchConfiguration("scan_topic"),
                "odom_topic": LaunchConfiguration("odom_topic"),
                "model_path": perception_model_path,
                "device": perception_device,
                "confidence": perception_confidence,
                "inference_rate_hz": perception_rate_hz,
                "camera_horizontal_fov_rad": camera_horizontal_fov_rad,
                "camera_yaw_offset_rad": camera_yaw_offset_rad,
                "horizon": 6,
                "period_s": 0.05,
            }
        ],
        condition=IfCondition(use_perception),
    )

    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[{"yaml_filename": map_file, "use_sim_time": use_sim_time}],
        condition=IfCondition(use_nav2),
    )

    bridge = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("turn_on_robot"), "launch", "bridge.launch.py"]
            )
        ),
        launch_arguments={
            "role": LaunchConfiguration("bridge_role"),
            "label": LaunchConfiguration("bridge_label"),
            "host": LaunchConfiguration("bridge_host"),
            "port": LaunchConfiguration("bridge_port"),
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
            "slam_enabled": use_slam,
            "slam_save_service": LaunchConfiguration("slam_save_service"),
            "localization_map_topic": LaunchConfiguration("localization_map_topic"),
            "map_save_root": LaunchConfiguration("map_save_root"),
            "navigation_inflation_m": LaunchConfiguration("navigation_inflation_m"),
            "navigation_snap_radius_m": LaunchConfiguration("navigation_snap_radius_m"),
        }.items(),
        condition=IfCondition(use_bridge),
    )

    return LaunchDescription(
        declarations
        + [
            SetEnvironmentVariable("ROS_DOMAIN_ID", LaunchConfiguration("ros_domain_id")),
            SetEnvironmentVariable(
                "RMW_IMPLEMENTATION", LaunchConfiguration("rmw_implementation")
            ),
            SetEnvironmentVariable(
                "ROS_LOCALHOST_ONLY", LaunchConfiguration("ros_localhost_only")
            ),
            runtime,
            sensors,
            perception,
            slam_supervisor,
            map_server,
            bridge,
        ]
    )
