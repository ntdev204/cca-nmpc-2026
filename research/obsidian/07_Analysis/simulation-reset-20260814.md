---
type: development-reset
status: complete
evidence_status: provenance-only
paper_edit: prohibited
updated_at: 2026-08-14
---

# Simulation campaign reset — 2026-08-14

The pre-campaign payload reset was executed before the fresh learning run. The
exact machine-readable audit is
`research/metadata/simulation-reset-20260814.json`.

Deleted outside `backup/`:

- `data/raw/web-cohort-20260814/` — Internet-image cohort and candidate
  presence annotation;
- `experiments/runs/` — all prior map, detector and MATLAB outputs;
- `experiments/commands/` — stale command payloads;
- `models/candidates/` — external detector checkpoint.

The inventory contained 51 files and 36,288,151 bytes. The four registries
remain empty and `backup/paper-current-2026-08-01` was not touched. The purge
script now targets only these exact campaign payload locations and refuses
targets outside the repository or inside `backup/`.

The next run is [[07_Analysis/simulation-learning-campaign-20260814]]. Purge
hashes are provenance only and must not be reconstructed as results.

[[07_Analysis/current-evidence-index]] ·
[[07_Analysis/experimental-analysis]] ·
[[01_Governance/status-and-provenance]]
