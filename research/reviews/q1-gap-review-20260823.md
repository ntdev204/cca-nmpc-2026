# Q1 Review Panel Report — Context-Conditioned Genetic Local Reference Generation with Terminal NMPC for Human-Aware Mecanum Navigation

This is a provisional review of the research gap and preregistered protocol,
not a review of a completed manuscript or an empirical contribution.

## Panel Composition

- Reviewer 1 — Novelty Skeptic: tests the narrowed contribution against PathFG,
  reference governors, evolutionary repair, context MPC, and GA planning.
- Reviewer 2 — Control Theory: checks whether the proposed reference interface
  overextends the fixed-reference terminal-NMPC result.
- Reviewer 3 — Evolutionary Constrained Optimization: evaluates the decoder,
  repair, feasibility witness, and deadline-bounded GA mechanism.
- Reviewer 4 — Robotics & Systems Integration: checks Mecanum embodiment,
  fixed-path operation, sensing assumptions, and executable scope.
- Reviewer 5 — Human-Robot Interaction / Context Awareness: checks whether the
  selected human context supports the intended human-aware claim.
- Reviewer 6 — Statistics & Reproducibility: checks causal ablations, matched
  baselines, thresholds, failure accounting, and confirmatory isolation.

## Reviewer 1: Novelty Skeptic

**Summary of assessment:** The revised gap no longer relies on novelty by
combination. It asks whether one specific context-conditioned Mecanum
genotype-to-dynamic-reference composition has a measurable downstream effect.

**Strengths (specific):**

- The gap explicitly concedes that PathFG already combines planning, a
  feasibility governor, and NMPC.
- No novelty is assigned to LSTM, GA, NMPC, homotopy repair, reference
  admission, or exclusive controller authority individually.
- The candidate claim can be rejected by preregistered mechanism and navigation
  thresholds rather than defended only through architectural prose.

**Weaknesses (specific, at least 3):**

1. The genotype-to-reference composition remains incremental unless its
   downstream effect survives the decoder-only and penalty-only contrasts.
2. Bounded homotopy repair closely follows established evolutionary repair and
   scalar reference-governor interpolation; it cannot carry a novelty claim.
3. PathFG uses equilibrium progression while this work uses a time-indexed
   reference. Any numerical comparison requires an explicit semantic adapter.
4. The focused DOI search is search-bounded and cannot support a universal
   priority or "first" statement.

**Recommendation:** Weak Accept

**Reasoning:** The gap is defensible for implementation and validation, but the
paper contribution exists only if the registered causal effects are observed.

## Reviewer 2: Control Theory

**Summary of assessment:** The gap correctly separates CCA reference generation
from NMPC motion control and confines Lyapunov analysis to the latter.

**Strengths (specific):**

- The fixed-reference theorem and the switching admission contract are not
  presented as a common-Lyapunov result for the whole pipeline.
- The admissible set and the state-dependent NMPC feasible-witness set are
  separated, including wheel-speed constraints.
- Solver timeout or failure causes rejection and is not misreported as proof
  that the mathematical feasible set is empty.

**Weaknesses (specific, at least 3):**

1. A previously feasible fallback can be invalidated by a changed environment;
   a stop policy remains necessary outside the nominal shift argument.
2. Reference admission establishes only a conditional fixed-reference result,
   not collision safety or stability under unrestricted CCA switching.
3. Constraint tolerances and local SQP feasibility are numerical evidence, not
   exact satisfaction of the theorem assumptions.
4. The physical wheel limits and first-order velocity lag remain nominal until
   calibrated, so hardware stability cannot be inferred.

**Recommendation:** Accept

**Reasoning:** These are explicit scope limits rather than hidden proof defects;
the control claim is adequately bounded for the proposed research stage.

## Reviewer 3: Evolutionary Constrained Optimization

**Summary of assessment:** The proposed GA mechanism is now an upstream local
reference search with deterministic decoding, bounded repair, and a downstream
feasible-witness gate.

**Strengths (specific):**

- The complete context on/off by penalty/decoder/decoder-plus-repair factorial
  isolates the claimed mechanism.
- Shifted initialization is held fixed in primary contrasts, with random
  initialization treated as a separate secondary comparison.
- Pre-repair and post-repair admissibility, diversity, deadline failures, and
  downstream navigation are all required; repaired yield alone is insufficient.

**Weaknesses (specific, at least 3):**

1. The deterministic repair can collapse genotype diversity and bias the search
   toward the previous accepted reference; this must be measured.
2. The finite repair sequence guarantees bounded computation, not that a
   feasible reference will be found.
3. Penalty-only fairness depends on identical candidate evaluations and budget;
   allowing it cheaper fitness calls would confound latency and yield.
4. GA stochasticity requires paired seeds and all empty/deadline outcomes in
   the denominator.

**Recommendation:** Weak Accept

**Reasoning:** The mechanism is falsifiable and correctly scoped, but its value
is empirical and cannot be assumed from the decoder construction.

## Reviewer 4: Robotics & Systems Integration

**Summary of assessment:** The gap is specific to a holonomic Mecanum platform
and preserves a fixed global path while CCA changes only the local reference.

**Strengths (specific):**

- The six-state body-velocity interface and wheel-speed map are common to all
  motion-control baselines.
- The embodiment claim requires a full-Mecanum versus constrained lateral-motion
  ablation instead of cross-platform published numbers.
- Hardware work and real-time claims remain paused until simulation acceptance.

**Weaknesses (specific, at least 3):**

1. The first-order velocity model omits slip, asymmetric wheel response,
   localization delay, and actuator saturation dynamics.
2. A permanently blocked global path is outside local-reference recovery; stop
   and failure accounting must be explicit.
3. Perception latency, missed detections, transforms, and context uncertainty
   are only scenario plans, not validated signals.
4. A Simulink signal-flow model is not a calibrated physical drivetrain model.

**Recommendation:** Weak Accept

**Reasoning:** The system question is worth testing, but Q1 systems claims will
require the frozen simulation and later physical evidence.

## Reviewer 5: Human-Robot Interaction / Context Awareness

**Summary of assessment:** Human context influences the robot reference, while
the method does not generate or display a human trajectory as a control output.

**Strengths (specific):**

- Prediction quality is not treated as evidence of navigation safety.
- Context-off ablations can reveal whether pose-derived direction information
  has causal downstream value.
- Missed detection, delay, density, and uncertainty are named scenario families.

**Weaknesses (specific, at least 3):**

1. Position, speed, direction, and confidence support direction-aware avoidance,
   not a broad social-compliance claim.
2. Minimum distance and collision do not measure comfort, legibility, or human
   disturbance.
3. Scripted pedestrian motion does not establish interactive human response.
4. Pose confidence must be calibrated across occlusion and viewpoint before it
   can be interpreted as behavioral uncertainty.

**Recommendation:** Weak Accept

**Reasoning:** The gap survives only with narrow "human-motion-aware avoidance"
language unless richer HRI outcomes are later introduced.

## Reviewer 6: Statistics & Reproducibility

**Summary of assessment:** The protocol has matched layers, a full mechanism
factorial, quantitative effect thresholds, tail latency, and failure accounting.

**Strengths (specific):**

- Primary repair and penalty contrasts use the same context-on and shifted-init
  conditions.
- Minimum effects, noninferiority limits, positive paired confidence bounds,
  deadline misses, and path-quality costs are registered.
- Development and confirmatory scenarios are separated and all attempted
  episodes remain in the denominator.

**Weaknesses (specific, at least 3):**

1. The independent sampling unit and hierarchical bootstrap scheme are not yet
   frozen.
2. Scenario counts or a precision/power justification are absent.
3. Secondary hypothesis families and multiplicity correction are not enumerated.
4. Baseline tuning budgets, seed registry, and configuration hashes must be
   frozen before confirmatory execution.

**Recommendation:** Weak Accept

**Reasoning:** The design is suitable to proceed, but it is not yet an executed
or fully frozen confirmatory protocol.

## Cross-Reviewer Disagreements

The Control Theory reviewer accepts the bounded theoretical scope because the
remaining risks are disclosed assumptions. The Novelty, Optimization, Systems,
HRI, and Statistics reviewers remain at Weak Accept because the contribution is
defined by empirical effects that have not yet been observed. No reviewer finds
a fatal contradiction in the current gap formulation.

## FINAL DECISION: Weak Accept

**Justification:** The research gap is sufficiently honest, closest-work-aware,
and falsifiable to enter implementation and frozen validation. This is not an
acceptance of a Q1 manuscript. The gap automatically fails if the exact
context-conditioned genotype-to-reference mechanism does not meet every primary
effect, latency, and path-quality threshold.

**What would be required to strengthen the paper (if not a clean Accept):**

- Freeze the statistical unit, scenario count, resampling, multiplicity, tuning,
  seed, and configuration-hash rules.
- Execute the registered factorial without changing thresholds after viewing
  confirmatory data.
- Demonstrate downstream navigation benefit and not merely repaired-reference
  feasibility.
- Keep the contribution language restricted to the Mecanum reference
  composition and its measured effect.

## Superseding closest-work refresh

A later focused DOI refresh identified context-aware GA planning, people-aware
GA trajectories, human-aware GA optimization, a GA--PCHIP--controller pipeline,
GPU local GA on an edge robot, and GA used inside nonlinear predictive control.
The earlier gap-only `ACCEPT` is therefore withdrawn. The current gap status is
`CANDIDATE`: implementation may proceed, but the contribution remains rejected
unless the exact fixed-path Mecanum decoder/repair mechanism survives the
registered matched ablations and produces downstream navigation benefit within
the frozen timing and path-quality limits.

## Theory-lock addendum — 2026-08-23

The implementation-facing wording in the preceding paragraph is obsolete for
the locked theory scope. Deterministic decoding, bounded repair, homotopy, and
the planner--controller cascade are prior art or engineering choices and are not
the candidate contribution.

The retained candidate question is whether observation-rate recurrent context
updates improve the fixed-global-path Mecanum local-path mechanism over
planning-event-only updates when P and GLT use the same fixed-weight LSTM, GA,
observations, planning events, and downstream NMPC contract. Repair comparisons
remain secondary future ablations in `IMPLEMENTATION_PLAN.md`.

The panel decision remains `Weak Accept` for a bounded, falsifiable research
question only. It does not admit an empirical benefit, a real-time result, a
safety result, or a complete Q1 manuscript claim.
