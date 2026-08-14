---
type: source-note
status: included-provisional
evidence_status: accepted-preprint-full-text
evidence_level: full-text
citekey: trepella2026sfmnmpc
doi:
zotero_uri:
verified_date: 2026-08-12
---

# Trepella et al. (2026) — Social-force NMPC for human-aware navigation

## Bibliographic verification

- [Accepted-version record](https://arxiv.org/abs/2607.10374) identifies the
  paper as accepted for IROS 2026; the final IEEE Xplore version is not yet
  available in this audit.
- The full HTML/PDF preprint was read on 2026-08-12. Venue, correction, and
  retraction status remain provisional until the proceedings record is checked.

## Method and evidence

The paper embeds a Social Force Model in the NMPC prediction loop and adds
social costs for personal distance, relative heading, and social work. It uses
HuNavSim/Gazebo scenarios, evaluates 30 repetitions per scenario, and compares
NMPC variants with MPPI, DWB, ORCA, SARL, and Pure SFM. The paper reports an
ablation of social-cost terms and a 20 Hz workstation execution rate.

## Consequence for the gap

Human-aware NMPC, local-path deviation, broad controller benchmarking, and
qualitative trajectory analysis are already represented in close prior art. The
present study therefore needs explicit MPC/DWA/MPPI comparators, paired seeds,
failure accounting, and a narrower claim about context-to-fixed-budget mapping.
The SFM predictor is not a direct allocator comparator and does not establish
that the proposed CCA interface is superior.

## Links

- [[03_Literature/source-index]]
- [[03_Literature/nearest-work-matrix]]
- [[03_Literature/web-verified-gap-sources]]
- [[04_Research_Gap/research-gap]]

Related hub: [[00_MOC/project-map]]
