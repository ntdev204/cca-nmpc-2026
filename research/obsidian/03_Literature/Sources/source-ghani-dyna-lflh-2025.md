---
type: source-note
status: screening-only
evidence_status: primary-landing-page
source_kind: author-maintained-paper-record
citekey: dyna_lflh_icra_2025
---

# Ghani et al. — Dyna-LfLH (IROS 2025)

## Source

- [Author-maintained paper record](https://www.cs.utexas.edu/~pstone/Papers/bib2html/b2hd-dyna_lflh_icra_2025.html)
- Venue: IEEE/RSJ International Conference on Intelligent Robots and Systems,
  2025.

## What is relevant

The record describes self-supervised motion-planner training for dynamic
obstacles and reports evaluation in simulation and on a ground robot. This is a
direct boundary for the project's self-supervised score-loop choice: the
learning protocol cannot be presented as a control novelty by itself.

## What is not established for this project

The source does not establish the fixed-budget CCA allocator, the
position-state Mecanum model, the Astra-S/N10P measurement contract or the
fixed-global/local-trigger protocol. Its reported performance is not imported
as a result, baseline number or evidence for this repository.

## Decision

Keep as a screening-only comparator boundary. If the paper is cited later,
verify the final proceedings metadata and correction/retraction status in
Zotero first. The active LSTM remains a current-context component inside CCA;
only CCA-NMPC may integrate that context internally for chance rows, and no
future path is created in an image or raw capture artifact.

Related: [[03_Literature/web-verified-gap-sources]] ·
[[03_Literature/pose-learning-gap]] · [[04_Research_Gap/research-gap]] ·
[[06_Methods/lstm-protocol]] · [[00_MOC/project-map]]
