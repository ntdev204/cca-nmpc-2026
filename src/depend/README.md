# ROS 2 dependency packages

This directory contains ROS 2 packages required by the robot bringup:

- `astra_camera_ros2/`: Astra camera driver and message package.
- `lidar_ros2/LSlidar/`: LSLiDAR N10P driver and messages.
- `serial_ros2/`: serial transport dependency.

The packages are kept inside the ROS 2 source tree so `colcon` can discover
them. The LDLiDAR variants are retained as optional reference drivers; the
N10P launch uses `lslidar_driver/launch/lsn10p_launch.py` by default. The
Ethernet variant is `lsn10p_net_launch.py`.

Build all packages from a sourced ROS 2 environment when the corresponding
system dependencies and sensor libraries are installed. The canonical robot
entrypoint remains:

```bash
ros2 launch turn_on_robot turn_on_robot.launch.py
```
