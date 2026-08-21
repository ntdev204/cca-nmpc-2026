---
type: hardware-preflight
status: blocked
date: 2026-08-21
capture_source: hardware
middleware: direct_tcp_backend_no_ros
---

# Physical hardware preflight — 2026-08-21

## Scope

This is a passive hardware preflight, not a motion experiment and not scientific
evidence. The robot core remains in `src/`; `app/backend/robot_console.py` is
only the no-ROS communication and monitoring bridge. The laptop app and web
dashboard do not open the sensors directly.

Related knowledge:

- [[01_Governance/status-and-provenance]]
- [[06_Methods/robot-console-architecture]]
- [[06_Methods/final-run-data-package]]
- [[07_Analysis/pr30-entry-preflight-20260813]]
- [[08_Decisions/position-state-control-scope-20260813]]

## Recorded observation

The direct Jetson backend was queried for approximately four seconds with the
robot disarmed and a zero body-velocity command. The raw preflight record is
`experiments/runs/physical-preflight-20260821-1/sensor_preflight.json`; the
runtime binding is in the same run folder as `hardware_runtime.json`.

| Component | Observation | Interpretation |
| --- | --- | --- |
| STM32 | 41 state/telemetry samples; last `vx=0`, `vy=0`, `wz=0`, voltage `23.039 V`, `flag_stop=0` | Transport and zero-command telemetry observed |
| Astra-S | 12 frames, shape `640x480`, last JPEG `10084` bytes | OpenNI2 stream observed |
| N10P | 41 stream messages, all with `0` decoded points | Serial endpoint opened, but no LiDAR measurement packet observed |
| Safety | `armed=false`, command `[0,0,0]` | No motion was requested or observed |

## Decision

The preflight is **blocked for mapping and motion capture** until the N10P
actually emits valid packets. A port marked `online` only confirms that the
serial endpoint opened; it does not confirm a usable scan. Do not create a map,
run a controller trial, or promote this record as a physical experiment until
the point stream is non-empty and the camera calibration, pose engine manifest,
and final-run package contract are available.

## Next check

With the robot stationary, verify N10P power/motor state, USB/serial identity,
and the measured baud/protocol for the supplied unit. Then repeat the same
passive check and require at least one non-empty decoded scan before opening a
fresh experiment run. Existing historical runs remain separate and are not
used as evidence for this preflight.
