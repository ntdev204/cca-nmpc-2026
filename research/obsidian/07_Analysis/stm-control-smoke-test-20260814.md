---
type: evidence-analysis
status: candidate-not-evidence
evidence_status: hardware-smoke-test; actuation-unconfirmed
updated_at: 2026-08-14
paper_edit: prohibited
---

# STM control smoke test — Jetson

## Scope

This is a one-second direct-serial smoke test only. It does not use the
LiDAR, camera, ROS, ROS 2, CCA-NMPC, LSTM, or a map, and it is not a paper
result.

## Run record

- Host: `rai-k63` (Jetson, aarch64).
- Transport: C++ `stm_probe` over `/dev/rai_controller` at 115200 baud.
- Command: `vx_cmd=0.02 m/s`, `vy_cmd=0`, `wz_cmd=0` for approximately 1 s,
  followed by the built-in zero command.
- Safety: user-confirmed H0 checks; remote record
  `experiments/runs/h0-safety-jetson.json`.
- Remote run: `experiments/runs/stm-motion-test-jetson/`.
- Process exit: `0`; `events.csv` contains `serial_open` and
  `zero_command` without a serial-write error.

## Observed data

- `control.csv` contains 29 telemetry-aligned rows with the requested
  `vx_cmd_mps=0.02`.
- The recorded applied body velocity is zero in the inspected rows:
  `vx_applied_mps=0`, `vy_applied_mps=0`, `wz_applied_radps=0`.
- `robot_state.csv` reports zero body velocity and pose displacement, with
  `flag_stop=0` and supply voltage near 23.52 V.

## Interpretation and next gate

The host process opened the STM serial port and completed the command loop,
so the host-side write path is operational. The zero applied telemetry does
not prove that the STM drive chain accepted or executed the nonzero command;
possible causes include firmware mode/port mapping, motor-driver enable, a
dead-band, or a mechanical test condition. This run must remain
`candidate-not-evidence`. Do not increase speed or repeat motion until the
STM-side command acknowledgment/applied-velocity path and motor-driver state
are identified. Link this note to a future verified hardware package only
after a repeatable nonzero applied velocity and independent displacement check
are recorded.

Related knowledge: [[06_Methods/final-run-data-package]],
[[07_Analysis/pr30-entry-preflight-20260813]], [[07_Analysis/current-evidence-index]].
