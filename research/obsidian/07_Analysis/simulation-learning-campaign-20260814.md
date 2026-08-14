---
type: simulation-learning-analysis
status: candidate-development-only
evidence_status: not-admissible
paper_edit: prohibited
updated_at: 2026-08-14
---

# Simulation learning campaign — 2026-08-14

This is the first learning campaign after the exact reset recorded in
[[07_Analysis/simulation-reset-20260814]]. It is a software-development run;
it is not a hardware experiment, not a confirmatory result and not a paper
claim. The Overleaf manuscript was not opened or built.

## Data generated from scratch

`capture/context.csv` contains 9,600 current-context observations from 40
deterministic simulation episodes at `dt=0.1 s`. Episode groups are frozen into
train, validation, calibration, test-ID and test-OOD partitions with 1,176
usable windows per partition. OOD episodes use a higher speed/noise range; no
future human path is exported and no direction label is used as a training
target. The capture manifest, calibration sidecar and split manifest are
hash-bound under
`experiments/runs/simulation-learning-20260814/`.

## Self-supervised LSTM score loop

The LSTM was initialized from scratch and trained through the existing
next-observed-velocity objective with five independent seeds. Temperature
calibration was fit only on the frozen calibration partition. The model has
1,176 windows in each train/validation/calibration/test-ID/test-OOD partition;
the self-supervised score is `0.837` on test-ID and `0.792` on test-OOD, with a
fitted temperature of `0.426`. The corresponding speed MAE is `0.068`/`0.088`
m/s and direction macro-F1 is `0.914`/`0.783` for ID/OOD. Direction confusion
matrices, reliability and bootstrap intervals are retained in
`model/metrics.json`. This is a stronger simulation split, but it remains
simulation-only and cannot support a real-data or Q1 claim.

## Score/penalty reinforcement loop

The local-path policy was learned with tabular Q-learning, not supervised
labels. The reward combines progress and clearance score, with explicit
penalties for action changes and collision states. The loop stopped after 81
episodes when the rolling score reached `0.859` and plateaued. The selected
development policy uses lateral offset `1.70 m`, longitudinal offset `0.85 m`,
and context radius `0.60 m`. It is a candidate policy only and has not been
validated on the target robot.

## Paired map benchmark

The calibrated simulation checkpoint and RL policy were evaluated on the
Python-built map with five replicates of each of three dynamic-context
scenarios (15 paired units). The global path was held fixed; local path
generation was trigger-only. The benchmark contains
MPC, NMPC, DWA, MPPI and CCA-NMPC with the common six-state position/body-
velocity interface. CCA-NMPC produced zero collisions, a minimum context
margin of `0.2212 m`, and a safe-completion rate of `0.667` in this small
development sample. These descriptive values do not establish superiority,
safety or real-time performance.

## MATLAB position-state development run

The bounded MATLAB position-state comparator was rerun from the clean campaign
under `experiments/runs/matlab-position-learning-20260814/` for MPC, NMPC, DWA,
MPPI and CCA-NMPC across the four declared scenarios (`x`, `y`, `diagonal`,
`yaw`). Its manifest is marked `candidate-development-only`; it is a
position/body-velocity artifact and does not replace the paired Python map
benchmark or a confirmatory campaign. The export records the six-state
definition, source/configuration hashes and `hardwareValidated=false`.

The bounded summary is retained for software comparison only. For example,
the diagonal final-position error is `1.2855 m` for CCA-NMPC and `1.2640 m` for
DWA; these values are descriptive and are not interpreted as superiority. The
MATLAB test harness remains a separate host-software check; passing tests do
not establish experimental validity.

## Integrity replay audit

An independent post-run audit replayed the package hashes and summary counts
without rerunning the controllers. The learning manifest lists 16 tracked
records; its capture/model and nested five-artifact map package were checked,
and the independent final map package contains five hash-matching artifacts
(the manifest is intentionally excluded from its own artifact list). The
final map CSV contains 300 unique paired keys (`10` replicates x `3` scenarios
x `5` controllers), and collision/safe-completion aggregates regenerated
from the raw episode table match the stored summary for every controller.
This is an integrity and reproducibility check only; it does not convert any
candidate output into confirmatory evidence.

## Requirement-bound integrity audit — continuation

A separate read-only replay checked every hash listed by the learning,
development benchmark and MATLAB manifests. It also checked the five completed
LSTM seed records, `self_supervised_score_loop`, the absence of direction labels
from training, `tabular_q_learning_score_penalty`, `training_targets_used=false`,
fixed global-path flags, absence of exported future-human-path fields, the
six-state MATLAB definition, Internet-media flags and the COCO8 preflight
boundary. The audit returned `PASS` for all listed checks. This strengthens
reproducibility and contract integrity only; it does not open the independent,
confirmatory, real-context or hardware gates.

## Independent 30-unit development benchmark — physical-spec rerun

To check stability before any confirmatory gate, the same hash-bound LSTM and
tabular Q-learning policy were evaluated on a separate 10-replicate Python map
run (`30` replicate-by-scenario units) at
`experiments/runs/simulation-benchmark-400mm-20260814/`. The run used
`--no-score-tune`, held the global path fixed and regenerated only the local
path on context conflict or direction change. Its manifest is
`completed-development-map-context`, with `score_tuning_allowed=false` and no
protocol-freeze record. The run is bound to the current user-supplied
`0.400 x 0.400 m` envelope (`footprint_radius_m=0.282843 m`) and the physical
specification hash `fb4a309f...c1b9c06`; independent dimensional and sensor
calibration verification remain open.

Descriptive aggregate values were: MPC `19/30` collisions and safe completion
`0.000`; NMPC `20/30` and `0.333`; DWA `12/30` and `0.600`; MPPI `10/30` and
`0.667`; CCA-NMPC `0/30` and `0.667`, with minimum context margin `0.2194 m`.
The CCA-NMPC mean controller-time P95 was `0.0107 ms`. These are simulated,
candidate-only outputs; they do not establish superiority, safety or real-time
performance. The checkpoint has a simulation calibration sidecar, but no real
capture source or protocol freeze, so this run cannot satisfy the PR20/PR21
confirmatory gate.

## Next gate

Do not promote this campaign to `data/registry.json`, `models/registry.json`,
or the claim register. The next admissible step for a real-data claim is a
frozen direct context capture with the same independent split/calibration
contract and an independent rerun. Hardware remains closed until PR30 H0,
measured geometry, sensor calibration and safety approval are complete.

[[07_Analysis/current-evidence-index]] ·
[[07_Analysis/experimental-analysis]] ·
[[06_Methods/simulation-protocol]] ·
[[06_Methods/statistical-analysis]] ·
[[01_Governance/status-and-provenance]]
