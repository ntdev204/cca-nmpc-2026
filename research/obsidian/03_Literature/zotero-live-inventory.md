---
type: zotero-inventory
status: candidate-live-export
date: 2026-08-12
paper_edit: prohibited
---

# Zotero live inventory for the research-gap audit

## API verification

Zotero Desktop 9.0.6, local API v3 and connector are reachable on
`127.0.0.1:23119`. The live export was written to
`references/zotero/export/library_live_2026-08-11.bib` with 43 BibTeX entries;
the export SHA-256 is
`1b80c6c9d2adf4607a83425776fbb90ba3cd7ed8dd5317060a953c2158cb07ea`.

The previously frozen portable export remains 32 entries. The 11 items added
to the Zotero library since that receipt are:

| Key | Scope | Zotero item key |
|---|---|---|
| `le_social_2024` | social navigation + learned human prediction | `552VM8FQ` |
| `nair_predictive_2023` | uncertain multimodal prediction + predictive control | `359XM6X7` |
| `gers_learning_2000` | LSTM forget-gate foundation | `ZEG5KQKH` |
| `jocher_ultralytics_2026` | YOLO26 tool provenance | `H3X52YUZ` |
| `salzmann_robots_2023` | human pose/keypoint trajectory prediction | `5XFZZK2I` |
| `dugas_navrep_2021` | unsupervised navigation representation | `C8QJXHSN` |
| `pfrommer_safe_2022` | safe RL with chance-constrained MPC | `NUXTSG34` |
| `sun_socially_2025` | online uncertainty-driven risk adaptation | `HSR6VLIH` |
| `wang_safe_2025` | risk-adaptive CVaR barrier navigation | `GD55NENG` |
| `engelaar_planning_2026` | elastic chance constraints in SMPC | `L6934LGI` |
| `wang_reinforcement_2026` | differentiable CVaR-barrier risk adaptation | `2JNRX662` |

The Zotero child-item query returned no attachment for the checked new records.
Therefore the live export is metadata/citation evidence only; it is not a
full-text verification of every item. The old `library.bib` and receipt are not
silently overwritten until the attachment/provenance audit is deliberately
reconciled.

## Current-session API recheck — 2026-08-12

A read-only request to `http://127.0.0.1:23119/api/users/0/items` was refused
and no Zotero process was present in the Windows session. The dated export
above remains valid historical provenance for 2026-08-11, but the two new
screening candidates added on 2026-08-12 are not treated as Zotero-admitted
records until Zotero is reopened and the metadata/attachment audit is rerun.

## Current-session API recheck — 2026-08-13

The API endpoint was checked again after the literature refresh and still
refused the connection; no Zotero process was present. The three 2026-08-13
screening notes (Luna--Gasga, Ye--Ren and Pham--Han) therefore remain
`screening-candidate` source notes only. Their DOI/landing-page metadata is
recorded in Obsidian, but no Zotero admission or attachment claim is made.

## Current-session launch recheck — 2026-08-13

The installed `Zotero 9.0.6` Start-menu entry was invoked through the Windows
Apps folder, but no Zotero process appeared and port `127.0.0.1:23119` still
actively refused a read-only API request. The three new risk/benchmark notes
(SICNav, cooperative GP--MPC and dynamic risk-aware MPPI) therefore remain
screening-only as well. No metadata was promoted or edited in the portable
export.

## Current-session API recheck — 2026-08-13 (reachable)

The Zotero skill relaunched Zotero Desktop 9.0.6 and verified local API v3 and
the connector with HTTP 200 at `127.0.0.1:23119`. A read-only inventory returned
43 top-level items, matching the existing live BibTeX export
`references/zotero/export/library_live_2026-08-11.bib` (43 entries,
SHA-256 `1B80C6C9D2ADF4607A83425776FBB90BA3CD7ED8DD5317060A953C2158CB07EA`).

Read-only searches for the newly screened collaborative emergency-protection
paper, ARMS, and dynamic risk-aware MPPI returned no matching Zotero item.
Those candidates therefore remain screening-only source notes; no import was
performed and the 32-entry portable export was not overwritten. This resolves
the API availability check but does not complete metadata/attachment admission.

## Gap implications

- Context-aware MPC, pose-aware prediction, unsupervised representations, safe
  RL, risk adaptation, elastic chance constraints and LSTM foundations all have
  direct records in the live library.
- `YOLO26s-pose + LSTM + NMPC` must remain an implementation stack, not a
  novelty claim.
- The defensible research question remains the causal characterization of a
  compact, transparent, training-free allocation semantics under a fixed total
  budget, with uniform/optimized/heuristic/learned comparators and complete
  failure accounting. The bounded focused audit is now reviewed; final citation
  admission still depends on attachment/provenance checks. A systematic
  database review is not required for this original research paper.

## Current read-only query audit — 2026-08-13 (continuation)

The local API was queried without modifying the library. Exact searches for
`Mecanum model predictive control` and `human-aware navigation MPC` returned no
matching item. `SICNav` returned Zotero item `RMQEU4RJ` (Samavi et al., 2025),
and `LSTM` returned the primary LSTM-gates record `ZEG5KQKH` plus the Huang--
Jafari preprint `5N9RXCHP`. The zero-result queries do not prove absence from
the literature; they only show that these screened candidates are not yet
admitted to this local library. No import or export overwrite was performed.

## Knowledge-link matrix

Các liên kết dưới đây là đường đi tri thức, không phải quyết định đưa nguồn vào
bài báo. Mọi bản ghi mới vẫn giữ `metadata-only` cho đến khi có attachment,
DOI/phiên bản và ghi chú toàn văn được kiểm độc lập.

| Citekey | Nút tri thức chính | Nút phương pháp/đối chiếu | Gate để promote |
|---|---|---|---|
| `le_social_2024` | [[04_Research_Gap/research-gap]] | [[03_Literature/pose-learning-gap]], [[06_Methods/simulation-protocol]] | full-text + focused audit |
| `nair_predictive_2023` | [[03_Literature/nearest-work-matrix]] | [[05_Theory/context-aware-risk-allocation]], [[06_Methods/evaluation-protocol]] | full-text + comparator audit |
| `gers_learning_2000` | [[06_Methods/lstm-protocol]] | [[05_Theory/notation]], [[05_Theory/implementation-parity]] | primary-source metadata + full-text |
| `jocher_ultralytics_2026` | [[06_Methods/perception-protocol]] | [[06_Methods/dataset-protocol]], [[01_Governance/claim-register]] | tool version/license audit |
| `salzmann_robots_2023` | [[03_Literature/pose-learning-gap]] | [[06_Methods/lstm-protocol]], [[04_Research_Gap/research-gap]] | scope check: context only, no human trajectory claim |
| `dugas_navrep_2021` | [[03_Literature/literature-synthesis]] | [[06_Methods/score-learning-design]], [[08_Decisions/decision-register]] | full-text + learning-scope audit |
| `pfrommer_safe_2022` | [[03_Literature/nearest-work-matrix]] | [[05_Theory/proof-obligations]], [[06_Methods/evaluation-protocol]] | full-text + safety-claim audit |
| `sun_socially_2025` | [[03_Literature/prior-art-delta]] | [[05_Theory/context-aware-risk-allocation]], [[04_Research_Gap/research-gap]] | full-text + novelty delta |
| `wang_safe_2025` | [[03_Literature/prior-art-delta]] | [[05_Theory/context-aware-risk-allocation]], [[06_Methods/statistical-analysis]] | full-text + comparator audit |
| `engelaar_planning_2026` | [[03_Literature/nearest-work-matrix]] | [[05_Theory/context-aware-risk-allocation]], [[05_Theory/proof-obligations]] | full-text + theorem-boundary audit |
| `wang_reinforcement_2026` | [[06_Methods/score-learning-design]] | [[05_Theory/context-aware-risk-allocation]], [[08_Decisions/decision-register]] | full-text + RL safety-boundary audit |

## Position-state screening links — 2026-08-13

The latest exact-title queries returned no local Zotero item for the records in
[[03_Literature/Sources/source-position-state-boundary-20260813]]. They remain
Obsidian screening nodes only and are not promoted into the portable BibTeX
export. Their role is to tighten the gap and benchmark boundary, not to supply
paper citations before attachment/metadata admission.

The matrix prevents a live export from becoming an isolated bibliography: every
record is attached to a gap, a mathematical obligation or a reproducible method
decision. No link in this table authorizes a manuscript edit.

## Boundary

This inventory updates internal research only. No LaTeX, Overleaf, manuscript
or professor-facing file was edited. Before using any new key in a final paper,
verify DOI metadata, attachment provenance and the focused-audit source note.
No PR01/SLR decision is required.

## Attachment spot-check — 2026-08-13

Read-only child-item queries were run for five records that influence the active
gap: SICNav (`RMQEU4RJ`) has one `Full Text PDF` child (`6YMXDJ86`), while the
current LSTM-gates foundation (`ZEG5KQKH`), YOLO26 tool record (`H3X52YUZ`),
elastic chance-constraint paper (`L6934LGI`) and differentiable CVaR paper
(`2JNRX662`) returned no child attachment. These results do not invalidate the
metadata records, but they keep the latter four at metadata-only status and
prevent a full-text claim until a verified attachment or authoritative full text
is recorded. No Zotero item was edited or imported.

## Attachment recheck — 2026-08-13 (current session)

The local API and connector were reachable during this recheck. Read-only child
queries confirmed one PDF child for SICNav (`RMQEU4RJ` -> `6YMXDJ86`) and no
child attachment for the current LSTM-gates foundation (`ZEG5KQKH`), YOLO26 tool
record (`H3X52YUZ`), elastic chance-constraint paper (`L6934LGI`), differentiable
CVaR paper (`2JNRX662`), pose prediction (`5XFZZK2I`), NavRep (`C8QJXHSN`), safe
RL (`NUXTSG34`), online risk adaptation (`HSR6VLIH`) or CVaR barrier navigation
(`GD55NENG`). The 43-item inventory therefore remains a mixed metadata/full-text
set; no new record is promoted to full-text evidence and no portable BibTeX
export is overwritten. The bounded audit remains closed for gap scope while the
mixed evidence set stays excluded from final citation promotion; the explicit
negative evidence that broad novelty claims are occupied is preserved.

## Current read-only query audit — 2026-08-13 (latest screening refresh)

Exact-title Zotero searches for the three newest screening records returned no
matching local item:

- `Pedestrian-Aware Control of AMRs Using Model Predictive Speed Control`
- `Accompaniment and collision avoidance for a cane-type robot`
- `Consolidated Control Architecture for Mecanum-Wheeled Mobile Robots`

The authoritative landing-page metadata is therefore retained in Obsidian only;
no import or portable BibTeX overwrite was performed. This is an explicit
screening boundary, not evidence that the works are absent from the literature.

## Related notes

[[00_MOC/project-map]] · [[03_Literature/literature-review]] · [[04_Research_Gap/research-gap]]

