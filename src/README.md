# Robot runtime source

`src/` is reserved for production robot code. Research simulations and
mathematical verification live under `simulations/`.

## Runtime map

- `ai/`: perception, causal human context, and LSTM inference interfaces.
- `control/`: compiled controller and STM transport interfaces.
- `runtime/`: controller adapter, six-state Kalman estimator, experiment
  session, fixed-global/local-path navigation, and map planning.
- `stm/`: STM32 firmware and vendor dependencies.
- `hardware.py`: sensor and robot hardware interfaces.
- `shared.py`: compact shared runtime contracts.

## Authority boundary

The intended runtime chain is:

```text
fixed global path
  -> CCA local robot reference
  -> reference admission
  -> NMPC body-velocity command
  -> STM wheel interface
```

Perception, LSTM, GA, and learned scoring must never issue robot commands. NMPC
is the sole command generator. Human motion predictions are internal context and
must not be rendered as a trajectory on images.

## Current freeze

Physical execution is enabled only through an explicit safety record and an
empty output directory. The existing compiled controller is not accepted as
evidence for the mathematical NMPC formulation until it solves the stated
finite-horizon nonlinear program and passes parity tests against
`simulations/matlab/`.

The production state is `[x,y,theta,vx,vy,omega]`. The command is
`[vx_cmd,vy_cmd,omega_cmd]`; no wheel-torque claim is active. STM velocity,
IMU acceleration and gyro samples are fused by `runtime.kalman.SixStateKalman`.
The filtered state and covariance diagnostics are written to
`robot_state.csv` by both direct experiment paths.

## Direct physical capture

The source-owned smoke/experiment entrypoint is no-ROS and sends zero velocity
unless motion is explicitly admitted:

```bash
PYTHONPATH=src python -m runtime.experiment \
  --port /dev/rai_controller --duration-s 30 --period-s 0.05 \
  --lidar-port /dev/rai_lidar --output experiments/runs/<run-id>
```

For a moving trial, add `--vx-mps`, `--vy-mps` or `--wz-radps`,
`--allow-actuation`, and a safety record containing verified stop, remote
disable and watchdog checks. The runner always sends a zero command in its
shutdown path and records the six-state EKF diagnostics.
