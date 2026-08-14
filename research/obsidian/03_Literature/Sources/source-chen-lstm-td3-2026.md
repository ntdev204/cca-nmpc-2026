---
type: source-note
status: screening-candidate
evidence_status: publisher-metadata-and-abstract
evidence_level: abstract
citekey: chen2026saltd3
doi: 10.1038/s41598-026-45819-0
zotero_uri:
verified_date: 2026-08-12
---

# Chen et al. (2026) — Self-attention LSTM with TD3 for dynamic navigation

## Bibliographic verification

- [Scientific Reports record](https://www.nature.com/articles/s41598-026-45819-0)
  identifies the 2026 article, DOI `10.1038/s41598-026-45819-0`, and describes
  a Self-Attention LSTM TD3 navigation method.
- Only the publisher metadata and abstract were used in this refresh. Zotero
  admission, full-text extraction, venue correction/retraction checks and the
  reported deployment details remain open.

## Relevance and boundary

The abstract places an LSTM temporal representation inside a reinforcement-
learning navigation policy and reports simulation, unseen-configuration and
real-world validation. This is direct evidence that LSTM plus learning-based
dynamic navigation is an active nearby direction. It does not establish a
CCA risk allocator, position-state Mecanum NMPC with body-velocity commands,
fixed-clearance comparison or
the project's no-human-trajectory interface.

## Consequence for the gap

LSTM and reinforcement learning must remain interfaces or explicitly declared
comparators, not standalone novelty claims. Any score-loop claim must separate
policy learning from CCA allocation and report matched controller, calibration,
OOD and failure outcomes.

## Links

- [[03_Literature/source-index]]
- [[03_Literature/web-verified-gap-sources]]
- [[04_Research_Gap/research-gap]]

Related hub: [[00_MOC/project-map]]
