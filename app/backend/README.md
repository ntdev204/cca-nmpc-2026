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
updates. Accepted LiDAR scan-matching corrections are fused as gated pose
measurements. The same EKF path is used by the manual map capture tool; the
direct runtime experiment uses the encoder/IMU portion while recording LiDAR.
During straight motion the filter gives more weight to encoder yaw; when gyro Z
reports a turn, it gives more weight to IMU yaw while continuing to use encoder
translation.
The configured yaw-axis sign is applied consistently to turn commands and
angular measurements. EKF covariance and LiDAR update diagnostics are included
in the live state and scan logs.

Motion is ready automatically when STM32 is online; the web client does not
need a separate enable command. Mapping uses a no-ROS 2D SLAM pipeline:
per-scan correlative matching, keyframe pose-graph constraints, nearby
loop-closure detection, robust sparse graph optimization, and occupancy replay
from all retained scans after optimization. Saved runs include
`slam_pose_graph.json`. N10P packet timestamps support packet-level motion
compensation; they do not provide true per-beam deskew.
camera frames are resized and JPEG-encoded for the constrained link. TCP
keep-alive and `TCP_NODELAY` are enabled so short control packets are not held
behind a stale stream frame. Compression is negotiated by the client in the
initial `ping`; clients that do not advertise it continue to receive ordinary
JSON lines.
