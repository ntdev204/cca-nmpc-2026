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
used to place the latest scan (`map_pose`). Stream messages for state, LiDAR and
map are zlib-compressed and Base64-framed when that is smaller than JSON;
camera frames are resized and JPEG-encoded for the constrained link. TCP
keep-alive and `TCP_NODELAY` are enabled so short control packets are not held
behind a stale stream frame. Compression is negotiated by the client in the
initial `ping`; clients that do not advertise it continue to receive ordinary
JSON lines.
