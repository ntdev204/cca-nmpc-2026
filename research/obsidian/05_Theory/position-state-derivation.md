---
type: position-state-derivation
status: proof-draft
evidence_status: model-contract-only
paper_edit: prohibited
---

# Derivation for the position-state update

This note closes a small theory gap left by the active six-state contract. It
uses the same simple update implemented in Python and MATLAB:

$$
s_k=[p_k^\top,\theta_k,v_k^\top]^\top,
\quad v_k=[v_{x,k},v_{y,k},\omega_k]^\top,
\quad u_k=[v_{x,k}^{\rm cmd},v_{y,k}^{\rm cmd},\omega_k^{\rm cmd}]^\top,
$$

$$
v_{k+1}=v_k+\alpha(u_k-v_k),
\qquad
\alpha=\operatorname{clip}(\Delta t/\tau_v,0,1).
$$

With $R(\theta)$ denoting the planar body-to-world rotation,

$$
p_{k+1}=p_k+\Delta t\,R(\theta_k)v_{k+1}^{(1:2)},
\qquad
\theta_{k+1}=\operatorname{wrap}(\theta_k+\Delta t\,\omega_{k+1}).
$$

The command is a body-velocity command. It is not a wheel-torque input.

## Proposition P-PS1 — velocity bound

Assume $0\le\alpha\le1$, $\lVert v_0\rVert_\infty\le U$, and
$\lVert u_k\rVert_\infty\le U$ for every step. Then
$\lVert v_k\rVert_\infty\le U$ for every $k$.

### Proof

For each component $i$,

$$
v_{k+1,i}=(1-\alpha)v_{k,i}+\alpha u_{k,i}.
$$

The coefficients are nonnegative and sum to one. Thus $v_{k+1,i}$ lies in
the interval with endpoints $v_{k,i}$ and $u_{k,i}$. Both endpoints lie in
$[-U,U]$, so $v_{k+1,i}\in[-U,U]$. Induction from $v_0$ proves the result.

This is a one-step invariant of the declared discrete model. It is not a
closed-loop stability or recursive-feasibility proof for the real robot.

## CCA projected-uncertainty margin

For a CCA prediction at stage $\ell$, let $d_\ell$ be the nominal
robot--person separation, $n_\ell$ its unit normal, and $\Sigma_\ell$ the
relative position covariance. The position-state implementation uses the
scalar projection

$$
\sigma_\ell=\sqrt{\max\left(0,n_\ell^{\mathsf T}\Sigma_\ell n_\ell\right)},
\qquad
r_\ell=r_0+0.12\sqrt{c_\ell}
  +\Phi^{-1}\!\left(1-\varepsilon_\ell\right)\sigma_\ell,
$$

where $r_0$ is the measured robot--context clearance, $c_\ell$ is the
bounded context score, and $\varepsilon_\ell$ is the fixed-budget allocation
for that stage. The controller treats $r_\ell-d_\ell$ as the one-step margin
used to push the body-velocity command away from the predicted person.

Under a Gaussian projected error, zero slack, and a frozen active set, the
one-dimensional condition $d_\ell\ge r_\ell$ is the same model-internal
half-space surrogate used in T4. It does not establish calibration under
$\Pr_\star$, closed-loop safety, or recursive feasibility. Missing covariance
provenance or an invalid snapshot must therefore fail closed before this
margin is used. The active risk-row implementation is in
`src/control/src/controller.cpp` and is called through the ABI adapter
`src/runtime/controller.py`; `scripts/python/tools/map_run.py` prepares the
position-state prediction arrays. The scalar projection is regression-tested
for monotonic growth with projected covariance.

## Direct candidate-rollout implementation boundary

The active compiled controller receives the six-state vector, a horizon
reference and the context arrays through the C ABI. It starts from a nominal
body-velocity command, applies the CCA projected-risk adjustment, clips the
command to the declared bounds, and rolls that command through the horizon
with the discrete update above. DWA and MPPI use their bounded command samples;
the CCA branch uses the context/covariance/nominal-robot arrays supplied by the
Python adapter. The current candidate implementation does not expose a
multiple-shooting nonlinear-program solver or a positive optimized slack
variable.

This is a finite-horizon bounded receding-horizon implementation contract, not
a proof of recursive feasibility or stability and not evidence of a general
nonlinear-program solver. MATLAB's active position study remains a separate
contract/comparator path; direct Python--MATLAB solver equivalence is not
claimed.

## Proposition P-PS2 — bounded pose increment

Under the assumptions of P-PS1, let
$U_{xy}=\max(|v_x|,|v_y|)$ over the declared command bound. Then

$$
\lVert p_{k+1}-p_k\rVert_2
\le \Delta t\sqrt{2}\,U_{xy},
\qquad
|\theta_{k+1}-\theta_k|_{\rm wrapped}
\le \Delta t\,U_\omega.
$$

### Proof

$R(\theta)$ is orthogonal, so it preserves the Euclidean norm. Therefore

$$
\lVert p_{k+1}-p_k\rVert_2
=\Delta t\lVert v_{k+1}^{(1:2)}\rVert_2
\le\Delta t\sqrt{v_{x,k+1}^2+v_{y,k+1}^2}
\le\Delta t\sqrt{2}\,U_{xy}.
$$

The yaw update is direct, and wrapping can only choose the equivalent angular
representative; the physical increment before wrap is bounded by
$\Delta t U_\omega$.

## Implementation boundary

`src/simulation/model.py::position_state_step` and
`matlab/+cca/Model.m::positionStep` implement this contract. The bound is
valid only for the declared velocity command limits and measured sample time.
Actuator saturation, communication delay, unmodelled slip and disturbance are
not covered until identification and a Markov augmentation are available.
Consequently this note cannot support recursive feasibility, ISS, hard
real-time, physical safety or a claim under $\Pr_\star$.

Related: [[05_Theory/system-model]] · [[05_Theory/assumptions]] ·
[[05_Theory/proof-obligations]] · [[07_Analysis/theory-parity-audit-20260813]]

## Frozen-row candidate contract — 2026-08-14

For each usable CCA stage, the implementation validates the nominal human mean
$m_\ell$, covariance, context score and nominal robot location before computing
the unit normal $n_\ell$ and context-dependent margin $r_\ell$. The nominal
robot locations are read from `NmpcPrediction.nominal_robot_xy`; they are not
silently replaced by a reference waypoint. A malformed or short nominal
sequence raises a validation error before actuation.

The compiled controller records the maximum row violation, adjusts the
candidate body velocity along the frozen normal, clips the command, and reports
the bounded rollout. The current output field for risk slack is reserved and is
zero because no optimized slack variable is exposed by this implementation.
These are execution contracts only; they do not establish recursive
feasibility, stability, or physical safety.
