# Reproducibility quality gates

Tests are necessary controls, but passing tests is not an experimental result. The future
test suite must cover at least:

- JSON Schema validation for every registry and manifest;
- referential integrity among dataset, experiment, and artifact IDs;
- SHA-256 verification and immutable revisions;
- source URL, retrieval date, license, attribution, and privacy metadata for internet
  human images;
- subject/scene/episode-disjoint split leakage and split-fraction checks;
- fixed ML matching/threshold rules and confusion-matrix accounting;
- coordinate-frame and image-calibration checks for observed, ground-truth, and LSTM
  local-path overlays;
- deterministic replay where supported, paired random seeds, and complete baseline and
  ablation matrices;
- statistical summaries, confidence intervals, failure accounting, timing percentiles,
  deadline misses, fallback use, and constraint violations;
- registry refusal when a run is partial, invalidated, unlicensed, or missing provenance;
- unchanged hashes for the single active paper backup.

The test suite must also enforce the local-paper firewall: active source may not
write manuscript source or macros, invoke a TeX build, or default generated output
to a manuscript directory. Backup verification is read-only.

`scripts/python/tools/repo_check.py` now implements the first static
gate: strict duplicate-key JSON loading, Draft 2020-12 schema validation, canonical
JSON/YAML instance checks, present file-reference hashes, and Obsidian frontmatter and
wikilink integrity. The historical PR01 verification option is retained only for
backward-compatibility checks; it is not an active release gate. The active literature
condition is the bounded Zotero/Obsidian focused audit recorded in
`research/metadata/focused_literature_audit.json`.

Host tests, simulation tests, target timing, hardware-in-the-loop, and integrated robot
tests must remain separately labelled.
