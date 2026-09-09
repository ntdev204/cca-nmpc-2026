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
- `turn_on_robot`: the canonical bringup, separate sensor launch and HTTP/WebRTC bridge launch.
- `rai_runtime_bridge`: ROS 2 node exposing telemetry, map snapshots, control and WebRTC over HTTP.
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
for package in cca_control cca_runtime cca_hardware cca_slam rai_runtime_bridge turn_on_robot; do
  ln -sfn "$PWD/src/$package" "$HOME/cca_ws/src/$package"
done
ln -sfn "$PWD/src/depend" "$HOME/cca_ws/src/depend"
colcon build --symlink-install --packages-select \
  cca_control cca_runtime cca_hardware cca_slam rai_runtime_bridge turn_on_robot \
  --cmake-args -DCMAKE_BUILD_TYPE=Release
source ~/cca_ws/install/setup.bash
ros2 launch turn_on_robot bringup.launch.py
```

The STM bridge owns the serial port and sends zero velocity on shutdown or
command timeout. `turn_on_robot/bringup.launch.py` includes the runtime,
`sensor.launch.py`, SLAM, optional Nav2 map server and `bridge.launch.py`.
The bridge publishes operator velocity commands to `/manual_cmd_vel`; the STM
bridge gives this topic priority over the autonomous controller's `/cmd_vel`
for a short, watchdog-protected interval. It reads `/odometry/raw`, `/scan`,
`/map` and `/camera/color/image_raw`, and has no process manager or raw TCP
protocol. `cca_slam` provides the canonical `map`/`odom`/`base_link` frames;
the static LiDAR transform is owned by `sensor.launch.py`. The
external driver packages under `depend/` are discovered by `colcon` when their
system dependencies and sensor libraries are installed.

The HTTP bridge exposes SLAM map controls through a single launch supervisor:
`POST /api/map/scan/start` and `/api/map/scan/stop` pause or resume new laser
measurements while preserving the active map, `POST /api/map/clear` restarts the
`cca_slam/online_async_launch.py` session with a fresh pose-graph, and
`POST /api/map/save` calls
`/slam_toolbox/save_map`. Maps are saved under
`/home/rai/cca-nmpc-ros2/maps/<name>.yaml` and `<name>.pgm` files. The caller
supplies only the map name; no per-map folder or file extension is needed. An
omitted name uses `map-YYYYMMDD-HHMMSS`; user names are normalized to safe file
names. Clear only affects the active map and leaves saved map files untouched.
previously saved map files untouched.

The N10P launch default is `lsn10p_launch.py`; override it with
`lidar_launch_file:=lsn10p_net_launch.py` for the Ethernet configuration.
