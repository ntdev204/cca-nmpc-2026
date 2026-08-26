# CCA--NMPC simulation, training, and experimental implementation plan

**Status:** `IN_PROGRESS`  
**Scope:** code-only implementation; manuscript and Overleaf remain locked  
**Execution:** reopened by the explicit implementation request on 2026-08-23

**Execution status (2026-08-23):** Stage A frozen contract, Stage C Python
CCA, Stage D Simulink integration, and Stage F software-in-the-loop code are
complete. Stage E campaign orchestration is implemented but confirmatory
statistics are not promoted because no independent dataset is present. Stage B
learning remains executable through the existing score-loop tools but has no
registered dataset. Stage G has hardware-compatible adapters only; the physical
hardware is inactive.

The implementation gate is `python scripts/research_harness.py
--implementation-only`; it passes all nine code-scope checks. The full
repository gate is intentionally separate from this simulation closure and is
not used to promote simulation or SIL artifacts as experimental evidence.

This is the single plan for all future code, simulation, learning, and physical
experiments. It does not constitute evidence that any stage has passed.

## 1. Locked theory boundary

```text
fixed global path + causal current context + robot state + obstacles
  -> CCA [fixed-weight LSTM + GA]
  -> geometric robot local path
  -> time parameterization + terminal NMPC
  -> body-velocity command
  -> Mecanum robot
```

- CCA updates recurrent context at each valid observation and plans only at
  planning events.
- The LSTM estimates current human velocity, coarse direction, and confidence;
  it does not generate future human coordinates.
- GA changes only interior lateral offsets and never modifies the global path.
- CCA returns a feasible geometric robot local path or no proposal.
- NMPC is the sole command authority with
  `X=[x,y,theta,vx,vy,omega]` and
  `u=[vx_cmd,vy_cmd,omega_cmd]`.
- Lyapunov analysis belongs only to nominal terminal NMPC.
- ROS and ROS2 are excluded.

## 2. Equation-to-implementation ledger

| Locked equation or contract | Future implementation | Required parity check |
|---|---|---|
| $\dot p=R(\theta)v$, $\dot v=(u-v)/\tau_v+d$ | Mecanum kinematics, first-order dynamics, and load block | same frames, time constant, load, and angle wrap |
| $X_{k+1}=f(X_k,u_k)$ | Mecanum plant and state propagation | same $\Delta t$, integration order, and angle wrap |
| $\omega_w^{cmd}=K_mu$, $\omega_w=K_m\nu$ | wheel interface | same row order, signs, geometry, and rate limits |
| $(\xi_n,C_n)=F_\theta(\zeta_n,\xi_{n-1})$ | LSTM training/export/inference | identical feature order, normalization, recurrent state, and frozen weights |
| $P_\chi$ and $\mathcal C_k$ | GA decoder and geometric validator | fixed start/rejoin, full-curve clearance, curvature, and offset checks |
| $\chi_k^\star=\arg\min_{\mathcal E_k\cap\mathcal C_k}J$ | finite GA selection | normalized terms, deterministic tie-break, and explicit empty-set outcome |
| path-to-$\mathcal R_k$ conversion | motion-control reference generator | exact plant residual and constraint checks |
| finite-horizon NMPC | controller | feasible selected cost no greater than shifted feasible cost |
| $z_k=X_k+\nu_k$, EKF update | noisy sensor model and Kalman state estimate | covariance PSD, innovation, and trace checks |
| $e_N^TPe_N\leq\rho$ | terminal admission | analytic $P,\rho$ and containment checks |
| Lyapunov descent inequality | proof falsification | nonpositive residual under exact theorem assumptions |

## 3. Stage A — frozen configuration and provenance

1. Freeze notation, frames, units, wheel order, global-path representation,
   state/input boxes, and all model parameters.
2. Register physical parameters separately from nominal values; do not silently
   replace theory values after confirmatory execution.
3. Define immutable train/development/validation/confirmatory partitions and
   separate random-seed namespaces.
4. Record code commit, configuration hash, model hash, dataset provenance, and
   target hardware for every evidence-producing run.

## 4. Stage B — LSTM dataset, learning, and calibration

1. Acquire permitted real human image/depth sequences and independent motion
   measurements; synthetic people may not substitute for the final image test.
2. Build causal features in the registered map/body frames without future-frame
   leakage.
3. Use participant- and recording-disjoint partitions; add site-held-out
   evaluation when sufficient sites exist.
4. Train the current-motion LSTM with score/reward-based self-supervision or
   another registered label-free objective. Do not change its public output.
5. Calibrate direction confidence and the unknown-direction gate on development
   data only, then freeze weights, normalization, and thresholds.
6. Compare constant velocity, Kalman-CV, and LSTM using speed error, direction
   macro-F1, confusion matrix, calibration error, failure rate, and subgroup/OOD
   analysis.

## 5. Stage C — Python CCA simulation

1. Implement the observation-rate recurrent update and planning-event GA update
   as separate clocks.
2. Decode only interior lateral offsets between the current position and fixed
   global-path rejoin point.
3. Validate the full curve against obstacles, the directional human region,
   circumscribed robot footprint, curvature, endpoints, and rejoin geometry.
4. Normalize every fitness term and log each term separately.
5. Compare G0, GCV, GLT, and P under identical GA seeds, decoder, feasibility
   rules, candidate counts, and common NMPC backend.
6. Return no proposal for an empty feasible set; any continued old reference is
   revalidated by the motion-control layer.

### Planned finite repair algorithm

Repair is an implementation option, not a theoretical contribution. Clip
offsets, then test a finite sequence between the proposed chromosome and a
shifted previously selected anchor. Decode and validate the complete curve at
each step; return the first feasible result or failure. Register the contraction
factor, maximum repair steps, decoder accounting, canonicalization, and changed-
rejoin behavior before evaluation. Do not claim monotonic clearance or guaranteed
success. Include penalty-only, reject-only, and finite-repair ablations.

## 6. Stage D — MATLAB/Simulink NMPC and Lyapunov verification

1. Keep MATLAB/Simulink restricted to the six-state plant, reference generator,
   linear MPC, nominal NMPC, terminal NMPC, and Lyapunov analysis.
2. Separate the plant into body-frame first-order velocity dynamics and
   world-frame Mecanum kinematics. Include a constant body-frame acceleration
   load, deterministic sensor noise, and an EKF between measurements and the
   NMPC feedback state.
3. Keep the physical equations in small plain MATLAB files: robot parameters,
   forward/inverse kinematics, dynamics, plant step, sensor model, and EKF.
4. Connect one horizontal Simulink chain: Python CCA reference, current-reference
   selector, tracking-error Sum, NMPC--Lyapunov command, dynamics and kinematics,
   state update, noisy sensors, EKF, and feedback memory. Group only the Mecanum
   Object and Sensors and EKF subsystems.
5. Use a nonzero initial tracking error and a dynamically feasible reference
   ending at a certified rest state.
6. Display and log reference/actual pose and velocity, tracking errors, commands,
   sensor measurements, EKF innovation/covariance, terminal ratio, feasibility,
   constraint margins, selected cost, and Lyapunov residual.
7. Falsify analytic Jacobians, stabilizability, Schur closed-loop dynamics,
   nonlinear terminal invariance, constraint containment, shifted feasibility,
   and descent.
8. Treat solve time as telemetry only; MATLAB real time is not an acceptance
   condition.
9. Use Simulink scopes for reference versus actual position, velocity, error,
   command, and planar trajectory. Arrange blocks horizontally for inspection.

## 7. Stage E — matched simulation and statistics

1. Freeze scenarios for crossing, head-on, passing, overtaking, stop--go,
   dropout/staleness, narrow passages, and lateral Mecanum motion.
2. Determine independent sample size from a declared effect/precision target;
   do not treat planning events, candidates, or timesteps as independent runs.
3. Use paired common-random-number packages and randomized/interleaved method
   order.
4. Report valid-path yield, clearance, length, curvature, global deviation,
   continuity, feasibility, pose/velocity RMSE, completion, collision, fallback,
   and tail latency with confidence intervals and effect sizes.
5. Apply a predeclared multiplicity correction to separate LSTM, CCA,
   motion-control, and end-to-end families.
6. Compare DWA/MPPI only at the end-to-end layer. Compare linear MPC, nominal
   NMPC, and terminal NMPC only on the same reference. Test full Mecanum against
   $v_y=0$ only as a secondary embodiment hypothesis.

## 8. Stage F — software parity and SIL

1. Keep Python as the CCA learning/simulation reference and C++ as the future
   real-robot controller/runtime.
2. Compare one-step and rollout fixtures across Python, MATLAB, Simulink, and C++
   where their equations overlap.
3. Run software-in-the-loop with recorded sensor streams and the frozen plant.
4. Reject parity when frames, angle wrapping, wheel order, time stamps, command
   limits, or fallback semantics differ from the locked theory.

## 9. Stage G — HIL, Jetson, and physical robot

1. Begin with Jetson--STM HIL, wheels lifted or mechanically constrained,
   watchdog active, zero-command timeout, and emergency stop verified.
2. Measure perception, LSTM, GA, NMPC, transport, and full-loop p50/p95/p99,
   worst case, deadline misses, CPU, RAM, and power on the target device.
3. Proceed through low-speed empty-space, fixed obstacle, moving person, and
   combined-context trials only after the previous gate passes.
4. Keep the global path fixed; CCA alone proposes local paths and NMPC alone
   commands the robot.
5. Do not draw a predicted human trajectory on images. Display detections,
   current direction/speed estimates, and the robot local path only.

## 10. Final data package

Each final run must be isolated from development data and export:

- `state.csv`: time, pose, body velocity, and odometry provenance;
- `reference.csv`: time-indexed reference and local-path identifier;
- `control.csv`: selected command, wheel rates, feasibility, and fallback source;
- `context.csv`: detection, current human state, confidence, and model hashes;
- `constraints.csv`: margins, terminal ratio, and Lyapunov residual;
- `map.json`: frame, resolution, origin, and occupancy-data reference;
- `run.json`: scenario, configuration, commit, hardware, sensor, and timing
  provenance.

Results stay outside `src/`. Their quantitative, qualitative, failure, and
limitation analyses are linked in Obsidian before any result enters the
manuscript.

## 11. Authorization gate

The theory-and-manuscript gate was reopened by the explicit implementation
request on 2026-08-23. This execution covers code, simulation, and software-in-
the-loop harnesses only. Hardware is inactive, so no HIL, Jetson deployment, or
physical-robot result is claimed. The manuscript and Overleaf project remain
locked.
