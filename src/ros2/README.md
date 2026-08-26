# ROS 2 runtime

The `cca_control`, `cca_runtime`, `cca_hardware`, `cca_bringup` and
`turn_on_robot` packages are the canonical runtime on the `ros2` branch. The
controller equations remain in `src/control`; ROS 2 owns transport, timing,
lifecycle and sensor integration.

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

`cca_bringup/launch/stack.launch.py` provides optional integration points for
the external ROS 2 packages `slam_toolbox`, Nav2 map services, the LSLiDAR
driver and the Orbbec Astra driver. The launch defaults match the hardware:

```text
LSLiDAR N10P: lslidar_driver/launch/lslidar_x10_launch.py
Astra-S:      astra_camera/launch/astra.launch.xml
```

The driver packages are external ROS 2 dependencies and are intentionally not
copied into this repository. The official LSLiDAR driver documents N10P on the
`LS-S1_V1.0` branch and starts single-line models with `lslidar_x10_launch.py`.
The official Orbbec driver starts Astra with `astra.launch.xml`. Install the
matching driver branch and its udev/USB or Ethernet rules on the Jetson before
enabling the corresponding flag. The sensor flags default to false because the
current Jetson image does not contain these two packages.

`use_slam:=true` starts `slam_toolbox` online asynchronous mapping and consumes
`/scan` plus the `odom -> base_link` transform. `use_nav2:=true` currently
starts only `nav2_map_server` for map serving. It deliberately does not start
a Nav2 controller: CA-NMPC remains the sole publisher that drives the STM, so
there is no competing `/cmd_vel` authority. Full Nav2 planning/controller
bringup can be added later behind a separate arbitration layer.

## Build on the Jetson

```bash
source /opt/ros/humble/setup.bash
mkdir -p ~/cca_ws/src
for package in cca_control cca_runtime cca_hardware cca_bringup turn_on_robot; do
  ln -sfn "$PWD/src/ros2/$package" "$HOME/cca_ws/src/$package"
done
colcon build --symlink-install --packages-select \
  cca_control cca_runtime cca_hardware cca_bringup turn_on_robot \
  --cmake-args -DCMAKE_BUILD_TYPE=Release
source ~/cca_ws/install/setup.bash
ros2 launch turn_on_robot turn_on_robot.launch.py
```

The STM port, controller period and frame names are in `config/params.yaml`.

Enable the complete sensor and mapping stack after installing the external
drivers:

```bash
ros2 launch cca_bringup stack.launch.py \
  use_lidar:=true use_camera:=true use_slam:=true
```

For the normal robot startup, use the dedicated one-command package. It starts
CA-NMPC hardware, N10P, Astra-S and SLAM with the correct defaults:

```bash
ros2 launch turn_on_robot turn_on_robot.launch.py
```

Pass `use_nav2:=true map:=/absolute/path/map.yaml` only when a saved map is
available. The wrapper always enables both sensor drivers; their packages must
be installed in the ROS 2 environment first.

The map can be saved through SLAM Toolbox's `slam_toolbox/save_map` service.
Do not enable Nav2 motion controllers in parallel with CA-NMPC.
