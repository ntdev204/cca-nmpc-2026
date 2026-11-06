# Robot backend

`robot_console.py` is the no-ROS Jetson service. It owns the direct STM32,
N10P and Astra-S interfaces and exposes the existing JSON-lines TCP protocol on
port `8765`. The laptop operator and the web dashboard are clients; they do not
open the hardware devices directly.

Run on Jetson:

```bash
PYTHONPATH=src:app python3 -B app/backend/robot_console.py --server --bind 0.0.0.0 --port 8765
```

The backend sends both the live odometry pose (`pose`) and the map-frame pose
used to place the latest scan (`map_pose`). State messages also carry the
monitoring-only `tf` tree (`map -> odom -> base_link -> laser/camera_link`) and
the declared circumscribed robot footprint. Stream messages for state, LiDAR
and map are zlib-compressed and Base64-framed when that is smaller than JSON;

Pose estimation uses the shared six-state EKF: STM32 body velocity (wheel
odometry) and IMU planar acceleration/gyro drive the prediction and velocity
updates. The console applies accepted LiDAR scan matches to the map-to-odom
transform. The standalone manual capture tool can feed scan matches into its
EKF as pose measurements.
During straight motion the filter gives more weight to encoder yaw; when gyro Z
reports a turn, it gives more weight to IMU yaw while continuing to use encoder
translation.
Actuator yaw-command sign and sensor yaw-measurement sign are configured
separately so a motor-direction correction cannot reverse the map heading.
EKF covariance and LiDAR update diagnostics are included in the live state and
scan logs.

The operator enables motion from the console. Local SLAM uses correlative
search followed by continuous refinement on a smoothed grid. It limits
correction along poorly observed directions and holds occupancy writes when
scan matching is unreliable. Closed submaps provide independent references for
loop closure. Graph optimization and occupancy replay run on a background
snapshot, with any pending optimization handled when saving.

The console estimates beam times from scan angle and the measured revolution
period. It interpolates EKF history for those times and falls back to packet
timing and constant twist when history is insufficient. Pose publication
targets 20 Hz and map publication targets 3 Hz. Fusion defaults to 5 Hz.
The optional top-level `slam_fusion_hz` in `configs/physical_robot.json` is
bounded to 3–10 Hz. Increase it only after checking scan age, queue depth and
end-to-end latency on the target Jetson.

To estimate the optional top-level `lidar_time_offset_s`, record two separate
runs with the robot stationary at first, then turning in place near fixed
walls. Run the calibration tool from the repository root:

```bash
python3 scripts/python/tools/calibrate_lidar_time_offset.py RUN --validation INDEPENDENT_RUN
```

The tool reports errors for candidate offsets on the calibration run and
compares the selected offset with zero on the independent run. Apply an offset
only if it improves the independent result. A positive offset means the LiDAR
timestamp is later than the estimated acquisition time.

Camera frames are resized and JPEG-encoded for the constrained link. TCP
keep-alive and `TCP_NODELAY` are enabled so short control packets are not held
behind a stale stream frame. Compression is negotiated by the client in the
initial `ping`; clients that do not advertise it continue to receive ordinary
JSON lines.
