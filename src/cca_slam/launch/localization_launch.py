from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode, Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    map_yaml = LaunchConfiguration("map_yaml")

    map_server = LifecycleNode(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        namespace="",
        output="screen",
        parameters=[
            {
                "yaml_filename": map_yaml,
                "use_sim_time": use_sim_time,
            }
        ],
    )

    amcl = LifecycleNode(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        namespace="",
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "alpha1": 0.2,
                "alpha2": 0.2,
                "alpha3": 0.2,
                "alpha4": 0.2,
                "alpha5": 0.2,
                "base_frame_id": "base_link",
                "beam_skip_distance": 0.5,
                "beam_skip_error_threshold": 0.9,
                "beam_skip_threshold": 0.3,
                "do_beamskip": False,
                "global_frame_id": "map",
                "lambda_short": 0.1,
                "laser_likelihood_max_dist": 2.0,
                "laser_max_range": 12.0,
                "laser_min_range": 0.21,
                "laser_model_type": "likelihood_field",
                "max_beams": 120,
                "max_particles": 2000,
                "min_particles": 300,
                "odom_frame_id": "odom",
                "pf_err": 0.05,
                "pf_z": 0.99,
                "recovery_alpha_fast": 0.0,
                "recovery_alpha_slow": 0.0,
                "resample_interval": 1,
                "robot_model_type": "nav2_amcl::OmniMotionModel",
                "scan_topic": "/scan",
                "save_pose_rate": 0.5,
                "set_initial_pose": True,
                "sigma_hit": 0.2,
                "tf_broadcast": True,
                "transform_tolerance": 0.2,
                "update_min_a": 0.05,
                "update_min_d": 0.05,
                "z_hit": 0.5,
                "z_max": 0.05,
                "z_rand": 0.5,
                "z_short": 0.05,
                "initial_pose.x": 0.0,
                "initial_pose.y": 0.0,
                "initial_pose.z": 0.0,
                "initial_pose.yaw": 0.0,
            }
        ],
    )

    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_localization",
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "autostart": True,
                "node_names": ["map_server", "amcl"],
                "bond_timeout": 4.0,
            }
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("map_yaml"),
            map_server,
            amcl,
            lifecycle_manager,
        ]
    )
