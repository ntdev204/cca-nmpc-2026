---
type: provenance-note
status: completed
evidence_status: provenance-only
paper_edit: prohibited
---

# Development-artifact purge — 2026-08-14

The user requested a clean reset before the next confirmatory campaign. All
currently retained candidate datasets, detector/LSTM weights, detector output
packages, and development simulation runs were deleted from the workspace.
The machine-readable audit is
`research/metadata/development-purge-20260814.json`.

The purge removed 55 files (59,260,346 bytes) from the exact allowlist in the
audit. It did not edit or build the paper, delete the `backup/` paper snapshot,
or remove source code, schemas, protocols, Zotero exports, or Obsidian
research notes. Hashes in the audit identify removed artifacts only and cannot
be used as experimental evidence.

The registries are now empty for datasets, models, experiments, and generated
artifacts. A new image cohort, target-compatible context recording, LSTM
checkpoint, simulation run, or physical capture must receive a new protocol
freeze, code snapshot, run identifier, calibration/provenance package, and
independent acceptance before it is retained.

The purge script is
`scripts/python/tools/purge_candidate_payloads.py`; its allowlist is explicit
and bounded to the paths recorded in the audit.

Related: [[07_Analysis/completion-audit]] ·
[[07_Analysis/current-evidence-index]] ·
[[01_Governance/status-and-provenance]] ·
[[00_MOC/project-map]]
