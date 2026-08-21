---
type: hardware-protocol
status: ready-for-operator-run
evidence_status: software-validated; hardware-run-pending
updated_at: 2026-08-14
paper_edit: prohibited
---

# Manual teleoperation and LiDAR map capture

## Purpose

The no-ROS commissioning path lets the operator drive the Mecanum robot by
keyboard while the N10P LiDAR is streamed. STM body-velocity telemetry is
integrated into a local pose, and each complete scan updates a two-dimensional
occupancy grid. The run is saved as CSV, JSON, PGM, and YAML artifacts for
later reconstruction. It is not a Q1 result and does not modify the locked
paper.

## Entry point

`python3 -B scripts/python/tools/manual_map.py` uses
`/dev/rai_controller` at `115200` and `/dev/rai_lidar` at `460800` by default.
The C++ STM transport is selected automatically when its shared library is
available. The default LiDAR mount is `x=0.10 m`, `y=0`, yaw `0` relative to
the robot body; these values must be replaced if the measured mount is
different.

Keyboard commands are `w/s/a/d` or arrows for planar motion, `q/e` for yaw,
`x` or space for zero velocity, and Escape to stop and save. The watchdog
sends a zero command when no command key is received within the timeout.

## Output and interpretation

Each run contains `map.json` (validated occupancy values `-1/0/100`),
`map.pgm`, `map.yaml`, `lidar.csv`, `robot_state.csv`, `control.csv`,
`context.csv`, `events.csv`, and `manifest.json`. The map uses STM telemetry as
an odometry prediction, then applies a bounded correlative scan-to-map
correction when the prior occupancy grid has enough returns. It does not
maintain a pose graph, perform global relocalisation or loop closure, or
publish through a ROS map server. Each map artifact records the matcher
method, attempts, accepted corrections, inlier score and last correction, so
drift and mount-angle errors must still be checked before the map is used for
controller experiments.

The decoder/grid path passed a local self-test on 2026-08-14. A real map run
still requires a clear emergency-stop area, measured LiDAR extrinsics, and an
operator review of the saved PGM/JSON. Hardware evidence remains separate from
the paper evidence gate.

Related knowledge: [[07_Analysis/jetson-lidar-connection-20260814]],
[[07_Analysis/current-evidence-index]], [[06_Methods/final-run-data-package]],
[[01_Governance/status-and-provenance]].
