---
type: source-note
status: included-provisional
evidence_status: publisher-full-text
evidence_level: full-text
citekey: crowdmpc2026multisensor
doi: 10.3389/frobt.2026.1812386
zotero_uri:
verified_date: 2026-08-12
---

# Crowd navigation in a multi-room environment (2026) — sensor-based MPC with real validation

## Bibliographic verification

- [Publisher full text](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2026.1812386/full)
  identifies an original research article in *Frontiers in Robotics and AI*,
  published 27 July 2026, DOI `10.3389/frobt.2026.1812386`.
- The publisher page provides the method and experimental sections; a Zotero
  item, correction/retraction check, and source-license record remain to be
  completed.

## Method and evidence

The framework fuses 2-D LiDAR with RGB-D semantic information, uses Kalman
filters for human-state estimation, and integrates predictions into MPC with
discrete-time control-barrier constraints. It reports high-fidelity simulation
and real-world experiments on a TIAGo platform, including sensor-aware crowd
navigation and emergency-stop handling.

## Consequence for the gap

Sensor fusion, human-state prediction, global-to-local navigation, MPC safety
constraints, and real-robot evaluation are already present in a close system
paper. The CCA study must not claim these ingredients as independent novelty;
it must separate perception from allocation and report the Astra S/N10P
configuration, direct CSV provenance, calibration/OOD performance, and matched
controller contrasts. The platform is differential-drive, so it is a boundary
comparator rather than a Mecanum-equivalent benchmark.

## Links

- [[03_Literature/source-index]]
- [[03_Literature/web-verified-gap-sources]]
- [[03_Literature/nearest-work-matrix]]
- [[04_Research_Gap/research-gap]]

Related hub: [[00_MOC/project-map]]
