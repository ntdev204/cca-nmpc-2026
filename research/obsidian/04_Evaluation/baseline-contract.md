---
domain: evaluation
type: note
status: planned
scope: outside-current-theory-goal
evidence: implementation-plan-only
tags: [baseline, fairness, reproducibility]
---

# Matched baseline contract

A method may be compared only within a layer where inputs, outputs, plant, and
decision authority are aligned. Published values from different robots, maps,
predictors, or compute platforms are literature context, not quantitative
baselines.

## Layer-wise comparison

| Layer | Future matched methods | Fixed interface | Permitted claim |
|---|---|---|---|
| Current-context estimation | constant velocity, Kalman-CV, LSTM | identical causal history; output position, speed, direction, confidence, and age | estimation only |
| CCA local-path generation | G0, GCV, GLT, proposed P | identical fixed global path, GA representation, feasibility tests, search budget, and NMPC backend | value of context/update rate |
| Motion control | linear MPC, nominal NMPC, terminal NMPC | identical time-indexed reference, six-state plant, horizon, and constraints | tracking/feasibility only |
| End-to-end navigation | native DWA, MPPI, MPC/NMPC pipelines | identical environment, observations, footprint, command limits, and tuning allowance | system-level outcomes only |

The primary CCA contrast is P versus GLT: both use the same fixed-weight LSTM
and GA, but P updates recurrent context at every valid observation whereas GLT
updates it only at planning events. P versus GCV tests the learned current-state
estimator; P versus G0 tests whether the registered context is useful. None of
these contrasts is currently executed.

Native DWA and MPPI retain command authority and therefore cannot isolate a CCA
local-path effect. The established DWA--MPC hierarchy
([Wang et al.](https://doi.org/10.3390/s25072014)) is the closest interface-level
system comparator. Omnidirectional local planning
([Kobayashi et al.](https://doi.org/10.1007/s12369-021-00791-9)) and Social
Elastic Band
([Perez et al.](https://doi.org/10.1007/s12369-024-01135-z)) are closer
local-generator comparators.

## Shared rules

Matched methods must share the causal observation stream, map, fixed global
path, start and goal, Mecanum model and footprint, constraints, initialization,
failure denominator, and paired scenario realization. Algorithm-specific
decision variables may differ, but tuning effort and compute allowances must be
registered before confirmatory execution. Empty feasible sets, timeouts,
collisions, and incomplete episodes remain in the denominator.

The value of lateral Mecanum motion is a secondary hypothesis and requires a
matched full-holonomic versus $v_y=0$ ablation. Dataset splits, sample sizes,
seeds, metrics, statistical families, timing budgets, and repair ablations are
specified only in `IMPLEMENTATION_PLAN.md` before execution.

## Links

[[01_Problem/research-gap]] · [[03_Theory/cca-trajectory-generation]] ·
[[03_Theory/nmpc-motion-control]] · [[04_Evaluation/simulation-design]] ·
[[04_Evaluation/claim-evidence-boundary]]
