---
domain: research-program
type: note
status: locked
scope: theory-and-manuscript
claim_status: candidate
evidence: doi-audited
tags: [cca-nmpc, human-aware-navigation, mecanum]
---

# CCA-NMPC research program

The study examines a two-layer navigation architecture for a holonomic Mecanum
robot operating near moving people. CCA means **Continuous Context-Aware**:

`global path + continuous context -> CCA [LSTM + GA] -> local path -> NMPC motion control`.

CCA contains the LSTM context estimator and GA path search. It receives the
fixed global path, robot state, current human context, obstacles, and previous
local path, then returns one geometric robot local path. NMPC tracks that path
and is the only block authorized to issue body-velocity commands.

Future CCA simulation is assigned to Python. Future MATLAB/Simulink work is
restricted to the NMPC motion-control layer and its Lyapunov-constrained
closed-loop response. The two environments may meet only through the geometric
local-path contract; neither is executed in the current theory goal.

The proposed contribution is not a claim that LSTM, GA, context-aware planning,
or Mecanum NMPC is new. It is a falsifiable study of continuous context updating
inside fixed-global-path local planning and its downstream effect under matched
evidence.

Until HRI outcomes are measured, “context-aware” is restricted to causal
direction/speed-aware collision avoidance and does not imply social compliance.

## Knowledge graph

- Problem: [[01_Problem/research-scope]] and [[01_Problem/research-gap]]
- Evidence: [[02_Literature/closest-work]],
  [[02_Literature/evidence-synthesis]], and
  [[02_Literature/core-doi-sources]]
- Theory: [[03_Theory/architecture]], [[03_Theory/mathematical-model]],
  [[03_Theory/cca-trajectory-generation]], [[03_Theory/nmpc-motion-control]], and
  [[03_Theory/lyapunov-stability]]
- Evaluation: [[04_Evaluation/baseline-contract]],
  [[04_Evaluation/simulation-design]], and
  [[04_Evaluation/claim-evidence-boundary]]
- Iteration: [[05_Workflow/research-loop]]
