---
type: focused-literature-refresh
status: screening-only
evidence_status: landing-page-and-abstract
screened_at: 2026-08-14
zotero_status: local-search-no-exact-match
paper_edit: prohibited
---

# Focused research refresh — 2026-08-14

## Search boundary

Google-oriented web queries were used for recent Mecanum control, ellipsoidal
obstacle MPC and uncertainty-aware human navigation. Google-Scholar-oriented
discovery was treated as discovery only; no coverage or citation-count claim is
made. The local Zotero API was reachable, but exact-title searches returned no
match for the records below. No Zotero item was imported without an explicit
source/destination confirmation.

## Screened records

| Record | Primary page | What it changes | Boundary |
|---|---|---|---|
| *Efficient avoidance of ellipsoidal obstacles with model predictive control for mobile robots and vehicles* (Mechatronics, 2025, DOI `10.1016/j.mechatronics.2025.103386`) | [Publisher record](https://www.sciencedirect.com/science/article/pii/S0957415825000959) | Joint local collision avoidance, dynamics and actuation constraints for ellipsoidal robot/obstacle geometry are established nearby. | Abstract/landing page only; no full-text extraction added. |
| Nghiem et al., *A study on the optimal control strategy using sliding mode controller for a Mecanum-Wheeled omnidirectional mobile robot* (Measurement, 2025, DOI `10.1016/j.measurement.2025.118113`) | [Publisher record](https://www.sciencedirect.com/science/article/pii/S0263224125014721) | Mecanum dynamics, trajectory error, energy and experimental comparison reinforce that the platform and ordinary control metrics are not novelty alone. | Landing-page/abstract screening; the controller is not the CCA comparator. |
| Pham and Han, *Consolidated Control Architecture for Mecanum-Wheeled Mobile Robots Using SMO-MPC-PID-Fuzzy Hybridization* (online 2025, JIFS, DOI `10.1177/18758967251394861`) | [SAGE record](https://journals.sagepub.com/doi/10.1177/18758967251394861) | A recent integrated Mecanum architecture reports broad simulation and claims stability; it raises the benchmark bar for matched baselines, physical metrics and claim restraint. | Publisher abstract/metadata only; reported performance is not adopted as evidence. |
| Ryu and Mehr, *Integrating Predictive Motion Uncertainties with Distributionally Robust Risk-Aware Control for Safe Robot Navigation in Crowds* (ICRA 2024) | [Author record](https://arxiv.org/abs/2403.05081) | Distributionally robust chance-constrained MPC already addresses prediction mismatch and crowd navigation with an interpretable risk metric. | Different ambiguity-set/CVaR method and platform; use as a robustness boundary comparator, not a novelty claim. |

## Continuation search — 2026-08-14

The subsequent Google-oriented search was checked against publisher or author
records. These records remain screening-only and were not imported into Zotero:

| Record | Primary page | Research consequence | Boundary |
|---|---|---|---|
| de Groot et al., *Scenario-based motion planning with bounded probability of collision* (IJRR, 2025) | [Publisher record](https://journals.sagepub.com/doi/10.1177/02783649251315203) | Joint-horizon collision probability and real shared-space demonstrations make a single-step Gaussian chance constraint an insufficient novelty claim. | Abstract/landing-page screening; scenario-optimization details must be read before any comparator decision. |
| *Dynamic Risk-Aware MPPI for Mobile Robots in Crowds via Efficient Monte Carlo Approximations* (IROS 2025) | [IEEE record](https://xplorestaging.ieee.org/document/11246822/) | MPPI now has a recent dynamic-risk baseline with simulated and real experiments; MPPI must be implemented as a matched baseline rather than a straw comparator. | Conference record/abstract screening; no local implementation or result imported. |
| *Model predictive control with residual learning and real-time disturbance rejection: Design and experimentation* (2025) | [Publisher record](https://www.sciencedirect.com/science/article/abs/pii/S0967066125003491) | Recent Mecanum hardware work reports physical tracking experiments, so the proposed study needs direct hardware provenance and matched tracking metrics. | Abstract/landing-page screening; reported percentages are not adopted as evidence. |
| *Trajectory Planning with Model Predictive Control for Obstacle Avoidance Considering Prediction Uncertainty* (IFAC, 2025) | [Publisher record](https://www.sciencedirect.com/science/article/pii/S2405896325016441) | Uncertainty-aware dynamic-obstacle MPC with a probabilistic prediction model is already available; the gap cannot be framed as “MPC plus prediction uncertainty.” | Abstract/landing-page screening; ROS2 implementation is not part of this project. |

These records narrow the gap further: the contribution must be evaluated as a
specific CCA risk-allocation and context-interface design on a fixed
position-state Mecanum platform, with matched MPC/NMPC/DWA/MPPI baselines,
paired repeated trials and transparent calibration. No “first,” “real-time,”
or “safe” claim is promoted from this refresh.

## Research-gap consequence

The refresh further rejects broad claims such as “Mecanum MPC is novel,”
“ellipsoidal chance constraints are new,” or “LSTM plus risk-aware MPC is
unoccupied.” The defensible question remains narrower: under a fixed global
path, fixed clearance and fixed total allowance, does the auditable causal
context interface produce a reproducible safety--tracking--fallback trade-off
on the stated position-state Mecanum platform? That question still requires a
proper context input, frozen comparator implementation, calibration/OOD evidence,
paired repeated runs and physical provenance.

## Search refresh — 2026-08-14 (learning and social-navigation benchmark boundary)

The latest Google/Google-Scholar-oriented pass checked a recent learning-based
social-navigation review, uncertainty-aware social MPC, online risk adaptation,
deep-residual MPC with hardware trials and a recent social-force NMPC preprint.
The consolidated source record is
[[03_Literature/Sources/source-social-navigation-refresh-20260814]].

The records further occupy broad claims about learning-based navigation,
LSTM--MPC integration, risk adaptation and social-force NMPC. They also raise the
evaluation bar: scenario diversity, matched controller access, repeated paired
units, closed-loop metrics and sim-to-real limits must be explicit. The current
physical-spec-bound 30-unit run remains `pilot` and `candidate-development-only`;
it cannot be
promoted to confirmatory evidence from this literature refresh.

No numerical result, citation count or database-coverage claim was transferred
from the external records. Exact-title Zotero matching and citation promotion
remain separate release gates; no manuscript file was edited.

## Targeted publisher refresh — 2026-08-14 (late pass)

An additional Google/Google-Scholar-oriented pass checked publisher or author
pages for recent crowd-navigation and MPC work. These records remain
screening-only and do not change the gap until their metadata and full texts
are reconciled in Zotero:

| Record | Primary page | Boundary consequence |
|---|---|---|
| *Crowd navigation in a multi-room environment: a model predictive control framework for mobile robots* (Frontiers in Robotics and AI, 2026) | [Publisher full text](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2026.1812386/full) | A recent multi-room MPC pipeline already combines crowd detection, estimation, prediction, map generation and obstacle avoidance; the present study must separate perception, context prediction and closed-loop control estimands. |
| *Accompaniment and collision avoidance for a cane-type robot using dynamic cost maps and MPC* (ROBOMECH Journal, 2026) | [Springer full text](https://link.springer.com/article/10.1186/s40648-026-00345-6) | Dynamic-obstacle MPC with a physical multi-sensor platform raises the hardware-provenance and close-range clearance bar; Mecanum/control integration alone is not a novelty claim. |
| Mizuta and Leung, *Unified Generation-Refinement Planning: Bridging Guided Flow Matching and Sampling-Based MPC for Social Navigation* (ICRA 2026) | [Author project page](https://cfm-mppi.github.io/) | Learned multimodal generation coupled to MPPI occupies the learning-plus-sampling-control boundary; MPPI must remain a matched baseline and learning cannot be presented as the sole contribution. |
| Trepella et al., *Navigating the Crowd: Non-linear MPC with Social Forces Dynamics for Human-Aware Robot Navigation* (2026 preprint) | [arXiv record](https://arxiv.org/abs/2607.10374) | Embedded human dynamics, repeated scenarios and ablations illustrate the expected evaluation bar; this is a boundary record, not peer-reviewed evidence for the current paper. |

The late pass further narrows the claim: the defensible contribution remains a
provenance-linked comparison of the declared causal context interface and
fixed-total CCA allocation on the position-state Mecanum plant. No source was
imported, no numerical result was copied, and no manuscript file was edited.

The read-only Zotero check matched Akhtyamov (`PTJ74J2E`) and Sun (`HSR6VLIH`).
The other screened records had no exact local match in this pass; no item was
imported and no BibTeX export or manuscript edit was performed.

## Continuation web check — 2026-08-14

A further Google/Scholar-oriented discovery pass checked recent primary or
publisher records. These are still screening-only; no title was copied into the
manuscript and no Zotero item was imported without metadata/full-text review:

| Record | Primary page | Boundary consequence |
|---|---|---|
| Hu et al., *NavThinker: Action-Conditioned World Models for Coupled Prediction and Planning in Social Navigation* (2026 preprint) | [arXiv](https://arxiv.org/abs/2603.15359) | Action-conditioned world-model prediction, RL and real-robot transfer occupy the coupled prediction--planning space; the present scope must not claim generic prediction-plus-RL novelty. |
| Mizuta and Leung, *Unified Generation-Refinement Planning: Bridging Guided Flow Matching and Sampling-Based MPC for Social Navigation* (ICRA 2026) | [Author project page](https://cfm-mppi.github.io/) | Learned multimodal generation coupled to MPPI further strengthens MPPI as a matched baseline and separates the CCA interface from learned trajectory generation. |
| Ren et al., *SCU-T-MPC: Risk-Aware and Socially Compliant Topological Motion Planning Under Uncertainty* (IET Cyber-Systems and Robotics, 2026) | [Publisher record](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/csy2.70051) | Probabilistic topology, chance constraints and learned social preference occupy risk-aware social MPC; fixed-budget CCA must be framed as a bounded interface comparison, not a universal risk novelty. |
| de Groot et al., *Scenario-based motion planning with bounded probability of collision* (IJRR, 2025) | [Publisher record](https://journals.sagepub.com/doi/10.1177/02783649251315203) | Joint-horizon scenario collision probability raises the standard beyond a single-step Gaussian row; report the CCA bound only within its explicit one-update scope. |
| *Chance-Constrained Sampling-Based MPC for Collision Avoidance in Uncertain Dynamic Environments* (IEEE RA-L, 2025) | [IEEE Xplore record](https://ieeexplore.ieee.org/abstract/document/11021391) | Chance-constrained unscented MPPI with simulated and real-world validation is a direct controller comparator; MPPI must be matched rather than treated as a straw baseline. | Publisher abstract only; full-text/Zotero reconciliation and platform details remain open. |

The update leaves the research gap unchanged but narrows its wording again:
the study tests a provenance-linked, fixed-total CCA context interface on the
declared position-state Mecanum plant against matched MPC/NMPC/DWA/MPPI
baselines. It does not claim a new world model, RL planner, topology planner,
social-preference model, or universal probability guarantee.

## Links

[[03_Literature/web-verified-gap-sources]] · [[03_Literature/nearest-work-matrix]] ·
[[04_Research_Gap/research-gap]] · [[01_Governance/status-and-provenance]]
