---
type: evidence-analysis
status: candidate-not-evidence
evidence_status: hardware-commissioning; encoder-response-confirmed; zero-tail-confirmed
updated_at: 2026-08-14
paper_edit: prohibited
---

# Jetson STM motion run — 0.30 m/s

## Scope

This is a one-second direct C++ STM32 serial commissioning run. LiDAR,
Astra-S, ROS/ROS 2, CCA-NMPC, LSTM, YOLO26s-pose, and map execution were not
used. The run is stored separately from the 0.10 m/s check and is not a Q1
result.

## Run records

- Host: `rai-k63` Jetson, aarch64; `/dev/rai_controller` at 115200 baud.
- Motion package: `experiments/runs/stm-motion-test-030-jetson/`.
- Command: `vx_cmd=0.30 m/s`, `vy_cmd=0`, `wz_cmd=0`, duration 1 s.
- Stop package: `experiments/runs/stm-stop-verification-030-jetson/`, zero-only
  observation for 2 s after the motion command.
- H0 safety record: `experiments/runs/h0-safety-jetson.json`.

## Observed telemetry

The motion package contains 30 valid state rows. The measured forward body
velocity increased through the firmware ramp from approximately `0.076 m/s`
to `0.211 m/s`; the final integrated state was approximately
`x=0.08316 m`, `y=-0.00017 m`, `theta=-0.00396 rad`. All inspected samples had
`flag_stop=0` and supply voltage near `23.52 V`. The event log contains
`serial_open` followed by the probe's normal-exit `zero_command`.

The subsequent zero-only package contains 50 state rows. Its final samples
are exactly zero in `vx`, `vy`, and `omega`, with no serial-write error.

## Interpretation and gate

The run confirms a repeatable higher-speed command response and a clean stop
tail through the Jetson-to-STM path. It remains commissioning evidence:
firmware identity, wheel-geometry calibration, external odometry, and
instrumented displacement measurement are still required before a hardware
result can enter the Q1 evidence set. No manuscript edit is authorized from
this run.

Related knowledge: [[07_Analysis/jetson-stm-actuation-check-20260814]],
[[07_Analysis/current-evidence-index]], [[06_Methods/final-run-data-package]],
[[01_Governance/status-and-provenance]].
