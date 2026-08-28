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
    use_slam = LaunchConfiguration("use_slam")
    use_nav2 = LaunchConfiguration("use_nav2")
    use_lidar = LaunchConfiguration("use_lidar")
    use_camera = LaunchConfiguration("use_camera")
    use_sim_time = LaunchConfiguration("use_sim_time")
    port = LaunchConfiguration("port")
    lidar_package = LaunchConfiguration("lidar_package")
    lidar_launch_file = LaunchConfiguration("lidar_launch_file")
    camera_package = LaunchConfiguration("camera_package")
    camera_launch_file = LaunchConfiguration("camera_launch_file")
    map_file = LaunchConfiguration("map")
    slam_launch_file = LaunchConfiguration("slam_launch_file")
    runtime_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("cca_runtime"), "launch", "cca_runtime.launch.py"]
            )
        ),
        launch_arguments={"port": port}.items(),
    )
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("cca_slam"), "launch", slam_launch_file]
            )
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
        }.items(),
        condition=IfCondition(use_slam),
    )
    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[{"yaml_filename": map_file, "use_sim_time": use_sim_time}],
        condition=IfCondition(use_nav2),
    )
    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare(lidar_package), "launch", lidar_launch_file]
            )
        ),
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
            DeclareLaunchArgument("use_slam", default_value="false"),
            DeclareLaunchArgument("slam_launch_file", default_value="online_async_launch.py"),
            DeclareLaunchArgument("use_nav2", default_value="false"),
            DeclareLaunchArgument("use_lidar", default_value="false"),
            DeclareLaunchArgument("use_camera", default_value="false"),
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("port", default_value="/dev/rai_controller"),
            DeclareLaunchArgument("map", default_value=""),
            DeclareLaunchArgument("lidar_package", default_value="lslidar_driver"),
            DeclareLaunchArgument(
                "lidar_launch_file", default_value="lsn10p_launch.py"
            ),
            DeclareLaunchArgument("camera_package", default_value="astra_camera"),
            DeclareLaunchArgument(
                "camera_launch_file", default_value="astra.launch.xml"
            ),
            runtime_launch,
            lidar,
            camera,
            slam_launch,
            map_server,
        ]
    )
