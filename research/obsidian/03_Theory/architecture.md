---
domain: theory
type: note
status: locked
scope: theory-only
claim_status: candidate
evidence: literature-bounded-theory-contract
tags: [architecture, authority]
---

# Continuous Context-Aware architecture

CCA means **Continuous Context-Aware**. The control flow is

$$
\{\mathcal G,X_k,\{Z_n\}_{t_n\leq t_k},\mathcal O_k\}
\rightarrow \mathrm{CCA}[\mathrm{LSTM},\mathrm{GA}]
\rightarrow \mathcal P^{loc}_k \rightarrow \mathrm{NMPC}
\rightarrow u_k \rightarrow \mathrm{robot}.
$$

Here, $\mathcal G$ is the immutable global path, $X_k$ is the six-state robot
state, $Z_n$ is the causal observation bundle, $\mathcal O_k$ is the obstacle
set, $\mathcal P^{loc}_k$ is the
geometric robot local path, and $u_k$ is a body-velocity command. LSTM and GA
are internal CCA components. Let $n$ index human observations, $k$ index local
planning events, and $C_k^\star$ denote the latest admissible context available
at event $k$. Their roles are separated by

$$
(\xi_n,C_n)=F_\theta(Z_n,\xi_{n-1}),\qquad
(\mathcal P_k^{loc},\eta_k)=G_\phi
(\mathcal G,X_k,C_k^\star,\mathcal O_k,\eta_{k-1}).
$$

The recurrent state $\xi_n$, current context $C_n$, and GA memory $\eta_k$
remain internal to CCA; $\eta_k$ may contain the previous selected chromosome
and local path. The layer's only public output is a local path or the empty set
when no feasible proposal exists. “Continuous” means that CCA updates its
context state from every valid observation, independently of the lower-rate
planning events. It does not mean continuous-time dynamics or processing of
observations that were never received.

## Authority contract

| Layer | May produce | Must not produce |
|---|---|---|
| Perception | human position and observed features | control command |
| CCA/LSTM | current speed, direction probabilities, confidence proxy | rendered human path or control command |
| CCA/GA | geometric robot local path or no proposal | global replan or control command |
| NMPC | path time-parameterization and first body-velocity command | global-path mutation |

YOLO pose estimation is an interchangeable perception tool, not the proposed
method. The mathematical interface begins with causal human observations.

## Rate-separation contract

LSTM updates may occur between two consecutive planning events. At event $k$,
GA reads the latest admissible context $C_k^\star$, if one exists. Trigger
policy, concurrent execution, deadlines, and target-compute timing are future
implementation questions recorded in `IMPLEMENTATION_PLAN.md`; they are not
assumptions of the mathematical model. NMPC remains the sole command authority.

## Research significance

The boundary is motivated by closest integrated work
[Stefanini et al., 2024](https://doi.org/10.1109/LRA.2024.3461552),
[SICNav-Diffusion, 2025](https://doi.org/10.1109/LRA.2025.3585713), and
[GO-MPC, 2021](https://doi.org/10.1109/LRA.2021.3068662). Reference governors
are prior art
[Garone et al., 2017](https://doi.org/10.1016/j.automatica.2016.08.013). The
candidate contribution is the continuous context-to-Mecanum-local-path mechanism
and its downstream effect to be evaluated, not the individual blocks.

## Links

[[01_Problem/research-gap]] · [[03_Theory/mathematical-model]] ·
[[03_Theory/cca-trajectory-generation]] · [[03_Theory/nmpc-motion-control]] ·
[[04_Evaluation/claim-evidence-boundary]]
