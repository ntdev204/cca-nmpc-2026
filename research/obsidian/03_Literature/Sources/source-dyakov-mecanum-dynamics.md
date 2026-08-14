---
type: source-note
status: included-provisional
evidence_status: publisher-metadata-and-abstract
evidence_level: abstract
citekey: dyakov2024mecanum
doi: 10.17816/2074-0530-629873
zotero_uri:
verified_date: 2026-08-12
---

# Dyakov and Fedorov (2024) — Mecanum geometry, dynamics, and drive torque

## Bibliographic verification

- [Publisher landing page](https://journal.hep.com.cn/2074-0530/EN/10.17816/2074-0530-629873)
  reports *Izvestiya MGTU MAMI*, 2024, 18(2), 139--148, DOI
  `10.17816/2074-0530-629873`.
- The page identifies a research article on Mecanum geometry, rolling contact,
  vehicle/wheel velocities, and the driving torque required for motion.
- Full-text correction/retraction and Zotero collection admission remain open.

## Relevance to CCA--NMPC

The work uses multibody simulation and a rolling-contact description to derive
kinematic and dynamic characteristics of a Mecanum vehicle. It is therefore a
relevant plant-model and torque-accounting prior, but it does not establish a
context-aware NMPC, human-motion interface, LSTM predictor, or fixed-budget risk
allocator.

## Consequence for the gap

The Mecanum platform and its actuator model cannot be presented as algorithmic
novelty by themselves. The study must state which plant and body-velocity input
assumptions are retained, identify slip/contact mismatch, and measure the
command/kinematic feasibility limits directly.
The remaining question is the controlled CCA interface and its matched
closed-loop evidence, not the existence of Mecanum dynamics equations.

## Links

- [[03_Literature/source-index]]
- [[03_Literature/web-verified-gap-sources]]
- [[04_Research_Gap/research-gap]]

Related hub: [[00_MOC/project-map]]
