---
domain: theory
type: note
status: locked
scope: theory-only
claim_status: candidate
evidence: literature-bounded-theory-contract
tags: [cca, lstm, genetic-algorithm]
---

# Continuous Context-Aware local-path generation

CCA contains the LSTM context estimator and the GA local-path generator. Let
$n$ index observations and $k$ index planning events. Its internal state obeys

$$
(\xi_n,C_n)=F_\theta(\zeta_n,\xi_{n-1}),\qquad
(\mathcal P_k^{loc},\eta_k)=G_\phi
(\mathcal G,X_k,C_k^\star,\mathcal O_k,\eta_{k-1}),
$$

where $\zeta_n$ is the causal feature vector extracted from observation $Z_n$,
$\xi_n$ is the recurrent
state, and $\eta_k$ is GA memory containing any previous chromosome and local
path used for initialization. With observation time $t_n$, planning time $t_k$,
validity flag $b_n$, and maximum context age $\tau_c>0$, define

$$
\mathcal I_k=\{n:t_n\leq t_k,\ b_n=1,\ t_k-t_n\leq\tau_c\},\qquad
C_k^\star=
\begin{cases}
C_{\max\mathcal I_k},&\mathcal I_k\neq\varnothing,\\
\varnothing,&\mathcal I_k=\varnothing.
\end{cases}
$$

If $b_n=0$, the recurrent state is held at $\xi_n=\xi_{n-1}$ and
$C_n=\varnothing$; otherwise $F_\theta$ is evaluated. Every valid observation
updates $\xi_n$ even when no planning event occurs. The only public
CCA output is a geometric robot local path; if no feasible proposal exists,
CCA returns $\varnothing$. It never modifies the global path or issues a motion
command. The locked model covers one selected moving person. Multi-person data
association and aggregation are future extensions.

## Causal current-context model

Let $\xi_n=(h_n,s_n)$, where $h_n$ and $s_n$ are the hidden and cell states.
The parameters $\theta$ of the recurrent model and $\phi$ of the local generator
are fixed within this theory contract.
A compact LSTM follows
[Hochreiter and Schmidhuber](https://doi.org/10.1162/neco.1997.9.8.1735):

$$
\begin{aligned}
[f_n,i_n,o_n,g_n]
&=[\sigma,\sigma,\sigma,\tanh]
  \bigl(W[\zeta_n,h_{n-1}]+b\bigr),\\
s_n&=f_n\odot s_{n-1}+i_n\odot g_n,\\
h_n&=o_n\odot\tanh(s_n),\\
\hat v_n^h&=W_vh_n+b_v,\qquad
\pi_n=\operatorname{softmax}(W_dh_n+b_d).
\end{aligned}
$$

All human positions and velocities are expressed in the map frame. Let
$R(\theta)$ be the planar rotation, let $\theta_n^R$ be the measured robot yaw at
$t_n$, and set $e_x=[1,0]^T$, $e_y=[0,1]^T$. Then
$D_n=R(\theta_n^R)[e_x,e_y,-e_x,-e_y]$ is the map-frame basis corresponding to
robot-relative forward, left, rear, and right. If
$r_n=\arg\max_i\pi_{n,i}$, then $d_n^h$ is column $r_n$ of $D_n$ and
$\gamma_n=\max_i\pi_{n,i}$ is a confidence proxy. Set
$d_n^h=\varnothing$ when $\gamma_n<\gamma_{min}$ or
$\|\hat v_n^h\|<v_{min}$. Thus
$C_n=(p_n^h,\hat v_n^h,d_n^h,\gamma_n,t_n)$ contains current position, velocity,
coarse direction, confidence, and time only. It contains no future human
coordinates and produces no human trajectory. Learning, thresholds, and
calibration are assigned to
[IMPLEMENTATION_PLAN.md](../../../IMPLEMENTATION_PLAN.md).

## Fixed-global-path geometry

Let the immutable global path be a locally regular, arc-length-parameterized
curve $g:[0,S]\rightarrow\mathbb R^2$. On each smooth local segment,
$t_g(s)=g'(s)$ and $n_g(s)=[-t_{g,y}(s),t_{g,x}(s)]^T$. In a chosen forward
progress interval $\mathcal S_k$, the start projection and fixed rejoin point are

$$
s_k^0=\arg\min_{s\in\mathcal S_k}\|g(s)-q_k^{xy}\|,\qquad
s_k^r=\min(s_k^0+L_a,S),
$$

with the smallest forward $s$ used as a deterministic tie-break. Choose fixed
stations $s_k^0<s_{k,2}<\cdots<s_{k,N_c-1}<s_k^r$. A chromosome contains only
interior lateral offsets,

$$
\chi=(\ell_2,\ldots,\ell_{N_c-1}),\quad |\ell_i|\leq\ell_{max},\qquad
c_1=q_k^{xy},\quad
c_i=g(s_{k,i})+\ell_i n_g(s_{k,i}),\quad
c_{N_c}=g(s_k^r).
$$

If $s_k^r=s_k^0$ at the goal, CCA returns no new proposal. Otherwise, the
decoder constructs a parametric piecewise-cubic Hermite curve
$P_\chi:[0,1]\rightarrow\mathbb R^2$ through these control points. It uses
chord-length-normalized knots, one-sided endpoint chords, and centered interior
chords; the exact numerical decoder belongs to the implementation plan. Hence
the robot may start off the global path, while every candidate rejoins the same
fixed global path at $g(s_k^r)$. Time parameterization is not part of CCA.

## Directional human region

Directional and context-dependent personal regions are established modeling
ideas [Neggers et al.](https://doi.org/10.1007/s12369-021-00805-6), including
asymmetric Gaussian constructions that depend on motion and gaze
([Wang et al.](https://doi.org/10.1109/ROBIO54168.2021.9739433)). Here they are
used only as a geometric context model, not as a calibrated human-comfort claim.
For admitted unit direction $d^h$, let
$n^h=[-d_y^h,d_x^h]^T$, $a=(p-p^h)^Td^h$, and $b=(p-p^h)^Tn^h$. Define

$$
\rho_C(p)=\frac{a^2}{r_\parallel(a)^2}+\frac{b^2}{r_\perp^2},\qquad
r_\parallel(a)=
\begin{cases}r_f,&a\geq0,\\r_r,&a<0,\end{cases}
\qquad
\mathcal H(C)=\{p:\rho_C(p)\leq1\},
$$

where $r_f=\bar r_f+\tau_h\|\hat v^h\|$, $\tau_h>0$ is a time parameter, and
$r_r,r_\perp,\bar r_f$ are positive lengths. For unknown direction,
$\mathcal H(C)$ is the disk of radius
$r_0=\max\{r_f,r_r,r_\perp\}$. Confidence controls admission of the direction;
it never shrinks the exclusion region. Set $\mathcal H(\varnothing)=\varnothing$
and $\operatorname{dist}(A,\varnothing)=+\infty$ for any nonempty set $A$.

## Geometric feasibility

Let $\mathcal O_k\subset\mathbb R^2$ be the closed occupied set and let
$r_R=\sqrt{(L_R/2)^2+(W_R/2)^2}$ be the robot's circumscribed radius. For a
curve satisfying $\inf_t\|P_\chi'(t)\|\geq\varepsilon_P>0$, define
$\kappa_\chi(t)=|\det(P_\chi'(t),P_\chi''(t))|/\|P_\chi'(t)\|^3$. The regular
candidate domain and feasible chromosome set are

$$
\begin{aligned}
\mathcal D_k&=\{\chi:\inf_t\|P_\chi'(t)\|\geq\varepsilon_P\},\\
\mathcal C_k=\{\chi\in\mathcal D_k:\;&|\ell_i|\leq\ell_{max},\quad
\sup_t\kappa_\chi(t)\leq\bar\kappa,\\
&\operatorname{dist}(\operatorname{Im}P_\chi,\mathcal O_k)
  \geq r_R+d_{safe},\\
&\operatorname{dist}(\operatorname{Im}P_\chi,\mathcal H(C_k^\star))
  \geq r_R+d_{safe},\\
&P_\chi(0)=q_k^{xy},\quad P_\chi(1)=g(s_k^r)\}.
\end{aligned}
$$

The human-region constraint is omitted when $\mathcal I_k$ is empty. Using the
circumscribed robot disk makes these centerline clearances conservative for the
rectangular footprint. They certify only the proposed geometric path, not the
executed robot trajectory under tracking error.

## GA objective and selection

Let $d_g(p)=\operatorname{dist}(p,\operatorname{Im}g)$. When
$C_k^\star\neq\varnothing$, let
$d_h(p)=\operatorname{dist}(p,\mathcal H(C_k^\star))$. With $\epsilon>0$, define

$$
\begin{aligned}
L&=\int_0^1\|P_\chi'(t)\|\,dt,\\
S_\kappa&=\int_0^1\kappa_\chi(t)^2\|P_\chi'(t)\|\,dt,\\
D_G&=\frac1L\int_0^1d_g(P_\chi(t))^2\|P_\chi'(t)\|\,dt,\\
R_H&=
\begin{cases}
\displaystyle\frac1L\int_0^1\frac{\|P_\chi'(t)\|}
{d_h(P_\chi(t))+\epsilon}\,dt,&C_k^\star\neq\varnothing,\\
0,&C_k^\star=\varnothing.
\end{cases}
\end{aligned}
$$

Fixed positive scales $L_0,S_0,D_0,R_0$ make the fitness dimensionless:

$$
J(\chi)=w_L\frac{L}{L_0}+w_\kappa\frac{S_\kappa}{S_0}
+w_G\frac{D_G}{D_0}+w_H\frac{R_H}{R_0},
\qquad w_i\geq0,\quad\sum_iw_i=1.
$$

The GA evaluates a finite set $\mathcal E_k$ of chromosomes after any selected
repair operation. An optional deterministic finite repair map may project a
candidate toward $\mathcal C_k$, but it has no
guaranteed success; its algorithm belongs to `IMPLEMENTATION_PLAN.md`. With a
lexicographic chromosome tie-break,

$$
\mathcal P_k^{loc}=
\begin{cases}
P_{\operatorname{lexargmin}_{\chi\in\mathcal E_k\cap\mathcal C_k}J(\chi)},
&\mathcal E_k\cap\mathcal C_k\neq\varnothing,\\
\varnothing,&\text{otherwise}.
\end{cases}
$$

This is the best evaluated feasible candidate, not a global optimum. GA is
placed in CCA because the local geometric search is nonconvex and because CCA
has no command authority. The NMPC numerical method and the feasibility
assumptions of its proof remain separate. Neither GA planning, GA inside
predictive control, nor GA--controller composition is claimed as new
([Gyenes et al.](https://doi.org/10.3390/s23063039),
[Song and Huh](https://doi.org/10.1177/16878140211027669)). The candidate claim
is restricted to the effect, still to be evaluated, of observation-rate context
updates within this fixed-weight LSTM--GA local generator.

The primary matched hypothesis compares observation-rate and planning-event-only
recurrent updates under identical fixed LSTM parameters, observation streams,
planning events, and GA settings; it assumes no performance advantage before
evaluation.

## Claim limits

The equations do not establish LSTM accuracy, GA convergence, social comfort,
NMPC feasibility, collision-free execution, real-time behavior, or hardware
performance. Closest local-path anchors include omnidirectional interaction
planning [Kobayashi et al.](https://doi.org/10.1007/s12369-021-00791-9) and the
Social Elastic Band
[Perez et al.](https://doi.org/10.1007/s12369-024-01135-z). Therefore the
architecture remains a literature-bounded candidate mechanism rather than a
theoretical novelty claim.

## Links

[[03_Theory/architecture]] · [[03_Theory/mathematical-model]] ·
[[03_Theory/nmpc-motion-control]] · [[04_Evaluation/baseline-contract]] ·
[[04_Evaluation/claim-evidence-boundary]]
