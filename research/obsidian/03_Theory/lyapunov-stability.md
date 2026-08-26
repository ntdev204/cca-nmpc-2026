---
domain: theory
type: note
status: locked
scope: theory-only
evidence: conditional-analytic-proof
tags: [lyapunov, terminal-nmpc, recursive-feasibility]
---

# Lyapunov certificate for NMPC motion control

The result below concerns only the nominal NMPC motion-control layer. It does
not prove perception validity, collision safety, GA convergence, robustness,
arbitrary reference-switch stability, real-time execution, or hardware
performance.

## Terminal-reference contract

Each admitted reference follows the nominal plant, satisfies its constraints,
and ends at a certified rest state:

$$
X^r_{j+1}=f(X^r_j,u^r_j),\qquad
X_N^r=[(q_f^r)^T,0,0,0]^T,\qquad u_f^r=0.
$$

A geometrically smooth local path is not sufficient; it must first satisfy the
time-parameterization contract in [[03_Theory/nmpc-motion-control]].

## Local terminal model

Let $T_f=T(\theta_f^r)$ and $0<\alpha\leq1$. Linearization of the nominal model
at the rest terminal state gives

$$
A_f=\begin{bmatrix}
I_3&\Delta t(1-\alpha)T_f\\0&(1-\alpha)I_3
\end{bmatrix},\qquad
B_f=\begin{bmatrix}\Delta t\alpha T_f\\\alpha I_3\end{bmatrix}.
$$

Assume $(A_f,B_f)$ is stabilizable. Choose $K_f$ such that
$A_c=A_f+B_fK_f$ is Schur. For $Q\succ0$, $R\succ0$, let
$S=Q+K_f^TRK_f\succ0$. The discrete Lyapunov equation

$$
A_c^TPA_c-P=-2S
$$

then has a unique solution $P\succ0$. The factor two reserves a strict margin
for the nonlinear rotation remainder. This is a standard terminal-NMPC
construction, not theoretical novelty
([Chen and Allgower](https://doi.org/10.1016/S0005-1098(98)00073-9),
[Mayne et al.](https://doi.org/10.1016/S0005-1098(99)00214-9)).

## Nonlinear terminal bound

Under the terminal law $\widetilde u=K_fe$, the exact error update in a local
angular chart is

$$
e^+=A_ce+r(e),\qquad
\|r(e)\|\leq L_r\|e\|^2,qquad
L_r=\Delta t\|F_{xy}\|_2,
$$

where
$F=[0_{3\times3},(1-\alpha)I_3]+\alpha K_f$ and $F_{xy}$ contains its first two
rows. The inequality follows from
$\|T(\theta_f^r+e_\theta)-T_f\|_2\leq|e_\theta|$. It is used only in a chart
$|e_\theta|\leq\bar\theta<\pi$.

Let

$$
c_1=2\|A_c^TP\|_2L_r,\qquad c_2=\|P\|_2L_r^2.
$$

Choose $r_e>0$ such that
$c_1r_e+c_2r_e^2\leq\lambda_{\min}(S)$, and select

$$
\mathcal X_f=\{e:e^TPe\leq\rho\},\qquad
0<\rho\leq\lambda_{\min}(P)r_e^2.
$$

For the theorem, assume the active terminal constraints admit affine
representations in the local error chart. Translate the state, command,
wheel-rate-command, and local-angle constraints by the terminal pair
$(X_N^r,u_f^r)$. Write every resulting inequality as
$a_i^Te\leq b_i$, where $b_i>0$. Thus the translated rows include
$X_N^r+e\in\mathcal X$, $u_f^r+K_fe\in\mathcal U$, and
$|K_m(u_f^r+K_fe)|\leq\bar\omega_w^{cmd}$. Reduce $\rho$ further until, for
every row $i$,

$$
\max_{e^TPe\leq\rho}a_i^Te
=\sqrt{\rho}\sqrt{a_i^TP^{-1}a_i}\leq b_i.
$$

The nonlinear bound and Lyapunov equation then give, for every
$e\in\mathcal X_f$,

$$
V_f(e^+)-V_f(e)
\leq-e^TQe-(K_fe)^TR(K_fe),\qquad V_f(e)=e^TPe.
$$

Consequently, the terminal set is positively invariant under the nominal
terminal law and remains inside the same angular chart.

## Conditional theorem

Consider one admitted reference and its one-step shifts. Assume:

1. the reference satisfies the terminal contract and all constraints;
2. constraints are time invariant or shift compatible;
3. the nominal model is exact and the computed command is applied unchanged;
4. the initial NMPC problem has a feasible command sequence;
5. for every $k\geq1$, the selected sequence is feasible and no more costly
   than the exact shifted feasible sequence;
6. $\mathcal X_f$, $K_f$, and $P$ satisfy the construction above; and
7. a local feasible initialization satisfies
   $\widehat V_0=J_N(X_0,U_0,\mathcal R_0)
   \leq c_u\|e_{0|0}\|^2$ for some $c_u>0$.

Shifting the selected sequence and appending $K_fe_{N|k}$ preserves nominal
feasibility. Let
$\widehat V_k=J_N(X_k,U_k,\mathcal R_k)$ be the cost of the selected feasible
plan. The terminal inequality yields

$$
\widehat V_{k+1}-\widehat V_k
\leq-\left(e_{0|k}^TQe_{0|k}
+\widetilde u_{0|k}^TR\widetilde u_{0|k}\right).
$$

Hence the nominal NMPC problem is recursively feasible. Summing the decrease
inequality and using $Q\succ0$ gives
$\sum_{k=0}^{\infty}\|e_{0|k}\|^2<\infty$, so
$e_{0|k}\rightarrow0$. Moreover,

$$
\lambda_{\min}(Q)\|e_{0|k}\|^2
\leq\widehat V_k\leq\widehat V_0
\leq c_u\|e_{0|0}\|^2.
$$

The initialization bound therefore establishes Lyapunov stability of the plant
tracking error. Together with convergence, this gives conditional local
asymptotic stability of the tracking error within the feasible neighborhood. No
convergence claim is made for the complete stored sequence.

## Reference-switch boundary

If CCA proposes a different local path, the result can restart only after the
new path has a dynamically feasible reference, a certified terminal
construction, and a feasible initialization satisfying the local cost bound at
the current state. Costs under different references are not compared, and no
decrease is claimed across the switch. Repeated unrestricted switching is
therefore outside the theorem.

The locked result is a conditional analytic theorem for nominal recursive
feasibility, tracking-error convergence, and local asymptotic tracking-error
stability under the stated initialization bound. All numerical falsification,
simulation, robustness, timing, and hardware work is deferred to
[IMPLEMENTATION_PLAN.md](../../../IMPLEMENTATION_PLAN.md).

## Links

[[03_Theory/mathematical-model]] · [[03_Theory/nmpc-motion-control]] ·
[[03_Theory/cca-trajectory-generation]] · [[04_Evaluation/simulation-design]] ·
[[04_Evaluation/claim-evidence-boundary]]
