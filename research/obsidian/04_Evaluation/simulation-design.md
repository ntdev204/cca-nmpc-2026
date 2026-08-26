---
domain: evaluation
type: note
status: planned
scope: outside-current-theory-goal
evidence: implementation-plan-only
tags: [python, matlab, simulink, simulation]
---

# Planned simulation design

No simulation result is active evidence for the current theory-only goal.
Future simulation must preserve the accepted layer boundary:

1. Python evaluates causal context updating, the LSTM interface, GA local-path
   generation, geometric feasibility, and matched CCA ablations.
2. MATLAB/Simulink evaluates only the six-state Mecanum plant, reference
   generator, NMPC tracking, terminal set, and Lyapunov conditions.
3. Cross-layer studies pass a geometric local path into the common NMPC backend;
   no CCA logic is embedded in MATLAB/Simulink.
4. `src/` remains the real-robot runtime and is outside simulation.

The simulated human may move, but the controller receives only causal current
position, velocity, coarse direction, confidence, and observation age. Future
human coordinates are never supplied or rendered as a generated trajectory.

The NMPC study must include a nonzero initial tracking error and a dynamically
feasible reference ending at rest. It must retain reference and actual
$x,y,\theta,v_x,v_y,\omega$, applied commands, commanded and actual wheel rates,
constraint margins, terminal ratio, and the Lyapunov descent residual. These are
planned observables, not current results.

The CCA study must isolate P from GLT, GCV, and G0 under the matched contract in
[[04_Evaluation/baseline-contract]]. It must report both geometric proposal
quality and downstream navigation outcomes without treating repeated candidates
as independent samples.

Exact scenarios, datasets, training, repair algorithm, budgets, seeds,
statistics, falsification thresholds, software parity checks, and execution
order are deferred to `IMPLEMENTATION_PLAN.md`. Simulation may test the theory;
it cannot prove real-time or hardware performance.

## Links

[[03_Theory/mathematical-model]] · [[03_Theory/cca-trajectory-generation]] ·
[[03_Theory/nmpc-motion-control]] · [[03_Theory/lyapunov-stability]] ·
[[04_Evaluation/baseline-contract]] · [[04_Evaluation/claim-evidence-boundary]]
