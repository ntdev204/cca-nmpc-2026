# Robot application surface

The operator surface is isolated from research utilities:

- `backend/manual_map.py` — an optional no-ROS commissioning utility; it is not
  the dashboard runtime and does not provide a network service.
- `web/` — the Next.js 16.3.1 dashboard and its server-side HTTP bridge client.

The robot runtime and HTTP/WebRTC bridge are ROS 2 packages under `src/`.
`turn_on_robot/bringup.launch.py` starts them together. The old direct socket
console has been removed; the dashboard uses the FastAPI bridge over HTTP and
the bridge uses WebRTC for camera frames.

The web project is a CLI-generated Next.js application; its reproducible
bootstrap command is recorded in `web/README.md`.

`scripts/python/tools/` is reserved for offline utilities, validators and
recovery tools. It is not the runtime entrypoint for the robot.
