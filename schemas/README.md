# Machine-readable evidence contracts

All schemas use JSON Schema Draft 2020-12 and reject unspecified fields where practical.
The registries are intentionally empty, but their future entries must satisfy:

| Registry or manifest | Schema |
| --- | --- |
| `data/registry.json` | `dataset-registry.schema.json` |
| Versioned dataset design/freeze YAML | `dataset-config.schema.json` |
| Versioned simulation configuration | `simulation-config.schema.json` |
| Versioned evaluation configuration | `evaluation-config.schema.json` |
| Versioned physical-experiment configuration | `physical-experiment-config.schema.json` |
| `experiments/registry.json` | `experiment-registry.schema.json` |
| `artifacts/registry.json` | `artifact-registry.schema.json` |
| `models/registry.json` | `model-registry.schema.json` |
| Internet-image provenance manifest | `web-image-manifest.schema.json` |
| Blind person bounding-box annotation manifest | `person-bbox-annotation.schema.json` |
| Per-run provenance manifest | `run-manifest.schema.json` |
| Real-frame LSTM context overlay | `context-overlay.schema.json` plus model/artifact provenance |
| Frozen context recording/episode split | `context-split-manifest.schema.json` |
| Short-history human heading observation | `human-heading-observation.schema.json` |
| Frozen protocol suite | `protocol-freeze-manifest.schema.json` |
| Focused literature audit | `focused-literature-audit.schema.json` |
| PR01 gap decision | `pr01-gap-decision.schema.json` |
| Frozen PR01 search plan | `pr01-search-manifest.schema.json` |
| PR01 raw-search exports | `pr01-raw-search-export-manifest.schema.json` |
| Claim-to-evidence matrix | `claim-evidence-matrix.schema.json` |
| Zotero source-PDF provenance manifest | `zotero-source-manifest.schema.json` |
| Zotero deterministic-export receipt | `zotero-export-receipt.schema.json` |
| Evidence release candidate/freeze | `release-manifest.schema.json` |

Machine identifiers are lowercase slug IDs with exact prefixes: `ds-*`, `model-*`,
`exp-*`, `run-*`, and `art-*`. Claim IDs use
`CLM-(NOV|EMP|T|ML|SIM|HW)-NN`; `CLM-EMP-*` maps only to claim type
`empirical`. A prefix match alone is insufficient: trailing spaces, uppercase slug
text, bare prefixes, arbitrary suffix characters, and an ID/type mismatch are invalid.

Every field documented as a relative path is repository-relative. Such fields reject
drive-letter paths, UNC/POSIX absolute paths, URI schemes (including `file:` and
`https:`), and any `..` path segment. External locations belong only in explicitly
named URI/URL fields. This prevents a machine-local path or download URL from being
mistaken for a reproducible repository reference.

Cross-file invariants must also be tested: IDs are unique, references resolve, revisions
are immutable, split fractions sum to one, leakage keys do not cross splits, and every
accepted checksum matches the external payload. JSON Schema validation alone cannot
establish those properties or scientific validity. Context-overlay validators must
additionally check timestamp ordering, bbox/keypoint geometry, context fields,
frame/calibration hashes and independent visual review. Release validators must reconcile run
accounting totals and ensure that every referenced ID resolves to exactly one immutable
registry entry.

The canonical draft claim ledger is
`research/metadata/claim_evidence_matrix.draft.json`. Its pinned contract sources and
all evidence `file` references must resolve and match their SHA-256 values. Under claim
matrix schema `2.0.0`, a blocked or withdrawn row must state at least one explicit
blocker. A `CLM-T-*` row cannot become `supported` or `approved` unless it contains
`PR02`, at least one canonical assumption ID, at least one proof-obligation ID, at least
one evidence file reference with SHA-256, and a verified verifier record. Cross-file
validation must also reject duplicate claim IDs and unresolved assumption, proof-
obligation, protocol, or artifact IDs.

Schema changes require a new `schema_version`, a migration note in `CHANGELOG.md`, and
revalidation of every existing entry. Never weaken a schema merely to admit a failed or
partial run.

The clean-slate registries contain no scientific entries, so their contract upgrades
required only instance-version migration: dataset/model registries are at `2.0.0`, and
experiment/artifact registries are at `1.2.0`/`1.1.0` respectively. Run manifests and
the three experiment configuration schemas are at `1.2.0`; the dataset configuration, Internet-media,
dataset-registry and model-registry contracts are at `2.0.0`. Context overlays are
validated through the evaluation, model and artifact contracts; no human-trajectory
overlay schema is active.

The claim-to-evidence schema is at `2.0.0`; this incompatible clean-slate revision adds
pinned contract sources, mandatory blockers for blocked/withdrawn rows, and fail-closed
theory admission. There were no earlier matrix instances to migrate. The protocol-freeze
schema is at `1.3.0` and binds a focused-literature audit record rather than a PR01
database decision. Confirmatory work requires the focused audit record and an immutable
protocol-freeze record; it does not require Scopus, Web of Science or IEEE Xplore export.
The simulation, evaluation and physical-experiment schemas were migrated to `1.2.0`, the
experiment registry and run manifest to `1.2.0`, the release schema to `1.1.0`, and the
focused-audit schema is `1.1.0` and hashes the research-gap note alongside the
source synthesis and nearest-work matrix. A protocol freeze is rejected unless the focused
audit record is `COMPLETE`; development templates may still reference an
`IN_PROGRESS` audit before freeze. The new `context-overlay.schema.json` makes the
existing `cca-context-overlay-v1` payload explicit; it accepts current context only
and does not permit human future-trajectory fields. Loader-level checks remain
responsible for heading normalization, direction consistency, timestamp/frame
alignment and source/model hash verification.
PR01 schemas remain frozen historical contracts. Future incompatible changes must bump
the corresponding instance version before any new entry is admitted.

The Zotero source-manifest schema is at `1.0.0`. Every PDF requires a matching
SHA-256. A `verified-download` record requires its source URL and retrieval timestamp;
an inherited record without those facts must use `legacy-origin-unresolved` and retain
the explicit `PDF-ORIGIN-UNRESOLVED` error. Verified sources accept only HTTPS origins
and no unresolved errors. The repository validator also rejects duplicate keys,
citation numbers or normalized DOI values, noncontiguous numbering and retrieval times
after the Zotero export. It reconciles the
manifest hash/counts with `receipt.json` and the portable BibTeX export. The export
receipt schema is at `1.1.0`; it fixes the two repository-relative source/export paths,
rejects unexpected fields, non-UTC timestamps, nonzero quality-gate counts and negative
counts. The repository validator additionally enforces export-before-verification order,
cross-file arithmetic, content-hash reconciliation, exact normalized DOI-set equality
and absence of machine-local BibTeX file/attachment fields.

The PR01 search-plan schema is at `1.2.0` and the raw-export schema is at `1.1.0`.
Those schemas are historical provenance only: their plan retains five databases and
six concept blocks with 30 exact database-specific queries, but none of those
database exports is an active requirement for the original research paper.
The current active condition is the focused-literature-audit schema above; it does
not require Scopus, Web of Science or IEEE Xplore accounts or exports.
Crossref is explicitly a non-exhaustive top-1000 relevance-ranked supplement;
Semantic Scholar is complete only when continuation-token pagination terminates.
The raw manifest records policy satisfaction and hashes every retained response without
equating a source-reported total with the number retrieved. PR01 decision schema `1.2.0`
binds both manifests directly for the archived record. Cross-file validation enforces database/query coverage,
query-snapshot parity, execution timing, part accounting and immutable payload hashes.
