---
type: research-roadmap
status: research-gates-in-progress
evidence_status: knowledge-only
---

# Research implementation roadmap

This is a dependency map, not an execution log or result record.

## Fixed architecture

```text
Astra S RGB-D + N10P LiDAR
  -> YOLO26s-pose measurement
  -> short-history position/speed/direction context
  -> self-supervised score-trained LSTM inside CCA
  -> dynamic context snapshots and CCA-only internal future-position prediction
     (not exported to the image)
  -> conflict-triggered local-path regeneration
  -> fixed-budget CCA allocation
  -> position-state Mecanum CCA-NMPC with body-velocity command
```

The global path is never replanned. Perception does not draw a human path on an
image. CCA-NMPC may use an internal future-position sequence for chance rows;
the robot local path exists on the map.

## Dependency order

| Phase | Knowledge to settle before implementation |
|---|---|
| K0 | research question, notation, coordinate frames, and claim boundary |
| K1 | focused Zotero/Obsidian audit of closest primary sources; no SLR/database export |
| K2 | pose/context/LSTM contracts and missingness semantics |
| K3 | fixed map, local-path trigger, controller baselines, and safety limits |
| K4 | metrics, paired units, failure denominator, and statistical model |
| K5 | hardware calibration and stop-rule design |

The bounded focused audit is complete for this original research paper;
PR01-SLR is historical provenance only. K0--K4 have passed design review, but
they still require freeze records and evidence-specific gates before an artifact
can enter the claim ledger. Development code and candidate data remain outside
the claim ledger. K5 is required before any physical trial.

## Research-gate checkpoint — 2026-08-13

PR00 is `REVIEWED` after the bounded literature/claim review. PR11, PR12,
PR20, PR21, PR30 and PR40 are `REVIEWED` for design only. PR02 remains a
proof-draft; PR10 has a mechanical pass but blocked admission; no real context
dataset, LSTM checkpoint, confirmatory simulation or physical package is
admitted. The next executable research gate is to acquire permitted real
context records and freeze PR11/PR12 before any robot trial.

## Direct-runtime checkpoint — 2026-08-13

K5 implementation has begun with the no-ROS recorder in
`src/hardware.py` and `scripts/python/tools/record_hardware.py`.
The code path binds Astra-S/OpenNI2, the explicitly declared N10P serial
profile, the STM32 serial bridge or optional CCA CAN, and the YOLO26s-pose
engine into direct CSV/JSON output. A frozen LSTM checkpoint is optional for
the first context-only capture and becomes required only when LSTM context is
enabled.
The STM32 bridge reproduces the legacy body-velocity command/telemetry frames,
and the mini-Mecanum URDF is checked for wheel spans before capture. The physical
state contract is `[x,y,theta,vx,vy,omega]`; the low-level interface is body
velocity and does not require torque/current feedback.
The hardware template still has unresolved port, firmware, calibration and
Mecanum dimensions, N10P baud and protocol profile; consequently this checkpoint is code QA only and does not
open a physical trial or promote a result. The recorder remains an integration
scaffold while the research gates above are completed.

The active recorder path is `src/hardware.py`; references to the former
`src/python/cca_hardware.py` path in historical audit entries are provenance
only and are not executable entry points.

The current physical-spec input is `configs/physical_robot.json`: total
footprint 0.4 m by 0.4 m, interpreted wheel radius 0.05 m, LiDAR height
0.24 m, camera height 0.20 m, LiDAR front-edge offset 0.10 m, camera
front-edge offset 0.035 m, and downward camera pitch 20 degrees. Its hash is
checked by the map contract and runtime-preparation path; independent
commissioning verification is still required.

## MATLAB interface checkpoint — 2026-08-14

The default MATLAB study path now exports the active position-state/body-
velocity contract without invoking compatibility torque studies. Bounded
exports are development packages only and contain a summary table, per-
controller/scenario six-state CSVs and a source/configuration-hashed manifest.
The compatibility exporter is opt-in and is excluded from the physical
position-state evidence path. This step is complete at the host-regression
level; it does not satisfy simulation, calibration or hardware gates.

Related: [[04_Research_Gap/research-gap]], [[06_Methods/dataset-protocol]],
[[06_Methods/perception-protocol]], [[06_Methods/lstm-protocol]],
[[06_Methods/simulation-protocol]], [[06_Methods/evaluation-protocol]],
[[06_Methods/final-run-data-package]], [[08_Decisions/decision-register]].

Related hub: [[00_MOC/project-map]]

## Low-level implementation split — 2026-08-14

The implementation boundary is intentionally mixed-language. C++ owns fixed
wire contracts and deterministic transport: STM32 11-byte commands, 24-byte
telemetry, stop-safe zeroing, C ABI access and CCA CAN CRC/frame parsing.
Python owns vendor SDK integration and research logic: Astra-S/OpenNI2, N10P,
YOLO26s-pose, self-supervised LSTM, CCA-NMPC, calibration and CSV/JSON
provenance. A C++ Release build and CTest pass in Ubuntu 22.04 WSL; this is
software/interface evidence only. The target still requires C++ build, H0
approval and a real device capture before hardware claims.
