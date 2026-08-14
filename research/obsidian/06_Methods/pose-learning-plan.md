---
type: perception-learning-design
status: planned
evidence_status: knowledge-only
---

# Pose and score-learning design

YOLO26s-pose is an external measurement tool. Its abstract interface is

```text
image -> person box + 17 keypoints + confidence + timestamp
```

The adapter must preserve image coordinates, validity masks, model identifier,
and preprocessing version. It must never interpret detector confidence as a
metric covariance before camera/depth/LiDAR calibration.

## Learning boundary

- No supervised direction labels are used to train the LSTM.
- A short observation history supplies a self-supervised velocity/context target.
- A score loop ranks candidates using frozen validation criteria and stops after
  a declared patience rule.
- Optional reinforcement learning may tune bounded allocation or trigger
  parameters only; it may not output body-velocity commands directly or disable
  hard constraints.
- The final test set is opened once after the candidate and score rule are frozen.

## Required contracts

`PoseDetection2D` contains box, keypoints, confidence, masks, timestamp, frame,
and model hash. The CCA snapshot contains only validated metric state, covariance,
context, freshness, and provenance identifiers. Image overlays show perception
and context; map plots show the robot local path.

Related: [[06_Methods/perception-protocol]], [[06_Methods/lstm-protocol]],
[[06_Methods/score-learning-design]], [[06_Methods/dataset-protocol]],
[[04_Research_Gap/research-gap]].

Related hub: [[00_MOC/project-map]]


