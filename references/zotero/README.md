# Zotero reference contract

Zotero Desktop is the authoritative reference library. The portable deterministic
export is `references/zotero/export/library.bib`; machine-local attachment `file`
fields are removed, while `references/zotero/export/receipt.json` records the source
inventory, verification counts, timestamp, and SHA-256. Both files are intentionally
eligible for version control.

`references/zotero/import_queue/source_manifest.json` is also versioned. It binds every
local PDF by SHA-256 and distinguishes verified downloads from inherited files whose
original URL/time is unresolved; a content hash alone does not establish source origin.

Workflow:

1. Verify the local Zotero API before inventory or export.
2. Curate DOI, title, creators, venue, year, retraction/correction status, and tags in
   Zotero rather than hand-editing the export.
3. Export only the project collection, remove machine-local attachment paths, record the
   export timestamp and SHA-256, then review missing fields and duplicate works.
4. Use stable BibTeX citation keys in Overleaf. A Zotero item key and a BibTeX citation
   key are different identifiers and must not be interchanged.
5. Re-export after library changes and review the diff before syncing to Overleaf.

Do not add a citation merely because it supports the desired claim; include relevant
contrary results and trace every research-gap statement to the curated corpus.
