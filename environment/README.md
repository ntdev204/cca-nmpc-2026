# Environment capture

`toolchain.template.yaml` is copied to an experiment-specific immutable environment
manifest before any confirmatory run. Replace every `null` value with a measured value;
do not infer a GPU, driver, solver, clock mode, or software version.

At minimum, capture:

- operating system, CPU, RAM, GPU/accelerator, power mode, and clock policy;
- Python, MATLAB/solver, CUDA/cuDNN, compiler, and relevant package versions;
- exact dependency lock or container digest;
- Overleaf compiler only in the remote manuscript record, never as a local build result;
- Zotero version and export timestamp for bibliography provenance;
- timezone, locale, and wall-clock synchronization for timing studies.

One environment manifest may be reused only when its content hash and execution host are
unchanged. Target-device timing requires a target-device manifest; desktop timing is not
a proxy.
