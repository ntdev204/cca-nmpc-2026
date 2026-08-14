---
type: dataset-acquisition
status: candidate-acquired
evidence_status: candidate-not-evidence
paper_edit: prohibited
updated_at: 2026-08-14
---

# Real-image cohort acquisition — 2026-08-14

## Acquisition result

Seven real Wikimedia Commons image files were acquired after the clean reset
through the reproducible script `scripts/python/tools/acquire_wikimedia_cohort.py`.
The cohort contains one calibration scene, two in-distribution test scenes, two
OOD person scenes, and two empty-scene controls. Person groups use fixed Commons
page IDs; empty-scene groups use a license-filtered Commons search because the
old fixed category pages were not image assets.

The manifest is
`data/raw/web-cohort-20260814/web-image-manifest.json` (SHA-256
`3c5a7f17ff224d20859fdc04a2f4952a2e6e345fb7b8c81a45f037771d00a5b6`); its
candidate-only preflight is
`research/metadata/pr10-web-cohort-preflight-20260814.json`.

## Visual screening record

| Asset group | Visual screening | Intended use | Annotation status |
|---|---|---|---|
| `outdoor_walking` | one clothed pedestrian in a strongly backlit urban scene | calibration candidate | pending blind boxes |
| `indoor_person` | one seated person viewed from behind indoors | test-ID candidate | pending blind boxes |
| `standing_person` | one standing person at a distant canyon viewpoint | test-ID candidate | pending blind boxes |
| `crowd_ood` | multiple pedestrians at different scales and truncations | test-OOD candidate | pending blind boxes |
| `backlight_ood` | one silhouetted jogger against a bright background | test-OOD candidate | pending blind boxes |
| `empty_indoor` | indoor room with no visible person | negative control candidate | pending blind review |
| `empty_outdoor` | empty street scene with no visible person | negative control candidate | pending blind review |

This visual screening is a source-quality check, not ground truth. No box,
presence label, detector output, model score or confusion-matrix entry is
derived from it. The manifest therefore keeps `approved=false` and
`annotation_status=pending` for every record.

## Gates still open

- independent blinded person bounding-box annotation and adjudication;
- privacy/ethics review for visible people;
- detector pretraining-overlap review;
- cohort expansion before any detector metric or model selection.

The cohort is suitable for preparing the real-image workflow, but it is not
scientific evidence and must not be cited as a detector result. No human future
trajectory is stored or drawn.

## Current gate

The manifest preflight is `PASS` with seven unique real non-AI media records,
valid rights/privacy fields and zero approved records. Admission remains
`BLOCKED` until independent blinded boxes, adjudication, pretraining-overlap
review and held-out expansion are complete.

## Fresh instrument replay — 2026-08-14

The previous detector diagnostic was deleted before replay. The official
YOLO26s-pose checkpoint was downloaded again and run on all seven images at CPU
device in `experiments/runs/person-web-inference-20260814/inference/`. The
scene-tag diagnostic matrix at confidence 0.25 is `[[2,0],[0,5]]`; this is not
ground-truth evidence because the manifest tags are not blinded annotations.
The gallery records the local LSTM checkpoint path as provenance and explicitly
states that no context snapshot or future human path was supplied.

## Knowledge links

[[07_Analysis/current-evidence-index]] · [[07_Analysis/completion-audit]] ·
[[07_Analysis/protocol-status-20260813]] · [[07_Analysis/pr10-preflight-20260813]] ·
[[07_Analysis/yolo26s-pose-candidate-acquisition-20260814]] ·
[[06_Methods/dataset-protocol]] · [[01_Governance/status-and-provenance]]
