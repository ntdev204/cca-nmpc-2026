# CCA-NMPC Research Memory

## Target and current phase

- Target: a strong SCIE Q1 journal submission in control and robotics.
- Current phase: theory and mathematical modeling are locked and synchronized
  to the English Overleaf manuscript; the current goal is complete.
- The real-robot runtime in `src/` is frozen unless a later request reopens it.
- Simulation, training, and experimental code are frozen and specified only in
  `IMPLEMENTATION_PLAN.md`.
- Overleaf is gated: only locked theory and models may be transferred there.
- The manuscript must not be written or built locally.
- Obsidian stores research knowledge; raw runs and operational logs do not belong
  in the vault.

## Immutable research scope

CCA means **Continuous Context-Aware**. The architecture is

`global path + continuous context -> CCA [LSTM + GA] -> local path -> NMPC motion control -> Mecanum robot`.

- CCA is the complete continuous-context layer; LSTM and GA are inside it.
- “Continuous” means one context update for each valid observation, independent
  of the lower-rate GA local-path trigger. Unobserved arrivals are not claimed.
- Its inputs are the fixed global path, robot state, current human context,
  obstacles, and the previous local path when available.
- Its public output is one geometric robot local path. It never emits a control
  command and never replans the global path.
- Human context contains position, speed, coarse direction, and confidence.
- No human trajectory is generated; only observed velocity, direction, and
  confidence are used as context.
- GA searches geometric local-path candidates.
- Reinforcement learning is excluded from the accepted architecture.
- NMPC is the sole command generator.
- State: `[x, y, theta, vx, vy, omega]`.
- Input: `[vx_cmd, vy_cmd, omega_cmd]`; no torque-control claim.
- Lyapunov analysis applies only to NMPC motion control.

## Defensible contribution boundary

Do not claim novelty for context-aware MPC, LSTM estimation, GA path planning,
reference governors, planner--NMPC integration, Mecanum MPC, or terminal-set
NMPC in isolation. The candidate mechanism is the continuously updated context
inside a fixed-path Mecanum local-path generator and its measured downstream
effect. Its value must be isolated with matched layer-wise evaluation.

CCA guarantees only the registered geometric local-path checks. Path
time-parameterization and state-dependent NMPC feasibility belong to the motion
control layer. Never claim that a geometrically valid path guarantees NMPC
feasibility.

The stability result is an adaptation of standard NMPC theory. It is conditional
on a dynamically feasible reference, terminal ingredients, and solver
feasibility. It is not a proof of perception, CCA, GA, arbitrary reference
switching, full-pipeline safety, robustness, or hardware performance.

## Evidence rules

- Every literature claim needs a DOI-bearing primary paper.
- A focused search may support "not found under the stated criteria" but never
  "the first" or "no prior work exists".
- No numerical result is written before a registered simulation produces it.
- Development runs cannot be promoted to confirmatory evidence.
- Learning is frozen before confirmatory evaluation.
- Simulation evidence is not hardware evidence.
- Compile success and unit tests are not experimental validation.

## Fair baseline contract

Prediction, trajectory generation, motion control, and end-to-end navigation are
separate comparison layers. Baselines within a layer share inputs, plant, global
path, constraints, compute budget, seeds, scenarios, failure rules, and metrics.
A DWA local-path adapter may be used in the matched CCA mechanism layer only
when it feeds the same NMPC backend. Native DWA and native MPPI belong only to
secondary end-to-end comparison and cannot substitute for NMPC tracking or
Lyapunov baselines.

## Repository contract

- `src/`: production robot runtime and firmware.
- `simulations/matlab/`: future NMPC motion-control and Lyapunov verification.
- `simulations/python/`: future CCA and matched mechanism simulation.
- `scripts/`: auxiliary setup, validation, and research harnesses only.
- `research/obsidian/`: linked research knowledge only.
- `backup/`: recoverable snapshots excluded from version control.

Code must implement the accepted equations exactly. Simulation comments must be
shorter than 80 characters. Prefer a small number of cohesive files.

## Research loop

1. Load this file and `research/RESEARCH_PROMPT.md`.
2. Update the DOI evidence matrix and nearest-work comparison.
3. Re-evaluate the research gap without changing the fixed architecture.
4. Lock notation, equations, assumptions, theorem, proof, and explicit limits.
5. Map every future falsification, simulation, and experiment to
   `IMPLEMENTATION_PLAN.md` without running it.
6. Check the knowledge graph and theory interfaces for internal consistency.
7. Transfer only the locked English theory/model blocks to Overleaf.
8. Stop the current goal; implementation requires a new explicit request.

## Current review state

The 2026-08-23 focused, non-exhaustive DOI audit locks the literature boundary
but leaves the proposed benefit as `candidate`. Context-aware MPC,
omnidirectional human-conditioned local planning, context-plus-GA, people-aware
GA, GA followed by control, GA inside predictive control, and planner--MPC
hierarchies are established prior art. The only retained candidate is the
measurable effect of observation-rate current-context updates inside the exact
fixed-weight LSTM--GA, fixed-global-path Mecanum local generator.

The six-state Mecanum model, CCA interface, NMPC formulation, and conditional
terminal-Lyapunov proof are locked as theory-only blocks. They establish no
simulation, learning, full-pipeline performance, real-time behavior, safety,
robustness, comfort, or hardware effectiveness. All such work is deferred to
`IMPLEMENTATION_PLAN.md`.

The theory-only manuscript release is recorded for Overleaf project
`6a6dd22be3ab13b78d949879`, history entry `23rd August, 2:31 pm`, on
2026-08-23. Abstract, Introduction, the separate Related Work section, and the
theory now use a curated 34-item DOI bibliography. The live six-page Overleaf
build has zero errors, warnings, and informational layout messages. The
corresponding receipt is
`research/metadata/overleaf_theory_sync_20260823.json`. The explicit
implementation request on 2026-08-23 reopens code execution while keeping the
manuscript and Overleaf project locked.

## Implementation progress — 2026-08-23

- Graph/CCA code is implemented in `simulations/python/study.py` and
  `simulations/python/planner.py`. It preserves the fixed global path, separates
  observation and planning clocks, records matched G0/GCV/GLT/P baselines, and
  emits an explicit no-proposal status when the feasible set is empty.
- The CCA contract is `cca_local_path.csv`, `cca_reference.csv`,
  `cca_events.csv`, and `cca_run.json`. The reference ends at a dynamically
  feasible rest state and uses the locked six-state order.
- Development-only CCA outputs are not paper evidence and do not assert
  hardware, real-time, safety, or closed-loop stability.
- The generated Simulink model is `simulations/matlab/cca_nmpc_closed_loop.slx`.
  It is fed by the Python CCA reference contract and contains the horizontal
  NMPC--Lyapunov, Mecanum plant, state, scope, and logging chain. MATLAB
  `run_checks` passed with Python parity residual about `3.55e-15`; a short
  Simulink smoke run also passed.
- The non-hardware experimental harness is `experiments/run_sil.py`. It uses
  the compiled C++ NMPC runtime, the locked body-velocity STM frame encoder,
  and Astra-S/N10P adapter contracts without transmitting to hardware. A SIL
  run was sealed by `final_pack.py` and analyzed as candidate, source-unverified
  data; no terminal-Lyapunov value or physical sensor result is claimed.
- Redundant development outputs and the superseded Simulink binary were moved
  to `temp/output/implementation-review-20260823`; canonical outputs remain
  under `simulations/results/cca_contract` and the current SIL run directory.
- `scripts/research_harness.py --implementation-only` now closes the code loop
  for layout, equation parity, CCA scope, Simulink linkage, motion contract,
  SIL hardware contracts, short comments, and the paper firewall; all 9 checks
  pass. The full repository gate remains intentionally separate and still
  reports pre-existing research-evidence metadata issues.
- The requested engineering loop is recorded as graph (fixed interfaces and
  scenarios), loop (campaign execution), harness (9-check implementation gate),
  context (causal observation updates), and prompt (this locked plan plus
  `MEMORY.md` state).
- Ruff passes for the changed Python code, and the targeted CCA, final-package,
  robot-model, and STM tests pass (`36 passed`). The two superseded research metadata
  instances (`focused_literature_audit.json` and `claim_evidence_matrix.draft.json`)
  were removed from active validation and retained under the ignored legacy archive
  `temp/output/research-metadata-legacy-20260823`. The full Python suite and repository
  contract check pass after removing only tests that depended on those retired records.

### NMPC plant redesign — 2026-08-23

- The MATLAB model now separates world-frame Mecanum kinematics from body-frame
  velocity dynamics for the six-state vector `[x,y,theta,vx,vy,omega]`.
- The Simulink plant includes a constant body-acceleration load, deterministic sensor
  noise, an EKF state estimator, explicit tracking-error Sum, and feedback memory.
- `build_model.m` generates one horizontal chain from the Python CCA reference
  through NMPC--Lyapunov, dynamics, kinematics, state update, sensors, and EKF;
  all chart outputs are connected to scopes or workspace logs.
- `run_checks()` passes the kinematics/dynamics/load/EKF checks, with
  `ekfCovarianceTrace=0.002069321960404166` and MATLAB--Python parity residual
  `3.5527136788005009e-15`. A 0.1 s generated Simulink smoke run passes, and the
  port audit reports no unconnected output ports.
- `scripts/research_harness.py --implementation-only` passes all nine checks
  after replacing stale block-name expectations with the current model contract.
- No manuscript or Overleaf file was modified; this is simulation implementation
  evidence only, not hardware calibration, real-time, or physical validation.

### MATLAB simplification — 2026-08-23

- The physical model class was removed. The model is now exposed as small plain
  MATLAB files: `robot_parameters.m`, `kinematics.m`, `dynamics.m`,
  `plant_step.m`, `position_step.m`, `sensor_model.m`, and `ekf_step.m`.
- `kinematics.m` contains both forward and inverse mappings. The NMPC class is
  retained only for the finite-horizon controller and certificate routines.
- `build_model.m` now generates `cca_nmpc_closed_loop.slx`: one closed loop at
  the top level, with `Mecanum Object` and `Sensors and EKF` as the only grouped
  subsystems. The object subsystem visibly contains kinematics, dynamics,
  derivative, and state-update blocks with their equations in the block names.
- A delayed command inside the sensor subsystem breaks the estimator/controller
  algebraic loop. Build, 0.1 s smoke simulation, recursive port audit, and
  `run_checks()` all pass; harness remains `9/9`.

### Robot-parameter source correction — 2026-08-23

- The robot geometry authority for this simulation is the user-supplied record
  used by the console: total length and width `0.400 m`, half-length and
  half-width `0.200 m`, and wheel radius `0.050 m`.
- The same source records LiDAR height `0.240 m`, camera height `0.200 m`,
  LiDAR front offset `0.100 m`, camera front offset `0.035 m`, camera position
  `x=0.165 m`, and a `20` degree downward camera pitch. The URDF remains a CAD
  reference and is not used to overwrite these values.
- The previous unreferenced mass/inertia and damping values were removed. The
  plant now uses the locked first-order velocity model
  `dv=(u-v)/tau+d`, where `d` is a constant simulation load; this keeps the
  MATLAB code aligned with the theory and avoids presenting invented dynamics
  as measured robot parameters.
- The MATLAB package folder was removed. The finite-horizon controller and
  study helpers are now `nmpc_controller.m` and `simulation.m` at the MATLAB
  root. The generated Simulink object label exposes the simple dynamics
  equation without a slash in the block name. Equation checks, Simulink build,
  0.1 s smoke simulation, and the 9-check implementation harness pass.

### Physical runtime and Kalman estimator — 2026-08-24

- Added `src/runtime/kalman.py` with a six-state EKF for
  `[x,y,theta,vx,vy,omega]`. It propagates body velocity through the measured
  heading, accepts STM acceleration and gyro inputs, updates with measured body
  velocity, wraps heading, clamps stale sample intervals, and exposes covariance
  diagnostics.
- `scripts/python/tools/record_hardware.py` and `stm_experiment.py` now feed STM
  or CAN telemetry through the EKF before logging `robot_state.csv` and before
  passing state to online CCA-NMPC. CSV rows include estimator identity and
  position/heading/velocity uncertainty indicators.
- Added the source-owned no-ROS entrypoint `python -m runtime.experiment` for
  direct STM32 capture with optional N10P logging, explicit actuation and safety
  gates, zero-command shutdown, CSV output, and runtime metadata.
- Tests: full Python suite passed; targeted EKF, hardware, runtime-entrypoint,
  and STM recorder tests passed. Ruff and `git diff --check` passed. CMake/CTest
  could not be rerun on this Windows host because `cmake` and `ctest` are not on
  PATH; existing build artifacts were not treated as a fresh build.
- No manuscript or Overleaf file was modified. This closes software integration
  only; it does not claim physical calibration, real-time performance, or a
  completed robot run.

### STM build verification — 2026-08-24

- The C++ STM/controller transport under `src/control` was configured and built
  in WSL Ubuntu 22.04. `control_core`, `control_transport`, `stm_probe`, and
  `control_tests` built successfully; CTest passed `1/1`.
- The STM32 firmware protocol/kinematics host suite
  `src/stm/tests/run_host_tests.ps1` compiled with Visual Studio C11 tools and
  reported `CCA STM host tests: PASS`.
- The embedded Keil project `src/stm/USER/RAI.uvprojx` was not converted to a
  `.hex` or `.bin` because Keil µVision and `arm-none-eabi-gcc` are not
  installed on this workstation. No firmware flash was performed.

### Simulink layout simplification — 2026-08-24

- Rebuilt `simulations/matlab/cca_nmpc_closed_loop.slx` from the shorter
  `build_model.m` layout: CCA local path, current reference, tracking error,
  NMPC--Lyapunov, Mecanum plant, and Sensors and Kalman are the visible
  horizontal loop.
- The plant group exposes kinematics, dynamics, and state update; the
  estimator group exposes measurement and Kalman blocks. One explicit unit
  delay is placed on the estimated-state feedback to remove the algebraic loop.
- Position, velocity, trajectory, tracking error, Kalman innovation, and
  Lyapunov scopes are grouped in one monitoring subsystem. A 0.2 s Simulink
  smoke simulation completed with `SIM_OK`; no manuscript was modified.

### STM host build — 2026-08-25

- Ran `src/stm/tests/run_host_tests.ps1`; protocol, kinematics, runtime,
  telemetry, wheel-control, and firmware tests compiled with MSVC and reported
  `CCA STM host tests: PASS`.
- A target `.hex` build was not attempted because µVision/UV4 and ArmCC are not
  installed on this workstation; the downloaded DFP is only the STM32 device
  pack and is not a compiler.

### EDGE web console and live map pose — 2026-08-25

- The no-ROS backend now initializes odometry at startup and keeps `map_pose`
  equal to live odometry whenever scan matching is disabled. The map grid stays
  fixed, so the web marker moves with the physical robot; an explicitly enabled
  matcher can still own a corrected map-frame pose.
- Repeated stream traffic was removed: state remains 10 Hz, LiDAR is emitted
  only for a new scan, map snapshots are emitted at 2 Hz, and each peer retains
  only the newest stream packet. The Next bridge losslessly delta-delivers map
  and camera frames while preserving JSON-bigint timestamps and full saved data.
- Keyboard control is mounted in the root layout (`W/S/A/D`, arrows, `Q/E`,
  Space stop), so it remains active across routes; the former web
  Teleoperation card was removed and the right dashboard rail was compacted.
- Verification: Python targeted runtime/map suite `27 passed`; web lint passed;
  `next build` passed; Jetson backend restarted with STM32, N10P and Astra-S
  online; `/api/status` returned HTTP 200 and `map_load` delivered one full map
  followed by a delta response without repeating the map payload.
- A new client automatically receives the newest saved map when one exists;
  the explicit `Load last map` action remains available for operator refresh.
- Keyboard velocity heartbeats now continue without an in-flight suppression;
  velocity commands bypass the slow command queue and the velocity API returns
  a tiny acknowledgement. Releasing the key still sends a zero command.
- Camera JPEGs are no longer copied into status JSON. The web uses the binary
  `/api/camera` multipart MJPEG stream, verified with four frames and the
  `multipart/x-mixed-replace` content type.

### Fixed-map monitor and combined keyboard control — 2026-08-25

- The web dashboard now presents one combined Map & camera monitor: the
  occupancy map and level Astra-S MJPEG view share the main panel. TF/sensor
  frame controls, the follow-robot option, and the old status-card list were
  removed; live pose, velocity, yaw rate, battery voltage, and LiDAR rate are
  compact header telemetry.
- Camera geometry is now declared level (`camera_pitch_deg=0`,
  `camera_pitch_rad=0`) in `configs/physical_robot.json`, and the same default
  is used by the backend on Jetson.
- Root keyboard control combines simultaneous keys. W+D produces diagonal
  velocity and W+Q produces forward velocity with yaw; releasing one key keeps
  the remaining command active, and release/blur/visibility still sends stop.
- Verification: `npm run lint`, `npm run build`, backend `py_compile`, targeted
  Python suite (`27 passed`), and a live MJPEG probe (5 JPEG frames, 50,894
  bytes in 2 s; timeout is expected for the persistent stream). Jetson was
  resynchronized and reported camera pitch `0` through `/api/status`.

### Realtime camera transport — 2026-08-25

- The initial JSON/base64 camera path was measured at below 20 FPS because the
  single control writer also carried the map and telemetry. The Jetson now
  serves raw multipart MJPEG on port `8766`, separate from control/telemetry on
  `8765`; the Next route proxies that binary stream without re-encoding.
- The camera source runs at about 29 FPS. The live Jetson profile is now
  640x480/JPEG-10; capture encoding remains full-resolution and is separate
  from the preview. Map packets are compressed before the first client map is
  sent; the camera is no longer scheduled on the control stream, while state
  and new LiDAR packets retain priority over map snapshots.
- Verification: direct Jetson MJPEG delivered 127 frames in 5 s (25.4 FPS),
  and the laptop `/api/camera` proxy delivered 134 frames in 5 s (26.8 FPS).
- Camera JPEGs are no longer emitted in the control/telemetry JSON stream;
  only state metadata carries camera timestamps/rate, while all image bytes
  travel through the raw MJPEG endpoint.
- Final no-base64 verification: direct Jetson MJPEG delivered 126 frames in 5 s
  (25.2 FPS), and the laptop `/api/camera` proxy delivered 133 frames in 5 s
  (26.6 FPS); status contained no camera JPEG field.
- The FE now calls `http://100.69.39.18:8766/mjpeg` directly. With the required
  640x480 stream, the same constrained link measured 28 frames in 5 s
  (5.6 FPS) at JPEG-20. The current JPEG-10 deployment delivered 45 frames in
  5 s (9.0 FPS) and the first JPEG decoded as 640x480; the source camera still
  reports about 28.8 FPS. This is the current resolution/bandwidth trade-off,
  not a JSON buffering delay.

### WebRTC H.264 camera transport — 2026-08-25

- The browser camera path now uses a direct `POST /webrtc/offer` signaling
  endpoint on Jetson port `8766`; the frontend creates a receive-only
  `RTCPeerConnection` and renders the negotiated track in a muted video node.
- Jetson has `aiortc 1.14.0`, PyAV `16.1.0`, and H.264 codec support. The
  backend sets H.264 codec preferences and publishes the raw 640x480 Astra-S
  frames without JPEG/Base64 conversion. `/mjpeg` remains only as a diagnostic
  fallback.
- End-to-end Jetson aiortc verification returned an SDP answer containing
  H.264 and three 640x480 frames. A five-second receive test delivered 144
  frames (29.4 FPS). The active frontend connection is visible as
  `webrtc_clients=1` in the Jetson status.
- PyAV's `libx264` encoder is the working aiortc encoder on this image;
  direct `h264_nvenc` and `h264_v4l2m2m` codec-open probes failed, so a future
  hardware-encoder optimization would require a separate GStreamer pipeline.
- The camera loop no longer JPEG-encodes frames when no MJPEG client is
  connected; this leaves CPU and bandwidth for WebRTC/H.264 and still keeps
  high-quality JPEG/depth capture for an active dataset run.

### Pose and yaw synchronization — 2026-08-25

- The STM packet exposes both encoder body yaw rate (`wz_radps`) and IMU
  `gyro_z_radps`. The map pose previously integrated only the encoder value.
- The pose integrator now uses gyro-z only when the two measured rates show a
  clear, same-sign disagreement; matched readings remain encoder-based.
- State telemetry now exposes both yaw-rate sources, selected source, used
  rate, integration interval, and planar speed. The SVG heading line was
  corrected for the inverted world-y display axis.
- Synthetic checks cover the half-rate disagreement case and a 180-degree
  integration. A live 180-degree turn is still required before claiming
  hardware calibration or final pose accuracy.

### Map capture and selection component — 2026-08-26

- Map capture is isolated in `app/web/src/components/map-capture-panel.tsx`.
  The component owns start, save, stop, saved-map selection, and map loading
  controls; the monitor remains responsible for displaying the fixed map.
- The Jetson backend exposes completed `console-map-*` runs through the state
  payload. Each entry includes run id, scan/point counts, resolution, size,
  and the currently selected map. `map_load` accepts only a single run
  directory name and broadcasts the selected map to the frontend.
- The frontend build and targeted backend tests pass. An interrupted raw run
  remains preserved but is excluded until `map.json` is present; it must not
  be reported as a completed map.

### Bounded straight hardware scan — 2026-08-26

- Jetson preflight confirmed STM, N10P (about 10 Hz), and Astra-S online. The
  straight-only supervisor used the 10th-percentile clearance per sector,
  repeated danger confirmation, a 0.05 m/s cap, a 1.2 m distance cap, and a
  watchdog-backed zero command.
- The controlled pass recorded `console-map-20260826-100218` with 6 scans and
  3,711 points; odometry reported about 0.23 m forward displacement before
  the time limit. It was saved at 25 mm resolution and then disarmed.
- A separate subsequent scan session (`console-map-20260826-100326`) appeared
  while checking the final state. It was emergency-stopped; its saved package
  contains 55 scans and 32,305 points. Its motion provenance must be reviewed
  before attributing it to the bounded supervisor.

### Map noise diagnosis and correction — 2026-08-26

- The saved `console-map-20260826-100326` package used odometry-only mapping
  (`scan_matching.enabled=false`). Its 55 scans covered about 0.6 m of pose
  displacement and produced diagonal ray artefacts, so it is not a valid final
  map result.
- The N10P stream contained 1,026 entries per scan, including zero-distance
  secondary returns. The decoder now rejects zero/invalid ranges, and the map
  integrator keeps only the nearest valid return for each angle before ray
  tracing. This prevents a farther secondary return from carving through a
  nearer obstacle.
- New captures enable the bounded local scan-to-map matcher. Offline replay of
  the saved raw package accepted 12 of 54 eligible corrections; this is a
  bounded local correction, not a global-SLAM claim. The robot console was
  restarted with the updated files and left disarmed after verification.
- A stationary verification capture (`console-map-20260826-102206`) recorded
  6 scans and 3,064 mapped points without commanding motion. It contains no
  zero-distance returns, accepted 5/5 local matcher updates, and reports 1,009
  occupied cells. The run is selected for inspection; it is a static sensor
  check, not a complete room-scale map.

### Bounded reverse scan attempt — 2026-08-26

- The first web-API trial stopped after 0.017 m because the local progress
  guard compared a distance value after overwriting its previous value. No
  5 m motion was commanded in that trial.
- A direct compressed control-socket trial then moved backward to about 1.11 m
  before the rear-sector LiDAR p10 clearance fell below the 0.75 m safety
  threshold (observed p10 0.728 m). The robot was emergency-stopped and the
  run `console-map-20260826-104226` was saved with 45 scans and 24,252 mapped
  points. The requested 5 m distance was not reached because continuing would
  violate the clearance gate.
- The control bridge was rebuilt so velocity requests do not wait for a state
  frame, and the backend no longer auto-arms a robot when a new client connects;
  E-STOP now persists across reconnects. Jetson and laptop web processes were
  restarted and the final status was `armed=false`, command zero.

### Web control latency and map rendering — 2026-08-26

- The keyboard sender now coalesces velocity requests with a single in-flight
  request and a 100 ms refresh period; stale commands are not queued behind
  newer commands. The production web build and lint pass.
- The map occupancy layer was moved from hundreds of thousands of SVG elements
  to a canvas overlay. This removes the rendering backlog that delayed key
  events while a large 25 mm map was visible.
- The map viewport now resets when width, height, resolution, or origin changes;
  loading a different saved map no longer reuses the previous viewport.
- Transient laser rays are off by default in the map view; the dedicated live
  LiDAR panel remains available and the rays can be enabled when needed.
- The laptop web process was restarted with the new build. The robot remains
  disarmed with a zero command; no motion was sent during this fix.

### Python map reconstruction and control-load fix — 2026-08-26

- The Python mapper now exports a cleaned occupancy map using an 8-connected
  occupied-component filter. Components smaller than three 25 mm cells are
  removed from `map.json` and `map.pgm`; raw sensor evidence remains in
  `lidar.csv`, `map_history.jsonl`, and the new `map_raw.json`.
- Loading an older saved map applies the same filter in memory before it is
  broadcast, so the current 661x649 map removed 649 isolated occupied cells
  (2368 raw occupied cells to 1719 displayed cells).
- Map payload generation now checks scan/point counters before rebuilding the
  full grid. After deployment, Jetson backend CPU settled near 51 percent with
  the robot disarmed; no velocity was sent.

### Motion permission toggle — 2026-08-26

- The web header now exposes a `Motion ON/OFF` button that sends the explicit
  `arm` command. The keyboard remains globally available, but it can actuate
  only while the button reports `Motion ON`; disabling it sends zero velocity.
- The backend and web build were restarted with the robot left disarmed after
  verification.

### Flat ROS 2 source workspace — 2026-08-26

- The active `src/` tree now contains only ROS 2 packages directly: `cca_control`,
  `cca_runtime`, `cca_hardware`, `cca_bringup`, `turn_on_robot`, and `depend/`.
- The former `src/ros2/` wrapper and non-ROS trees (`ai`, `runtime`, `control`,
  `stm`, and Python hardware modules) were removed from the active branch.
- The C++ controller and serial core used by ROS 2 was moved into
  `src/cca_control`; the manufacturer's STM32 firmware remains on the robot.

### shadcn navigation primitives and synchronized branches — 2026-08-28

- The web dashboard keeps the sidebar layout and now uses the generated shadcn
  `Pagination` and `Select` primitives; no native `<select>` remains in the
  control, history, or map-capture panels.
- Local `ros2` is synchronized at `6faff34`; the clean Jetson ROS 2 worktree
  `/home/rai/cca-nmpc-ros2` is at the same commit. Jetson runtime changes are
  committed on `codex/repository-bootstrap` at `4c1eb49`, followed by the same
  six UI files at `600865a`.
- Web lint, TypeScript, and production build pass. Jetson Python syntax and
  C++ control tests pass; the robot was not commanded during synchronization.

### Map transport and scan-lag correction — 2026-08-28

- The live map message now uses lossless `rle-v1` occupancy encoding and keeps
  only short history slices on the wire. Saved `map.json` and `map_raw.json`
  remain full-resolution occupancy arrays; the browser decodes RLE before
  drawing the canvas.
- Map history in the laptop bridge stores metadata summaries rather than full
  occupancy grids. This prevents old 25 mm maps from accumulating in Node.js
  memory and blocking control responses.
- The map viewport expands by world-coordinate union as a scan grows, so the
  fixed map frame remains fixed while newly explored cells are not clipped.
- Local commit `a55da12` and Jetson commit `247ffc8` contain the transport and
  viewport fix. Web lint, TypeScript, production build, Python syntax, and an
  RLE round-trip check pass.
- A stationary Jetson validation run (`console-map-20260828-123648`) recorded
  325 scans and 76,583 mapped points at 10 Hz without motion commands. During
  the scan, ten status requests averaged 24.7 ms (maximum 39.9 ms); the saved
  map retained all 101,120 occupancy cells.
- With one active WebRTC client, a second stationary scan
  (`console-map-20260828-124517`) kept velocity-zero requests at 36.8 ms on
  average (160.6 ms maximum) and status requests below 170 ms. It was saved
  with 291 scans and 66,586 mapped points; the final command was zero and
  motion was disarmed.
- The custom occupancy mapper is still odometry-based and is not a validated
  room-scale SLAM result. A moving hardware run with calibrated odometry or
  the ROS 2 `slam_toolbox` pipeline remains required before claiming a complete
  map; no moving test was issued in this correction.

### Persistent scan correction and edge-load check — 2026-08-28

- Runtime mapping now enables bounded scan-to-map correction every fifth scan
  and carries the corrected map pose into the next fusion update; live odometry
  remains separate from the map-frame pose.
- WebRTC remains 640x480 but uses a 15 fps idle budget and 5 fps scan budget to
  reduce CPU contention with LiDAR fusion. Zero-velocity requests during a
  stationary scan averaged 10.8 ms with a 23.9 ms maximum.
- Jetson `manual_map.py --self-test` and `robot_console.py --self-test` pass
  after correcting the self-check to distinguish raw cells from cleaned cells.
- The latest stationary check (`console-map-20260828-130448`) finished with
  64 LiDAR scans, 14,524 mapped points, and the robot disarmed at zero command.
- Commits `d955a35`, `cd90640`, and `0a25bcc` are on `ros2`; corresponding
  active Jetson commits are `abd7160`, `0f619c1`, and `77041f2`.
- The map is not yet certified as complete for moving operation: scan matching
  is local and bounded, without loop closure. A controlled moving run or the
  ROS 2 `slam_toolbox` path is still needed for room-scale map validation.

### Remove live LiDAR overlay and guard map turns — 2026-08-28

- The standalone Live LiDAR card, transient laser rays, and browser-side raw
  LiDAR stream were removed. LiDAR remains active inside the Jetson mapper and
  is still written to each run's `lidar.csv`.
- Runtime mapping now uses the measured odometry frame (`LIVE_SCAN_MATCHING`
  is false). The offline bounded matcher keeps stricter inlier/gain gates,
  rejects high-yaw-rate scans, and limits accepted yaw corrections to 3 degrees.
- The map canvas uses the saved map footprint metadata and displays only the
  fixed occupancy grid, robot pose, trace, and planned path.
- Local `ros2` commit `8582c0f` is pushed to `origin/ros2`; the active Jetson
  runtime contains the cherry-pick `cdc0fa9`. Web lint, TypeScript, production
  build, Python syntax, and both Jetson self-tests pass.
- After restart, an emergency stop left the robot at `armed=false` with command
  `0,0,0`; no scan or motion command was issued during this fix.
