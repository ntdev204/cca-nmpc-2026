# Zotero import queue

This local-only queue contains 32 primary-source PDFs and the versioned
`source_manifest.json` used for controlled import into Zotero. The PDFs remain excluded
from Git; the manifest is tracked so every payload is bound by SHA-256.

`web-refresh-2026-08-12.bib` is a metadata-only staging export from the latest
Google/Google Scholar-oriented refresh. Its four records are pending Zotero
import and primary-text/correction checks; they are not part of the 32-PDF
manifest and must not be treated as admitted literature.

The first 27 files were inherited from the pre-cleanup corpus. Their content hashes are
known, but their original download URLs and retrieval times were not preserved; each is
therefore marked `legacy-origin-unresolved` with error `PDF-ORIGIN-UNRESOLVED`. Files
28--32 have verified download URLs/times and are marked `verified-download`. An imported
attachment is not equivalent to source-provenance closure.

Before clearing the queue:

1. import into a dedicated CCA-NMPC Q1 collection as stored copies;
2. retrieve and verify DOI/title/creators/venue/year against the primary source;
3. detect duplicates and corrections/retractions;
4. export the curated collection to `../export/library.bib`;
5. verify the Zotero stored attachment opens after the queue path is unavailable.

Do not treat successful import as literature acceptance. Admission to the gap
synthesis follows the focused Zotero/Obsidian audit: a source needs verified
metadata, an accessible primary text or authoritative record, and a linked
nearest-work/source note. This queue is not a systematic-review workflow.
