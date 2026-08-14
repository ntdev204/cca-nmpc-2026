---
type: research-boundary-note
status: purged-provenance-only
evidence_status: no-result-retained
paper_edit: prohibited
---

# Position-state map pilot v8 — design lesson

The former v8 development run tested the six-state/body-velocity map contract,
fixed global path, local-only replanning and the rule that only CCA may use an
internal context prediction. Its candidate LSTM was external to the target
Mecanum/Astra-S/N10P platform and lacked an independent calibration/ID/OOD
holdout.

The run, checkpoint, metrics, plots and hashes were physically purged on
2026-08-14. No numerical result from that pilot is retained or admissible.
The reusable research lesson is methodological: an uncalibrated context model
must be rejected before it reaches a CCA chance row, and the fallback decision
must be observable in the event log.

The next run requires a new protocol freeze, target-compatible context capture,
calibration split, ID/OOD test and independent analysis. No human future path
is exported or drawn on an image.

Audit: [[07_Analysis/development-artifact-purge-20260814]] ·
[[07_Analysis/current-evidence-index]] · [[06_Methods/lstm-protocol]] ·
[[00_MOC/project-map]]
