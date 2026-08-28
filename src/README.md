# Robot runtime source

`src/` is the canonical ROS 2 workspace on the `ros2` branch. Research
simulations and mathematical verification remain under `simulations/` and are
not imported by the robot runtime.

## Runtime map

All robot runtime code is now organized as ROS 2 packages directly under `src/`:

- `cca_control`: C++ CCA-NMPC, context scoring and STM transport core.
- `cca_runtime`: local-reference and CA-NMPC nodes.
- `cca_hardware`: STM bridge, odometry, IMU and TF.
- `cca_slam`: the project-owned SLAM Toolbox launch and mapping parameters.
- `cca_bringup`: sensor startup, the main SLAM launch and optional Nav2 map server.
- `turn_on_robot`: one-command startup for the robot and all sensors.
- `depend/`: ROS 2 dependency packages for Astra, LSLiDAR and serial support.

The ROS 2 source tree is the only active robot-code tree. STM32 firmware remains
the manufacturer's hardware image and is not rebuilt by this workspace.

## Authority boundary

```text
/cca/global_path
  -> cca_reference_node: CCA local reference
  -> cca_nmpc_node: CA-NMPC body velocity
  -> cca_stm_bridge: STM wheel interface
```

Perception, LSTM, GA and learned scoring publish context only. They never issue
robot commands. The production state is `[x,y,theta,vx,vy,omega]`; the command
is `[vx_cmd,vy_cmd,omega_cmd]`.

## ROS 2 build

Build from a ROS 2 Humble environment with:

```bash
source /opt/ros/humble/setup.bash
mkdir -p ~/cca_ws/src
for package in cca_control cca_runtime cca_hardware cca_slam cca_bringup turn_on_robot; do
  ln -sfn "$PWD/src/$package" "$HOME/cca_ws/src/$package"
done
ln -sfn "$PWD/src/depend" "$HOME/cca_ws/src/depend"
colcon build --symlink-install --packages-select \
  cca_control cca_runtime cca_hardware cca_slam cca_bringup turn_on_robot \
  --cmake-args -DCMAKE_BUILD_TYPE=Release
source ~/cca_ws/install/setup.bash
ros2 launch turn_on_robot turn_on_robot.launch.py
```

The STM bridge owns the serial port and sends zero velocity on shutdown or
command timeout. `cca_slam` launches the selected `slam_toolbox` node and
provides the canonical `map`/`odom`/`base_link` frames and N10P `/scan` setup;
it does not become part of the CA-NMPC command path. The
external driver packages under `depend/` are discovered by `colcon` when their
system dependencies and sensor libraries are installed.

The N10P launch default is `lsn10p_launch.py`; override it with
`lidar_launch_file:=lsn10p_net_launch.py` for the Ethernet configuration.
