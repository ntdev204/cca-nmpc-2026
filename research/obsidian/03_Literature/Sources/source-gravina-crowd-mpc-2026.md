---
type: source-note
status: screening-candidate
evidence_status: publisher-full-text
evidence_level: full-text
citekey: gravina2026crowdmpc
doi: 10.3389/frobt.2026.1812386
zotero_uri:
verified_date: 2026-08-14
---

# Gravina et al. (2026) — Crowd navigation with multisensor MPC

## Bibliographic verification

- [Frontiers full text](https://doi.org/10.3389/frobt.2026.1812386) identifies
  the article *Crowd navigation in a multi-room environment: a model
  predictive control framework for mobile robots* and its 2026 publication.
- The publisher page was inspected again on 2026-08-14. Zotero admission,
  complete metadata export and correction/retraction checks remain open.

## Method and evidence

The article combines 2D LiDAR and RGB-D semantic information, Kalman-filter
human-state estimation, model predictive control and discrete-time control
barrier constraints. The abstract reports high-fidelity simulation and
real-world TIAGo experiments over multiple crowd and room configurations.

## Consequence for the gap

Sensor fusion, human-state prediction, MPC safety constraints and robot trials
are already established components. The present work must isolate the CCA
interface, keep the Mecanum plant and fixed-clearance policy explicit, and
provide direct sensor/timing provenance instead of presenting perception--MPC
integration as novelty.

## Links

- [[03_Literature/source-index]]
- [[03_Literature/web-verified-gap-sources]]
- [[04_Research_Gap/research-gap]]

Related hub: [[00_MOC/project-map]]
