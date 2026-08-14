---
type: source-note
status: screening-candidate
evidence_status: publisher-full-text
evidence_level: full-text
citekey: gnimady2026integratednmpc
doi: 10.1007/s11370-025-00661-7
zotero_uri:
verified_date: 2026-08-13
---

# Gnimady et al. (2026) — Integrated estimation and predictive control

## Bibliographic verification

- The [Springer Nature full text](https://doi.org/10.1007/s11370-025-00661-7)
  identifies *Development of an integrated estimation and predictive control
  framework for safe navigation in mobile robots for industrial environments*,
  volume 19, article 33, published 9 February 2026.
- The article reports LiDAR/RADAR/IMU estimation, MPC-based obstacle avoidance,
  Gazebo evaluation and real-robot experiments. Zotero admission and
  correction/retraction checks remain open.

## Relevance and boundary

This is direct prior art for integrated sensing, state estimation, predictive
control and physical validation. Its reported platform and control interface
are not the present position-state Mecanum implementation with body-velocity
commands, and it does not
establish the CCA fixed-budget mechanism or the contract that keeps any
CCA-NMPC future-position sequence internal and off images/raw artifacts.

## Consequence for the gap and experiments

Sensor fusion plus MPC and real-robot testing must be treated as established
system components. The present study must isolate the CCA allocation effect,
report actuator/model mismatch, and disclose target-hardware timing rather than
borrowing the prior paper's runtime values.

## Links

- [[03_Literature/source-index]]
- [[03_Literature/web-verified-gap-sources]]
- [[03_Literature/nearest-work-matrix]]
- [[04_Research_Gap/research-gap]]

Related hub: [[00_MOC/project-map]]
