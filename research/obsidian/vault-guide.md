---
type: vault-guide
status: active
evidence_status: knowledge-only
---

# CCA--NMPC research knowledge vault

The visual entry point is [[00_MOC/knowledge-galaxy]]. It is a styled Markdown
index; the Obsidian Graph view supplies the interactive node galaxy.

This vault stores linked research knowledge: literature, research gaps,
definitions, theory, methods, assumptions, decisions, and provenance-linked
analysis of completed runs. It is not a dataset store, experiment log, raw
result archive, or manuscript.

## Scope

- CCA is the central contribution: context-conditioned risk allocation inside
  position-state Mecanum NMPC with body-velocity commands.
- LSTM is a context component that estimates position, speed, and coarse
  direction; it does not generate a human trajectory on an image.
- YOLO26s-pose is a replaceable perception instrument, not the novelty claim.
- The global path is fixed; a local robot path is regenerated only on a map
  conflict or registered direction change.

## Knowledge graph entry points

- Hub: [[00_MOC/project-map]]
- Governance: [[01_Governance/research-charter]], [[01_Governance/claim-register]], [[01_Governance/status-and-provenance]]
- Literature and gap: [[03_Literature/literature-review]], [[03_Literature/source-index]], [[04_Research_Gap/research-gap]]
- Theory: [[05_Theory/system-model]], [[05_Theory/context-aware-risk-allocation]], [[05_Theory/theorems]], [[05_Theory/proofs]]
- Methods: [[06_Methods/methods-overview]], [[06_Methods/dataset-protocol]], [[06_Methods/perception-protocol]], [[06_Methods/simulation-protocol]]
- Decisions: [[08_Decisions/decision-register]]

## Boundary

All previous datasets, models, run outputs, figures, tables, and experiment
archives were removed from the workspace. New raw evidence remains outside this
vault; derived analysis may be recorded only with an immutable run ID, manifest
hash, analysis script revision, and explicit evidence status.

Zotero stores sources; Obsidian stores linked reasoning; Overleaf stores the
manuscript.
