---
type: model-acquisition
status: candidate-not-evidence
paper_edit: prohibited
updated_at: 2026-08-14
---

# YOLO26s-pose candidate acquisition — 2026-08-14

The official `yolo26s-pose.pt` checkpoint was downloaded again from the
Ultralytics release asset after the stale diagnostic package was purged. It is
stored at `experiments/runs/person-web-inference-20260814/yolo26s-pose.pt`. The payload
is an external perception interface for person boxes/keypoints; it is not a new
detector contribution and no local detector training was performed.

## Provenance

- checkpoint SHA-256: `A083ADB42303728AE14C4BD6BD56D80DA46F82FB2564DBD6F31DCC92EA321646`
- size: `24,151,790` bytes
- source: [Ultralytics pose release asset](https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26s-pose.pt)
- documentation: [Ultralytics pose task](https://docs.ultralytics.com/tasks/pose)
- runtime: Ultralytics `8.4.16`, PyTorch `2.11.0+cpu`, CPU only
- structured record: `research/metadata/yolo26s_pose_acquisition_20260814.json`

## Admission boundary

The model remains `candidate-not-evidence`. The seven real Wikimedia images in
[[07_Analysis/web-cohort-acquisition-20260814]] have pending annotations and
are not ground truth. The fresh diagnostic package is
`experiments/runs/person-web-inference-20260814/inference/`; it uses manifest
scene tags only and is marked `candidate-not-evidence`. Its descriptive
image-level matrix is `[[2,0],[0,5]]` at confidence `0.25`, with CPU
P50/P95/max latency `313.43/505.37/544.43 ms`. Blind bounding-box metrics are
unavailable. The evaluation overlay visibly records the local LSTM checkpoint
path while declaring `context=not-provided`; it draws no human future
trajectory and no robot local path. Blinded annotations are still required
before any valid detector metric package can be admitted.

## Contract-only sanity check

The checkpoint loaded successfully on CPU and returned the required `[N, 17, 2]`
pose tensor for all seven images. The diagnostic is a plumbing check only; no
blind boxes, calibration, target-device timing or model-selection decision is
derived from it.

The next gates are independent annotation/adjudication, privacy and ethics
review, detector-pretraining overlap review, held-out cohort expansion, and
target-device timing. The checkpoint is not yet placed in `models/registry.json`
as a verified model; the registry remains reserved for a frozen, auditable
candidate record after the data gate is satisfied.

## Public ground-truth diagnostic — 2026-08-14

To obtain a measurable box diagnostic without inventing labels, the official
Ultralytics COCO8-pose subset was downloaded from its public release archive.
The four validation images and provider boxes are recorded in
`data/raw/coco8-pose-20260814/coco8-pose-manifest.json` and
`data/raw/coco8-pose-20260814/coco8-pose-bbox-annotations.json`; the mechanical
preflight is `research/metadata/coco8_pose_preflight_20260814.json`.

At confidence `0.25` and IoU `0.5`, the fresh CPU run
`experiments/runs/coco8-pose-inference-20260814/` retained 14 provider person
boxes and produced TP `11`, FP `1`, FN `3`, precision `0.9167`, recall
`0.7857`, F1 `0.8462`, and mean matched IoU `0.8562`. The image-level matrix
is `[[0,0],[1,3]]` because all four images are positive; a meaningful
specificity estimate is therefore unavailable. CPU latency was P50 `324.91`
ms, P95 `573.17` ms and maximum `603.18` ms. Bootstrap intervals are
descriptive only because the cohort has four images.

These boxes are official provider annotations created before this inference,
so `blinded_to_predictions=true`, but they are **not independent human
annotation or adjudication**. The preflight consequently remains
`PASS / admission BLOCKED`; detector-pretraining overlap, privacy release,
independent annotation/adjudication, cohort expansion and held-out OOD review
remain open. No metric from this package is eligible for a paper claim or
model selection.

## Visual overlay check

The first COCO8-pose gallery frame was inspected after inference. The image
contains the detected person boxes/keypoints and the resolved local LSTM
checkpoint path (`LSTM PATH: ...`). It does not draw a future human trajectory
or a robot local path. This verifies the model-path provenance overlay only;
it is not a visual-quality or detector-accuracy claim.

## Knowledge links

[[07_Analysis/web-cohort-acquisition-20260814]] · [[06_Methods/perception-protocol]] ·
[[03_Literature/Sources/source-ultralytics-yolo26-pose]] ·
[[07_Analysis/current-evidence-index]] · [[01_Governance/status-and-provenance]]
