# Robot application surface

The operator surface is isolated from research utilities:

- `backend/` — the no-ROS Jetson service and direct sensor/STM integration.
- `desktop/` — the laptop Tk operator app, which is a client of the backend.
- `web/` — the Next.js 16.3.1 dashboard and its server-side TCP bridge.

The web project is a CLI-generated Next.js application; its reproducible
bootstrap command is recorded in `web/README.md`.

`scripts/python/tools/` is reserved for offline utilities, validators and
recovery tools. It is not the runtime entrypoint for the robot.
