# PR01 open-retrieval staging

This directory is the default destination for candidate bundles produced by
`scripts/python/tools/pr01_run.py --execute`.

Candidate bundles contain hashed raw Crossref and Semantic Scholar JSON responses and
machine-readable execution provenance. They are not accepted search evidence and the
runner never updates `pr01_search_manifest.json`, `pr01_raw_search_export_manifest.json`
or `pr01_gap_decision.json`. Promotion requires an explicit independent validation step.

An interrupted request leaves an `IN-PROGRESS` bundle with only the completed
query parts. Such a bundle is retained as a candidate audit trail, but it is
not a database export, PRISMA count, or novelty evidence.

The generated bundle payloads are machine-local and ignored by Git. No PDF or full-text
download is performed by this workflow.
