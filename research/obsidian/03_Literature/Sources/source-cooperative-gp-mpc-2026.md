---
type: source-note
status: screening-candidate
evidence_status: publisher-full-text-screening
paper_edit: prohibited
---

# Cooperative Gaussian-process MPC (2026)

## Primary record

- **Title:** *Cooperative Gaussian process-based model predictive control for safe multi-agent navigation*
- **Venue:** Journal on Advances in Signal Processing, 2026
- **DOI:** [10.1186/s13634-026-01306-2](https://doi.org/10.1186/s13634-026-01306-2)
- **Record:** [Springer article](https://link.springer.com/article/10.1186/s13634-026-01306-2)
- **Screened:** 2026-08-13, Google/web discovery followed by the open-access publisher full text

## What is established

The article combines Gaussian-process residual dynamics, uncertainty-aware
chance constraints and ADMM-based multi-agent coordination in an MPC framework.
The publisher text explicitly reports simulation comparisons with nominal and
nonlinear MPC and discusses robust consensus. It is a nearby boundary for
learning-assisted uncertainty handling and for evaluating more than a single
nominal trajectory.

## Boundary for this project

The full text does not show that the method uses a human-context score to
redistribute one fixed chance budget across human--step events, nor that it
uses a position-state Mecanum plant with body-velocity commands. Independent metadata/admission review
remains open. It is not evidence of superiority or of a direct algorithmic
equivalence.

## Consequence

If the method is reproducible under the available compute and scope, it is a
useful uncertainty-aware comparator or limitation reference. The proposed
study must keep predictor calibration, allocation semantics and plant/input
model explicit instead of treating every learned uncertainty method as the
same baseline.

## Knowledge links

[[03_Literature/nearest-work-matrix]] · [[03_Literature/literature-synthesis]] ·
[[05_Theory/context-aware-risk-allocation]] · [[06_Methods/evaluation-protocol]]
