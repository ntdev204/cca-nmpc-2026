from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_slam = LaunchConfiguration("use_slam")
    use_nav2 = LaunchConfiguration("use_nav2")
    use_sim_time = LaunchConfiguration("use_sim_time")
    port = LaunchConfiguration("port")
    map_file = LaunchConfiguration("map")
    lidar_package = LaunchConfiguration("lidar_package")
    lidar_launch_file = LaunchConfiguration("lidar_launch_file")
    camera_package = LaunchConfiguration("camera_package")
    camera_launch_file = LaunchConfiguration("camera_launch_file")

    stack = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("cca_bringup"), "launch", "stack.launch.py"]
            )
        ),
        launch_arguments={
            "use_slam": use_slam,
            "use_nav2": use_nav2,
            "use_lidar": "true",
            "use_camera": "true",
            "use_sim_time": use_sim_time,
            "port": port,
            "map": map_file,
            "lidar_package": lidar_package,
            "lidar_launch_file": lidar_launch_file,
            "camera_package": camera_package,
            "camera_launch_file": camera_launch_file,
        }.items(),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_slam", default_value="true"),
            DeclareLaunchArgument("use_nav2", default_value="false"),
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("port", default_value="/dev/rai_controller"),
            DeclareLaunchArgument("map", default_value=""),
            DeclareLaunchArgument("lidar_package", default_value="lslidar_driver"),
            DeclareLaunchArgument(
                "lidar_launch_file", default_value="lslidar_x10_launch.py"
            ),
            DeclareLaunchArgument("camera_package", default_value="astra_camera"),
            DeclareLaunchArgument(
                "camera_launch_file", default_value="astra.launch.xml"
            ),
            stack,
        ]
    )
