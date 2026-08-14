---
type: source-note
status: screening-primary
evidence_status: preprint-abstract
evidence_level: abstract
citekey: humain2026implicit
doi:
zotero_uri:
verified_date: 2026-08-12
---

# HumAIN (2026) — implicit social cues for human-aware navigation

## Bibliographic verification

- [arXiv record](https://arxiv.org/abs/2607.07357) identifies a July 2026
  preprint on human-aware implicit social robot navigation.
- Only the public abstract was used in this refresh; peer-review, venue,
  correction/retraction, and full-text extraction remain open.

## Relevance and boundary

The abstract describes a teacher--student knowledge-distillation pipeline using
images, skeletal keypoints, robot state, and goal information to infer
human-aware planning representations. This is adjacent evidence that pose or
implicit social cues and learned planning are active research directions, but it
does not establish a chance-risk allocator, position-state Mecanum NMPC with
body-velocity commands, or a
real-robot result that can replace the project's evidence.

## Consequence for the gap

YOLO26s-pose and LSTM must remain measurement/prediction interfaces rather than
being advertised as a new perception architecture. Any learning result in this
study needs a fixed split, independent OOD evaluation, and a controller-level
ablation.

## Links

- [[03_Literature/source-index]]
- [[03_Literature/web-verified-gap-sources]]
- [[04_Research_Gap/research-gap]]

Related hub: [[00_MOC/project-map]]
