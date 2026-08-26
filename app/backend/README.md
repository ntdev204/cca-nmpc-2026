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
the declared circumscribed robot footprint. Stream messages for state, LiDAR and
map are zlib-compressed and Base64-framed when that is smaller than JSON. State
is emitted at 10 Hz, new LiDAR scans are emitted only when a scan arrives, and
map snapshots are emitted at 2 Hz; unchanged stream items are replaced in the
per-client queue rather than buffered.

Motion is ready automatically when STM32 is online; the web client does not
need a separate enable command. Mapping uses accumulated bounded log-odds
evidence, keeps a trajectory/history record, and uses odometry as the
authoritative pose for map placement so new scans do not overwrite or shift
earlier map layers.
Camera capture remains full-resolution for data collection; the H.264 WebRTC
preview is separate from saved frames. TCP
keep-alive and `TCP_NODELAY` are enabled so short control packets are not held
behind a stale stream frame. Compression is negotiated by the client in the
initial `ping`; clients that do not advertise it continue to receive ordinary
JSON lines.

When `aiortc` and PyAV are available (the Jetson deployment includes both),
port `8766/webrtc/offer` is the primary camera transport. The backend publishes
the live 640x480 Astra-S frames as an H.264 WebRTC video track, and the browser
completes a single SDP offer/answer exchange. The `/mjpeg` endpoint remains a
diagnostic fallback only; camera images are never inserted into the JSON
telemetry stream.

`scan_start` opens a new dataset run under `experiments/runs/`. During a run,
the service records `robot_state.csv`, `control.csv`, `lidar.csv`,
`camera.csv`, `camera/*.jpg`, `depth/*.png`, `context.csv`, `events.csv`,
`map_history.jsonl`, and the occupancy map. `scan_save` closes the run and
writes a recursive SHA-256 manifest for the raw package.
