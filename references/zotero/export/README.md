# Deterministic export

`library.bib` is the portable, machine-path-free export. `receipt.json` records the
verified Zotero/API inventory, source-manifest hash, export hash, and entry count.
Re-export and replace both files together whenever the curated library changes.

`library_live_2026-08-11.bib` is a separate 43-entry metadata snapshot produced
for the current research-gap audit. It is not the canonical portable export yet:
its newer records require attachment/provenance reconciliation before
`library.bib` and `receipt.json` are updated together.
