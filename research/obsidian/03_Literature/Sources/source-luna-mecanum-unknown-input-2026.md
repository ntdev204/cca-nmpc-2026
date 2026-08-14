---
type: source-note
status: screening-candidate
evidence_status: publisher-full-text-and-abstract
evidence_level: abstract-plus-landing-page
citekey: luna2026mecanumunknowninput
doi: 10.1016/j.ejcon.2026.101466
zotero_uri:
verified_date: 2026-08-13
---

# Luna et al. (2026) — Robust unknown-input estimation for Mecanum robots

## Bibliographic verification

- [European Journal of Control record](https://doi.org/10.1016/j.ejcon.2026.101466)
  identifies volume 88 (March 2026), article 101466 and DOI
  `10.1016/j.ejcon.2026.101466`.
- The publisher abstract describes a convex qLPV unknown-input observer for
  simultaneous actuator-fault and model-uncertainty estimation in a four-wheel
  Mecanum robot. Zotero admission and correction/retraction checks remain open.

## Relevance and boundary

The paper treats wheel slip, actuator effectiveness loss, disturbances and
sensor noise as coupled sources of uncertainty, with an $\mathcal{H}_\infty$
criterion and LMI-based sufficient conditions. It is an observer/fault-
diagnosis contribution, not a human-aware CCA allocator or position-state NMPC
benchmark.

## Consequence for the gap and experiments

The result strengthens the requirement to identify or bound actuator/model
mismatch before interpreting CCA-NMPC results. The present study should report
applied torque, wheel-speed limits, delay/slip indicators and estimator error,
but must not import the qLPV observer or its stability claims into the active
model without a separate amendment.

## Links

- [[03_Literature/source-index]]
- [[03_Literature/web-verified-gap-sources]]
- [[03_Literature/nearest-work-matrix]]
- [[04_Research_Gap/research-gap]]

Related hub: [[00_MOC/project-map]]
