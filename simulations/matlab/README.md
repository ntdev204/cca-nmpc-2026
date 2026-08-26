# MATLAB and Simulink simulation

This directory contains only the NMPC motion-control and Lyapunov simulation.
CCA context processing and GA local-path generation are implemented in Python.

Files:

- `robot_parameters.m`: one simple source for the user-supplied 0.4 m by
  0.4 m geometry, wheel radius, sensor mounts, and nominal simulation load.
- `kinematics.m`: Mecanum inverse (body velocity to four wheel rates) and
  forward (four wheel rates to body velocity) kinematics; `world` and `body`
  modes provide the frame transform.
- `dynamics.m`: body-frame first-order velocity dynamics with constant load.
- `plant_step.m`, `position_step.m`: loaded plant and nominal NMPC prediction.
- `sensor_model.m`, `ekf_step.m`: noisy measurement and six-state EKF.
- `state_jacobian.m`, `rollout_states.m`, `wheel_speeds.m`, `wrap_angle.m`:
  small controller helpers.
- `nmpc_controller.m`: terminal certificate, reference admission, and finite-horizon NLP.
- `simulation.m`: NMPC closed-loop study and Simulink helpers.
- `build_model.m`: generates the closed-loop Simulink motion-control model.
- `run_checks.m`: fast equation and interface checks.

Run from MATLAB:

```matlab
cd simulations/matlab
build_model
run_checks
```

`cca_nmpc_closed_loop.slx` is generated from the Python CCA contract. The top
level is one short closed loop: CCA local path, current reference, tracking
error, NMPC--Lyapunov, Mecanum plant, and Sensors and Kalman. A single
discrete delay makes the estimated-state feedback explicit. The plant group
shows Kinematics, Dynamics, and State update. The estimator group shows the
measurement model and Kalman filter. Position, velocity, trajectory, error,
innovation, and Lyapunov scopes are collected in one Monitoring scopes group
so the main diagram remains readable.

The plant uses the six-state vector `[x y theta vx vy omega]` and body-velocity
command `[vx_cmd vy_cmd omega_cmd]`. The nominal NMPC model is load-free; the
plant receives a constant body acceleration load. The geometry and sensor
mounts come from the user-supplied record used by the console, not from URDF.
Dynamic/load and sensor values are simulation settings, not hardware
identification. The checks are mathematical implementation evidence, not
experimental or real-time evidence.
