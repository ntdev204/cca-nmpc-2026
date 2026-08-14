# Automation boundary

The first accepted automation is the read-only repository contract validator:

```powershell
$env:PYTHONPATH = 'src;scripts/python'
python -B scripts/python/tools/repo_check.py
python -B scripts/python/tools/repo_check.py --require-focused-audit-complete
```

The first command validates all Draft 2020-12 schemas, canonical JSON/YAML instances,
present file-reference hashes, and Obsidian frontmatter/wikilinks. The second is the
focused-audit completion preflight for final evidence release; the archived PR01
workflow is not part of
the active focused-audit scope. Neither command runs data acquisition, training,
simulation, experiments, or manuscript tooling.

Future scripts may freeze splits, capture environments, run simulations/experiments,
compute metrics, render evidence figures, and verify checksums.

All executable tools live in `scripts/python/tools/`; the core packages remain
under `src/`. The active entry points are `ctx_run.py`, `map_run.py`,
`det_eval.py`, `final_pack.py`, `analyze_run.py`, and `repo_check.py`. The
PR01 search manifests and schemas remain only as historical provenance; no PR01
runner is part of the active workflow.
Superseded simulation, generation, figure, and export commands were removed from
the active workflow.

Every executable script must:

- accept a versioned configuration instead of hidden constants;
- emit a run manifest and nonzero exit status on incomplete work;
- record code revision, dataset revision, random seeds, environment, command, timing,
  and output checksums;
- refuse train/test leakage and mutable dataset revisions;
- separate provisional outputs from accepted artifacts;
- avoid writing, editing, or building the paper locally.

Executable tools must default to `experiments/runs/` for run payloads or
`artifacts/payload/` for generated exports. A CLI must not default to `docs/paper`,
emit manuscript macros, or invoke a TeX engine.

Convenience commands are not experimental evidence. Evidence exists only after the run
manifest, metrics, artifacts, and registry entry pass their declared gates.
