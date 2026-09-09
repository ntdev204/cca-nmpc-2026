from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    port = LaunchConfiguration("port")
    manual_command_topic = LaunchConfiguration("manual_command_topic")
    odom_reset_service = LaunchConfiguration("odom_reset_service")
    params_file = PathJoinSubstitution(
        [FindPackageShare("cca_runtime"), "config", "params.yaml"]
    )
    return LaunchDescription(
        [
            DeclareLaunchArgument("port", default_value="/dev/rai_controller"),
            DeclareLaunchArgument("manual_command_topic", default_value="/manual_cmd_vel"),
            DeclareLaunchArgument("odom_reset_service", default_value="/odometry/reset"),
            Node(
                package="cca_hardware",
                executable="cca_stm_bridge",
                name="cca_stm_bridge",
                output="screen",
                parameters=[
                    params_file,
                    {
                        "port": port,
                        "manual_command_topic": manual_command_topic,
                        "odom_reset_service": odom_reset_service,
                    },
                ],
            ),
            Node(
                package="cca_runtime",
                executable="cca_reference_node",
                name="cca_reference_node",
                output="screen",
                parameters=[params_file],
            ),
            Node(
                package="cca_runtime",
                executable="cca_nmpc_node",
                name="cca_nmpc_node",
                output="screen",
                parameters=[params_file],
            ),
        ]
    )
