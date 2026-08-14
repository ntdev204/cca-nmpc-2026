---
type: source-note
status: included-provisional
evidence_status: full-text
evidence_level: full-text
citekey: samavi_sicnav_2025
zotero_uri: zotero://select/library/items/RMQEU4RJ
paper_edit: prohibited
---

# Samavi et al. — SICNav (2025)

## Primary record

- **Title:** *SICNav: Safe and Interactive Crowd Navigation Using Model Predictive Control and Bilevel Optimization*
- **Authors:** S. Samavi, J. R. Han, F. Shkurti, A. P. Schoellig
- **Venue:** IEEE Transactions on Robotics, vol. 41, 2025, pp. 801--818
- **DOI:** [10.1109/TRO.2024.3484634](https://doi.org/10.1109/TRO.2024.3484634)
- **Zotero:** item `RMQEU4RJ`; attachment `6YMXDJ86` (full-text PDF)
- **Screened:** 2026-08-13, Zotero metadata/attachment and indexed full text

## What is established

The work embeds an ORCA-based human response model inside a bilevel nonlinear
MPC formulation and uses a KKT reformulation to obtain a single-level problem.
The full text validates ORCA forecasting on ETH/UCY human data, evaluates two
simulation settings (ORCA and social-force agents) with 500 random scenarios per
setting and compares against multiple baselines, then reports an indoor
real-robot study. The reported metrics include success, navigation time,
collision frequency and freezing frequency, with pairwise Mann--Whitney tests.
It is therefore direct prior art for interactive crowd MPC, explicit safety
constraints, statistical failure analysis and the need to separate forecast
quality from closed-loop outcomes.

## Boundary for this project

The full text does not establish a context-score fixed-budget allocator for a
position-state Mecanum NMPC with body-velocity commands. It models human response through ORCA and jointly
optimizes predicted human motion with robot motion, whereas the current project
uses a current-context LSTM interface and does not generate a human future
trajectory. No matching position-state/body-velocity evidence was identified in the audited
record. The project cannot present real-robot validation, interactive human
modeling, or statistical baseline comparison as novel in isolation.

## Consequence

The confirmatory benchmark should include an interaction-aware or strong
dynamic-obstacle comparator when feasible, and should report safety,
completion, clearance, tracking, timing and failure outcomes rather than only a
prediction metric. The CCA contrast remains a bounded allocation interface
under a fixed global path and conflict-triggered local-path update; SICNav is a
comparator boundary, not a component to copy into the active model.

## Knowledge links

[[03_Literature/nearest-work-matrix]] · [[03_Literature/prior-art-delta]] ·
[[04_Research_Gap/research-gap]] · [[06_Methods/evaluation-protocol]] ·
[[01_Governance/claim-register]]
