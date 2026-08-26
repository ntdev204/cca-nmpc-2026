---
domain: theory
type: note
status: locked
scope: theory-only
evidence: theory-only-nmpc-formulation
tags: [nmpc, motion-control, tracking]
---

# NMPC motion control

CCA supplies a geometric local path. NMPC is the only layer that converts that
path into a time-indexed reference and produces body-velocity commands.

## Geometric path to feasible reference

Parameterize a CCA-proposed local path by arc length
$\gamma:[0,L]\rightarrow\mathbb R^2$, where $\gamma$ is piecewise $C^1$. A
nonnegative progress profile $v_s$ defines

$$
\lambda_0=0,\qquad
\lambda_{j+1}=\min\{\lambda_j+\Delta t\,v_s(\lambda_j),L\},\qquad
q_j^r=\begin{bmatrix}\gamma(\lambda_j)^T&\psi^r(\lambda_j)\end{bmatrix}^{T},
$$

where $v_s(L)=0$ and $\psi^r$ is a chosen fixed-yaw policy or a tangent-yaw
policy used only where $\gamma'$ exists and is nonzero; thus
$\theta_j^r=\psi^r(\lambda_j)$. Choose $\nu_0^r$ as a reference-design value.
It is retained only if the resulting reference and NMPC problem are feasible.
With

$$
\Delta q_j^r=
\begin{bmatrix}
x_{j+1}^r-x_j^r&y_{j+1}^r-y_j^r&
\operatorname{wrap}_{\pi}(\theta_{j+1}^r-\theta_j^r)
\end{bmatrix}^{T},
$$

the nominal model yields

$$
\nu_{j+1}^r=T(\theta_j^r)^T\frac{\Delta q_j^r}{\Delta t},\qquad
u_j^r=\nu_j^r+\frac{\nu_{j+1}^r-\nu_j^r}{\alpha}.
$$

The horizon includes a duplicate terminal pose
$q_{N-1}^r=q_N^r=q_f^r$, which gives $\nu_N^r=0$. The braking command
$u_{N-1}^r$ follows from the inversion above and must satisfy all constraints.
The shifted reference is extended by the rest pair
$(X_f^r,u_f^r)=(X_N^r,0)$. Equivalently, $u_N^r=0$ denotes only this terminal
extension and is not an element of $u^r_{0:N-1|k}$. The resulting reference
$\mathcal R_k=(X^r_{0:N|k},u^r_{0:N-1|k})$ is admissible only if it satisfies the
plant recursion and all state, command, wheel-rate-command, and terminal
constraints exactly. Existence of such a parameterization is not claimed for an
arbitrary geometric path, horizon, or progress profile. Numerical tolerances
and the concrete construction algorithm belong to
[IMPLEMENTATION_PLAN.md](../../../IMPLEMENTATION_PLAN.md).

## Tracking error

For the state definition in [[03_Theory/mathematical-model]], use

$$
e_{j|k}=\begin{bmatrix}
x_{j|k}-x^r_{j|k}\\
y_{j|k}-y^r_{j|k}\\
\operatorname{wrap}_{\pi}(\theta_{j|k}-\theta^r_{j|k})\\
\nu_{j|k}-\nu^r_{j|k}
\end{bmatrix},\qquad
\widetilde u_{j|k}=u_{j|k}-u^r_{j|k}.
$$

The initial reference need not equal the measured state; a nonzero initial
tracking error is permitted whenever the finite-horizon problem is feasible.

## Finite-horizon NMPC

For $Q\in\mathbb S_{++}^{6}$, $R\in\mathbb S_{++}^{3}$,
$P\in\mathbb S_{++}^{6}$, and horizon $N$, define

$$
J_N=\sum_{j=0}^{N-1}
\left(e_{j|k}^TQe_{j|k}+\widetilde u_{j|k}^TR\widetilde u_{j|k}\right)
+e_{N|k}^TPe_{N|k}.
$$

The nominal finite-horizon optimization problem is

$$
\begin{aligned}
\min_{u_{0:N-1|k}}\quad &J_N\\
\text{s.t.}\quad
&X_{0|k}=X_k,\quad
X_{j+1|k}=f(X_{j|k},u_{j|k}),\quad j=0,\ldots,N-1,\\
&X_{j|k}\in\mathcal X,\quad j=0,\ldots,N,\\
&u_{j|k}\in\mathcal U,\quad
|K_mu_{j|k}|\leq\bar\omega_w^{cmd},\quad j=0,\ldots,N-1,\\
&e_{N|k}\in\mathcal X_f,\qquad
\mathcal X_f=\{e:e^TPe\leq\rho\}.
\end{aligned}
$$

Vector absolute values and inequalities are interpreted componentwise.
The state set $\mathcal X$ may also bound actual wheel rates through
$|K_m\nu|$. The terminal law is $\widetilde u=K_fe$; $K_f$, $P$, and $\rho$
are constructed in [[03_Theory/lyapunov-stability]], rather than chosen by
inspection.

## Feasible-plan selection

Let $\mathcal F(X_k,\mathcal R_k)$ be the feasible command-sequence set and
assume an initial feasible selected sequence $U_0$ exists. For every $k\geq1$,
let $\bar U_k$ be the exact shift of the preceding selected sequence. The theory
requires $U_k$ to satisfy

$$
U_k\in\mathcal F(X_k,\mathcal R_k),\qquad
J_N(X_k,U_k,\mathcal R_k)\leq
J_N(X_k,\bar U_k,\mathcal R_k).
$$

Only the first command is applied. The condition does not require global
optimality and does not prescribe a numerical solver. It is the selection rule
needed by the shifted-sequence Lyapunov proof.

## Reference changes

The proof applies while $\mathcal R_{k+1}$ is the one-step shift of the admitted
reference, extended by its certified rest state and zero command. A different
CCA path may be admitted only after it receives a dynamically feasible
time-parameterization and the corresponding NMPC problem is feasible from the
current state. The cost before and after such a switch is not compared.
Thereafter, the fixed-reference shifted-sequence argument may restart for the
new certified reference. No common-Lyapunov or arbitrary-switching claim is
made.

Reference and feasibility governance are prior art
([Garone et al.](https://doi.org/10.1016/j.automatica.2016.08.013),
[Convens et al.](https://doi.org/10.1109/TCST.2024.3365996)). Terminal NMPC is
supporting motion-control theory, not the proposed novelty.

## Claim limits

The formulation does not by itself establish recursive feasibility from every
state, robustness, collision safety, solver timing, or performance under
reference switching. Adding command-rate constraints would require augmenting
the optimization state and proof with the previous command.

## Links

[[03_Theory/mathematical-model]] · [[03_Theory/cca-trajectory-generation]] ·
[[03_Theory/lyapunov-stability]] · [[04_Evaluation/baseline-contract]] ·
[[04_Evaluation/claim-evidence-boundary]]
