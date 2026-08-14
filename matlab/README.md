# MATLAB — Continuous Context-Aware NMPC mathematical proof

`CCA` is defined as **Continuous Context-Aware**. The MATLAB controller uses
the six-state EKF estimate, not plant truth, as the NMPC initial condition.

MATLAB is a simulation gate. Historical pass statements are not current evidence;
all redesigned runs must be registered with a frozen configuration and regenerated
under the new repository provenance before they may support a claim.

## Entry points

```matlab
cd matlab
run_tests
run_studies
```

`run_studies` also executes the position-state comparison by default. The
active physical contract is `state=[x,y,theta,vx,vy,omega]` with
`command=[vx_cmd,vy_cmd,wz_cmd]`; the position-only results are under
`results.positionState`. The default entry point does not execute the older
wheel-input studies. Those regression-compatibility studies are available only
with `IncludeCompatibilityStudies=true` and are not physical evidence.

For a bounded position-state development artifact, use the explicit pilot profile:

```matlab
run_studies(Profile="bounded", ExportResults=true, ...
    OutputDirectory="../../experiments/runs/matlab-bounded-<UTC>")
```

The bounded profile shortens the horizon of the campaign and solver budget and
exports a position-state CSV/JSON package marked `candidate-development-only`;
it cannot satisfy the full Gate-A export. The default `Profile="full"` keeps
the confirmatory settings. Position-state export does not invoke compatibility
torque studies; the legacy Gate-A exporter remains available only when
`IncludeCompatibilityStudies=true`.

The active implementation is only `+cca`. The tracked legacy `+rbcca` code
has been removed; no active source may depend on it.

## Active classes

- `+cca/defaults.m`, `+cca/score.m`: configuration and context score;
- `+cca/Model.m`, `+cca/Estimator.m`, `+cca/Plant.m`: model, EKF and plant;
- `+cca/Risk.m`, `+cca/Safety.m`, `+cca/Scenario.m`: risk, safety and static
  context snapshots;
- `+cca/ControlPrimitives.m`, `+cca/Controllers.m`, `+cca/Nmpc.m`,
  `+cca/Simulation.m`: control and simulation core;
- `+cca/StudyRunner.m`, `+cca/StudyMetrics.m`, `+cca/StudyIO.m`:
  reproducible studies, summaries and exports;
- `+cca/AnalysisTools.m`: open-loop, stability and response evidence.

The active tree intentionally keeps one class per responsibility group. The
former multi-folder function packages are recoverable under `backup/` and are
not on the active source path.

Numerical plant parameters tagged `SIMULATION_NOMINAL` are not hardware
measurements. Geometry currently comes from STM `Car_Mode 0/1`; the active
physical profile must be confirmed on the robot before HIL.

The position-state study labels MPC, NMPC, DWA, MPPI and CCA-NMPC share the
same body-velocity interface. The MATLAB entry is a bounded contract/parity
smoke, not the primary comparative evidence: the distinct controller
implementations and matched map benchmark are in
`scripts/python/tools/map_run.py`. Legacy torque-oriented foundation routines
are kept only for regression compatibility; they are not the active hardware
control contract.

Scenario studies keep context position fixed over an episode and expose only
current speed/direction alternatives to the chance rows. They do not generate
or store a future human trajectory; robot local-path regeneration belongs to
the Python map branch.

## Output hygiene

By default, `run_studies(ExportResults=true)` writes a unique position-state
payload under `experiments/runs/matlab_<profile>_<UTC>/`. It contains one summary
CSV, one six-state/body-velocity CSV per controller/scenario pair and a hashed
manifest. These are experimental artifacts, never manuscript files. Debug or
candidate data must use a versioned run directory and must not be committed.

The manifest records source, configuration, and artifact hashes, Git state,
MATLAB/toolbox versions, and the explicit `realTimeReady=false` and
`hardwareValidated=false` limits. It has no manuscript hash or build contract.
