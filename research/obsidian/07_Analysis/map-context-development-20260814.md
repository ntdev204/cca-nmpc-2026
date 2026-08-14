---
type: evidence-analysis
status: candidate-development-only
evidence_status: no-ground-truth-human-path
run_id: run-map-context-development-20260814
paper_edit: prohibited
updated_at: 2026-08-14
---

# Dynamic-map context pilot — 2026-08-14

This note records a reproducible development pilot after the reference-layout
adapter was corrected. It is not a confirmatory result and it must not be
promoted to the manuscript or the claim register.

## Scope

The Python map is generated for three context-change scenarios with three
replicates per scenario. The global path is held fixed; a local path is
regenerated only after a context conflict or direction-change trigger. The
person is represented only by current context (position, speed and direction).
No future human trajectory is exported, passed to the controller, or drawn on
an image. The CCA branch predicts internally through the causal context
interface.

The pilot uses a direct direction/speed adapter because no sealed LSTM
checkpoint and calibration sidecar are available. Thus `lstm_inside_cca=false`;
the artifact is not LSTM evidence, unsupervised-learning evidence, or hardware
evidence.

## Aggregate diagnostic values

| Controller | Collision episodes / 9 | Safe completion / 9 | Minimum margin (m) | Progress | Compute P95 (ms) |
|---|---:|---:|---:|---:|---:|
| MPC | 3 | 0 | -0.4717 | 0.5686 | 0.0032 |
| NMPC | 3 | 3 | -0.2217 | 0.8932 | 0.0027 |
| DWA | 5 | 3 | -0.5283 | 0.9034 | 0.1033 |
| MPPI | 5 | 3 | -0.3092 | 0.9270 | 0.1067 |
| CCA-NMPC | 0 | 3 | 0.2120 | 0.8584 | 0.0040 |

These values are descriptive diagnostics from a small tuned pilot. They do not
establish superiority, safety, real-time performance, generalisation, or a
validated CCA/LSTM contribution. The score loop stopped at a plateau with best
score `0.1675` below target `0.85`; no training targets were used and no direct
command policy was learned.

## Provenance and limitations

The package is
`experiments/runs/map-context-development-20260814/`. Its manifest records
`campaign=pilot`, `replicates=3`, `score_tuning_allowed=true`,
`global_path_replan_count=0`, `human_trajectory_generated=false`, and
`human_trajectory_provided_to_controller=false`.

Artifact SHA-256 values are:

- `manifest.json`: `D13BA2C6F6BFFE5A386673C41E7F46B4BFDE1A2C76ADF7B5B78DBCB9192431EA`
- `episode_metrics.csv`: `122980A51D82A485A5C922E2A79CED62CA49D85D45FD84FDB2196984D68A7E28`
- `time_series.csv`: `93FC93B3375A797019C354FA5E10497330FD4F3335A16267E0B2078696C438D8`
- `summary.json`: `ECA3F016E940F92FC5BBFA48E528F90C8F19311493EBA98731BE8948E0BAB6CB`
- `score_tuning.json`: `4339DC10DECDAE92CCC30F51975AAF31088D1C5DC2F11FF5A8B754A3770F259B`
- `map_traces.png`: `24A457AF1313E95B5E8A92C93A0099543ECA1EF846D67DF4E27A0F1696B9ADD1`

An earlier run at the same output name was invalidated because the Python
adapter flattened the controller reference in the wrong memory order. It was
deleted before the corrected rerun and is not evidence. The regression test
`test_compiled_controller_reads_state_major_reference_correctly` now protects
the interleaved six-state reference contract.

## Acceptance boundary

The next admissible run requires a frozen protocol, at least 30 paired
replicates, a sealed direct context CSV, a fitted self-supervised LSTM and
calibration sidecar, independent review, and then hardware validation. Until
those gates are met, this note remains development-only.

[[07_Analysis/current-evidence-index]] · [[07_Analysis/experimental-analysis]] ·
[[06_Methods/evaluation-protocol]] · [[06_Methods/lstm-protocol]] ·
[[01_Governance/status-and-provenance]]
