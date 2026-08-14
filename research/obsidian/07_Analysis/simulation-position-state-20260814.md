---
type: simulation-analysis
status: candidate-development-only
evidence_status: software-run-not-confirmatory
run_id: matlab-position-learning-20260814
manifest_sha256: 9CDA092E3E7CB63A3953A4E36CDD30954AD90192DA247193889E038099F99E1A
summary_sha256: C008D53E013BCDD3C82477D2A3B441EFE6A23A1E51F07990C18CBA48D2DF34D3
paper_edit: prohibited
---

# Position-state benchmark — 2026-08-14

## Scope

This is a fresh MATLAB run created after the clean reset. It uses the
position-state/body-velocity interface
`[x,y,theta,vx,vy,omega]` with commands
`[vx_cmd,vy_cmd,wz_cmd]`, four simple set-point scenarios (`x`, `y`,
`diagonal`, `yaw`) and the five pre-registered controller labels: MPC, NMPC,
DWA, MPPI and CCA-NMPC. The profile is `bounded` (`0.25 s` study duration,
`0.50 s` trajectory duration); no previous result package was read.

Raw package: `experiments/runs/matlab-position-learning-20260814/`.
The MATLAB manifest declares `paperEdit=false`, `hardwareValidated=false`,
`realTimeReady=false` and `evidenceStatus=candidate-development-only`.

## Observed summary

| Scenario | Controller | Final position error (m) | Position RMSE (m) | Yaw RMSE (rad) | Mean command variation |
|---|---:|---:|---:|---:|---:|
| x | MPC / NMPC / DWA / CCA-NMPC | 0.8938 | 0.9585 | 0 | 0.1300 |
| x | MPPI | 0.8981 | 0.9596 | 0.0043 | 0.1352 |
| y | MPC / NMPC / DWA / CCA-NMPC | 0.8938 | 0.9585 | 0 | 0.1300 |
| y | MPPI | 0.8971 | 0.9594 | 0.0042 | 0.1397 |
| diagonal | MPC | 1.2934 | 1.3638 | 0 | 0.1300 |
| diagonal | NMPC | 1.2647 | 1.3556 | 0 | 0.1820 |
| diagonal | DWA | 1.2640 | 1.3555 | 0 | 0.1838 |
| diagonal | MPPI | 1.2903 | 1.3632 | 0.0058 | 0.1680 |
| diagonal | CCA-NMPC | 1.2855 | 1.3615 | 0 | 0.1430 |
| yaw | MPC / NMPC / DWA / CCA-NMPC | 0 | 0 | 1.4940 | 0.2800 |
| yaw | MPPI | 0.0011 | 0.0006 | 1.4951 | 0.2740 |

Values are copied from the sealed `position_state_summary.csv`; they are not
interpreted as paper results.

## Interpretation and limits

The run is a software execution check, not a Q1 result. The short bounded
horizon leaves large set-point residuals, and several controller outputs are
identical. Therefore it does not establish controller superiority, safety,
real-time performance, stability or hardware validity. The identical rows are
an actionable diagnostic: before a confirmatory campaign, verify that the
controller-specific policies, target scaling and horizon are actually engaged
and add the locked collision/clearance/progress/fallback metrics required by
PR21. No trajectory of a human is generated or exported.

## Linked evidence

- [[07_Analysis/current-evidence-index]]
- [[07_Analysis/experimental-analysis]]
- [[06_Methods/evaluation-protocol]]
- [[01_Governance/status-and-provenance]]
- [[08_Decisions/position-state-control-scope-20260813]]
