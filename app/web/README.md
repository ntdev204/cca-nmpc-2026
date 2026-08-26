# Web operator dashboard

This is a Next.js 16.3.1 App Router dashboard. It polls the Next.js route
handlers, which bridge to the no-ROS TCP backend on Jetson. The interface uses
the CLI-installed shadcn/ui base-nova components with a light, cold-blue theme.

The project was bootstrapped with the official CLI:

```powershell
npx create-next-app@latest app/web --ts --eslint --app --empty --use-npm `
  --import-alias "@/*" --disable-git --yes
```

```powershell
$env:ROBOT_HOST = '100.69.39.18'
$env:ROBOT_PORT = '8765'
$env:ROBOT_CAMERA_PORT = '8766'
$env:NEXT_PUBLIC_ROBOT_WEBRTC_URL = 'http://100.69.39.18:8766/webrtc/offer'
npm install
npm run dev
```

Open `http://localhost:3000`. The web dashboard is the single operator client.
Its server-side bridge keeps one persistent TCP connection to the Jetson, so
status polling and control requests cannot race to occupy the backend's
single-client slot. It decodes compressed state/LiDAR/map frames losslessly and
uses a JSON-bigint parser so nanosecond timestamps are not rounded before the
data reaches the UI.

The browser receives state and new LiDAR scans at the monitoring rate; map
updates are published at 2 Hz while the full-resolution map remains on the
Jetson. Camera bytes never enter the JSON control stream, which keeps the 4G/
EDGE path bounded without changing saved measurements.

When the robot bridge is online the service starts in the motion-ready state.
The map view uses the odometry pose as the shared robot/map pose, displays
accumulated log-odds occupancy and scan-history trajectory, and intentionally
does not expose TF or sensor-frame controls. The Astra-S panel is placed beside
the fixed map for synchronized monitoring. The dashboard also includes a
standalone polar LiDAR view, continuous keyboard control (`W/S/A/D`, arrows,
`Q/E`), watchdog-safe stop handling, map reload, and a dataset capture panel.
Simultaneous keys are combined: W+D commands diagonal motion and W+Q commands
forward motion with a left turn. `Start capture` and `Save dataset` create a
Jetson-side run containing state, commands, LiDAR scans, RGB/depth frames, map
history and a recursive hash manifest; the run identifier and live sample
counts remain visible in the dashboard for provenance.

The Jetson serves the live Astra-S camera through a WebRTC offer endpoint at
`8766/webrtc/offer`, separate from the control/telemetry port `8765`. The FE
creates a receive-only `RTCPeerConnection`, exchanges one SDP offer/answer, and
renders the H.264 track in a muted `<video>` element. No camera bytes enter
JSON, Base64, or the Next.js polling path. The negotiated camera frame is
640x480; status metadata carries only timing and transport state. The old raw
MJPEG endpoint remains at `/mjpeg` as a diagnostic fallback during deployment.
