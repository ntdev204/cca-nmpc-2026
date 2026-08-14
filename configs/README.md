# Configuration policy

Configuration is frozen before data inspection or confirmatory execution. Templates use
`null` for decisions that have not yet been justified; a `null` acceptance threshold or
sample size blocks the run rather than being filled after results are visible.

- `project.yaml` records the stable scientific and evidence boundary.
- `dataset.template.yaml` captures acquisition, provenance, split, and leakage decisions
  for person context (position, speed, and direction); it does not authorize a human
  trajectory output.
- `evaluation.template.yaml` defines Q1-level quantitative, qualitative, statistical,
  confusion-matrix, and visualization requirements.
- `simulation.template.yaml` defines paired scenarios, baselines, ablations, timing, and
  failure reporting without changing the CCA-NMPC + LSTM research identity.
- `physical_experiment.template.yaml` defines staged ethics, consent, safety, stopping,
  target-hardware and ground-truth gates for robot experiments.
- `hardware_runtime.template.json` is the direct device recorder template for
  Astra-S, N10P and the STM32 serial bridge (CCA CAN remains an optional
  transport). It declares the six-state position contract and keeps all
  physical geometry unresolved until measurement; a template copy cannot open
  a device or count as a run.
- `physical_robot.template.json` defines the accepted input shape for measured
  wheel geometry, footprint and sensor mounts. The current user-supplied
  record is `physical_robot.json`; it records the 400 mm by 400 mm envelope,
  50 mm interpreted wheel radius, 240/200 mm sensor heights, front-edge
  offsets of 100/35 mm (LiDAR/camera), and 20 degree downward camera pitch in
  SI units. Independent dimensional/calibration
  verification is still required before actuation. URDF/xacro files under
  `reference/robot` are CAD and mount/protocol references only; they are never
  promoted to physical dimensions automatically.
- `study_contract.json` is the small cross-language contract read by the active Python
  runners and MATLAB defaults. It owns shared direction order, timing, score targets,
  controller names, primary metrics, and paper-edit boundaries; backend-specific plant
  parameters remain in their native implementation. For the Python map benchmark,
  `pilot_replicates` is the development default and `confirmatory_replicates` is the
  minimum paired count for a confirmatory campaign. The latter must run with score
  tuning disabled; the two counts are intentionally separate so a five-run pilot
  cannot be mistaken for the confirmatory sample.

Copy a template to a uniquely named, versioned configuration; never overwrite the frozen
configuration of an existing experiment. Machine-local overrides match `local*.yaml` and
are intentionally ignored.

`dataset.template.yaml` is validated by `schemas/dataset-config.schema.json` version
2.0.0. Internet images remain mandatory for person-detection testing, while context
sequences must preserve real-frame provenance and a verified camera-to-local transform.

The simulation, evaluation and physical-experiment templates validate against their
same-named schemas under `schemas/`. The physical-experiment template also freezes
the final CSV/map package contract before a robot run. The active scope uses a
focused Zotero/Obsidian literature audit; the archived PR01/SLR export is not a
scientific prerequisite for code, simulation or hardware work. An immutable
protocol-freeze record remains required before confirmatory execution.
