# PR02 — Terminal-NMPC motion-control theory

**Status:** `RELEASED — THEORY ONLY`  
**Version:** 3.1  
**Date:** 2026-08-23

## Scope

PR02 covers only the nominal six-state Mecanum model, finite-horizon NMPC, and
the conditional terminal-Lyapunov argument recorded in:

- `research/obsidian/03_Theory/mathematical-model.md`;
- `research/obsidian/03_Theory/nmpc-motion-control.md`;
- `research/obsidian/03_Theory/lyapunov-stability.md`.

It does not verify code, simulation, learning, collision safety, robustness,
arbitrary reference switching, real-time execution, or hardware behavior.

## Locked model

$$
X_k=[x_k,y_k,\theta_k,v_{x,k},v_{y,k},\omega_k]^T,\qquad
u_k=[v^{cmd}_{x,k},v^{cmd}_{y,k},\omega^{cmd}_k]^T,
$$

$$
\nu_{k+1}=(1-\alpha)\nu_k+\alpha u_k,\qquad
q_{k+1}=q_k+\Delta t\,T(\theta_k)\nu_{k+1},\qquad
0<\alpha\leq1.
$$

The nominal wheel interfaces are
$\omega_w^{cmd}=K_mu$ and $\omega_w=K_m\nu$.

## Locked conditional theorem

For one dynamically feasible admitted reference and its one-step shifts, assume
the nominal model is exact, constraints are shift compatible, the initial NMPC
problem is feasible, and each selected feasible sequence is no more costly than
the exact shifted feasible sequence. Let $K_f$ make
$A_c=A_f+B_fK_f$ Schur, let $P\succ0$ satisfy

$$
A_c^TPA_c-P=-2(Q+K_f^TRK_f),
$$

and choose the terminal ellipsoid inside the analytic nonlinear and constraint
bounds. Then the shifted sequence remains feasible and

$$
\widehat V_{k+1}-\widehat V_k
\leq-e_{0|k}^TQe_{0|k}
-\widetilde u_{0|k}^TR\widetilde u_{0|k}.
$$

This establishes nominal recursive feasibility and tracking-error convergence
under the stated assumptions. If the feasible initialization also satisfies
$\widehat V_0\leq c_u\|e_{0|0}\|^2$, the cost lower bound establishes local
asymptotic stability of the plant tracking error within the feasible
neighborhood. No convergence claim is made for the complete stored sequence,
and no decrease is claimed across an unrelated CCA reference switch.

## Review decision

The analytic construction, nonlinear remainder bound, terminal containment,
shift argument, and claim limits are internally consistent at theory level.
They are standard supporting terminal-NMPC theory and are not claimed as a new
control theorem.

All numerical falsification, MATLAB/Simulink closed-loop work, parity tests,
solver behavior, timing, SIL/HIL, and physical experiments are future gates in
`IMPLEMENTATION_PLAN.md`. Earlier execution receipts are historical development
artifacts and are not evidence for this theory-only decision.

## Current goal gate

The locked English model and theorem were synchronized without widening the
claim to Overleaf project `6a6dd22be3ab13b78d949879`, history entry
`23rd August, 2:31 pm`, on 2026-08-23. The manuscript now includes a separate
Related Work section and a curated 34-item DOI bibliography. The six-page
Overleaf build completed with zero errors, warnings, and informational layout
messages. The synchronization receipt is
`research/metadata/overleaf_theory_sync_20260823.json`.
