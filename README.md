# CCA--NMPC + LSTM research workspace

This repository is the clean control plane for the redesigned Q1/SCIE study.
It contains source code, schemas, protocols, provenance metadata, tests, and a
linked Obsidian vault. It does not contain legacy datasets, checkpoints, or
accepted result tables. Development run payloads, when present, are explicitly
unregistered and cannot support manuscript claims.

## Scientific boundary

- CCA--NMPC is the control contribution.
- The physical control contract is the six-state position/velocity vector
  `[x,y,theta,vx,vy,omega]` with body-velocity commands; torque/current control
  is not required.
- LSTM supplies context features (position, speed, and coarse direction).
- YOLO26s-pose is a perception interface, not the novelty claim.
- The global path is fixed; only a conflict-triggered local path is regenerated.
- New evidence must compare the declared controller baselines and preserve failed
  runs, metrics, provenance, and uncertainty.
- The active position-state CCA branch is a compiled C++ bounded candidate
  rollout with validated geometry, reduced context-risk correction, command
  clipping and six-state propagation. The reserved risk-slack field is
  bookkeeping only; no nonlinear-program residual, optimized slack or chance
  feasibility certificate is exposed by the current executable.

## Source-of-truth boundary

Overleaf is the only manuscript authoring/build environment. Zotero is the
reference source. Obsidian is the linked research notebook. The only retained
local paper snapshot is `backup/paper-current-2026-08-01/` and it is not evidence
for the redesigned study.

The paper uses a focused primary-source literature audit in Zotero/Obsidian;
PR01/SLR, PRISMA flow counts, and Scopus/Web of Science/IEEE Xplore export access
are not active requirements for this original research paper. Historical PR01
metadata is retained only for provenance.

## Clean-reset layout

- `src/`: active perception, simulation support, C++ control runtime, and embedded source.
- `matlab/`: offline MATLAB research scripts kept outside the runtime source tree.
- `reference/robot/`: read-only URDF/sensor/legacy-serial snapshot used for
  hashes and geometry intake; it is not a ROS runtime.
- `configs/`, `schemas/`: frozen contracts and validation rules.
- `data/`, `models/`, `artifacts/`, and `experiments/`: tracked registries are
  empty after the 2026-08-14 clean reset. Ignored candidate outputs may remain
  on the local research workstation, but they are not evidence, are not part
  of the GitHub deployment snapshot, and cannot be promoted without a new
  protocol freeze and run ID.
- `research/obsidian/`: linked research knowledge graph, starting at
  `[[00_MOC/project-map]]`.
- `references/zotero/`: citation exports and Zotero provenance.
- `tests/`, `scripts/`: quality gates and reproducibility tooling.

## Evidence rule

No scientific entry is accepted yet. A dataset/model/experiment/artifact may be
promoted only after its manifest, hashes, protocol, and decision link pass the
corresponding schema. No legacy number or figure may be reused.

## Direct no-ROS hardware entry

The staged no-ROS hardware path starts with the C++ `stm_probe` executable in
`src/control`, which owns the legacy STM32 serial contract from the
`reference/robot` source snapshot
bridge and records direct telemetry. The Python
`scripts/python/tools/stm_experiment.py` path remains an explicit compatibility
fallback. The full
operator entrypoint is `scripts/python/tools/hardware_entry.py`; it reads the
complete `rai_robot_urdf` package before capture, catalogues all package
models, records the mini-Mecanum wheels/body and Astra-S/N10P sensor mounts by
hash, and keeps the mesh-and-mount footprint as CAD reference metadata. A
runtime config receives physical dimensions only from a separate measured
`cca-physical-robot-v1` file. No ROS process is started.

Build the C++ transport on Jetson/Raspberry Pi before commissioning:

```bash
cmake -S src/control -B src/control/build -DCMAKE_BUILD_TYPE=Release
cmake --build src/control/build -j2
ctest --test-dir src/control/build --output-on-failure
```

`hardware.Stm32SerialSource` automatically selects the resulting shared
library on Linux. The same library supplies the fixed-width CCA CAN codec
through `shared.py`; set `CCA_STM_BACKEND=python` or
`CCA_CAN_BACKEND=python` only for an explicit compatibility fallback.

```bash
export PYTHONPATH=src:scripts/python
python3 -B scripts/python/tools/hardware_entry.py inspect \
  --output research/metadata/hardware/mini_mec_intake_<UTC>.json
python3 -B scripts/python/tools/hardware_entry.py prepare \
  --output configs/hardware_runtime.<run>.json \
  --stm-port /dev/rai_controller --lidar-port /dev/rai_lidar \
  --lidar-baud <measured-N10P-baud> --firmware <STM32-firmware-id> \
  --physical-spec configs/physical_robot.<run>.json
python3 -B scripts/python/tools/hardware_entry.py schedule \
  --output experiments/commands/<run>.csv --kind forward \
  --duration-s 5 --step-s 0.1 --speed-mps 0.05
```

First run the STM recorder in `observe` mode to verify serial telemetry. Before
any nonzero command, H0 must verify emergency stop, remote disable and watchdog;
the STM recorder then requires `--allow-actuation` and `--safety-record`.
Before the full sensor stack is connected, run `hardware_entry.py preflight` with
the config, calibration, map, Jetson TensorRT manifest and planned output
directory. It performs the same provenance and input checks as `record` without
opening any device or creating a run. For motion, pass a validated
`--safety-record` as well as `--confirm-motion`; the record must verify approval,
emergency stop, remote disable and watchdog.

After H0 approval and calibration, use `hardware_entry.py record` with the
map, YOLO26s-pose TensorRT engine/manifest and optional LSTM checkpoint. The
wrapper requires both `--confirm-motion` and `--safety-record` before nonzero
actuation; without either the capture remains zero-velocity. For a moving-person final trial use
`--controller cca_nmpc` and omit `--command-csv`.

## Final robot data

For a final physical run, keep only the data package below; no replay file is
required:

```text
final-run-<UTC>/
  robot_state.csv
  control.csv
  context.csv
  lidar.csv
  events.csv
  map.json
  calibration.json
  manifest.json
  checksums.sha256
```

After the robot is stopped safely, validate and seal the folder once:

```powershell
$env:PYTHONPATH = 'src;scripts/python'
python -B scripts/python/tools/final_pack.py `
  --input final-run-<UTC> `
  --run-id final-run-<UTC> `
  --robot mecanum `
  --controller cca_nmpc `
  --clock robot_time `
  --camera "Astra-S" `
  --lidar "N10P" `
  --firmware "<STM32-firmware-id>" `
  --control-interface body_velocity `
  --capture-source hardware
```

The tool performs only schema/monotonic-time/hash checks and writes the
manifest; it does not run MATLAB or replay the robot.

To derive a separate machine-readable analysis without modifying the raw package:

```powershell
python -B scripts/python/tools/analyze_run.py `
  --input final-run-<UTC> `
  --output experiments/analyses/final-run-<UTC>
```

The analysis remains candidate until independent ground truth, protocol QA and
review are complete; raw CSV/JSON files stay outside Obsidian.
