# Protocol registry for CCA-NMPC research

These protocols define work that must be completed before a claim is admitted.
They are not experimental results. Old datasets, models, simulations, and robot
runs are outside the active evidence set.

## Status lifecycle

```text
DRAFT-DESIGN -> REVIEWED -> FROZEN -> EXECUTED -> VERIFIED -> RELEASED
```

`STRUCTURAL-PASS` means equations and software checks agree. It does not mean
that a theorem, experiment, real-time claim, or hardware claim is verified.
`VERIFIED — THEORY ONLY` means an analytic formulation and its stated proof
limits are locked; it says nothing about software or empirical performance.

## Current status — 2026-08-23

| ID | Scope | Status | Next gate |
|---|---|---|---|
| PR00 | Research scope and claims | `FROZEN — THEORY ONLY` | none in current theory goal |
| PR01 | Systematic literature review | `ARCHIVED` | not an active gate for this original research article |
| PR02 | Motion-control theory and proof | `RELEASED — THEORY ONLY` | current theory goal complete |
| PR10 | Real person-image acquisition | `DEFERRED` | outside current goal |
| PR11 | Causal LSTM dataset | `DEFERRED` | outside current goal |
| PR12 | Self-supervised LSTM evaluation | `DEFERRED` | outside current goal |
| PR20 | MATLAB/Simulink simulation | `DEFERRED` | outside current goal |
| PR21 | Matched controller benchmark | `DEFERRED` | outside current goal |
| PR22 | Legacy pilot simulation | `ARCHIVED` | none |
| PR23 | Legacy stabilization pilot | `ARCHIVED` | none |
| PR24 | Legacy feasibility pilot | `ARCHIVED` | none |
| PR30 | Physical experiment | `DEFERRED` | outside current goal |
| PR40 | Statistical analysis | `DEFERRED` | outside current goal |
| PR50 | Evidence release | `DEFERRED` | outside current goal |

## Active architecture

```text
fixed global path
  -> LSTM context inside CCA
  -> GA local robot-reference generation
  -> prior-art-inspired reference admission
  -> terminal NMPC motion control
  -> Mecanum robot
```

- State: `[x,y,theta,vx,vy,omega]`.
- Input: `[vx_cmd,vy_cmd,omega_cmd]`.
- GA is the only active search mechanism beyond the LSTM.
- Lyapunov analysis belongs only to terminal NMPC motion control.
- `src/` and `simulations/` are frozen during the current theory goal.
- Only accepted theory is transferred to Overleaf; no local paper is maintained.

## Evidence boundary

- Historical parity and smoke runs are not evidence for the current theory lock.
- Development tuning is not confirmatory evidence.
- Failed, infeasible, and timed-out episodes remain in the denominator.
- Simulation does not establish hardware performance or real-time execution.
- A focused DOI audit replaces PR01; it is not a systematic review.
