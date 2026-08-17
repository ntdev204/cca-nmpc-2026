---
type: methods-overview
status: protocol-frozen-for-development
evidence_status: no-results-after-reset
---

# Methods overview

## Causal pipeline

```text
real Internet image or sensor frame
  -> YOLO26s-pose measurement interface
  -> short-history position/speed/direction context
  -> self-supervised score-trained LSTM inside CCA
  -> context validity and local-path trigger on the Python map
  -> fixed-budget risk allocation
  -> position-state Mecanum CCA-NMPC with body-velocity command
  -> paired controller and safety metrics
```

YOLO26s-pose is replaceable instrumentation. LSTM is a context component of CCA,
not a separate contribution. CCA-NMPC may predict future human positions
internally from the causal context velocity, but no predicted trajectory is
stored in the image branch or drawn on the image. The global path is fixed;
only the local robot path is regenerated after a registered conflict or
direction change.

The physical-data boundary is direct CSV/JSON: no ROS, ROS 2 or rosbag runtime is
part of the active pipeline. The physical state is
`[x,y,theta,vx,vy,omega]`; the STM interface receives body velocity commands and
does not require torque/current feedback. A real run is accepted only after the recorder
produces the four CSV files and `map.json`, and `final_pack.py` seals their
checksums and declared sensor/firmware identity.

## Staged evidence

| Stage | Question | Evidence ceiling |
|---|---|---|
| S0 | Do formulas, schemas, and imports agree? | software consistency only |
| S1 | Does the map/controller mechanism behave under paired scenarios? | simulation scope only |
| S2 | Does the perception/context interface replay on real media? | recorded-media scope only |
| S3 | Does the implementation meet timing and sensor contracts? | declared HIL platform only |
| S4 | Does the physical robot satisfy the safety gate? | tested robot/site only |

Never promote evidence from one stage to another.

## Protocol links

[[06_Methods/dataset-protocol]] · [[06_Methods/perception-protocol]] ·
[[06_Methods/lstm-protocol]] · [[06_Methods/simulation-protocol]] ·
[[06_Methods/evaluation-protocol]] · [[06_Methods/statistical-analysis]] ·
[[06_Methods/final-run-data-package]] · [[06_Methods/robot-console-architecture]]

Related: [[04_Research_Gap/research-gap]], [[05_Theory/system-model]],
[[06_Methods/execution-roadmap]].

Related hub: [[00_MOC/project-map]]

