---
type: scope-amendment
status: accepted-for-code-and-protocols
paper_edit: prohibited
date: 2026-08-13
---

# Position-state control scope amendment

The physical experiment uses the six-state vector
`[x,y,theta,vx,vy,omega]` and a body-velocity command. The objective is pose
tracking on the fixed global path with conflict-triggered local robot-path
updates. A torque or current channel is not required for admission, capture, or
the physical claim boundary.

The STM bridge therefore sends `(vx_cmd_mps, vy_cmd_mps, wz_cmd_radps)` and
records the corresponding measured body velocities, integrated pose, IMU and
stop flag. The CSV compatibility names `yaw_rad` and `wz_radps` map to `theta`
and `omega`. The person is dynamic; only CCA-NMPC may keep a causal future-
position prediction internally for chance rows. No predicted human path is
exported or drawn on an image.

This amendment changes code, protocol and Obsidian scope only. The Overleaf
paper remains locked. The older torque-input simulator is not physical evidence
and must not be used to label a hardware result.

The simulation schema now accepts only `body_velocity` with the symbolic
state definition `[x,y,theta,vx,vy,omega]` for a confirmatory configuration.
The MATLAB defaults expose the same position-state/body-velocity contract;
legacy wheel-input routines remain outside the active position study.

Related: [[08_Decisions/decision-register]], [[00_MOC/project-map]],
[[04_Research_Gap/research-gap]], [[05_Theory/system-model]],
[[06_Methods/execution-roadmap]], [[06_Methods/final-run-data-package]],
[[07_Analysis/protocol-status-20260813]],
[PR30 physical experiment](../../../protocols/PR30_physical_experiment.md)
