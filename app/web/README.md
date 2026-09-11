# Web operator dashboard

This is a Next.js 16.3.1 App Router dashboard for the FastAPI runtime bridge.
All robot requests go through HTTP REST endpoints on the bridge; the website
does not open a raw socket or use the legacy JSON-lines transport.

From `app/web`:

```powershell
$env:ROBOT_BRIDGE_URL = 'http://100.69.39.18:8000'
npm install
npm run dev
```

Open `http://localhost:3000`. Next.js route handlers proxy telemetry, map,
commands and the WebRTC offer to the Jetson bridge, so the browser only talks
to the local website origin.

The dashboard reads:

- `GET /api/telemetry/current` for odometry, battery and controller telemetry;
- `GET /api/system/components` for runtime/component status;
- `GET /api/map/snapshot` for the ROS occupancy map;
- `GET /api/map/status` plus `POST /api/map/scan/start`, `/api/map/scan/stop`,
  `/api/map/select`, `/api/map/localization/pose`, `/api/map/clear` and
  `/api/map/save` for SLAM/localization map control;
- `POST /api/robot/cmd_vel` for velocity commands;
- `POST /api/robot/nav/goal` and `/api/robot/nav/cancel` for navigation;
- `POST /api/webrtc/offer` for the camera's HTTP SDP exchange.

To navigate, click a point on the live map. The dashboard converts the click
to fixed map-frame coordinates, draws the measured-pose-to-goal line, and fills
the goal form. The operator must still press `Send goal`; that confirmation
publishes the goal through the existing HTTP navigation endpoint. Saved maps
can also accept a goal while the bridge reports an active `map -> odom`
localization transform. Selecting a saved PGM/YAML starts the Nav2 map server
and AMCL localization on the robot, so the saved map can be used directly; the
button remains locked when that transform is unavailable.

The browser-side motion gate starts disabled. Enabling motion is a website
session safety gate; velocity commands then go to the bridge's manual override
channel and the STM bridge prioritizes them over autonomous `/cmd_vel` only
while the short command watchdog is refreshed. Emergency stop sends zero
velocity and disables the website session gate.

The current HTTP bridge exposes the ROS map and runtime components rather than
the old custom scan/saved-map protocol. Dataset controls are shown only when
the bridge role grants the `dataset` action. Camera preview uses the bridge's
WebRTC endpoint; there is no MJPEG or separate camera port fallback.

SLAM is owned by a single supervisor launched from `turn_on_robot/bringup.launch.py`.
Start/Stop pause or resume new laser measurements without losing the active map;
Clear asks the supervisor to restart one fresh SLAM launch session, then Save calls
`/slam_toolbox/save_map`. Saves use the standard Jetson root
`/home/rai/cca-nmpc-ros2/maps/<name>.yaml` and `<name>.pgm`; the UI only accepts
the map name and creates the file names automatically without creating a per-map
folder. Leaving the name empty generates `map-YYYYMMDD-HHMMSS`. Clear never
removes saved map files. The Mapping panel lists valid YAML/PGM pairs from that
root; selecting one loads it into the dashboard and starts AMCL localization.
A
selected saved map can be used for goal dispatch after AMCL publishes the
localization transform. The panel also lets the operator publish an initial
pose in the selected map. Click New scan to stop localization and return to a
fresh live SLAM map. The default initial pose is `(0, 0, 0)` and should be
updated when the robot starts elsewhere.

The `/api/history?kind=state|lidar|map|event&page=1&pageSize=12` route keeps a
bounded in-memory history of the HTTP snapshots for the telemetry view.
