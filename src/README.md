# Python Continuous CCA-NMPC research stack

The Python package implements control-centered simulation, prediction-interface
validation, and closed-loop benchmark tooling. Generated evidence is kept separate
from the manuscript, which is authored and built only on Overleaf.

## Active context-to-control chain

```text
real image / pose measurement
  -> position, speed and direction context
  -> score-trained LSTM context-velocity head
  -> Continuous Context-Aware relevance
  -> fixed-budget chance-risk allocation
  -> position-state CCA-NMPC with body-velocity command
  -> Python Mecanum map and robot local path
```

The image branch describes the person's current context: an image-plane
position proxy, observed speed, and a discrete direction (left, right,
forward, or backward). The person is dynamic in the map scenarios. Only
CCA-NMPC may propagate the causal context velocity into an internal future
position sequence for its chance rows; that sequence is neither stored in the
image branch nor drawn on a camera overlay. Robot motion is evaluated
independently on a Python-built map.
The global path is planned once; a local path is regenerated only after a
dynamic-context conflict or a direction change. An invalid context snapshot
invokes the controller's bounded safe response.

## Package map

- `ai/`: context features, the direction/speed LSTM, context scorer,
  calibration, perception, fusion, tracking, and compact inference contracts.
- `simulation/`: Mecanum map geometry (the active map binds its footprint to the
  full `rai_robot_urdf` mesh-and-mount intake), dynamic context footprints,
  trigger-only local-path generation, and the `NmpcPrediction` contract. The
  compiled controller in `control/` is the only controller implementation;
  Python map code only prepares inputs and records outputs.
- `repository.py`: repository, evidence, and web-image contract validation.
- `tests/python/tests/`: regression tests are kept outside the runtime source
  tree; context/path, A* and CSV checks share compact test modules.
- `scripts/python/tools/ctx_run.py`: self-supervised CCA-LSTM training and
  evaluation from a real robot `context.csv`, with constant-velocity and
  Kalman-velocity baselines on the same split; direction labels are diagnostic
  only; CCA's internal future-position sequence is runtime-only and is not
  exported as a human trajectory.
- `scripts/python/tools/map_run.py`: Python map benchmark with a
  bounded environment-score search for local-path parameters, a fixed global
  path and trigger-only local-path updates.
- `scripts/python/tools/det_eval.py`: real Internet-image detector evaluation
  with image-level confusion matrix, latency diagnostics, overlays, and
  manifest. The optional `--annotations` input adds candidate blind-annotation
  IoU/TP--FP--FN/AP diagnostics; without it, no box metric is reported. The
  optional `--context` input displays a provenance-checked LSTM
  context snapshot (position, speed, direction, confidence and validity) only;
  it never draws a human trajectory or robot local path.
- `scripts/python/tools/repo_check.py`: read-only repository contract check.
- `scripts/python/tools/final_pack.py`: validates and seals a direct CSV/JSON
  robot-run package without a middleware runtime.
- `scripts/python/tools/record_hardware.py`: records Astra-S/OpenNI2 frames,
  N10P serial packets and either the STM32 serial telemetry
  bridge or CCA CAN telemetry into direct CSV/JSON files; it requires measured
  robot dimensions, calibration and a validated YOLO26s-pose TensorRT engine
  before opening devices. A score-trained LSTM checkpoint is optional for the
  initial context-only capture and required only when LSTM context is enabled.
  The STM32 path reproduces the bridge's 11-byte body-velocity command and
  24-byte telemetry frames. Nonzero commands require a monotonic command CSV
  plus explicit `--allow-actuation`; otherwise only zero velocity is sent.
  URDF/xacro files remain source-hash and mount/protocol references; they do
  not supply physical dimensions. Geometry must carry
  `geometry_authority=measured_physical_spec` from a separate physical-spec
  record.
  The physical configuration must also declare the measured N10P protocol
  profile (`n10p-108b-v1`); no packet layout is selected implicitly.
  The recorder uses the frozen 0.1 s context period and rejects unaligned
  color/depth streams or excessive color/depth device-timestamp skew. It keeps
  host receive time as canonical `t_ns` and records the optional device time in
  `camera_device_t_ns`. CAN command-frame encoders in `shared.py` select
  the C++ codec on Linux when `libcontrol_transport` is present and retain a
  tested Python fallback; both paths are parity-tested against the STM
  contract. The five-feature context scorer in `ai.context` uses the same
  shared library through `cca_context_score` on Linux; set
  `CCA_CONTEXT_BACKEND=python` only for an explicit compatibility fallback.
  This
  direct mode never exports or draws a human trajectory; CCA's internal
  prediction is not a recorder artifact. Actuation is explicit and
  fail-closed.
  Context speeds above the frozen `max_speed_mps=2.0` bound are treated as OOD;
  map pilots fall back to the current observation, while confirmatory/online
  CCA additionally requires an independently fitted calibration record.
  The physical state record is `[x,y,theta,vx,vy,omega]`; no torque/current
  channel is required. Every saved camera frame carries a context overlay. The
  overlay labels the LSTM state as `disabled`, `active`, `warmup`, or `invalid`,
  so checkpoint-free capture and startup frames are not misreported as LSTM
  predictions; no human future trajectory or robot local path is drawn.
- `src/control/build/stm_probe`: preferred low-level STM32 serial bring-up executable;
  the C++ core owns the 11-byte command and 24-byte telemetry frame. The
  Python `stm_experiment.py` path remains an offline-compatible recorder for
  hosts where the C++ target is not built, but it is not the preferred
  low-level transport on Jetson/Raspberry Pi.
- `hardware.Stm32SerialSource`: selects the C++ shared transport
  (`libcontrol_transport.so`/platform equivalent) automatically when it is
  built; `CCA_STM_BACKEND=python` is an explicit compatibility fallback.
- `scripts/python/tools/analyze_run.py`: computes provenance-linked analysis
  from a sealed package without modifying the raw data.
- The active tool directory contains the active direct-run entry points. Legacy detector export,
  retrieval, simulation, generation and figure commands are not active and are
  excluded from evidence.
- Pre-reset trajectory, timing, synthetic-data and supervised-learning modules were
  removed from the active workspace; they are not active entry points or evidence.
## Output boundary

- Run manifests, traces, and provisional metrics belong under `experiments/runs/`.
- Generated evidence figures and immutable export payloads belong under
  `artifacts/payload/`.
- Model checkpoints are run artifacts; a checkpoint is not accepted evidence until
  its frozen dataset, configuration, evaluation report, and hashes are registered.
- No Python tool writes manuscript source, manuscript macros, or local paper builds.
- The physical-run deliverable is a clean folder containing `robot_state.csv`,
  `control.csv`, `context.csv`, `lidar.csv`, `events.csv`, `map.json`, `manifest.json`, and
  `checksums.sha256`. No replay file is required. The sealed manifest records
  the capture source and keeps structural integrity separate from scientific
  evidence status.

## Context LSTM from final-run data

The active person-frame entry point is explicit and context-only:

```powershell
python -B scripts/python/tools/ctx_run.py `
  --input final-run-<UTC> `
  --output experiments/runs/context-lstm-<UTC>
```

The runner uses the position and validity fields in `context.csv` to form
self-supervised next-velocity windows. With a frozen five-way split it fits one
temperature on the independent calibration partition; without that split it
records `status=not_fit`. It writes calibration provenance, direction
reliability diagnostics (ECE, Brier and NLL), bootstrap intervals, and a
manifest; the chronological split is not a substitute for an independent Q1
holdout. Confirmatory five-way execution additionally requires the input to be a
sealed direct CSV/JSON package with a verified manifest, real capture source and
matching `context.csv` hash; synthetic or unsealed input is rejected. Image-level
person detection remains the separate `det_eval.py` workflow.

```powershell
python -m ruff check src
python -B -m pytest -s -p no:cacheprovider -q tests/python/tests
```

## Evidence boundary

Legacy code paths support synthetic simulation and recorded-host software timing
only. They do not establish camera performance, real-human prediction, HIL,
physical-robot safety, or hard real-time execution. YOLO remains a measurement
interface, not the control contribution.
