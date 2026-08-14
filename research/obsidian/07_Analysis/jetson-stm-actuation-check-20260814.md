---
type: evidence-analysis
status: candidate-not-evidence
evidence_status: hardware-smoke-test; encoder-actuation-confirmed; physical-displacement-confirmed-by-operator
updated_at: 2026-08-14
paper_edit: prohibited
---

# Jetson STM actuation check — controlled serial motion

## Scope

This check isolates the direct C++ STM32 serial boundary. It does not use
LiDAR, Astra-S, ROS/ROS 2, CCA-NMPC, LSTM, YOLO26s-pose, or a map. It is a
bring-up result, not a Q1 experiment and must not be promoted to the paper.

## Runs

- Host: `rai-k63` Jetson, aarch64; port `/dev/rai_controller` (`ttyACM0`),
  115200 baud.
- Safety: user-confirmed H0 record at
  `experiments/runs/h0-safety-jetson.json`; each motion run was one second
  and the C++ probe sent a zero command on normal exit.
- `experiments/runs/stm-motion-test-010-jetson/`: requested
  `vx_cmd=0.10 m/s`, `vy_cmd=0`, `wz_cmd=0`.
- `experiments/runs/stm-stop-verification-jetson/`: zero-only observation for
  two seconds after the motion command.

## Observed telemetry

The 0.10 m/s run returned valid legacy 24-byte telemetry with `flag_stop=0`
and supply voltage about 23.5 V. The measured body velocity rose from
`0.004 m/s` to `0.053 m/s`; integrated pose reached approximately
`x=0.00737 m`, `y=-0.00032 m`, `theta=-0.00391 rad` in the recorded state
stream. The first samples are consistent with the firmware's velocity ramp.

The following zero-only run recorded a short deceleration tail (ten nonzero
rows) and then zero velocity for the remainder; its normal-exit event is
`zero_command`. No serial-write error or nonzero stop flag was recorded. The
operator additionally confirmed that the chassis moved and responded during
the motion run.

## Interpretation and gate

This establishes the host serial write path, a repeatable nonzero encoder
response, and operator-confirmed chassis motion through the connected STM
device. The confirmation is still a commissioning observation rather than
independent metrology: no external odometry or video observation was captured.
Therefore the status remains `candidate-not-evidence`; firmware identity,
enable-state telemetry, wheel geometry calibration, and an instrumented
displacement check remain open before any Q1 hardware claim. Do not extend
duration or speed from this note without a new H0-approved run and a fresh
output directory.

Related knowledge: [[07_Analysis/stm-control-smoke-test-20260814]],
[[06_Methods/final-run-data-package]], [[07_Analysis/current-evidence-index]],
[[01_Governance/status-and-provenance]].
