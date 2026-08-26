# ROS 2 runtime

The `cca_control`, `cca_runtime` and `cca_hardware` packages are the canonical
runtime on the `ros2` branch. The controller equations remain in `src/control`;
ROS 2 only owns transport, timing, lifecycle and sensor integration.

## Runtime chain

```text
/cca/global_path -> cca_reference_node -> /cca/local_reference
/odometry/filtered + /cca/local_reference + /cca/context
    -> cca_nmpc_node -> /cmd_vel
/cmd_vel -> cca_stm_bridge -> STM32 -> /odometry/filtered, /imu/data
```

`cca_nmpc_node` is the only node that generates the body-velocity command.
The reference node never writes to the hardware. The STM bridge has a command
watchdog and sends zero velocity when a command becomes stale.

The production state is `[x, y, theta, vx, vy, omega]`. Odometry carries the
pose and body velocity using `nav_msgs/Odometry`. A local reference is a
`nav_msgs/Path` with at least two poses; the node reconstructs the six-state
reference samples. Context prediction uses a `std_msgs/Float64MultiArray`
with this fixed layout for horizon `H`:

```text
human_mean(2H), context(H), covariance(4H), nominal_robot(2H)
```

The runtime path does not require ROS 2 to change the CCA-NMPC mathematics.
Simulation files remain under `simulations/` and are not built by this package.

## Build on the Jetson

```bash
source /opt/ros/humble/setup.bash
mkdir -p ~/cca_ws/src
for package in cca_control cca_runtime cca_hardware; do
  ln -sfn "$PWD/src/ros2/$package" "$HOME/cca_ws/src/$package"
done
colcon build --symlink-install --packages-select cca_control cca_runtime cca_hardware \
  --cmake-args -DCMAKE_BUILD_TYPE=Release
source ~/cca_ws/install/setup.bash
ros2 launch cca_runtime cca_runtime.launch.py
```

The STM port, controller period and frame names are in `config/params.yaml`.
Start `slam_toolbox` separately when mapping is required; it consumes `/scan`
and the odometry TF and is not part of the CA-NMPC command path.
