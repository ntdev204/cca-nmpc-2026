---
type: research-gap
status: hypothesis-ready
evidence_status: literature-grounded; study-design-only
---

# Research gap and falsifiable scope

## What is already established

Prior work already covers context-aware MPC/NMPC, online or fixed-budget risk
allocation, chance constraints, human motion prediction, Mecanum control, and
learning-assisted navigation. Therefore none of the following is a defensible
stand-alone novelty claim: “YOLO26s-pose + LSTM + NMPC”, “Mecanum NMPC”, “RL +
NMPC”, or “context-aware risk” in isolation.

See [[03_Literature/literature-review]], [[03_Literature/prior-art-delta]],
[[03_Literature/nearest-work-matrix]], and the dated primary-source refresh in
[[03_Literature/web-verified-gap-sources]]. The continuation search is recorded
in [[03_Literature/current-research-refresh-20260814]] and is still
screening-only; it further narrows the claim boundary without promoting a new
gap.

## Defensible gap

The remaining question is narrower and testable:

> Under a fixed total chance-constraint allowance, does a compact context
> interface—position, speed, and coarse direction from a short observation
> history—improve the safety–tracking–feasibility trade-off of a position-state
> Mecanum CCA-NMPC with body-velocity commands when the global path is fixed and
> only a conflict-triggered local path is regenerated on a map?

The contribution is the auditable interface and its evaluation protocol, not a
new detector or a claim that risk allocation itself is unprecedented.

## Evidence binding for the gap

| Gap statement | Closest prior-art rows | Consequence for this study |
|---|---|---|
| Context-aware human navigation is not sufficient novelty. | NW-01, NW-02, NW-20, NW-22 | Report context as an interface and compare against context-off/permuted-context conditions. |
| Fixed-total or adaptive risk redistribution is established. | NW-14--NW-18, NW-21, NW-25 | Treat the allocator as a transparent heuristic; include uniform, optimized/feasibility and learned allocation baselines. |
| LSTM/predictor plus MPC/NMPC integration is established. | NW-05, NW-10, NW-20, NW-22, NW-23 | LSTM remains inside CCA; require calibration, ID/OOD split and failure propagation rather than claiming architecture novelty. |
| The unverified question is the matched system trade-off under the stated boundary. | NW-01, NW-04, NW-18, NW-21, NW-25 | Test safety, tracking, feasibility and computational cost on the same fixed map, clearance, seeds and denominator. |

These rows are the scope of the focused Zotero/Obsidian audit. They are not an
exhaustive database inventory and do not imply a systematic-review count.

## Boundary update from the 2026-08-13 discovery refresh

The latest Google/web pass and Zotero full-text audit added three boundary
records without changing the gap: SICNav (IEEE T-RO, 2025) adds interactive
crowd MPC and real-robot safety evaluation
([[03_Literature/Sources/source-samavi-sicnav-2026]]);
cooperative GP--MPC adds learned uncertainty with chance-constrained
multi-agent control ([[03_Literature/Sources/source-cooperative-gp-mpc-2026]]);
and dynamic risk-aware MPPI is a direct sampling-controller comparator
([[03_Literature/Sources/source-dra-mppi-2025]]). SICNav is now admitted as a
Zotero full-text audit; the other two remain screening-only and none is
promoted to quantitative evidence. They reinforce that interaction, learned
uncertainty and MPPI are comparator boundaries, while the remaining question is
still the matched CCA interface trade-off on the stated position-state Mecanum
plant.

The subsequent risk/context refresh adds SHARP's Gaussian/Bonferroni/CVaR safety
mask and a context-aware human-preference MORL pipeline as further boundary
evidence ([[03_Literature/web-verified-gap-sources]]). These records make the
claim boundary stricter: generic closed-form risk allocation, CVaR safety,
context adaptation and learning-based navigation are already occupied. They do
not answer the matched fixed-budget CCA interface comparison on this plant, so
the gap remains empirical and bounded rather than a first-principles novelty
claim.

The 2026-08-13 control/uncertainty/Mecanum refresh adds risk-aware MPPI,
Mecanum MPC and hardware disturbance-rejection, and uncertainty-aware
predictive safety as additional screening boundaries
([[03_Literature/web-verified-gap-sources]]). These records further exclude
stand-alone claims of CVaR/MPPI novelty, Mecanum MPC novelty, or
uncertainty-aware safety novelty. They do not supply a matched fixed-budget CCA
interface evaluation in the position-state Mecanum setting; no claim or paper
file was changed.

The latest learning/control refresh adds model-based reinforcement learning for
uncertain social navigation and neural chance-constrained MPC under
uncontrollable agents. Both occupy the learning-based planning and neural
chance-control boundaries, respectively. Therefore RL, neural MPC and
chance-constrained learning remain comparator or ablation choices, not new
components that can carry the novelty claim. The gap remains the matched,
provenance-linked empirical comparison of the CCA interface under the stated
Mecanum/global-path/local-trigger boundary.

The 2026-08-13 position-state refresh adds a kinematic Mecanum MPC record,
social-force NMPC with velocity-level commands and fixed global planning,
model-based RL with stochastic pedestrian interaction, uncertainty-aware
predictive safety filtering and ellipsoidal-obstacle MPC
([[03_Literature/Sources/source-position-state-boundary-20260813]]). These
records further exclude standalone claims of position-control, Mecanum-MPC,
RL, uncertainty-aware safety or ellipse-based obstacle novelty. They do not
answer the matched fixed-budget CCA interface comparison; the gap and the
non-claims therefore remain unchanged.

## Boundary refresh — 2026-08-13

The newest targeted web/Zotero check adds a hardware Mecanum MPC study with
residual learning, a multisensor crowd-MPC system validated on a real robot,
and an HRI study showing that prediction error alone is not a reliable proxy for
closed-loop navigation or human outcomes ([[03_Literature/Sources/source-2026-mecanum-crowd-control-refresh]]).
These records make the study boundary stricter: Mecanum MPC, sensor fusion,
human prediction, self-supervision and real-robot tracking are interfaces or
comparators, not standalone novelty. The only remaining claim candidate is the
matched fixed-total CCA interface comparison under the declared position-state,
body-velocity, fixed-global-path and local-trigger conditions. No manuscript
file was edited.

The same note was refreshed with recent pedestrian-prediction, pedestrian-aware
MPC and Mecanum-validation records. Those works further occupy the prediction,
interaction-objective and platform-integration spaces. They do not answer the
matched fixed-budget CCA comparison; they instead require the study to report
prediction, safety, tracking, timing and hardware-boundary outcomes separately.
The gap remains a bounded empirical question, not a claim that LSTM, MPC or
Mecanum hardware is novel in isolation.

The 2026-08-13 attention/interaction refresh adds a physical attention-aware
collision-avoidance study and a robot--pedestrian influence dataset record
([[03_Literature/Sources/source-tadano-pedestrian-attention-2025]],
[[03_Literature/Sources/source-agrawal-rpi-dataset-2025]]). These records further
require explicit interaction-condition metadata and a separation between
perception/context quality and closed-loop control outcomes. They do not provide
target Astra-S/N10P/Mecanum evidence and do not change the narrow CCA interface
gap. Wikimedia Commons remains only a source-discovery route for real images;
page-level rights, privacy screening and blinded annotations remain mandatory.

The subsequent 2026-08-13 physical-baseline refresh checked DR-MPC, SI-MPC,
Mecanum velocity-obstacle navigation and a Mecanum RL local controller
([[03_Literature/Sources/source-screening-refresh-20260813]]). These records
further occupy residual-learning, learned prediction, dynamic-obstacle
planning and omnidirectional-RL spaces. They also reinforce a required
separation between open-loop predictor metrics and closed-loop safety/tracking
outcomes. The gap remains the matched transparent CCA interface comparison, not
the use of LSTM, MPC, Mecanum hardware or learning in isolation.

## Hypotheses

- **H1 — mechanism:** CCA changes the allocation while preserving the declared
  total allowance and hard actuator constraints.
- **H2 — context value:** adding the LSTM context signal changes local-path
  triggers and improves a pre-registered safety/tracking trade-off relative to
  the same NMPC with a fixed or uniform allocation.
- **H3 — interface robustness:** bounded missingness and direction uncertainty
  do not produce unsafe commands because the fallback and stale-context rules
  are explicit.
- **H4 — system boundary:** any improvement must survive comparisons with MPC,
  DWA, and MPPI under the same map, footprint, trigger, seeds, and denominator.

These are hypotheses, not findings. They remain research questions until the
protocol and analysis defined in [[06_Methods/evaluation-protocol]] are applied.

## Boundary refresh — 2026-08-14

The latest publisher-level refresh adds uncertainty-aware dynamic-obstacle MPC,
ellipsoidal-obstacle MPC with a real wheeled platform, social MPC evaluated in
simulation and the real world, and a holonomic/Mecanum MPC baseline. These
records further occupy uncertainty modeling, geometric clearance, social
navigation, and computational-efficiency claims. They do not answer the
matched fixed-budget CCA interface comparison on the selected position-state
Mecanum plant. The update is screening-only and does not change the hypotheses,
open protocol gates, or locked manuscript.

See the dated source audit in [[03_Literature/web-verified-gap-sources]].

The 2026-08-14 learning/social-navigation refresh adds a recent benchmark
review, uncertainty-aware social MPC, online risk adaptation, deep-residual MPC
with hardware trials and social-force NMPC
([[03_Literature/Sources/source-social-navigation-refresh-20260814]]). These
records further exclude standalone claims for learning-based navigation,
LSTM--MPC integration, risk adaptation or social-force modeling. They increase
the required evaluation bar but do not answer the matched fixed-budget CCA
interface comparison on the stated position-state Mecanum plant. The gap and
hypotheses remain screening-grounded and unverified until the frozen
confirmatory and hardware gates are met.

The late publisher refresh adds a multi-room crowd-MPC pipeline, a physical
dynamic-cost-map MPC platform, learning-guided MPPI and a repeated social-force
NMPC benchmark ([[03_Literature/current-research-refresh-20260814]]). These
records further raise the required separation between perception quality,
context prediction, closed-loop safety, tracking, timing and physical
provenance. They do not create a new standalone novelty claim and do not alter
the bounded CCA interface hypothesis.

The continuation web check adds action-conditioned world-model social
navigation, flow-matching/MPPI generation-refinement, chance-constrained
sampling-based MPPI, uncertainty-aware topological social MPC and scenario-
based joint collision-probability planning. The chance-constrained MPPI record
further rules out treating probabilistic sampling control as an unoccupied
baseline category ([[03_Literature/Sources/source-c2u-mppi-2025]]).
Together they close the remaining broad interpretations of “prediction + RL,”
“learning + MPPI,” “risk-aware social MPC,” and “probabilistic collision
avoidance.” The gap remains the narrower matched comparison of a causal,
fixed-budget CCA context interface on the position-state Mecanum plant, with
global path fixed, local replanning trigger-only, and explicit safety,
tracking, feasibility and computation estimands. This is a screening update;
no citation or empirical claim was promoted.

## Non-claims

The study does not claim a universal risk-allocation theorem, real-time
performance, hardware safety, detector superiority, or human-trajectory
forecasting from still images. For a dynamic person, only CCA-NMPC may use a
causal context-velocity prediction internally for chance rows; the image
overlay reports perception/context only, and no predicted human path is
exported or drawn. The robot local path is generated and evaluated on the
Python map.

## Evidence questions

1. Does the allocator conserve the total allowance for every evaluated event?
2. Does context affect only the declared allocation/trigger interface?
3. Which failure modes change under missingness, occlusion, and direction
   reversal?
4. Are any gains reproducible across paired seeds and controller baselines?

Related: [[05_Theory/context-aware-risk-allocation]],
[[05_Theory/proof-obligations]], [[06_Methods/evaluation-protocol]],
[[08_Decisions/decision-register]].

Related hub: [[00_MOC/project-map]]
