---
type: literature-source
status: zotero-matched-refresh
evidence_status: full-text-matrix-plus-landing-page-refresh
zotero_item_key: 8T4BRJA4
doi: 10.1109/LRA.2024.3461552
screened_at: 2026-08-13
paper_edit: prohibited
---

# Stefanini et al. — Efficient Context-Aware Model Predictive Control for Human-Aware Navigation

## Source record

- [IEEE/DOI landing page](https://doi.org/10.1109/LRA.2024.3461552)
- [Author/project page](https://darko-project.eu/publications/2024-2/efficient-context-aware-model-predictive-control-for-human-aware-navigation/)
- Zotero item: `8T4BRJA4` (local API search matched title, authors and year 2024)

## What the source establishes

The paper reports a context-aware MPC formulation for crowded human-aware
navigation. Its context includes human body pose, velocity and activity cues;
the abstract and project record report simulation and real-life experiments.
This is direct prior art for the broad statement that context-aware perception
can be coupled to MPC for human-aware navigation.

## Consequence for the active study

The source rules out novelty claims based only on the words *context-aware*,
human pose/velocity input, LSTM/perception-to-MPC integration, or the existence
of real-robot evaluation. The active delta must remain the narrow, falsifiable
comparison of a transparent fixed-budget CCA interface inside the declared
position-state Mecanum NMPC with body-velocity commands, fixed clearance, fixed global path and explicit
local-trigger semantics. Even that delta is provisional until matched baselines,
independent analysis and physical evidence are available.

## Audit boundary

The full-text equation/implementation audit is already recorded in NW-01 of
`nearest-work-matrix.md` (Zotero PDF `[02]`, pages 1--5 and 8). This dated note
is a Zotero/landing-page refresh and does not repeat that extraction. It does
not assert that the source uses the same risk allocator, Mecanum dynamics,
LSTM, dataset, or actuator interface. The source therefore strengthens the
exclusion boundary but is not a quantitative nearest-work equivalence claim.

## Links

[[03_Literature/nearest-work-matrix]] · [[04_Research_Gap/research-gap]] ·
[[03_Literature/web-verified-gap-sources]] · [[07_Analysis/protocol-status-20260813]]
