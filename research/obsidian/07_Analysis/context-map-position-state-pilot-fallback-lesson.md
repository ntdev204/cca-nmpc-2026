---
type: research-boundary-note
status: purged-provenance-only
evidence_status: no-result-retained
paper_edit: prohibited
---

# Position-state map pilot v9 — fail-closed design lesson

The former v9 development run exercised the context-speed domain check and
the CCA fallback boundary. It preserved the fixed global path, local-only
replanning and the no-human-trajectory-artifact rule.

The run, checkpoint, metrics, plots and hashes were physically purged on
2026-08-14. No collision count, completion rate, margin, timing number or
confusion matrix from that pilot is retained or admissible. The reusable
research lesson is that an out-of-domain LSTM output must be rejected before
actuation, with a visible fallback/stop status rather than an implicit success.

The next run requires a new protocol freeze, target-compatible LSTM calibration,
independent ID/OOD evaluation and hardware timing evidence.

Audit: [[07_Analysis/development-artifact-purge-20260814]] ·
[[07_Analysis/current-evidence-index]] · [[06_Methods/lstm-protocol]] ·
[[00_MOC/project-map]]
