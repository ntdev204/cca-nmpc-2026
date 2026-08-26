# Q1 Review Panel Report — Terminal-NMPC Motion-Control Support for Context-Conditioned Mecanum Navigation

This is a review of one supporting motion-control block. It is not a review of
the complete CCA-NMPC manuscript, trajectory generator, or empirical
contribution.

## Panel Composition

- Reviewer 1 — Novelty Skeptic: tests whether standard terminal-NMPC and
  governor theory is being misrepresented as the paper contribution.
- Reviewer 2 — Control Theory: checks terminal invariance, recursive
  feasibility, Lyapunov descent, and every limiting assumption.
- Reviewer 3 — Numerical Optimization: checks local SQP acceptance, smooth
  constraints, feasible warm starts, and numerical claim limits.
- Reviewer 4 — NMPC Implementation Verification: checks equation-to-code
  correspondence across MATLAB, Python, and Simulink.
- Reviewer 5 — Robotics & Systems Integration: checks whether nominal
  simulation evidence is being extended to safety, real time, or hardware.
- Reviewer 6 — Statistics & Reproducibility: checks deterministic
  falsification coverage, provenance, and the limits of a smoke test.

## Reviewer 1: Novelty Skeptic

**Summary of assessment:** The block is correctly positioned as standard
supporting control theory. The paper contribution is reserved for the exact
context-conditioned Mecanum genotype-to-dynamic-reference composition and its
measured downstream effect.

**Strengths (specific):**

- The notes cite Chen--Allgower and Mayne for terminal-NMPC ingredients and do
  not claim a new theorem family.
- Reference governors and planner--NMPC integration are explicitly treated as
  prior art.
- The architecture note no longer calls authority separation or the reference
  interface a contribution.

**Weaknesses (specific, at least 3):**

1. LQR terminal feedback, a quadratic terminal set, and shifted-sequence descent
   are established theory and cannot appear in the novelty list.
2. The Mecanum-specific nonlinear remainder calculation is an implementation
   specialization, not a new stability principle.
3. Strict post-solve checking and fallback selection are engineering rigor, not
   a new optimizer.
4. Any claim of full CCA-NMPC stability would conflict with the fixed or
   shift-compatible reference theorem.

**Recommendation:** Accept

**Reasoning:** No novelty overclaim remains when this block is used only as the
correctness foundation for the separate CCA contribution.

## Reviewer 2: Control Theory

**Summary of assessment:** The terminal construction and conditional theorem
are internally consistent for the nominal six-state model.

**Strengths (specific):**

- The nominal actuator factor is nondegenerate at
  \(\alpha=\Delta t/\tau_v=0.5\).
- The analytic remainder bound determines a positive terminal level
  \(\rho=9.51\times10^{-4}\), rather than selecting the set visually.
- The proof defines the storage value on the augmented controller state
  containing the robot state, admitted reference, and stored feasible plan; it
  does not require a globally optimal SQP solution.
- Terminal invariance, angular-chart containment, recursive feasibility, and
  the selected-plan descent inequality are stated explicitly.

**Weaknesses (specific, at least 3):**

1. The result is local; the certified terminal level has no global
   region-of-attraction interpretation.
2. Exact model matching and unchanged command exclude slip, delay, disturbance,
   and state-estimation error.
3. A newly admitted reference starts a new conditional argument; no common
   Lyapunov function is proved for arbitrary repeated switching.
4. Collision avoidance is a reference-generation constraint, not a consequence
   of the Lyapunov inequality.

**Recommendation:** Accept

**Reasoning:** These are explicit theorem assumptions and claim boundaries, not
hidden proof defects. No fatal theorem--code contradiction remains.

## Reviewer 3: Numerical Optimization

**Summary of assessment:** The local SQP implementation preserves the stated
suboptimal-NMPC argument but is not deployment-ready.

**Strengths (specific):**

- Wheel-speed bounds use smooth paired inequalities rather than an absolute
  value inside SQP.
- A new reference supplies its dynamically feasible decoded command sequence as
  the warm start.
- Candidate output is independently rolled out and rejected for any positive
  evaluated inequality residual or cost above the feasible warm start.
- A cached fallback flag is not trusted; the fallback is reevaluated from the
  current state.

**Weaknesses (specific, at least 3):**

1. No analytic gradients, constraint Jacobians, or Hessian structure are
   supplied.
2. Variable scaling, KKT residuals, and conditioning are not reported.
3. The approximately 1.46 s receipt-run solve exceeds the 0.10 s sample interval by
   an order of magnitude.
4. A zero post-check tolerance is theorem-aligned but may be sensitive to
   platform-dependent floating-point roundoff.

**Recommendation:** Weak Accept

**Reasoning:** The implementation is adequate for offline theorem verification.
It supports no real-time or target-code claim.

## Reviewer 4: NMPC Implementation Verification

**Summary of assessment:** The exercised MATLAB, Python, and Simulink paths now
match the accepted model and shifted-plan contract.

**Strengths (specific):**

- The shifted sequence appends \(K_fe_N\), including a nonzero-terminal-error
  regression with residual \(-7.39\times10^{-10}\).
- MATLAB--Python parity is \(3.55\times10^{-15}\) over both
  \(\alpha<1\) and \(\alpha=1\), including yaw near \(\pi\).
- Tests cover five terminal headings, 128 additional deterministic directions,
  strict residual rejection, state containment, initial mismatch, invalid
  switch, and forged stale fallback.
- The 30-block Simulink model generates a time-indexed dynamic reference outside
  NMPC and produced three finite, feasible controller samples.

**Weaknesses (specific, at least 3):**

1. The Simulink run is only 0.2 s and does not demonstrate long-horizon
   convergence.
2. Deterministic direction sampling is falsification evidence, not a replacement
   for the analytic ellipsoidal proof.
3. Two cross-language cases do not exhaust the parameter domain.
4. The Simulink reference helper has not been tested for arbitrary target yaw
   and nonzero terminal velocity.

**Recommendation:** Accept

**Reasoning:** The current evidence is sufficient for theorem--implementation
parity, not for performance, robustness, or real-time claims.

## Reviewer 5: Robotics & Systems Integration

**Summary of assessment:** The block is suitable as a nominal Mecanum
motion-control model and nothing broader.

**Strengths (specific):**

- State, body-velocity command, wheel-speed interface, and update order are
  shared by MATLAB, Python, and Simulink.
- Reference admission and NMPC command authority are separated.
- Hardware, collision-safety, robustness, and real-time claims remain blocked.

**Weaknesses (specific, at least 3):**

1. Wheel ordering, signs, speed limits, actuator time constant, delay, and slip
   remain uncalibrated.
2. The wheel block is a kinematic command map, not measured drivetrain dynamics.
3. The ideal nominal reference stream does not include localization or
   communication faults.
4. A changing environment may invalidate both the shifted plan and its
   reference; this block does not prove a safe-stop policy.

**Recommendation:** Accept

**Reasoning:** No robotics overclaim remains inside the bounded manuscript-safe
scope.

## Reviewer 6: Statistics & Reproducibility

**Summary of assessment:** Deterministic structural evidence is reproducible
once tied to the PR02 execution receipt; it is not an empirical experiment.

**Strengths (specific):**

- Positive and adversarial negative checks are both included.
- The clean MATLAB invocation exited with code zero and Python compilation and
  parity checks passed.
- The receipt freezes tool versions, configuration, code hashes, result values,
  and the structural-nominal evidence boundary.

**Weaknesses (specific, at least 3):**

1. A three-sample smoke run cannot estimate solver reliability.
2. One solve time cannot support latency statistics or a real-time statement.
3. No parameter sensitivity, Monte Carlo campaign, or empirical
   region-of-attraction estimate is available.
4. Controller baselines currently establish structural feasibility only, not
   comparative performance.

**Recommendation:** Weak Accept

**Reasoning:** Repetition and confidence intervals are unnecessary for the
analytic theorem, but they remain mandatory for later performance claims.

## Cross-Reviewer Disagreements

The Control Theory and Implementation reviewers accept the bounded correctness
claim. Numerical Optimization and Reproducibility remain at Weak Accept because
the implementation is slow and the execution is deliberately a structural
check. The Novelty reviewer accepts the block only because the manuscript does
not count it as the paper contribution.

## FINAL DECISION: Accept

**Justification:** No fatal mathematical, implementation-parity, novelty, or
claim-scope flaw remains. The block is accepted for transfer as standard
supporting motion-control theory only. This decision is not acceptance of the
full paper and does not admit CCA performance, safety, robustness, real-time, or
hardware claims.

**What would be required to strengthen the paper (if not a clean Accept):**

- Demonstrate the separate CCA contribution with the frozen matched factorial
  and downstream navigation thresholds.
- Run long-horizon and matched controller simulations before reporting
  performance.
- Report target-device latency distributions before any real-time claim.
- Calibrate and validate the physical model before any hardware-stability claim.
