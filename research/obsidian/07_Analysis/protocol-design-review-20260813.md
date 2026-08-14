---
type: protocol-design-review
status: reviewed-design-only
evidence_status: no-new-evidence
date: 2026-08-13
paper_edit: prohibited
---

# Downstream protocol design review — 2026-08-13

This review checks that the next research protocols are internally executable
and consistent with the completed bounded literature audit. It is a design
review only. It does not freeze a confirmatory holdout, admit a dataset,
certify a checkpoint, promote a simulation, or open physical-robot admission.

## Review matrix

| Protocol | Design check | Result | Evidence boundary |
|---|---|---|---|
| PR11 | causal context schema, recording-level leakage groups, real-frame/calibration contract, no-human-trajectory rule | `PASS` | no permitted real context recording or frozen dataset |
| PR12 | self-supervised next-velocity target, constant/Kalman baselines, five-seed rule, ID/OOD/confusion/calibration/timing metrics, fail-closed checkpoint provenance | `PASS` | no admissible checkpoint or independent test |
| PR20 | S0–S4 separation, fixed global path, local-path trigger only, common-random-number pairing, five-controller comparison and failure denominator | `PASS` | no confirmatory simulation; freeze record still required |
| PR21 | position-state MPC/NMPC, DWA, MPPI and CCA-NMPC fairness ledger; physical clearance and primary estimands separated from exploratory ablations | `PASS` | no independent benchmark or causal result |
| PR30 | direct no-ROS Astra-S/N10P/CAN capture path, strict timestamps, calibration binding and commissioning lock | `PASS` | physical dimensions, calibration, devices and safety approval absent |
| PR40 | ITT-like denominator, paired/clustered uncertainty, multiplicity, classification semantics, qualitative coding and failure taxonomy | `PASS` | no holdout analysis or independent coder |

## Cross-protocol invariants

- The global path is fixed. Only the robot local path may be regenerated after a
  current-context conflict; no human trajectory is generated or stored.
- YOLO26s-pose remains a replaceable perception instrument. LSTM remains a
  context component inside CCA, not a separate controller or novelty claim.
- The physical interface is position-state control with body-velocity commands;
  no torque-input hardware evidence is required. The older torque-input
  simulator remains outside the physical evidence boundary until the simulation
  runner is aligned with the amended state/input contract.
- Software tests and static preflights are QA artifacts. They are not scientific
  outcomes, robot evidence, safety guarantees, or hard-real-time claims.

## Status consequence

The design portions of PR11, PR12, PR20, PR21, PR30 and PR40 may be marked
`REVIEWED`. Their execution/evidence gates remain open. PR02 stays
`PROOF-DRAFT` because an independent proof/geometry review and calibration
obligations are not complete. PR50 stays `DRAFT-DESIGN` until the evidence
release can be populated.

Related: [[07_Analysis/focused-audit-review-20260813]] ·
[[07_Analysis/protocol-status-20260813]] · [[07_Analysis/completion-audit]]
