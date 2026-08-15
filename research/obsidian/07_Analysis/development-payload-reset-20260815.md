---
type: provenance-note
status: completed
evidence_status: provenance-only
updated_at: 2026-08-15
paper_edit: prohibited
---

# Development payload reset — 2026-08-15

All old local experiment runs, dataset payloads, generated test/build output,
and Python caches were deleted before the real-hardware campaign. The exact
inventory is recorded in
`research/metadata/development-payload-reset-20260815.json`.

The purge removed 405 files (`58,148,030` bytes): 67 experiment/run files,
32 raw dataset files, local native build output, test/lint caches, and Python
bytecode caches. The empty intake directories `experiments/runs/`,
`data/raw/`, `data/processed/`, and `data/manifests/` were recreated. All four
registries remain empty.

The source code, MATLAB/Python/C++ tests, schemas, protocols, references,
Obsidian knowledge base, paper snapshot, and `backup/` were preserved. Test
source remains available for code QA; no old test result or generated payload
remains. Rows in the evidence index that point to deleted paths are historical
provenance only and cannot be used as data or results.

The next real-data run must use a new run identifier, explicit device
configuration, calibration/provenance sidecars, and a fresh acceptance record.
No manuscript edit was made.

Related knowledge: [[07_Analysis/current-evidence-index]],
[[07_Analysis/jetson-lidar-connection-20260814]],
[[07_Analysis/manual-teleop-lidar-mapping-20260814]],
[[01_Governance/status-and-provenance]].
