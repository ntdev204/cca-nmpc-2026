from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import (
    FrontendLaunchDescriptionSource,
    PythonLaunchDescriptionSource,
)
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_lidar = LaunchConfiguration("use_lidar")
    use_camera = LaunchConfiguration("use_camera")
    lidar_package = LaunchConfiguration("lidar_package")
    lidar_launch_file = LaunchConfiguration("lidar_launch_file")
    camera_package = LaunchConfiguration("camera_package")
    camera_launch_file = LaunchConfiguration("camera_launch_file")

    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare(lidar_package), "launch", lidar_launch_file]
            )
        ),
        condition=IfCondition(use_lidar),
    )

    laser_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="laser_static_transform",
        output="screen",
        arguments=[
            LaunchConfiguration("laser_x"),
            LaunchConfiguration("laser_y"),
            LaunchConfiguration("laser_z"),
            LaunchConfiguration("laser_yaw"),
            LaunchConfiguration("laser_pitch"),
            LaunchConfiguration("laser_roll"),
            "base_link",
            LaunchConfiguration("laser_frame"),
        ],
        condition=IfCondition(use_lidar),
    )

    camera = IncludeLaunchDescription(
        FrontendLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare(camera_package), "launch", camera_launch_file]
            )
        ),
        condition=IfCondition(use_camera),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_lidar", default_value="true"),
            DeclareLaunchArgument("use_camera", default_value="true"),
            DeclareLaunchArgument("lidar_package", default_value="lslidar_driver"),
            DeclareLaunchArgument("lidar_launch_file", default_value="lsn10p_launch.py"),
            DeclareLaunchArgument("camera_package", default_value="astra_camera"),
            DeclareLaunchArgument("camera_launch_file", default_value="astra.launch.xml"),
            DeclareLaunchArgument("laser_frame", default_value="laser"),
            DeclareLaunchArgument("laser_x", default_value="0.0"),
            DeclareLaunchArgument("laser_y", default_value="0.0"),
            DeclareLaunchArgument("laser_z", default_value="0.18"),
            DeclareLaunchArgument("laser_yaw", default_value="0.0"),
            DeclareLaunchArgument("laser_pitch", default_value="0.0"),
            DeclareLaunchArgument("laser_roll", default_value="0.0"),
            lidar,
            laser_tf,
            camera,
        ]
    )
