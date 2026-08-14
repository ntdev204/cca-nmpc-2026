---
type: source-screening
status: screening-only
evidence_status: publisher-or-author-landing-page-and-abstract
screened_at: 2026-08-14
paper_edit: prohibited
---

# Social-navigation and learning-control refresh — 2026-08-14

This note records a focused Google/Google-Scholar-oriented discovery pass. Each
record was checked at a publisher, institutional, or author landing page. The
records are not a systematic-review count, are not imported into the locked
manuscript, and do not transfer numerical results to this project.

## Screened records

| Record | Primary page | Boundary consequence |
|---|---|---|
| *Social robot navigation: a review and benchmarking of learning-based methods* (Frontiers in Robotics and AI, 2025) | [Frontiers full text](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2025.1658643/full) | Recent benchmarking already combines kinematic simulation, sensor simulation, human-motion scenarios, DWA/ORCA/SFM and learning-based planners. The study must define its own map, denominator and sensor access explicitly. |
| Akhtyamov et al., *Social robot navigation through constrained optimization: A comprehensive study of uncertainty-based objectives and constraints in the simulated and real world* (RAS, 2025; Zotero `PTJ74J2E`) | [ScienceDirect record](https://www.sciencedirect.com/science/article/pii/S0921889024002148) | Simulation/real comparison and adaptive uncertainty constraints occupy broad uncertainty-aware social-MPC novelty. Perception, clearance, completion and timing must remain separate estimands. |
| Kabir and Mysorewala, *Socially aware navigation for mobile robots: a survey on deep reinforcement learning approaches* (2025 preprint) | [arXiv record](https://arxiv.org/abs/2512.00049) | Non-uniform evaluation, computational burden and sim-to-real transfer are recognized field-wide limitations. RL is therefore a training mechanism or comparator, not a standalone contribution. |
| Sun et al., *Socially Aware Robot Crowd Navigation via Online Uncertainty-Driven Risk Adaptation* (2025 preprint; Zotero `HSR6VLIH`) | [arXiv record](https://arxiv.org/abs/2506.14305) | Learned uncertainty filtering and online waypoint risk adaptation already cover the broad risk-adaptive-MPC space. The remaining distinction is the declared event-level fixed-budget interface inside the stated NMPC rows. |
| Han et al., *DR-MPC: Deep Residual Model Predictive Control for Real-world Social Navigation* (RA-L, 2025) | [LEAF publication record](https://leaf.utias.utoronto.ca/publication/han-2024-drmpc/) | Residual learning, MPC and hardware crowd trials occupy the learning-plus-real-robot overlap. LSTM and self-supervised scoring cannot carry novelty alone. |
| Trepella et al., *Navigating the Crowd: Non-linear MPC with Social Forces Dynamics for Human-Aware Robot Navigation* (2026 preprint) | [Author/arXiv record](https://arxiv.org/abs/2607.10374) | Social-force NMPC, multiple baselines, repetitions and ablation establish a stronger evaluation bar. The present protocol must not claim superiority from a small pilot. |

## Decision for the current study

The refresh rejects the broad claims “learning-based social navigation is new,”
“LSTM plus MPC is new,” “risk-adaptive MPC is new,” and “benchmarking itself is
new.” The defensible question remains a bounded empirical comparison: under a
fixed global path, fixed clearance and fixed total allowance, does the causal
context interface change the safety--tracking--feasibility trade-off of the
position-state Mecanum CCA-NMPC relative to matched MPC, NMPC, DWA and MPPI
conditions? The pilot campaign is insufficient to answer that question.

## Zotero reconciliation

Read-only local searches on 2026-08-14 matched Akhtyamov (`PTJ74J2E`) and Sun
(`HSR6VLIH`). The Frontiers review, DR-MPC record, social-navigation survey and
SFM-NMPC preprint had no exact local match in the same pass. No Zotero write or
BibTeX export was performed; unmatched records remain screening-only until
metadata and full text are reconciled.

## Linked knowledge nodes

[[03_Literature/current-research-refresh-20260814]] ·
[[03_Literature/literature-review]] ·
[[04_Research_Gap/research-gap]] ·
[[03_Literature/nearest-work-matrix]] ·
[[06_Methods/evaluation-protocol]] ·
[[07_Analysis/completion-audit]]
