---
type: provenance-note
status: completed
evidence_status: provenance-only
paper_edit: prohibited
---

# Development-artifact purge — 2026-08-13

The development-only Python map runs, Internet-image detector runs, bounded
MATLAB packages and the local YOLO26s-pose payload were deleted before the new
campaign. This note is a navigation page; the machine-readable record is
`research/metadata/development-purge-20260813.json`.

The record preserves target paths, file counts, byte counts and prior hashes
for auditability only. It does not preserve the deleted data and must not be
used as experimental evidence. Recovery is not available from this workspace.

## Scope boundary

- The paper/Overleaf source was not edited.
- `backup/paper-current-2026-08-01/` was preserved; the previous raw
  Internet-image cohort and its manifests were explicitly deleted as old
  dataset artifacts. A later four-asset cohort is a separate candidate
  acquisition and remains admission-blocked.
- A new model, dataset or run must use a new protocol freeze, code snapshot
  and run identifier.
- Detector evaluation and cohort preflight no longer contain implicit paths to
  the purged manifest, model or output; every new acquisition must provide
  explicit `--manifest`, `--weights`/`--annotations` and `--output` paths.

[[07_Analysis/current-evidence-index]] ·
[[07_Analysis/protocol-status-20260813]] ·
[[01_Governance/status-and-provenance]]
