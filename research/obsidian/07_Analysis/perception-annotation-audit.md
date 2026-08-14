---
type: annotation-audit
status: candidate-acquired-blocked
evidence_status: candidate-not-evidence
paper_edit: prohibited
updated_at: 2026-08-14
---

# PR10 — Audit annotation và perception

Superseded Internet-image cohorts, manifests, detector payloads and prediction
packages were purged under [[07_Analysis/development-artifact-purge-20260814]].
A new seven-image Wikimedia candidate cohort is now retained at
`data/raw/web-cohort-20260814/`; it passed structural preflight but remains
blocked from admission.

## Mechanical preflight contract

The future preflight must exercise schema, media hash/byte/decode/dimension,
blind-bbox binding, source-group split, rights and privacy checks. Independent
adjudication, pretraining-overlap review and ID/OOD expansion remain required
before admission.

## Current diagnostic boundary

The stale YOLO26s-pose diagnostic was purged before a fresh run. The current
diagnostic is at `experiments/runs/person-web-inference-20260814/inference/`.
It uses manifest
scene tags only, not blind ground truth, and is marked `candidate-not-evidence`.
The image-level matrix `[[2,0],[0,5]]` and CPU latency are descriptive plumbing
outputs; no AP, blind-box metric, calibration or target-device claim is open.
Every gallery image shows the local LSTM checkpoint path with
`context=not-provided`; no fabricated speed/direction and no future human path
are drawn.

## Cách mở lại

Annotator thứ hai phải tạo một manifest độc lập, cùng guideline nhưng khác
`annotator_id`; adjudicator thứ ba phải ghi agreement, matched IoU, presence
agreement và mọi asset thay đổi. Chỉ sau đó mới được freeze detector/tool
version, mở lại diagnostic và tính AP/precision/recall/image-level confusion
matrix. A future image-level matrix is only a diagnostic and never a
replacement for blind bbox metrics. Superseded metrics do not exist in the
workspace and must not be reconstructed from a hash.

YOLO26s-pose vẫn chỉ là instrument đo bbox/keypoint. LSTM chỉ nhận context hiện
tại (position/speed/direction/confidence/validity); ảnh tĩnh hiện chỉ ghi
provenance path, không vẽ human future trajectory hoặc robot local path.

[[06_Methods/perception-protocol]] · [[06_Methods/dataset-protocol]] ·
[[07_Analysis/pr10-preflight-20260813]] ·
[[07_Analysis/web-cohort-acquisition-20260814]] ·
[[07_Analysis/yolo26s-pose-candidate-acquisition-20260814]] ·
[[01_Governance/status-and-provenance]]
