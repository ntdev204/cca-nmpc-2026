---
type: model-implementation-contract
status: candidate-checked
evidence_status: static-qa-only; scientific-validation-open
---

# Model--implementation contract

This note defines interfaces that must remain equivalent between the mathematical
description and the implementation. It is a design contract, not a test report.

| Contract | Required invariant |
|---|---|
| State | pose and body velocity use one declared frame and ordering |
| Context | position, speed, direction, validity, and freshness have explicit units |
| Risk | every active event receives one allowance and the total budget is conserved |
| Controller | body velocity, pose, slew, state and bounded candidate-rollout interfaces are explicit; the full chance-constrained NMPC formulation is a reference contract and is not yet an executable solver |
| Local path | generated on the map only after the fixed trigger; global path is unchanged |
| Learning | score loop can reject a candidate without modifying the controller safety layer |
| Provenance | every accepted data/model/run object has an immutable identifier and hash |

The active LSTM interface has the same causal boundary: a history window is
encoded by the standard gated recurrence, a velocity head returns only
\(\hat v_k\), and direction scores are projections on four fixed axes. The
controller may integrate that velocity internally for a chance row, but the
adapter does not decode or export a human future path. This is a source-level
and unit-test parity requirement, not evidence of prediction accuracy.

The corresponding definitions are in [[05_Theory/notation]],
[[05_Theory/system-model]], [[05_Theory/context-aware-risk-allocation]], and
[[05_Theory/proof-obligations]].

Related: [[06_Methods/methods-overview]], [[06_Methods/execution-roadmap]],
[[08_Decisions/decision-register]].

## Static parity checkpoint — 2026-08-12

The current MATLAB unit/property suite passed 70/70 tests and the Python
repository/contract suite passed. This closes only the software-level parity
checkpoint for the listed invariants. It does not establish predictor
calibration, actuator identification, recursive feasibility, closed-loop
stability, real-time execution, or physical safety. Those items remain linked
to [[05_Theory/proof-obligations]] and the experimental protocols.

The Python and MATLAB NMPC probability-eligibility flags now fail closed unless the
prediction carries a calibration SHA-256/domain, independent one-sided tail
verification, frame/time/age verification, complete mode partition,
covariance provenance and geometry-containment verification. The guard is
tested as software plumbing; no active calibration artifact is thereby created.

The position-state chance-row paths additionally reject non-finite, asymmetric
or materially non-positive-semidefinite relative covariance before projection.
This input-domain parity check does not provide covariance provenance,
calibration or operational probability evidence.

The active physical model uses the six-state Mecanum pose/velocity vector with
body velocity as the command. The compiled candidate controller reports a
reduced risk correction, maximum violation and a reserved zero slack field; it
does not solve the full chance-constrained nonlinear program. The older
wheel-input simulator is compatibility code and is not physical evidence.

Related hub: [[00_MOC/project-map]]
