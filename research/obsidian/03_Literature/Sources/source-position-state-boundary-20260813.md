---
type: source-screening
status: web-verified-zotero-pending
date: 2026-08-13
paper_edit: prohibited
---

# Position-state, human-aware MPC and learning boundary — 2026-08-13

This note records a web/Google-Scholar-oriented discovery refresh. The records
were checked against an IEEE, publisher or author landing page. They are
screening boundaries only; no result, runtime value or superiority claim is
imported into the study. The local Zotero API is reachable, but these records
were not found by exact-title search and were not imported without an explicit
record/destination confirmation.

## Sources and consequences

| Source | Verified record | Consequence for this project |
|---|---|---|
| S. A. Shahzadeh Fazeli et al., “Kinematic Control of a Mecanum Mobile Robot using Time-Varying Model Predictive Control,” ICRoM 2024 | [IEEE record](https://ieeexplore.ieee.org/document/10903625); DOI [10.1109/ICRoM64545.2024.10903625](https://doi.org/10.1109/ICRoM64545.2024.10903625) | High-level position control with a kinematic Mecanum model and velocity-level actuation is established. The present work must state its position-state/body-velocity boundary plainly and cannot claim position control or Mecanum MPC as standalone novelty. |
| S. Trepella et al., “Navigating the Crowd: Non-linear MPC with Social Forces Dynamics for Human-Aware Robot Navigation,” accepted IROS 2026 | [Author/accepted version](https://arxiv.org/abs/2607.10374) | Social-force NMPC, fixed global planning, DWB/MPPI/NMPC comparisons, ablation and repeated crowded-scene evaluation already set a strong benchmark boundary. This project must retain fixed global path/local-trigger rules and report failure denominators. |
| X. Gao et al., “Motion planning with uncertainty in human-populated environments via model-based reinforcement learning for social robot navigation,” *Neurocomputing* 673 (2026) 132702 | [ScienceDirect record](https://www.sciencedirect.com/science/article/pii/S0925231226000998); DOI [10.1016/j.neucom.2026.132702](https://doi.org/10.1016/j.neucom.2026.132702) | Model-based RL with stochastic pedestrian prediction and a real mobile-robot validation occupies the learning-based planning boundary. RL remains a comparator/ablation plan, not the claimed CCA novelty. |
| L. Busellato et al., “Uncertainty Aware-Predictive Control Barrier Functions,” *Robotics and Autonomous Systems* 197 (2026) 105291 | [Publisher record](https://www.sciencedirect.com/science/article/pii/S0921889025003884); DOI [10.1016/j.robot.2025.105291](https://doi.org/10.1016/j.robot.2025.105291) | Probabilistic human forecasting, uncertainty-dependent safety margins and real HRI evaluation are established nearby. Any CCA probability statement must remain model-internal or be supported by independent calibration; no generic uncertainty-aware safety novelty is allowed. |
| “Efficient avoidance of ellipsoidal obstacles with model predictive control for mobile robots and vehicles,” *Mechatronics* 110 (2025) 103386 | [Publisher record](https://www.sciencedirect.com/science/article/pii/S0957415825000959); DOI [10.1016/j.mechatronics.2025.103386](https://doi.org/10.1016/j.mechatronics.2025.103386) | Ellipsoidal geometry embedded in local MPC is an active baseline boundary. The ellipse-to-half-space derivation in this project needs explicit geometry/parity checks and cannot be presented as a new obstacle formulation. |

## Updated gap decision

The refresh does not change the bounded gap in
[[04_Research_Gap/research-gap]]. The defensible question remains whether the
auditable CCA context interface changes the safety--tracking--feasibility
trade-off under a fixed total allowance and fixed clearance on the stated
position-state Mecanum plant. The source boundary strengthens the requirements
for a fair MPPI/NMPC comparison, context calibration, OOD analysis and physical
provenance; it does not justify a “first,” universal-safety or detector/LSTM
architecture claim.

## Knowledge links

[[00_MOC/project-map]] · [[03_Literature/nearest-work-matrix]] ·
[[03_Literature/web-verified-gap-sources]] · [[04_Research_Gap/research-gap]] ·
[[05_Theory/position-state-derivation]] · [[06_Methods/evaluation-protocol]] ·
[[08_Decisions/decision-register]]
