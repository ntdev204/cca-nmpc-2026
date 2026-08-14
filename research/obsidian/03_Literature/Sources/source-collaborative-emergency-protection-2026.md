---
type: source-note
status: screening-candidate
evidence_status: publisher-metadata-and-abstract
evidence_level: abstract
citekey: collaborative2026emergencyprotection
doi: 10.1109/LRA.2026.3671537
zotero_uri:
verified_date: 2026-08-13
---

# Collaborative optimization and emergency protection (2026)

## Bibliographic verification

- The [IEEE Robotics and Automation Letters record](https://doi.org/10.1109/LRA.2026.3671537)
  identifies the 2026 article *Collaborative Optimization Framework of
  Interactive Motion Planning and Emergency Protection Control for Human-Robot
  Interaction* and DOI `10.1109/LRA.2026.3671537`.
- The publisher landing page was reachable only through a JavaScript challenge
  in this session. The title, venue, DOI and abstract-level description are
  therefore screening evidence, not a full-text extraction. Zotero admission,
  version/correction checks and independent reproduction remain open.

## Relevance and boundary

The abstract describes a framework that coordinates nominal motion planning with
an emergency protection controller using stochastic MPC and a sparse scenario
tree for anticipated collision events. This is adjacent prior art for
interaction-aware planning and emergency fallback. It does not establish the
current transparent fixed-budget context allocator, current-snapshot LSTM
interface, position-state Mecanum plant with body-velocity commands, or the
contract that keeps any CCA-NMPC future-position sequence internal and off
images/raw artifacts.

## Consequence for the gap

The paper must not present interactive planning, stochastic MPC, scenario-tree
anticipation or emergency protection as standalone novelty. The remaining
candidate gap stays narrow: an empirically falsifiable fixed-budget CCA
interface inside position-state Mecanum NMPC, evaluated against matched MPC,
NMPC, DWA and MPPI baselines. No paper claim is changed by this
screening record.

## Links

- [[03_Literature/source-index]]
- [[03_Literature/web-verified-gap-sources]]
- [[04_Research_Gap/research-gap]]

Related hub: [[00_MOC/project-map]]
