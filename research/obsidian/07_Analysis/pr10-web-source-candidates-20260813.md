---
type: pr10-source-discovery
status: purged-provenance-only
evidence_status: landing-page-only
paper_edit: prohibited
discovered_at: 2026-08-13
---

# PR10 web-source candidates — 2026-08-13

This is a source-discovery and provenance record, not a detector result. The
earlier Bromo/Nairobi scratch media and the later Wikimedia candidate cohort
were removed by the 2026-08-14 clean reset. The former paths and hashes are
audit history only; no image, annotation, preflight result or metric from this
note is retained or admissible. A new cohort must be acquired under a new ID
and pass independent annotation, adjudication, pretraining-overlap review and
OOD expansion before PR10 can open.

## Discovery query

The Wikimedia Commons API was queried with:

```text
people walking filetype:bitmap
```

The API response was checked for a public landing page, image URL, declared
license, dimensions, and creator metadata. Candidates were retained only as
possible real-media additions; artwork, low-resolution files, and any source
without a page-level license check must be excluded before download.

## Candidate landing pages

| Candidate | Landing page | Declared license | Intended stratum | Status |
|---|---|---|---|---|
| People walking in Bromo | [Commons page](https://commons.wikimedia.org/wiki/File:People_walking_in_Bromo.jpg) | CC BY 2.0 | outdoor / multi-person | discovery only; not local |
| People walking on the street in Nairobi | [Commons page](https://commons.wikimedia.org/wiki/File:People_walking_on_the_street_in_Nairobi,_Kenya.jpg) | CC BY 4.0 | urban / multi-person | discovery only; not local |
| People walking the Gwynns Falls Trail | [Commons page](https://commons.wikimedia.org/wiki/File:People_walking_the_Gwynns_Falls_Trail.png) | CC BY-SA 3.0 | outdoor / elevated view | discovery only; not local |
| Throngs walking towards Himeji Castle | [Commons page](https://commons.wikimedia.org/wiki/File:Throngs_of_people_walking_towards_Himeji_Castle,_Himeji,_2016.jpg) | CC0 | crowd / outdoor | discovery only; not local |
| Young people walking in Hungary | [Commons page](https://commons.wikimedia.org/wiki/File:Young_people_walking_in_the_street,_Hungary_2011.jpg) | CC0 | street / small group | discovery only; not local |

## Admission rule

Before any candidate is added to `person_context_manifest.json`, the source
page, download bytes, SHA-256, decoder dimensions, privacy basis, and split
group must be recorded. A second annotator and adjudicator must then review the
bounding boxes. Until that happens, `approved=false` and
`admission_status=BLOCKED` remain mandatory.

Related records: [[07_Analysis/pr10-preflight-20260813]] ·
[[07_Analysis/perception-annotation-audit]] ·
[PR10 protocol](../../../protocols/PR10_person_data_acquisition.md) ·
[[03_Literature/web-verified-gap-sources]]

## Reset boundary

The former candidate cohort, manifests, preflight report and detector
diagnostics were deleted by the 2026-08-14 clean reset. No local bytes,
annotation, metric or model checkpoint remains. The landing pages above are
research-discovery links only and are not a dataset or a detector evaluation.

Related methods: [[06_Methods/dataset-protocol]] ·
[[06_Methods/perception-protocol]] · [[07_Analysis/perception-annotation-audit]]
