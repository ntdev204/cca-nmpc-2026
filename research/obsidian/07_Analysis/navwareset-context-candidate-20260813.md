---
type: source-analysis
status: purged-provenance-only
date: 2026-08-13
paper_edit: prohibited
---

# NavWareSet context candidate — 2026-08-13

NavWareSet scene 13 was previously inspected from the public project repository
under the stated CC BY-SA 4.0 license. Its local raw/processed files,
checkpoint and score-loop output were removed by the 2026-08-14 clean reset.
No ROS runtime or rosbag playback was used. The source remains a literature and
dataset-design reference, not a Mecanum/Astra-S/N10P capture or retained result.

## Conversion

`navwareset_context.py` selected participant track 1 and transformed its
published world coordinates into the robot-local frame using the published
robot pose. Current position, finite-difference speed and the four direction
tokens were written to a context-only CSV. The converter does not create a
future human path; it records only the observed sequence and a self-supervised
next-velocity target is constructed by `ctx_run.py` at training time.

The former provenance paths are retained only in
`research/metadata/development-purge-20260814.json` as hashes for audit.

## Rejected development result (not retained)

Former score-loop numbers, confusion matrices and checkpoint details are
intentionally not reproduced here. They were development-only and were purged;
this note records only the data-design lessons and the target-platform
incompatibility.

## Admission boundary

This source remains `purged-provenance-only`. It lacks target-platform
camera frames, Astra-S/N10P calibration, target robot geometry, independent
annotation and a frozen ID/OOD split. It may validate the mechanics of the
self-supervised LSTM score loop, but it cannot support a claim about the
Mecanum robot, hardware timing, detector performance or CCA-NMPC safety. The
locked Overleaf manuscript was not edited or built.

## Knowledge links

[[06_Methods/lstm-protocol]] · [[07_Analysis/experimental-analysis]] ·
[[07_Analysis/protocol-status-20260813]] · [[07_Analysis/current-evidence-index]] ·
[[04_Research_Gap/research-gap]] · [[00_MOC/project-map]]
