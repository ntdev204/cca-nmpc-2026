---
type: literature-source-screening
status: screening-only
scope: research-knowledge
updated_at: 2026-08-13
zotero_admission: not-imported
paper_edit: prohibited
---

# Screening refresh — dynamic human prediction, Mecanum control and self-supervision

This note records a read-only Google/web refresh performed after the current
focused audit. These records are not a systematic-review count, are not final
citation admissions, and do not create a dataset, checkpoint or paper claim.

## Boundary records

| Record | Primary source | Direct consequence for this study |
|---|---|---|
| Zhang, Ge, Su, Gu, Wang, Chen and Li, *Model predictive control with residual learning and real-time disturbance rejection: Design and experimentation* (Control Engineering Practice, 2025) | [DOI 10.1016/j.conengprac.2025.106587](https://doi.org/10.1016/j.conengprac.2025.106587); [PolyU record](https://research.polyu.edu.hk/en/publications/model-predictive-control-with-residual-learning-and-real-time-dis/) | A Mecanum hardware study with learned residual/disturbance compensation makes physical calibration, actuator-interface disclosure and target-hardware timing mandatory. It does not establish the CCA allocation contribution. |
| Stratton et al., *How Human Motion Prediction Quality Shapes Social Robot Navigation Performance in Constrained Spaces* (HRI 2026) | [ACM/IEEE DOI 10.1145/3757279.3788664](https://doi.org/10.1145/3757279.3788664); [author PDF](https://chrismavrogiannis.com/pdfs/stratton2026hmp2nav.pdf) | ADE alone is not a sufficient downstream navigation or human-experience measure. Prediction quality, closed-loop control outcomes and any human-centred measures must remain separate in PR12/PR40. |
| Samavi, Han, Shkurti and Schoellig, *SICNav: Safe and Interactive Crowd Navigation Using Model Predictive Control and Bilevel Optimization* (AAAI 2026) | [AAAI record](https://ojs.aaai.org/index.php/AAAI/article/view/41408); [DOI 10.1609/aaai.v40i47.41408](https://doi.org/10.1609/aaai.v40i47.41408) | Interactive human-response modeling, MPC and real-robot evaluation are established nearby. CCA-NMPC must not claim generic interactive prediction or social-navigation novelty; the active scope remains a transparent position-state allocation interface. |
| Gao et al., *Motion planning with uncertainty in human-populated environments via model-based reinforcement learning for social robot navigation* (Neurocomputing, 2026) | [ScienceDirect record](https://www.sciencedirect.com/science/article/pii/S0925231226000998); [DOI 10.1016/j.neucom.2026.132702](https://doi.org/10.1016/j.neucom.2026.132702) | Uncertainty-aware model-based RL already occupies the learning-based planning boundary. RL, if retained, is a fixed-budget comparator/ablation, not a new core pipeline contribution. |
| Huang, Cheng and Wang, *Learning Velocity and Acceleration: Self-Supervised Motion Consistency for Pedestrian Trajectory Prediction* (2025 preprint) | [arXiv:2503.24272](https://arxiv.org/abs/2503.24272) | Self-supervised motion learning is already active. The project must describe its LSTM score loop as an implementation choice and keep novelty centered on the matched CCA allocation/control comparison. |
| Mohamed, Khan, Naseer, Tahir and Jamil, *Transformer-based human-motion forecasting coupled with safe reinforcement learning for telepresence robot co-navigation* (Frontiers in Neurorobotics, 2026) | [DOI 10.3389/fnbot.2025.1697518](https://doi.org/10.3389/fnbot.2025.1697518) | Transformer forecasting plus Safe-RL/CBF is an adjacent anticipatory-navigation stack, mainly evaluated with simulated agents and different control semantics. It further limits any claim that prediction-plus-learning integration is novel; the present contribution remains the transparent CCA interface and matched position-state Mecanum benchmark. |

## Decision update

The narrow gap is unchanged: a provenance-linked, matched evaluation of a
transparent fixed-total context allocation interface inside position-state
Mecanum CCA-NMPC with body-velocity commands, fixed global path and
conflict-triggered robot local-path updates. The dynamic person is measured as a
current context snapshot; only CCA-NMPC may integrate its causal velocity
internally for chance rows, and no predicted human path is exported or drawn.

The refresh strengthens three pending gates rather than opening them:

- PR12 must report context-prediction metrics separately from closed-loop
  navigation outcomes.
- PR20/PR21 must retain MPC, NMPC, DWA and MPPI as matched comparators with
  equal timing, failure and safety accounting.
- PR30 must measure the supplied Mecanum platform, sensor calibration and
  target-hardware timing rather than reuse values from a published platform.

## Boundary refresh — 2026-08-13 (physical crowd-MPC and omnidirectional baselines)

| Record | Primary source | Consequence for this study |
|---|---|---|
| Han et al., *DR-MPC: Deep Residual Model Predictive Control for Real-world Social Navigation* (RA-L, 2025) | [LEAF publication page](https://leaf.utias.utoronto.ca/publication/han-2024-drmpc/) | Real-crowd hardware validation and residual learning already occupy the learned-MPC boundary. The present study must keep LSTM inside CCA and compare complete safety/tracking/runtime outcomes rather than claim generic learning-plus-MPC novelty. |
| Aslam et al., *Model Predictive Control for Crowd Navigation via Learning-Based Trajectory Prediction* (2025 preprint) | [arXiv:2508.07079](https://arxiv.org/abs/2508.07079) | A physical robot comparison of a learned pedestrian predictor against constant velocity explicitly separates open-loop prediction error from closed-loop navigation. PR12/PR40 must retain this separation and report controller-level effects. |
| Shafiq et al., *Real-time navigation of mecanum wheel-based mobile robot in a dynamic environment* (Heliyon, 2024) | [DOI 10.1016/j.heliyon.2024.e26829](https://doi.org/10.1016/j.heliyon.2024.e26829) | Mecanum dynamic-obstacle experiments already exist with A* plus velocity-obstacle planning. It is a platform/planner comparator, not evidence for CCA allocation; the benchmark must use matched position/body-velocity metrics. |
| Tsai et al., *Autonomous Steering System Using Fuzzy TD3 and GRU-Attention for Omnidirectional AMRs in Dynamic Environments* (International Journal of Fuzzy Systems, 2026) | [DOI 10.1007/s40815-025-02209-4](https://doi.org/10.1007/s40815-025-02209-4) | A Mecanum platform with LiDAR, learned local control and real hardware establishes an adjacent RL/omnidirectional baseline. It also uses ROS and a different actuator stack, so it cannot be treated as target-hardware evidence; RL remains comparator-only. |

Exact-title Zotero searches for these four records returned no local matches on
2026-08-13. They remain screening-only, with no citation-key or quantitative
claim admitted. The refresh tightens the requirement to compare prediction,
safety, tracking, compute, failure denominator and hardware interface on the
same fixed global path and local-trigger rule.

## Knowledge links

[[03_Literature/web-verified-gap-sources]] · [[03_Literature/nearest-work-matrix]] ·
[[04_Research_Gap/research-gap]] · [[06_Methods/lstm-protocol]] ·
[[06_Methods/simulation-protocol]] · [[06_Methods/final-run-data-package]] ·
[[07_Analysis/protocol-status-20260813]]
