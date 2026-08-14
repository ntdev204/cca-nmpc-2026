---
type: primary-source-check
status: metadata-and-landing-page-verified
date: 2026-08-11
paper_edit: prohibited
---

# Primary-source landing-page check

This note records a small verification pass after the Zotero live export. It
does not replace the focused source-note and full-text audit.

| Zotero key | Primary/authoritative landing page | What it verifies | Boundary |
|---|---|---|---|
| `wang_safe_2025` | [DASC Lab project page](https://dasc-lab.github.io/papers/2025/2025-risk_adaptive_cvar_bf/) | risk-adaptive CVaR barrier navigation and dynamic safety-zone framing | project abstract; not a full comparative audit |
| `engelaar_planning_2026` | [ScienceDirect article](https://www.sciencedirect.com/science/article/pii/S0167691126001349) | elastic chance constraints and adaptive SMPC framing; DOI `10.1016/j.sysconle.2026.106474` | landing page/abstract; proof details require full text |
| `wang_reinforcement_2026` | [arXiv record](https://arxiv.org/abs/2605.21257) | differentiable CVaR-barrier risk adaptation with RL | preprint record; peer-review status not inferred |
| `sun_socially_2025` | [arXiv record](https://arxiv.org/abs/2506.14305) | online uncertainty-driven risk adaptation/LR-MPC framing | preprint record; no claim of superiority imported |

## Consequence for the gap

These records are sufficient to reject a broad claim that context-aware or
risk-adaptive MPC, elastic chance constraints, or RL-based risk adaptation is
unoccupied. They do not prove that every nearest comparator is equivalent to
the proposed fixed-budget allocator. That narrower equivalence question still
requires full-text extraction of assumptions, action space, budget semantics,
clearance policy, and evaluation protocol.

## Related notes

[[00_MOC/project-map]] · [[03_Literature/literature-review]] · [[04_Research_Gap/research-gap]]

## Search refresh — Google and Google Scholar-oriented queries — 2026-08-12

This refresh used broad Google and Google-Scholar-oriented queries for
`context-aware risk allocation chance-constrained NMPC human robot` and
`LSTM uncertainty chance-constrained MPC human robot`. Each candidate was
checked against an author, publisher, or repository landing page before being
used as evidence. The connector could not open a direct Google Scholar result
page in this session, so the discovery pass was supplemented by ordinary web
search and then restricted to authoritative landing pages; it is not claimed
as Google Scholar coverage. The refresh is a focused-source update, not a claim
of Scopus, Web of Science, or IEEE Xplore coverage.

| Candidate | Primary landing page | Screening consequence |
|---|---|---|
| Liu et al., *Adaptive Reinforcement and Model Predictive Control Switching for Safe Human-Robot Cooperative Navigation* (2026) | [arXiv record](https://arxiv.org/abs/2601.16686) | LSTM context, MPC safety filtering, DWA comparison, and initial deployment are already combined; this further rejects a broad “LSTM + context + MPC” novelty claim. |
| Akhtyamov et al., *Chance-constrained neural MPC under uncontrollable agents via sequential convex programming* (2026) | [ScienceDirect record](https://www.sciencedirect.com/science/article/abs/pii/S1751570X26000774) | Learned prediction, policy-shift-aware uncertainty bounds, chance-constrained MPC, and closed-loop evaluation are established nearby; the present study must keep its claim narrower and report calibration/OOD limits. |
| Busellato et al., *Uncertainty Aware-Predictive Control Barrier Functions* (2026) | [Robotics and Autonomous Systems record](https://www.sciencedirect.com/science/article/pii/S0921889025003884) | Probabilistic human forecasting with formal safety filtering and real-world HRI is adjacent prior art; it is a boundary comparator, not evidence that the present allocator is novel. |
| Engelaar et al., *Planning with elastic chance constraints in stochastic model predictive control* (2026) | [DOI landing page](https://doi.org/10.1016/j.sysconle.2026.106474) | Adaptive risk values with a total bound and closed-loop conditions remain established; the fixed-budget allocator can only be presented as a transparent interface hypothesis. |

### Mecanum, benchmark, and sensing refresh

| Candidate | Primary landing page | Screening consequence |
|---|---|---|
| Dyakov and Fedorov, *Geometry, kinematics and dynamics of the Mecanum wheel* (2024/online 2025) | [Publisher record](https://journal.hep.com.cn/2074-0530/EN/10.17816/2074-0530-629873) | Mecanum contact, motion and drive-torque modeling are established; the platform alone cannot be claimed as control novelty. |
| Trepella et al., *Navigating the Crowd: Non-linear MPC with Social Forces Dynamics* (2026) | [Accepted IROS version](https://arxiv.org/abs/2607.10374) | SFM-NMPC, multiple baselines, ablation, 30 repetitions per scenario and a real-time execution report set a stronger benchmark/evaluation bar. |
| *Crowd navigation in a multi-room environment* (2026) | [Frontiers full text](https://doi.org/10.3389/frobt.2026.1812386) | LiDAR/RGB-D sensing, human-state prediction, MPC safety constraints and TIAGo experiments already exist; the present work must isolate its CCA interface and use direct sensor provenance. |
| *HumAIN: Human-Aware Implicit Social Robot Navigation* (2026) | [arXiv record](https://arxiv.org/abs/2607.07357) | Pose/social-cue learning and planning representations are active prior art; YOLO26s-pose and LSTM remain interfaces rather than standalone novelty. |
| Chen et al., *Integrating self-attention and LSTM into TD3 for robust mobile robot navigation in dynamic environments* (2026) | [Scientific Reports record](https://doi.org/10.1038/s41598-026-45819-0) | LSTM inside a reinforcement-learning navigation policy is a nearby learning baseline; it further rules out LSTM/RL integration as standalone novelty. Abstract-level only until Zotero/full-text review. |

The research-gap note is therefore unchanged: the falsifiable question is the
matched safety–tracking–feasibility trade-off of the stated CCA interface under
fixed clearance, fixed total allowance, and fixed global-path/local-trigger
rules. No “first”, exhaustive-coverage, or superiority claim is promoted from
this search refresh.

## Search refresh — 2026-08-12T15:15:14Z

The following discovery queries were executed in ordinary Google-oriented web
search and in a Google-Scholar-oriented search pass:

```text
context-aware nonlinear model predictive control mobile robot human-aware navigation LSTM 2025
Mecanum wheel nonlinear model predictive control mobile robot 2025
YOLO26 pose Ultralytics official documentation
context-aware risk allocation chance-constrained NMPC human robot
LSTM uncertainty chance-constrained MPC human robot
site:scholar.google.com/scholar "Mecanum" "nonlinear model predictive control"
site:scholar.google.com/scholar "context-aware" mobile robot navigation LSTM
site:scholar.google.com/scholar "human-aware navigation" "model predictive control"
```

The Scholar-oriented connector returned an author-profile page rather than a
stable result list for the first pass. It is therefore recorded as a discovery
attempt only; no Scholar coverage or citation-count claim is made. The
technical records admitted for screening were opened at authoritative pages:

- [Ultralytics pose documentation](https://docs.ultralytics.com/tasks/pose),
  which documents YOLO26 pose outputs (boxes, 17 keypoints and confidence) and
  the COCO pose validation interface;
- [Ultralytics COCO8-Pose dataset](https://docs.ultralytics.com/datasets/pose/coco8-pose),
  which identifies the eight-image, four-train/four-validation package as a
  debugging cohort rather than a generalization benchmark;
- [Ultralytics YOLO26 model page](https://docs.ultralytics.com/models/yolo26),
  which is treated as tool/version documentation rather than research novelty;
- [NMPC-Augmented Visual Navigation and Safe Learning Control](https://arxiv.org/abs/2601.00609),
  retained as a nearby 2026 preprint comparator for visual pose estimation,
  NMPC and learned control, not as evidence for the present allocator;
- [Mecanum-drive modelling in Isaac Sim](https://arxiv.org/abs/2510.10273),
  retained as a platform/modelling boundary source, not as a claim of control
  novelty.

This pass does not change the research gap. It reinforces the existing rule:
search results discover candidates, while only checked DOI/publisher/arXiv
records support a gap or claim. A new refresh is required before the next gap,
model, baseline, metric or evidence-freeze decision, and at least weekly while
the project remains active.

## Additional gap stress-test — 2026-08-12T15:24Z

A second Google/Google-Scholar-oriented pass used the following exact queries:

```text
"risk allocation" "chance constraints" MPC mobile robot human 2026
"fixed total" chance constraint allocation nonlinear MPC
"context-aware" risk allocation nonlinear model predictive control robot
site:scholar.google.com/scholar "risk allocation" "chance constraints" MPC robot
```

The [Barbosa--Löfberg preprint](https://arxiv.org/abs/2604.04602) explicitly
optimizes online risk allocation under a total allowance while selecting
feedback policies. It is already recorded as NW-16; this refresh therefore
does not create a new novelty claim. The [ARMS preprint](https://arxiv.org/abs/2601.16686)
also confirms that LSTM, context-aware control switching, RL and an MPC safety
filter are a nearby integrated stack. The [DARKO RA-L record](https://doi.org/10.1109/LRA.2024.3461552)
confirms that body pose/activity context has already been used in human-aware
MPC with simulation and robot experiments.

The resulting decision is unchanged: the project must be framed as a
controlled empirical comparison of a bounded, auditable CCA interface on the
stated position-state Mecanum platform with body-velocity commands. No “first”, “unoccupied” or
“risk-allocation novelty” statement is admitted from this search.

## Search refresh — Google and Google Scholar-oriented — 2026-08-12 (evaluation stress test)

The next discovery pass used the following queries:

```text
2026 human-aware navigation nonlinear model predictive control mobile robot LSTM chance constraints
2026 Mecanum wheel torque nonlinear model predictive control robot navigation benchmark
site:scholar.google.com/scholar 2026 human-aware navigation model predictive control LSTM
site:scholar.google.com/scholar Mecanum torque NMPC mobile robot
```

The Scholar-oriented results were treated as discovery only; no coverage or
citation-count claim is made. Candidate records were checked against an ACM
DOI/author version or a publisher full-text page:

| Candidate | Primary landing page | Screening consequence |
|---|---|---|
| Stratton et al., *How Human Motion Prediction Quality Shapes Social Robot Navigation Performance in Constrained Spaces* (HRI 2026) | [ACM/IEEE DOI](https://doi.org/10.1145/3757279.3788664); [author version](https://arxiv.org/abs/2601.09856) | A two-site, two-platform, 80-participant study reports that ADE alone does not predict navigation or human-experience outcomes and that cooperation cannot be assumed. Context calibration/OOD and closed-loop outcomes must remain separate. |
| Alfayizi, *Traction-Adaptive Super-Twisting Sliding Mode Control for Mecanum Robotaxi Tracking under Wheel-Speed Constraints* (2026) | [publisher full text](https://www.iieta.org/journals/jesa/paper/10.18280/jesa.590406) | Mecanum traction variation, wheel-speed feasibility, terminal error, saturation and control-activity trade-offs are already benchmarked. Torque/actuator metrics remain mandatory; the platform is not algorithmic novelty. |
| Akhtyamov et al., *Chance-constrained neural MPC under uncontrollable agents via sequential convex programming* (2026) | [ScienceDirect record](https://www.sciencedirect.com/science/article/abs/pii/S1751570X26000774) | Robust conformal uncertainty bounds inside chance-constrained MPC further reject any broad learned-prediction/safety novelty claim. |

The official [YOLO26 model documentation](https://docs.ultralytics.com/models/yolo26)
and [pose task documentation](https://docs.ultralytics.com/tasks/pose) were also
checked. They verify the `-pose` tool interface, 17 COCO keypoints and confidence
outputs. They do not verify the study's detector accuracy, target-hardware
latency or control contribution; those remain protocol-specific measurements.

No candidate changes the narrow gap. The active question remains a matched
empirical comparison of a transparent fixed-budget CCA interface under fixed
clearance and fixed global-path/local-trigger rules, with context calibration,
control metrics and physical provenance reported separately.

## Linked screening notes

- [[03_Literature/Sources/source-stratton-hmp-navigation-2026]]
- [[03_Literature/Sources/source-alfayizi-mecanum-2026]]
- [[03_Literature/Sources/source-ultralytics-yolo26-pose]]

## Search refresh — 2026-08-13 — actuator uncertainty and risk-aware planning

The next Google/Google-Scholar-oriented pass used the following queries:

```text
2026 Mecanum robot actuator uncertainty wheel slip observer control
2026 risk-aware social MPC chance constraints mobile robot
2026 Mecanum MPC tracking benchmark wheel-speed constraints
```

Discovery results were checked against publisher or DOI landing pages. They are
screening updates only; they do not represent Scopus, Web of Science, IEEE
Xplore or systematic-review coverage, and they are not yet admitted to Zotero
because the local Zotero API was unavailable during this session.

| Candidate | Primary landing page | Screening consequence |
|---|---|---|
| Luna et al., *Robust unknown input estimation for a mecanum-wheels omnidirectional mobile robot modeled as a convex qLPV system* (2026) | [European Journal of Control, DOI 10.1016/j.ejcon.2026.101466](https://doi.org/10.1016/j.ejcon.2026.101466) | Wheel slip, actuator effectiveness loss, disturbances and sensor noise are treated as coupled uncertainty sources; the experiment must report actuator/model mismatch separately from CCA allocation. |
| Ye and Ren, *SCU-T-MPC: Risk-Aware and Socially Compliant Topological Motion Planning Under Uncertainty* (2026) | [IET Cyber-Systems and Robotics, DOI 10.1049/csy2.70051](https://doi.org/10.1049/csy2.70051) | Chance-constrained social planning and qualitative failure analysis are established nearby; generic risk-aware/social MPC novelty is rejected. |
| Pham and Han, *Consolidated Control Architecture for Mecanum-Wheeled Mobile Robots Using SMO-MPC-PID-Fuzzy Hybridization* (2026) | [Journal of Intelligent & Fuzzy Systems, DOI 10.1177/18758967251394861](https://doi.org/10.1177/18758967251394861) | Mecanum hybrid control, wheel-slip compensation and tracking/control-activity metrics are established; the platform and hybridization cannot be claimed as the CCA contribution. |

The gap remains unchanged and narrower: a matched empirical study of a
transparent fixed-budget CCA interface in position-state Mecanum NMPC with body-velocity commands, with fixed
clearance/global path, explicit local-trigger semantics, context calibration,
actuator uncertainty and separated safety/tracking/runtime outcomes. These
sources strengthen the benchmark and limitation requirements but do not create
a new “first” claim.

### Linked screening notes

- [[03_Literature/Sources/source-luna-mecanum-unknown-input-2026]]
- [[03_Literature/Sources/source-ye-scu-t-mpc-2026]]
- [[03_Literature/Sources/source-pham-mecanum-hybrid-2026]]

## Search refresh — 2026-08-13 (position-state and learning boundary)

The follow-up Google/web pass checked position-level Mecanum control, social
NMPC, model-based RL and uncertainty-aware safety against primary landing pages.
The local Zotero API was reachable, but exact-title searches did not find the
new records; no import was performed without an explicit destination decision.
The screening record is
[[03_Literature/Sources/source-position-state-boundary-20260813]].

The refresh adds no novelty claim. It confirms that position-level Mecanum
control, velocity-command NMPC, RL/social navigation and uncertainty-aware
safety are occupied boundaries. The study therefore keeps the narrow empirical
question: a matched, fixed-budget CCA interface under the six-state
position/body-velocity contract, fixed clearance and fixed-global/local-trigger
path semantics.

## Search refresh — Google and Google Scholar-oriented — 2026-08-13 (risk and benchmark boundary)

The next discovery pass used the following exact queries. Search results were
treated as discovery only; the linked publisher or author records were opened
before recording a screening consequence.

```text
2026 human-aware navigation risk allocation MPC dynamic pedestrians robot chance constraints
2026 Mecanum robot torque model predictive control wheel slip benchmark
2026 self-supervised reinforcement learning human-aware navigation MPC robot
```

The pass does not claim Google Scholar coverage, a database count or a
systematic review. Zotero was unavailable in the current session, so these
records remain screening candidates.

| Candidate | Primary landing page | Screening consequence |
|---|---|---|
| Samavi et al., *SICNav: Safe and Interactive Crowd Navigation Using Model Predictive Control and Bilevel Optimization* (IEEE T-RO, 2025) | [IEEE T-RO record](https://doi.org/10.1109/TRO.2024.3484634) | Zotero full text confirms ORCA/KKT interactive crowd MPC, 500-scenario ORCA/social-force evaluations and an indoor real-robot study; safety and interaction claims cannot be presented as novel in isolation. |
| *Cooperative Gaussian process-based model predictive control for safe multi-agent navigation* (2026) | [Springer full text](https://doi.org/10.1186/s13634-026-01306-2) | Learned residual uncertainty, chance-constrained MPC and ADMM multi-agent coordination strengthen the uncertainty-aware comparator boundary; independent admission and fair reproduction remain open. |
| *Dynamic Risk-Aware MPPI for Mobile Robots in Crowds via Efficient Monte Carlo Approximations* (2025) | [arXiv record](https://arxiv.org/abs/2506.21205) | MPPI is a direct risk-aware sampling baseline for the requested benchmark; fair reproduction and equal compute budget must be checked before use. |
| Liu et al., *Adaptive Reinforcement and Model Predictive Control Switching for Safe Human-Robot Cooperative Navigation* (2026) | [arXiv record](https://arxiv.org/abs/2601.16686) | LSTM/context encoding, RL and an MPC safety filter are already integrated nearby; the stack is not a standalone novelty claim. |

The gap therefore remains an empirical, bounded question about a transparent
fixed-budget interface inside position-state Mecanum NMPC with body-velocity commands. The new records add
stronger interaction, uncertainty and MPPI comparator requirements; they do not
support a new “first” claim.

### Linked screening notes

- [[03_Literature/Sources/source-samavi-sicnav-2026]]
- [[03_Literature/Sources/source-cooperative-gp-mpc-2026]]
- [[03_Literature/Sources/source-dra-mppi-2025]]

## Search refresh — Google and Google Scholar-oriented — 2026-08-13 (risk-map and embedded-control boundary)

The latest discovery pass used the following exact queries:

```text
2026 human-aware navigation model predictive control mobile robot uncertainty risk allocation paper
2026 Mecanum wheel nonlinear model predictive control wheel slip experimental paper
2025 2026 self-supervised human motion prediction LSTM robot navigation uncertainty
2026 risk-aware MPPI human-aware mobile robot navigation chance constraints
```

Search results were treated as discovery only. The records below were opened at
publisher or DOI pages before being added as screening notes; no Google Scholar,
Scopus, Web of Science or IEEE Xplore coverage is claimed.

| Candidate | Primary landing page | Screening consequence |
|---|---|---|
| *A Unified Local Risk Map for Uncertainty-Aware Mobile Robot Navigation in Cluttered and Dynamic Environments* (2026) | [Sensors DOI 10.3390/s26123900](https://doi.org/10.3390/s26123900) | A continuous contextual/uncertainty risk representation is adjacent prior art; risk maps and uncertainty-aware navigation are not standalone CCA novelty. |
| Gnimady et al., *Development of an integrated estimation and predictive control framework for safe navigation in mobile robots for industrial environments* (2026) | [Springer DOI 10.1007/s11370-025-00661-7](https://doi.org/10.1007/s11370-025-00661-7) | LiDAR/RADAR/IMU estimation, MPC obstacle avoidance, embedded timing and real-robot validation are already reported; the study must isolate CCA and disclose its own target-hardware timing. |
| *Motion planning with uncertainty in human-populated environments via model-based reinforcement learning for social robot navigation* (2026) | [ScienceDirect record](https://www.sciencedirect.com/science/article/pii/S0925231226000998) | Uncertainty-aware model-based RL is a nearby learning comparator; self-supervised/RL navigation is not a standalone contribution. |
| Chen et al., *Integrating self-attention and LSTM into TD3 for robust mobile robot navigation in dynamic environments* (2026) | [Scientific Reports DOI 10.1038/s41598-026-45819-0](https://doi.org/10.1038/s41598-026-45819-0) | LSTM plus learning-based dynamic navigation is established; LSTM remains an interface inside CCA, not the novelty claim. |
| *Collaborative Optimization Framework of Interactive Motion Planning and Emergency Protection Control for Human-Robot Interaction* (2026) | [IEEE RA-L DOI 10.1109/LRA.2026.3671537](https://doi.org/10.1109/LRA.2026.3671537) | Stochastic MPC, scenario-tree interaction and emergency protection are boundary prior art; interaction/fallback cannot be claimed as new by integration alone. |

Linked source notes:

- [[03_Literature/Sources/source-unified-risk-map-2026]]
- [[03_Literature/Sources/source-integrated-estimation-nmpc-2026]]
- [[03_Literature/Sources/source-chen-lstm-td3-2026]]
- [[03_Literature/Sources/source-collaborative-emergency-protection-2026]]

The narrow gap remains an empirical question about a transparent fixed-budget
CCA interface inside position-state Mecanum NMPC with body-velocity commands under fixed clearance, fixed
global path and explicit local-trigger rules. This refresh further rejects
generic risk-map, LSTM/RL, multisensor-MPC and emergency-protection novelty.

## Dataset discovery refresh — 2026-08-13

The following exact queries were used to identify a real context source for the
LSTM/overlay protocol:

```text
JRDB dataset download pedestrian trajectories robot view official
Oxford Indoor Human Motion dataset download robot RGB-D official
public pedestrian video dataset images trajectories license CC BY robot navigation
```

The authoritative landing pages identified Oxford-IHM, JRDB/JRDB-Pose, SiT,
NavWareSet and uB-VisioGeoloc. Their access, license and runtime implications
are recorded in [[03_Literature/Sources/source-dataset-candidates-2026]]. No raw
dataset was downloaded or frozen in this pass. The active no-ROS boundary is
unchanged: only a direct, provenance-preserving CSV/JSON extraction can enter
the experiment pipeline.

## Search spot-check — 2026-08-13 (continuation)

A follow-up Google-oriented pass and a Google-Scholar-oriented discovery attempt
used the exact queries below:

```text
2026 human-aware navigation model predictive control dynamic pedestrians robot risk allocation
2026 Mecanum robot torque model predictive control wheel slip
2026 self-supervised human-aware navigation reinforcement learning robot MPC
2026 chance-constrained MPPI human-aware mobile robot navigation
```

The Scholar-oriented query returned no stable result list in this session, so it
is recorded only as a discovery attempt. Ordinary web results were checked
against authoritative landing pages. The prominent records were already
represented in the focused notes: ARMS (LSTM plus RL/MPC safety filtering),
SCU-T-MPC (risk-aware social MPC), the 2026 Mecanum unknown-input study, the
HRI prediction-quality study, and the risk-aware MPPI preprint. No additional
source was admitted, and no claim of exhaustive Google Scholar coverage was
made. The gap and comparator requirements therefore remain unchanged.

Related source notes: [[03_Literature/Sources/source-liu-arms-mpc]] ·
[[03_Literature/Sources/source-ye-scu-t-mpc-2026]] ·
[[03_Literature/Sources/source-luna-mecanum-unknown-input-2026]] ·
[[03_Literature/Sources/source-stratton-hmp-navigation-2026]] ·
[[03_Literature/Sources/source-dra-mppi-2025]]

## Search spot-check — 2026-08-13 (new interaction and control boundary)

The next discovery pass used these exact queries:

```text
2026 context-aware risk allocation model predictive control human-aware mobile robot primary paper
2026 chance-constrained MPC human-aware navigation risk allocation primary paper
2026 torque-input Mecanum nonlinear model predictive control robot primary paper
2026 LSTM self-supervised pedestrian motion prediction robot navigation primary paper
```

The primary records checked included the HRI 2026 prediction-quality study, the
2026 LSTM--TD3 navigation study, the 2026 collaborative optimization and
emergency-protection framework, and recent chance-constrained MPC/CBF boundary
papers. The collaborative framework is recorded as a screening note in
[[03_Literature/Sources/source-collaborative-emergency-protection-2026]]. The
IEEE page required a JavaScript challenge, so its entry remains
publisher-metadata/abstract-level and was not admitted to Zotero or the
nearest-work matrix. This pass adds no support for a broad “interactive MPC,”
“LSTM navigation,” “chance-constrained safety,” or “Mecanum control” novelty
claim; the narrow fixed-budget CCA position-state NMPC question is unchanged.

The Google-Scholar-oriented results were not treated as exhaustive coverage,
and no subscription-database coverage was inferred. No paper file was edited.

## Search spot-check — 2026-08-13 (current web recheck)

To keep the gap current, a further primary-source search used these exact
queries:

```text
"context-aware" risk allocation nonlinear model predictive control mobile robot 2025 2026
"torque" Mecanum nonlinear model predictive control mobile robot 2025 2026
self-supervised LSTM pedestrian direction prediction robot navigation 2025 2026
risk-aware MPPI mobile robot crowds 2025 2026
```

The following records were checked only at their authoritative landing pages
and remain screening-only; they were not added to the frozen citation export:

| Candidate | Primary landing page | Screening consequence |
|---|---|---|
| Trevisan et al., *Dynamic Risk-Aware MPPI for Mobile Robots in Crowds via Efficient Monte Carlo Approximations* (IROS 2025) | [IEEE record](https://xplorestaging.ieee.org/document/11246822/) | Confirms that risk-aware MPPI and real-robot crowd navigation are direct comparator boundaries. |
| Liu et al., *Adaptive Reinforcement and Model Predictive Control Switching for Safe Human-Robot Cooperative Navigation* (2026) | [arXiv record](https://arxiv.org/abs/2601.16686) | Confirms that RL/MPC safety-filter integration and context-aware switching are nearby; they cannot be claimed as standalone novelty. |
| *Pedestrian trajectory prediction model based on self-supervised spatiotemporal graph network* (2025) | [ScienceDirect record](https://doi.org/10.1016/j.iswa.2025.200533) | Self-supervised pedestrian prediction is adjacent prior art; the current study keeps perception as a context interface, while any CCA-NMPC future-position sequence remains internal and is not exported or drawn. |
| *Integrating self-attention and LSTM into TD3 for robust mobile robot navigation in dynamic environments* (2026) | [Scientific Reports record](https://doi.org/10.1038/s41598-026-45819-0) | LSTM plus learning-based navigation is already reported; LSTM remains an interface inside CCA rather than the novelty claim. |

This recheck does not change the narrow gap: a matched empirical evaluation of
a transparent fixed-budget CCA interface inside position-state Mecanum NMPC with body-velocity commands,
with fixed global path, conflict-triggered local update, and separated safety,
tracking and computation outcomes. It also does not constitute Google Scholar,
Scopus, Web of Science or IEEE Xplore coverage.

## Search spot-check — 2026-08-13 (current HRI/control refresh)

The next exact queries were:

```text
2026 context-aware risk allocation chance constrained NMPC mobile robot human navigation
2026 current-context pedestrian direction prediction robot local path MPC no trajectory
2026 Mecanum torque NMPC human-aware navigation experimental robot
```

The primary landing pages rechecked were the HRI 2026 study by Stratton et al.,
the accepted SFM--NMPC work by Trepella et al., ARMS, RCSP and the 2026 neural
chance-constrained MPC paper. Their consequences are boundary conditions rather
than new claims:

| Record | Screening consequence |
|---|---|
| Stratton et al., HRI 2026, [DOI 10.1145/3757279.3788664](https://doi.org/10.1145/3757279.3788664) | Closed-loop and human-centred outcomes cannot be replaced by ADE/FDE alone; cooperation and comfort must be measured separately when applicable. |
| Trepella et al., SFM--NMPC, [arXiv:2607.10374](https://arxiv.org/abs/2607.10374) | Human-aware NMPC with embedded social dynamics, repeated scenarios and ablation is established nearby; it sets a benchmark-design bar, not CCA allocator novelty. |
| Han and Zhu, RCSP, [arXiv:2605.26348](https://arxiv.org/abs/2605.26348) | Risk-sensitive local planning under plausible short-horizon futures is adjacent prior art; the current scope still uses a current-context footprint and no human future path. |
| *Chance-constrained neural MPC under uncontrollable agents*, [DOI 10.1016/j.nahs.2026.101751](https://doi.org/10.1016/j.nahs.2026.101751) | Learned prediction, distribution shift and robust chance constraints are already addressed nearby; probability claims in this project remain model-internal and calibration-gated. |

No source from this pass was imported into the frozen Zotero export, and no
source supports a broad claim of novelty for LSTM, risk-aware MPC, human-aware
NMPC or Mecanum control. The narrow gap and comparator requirements remain
unchanged.

## Search spot-check — 2026-08-13 (Google/Scholar refresh: temporal learning boundary)

The next discovery pass used Google and a Google-Scholar-oriented search with
the following exact queries:

```text
2026 LSTM reinforcement learning mobile robot navigation dynamic pedestrians
2026 intention-aware pedestrian direction prediction robot navigation
2026 self-supervised pedestrian motion prediction robot control
```

Scholar did not expose a stable, reproducible result list in this session; the
records below were therefore checked at their publisher landing pages and are
screening evidence only.

| Record | Primary landing page | Screening consequence |
|---|---|---|
| Chen et al., *Integrating self-attention and LSTM into TD3 for robust mobile robot navigation in dynamic environments* (Scientific Reports, 2026) | [Publisher record](https://doi.org/10.1038/s41598-026-45819-0) | LSTM-plus-learning navigation with simulation and real-robot evaluation is already reported; LSTM cannot be presented as the sole novelty or as a guarantee of safety. |
| Liu et al., *Intention-Aware Diffusion Model for Pedestrian Trajectory Prediction* (AAAI 2026) | [AAAI record](https://doi.org/10.1609/aaai.v40i22.38912) | Direction/magnitude separation and multimodal intention prediction are established nearby; the present scope remains deliberately narrower, using causal context for CCA-NMPC's internal chance rows without exporting a human path. |

The refresh strengthens the exclusion boundary around end-to-end RL,
trajectory generation and intention forecasting. It does not alter the narrow
research question: a matched empirical evaluation of a transparent fixed-budget
CCA interface inside position-state Mecanum NMPC with body-velocity commands, with a fixed global path,
conflict-triggered local update, and separately reported safety, tracking and
computation outcomes. No record was imported into the frozen Zotero export, and
no manuscript claim was changed.

## Search spot-check — 2026-08-13 (protocol continuation: control and plant boundary)

The protocol continuation used these exact discovery queries:

```text
2026 human-aware nonlinear model predictive control mobile robot uncertainty risk allocation pedestrian navigation
2026 Mecanum wheel torque-input nonlinear model predictive control physical experiment
2026 LSTM self-supervised pedestrian motion prediction mobile robot context-aware navigation
2026 chance-constrained MPC human robot navigation risk allocation
```

Publisher landing pages were checked for the following screening records:

| Record | Primary landing page | Consequence for the active study |
|---|---|---|
| Gravina et al., *Crowd navigation in a multi-room environment* (2026) | [Frontiers DOI 10.3389/frobt.2026.1812386](https://doi.org/10.3389/frobt.2026.1812386) | LiDAR/RGB-D fusion, human-state estimation, MPC/DT-CBF and TIAGo simulation/experiments are established; the CCA interface and Mecanum plant must be isolated. |
| Luna et al., *Robust unknown input estimation for a mecanum-wheels omnidirectional mobile robot* (2026) | [EJCON DOI 10.1016/j.ejcon.2026.101466](https://doi.org/10.1016/j.ejcon.2026.101466) | Actuator faults, slip, disturbances and sensor/model uncertainty are direct plant-boundary concerns; they strengthen the actuator-mismatch reporting requirement. |
| Chen et al., *Integrating self-attention and LSTM into TD3* (2026) | [Scientific Reports DOI 10.1038/s41598-026-45819-0](https://doi.org/10.1038/s41598-026-45819-0) | LSTM plus learning-based navigation is already nearby prior art; LSTM remains a CCA interface rather than a standalone novelty claim. |
| *Motion planning with uncertainty in human-populated environments via model-based reinforcement learning* (2026) | [Neurocomputing DOI 10.1016/j.neucom.2026.132702](https://doi.org/10.1016/j.neucom.2026.132702) | Probabilistic pedestrian prediction and model-based RL are adjacent alternatives; the active scope still uses current context and does not generate a human future path. |

This pass is discovery/screening only. No new record was imported into the
frozen Zotero export, no source was promoted to quantitative nearest-work
evidence, and no manuscript file was edited.

## Search spot-check — 2026-08-13 (latest risk-allocation and context-learning refresh)

The latest Google-oriented and Google-Scholar-oriented discovery queries were:

```text
2026 context-aware MPC human navigation risk allocation CVaR robot
2026 Bonferroni risk allocation chance constraint mobile robot human
2026 context-aware human preference navigation model predictive control
2026 LSTM MPC human robot navigation real experiment
```

The Scholar-oriented results were treated as discovery only; the records below
were checked at publisher or author landing pages and remain screening-only.

| Record | Primary landing page | Screening consequence |
|---|---|---|
| *SHARP: A Risk-Constrained Transformer with Closed-Form CVaR Safety Masks for Multi-Robot Task Allocation in Human-Shared Warehouses* (2026) | [MDPI article](https://doi.org/10.3390/math14122096) | Gaussian pedestrian beliefs, fixed closest-approach directions, Bonferroni allocation and a closed-form CVaR safety mask are already combined; the present allocator cannot claim generic closed-form risk/CVaR novelty. |
| *Interpreting Context-Aware Human Preferences for Multi-Objective Robot Navigation* (2026) | [arXiv record](https://arxiv.org/abs/2603.17510) | VLM/LLM preference extraction and MORL deployment establish a broader context-adaptation boundary; this is not a direct torque-NMPC comparator, but it rules out generic “context-aware adaptation” novelty. |
| *Adaptive Reinforcement and Model Predictive Control Switching for Safe Human-Robot Cooperative Navigation* (2026) | [arXiv record](https://arxiv.org/abs/2601.16686) | LSTM temporal encoding, learning-based switching and an MPC safety filter remain established nearby; ARMS is retained as a boundary comparator rather than a fixed-budget allocator. |

The gap is unchanged: only a bounded matched empirical comparison of the
transparent fixed-budget CCA interface inside position-state Mecanum NMPC with body-velocity commands remains
open for testing. This refresh does not claim exhaustive Google Scholar,
Scopus, Web of Science or IEEE Xplore coverage, and no manuscript file was
edited.

## Search spot-check — 2026-08-13 (tool and comparator refresh)

The latest web check used these exact queries:

```text
site:docs.ultralytics.com/tasks/pose YOLO26 pose Ultralytics
context-aware chance-constrained model predictive control human robot navigation 2025
risk-aware MPPI human-aware navigation real robot 2025
```

The official Ultralytics pose documentation confirms that YOLO26 pose outputs
bounding boxes and 17 COCO keypoints; this is recorded as a perception-tool
interface only, not detector performance or a control novelty claim. The DRA-
MPPI IROS 2025 record confirms a direct risk-aware MPPI comparator with
simulation and real-robot evaluation. These checks reinforce the existing
protocol requirement for a matched MPC/NMPC/DWA/MPPI benchmark and hardware
latency evidence, but they do not change the narrow CCA position-state NMPC gap.
No record was imported into the frozen Zotero export, and no manuscript file
was edited.

## Search spot-check — 2026-08-13 (control, uncertainty and Mecanum hardware refresh)

The latest Google-oriented discovery pass used the following exact queries:

```text
context-aware model predictive control mobile robot human uncertainty 2025
risk-aware MPPI CVaR mobile robot human navigation
Mecanum mobile robot model predictive control hardware experiment 2024 2025
uncertainty-aware predictive control barrier function human robot 2025
```

The Scholar-oriented result list was not stable enough to treat as a database
count; the records below were checked at primary publisher or author pages and
remain screening-only.

| Record | Primary landing page | Screening consequence |
|---|---|---|
| *Risk-Aware Model Predictive Path Integral Control Using Conditional Value-at-Risk* (ICRA 2023) | [IEEE record](https://ieeexplore.ieee.org/abstract/document/10161100) | CVaR-based risk-aware MPPI is a direct comparator family; the present work must not present risk-aware sampling control as an unoccupied novelty. |
| *Sliding mode observer-based model predictive tracking control for Mecanum-wheeled mobile robot* (2024) | [ScienceDirect record](https://www.sciencedirect.com/science/article/abs/pii/S0019057824002672) | Mecanum MPC tracking under disturbances/model uncertainty is established plant-boundary prior art; torque-input and context interface must be evaluated separately. |
| *Model predictive control with residual learning and real-time disturbance rejection: Design and experimentation* (2025) | [ScienceDirect record](https://www.sciencedirect.com/science/article/abs/pii/S0967066125003491) | A Mecanum hardware study with learned disturbance rejection reinforces the need for physical calibration, actuator-interface disclosure and measured latency; it does not close the CCA interface gap. |
| *Uncertainty Aware-Predictive Control Barrier Functions: Safer Human Robot Interaction through Probabilistic Motion Forecasting* (2025) | [arXiv record](https://arxiv.org/abs/2508.20812) | Probabilistic forecasting coupled to predictive safety control with real-world HRI evaluation is already reported; uncertainty-aware safety cannot be claimed as the sole novelty. |

The active gap therefore remains deliberately narrow: a matched, provenance-linked
comparison of a transparent fixed-budget CCA interface inside position-state
Mecanum NMPC with body-velocity commands, with a fixed global path and
conflict-triggered local update. This
refresh tightens the comparator and evidence obligations but does not claim
exhaustive Google Scholar, Scopus, Web of Science or IEEE Xplore coverage. No
record was imported into the frozen Zotero export and no manuscript file was
edited.

## Google Scholar spot-check — 2026-08-13 (discovery only)

The requested Scholar-oriented checks were repeated with these queries:

```text
context-aware risk allocation nonlinear model predictive control human-aware robot navigation Mecanum
Mecanum wheel robot nonlinear model predictive control human-aware navigation LSTM
uncertainty-aware predictive control dynamic obstacle avoidance mobile robot
```

The returned pages were author profiles and mixed discovery results rather than
stable publisher records for a directly matched CCA--LSTM--Mecanum study. They
are therefore not counted as primary evidence, not imported into Zotero, and do
not alter the gap. The existing publisher/DOI records above remain the only
screening boundaries used in the current audit. This is a search log, not a
claim of exhaustive Google Scholar coverage.

## Search refresh — 2026-08-13 (risk-aware and real-robot boundary)

The follow-up search checked recent primary landing pages for risk-aware
sampling control, uncertainty-aware safety and closed-loop human navigation:

| Record | Primary landing page | Screening consequence |
|---|---|---|
| Trevisan et al., *Dynamic Risk-Aware MPPI for Mobile Robots in Crowds via Efficient Monte Carlo Approximations* (IROS 2025) | [IEEE DOI record](https://doi.org/10.1109/IROS60139.2025.11246822) | Real-robot and simulation evaluation of collision-probability-aware MPPI makes MPPI a required benchmark family and rules out generic risk-aware navigation novelty. |
| Busellato et al., *Uncertainty Aware-Predictive Control Barrier Functions* (Robotics and Autonomous Systems, 2026) | [Elsevier DOI record](https://doi.org/10.1016/j.robot.2025.105291) | Probabilistic human forecasting coupled with a predictive safety controller and real HRI evaluation already exists; uncertainty alone is not the contribution. |
| Han et al., *DR-MPC: Deep Residual Model Predictive Control for Real-world Social Navigation* (RA-L, 2025) | [University/author publication page](https://leaf.utias.utoronto.ca/publication/han-2024-drmpc/) | Hardware social-navigation results with MPC plus learning reinforce the requirement to separate prediction, control and measured physical evidence. |
| Aslam et al., *Model Predictive Control for Crowd Navigation via Learning-Based Trajectory Prediction* (2025) | [Publisher record](https://www.scitepress.org/PublishedPapers/2025/137104/) | Physical-robot comparison shows open-loop prediction gains do not automatically imply closed-loop navigation gains; both metric families must be reported separately. |

These records tighten the evidence plan but leave the same bounded gap: a
matched, provenance-linked comparison of the transparent fixed-budget CCA
interface inside position-state Mecanum NMPC with body-velocity commands. The refresh is screening-only; no
Zotero item or manuscript file was changed.

## Search refresh — 2026-08-13 (human-centred MPC and Mecanum boundary)

The next Google-oriented discovery pass used these exact queries:

```text
2026 "Mecanum" human-aware nonlinear model predictive control mobile robot experiment
2026 risk-aware model predictive control dynamic pedestrians mobile robot real robot
2026 self-supervised pedestrian context prediction mobile robot LSTM navigation
2026 fixed-budget risk allocation chance-constrained MPC human robot
```

The results below were checked at publisher or authoritative landing pages and
remain screening-only. They do not add a systematic-search count or a Zotero
import.

| Record | Primary landing page | Screening consequence |
|---|---|---|
| Kada et al., *Pedestrian-Aware Control of AMRs Using Model Predictive Speed Control Minimizing Pedestrian Hesitation* (JRSJ, 2026) | [J-STAGE record](https://doi.org/10.7210/jrsj.44.196) | Real AMR--pedestrian crossing experiments and human-centred outcomes reinforce PR40's qualitative/interaction metrics; this is not a CCA allocator or Mecanum torque model. |
| Miyachi et al., *Accompaniment and collision avoidance for a cane-type robot using dynamic cost maps and MPC* (ROBOMECH Journal, 2026) | [Springer record](https://doi.org/10.1186/s40648-026-00345-6) | Real-robot dynamic-obstacle MPC and target selection reinforce the separation of global goal, local update, clearance and physical evidence. |
| Pham and Han, *Consolidated Control Architecture for Mecanum-Wheeled Mobile Robots Using SMO-MPC-PID-Fuzzy Hybridization* (JIFS, 2026) | [SAGE record](https://doi.org/10.1177/18758967251394861) | Mecanum hybrid control and wheel-slip compensation occupy further plant/control space; abstract-level numbers are not reused as results or baseline evidence. |

The bounded gap is unchanged: a matched empirical comparison of the transparent
fixed-budget CCA interface inside position-state Mecanum NMPC with body-velocity commands, with a fixed global
path and conflict-triggered local update. The new records strengthen PR40 and
PR30 evidence requirements but do not justify a broader novelty claim. No
manuscript file was edited.

## Search refresh — 2026-08-13 00:31 UTC (prediction-quality boundary)

A further Google/web pass used the following exact queries:

```text
2025 2026 self-supervised pedestrian motion prediction LSTM robot navigation
2026 human motion prediction quality social robot navigation constrained spaces
2026 context-aware LSTM MPC human robot experimental evaluation
```

The records below are discovery/screening only. They were not imported into
Zotero and do not reopen the archived PR01 workflow.

| Record | Authoritative landing page | Screening consequence |
|---|---|---|
| Stratton et al., *How Human Motion Prediction Quality Shapes Social Robot Navigation Performance in Constrained Spaces* (HRI 2026) | [ACM/IEEE DOI record](https://doi.org/10.1145/3757279.3788664) | Prediction ADE cannot stand in for navigation or human-experience outcomes; PR12 and PR40 must keep prediction, closed-loop performance and qualitative interaction measures separate. See [[03_Literature/Sources/source-stratton-hmp-navigation-2026]]. |
| *Learning Velocity and Acceleration: Self-Supervised Motion Consistency for Pedestrian Trajectory Prediction* (2025 preprint) | [arXiv record](https://arxiv.org/abs/2503.24272) | Self-supervised motion-consistency learning is an adjacent prior-art boundary; the present LSTM remains a current-context interface and must not claim self-supervision itself as novelty. |

This pass reinforces the existing evidence boundary: the contribution, if
supported, must be the matched CCA allocation/control comparison and not the
YOLO instrument, LSTM architecture, self-supervised objective or generic
human-aware navigation claim. No manuscript file was edited.

## Search refresh — 2026-08-13 (no-ROS hardware deployment boundary)

The hardware-oriented Google/web pass checked authoritative vendor or platform
documentation for the requested deployment stack:

| Component | Authoritative record | Design consequence |
|---|---|---|
| Astra-S/OpenNI2 | [Orbbec OpenNI SDK support](https://www.orbbec.com/developers/openni-sdk/), [OpenNI SDK repository](https://github.com/orbbec/OpenNI_SDK/) | Astra-family support and OpenNI2 distribution are documented, but firmware/model and Linux ARM64 compatibility must be recorded from the actual unit; the recorder must fail closed on an unverified SDK/device identity. |
| Astra SDK maintenance boundary | [Orbbec SDK documentation](https://orbbec.github.io/OrbbecSDK/) | The vendor distinguishes legacy OpenNI devices and SDK branches; do not silently substitute SDK v2 for the installed Astra-S/OpenNI2 path. |
| Jetson Orin Nano | [NVIDIA Jetson Orin Nano User Guide](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/index.html) | TensorRT/YOLO26s-pose inference is assigned to the ARM64 Jetson target; the engine manifest must bind JetPack/runtime, GPU and TensorRT fingerprint, as already enforced in code. |
| Raspberry Pi 4 | [Raspberry Pi computer documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html) | RPi4 is treated as a no-ROS recorder/bridge candidate only; actual USB serial/CAN device availability and timing must be measured, not inferred from the board model. |
| N10/N10P serial family | [LSLIDAR N10 manual](https://www.lslidar.com/wp-content/uploads/2024/09/N10.pdf) | Public N10 documentation reports serial configuration details that may differ by N10/N10P revision; the exact N10P firmware/protocol and baud must be read from the supplied unit before enabling capture. |

This refresh does not admit a hardware package, does not establish real-time
performance, and does not change the research gap. It only fixes the deployment
boundary: Jetson is the perception/inference target, RPi4 is a recorder/bridge
candidate, and Astra-S/N10P identity plus calibration remain physical-entry
requirements. No manuscript file was edited and no Zotero item was imported.

## Search refresh — 2026-08-13 (learning-based and neural chance-control boundary)

The next Google/web pass checked recent publisher landing pages for learning-
based planning and neural chance-constrained control. The records remain
screening-only because their full-text/version/retraction checks have not been
added to the bounded Zotero admission set.

| Record | Primary landing page | Screening consequence |
|---|---|---|
| *Motion planning with uncertainty in human-populated environments via model-based reinforcement learning for social robot navigation* (2026) | [ScienceDirect record](https://www.sciencedirect.com/science/article/pii/S0925231226000998) | Model-based RL already occupies learning-based uncertainty-aware social planning; RL cannot be presented as a new pipeline component. If used, it is a comparator/ablation with a fixed compute and data budget. |
| *Chance-constrained neural MPC under uncontrollable agents via sequential convex programming* (2026) | [ScienceDirect record](https://www.sciencedirect.com/science/article/abs/pii/S1751570X26000774) | Neural prediction/control combined with chance constraints is an active boundary; the CCA claim must remain a matched empirical interface comparison and not neural-MPC novelty. |
| *Dynamic Risk-Aware MPPI for Mobile Robots in Crowds via Efficient Monte Carlo Approximations* (IROS 2025) | [IEEE record](https://doi.org/10.1109/IROS60139.2025.11246822) | The required MPPI benchmark has both simulation and physical evidence in the source record; a controller comparison must report safety, compute and failure accounting rather than only path length. |

These records further narrow the defensible contribution to the transparent
fixed-total CCA interface, its LSTM context measurement boundary, and a matched
Mecanum-control evaluation. They do not reopen PR01, do not create a dataset or
model, and do not change any manuscript file.

The read-only Zotero local-API search on 2026-08-13 returned no matching items
for the two new 2026 records. They remain URL-linked screening records and were
not imported without a verified full-text/metadata decision.

## Search refresh — 2026-08-13 (direction-aware embedded perception)

The early-online article [Real-time direction-aware time-to-collision reasoning
with pose-guided light detection and ranging grounding for pedestrian safety on
autonomous ground vehicles](https://doi.org/10.1016/j.engappai.2026.115660)
reports pose-guided LiDAR association, direction-aware TTC reasoning and an
embedded AGV evaluation. It is a screening boundary for the Astra-S/N10P
perception and direction/TTC measurement protocol, not a CCA or Mecanum
position-state contribution. Reported accuracy and frame-rate values are not
imported as evidence; full-text, platform, dataset and pretraining-overlap
checks remain open.

## Search refresh — 2026-08-13 (self-supervised navigation boundary)

The latest Google/web pass rechecked the self-supervised learning boundary with
the exact queries `self-supervised pedestrian motion prediction LSTM robot
navigation 2025 2026` and `self-supervised motion planner dynamic obstacles
real robot 2025`. The following primary landing page was added as screening
provenance only:

| Record | Primary landing page | Screening consequence |
|---|---|---|
| Ghani et al., *Dyna-LfLH: Learning Agile Navigation in Dynamic Environments from Learned Hallucination* (IROS 2025) | [author-maintained paper record](https://www.cs.utexas.edu/~pstone/Papers/bib2html/b2hd-dyna_lflh_icra_2025.html) | Self-supervised motion-planner training with simulation and real-ground-robot evaluation is an adjacent learning boundary; it prevents treating a score loop or self-supervision as the control novelty. The present LSTM remains a current-context component inside CCA; only CCA-NMPC may keep a causal future-position sequence internally, with no image or raw-data path artifact. |

This refresh does not add a Zotero item, dataset, checkpoint or quantitative
claim. It only tightens the requirement to compare the self-supervised context
interface against non-learning baselines and to separate context metrics from
closed-loop position-control outcomes.

## Search refresh — 2026-08-13 (Mecanum hardware and crowd-MPC boundary)

The latest targeted Google/web pass used the queries `2026 human-aware
navigation MPC uncertainty pedestrian robot`, `2025 2026 Mecanum robot position
control model predictive control velocity command`, and `2026 LSTM human
motion prediction robot navigation uncertainty`. The three primary records are
linked in [[03_Literature/Sources/source-2026-mecanum-crowd-control-refresh]].

The refresh adds a recent hardware Mecanum MPC/residual-learning record, a
multisensor crowd-MPC paper with real-robot validation, and an HRI study showing
that prediction error metrics alone do not establish navigation or human
outcomes. The gap remains unchanged but the evidence obligation is stronger:
the paper must isolate the CCA allocation interface, keep downstream safety and
tracking metrics, and report the position/body-velocity hardware boundary.
Exact-title searches in Zotero were run read-only and returned no matching
items; no record was imported and no manuscript file was edited.

## Search refresh — 2026-08-13 (prediction, pedestrian-aware MPC and Mecanum overlap check)

A second targeted pass checked the exact queries `2025 pedestrian trajectory
prediction physical guided LSTM`, `2026 pedestrian aware MPC hesitation AMR`,
and `2026 Mecanum omnidirectional robot experimental validation`. The following
publisher records were added to the same screening note:

| Record | Primary landing page | Screening consequence |
|---|---|---|
| *Pedestrian trajectory prediction via physical-guided position association learning* (2025) | [ScienceDirect](https://doi.org/10.1016/j.jestch.2025.102008) | Learned/physical-guided pedestrian prediction is prior art; prediction architecture is not the claimed control novelty. |
| *Pedestrian-Aware Control of AMRs Using Model Predictive Speed Control Minimizing Pedestrian Hesitation* (2026) | [J-STAGE](https://doi.org/10.7210/jrsj.44.196) | Pedestrian-aware MPC and interaction objectives are prior art; downstream safety and interaction outcomes remain required. |
| *Eight-Wheel Mecanum Omnidirectional Autonomous Mobile Robot: Kinematics, Architecture, and Validation* (2026) | [MDPI](https://doi.org/10.3390/electronics15112441) | Mecanum hardware architecture/validation is prior art; PR30 must bind claims to measured geometry, timing and calibration. |

Exact-title Zotero searches returned no local matches, so no records were
imported. These sources tighten the gap but do not reopen PR01-SLR or alter the
locked manuscript.

## Search refresh — 2026-08-13 (attention-aware perception and interaction data)

The follow-up Google/web pass checked `pedestrian attention mobile robot
collision avoidance 2025`, `robot pedestrian influence dataset 2025`, and the
Wikimedia `People walking` category for the real-image acquisition boundary.
The following records are screening-only:

| Record | Primary landing page | Screening consequence |
|---|---|---|
| Tadano, Tamura and Hirata, *Collision avoidance of mobile robots considering pedestrian attention states* (2025) | [Project/publication page](https://tamlab.jp/en/publication/tadano-robomech2025/) | Attention estimation, uncertainty-aware prediction and cost-map adaptation with a physical mobile platform are adjacent prior art; they do not establish fixed-budget CCA allocation or position-state Mecanum CCA-NMPC. |
| Agrawal et al., *The Robot-Pedestrian Influence Dataset for Learning Distinct Social Navigation Forces* (2025) | [Workshop page](https://motionpredictionicra2025.github.io/) · [paper PDF](https://motionpredictionicra2025.github.io/assets/papers/Agrawal2025.pdf) | Robot type and interaction condition affect pedestrian response; PR11 must retain scene/episode/robot-condition metadata. Dataset access/license and target-platform equivalence remain unverified. |
| Wikimedia Commons `People walking` category | [Category page](https://commons.wikimedia.org/wiki/Category:People_walking) | The category is a source-discovery route for real Internet images; each file still requires page-level license, byte hash, privacy screen and blinded annotation before admission. |

Exact-title Zotero searches for the two research records returned no matches on
2026-08-13. No record was imported, no dataset gate was opened, and no
manuscript file was edited.

## Search refresh — 2026-08-13 (physical crowd-MPC and omnidirectional baselines)

The latest publisher/author-page pass checked four nearby systems: DR-MPC for
real-crowd residual MPC, SI-MPC on a physical robot, a Mecanum A*--velocity-
obstacle system, and a Mecanum RL/local-control system. The records are linked
from [[03_Literature/Sources/source-screening-refresh-20260813]]. They are
screening-only and do not enter a systematic-review count or the final Zotero
citation set. Their common consequence is methodological: separate predictor
error from closed-loop navigation, match the controller/failure denominator,
and bind all timing and safety claims to the supplied hardware.

## Search refresh — 2026-08-14 (four-way control and hardware overlap audit)

The targeted Google/web pass checked four exact titles against primary publisher
or institutional records. The records are screening-only and were not used to
create a paper citation, model, dataset or result.

| Record | Primary record | Boundary consequence |
|---|---|---|
| *OA-MPC: Occlusion-Aware MPC for Guaranteed Safe Robot Navigation with Unseen Dynamic Obstacles* (TCST, DOI `10.1109/TCST.2024.3520462`) | [ETH Research Collection](https://www.research-collection.ethz.ch/entities/publication/72b2797e-eb2e-4b51-a10e-1c71a595837a) · [IEEE DOI](https://doi.org/10.1109/TCST.2024.3520462) | Occlusion-aware safety MPC and physical validation are prior art; the present gap cannot claim unseen-obstacle safety alone and must isolate the CCA context/allocation interface. |
| Wang et al., *Sliding mode observer-based model predictive tracking control for Mecanum-wheeled mobile robot* (ISA Transactions, 2024, DOI `10.1016/j.isatra.2024.05.050`) | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0019057824002672) | Mecanum MPC with disturbance observation and constraint handling is established; the control comparison must include a conventional Mecanum-compatible MPC baseline and must not present Mecanum geometry as novelty. |
| Nguyen et al., *Model-Free Safety Critical Model Predictive Control for Mobile Robot in Dynamic Environments* (IEEE T-IV, 2024, DOI `10.1109/TIV.2024.3389111`) | [IEEE DOI](https://doi.org/10.1109/TIV.2024.3389111) | Model-free safety-critical MPC in dynamic environments is adjacent prior art; a CCA claim requires explicit separation from model-learning, safety filter and predictor contributions. |
| Ma and Corves, *Model Predictive Control-based dynamic movement primitives for trajectory learning and obstacle avoidance* (RAS, 2025, DOI `10.1016/j.robot.2025.105027`) | [RWTH institutional record](https://publications.rwth-aachen.de/record/1011822/) | Learning-plus-MPC obstacle avoidance with real-robot validation is established; a self-supervised score loop or LSTM cannot be presented as the sole novelty and closed-loop Mecanum evidence remains mandatory. |

The narrow defensible gap is therefore unchanged: a transparent fixed-budget
context allocator inside CCA-NMPC for a position-state Mecanum platform, with
LSTM restricted to the context interface and with matched MPC/DWA/MPPI controls,
calibrated perception, and direct hardware evidence. The refresh strengthens
the comparator and claim-boundary requirements; it does not establish a
superiority claim.

Read-only exact-title Zotero searches on 2026-08-14 returned no matching local
items for these four records. No Zotero write was performed; metadata must be
verified and imported only after an explicit bibliographic decision. No
manuscript file was edited.

## Search refresh — 2026-08-14 (current control/perception boundary)

An additional current web pass checked the official YOLO26 pose documentation
and newly published control records. These are screening updates only; they do
not reopen PR01 or create evidence.

| Record | Primary record | Consequence for the study |
|---|---|---|
| Gravina et al., *Crowd navigation in a multi-room environment: a model predictive control framework for mobile robots* (2026, DOI `10.3389/frobt.2026.1812386`) | [Frontiers full text](https://doi.org/10.3389/frobt.2026.1812386) | Multisensor human-state estimation, MPC, safety constraints and real-robot validation are already combined on a TIAGo platform; the present claim must remain the matched CCA interface on the Mecanum position-state plant. |
| Pham and Han, *Consolidated Control Architecture for Mecanum-Wheeled Mobile Robots Using SMO-MPC-PID-Fuzzy Hybridization* (2026, DOI `10.1177/18758967251394861`) | [SAGE record](https://doi.org/10.1177/18758967251394861) | Mecanum control architecture, disturbance/slip compensation and MATLAB validation are occupied prior art; Mecanum geometry and MPC cannot be novelty claims by themselves. |
| *Ultralytics YOLO26* and *Pose Estimation with Ultralytics YOLO* | [model documentation](https://docs.ultralytics.com/models/yolo26) · [pose documentation](https://docs.ultralytics.com/tasks/pose) | YOLO26s-pose is a documented perception interface with boxes/keypoints/confidence; the documentation does not establish target-camera accuracy, latency or robot real-time performance. Those remain measurement gates. |

The narrow gap is unchanged: a transparent fixed-budget context interface
inside CCA-NMPC, evaluated against matched MPC/NMPC/DWA/MPPI conditions with
separate perception, closed-loop and hardware evidence. Exact-title Zotero
searches were read-only and returned no local match for the new control records;
no citation, model, dataset or manuscript was changed.

## Search refresh — 2026-08-14 (hardware Mecanum and multisensor MPC overlap)

A further publisher-focused pass checked recent hardware and embedded-control
records. These entries are screening-only; they do not change the locked gap or
open an evidence gate.

| Record | Primary record | Boundary consequence |
|---|---|---|
| *Model predictive control with residual learning and real-time disturbance rejection: Design and experimentation* (2025) | [ScienceDirect record](https://www.sciencedirect.com/science/article/abs/pii/S0967066125003491) | Real indoor/outdoor Mecanum experiments with residual learning and disturbance observation occupy the hardware-learning overlap; the present work must not claim Mecanum hardware validation or learning-based disturbance rejection as its novelty. |
| Gnimady et al., *Development of an integrated estimation and predictive control framework for safe navigation in mobile robots for industrial environments* (2026) | [Springer full text](https://doi.org/10.1007/s11370-025-00661-7) | LiDAR/RADAR/IMU fusion, MPC, dynamic obstacles, embedded execution and real experiments are already combined; the defensible distinction remains the CCA fixed-budget context interface on the specified Mecanum position-state plant. |
| Cipriano, Oriolo and Cherubini, *Singularity-free trajectory tracking for steerable wheeled mobile robots* (2025) | [IEEE RA-L DOI](https://doi.org/10.1109/LRA.2025.3564209) | Efficient real-time NMPC for an omnidirectional wheeled platform is adjacent control prior art; real-time iteration and tracking alone cannot be claimed as the contribution. |

The refresh reinforces the same claim discipline: compare against matched
MPC/NMPC/DWA/MPPI, report perception and controller timing separately, retain
complete sensor provenance, and reserve any safety/performance superiority claim
for a frozen real-data campaign. Exact-title Zotero matching was read-only;
no item was imported and no manuscript file was edited.

## Search refresh — 2026-08-14 (real-robot evaluation design and MPPI overlap)

This focused pass checked current real-robot evaluation and Mecanum/MPPI
overlap. The records below remain screening-only and are used to sharpen the
protocol, not to populate the manuscript or an evidence registry.

| Record | Primary record | Boundary consequence |
|---|---|---|
| *Accompaniment and collision avoidance for a cane-type robot using dynamic cost maps and MPC* (2026) | [ROBOMECH Journal](https://doi.org/10.1186/s40648-026-00345-6) | A real-robot dynamic-obstacle study reports LiDAR-based state estimation, safety distance and end-to-end MPC timing; the present protocol should retain separate clearance, completion and controller-latency measures rather than report a single success rate. |
| Pham et al., *Safe and Efficient Mobile Robot Navigation using Sampling-based Optimal Control with Barrier Function Constraints* (2025/2026 record) | [Journal of Robotics and Control](https://doi.org/10.18196/jrc.v6i6.27770) | Mecanum MPPI/CBF simulation is adjacent prior art; MPPI must remain a matched baseline and CCA cannot claim generic sampling-based safety novelty. |
| *Trajectory tracking control of omni-directional mobile robots: A HOFA-LESO based approach* (2026) | [ScienceDirect](https://doi.org/10.1016/j.robot.2026.105492) | Mecanum/omnidirectional disturbance rejection with simulation and experiment occupies the tracking-control overlap; tracking error alone is insufficient to establish a context-aware navigation contribution. |
| Muhammed, Nada and El-Hussieny, *Real-time decentralized model predictive control for cooperative multi-robot object transport* (2026) | [Scientific Reports](https://doi.org/10.1038/s41598-026-41881-w) | Physical MPC evaluation with vision and sensor fusion demonstrates a useful reporting pattern, but the platform is differential-drive and the ROS 2 stack is not evidence for this no-ROS Mecanum pipeline. |

The research gap is unchanged. The required confirmatory design must report
matched controller denominators, minimum clearance, collision/near-miss counts,
goal completion, path error, command latency and sensor timing separately. No
quantitative claim from these external records is transferred to this project.
Exact-title Zotero searches remain read-only; no item was imported and no
manuscript file was edited.

## Search refresh — 2026-08-14 (uncertainty-aware MPC and Mecanum benchmark check)

An additional Google/Google-Scholar-oriented pass used the following queries:

```text
2025 uncertainty-aware MPC dynamic obstacle prediction mobile robot chance constraint
2025 Mecanum robot MPC obstacle avoidance hardware experiment
2025 holonomic robot proximal gradient MPC Mecanum
2025 social robot navigation constrained optimization uncertainty MPC real world
```

The Scholar-oriented results were used for discovery only. Each record below
was checked at a publisher or institutional landing page; no database coverage,
citation count or systematic-review total is inferred.

| Record | Primary record | Boundary consequence |
|---|---|---|
| *Trajectory Planning with Model Predictive Control for Obstacle Avoidance Considering Prediction Uncertainty* (IFAC, 2025) | [ScienceDirect record](https://doi.org/10.1016/j.ifacol.2025.10.245) | Stochastic dynamic-obstacle prediction and uncertainty-aware MPC are already reported; the present study must distinguish its fixed-budget CCA interface from the prediction model and report calibration separately. |
| *Efficient avoidance of ellipsoidal obstacles with model predictive control for mobile robots and vehicles* (Mechatronics, 2025) | [ScienceDirect full text](https://doi.org/10.1016/j.mechatronics.2025.103386) | Ellipsoidal geometry, dynamic obstacles and a real wheeled-robot experiment occupy the geometric MPC/safety overlap; the ellipse--disk derivation cannot be claimed as standalone novelty. |
| *Social robot navigation through constrained optimization: a comprehensive study of uncertainty-based objectives and constraints in the simulated and real world* (RAS, 2025) | [ScienceDirect record](https://doi.org/10.1016/j.robot.2024.104830) | Simulation/real comparison of uncertainty-aware social MPC establishes the evaluation bar; context accuracy, navigation outcomes and uncertainty effects must remain separate estimands. |
| Lopez Hernandez et al., *Proximal Gradient-Based Model Predictive Control for Obstacle Avoidance in Holonomic Robots* (CCE, 2025) | [IEEE DOI record](https://doi.org/10.1109/CCE67728.2025.11272001) | A holonomic/Mecanum MPC baseline and computational-efficiency comparison are nearby prior art; controller comparison must use matched maps, constraints and compute budgets. |
| *Model Predictive Control for a Mecanum-wheeled Robot Navigating among Obstacles* (IFAC, 2021) | [ScienceDirect record](https://doi.org/10.1016/j.ifacol.2021.08.533) | Mecanum dynamics, actuator response and nonlinear obstacle constraints are established; platform dynamics are background, not the CCA contribution. |

The narrow gap remains unchanged: an auditable fixed-budget context allocator
inside position-state CCA-NMPC, with LSTM limited to the causal context interface,
matched MPC/NMPC/DWA/MPPI baselines, and separate perception, controller and
hardware evidence. The new records strengthen PR21 comparator fairness and
PR40 metric separation; they do not support a first, exhaustive or superiority
claim. Exact-title Zotero matching remains read-only and no manuscript file was
edited.

## Search refresh — 2026-08-14 (context, learning and closed-loop safety)

This refresh used Google/Google-Scholar-oriented discovery with the following
queries, followed by primary landing-page checks:

```text
Google Scholar 2025 human-aware navigation chance-constrained MPC dynamic pedestrians robot
Google Scholar 2024 2025 context-aware MPC social navigation human prediction robot
2025 self-supervised reinforcement learning human-aware robot navigation model predictive control
```

| Record | Primary record checked | Updated boundary |
|---|---|---|
| Stefanini et al., *Efficient Context-Aware Model Predictive Control for Human-Aware Navigation* (RA-L, 2024) | [DARKO publication record](https://darko-project.eu/publications/2024-2/efficient-context-aware-model-predictive-control-for-human-aware-navigation/) · DOI `10.1109/LRA.2024.3461552`; Zotero `8T4BRJA4` | Context from 3-D pose, velocity and activity already enters MPC and is evaluated in simulation and on a robot. “Context-aware MPC” is therefore not a novelty claim; the remaining testable delta must be the transparent fixed-total allocation interface and matched position-state Mecanum evidence. |
| Akhtyamov et al., *Social robot navigation through constrained optimization: A comprehensive study of uncertainty-based objectives and constraints in the simulated and real world* (RAS, 2025) | [publisher record](https://doi.org/10.1016/j.robot.2024.104830); Zotero `PTJ74J2E` | Uncertainty-aware objective/constraint variants with simulation and physical evaluation establish the evaluation bar. Perception/prediction error, clearance, completion and timing must remain separate estimands. |
| Han et al., *DR-MPC: Deep Residual Model Predictive Control for Real-world Social Navigation* (RA-L, 2025) | [LEAF publication page](https://leaf.utias.utoronto.ca/publication/han-2024-drmpc/) | Residual learning plus MPC and hardware crowd trials occupy the learning-control overlap. LSTM and self-supervised scoring cannot be presented as standalone novelty; the CCA contribution must remain the fixed-budget control interface and its audit. |
| Sun et al., *Socially Aware Robot Crowd Navigation via Online Uncertainty-Driven Risk Adaptation* (2025 preprint) | [arXiv full text](https://arxiv.org/abs/2506.14305) | PENN-based uncertainty filtering and online waypoint risk adaptation occupy “risk-adaptive MPC”. The defensible difference is only event-level fixed-budget allocation inside the NMPC constraint rows, and it requires direct comparator/ablation evidence. |
| *Transformer-based human-motion forecasting coupled with safe reinforcement learning for telepresence robot co-navigation* (2025) | [Frontiers full text](https://www.frontiersin.org/journals/neurorobotics/articles/10.3389/fnbot.2025.1697518/full) | Forecasting plus Safe-RL/CBF, DWA and MPC baselines with large simulation cohorts already cover a broad learned safety stack. This project should not claim generic learned prediction or safe-RL novelty; LSTM remains a bounded context interface and NMPC remains the executor. |

The local Zotero read-only searches found Stefanini and Akhtyamov but no exact
match for Han, Sun or the Frontiers record. They remain screening records until
metadata, full text and licensing are reconciled; no item was imported and no
paper file was edited. No external numerical result is transferred to this
project.

The gap is consequently narrowed again: test whether a simple, auditable,
causal context score can redistribute a predeclared total chance allowance
across human--horizon events inside a position-state Mecanum CCA-NMPC, under
matched MPC/NMPC/DWA/MPPI controls and separately audited perception,
calibration, closed-loop and hardware evidence. This is a falsifiable systems
comparison, not a claim that context-aware navigation, risk adaptation,
learning-plus-MPC or hardware social navigation are new in isolation.

