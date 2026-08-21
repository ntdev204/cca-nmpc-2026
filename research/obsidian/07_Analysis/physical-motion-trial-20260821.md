---
type: hardware-motion-trial
status: candidate-not-evidence
date: 2026-08-21
capture_source: hardware
middleware: direct_tcp_backend_no_ros
---

# Physical motion trial — forward command 0.30 m/s for 1 s

## Run identity

The trial was issued through the no-ROS backend after the sensor preflight
passed. The robot core remained in `src/`; `app/backend/robot_console.py` was
used only as the communication and safety bridge.

- Run: `experiments/runs/app-motion-030-1s-20260821-2/`
- Requested body velocity: `vx=0.30 m/s`, `vy=0`, `wz=0`
- Requested command window: `1.0 s`
- Safety record: `experiments/runs/h0-safety-jetson.json`
- Final state: `armed=false`, command `[0,0,0]`, measured velocity returned to zero

Related knowledge:

- [[07_Analysis/physical-hardware-preflight-20260821]]
- [[06_Methods/robot-console-architecture]]
- [[06_Methods/final-run-data-package]]
- [[08_Decisions/position-state-control-scope-20260813]]

## Observed telemetry

The STM32 telemetry reached a maximum forward velocity of `0.236 m/s`; the
response is a ramp and therefore did not equal the requested command
instantaneously. The run recorded 39 state samples, 38 LiDAR messages and 11
camera messages. This is commissioning data only and is not a paper result.

## Operational findings

1. A `watchdog_zero` event occurred while waiting for the arm acknowledgement.
   The system stayed safe, but the next trial must send the first zero/velocity
   command immediately after arm acknowledgement rather than waiting through
   the watchdog interval.
2. The backend `pose` remained `[0,0,0]` throughout the capture even while
   STM32 velocity was nonzero. The telemetry is therefore usable for this
   velocity/stop check, but the application pose/map update is not yet valid
   evidence of displacement. Mapping trials must fix or explicitly replace
   this pose source before they are interpreted.

No map was started and no paper or manuscript file was modified.
