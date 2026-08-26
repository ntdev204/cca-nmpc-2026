---
domain: problem
type: note
status: locked
scope: theory-only
evidence: scope-contract
tags: [scope, research-question]
---

# Research scope

## Main question

Can a Continuous Context-Aware local-path layer improve human-motion-aware
navigation on a holonomic Mecanum robot while NMPC remains an interpretable
motion controller under fair, reproducible comparisons?

## Scope boundaries

- The global path is fixed during local interactions.
- CCA is the full continuous-context layer and contains LSTM and GA.
- CCA receives the global path, robot state, current context, obstacles, and the
  previous local path when available.
- LSTM estimates causal current human velocity, direction, and confidence at
  every valid observation.
- GA searches geometric local-path candidates.
- The only CCA output is the robot local path.
- Reinforcement learning is excluded from the accepted architecture.
- NMPC time-parameterizes and tracks an admitted path using body-velocity
  commands; a new infeasible reference is not admitted.
- The nominal Lyapunov statement concerns NMPC only.
- No current empirical claim is accepted; all simulation, learning, and
  hardware work is deferred to `IMPLEMENTATION_PLAN.md`.
- The present context model supports direction-aware avoidance, not a claim of
  social compliance, comfort, or interactive human-response modeling.

## Falsifiable hypotheses

- H1: observation-rate LSTM updating improves local-path outcomes over the same
  frozen LSTM updated only at the GA trigger; frozen-LSTM, constant-velocity,
  and no-context GA cells test the value of the estimator and context.
- H2: the current-context LSTM improves downstream local-path outcomes over
  constant-velocity and no-context variants under a matched GA backend.
- H3: full lateral Mecanum motion provides a material secondary benefit over a
  matched $v_y=0$ restriction in human-interaction scenarios.
- H4: the complete hierarchy improves end-to-end navigation over native DWA and
  MPPI under shared system conditions; failure rejects only the system claim.

Terminal-NMPC tracking, reference feasibility, and Lyapunov descent are future
validation obligations for supporting theory, not novelty hypotheses.

## Links

[[cca-nmpc-research]] · [[01_Problem/research-gap]] ·
[[04_Evaluation/baseline-contract]] · [[04_Evaluation/claim-evidence-boundary]]
