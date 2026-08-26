---
domain: theory
type: note
status: locked
scope: theory-only
evidence: theory-only-nominal-model
tags: [mecanum, state-space, position-control]
---

# Mecanum position-state model

## State and input

$$
q_k=\begin{bmatrix}x_k&y_k&\theta_k\end{bmatrix}^{\!T},\qquad
\nu_k=\begin{bmatrix}v_{x,k}&v_{y,k}&\omega_k\end{bmatrix}^{\!T},
$$

$$
X_k=\begin{bmatrix}q_k^T&\nu_k^T\end{bmatrix}^{\!T},\qquad
u_k=\begin{bmatrix}v_{x,k}^{cmd}&v_{y,k}^{cmd}&\omega_k^{cmd}\end{bmatrix}^{\!T}.
$$

The input is a commanded body velocity, not wheel torque.

## Discrete plant

The velocity response uses a first-order actuator approximation. Assume
$\Delta t>0$ and $\tau_v>0$, so $0<\alpha\leq1$:

$$
\nu_{k+1}=\nu_k+\alpha(u_k-\nu_k),\qquad
\alpha=\min\left(1,\frac{\Delta t}{\tau_v}\right).
$$

This is a nominal forward-Euler update with a clipped integration coefficient.
It is not
the exact discretization of an identified actuator and does not model wheel
slip, delay, or cross-axis coupling.

The pose is updated semi-implicitly and the angular coordinate is returned to
the principal chart:

$$
\bar q_{k+1}=q_k+\Delta t\,T(\theta_k)\nu_{k+1},\qquad
q_{k+1}=\begin{bmatrix}
\bar x_{k+1}&\bar y_{k+1}&
\operatorname{wrap}_{\pi}(\bar\theta_{k+1})
\end{bmatrix}^{\!T},
$$

$$
T(\theta)=
\begin{bmatrix}
\cos\theta&-\sin\theta&0\\
\sin\theta& \cos\theta&0\\
0&0&1
\end{bmatrix}.
$$

Thus $X_{k+1}=f(X_k,u_k)$. This update order and angle convention define the
nominal plant used by the motion-control theory. Cross-language parity belongs
to the future implementation plan. The stored angle may be wrapped for a unique
representation, but NMPC and the Lyapunov argument use a local unwrapped angular
error chart strictly inside $(-\pi,\pi)$; branch crossings are outside the
locked theorem domain.

## Mecanum actuator interface

Use body axes $x$ forward, $y$ left, and positive yaw counterclockwise. For
wheel radius $r_w$ and half-dimensions $a,b$, the nominal commanded and actual
wheel rates are

$$
\omega_w^{cmd}=K_m u,\qquad \omega_w=K_m\nu,
$$

$$
K_m=\frac{1}{r_w}
\begin{bmatrix}
1&-1&-(a+b)\\
1& 1& (a+b)\\
1& 1&-(a+b)\\
1&-1& (a+b)
\end{bmatrix}.
$$

The rows are front-left, front-right, rear-left, and rear-right; under this
nominal sign convention, equal positive wheel rates produce positive body-$x$
motion. Their association with physical motors is deferred to hardware
calibration. NMPC imposes the wheel-rate command constraint
$|K_m u|\leq\bar\omega_w^{cmd}$. Moreover,

$$
K_m\nu_{k+1}=(1-\alpha)K_m\nu_k+\alpha K_m u_k,
$$

so the same componentwise wheel-rate box is invariant when it contains the
initial actual wheel rates and every commanded wheel-rate vector.

Mecanum MPC is prior art
[Moreno et al., 2021](https://doi.org/10.1016/j.ifacol.2021.08.533),
[Wang et al., 2024](https://doi.org/10.1016/j.isatra.2024.05.050). This compact
model is chosen for transparent position control, not claimed as new dynamics.

## Links

[[03_Theory/architecture]] · [[03_Theory/nmpc-motion-control]] ·
[[03_Theory/lyapunov-stability]] · [[04_Evaluation/simulation-design]] ·
[[04_Evaluation/claim-evidence-boundary]]
