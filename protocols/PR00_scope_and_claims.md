# PR00 — Research scope and claim contract

**Status:** `FROZEN — THEORY ONLY`
**Version:** 4.0
**Date:** 2026-08-23

## 1. Fixed scope

The study concerns position-state control of a Mecanum robot among moving
people. Its active architecture is

```text
fixed global path
  + robot state + current context + obstacles
  -> CCA (Continuous Context-Aware: LSTM + GA)
  -> robot local path
  -> terminal NMPC motion control
```

The state and command are

$$
X=[x,y,\theta,v_x,v_y,\omega]^T,
\qquad
u=[v_x^{cmd},v_y^{cmd},\omega^{cmd}]^T.
$$

GA is the only active search mechanism. Reinforcement learning, torque control,
identity recognition, global-path replanning, and a new low-level controller are
outside scope. Human motion is used internally as context; CCA generates only
the robot local path.

## 2. Research questions

- **RQ1 — context utility:** Does the registered causal current-context estimator
  improve speed and coarse-direction estimates over matched constant-velocity
  and Kalman baselines, and does any gain survive downstream evaluation?
- **RQ2 — continuous-update mechanism:** With the same fixed-weight LSTM, GA,
  observations, planning events, and local-path contract, does updating recurrent
  context at every valid observation improve local-path generation over updating
  it only when a planning event occurs?
- **RQ3 — motion control:** Under the stated nominal assumptions, does terminal
  NMPC preserve feasibility and local asymptotic tracking for an admitted
  reference, and how does it compare with matched linear MPC and nominal NMPC?
- **RQ4 — system effect:** Under identical maps, paths, observations, limits,
  scenarios, and compute budget, how does CCA-NMPC compare with DWA, MPPI,
  linear MPC, and nominal NMPC on navigation and latency outcomes?

## 3. Candidate contribution

No novelty is claimed for LSTM, GA, NMPC, reference governors, deterministic
repair, homotopy, or planner/controller separation individually. PathFG already
combines planning, a feasibility governor, and NMPC.

The candidate technical contribution is restricted to the continuous
context-to-Mecanum-local-path mechanism and its measured downstream effect. The
terminal-NMPC construction is standard control
theory adapted transparently to the accepted six-state model; it supports the
system study but is not claimed as a new theorem family.

## 4. Candidate hypotheses and rejection rules

- **H1 — continuous-update effect:** The observation-rate cell P improves at
  least one preregistered local-path or downstream endpoint over GLT, which uses
  the same frozen LSTM and GA but updates recurrent state only at planning
  events.
- **H2 — context value:** P is evaluated against GCV and G0 to separate the
  learned current-context estimator from constant-velocity and no-context
  alternatives.
- **H3 — nominal motion control:** For one admitted dynamically feasible
  reference and its shifts, the terminal-NMPC sequence remains feasible and its
  value decreases under the exact assumptions in PR02.
- **H4 — system and embodiment effects:** End-to-end comparisons and the value
  of lateral Mecanum motion are secondary empirical hypotheses.

Exact endpoints, effect thresholds, sample size, seeds, timing budgets,
multiplicity correction, decoder/repair ablations, and rejection rules are
future preregistration items in `IMPLEMENTATION_PLAN.md`. Failure of H1 rejects
the candidate CCA contribution but does not invalidate the architecture or the
conditional NMPC theorem. Deterministic repair is not the primary contribution.

## 5. Claim ledger

| ID | Permitted claim | Minimum evidence | Current status |
|---|---|---|---|
| GAP-01 | A focused DOI audit supports a bounded, falsifiable question | closest-work matrix and Q1 gap review | theory boundary locked; benefit candidate |
| T-01 | The six-state nominal Mecanum model is defined coherently | equation and notation review | theory locked |
| T-02 | Terminal NMPC has conditional nominal recursive feasibility and tracking convergence | analytic proof and independent theory review | theory locked |
| CCA-01 | CCA updates recurrent context independently of planning events and outputs only a robot local path | architecture and CCA equation review | theory locked; effect candidate |
| G-01 | Observation-rate updating improves local-path generation over trigger-rate updating | future matched P--GLT study | not tested |
| G-02 | CCA-GA improves downstream navigation | frozen paired end-to-end runs | not tested |
| S-01 | Full CCA-NMPC outperforms named navigation baselines | matched DWA/MPPI/MPC/NMPC benchmark | not tested |
| RT-01 | A component meets its computation deadline | target-device p50/p95/p99/max and miss rate | not tested |
| HW-01 | The method is effective on the physical robot | registered repeated hardware trials | paused |

No aggregate "overall superiority" score is permitted. Prediction, generation,
tracking, navigation, computation, and hardware outcomes remain separate.

## 6. Evidence and language limits

- A focused search supports only "the focused DOI audit did not identify"; it
  does not support "first" or universal priority.
- The locked formulation does not prove that a future numerical solver will
  return a feasible witness for every state.
- Lyapunov tracking is not collision safety.
- Mean solve time is not real-time evidence.
- Historical parity or Simulink smoke tests are not evidence for this
  theory-only freeze.
- Development runs cannot be reported as confirmatory results.

## 7. Freeze gate

PR00 is `FROZEN — THEORY ONLY` when:

1. the focused DOI boundary and component-level prior-art exclusions are locked;
2. the CCA architecture, six-state model, NMPC formulation, assumptions,
   conditional theorem, and claim limits are locked;
3. the candidate contribution is P versus GLT rather than component novelty or
   deterministic repair;
4. every future implementation and empirical gate is routed to
   `IMPLEMENTATION_PLAN.md` without execution; and
5. no numerical, real-time, safety, robustness, or hardware claim is admitted.

Review record:
`research/reviews/q1-gap-review-20260823.md` (`Weak Accept`, gap/protocol only).
