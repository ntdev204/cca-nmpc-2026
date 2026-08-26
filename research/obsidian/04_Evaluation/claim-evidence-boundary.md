---
domain: evaluation
type: note
status: locked
scope: theory-only
evidence: claim-register
tags: [claims, limitations, evidence]
---

# Claim and evidence boundary

| Claim | Current status | Required future evidence | Explicit limit |
|---|---|---|---|
| A focused contribution question is defensible | literature boundary locked; benefit claim candidate | updated DOI audit before submission | no universal priority or “first” claim |
| CCA updates context independently of planning events | theory locked | implementation parity later | no accuracy, asynchronous-runtime, or real-time claim |
| CCA outputs only a geometric robot local path | theory locked | interface verification later | no command authority or global replan |
| Observation-rate context improves local generation | pending evidence | matched P−GLT comparison | no benefit wording yet |
| Six-state Mecanum NMPC formulation is coherent | theory locked | numerical parity and simulation later | nominal model only |
| NMPC is recursively feasible and tracking error converges | conditional analytic theorem locked | assumption falsification and simulation later | one admitted reference and its shifts; no full-pipeline stability |
| Path time-parameterization is feasible | pending evidence per path | dynamic residual and constraint checks | not guaranteed for arbitrary geometric paths |
| System outperforms DWA, MPPI, or MPC | pending evidence | paired end-to-end study | no cross-paper numerical comparison |
| Real-time capability | pending evidence | target-device tail latency and deadline misses | mean runtime is insufficient |
| Hardware effectiveness | pending evidence | registered physical experiments | simulation is not hardware evidence |
| Collision safety or human comfort | outside current theorem | calibrated formal and empirical evidence | Lyapunov tracking is neither safety nor comfort proof |

Use “a focused, non-exhaustive DOI audit leaves a candidate mechanism question”
rather than “no prior work exists”. Use “conditional nominal recursive
feasibility and tracking-error convergence of NMPC” rather than “the system is
stable”. Use “CCA local path” for the CCA output and “tracking reference” only
for the time-indexed representation produced inside motion control.

## Manuscript firewall

The locked English theory and mathematical model may be transferred to the
Overleaf manuscript. Candidate benefits, numerical results, simulations,
real-time claims, and hardware claims remain excluded until their planned
evidence exists. The manuscript is not written or built locally.

## Links

[[01_Problem/research-scope]] · [[01_Problem/research-gap]] ·
[[02_Literature/closest-work]] · [[03_Theory/lyapunov-stability]] ·
[[04_Evaluation/simulation-design]]
