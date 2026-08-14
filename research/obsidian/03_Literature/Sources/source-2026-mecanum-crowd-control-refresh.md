---
type: source-screening
status: web-verified-zotero-pending
date: 2026-08-13
paper_edit: prohibited
---

# Mecanum hardware and crowd-MPC boundary refresh — 2026-08-13

This note records a targeted Google/web and local-Zotero refresh. The sources
are primary publisher or proceedings records and are screening boundaries only;
their numerical results are not imported into this project.

## Sources

| Source | Verified record | Consequence for this study |
|---|---|---|
| “Model predictive control with residual learning and real-time disturbance rejection: Design and experimentation,” *Control Engineering Practice* (2025), DOI 10.1016/j.conengprac.2025.106587 | [ScienceDirect record](https://doi.org/10.1016/j.conengprac.2025.106587) | Hardware Mecanum tracking with MPC, residual learning and disturbance estimation is already established. The present work cannot claim Mecanum MPC or real-robot tracking as standalone novelty; it must bind its contribution to the CCA interface and report the position/body-velocity boundary. |
| G. G. Gravina et al., “Crowd navigation in a multi-room environment: a model predictive control framework for mobile robots,” *Frontiers in Robotics and AI* (2026), DOI 10.3389/frobt.2026.1812386 | [Publisher full text](https://doi.org/10.3389/frobt.2026.1812386) | RGB-D/LiDAR perception, human state prediction, MPC safety constraints and real-robot validation are already combined in a recent system. Our evaluation must therefore separate sensor measurement, causal prediction, controller allocation and hardware evidence. |
| A. Stratton et al., “How Human Motion Prediction Quality Shapes Social Robot Navigation Performance in Constrained Spaces,” HRI 2026, DOI 10.1145/3757279.3788664 | [ACM record](https://doi.org/10.1145/3757279.3788664) | Prediction ADE alone is not a sufficient proxy for closed-loop navigation or human outcomes. PR12/PR40 must retain downstream safety, tracking, timing and qualitative measures instead of selecting a model from ADE only. |
| “Pedestrian trajectory prediction via physical-guided position association learning,” *Engineering Science and Technology, an International Journal* (2025), DOI 10.1016/j.jestch.2025.102008 | [ScienceDirect record](https://doi.org/10.1016/j.jestch.2025.102008) | Physical-guided and learned pedestrian prediction is already an active line; LSTM prediction itself cannot be the novelty. The project must evaluate the CCA interface and closed-loop outcomes, not only prediction error. |
| A. Kada et al., “Pedestrian-Aware Control of AMRs Using Model Predictive Speed Control Minimizing Pedestrian Hesitation,” *Journal of the Robotics Society of Japan* (2026), DOI 10.7210/jrsj.44.196 | [J-STAGE record](https://doi.org/10.7210/jrsj.44.196) | Pedestrian-aware MPC with interaction-oriented objectives is already reported. The present scope keeps the claim to transparent fixed-budget CCA allocation in a position-state Mecanum controller and reports interaction/safety metrics separately. |
| “Eight-Wheel Mecanum Omnidirectional Autonomous Mobile Robot: Kinematics, Architecture, and Validation,” *Electronics* (2026), DOI 10.3390/electronics15112441 | [MDPI record](https://doi.org/10.3390/electronics15112441) | Recent Mecanum hardware architecture and validation further remove any standalone novelty claim for omnidirectional kinematics or robot integration; exact robot geometry, timing and calibration must be measured for PR30. |

## Zotero status

Exact-title read-only searches in the local Zotero API on 2026-08-13 returned
no matching items for these six records. They remain URL-linked screening
notes and were not imported without a verified metadata/full-text decision.

## Gap consequence

The refresh further rejects claims of novelty for Mecanum MPC, multimodal
perception plus human prediction, and generic LSTM trajectory accuracy. The
remaining falsifiable question is the matched safety--tracking--feasibility
trade-off produced by the transparent fixed-total CCA interface inside the
position-state Mecanum controller, with a fixed global path and only a
conflict-triggered local update. For a moving person, only CCA-NMPC may keep a
causal future-position estimate internally; no predicted human path is an
image or raw-data output.

## Knowledge links

[[03_Literature/literature-review]] · [[03_Literature/source-index]] ·
[[03_Literature/web-verified-gap-sources]] · [[04_Research_Gap/research-gap]] ·
[[06_Methods/evaluation-protocol]] · [[07_Analysis/protocol-status-20260813]] ·
[[00_MOC/project-map]]
