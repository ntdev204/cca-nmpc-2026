# Robot runtime source

`src/ros2/` is the canonical runtime on the `ros2` branch. Research simulations
and mathematical verification remain under `simulations/` and are not imported
by the robot runtime.

## Runtime map

- `ros2/`: ROS 2 packages for control, runtime and hardware.
- `ai/`: perception and context interfaces used by the CCA layer.
- `control/`: C++ controller, context scorer and STM serial transport.
- `runtime/`: replayable Python contracts and the six-state Kalman reference.
- `stm/`: existing STM32 firmware and vendor dependencies.

The Python runtime modules are retained for replay and contract tests. They are
not an alternative actuation path on this branch; hardware commands go through
`cca_stm_bridge`.

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
colcon build --symlink-install --packages-select cca_ros2 \
  --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
ros2 launch cca_ros2 cca_runtime.launch.py
```

The STM bridge owns the serial port and sends zero velocity on shutdown or
command timeout. `slam_toolbox` can consume the bridge's odometry TF and the
N10P `/scan` topic without becoming part of the CA-NMPC command path.
