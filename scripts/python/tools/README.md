# Active experiment entry points

The active workflow has two independent parts:

1. `ctx_run.py` reads a real robot `context.csv`, trains/evaluates the CCA LSTM
   from future observed context velocity, and reports constant-velocity and
   Kalman-velocity baselines on the same chronological split. Direction labels
   are diagnostic only and never enter the optimizer. It emits only context
   snapshots; CCA-NMPC may later propagate a snapshot velocity internally, but
   `ctx_run.py` never exports that future sequence. The metrics include
   direction calibration (reliability
   bins, ECE, Brier and NLL) and deterministic bootstrap intervals; a
   per-class precision/recall/F1/support table and confusion matrix are emitted
   for each evaluation split; a chronological single-run split is explicitly
   not an ID/OOD holdout.
   For confirmatory data, pass `--split-manifest` with schema
   `cca-context-split-manifest-v1` and point `--input` to a sealed direct
   CSV/JSON run directory. The directory must contain a verified `manifest.json`
   whose capture source is `hardware`, `hardware_in_loop`, or `real_offline`,
   whose `context.csv` digest matches the input, and whose context-only and
   no-human-trajectory flags are intact. Assignments are made by
   recording/episode group before training and must include train, validation,
   calibration, test_id and test_ood. After checkpoint selection it fits one
   temperature on `calibration` only, records the fit provenance, then reports
   independent ID/OOD metrics without tuning on either test partition. It rejects
   missing or contradictory group assignments and synthetic/unsealed input.
   The score loop accepts `--seed-count N` to train independent candidates and
   retain a completed/failed seed ledger. The highest validation self-supervised
   score is selected with a deterministic lowest-seed tie-break. Confirmatory
   runs require at least five requested and five successfully completed seeds;
   development runs may use one seed and remain candidate-only. The selected
   seed and full ledger are written to the checkpoint and run metadata.
   An explicit `--simulation-only` flag permits a sealed simulator package with
   `capture_source=simulation`, an episode-group split and a simulation
   calibration sidecar. This exception is candidate-only and never satisfies
   the real-capture or hardware gate; without the flag synthetic input remains
   rejected.
2. `map_run.py` builds the Python map, uses a
   bounded environment-score loop to tune local-path parameters, holds the
   global path fixed, and regenerates the robot local path only when the latest
   dynamic context footprint conflicts with the path or the direction context
   changes. Only the CCA-NMPC branch receives its internal future-position
   prediction; all baselines use the current snapshot.
   Use the default `--campaign pilot` for development. A confirmatory campaign
   requires at least 30 paired replicates and `--no-score-tune`; it cannot tune
   local-path parameters on the confirmatory scenarios. Confirmatory execution
   also requires `--protocol-freeze` pointing to a valid frozen PR20/PR21 record;
   the focused audit and protocol schema therefore remain fail-closed. The
   runner also rejects missing or duplicate replicate/scenario/controller pairs
   and any change to the global path. Aggregate output records paired bootstrap
   95% intervals for the primary descriptive metrics with a fixed seed; these
   intervals do not promote a development campaign to confirmatory evidence.
   The optional `--lstm-checkpoint` connects the frozen self-supervised LSTM
   output to the CCA prediction rows using only the causal context history. A
   pilot without this option is explicitly recorded as the direct
   direction/speed adapter; confirmatory execution requires the checkpoint and
   rejects it unless its metadata carries the sealed real-capture manifest hash.

The optional `navwareset_context.py` adapter is a provenance-bound,
real-offline data converter for a future mechanics exercise. No candidate
payload is currently retained after the 2026-08-14 reset; a new source must be
provided explicitly and must never export or draw a human future path.

The four tracked registries are empty after the 2026-08-14 clean reset.
Candidate run outputs can remain in the local ignored `experiments/runs/`
directory for internal diagnosis, but they are not committed, are not evidence,
and are excluded from the Jetson deployment snapshot. Superseded data, model,
result and human-trajectory payloads were removed; only the paper snapshot under
`backup/paper-current-2026-08-01/` is retained for archival reference. The
exact-path purge audit is `research/metadata/development-purge-20260814.json`.

Each entry point bootstraps the repository source paths, so it can be invoked
directly from the repository root with `python -B scripts/python/tools/<tool>.py`.
No ROS/ROS 2 runtime or editable local paper build is required.

3. `det_eval.py` evaluates YOLO26s-pose on a newly acquired Internet-image
   manifest and writes an image-level confusion matrix, latency diagnostics,
   overlays, and a manifest. Bounding-box metrics remain disabled until blind
   box annotations are available. Supplying the independently created
   `--annotations` manifest enables candidate IoU, TP--FP--FN and
   average-precision diagnostics; it never treats model predictions as labels.
   An optional `--context` file adds a
   provenance-checked current position/speed/direction overlay; it rejects
   predicted human trajectory fields and does not create a robot local path on
   the image. When `--lstm-checkpoint` is supplied with `--context`, the tool
   verifies its SHA-256 against the snapshot model hash and prints the resolved
   local checkpoint path on every gallery image; omission is shown explicitly
   as `LSTM_PATH=<not-provided>`.
   The reset removed all former defaults: `--manifest`, `--weights` and
   `--output` must be supplied explicitly for each new acquisition.
4. `validate_web_cohort.py` performs the non-model PR10 preflight for schema,
   media hash/decode, blinded annotation binding, split-group disjointness,
   rights and privacy fields. A `PASS` from this tool does not admit the cohort;
   independent annotation, overlap review and held-out expansion remain gates.
   Its manifest, annotation and output paths are also explicit and cannot point
   implicitly to the purged cohort.
5. `validate_hardware_entry.py` performs the static PR30 entry preflight for the
   STM CAN and legacy serial frame boundaries, Python decoder parity,
   position-state/body-velocity scope, mini-Mecanum URDF binding, commissioning
   lock, direct CSV/JSON mapping and no-ROS path. A `PASS`
   is software/interface QA only; hardware admission remains blocked until H0
   approvals, calibration and a sealed direct package exist.
6. The frozen PR01 search files are historical provenance only; no PR01 runner
   is part of the active workflow. The paper uses a focused Zotero/Obsidian
   literature audit and does not require database export access.
7. `repo_check.py` runs the repository contract checks.
8. `final_pack.py` validates the four robot CSV plus map inputs after a physical
   run and seals them with `manifest.json` and `checksums.sha256`. Pass
   `--camera "Astra-S" --lidar "N10P" --firmware <version>` and the explicit
   `--control-interface body_velocity` so the package records the actual sensor,
   firmware and physical actuator interface. The interface option checks that
   `control.csv` contains the body-velocity signal group;
    this keeps the physical package aligned with position tracking. A non-unknown capture source also requires a hashed
    `calibration.json` sidecar containing camera intrinsics, camera/LiDAR
    extrinsics and calibration residuals; without it, `ctx_run.py` cannot admit
    the package for confirmatory LSTM training. It rejects unrelated files and does not connect to a
   runtime message layer, replay a run, or run MATLAB.
    The active recorder/package path is direct CSV/JSON and has no ROS/ROS 2
   runtime dependency.
9. `analyze_run.py` reads a sealed package and writes a separate provenance-linked
   `analysis.json`; it never copies or modifies the raw package and refuses to
   manufacture tracking labels or a direction confusion matrix. It also
   summarizes structured online CCA-NMPC events (solver status, local replans,
   deadline misses, risk/constraint diagnostics and parse failures) without
   exporting a human future path.

10. `record_hardware.py` is the higher-level physical recorder. It opens Astra-S through
    OpenNI2, N10P through its serial packet stream, and consumes the C++ STM32
    serial bridge or the CCA CAN telemetry interface without ROS or ROS 2. The
    C++ path reproduces the 11-byte body-velocity command frame and 24-byte
    telemetry frame; `shared.py` also selects the C++ CCA CAN codec when
    the shared library is present. The
    default `--controller external` mode can execute a time-stamped command CSV
    only with explicit `--allow-actuation`; the explicit `--controller cca_nmpc`
    mode computes body-velocity commands online from six-state odometry, the
    fixed global path and the current context through the finite-horizon
    position-state CCA-NMPC solver.
    It writes context, robot state, applied and commanded body velocity, events,
    a copied map and a calibration sidecar.
    Online event details include controller status, bounded-rollout diagnostics,
    deadline, nominal constraint violation and the reserved bookkeeping field
    `risk_slack_m`; it is not an optimized slack variable or solver residual.
    The command fails closed before opening a device when physical dimensions,
    calibration or YOLO26s-pose TensorRT provenance is missing. The
    `--lstm-checkpoint` argument is optional for the initial context-only
    capture used to create the first real training dataset; when omitted, every
    overlay and CSV row records `LSTM=disabled` and
    `LSTM_PATH=<not-configured>`. When supplied, every overlay prints the
    resolved local checkpoint path and distinguishes `warmup`, `active` and
    `invalid`. Bounded candidate-rollout faults and deadline misses are recorded
    as fallback status. The
    recorder never exports
    or draws the CCA-NMPC internal future-position sequence. Online CCA requires
    `--controller cca_nmpc`, a sealed checkpoint, map settings containing
    `global_path_xy` and `cca_nmpc`, STM32 serial transport and
    `--allow-actuation`; it sends zero velocity during LSTM warmup, invalid
    context, deadline miss or STM stop. External mode is capture-only/
    commissioning for this protocol and is not an admitted final controller for
    dynamic-human trials; without a schedule it sends only zero velocity.

    A direct STM32 run is launched only after H0 approval and concrete config:

    ```powershell
    python -B scripts/python/tools/record_hardware.py `
      --config configs/hardware_runtime.<run>.json `
      --calibration <calibration.json> `
      --map <map.json> `
      --pose-engine <yolo26s-pose.engine> `
      --pose-manifest <pose-manifest.json> `
      --lstm-checkpoint <ctx_lstm.pt> `
      --command-csv <body-velocity-commands.csv> `
      --safety-record <h0-safety.json> `
      --allow-actuation `
      --output experiments/runs/<run-id> `
      --duration-s <seconds>
    ```

    For online CCA-NMPC, omit `--command-csv` and add `--controller cca_nmpc`.
    The copied map must contain positive `cca_nmpc.horizon`,
    `cruise_speed_mps`, `human_std_m`, `safe_distance_m`, `lateral_offset_m`
    and `longitudinal_offset_m`; `human_clearance_m` may be supplied to bind
    the controller to the measured robot-plus-context footprint. Global path points are never replaced; only a
    local detour is regenerated on a declared context conflict or direction
    change.

    The command CSV contains `t_s,vx_mps,vy_mps,wz_radps` with strictly
    increasing timestamps. `transport` must be `stm32_serial`; the recorder
    binds `mini_mec_robot.urdf` before opening devices. The command is not run
    until ports, firmware, calibration, watchdog, emergency stop and the H0
     stage gate are recorded.

11. `stm_experiment.py` is the small Python-compatible STM32 bring-up and
    telemetry recorder. The preferred direct path is the C++ `stm_probe`
    target in `src/control`; this Python path reuses the same 11-byte command and
    24-byte telemetry contract implemented in `src/hardware.py`,
    whose constants are audited against `reference/robot/turn_on_rai_robot/src/rai_robot.cpp`
    and `include/turn_on_rai_robot/rai_robot.h`. It opens only the serial device,
    never imports or launches ROS/ROS 2, sends body-velocity commands, and
    writes `robot_state.csv`, `control.csv`, `events.csv`, `capture.json`,
    `manifest.json` and the exact command schedule. The state CSV integrates
    the STM-reported body velocity into
    `[x_m,y_m,theta_rad,vx_mps,vy_mps,omega_radps]`; it does not silently use
    URDF dimensions. A nonzero schedule requires both `--allow-actuation` and
    a safety record with verified emergency stop, remote disable and watchdog.
    The recorder sends an explicit zero command on normal exit, Ctrl-C and
    serial failure, and latches an STM stop flag before selecting any next
    command. `--map-json` only copies and hashes an existing map; no map
    or result is generated by this tool.

    The physical run is staged:

    ```powershell
    python -B scripts/python/tools/stm_experiment.py `
      --port COM5 --baud 115200 --duration-s 30 --period-s 0.05 `
      --pattern observe --operator <name> --firmware-id <id> `
      --output experiments/runs/<bringup-id>
    ```

    After the measured dimensions, wheel signs and footprint are supplied,
    copy `configs/physical_robot.template.json` to a versioned file, fill it
    with `status: measured`, and pass it to `hardware_entry.py prepare
    --physical-spec`. The URDF/xacro values remain CAD and mount/protocol
    references and are not valid substitutes for that measured file.

12. `hardware_entry.py` is the single no-ROS operator entrypoint. It reads the
    supplied `rai_robot_urdf` package before any device is opened: all 37 package
    URDF models are catalogued, and the selected mini-Mecanum record contains the
    four wheel components (origins, axes, masses and meshes), body mesh,
    camera/laser mounts, sensor-library assets (`astra.dae`, `lds.stl`,
    `r200.dae`) and the mini-Mecanum xacro wheel radius. It also records the
    mesh-and-mount circumscribed planar footprint used by the Python map
    contract. The recorder verifies the URDF/xacro hashes before opening a
    device, and the runtime capture sidecar repeats those hashes,
    measured geometry provenance and footprint so each physical CSV package
    remains traceable to the loaded robot model. The xacro ray-lidar,
    RGB/depth-camera and IMU settings are recorded as simulation-only metadata;
    they do not identify or calibrate the physical Astra-S/N10P devices. It also
    creates a path-resolvable runtime config and explicit zero-terminated body
    velocity schedules, then forwards the final record command to
    `record_hardware.py`.

    ```powershell
    $env:PYTHONPATH = 'src;scripts/python'
    python -B scripts/python/tools/hardware_entry.py inspect `
      --output research/metadata/hardware/mini_mec_intake_<UTC>.json
    python -B scripts/python/tools/hardware_entry.py prepare `
      --output configs/hardware_runtime.<run>.json `
      --stm-port /dev/rai_controller `
      --lidar-port /dev/rai_lidar `
      --lidar-baud <measured-baud> `
      --firmware <STM32-firmware-id> `
      --physical-spec configs/physical_robot.<run>.json
    python -B scripts/python/tools/hardware_entry.py schedule `
      --output experiments/commands/<run>.csv `
      --kind forward --duration-s 5 --step-s 0.1 --speed-mps 0.05
    ```

    `record` accepts the same calibration, map, YOLO26s-pose TensorRT manifest
    and optional frozen LSTM inputs as the recorder. It requires
    `--confirm-motion` and `--safety-record` before any nonzero command; without
    them the capture path remains zero-velocity. The safety record must verify
    approval, emergency stop, remote disable and watchdog. For the final moving-person trial use
    `--controller cca_nmpc` without `--command-csv`; only that branch receives
    the internal LSTM human-position prediction. No human future path is saved
    or drawn.

    Before a physical run, use the no-device preflight to catch configuration
    and provenance errors without opening a sensor or creating an output run:

    ```powershell
    python -B scripts/python/tools/hardware_entry.py preflight `
      --config configs/hardware_runtime.<run>.json `
      --calibration <calibration.json> --map <map.json> `
      --pose-engine <yolo26s-pose.engine> `
      --pose-manifest <pose-manifest.json> `
      --safety-record <h0-safety.json> `
      --output experiments/runs/<run-id> --duration-s 60 `
      --report experiments/runs/<run-id>-preflight.json
    ```

    The command validates the URDF/Xacro hashes, calibration, map, ARM64
    TensorRT manifest, optional LSTM path, schedule and empty output paths;
    when motion is requested it also validates `--safety-record`. `record`
    repeats this validation immediately before device access.

13. `manual_map.py` is the no-ROS commissioning entrypoint for hand driving
the robot while the N10P LiDAR scans. It uses the C++ STM transport when the
shared library is available, integrates STM body-velocity telemetry into a
local pose, updates a 2-D occupancy grid from N10P scans, and saves
`map.json`, `map.pgm`, `map.yaml`, `lidar.csv`, `robot_state.csv`,
`control.csv`, `context.csv`, `events.csv` and a provenance manifest. The map
uses STM body-velocity telemetry as its prediction and applies a bounded
correlative scan-to-map correction when enough occupied cells and valid LiDAR
returns are available. This is local scan matching only: it has no pose graph,
global relocalisation, loop closure, or ROS map-server publication. The map
manifest and `map.json` metadata record matcher attempts, inliers and the last
accepted correction so a run can be audited before it is used for controller
experiments.

On the Jetson, after confirming the emergency-stop area is clear:

```bash
PYTHONPATH=src:app python3 -B app/backend/manual_map.py \
  --stm /dev/rai_controller --lidar /dev/rai_lidar \
  --stm-baud 115200 --lidar-baud 460800 \
  --output experiments/runs/manual-map-<run-id>
```

Use `w/s/a/d` or the arrow keys for forward/back/lateral motion, `q/e` for
rotation, `x` or space for a zero command, and Escape to finish and save. A
keyboard watchdog sends zero velocity after the configured timeout. The
default LiDAR mount is 0.10 m forward of the robot centre; override
`--lidar-x`, `--lidar-y` or `--lidar-yaw-deg` if the measured mount differs.
Run `--self-test` before a hardware session to validate the decoder and grid
writer without opening devices.

14. The operator runtime is the ROS 2 bringup under `src/`. On the Jetson,
    build and source the workspace, then run
    `ros2 launch turn_on_robot bringup.launch.py`; this starts the STM32,
    N10P, Astra-S, SLAM Toolbox and FastAPI/WebRTC bridge together. Run the
    Next.js dashboard in `app/web`. Motion is armed explicitly in the browser;
    hold a direction button (or
    use the keyboard controls) for forward, reverse, lateral and diagonal
    motion; release sends zero velocity. The emergency-stop button is always
    available. The dashboard reads telemetry and `/map` snapshots from the
    bridge over HTTP, sends velocity and CCA path goals through REST, and
    receives Astra-S frames through the bridge's WebRTC endpoint. There is no
    direct socket console or second camera service. The bridge watchdog sends a
    zero command when HTTP velocity refreshes stop.

15. `plan_map.py` converts a saved `map.json` plus `--start X Y --goal X Y` to
    a controller-ready JSON containing `global_path_xy`. It wraps the result
    in the existing `FixedGlobalLocalPath`; no CCA/NMPC formula is changed. If
    the source map already has `cca_nmpc` settings they are retained; otherwise
    pass `--cca-settings <settings.json>`. The output is consumed by the
    existing `record_hardware.py --controller cca_nmpc` command, which still
    requires its normal STM32, LSTM, `--allow-actuation` and H0 safety gates.

    Example (plan only; no device is opened):

    ```powershell
    python -B scripts/python/tools/plan_map.py `
      --map experiments/runs/<scan>/map.json `
      --start 0 0 --goal 2 1 `
      --output experiments/runs/<scan>/navigation-controller-map.json `
      --cca-settings configs/cca_nmpc-settings.json
    ```

The active workflow has ten primary entry points: `ctx_run.py`, `map_run.py`,
`det_eval.py`, `stm_experiment.py`, `hardware_entry.py`, `record_hardware.py`,
`plan_map.py`, `final_pack.py`, `analyze_run.py`, and `repo_check.py`; the two
preflight validators (`validate_web_cohort.py` and
`validate_hardware_entry.py`) are support gates, not research workloads.
Pre-reset timing, trajectory, synthetic-data, supervised-learning,
figure-generation, duplicate benchmark, and PR01 retrieval tools are not active
and are not evidence. New learning
must use the self-supervised LSTM score loop and the environment
score policy search described above; no legacy supervised checkpoint may enter an
active manifest.
