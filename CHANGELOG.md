# Changelog

All notable changes to the research control plane are documented here. Experimental
measurements belong in registered manifests, not in this changelog.

## Unreleased

### Added

- Amended the physical control contract to the six-state position vector
  `[x,y,theta,vx,vy,omega]` with body-velocity commands; torque/current is not a
  hardware requirement. Added direct recorder/manifest state metadata, schema
  `1.3.0`, and linked Obsidian scope notes without editing the paper.
- Clean-slate Q1/SCIE reproducibility structure for CCA-NMPC + LSTM.
- Clarified that PR01 remains a hash-protected historical record only; the active
  literature condition is the focused Zotero/Obsidian audit and does not require
  SLR, PRISMA, or subscription-database accounts.
- Relabeled PR01 as an archived, non-execution phase in the protocol index and
  removed the obsolete test-documentation wording that treated PR01 verification
  as an active release gate.
- Synchronized the archived PR01 header and its historical hash chain, and added
  the non-gating literature-scope row to the internal completion audit.
- Added a regression test for direction-change-triggered local replanning; it
  verifies that the global path remains bytewise unchanged.
- Extended the Python map-runner measurement contract with path/progress,
  tracking, torque-variation, near-miss and fallback-duration fields; the prior
  pilot package is explicitly not retroactively promoted and must be regenerated
  before these metrics are used.
- Added a dated Google/Google-Scholar-oriented evaluation refresh for the HRI
  2026 human-motion-prediction study and a 2026 Mecanum traction benchmark;
  both tighten evaluation requirements without changing the narrow research gap.
- Added two further 2026 screening notes: LSTM-plus-TD3 navigation and
  multisensor crowd MPC with TIAGo validation. Both are linked in Obsidian as
  prior-art boundaries only; Zotero admission and independent review remain open.
- Added the 2026-08-13 search refresh for Mecanum actuator/model uncertainty,
  risk-aware social planning and hybrid Mecanum control. The three source notes
  are screening-only and strengthen benchmark/limitation requirements without
  expanding the novelty claim.
- Added the 2026-08-13 risk/benchmark refresh with SICNav interactive crowd MPC,
  cooperative GP-MPC and dynamic risk-aware MPPI. These remain screening-only
  Obsidian sources and strengthen the comparator boundary without changing the
  locked paper.
- Added the internal requirement-to-evidence completion audit and linked it from
  the Obsidian project map; it records missing gates without promoting any
  candidate result or unlocking the manuscript.
- Rechecked the ARMS primary landing page during the 2026-08-13 spot-check,
  recorded its arXiv DOI and provenance hash, and confirmed that the new search
  results were already covered by existing screening notes.
- Updated the STM host-test runner to remove its generated object/executable
  directory after every run; the host protocol test still passes and leaves no
  `src/stm/tests/build` artifact.
- Pruned unreachable Git objects after confirming the new repository has no
  project branch, commit, tag or remote history; only Codex checkpoint refs
  remain and `git fsck` reports no unreachable objects.
- Added a 2026-08-13 dataset discovery note covering Oxford-IHM, JRDB/JRDB-Pose,
  SiT, NavWareSet and uB-VisioGeoloc. They remain screening candidates; no raw
  dataset was downloaded, frozen or used for LSTM training, and the direct
  CSV/JSON plus no-ROS boundary is preserved.
- Confirmed from the Oxford-IHM primary page that its raw release is rosbag;
  it is now reference-only unless an authorized direct CSV/JSON export becomes
  available, consistent with the no-ROS/no-rosbag boundary.
- Regenerated a fresh bounded MATLAB development package after the reset;
  `matlab-bounded-20260813` is retained as candidate-only because the numerical
  gate is false, host NMPC timing misses the 50 ms deadline, and no hardware
  validation is present.
- Reran the bounded MATLAB profile with 16 SQP iterations and 3,000 function
  evaluations in isolated package `matlab-bounded-20260813-r2`; solver fallback
  was removed in the sampled rows, but settling/deadline gates remain false and
  the package is still candidate-only.
- Aligned the Python map benchmark NMPC deadline with the declared 100 ms map
  sample period; the previous 150 ms value violated the shared timing contract.
- Added `schemas/context-overlay.schema.json` for the existing current-context
  image overlay payload; it is context-only and does not authorize human
  future-trajectory fields.
- Made the overlay loader reject every unregistered field and added a regression
  test while preserving the explicit human-trajectory rejection path.
- Aligned the Obsidian system model and notation with the active causal LSTM
  interface: context velocity/direction only; mode, mean and covariance symbols
  remain compatibility notation and no human future path is generated.
- Removed the remaining proposal/PR02 wording that presented LSTM trajectory
  distribution as an active deliverable; extended mode notation is now marked
  explicitly as calibration-gated compatibility material.
- Renamed and narrowed the proposal framing to context risk allocation: the
  active LSTM interface supplies current speed/direction/validity only, while
  mode/covariance chance output remains an optional extension rather than an
  active human-trajectory deliverable.
- Added an optional causal `--lstm-checkpoint` path from the score-trained LSTM
  into CCA prediction rows; pilot manifests identify the direct adapter, while
  confirmatory execution now requires a hashed checkpoint.
- Added a fail-closed confirmatory provenance check to `ctx_run.py`: a frozen
  split is accepted only from a sealed direct CSV/JSON capture whose verified
  manifest declares a real capture source and whose `context.csv` hash matches.
  Pilot/diagnostic runs remain available without this gate; no synthetic data
  or checkpoint was created.
- Added the sealed capture-manifest hash and capture-source fields to any new
  LSTM checkpoint metadata; this improves provenance without changing the
  CCA--LSTM interface or training objective.
- Made confirmatory `map_run.py` reject an LSTM checkpoint without the sealed
  real-capture provenance hash, so a diagnostic checkpoint cannot silently
  enter the controller benchmark.
- Added a recurring Google/Google Scholar-oriented refresh rule: search before
  each gap/model/evidence change, at least weekly while active, and before freeze;
  four 2026 candidates are staged in a pending Zotero BibTeX queue without being
  admitted as verified nearest-work evidence.
- Strengthened the direct-run contract: sealed manifests record declared camera,
  LiDAR and firmware identity, while repository QA checks real-media integrity,
  blind-bbox binding and the absence of ROS/ROS 2 runtime dependencies.
- A machine-readable final robot-run package contract for state/control/context/events
  CSV files, map JSON/YAML, checksums and manifest provenance.
- Direct STM CAN-to-CSV mapping for the final recorder; the pose/state estimator
  boundary is explicit and no middleware log is required.
- Added an explicit capture-source and evidence-status boundary to the final
  package manifest; structural hash validation no longer implies real-hardware
  or scientific evidence.
- Corrected the Obsidian theory ledger so T6 is traced to its own proof and
  PO-011 invariant instead of being misattributed to the T5 chance-accounting claim.
- Recorded a second PR01 open-retrieval attempt that was stopped after a network
  hang; the incomplete candidate bundle remains isolated from canonical evidence.
- STM CAN/protocol host test passed; this is firmware QA only and does not promote
  the run to hardware evidence.
- Recorded that the current Python map candidate uses a direct context adapter,
  not a trained LSTM checkpoint; no CCA--LSTM claim is admitted from that run.
- Added a fail-closed context-LSTM checkpoint loader with strict schema,
  self-supervised-mode and state/config parity checks.
- Added the context-LSTM prediction-to-heading adapter; it emits only the
  current position/speed/direction snapshot and never constructs a human path.
- Audited the reset boundary: the model registry remains empty, no checkpoint or
  build binary remains outside backup, and YOLO26s-pose is isolated as a tool artifact.
- Re-ran the bounded MATLAB candidate after removing time-indexed human context;
  the superseded package was removed and the new package is explicitly
  candidate-development-only.
- Empty dataset, experiment, and artifact registries with strict JSON Schemas.
- Added a strict optional context overlay contract to `det_eval.py`; paired
  records and source/checkpoint hashes are required, while human trajectories
  and robot local paths are rejected on the image branch.
- Added a focused regression test that renders the current LSTM/context snapshot
  on a real-image-shaped frame without introducing trajectory or path geometry.
- Added a blinded person bounding-box annotation schema and optional IoU/TP--FP--FN/
  average-precision diagnostics to `det_eval.py`; image-level detector metrics
  remain candidate-only when no independent annotations are supplied.
- Added the first prediction-blind eight-image bbox annotation candidate and
  reran YOLO26s-pose as `det-eval-web-bbox-20260812-r8`; its box diagnostics are
  recorded as development-only until cohort expansion and independent review.
- Added a separate 128-image COCO128 public-benchmark development diagnostic
  with source-derived person boxes; it is registered as restricted/acquiring and
  explicitly excluded from confirmatory evidence because of train/validation
  reuse and possible pretraining overlap.
- Added an official COCO8-Pose source manifest and a real YOLO26s-pose validation
  diagnostic (`pose-val-coco8-dev-20260812`) with COCO-17 pose metrics, class
  confusion plots and qualitative mosaics; it remains candidate-only because
  the four-image validation split is a debugging cohort with possible
  pretraining overlap.
- Re-ran the fixed-budget proof-contract checks: Python risk properties 27/27
  and the full MATLAB unit/property suite 68/68; these remain implementation
  QA, not calibration, safety, stability or hardware evidence.
- Added constant-velocity and Kalman-velocity baselines to `ctx_run.py`; both
  use only observed history and are evaluated on the same chronological split
  as the self-supervised CCA-LSTM.
- Added independent temperature-scaling calibration to `ctx_run.py`: a frozen
  calibration partition is fit only after checkpoint selection, while test-ID
  and test-OOD remain evaluation-only; chronological runs fail closed to an
  explicit `not_fit` status.
- Made the LSTM checkpoint loader apply the recorded temperature to direction
  confidence and reject calibration metadata sourced from either test partition.
- Hardened `analyze_run.py` against duplicate checksum records, payload/manifest
  omissions, map-hash drift and missing camera/LiDAR/firmware identity.
- Added paired-campaign validation to `map_run.py`; every replicate/scenario must
  contain all five controllers, the global path must remain fixed, and forbidden
  human-trajectory fields are rejected before aggregate metrics are written.
- Added deterministic paired bootstrap 95% intervals for map collision,
  completion, goal-error and P95 compute-time summaries, with explicit
  descriptive-only provenance.
- Added paired effect-size intervals versus CCA-NMPC for every registered
  baseline, with a fixed positive-favors-reference sign convention.
- Added image-level bootstrap 95% CI for detector presence and blind-bbox
  precision/recall/F1, with fixed seed and descriptive-only provenance.
- Added a fail-closed minimum-support gate requiring 30 valid windows in each
  LSTM calibration, test-ID and test-OOD partition before confirmatory metrics
  can be produced.
- Added a frozen group-split mode to `ctx_run.py`; recording/episode assignments
  now support disjoint train, validation, calibration, test-ID and test-OOD
  windows without allowing a group to cross partitions.
- Added `context-split-manifest.schema.json` for the frozen group assignments
  consumed by the confirmatory LSTM split mode.
- Added explicit controller-definition metadata to the Python map benchmark so
  MPC, NMPC, DWA, MPPI and CCA-NMPC cannot be reported as unlabeled aliases.
- Added pilot/confirmatory campaign separation to `map_run.py`; confirmatory
  runs require the predeclared 30 paired replicates and disable score tuning.
- Confirmatory map manifests now carry a distinct unreleased status and campaign
  field, preventing pilot-development status from being reused for a future
  confirmatory package.
- The LSTM split loader now validates the JSON Schema directly and rejects
  unknown fields before any training window is constructed.
- Confirmatory map execution now fails closed without a valid frozen PR20/PR21
  manifest; the current focused audit therefore cannot be bypassed by a CLI flag.
- Shared context readers now reject future-position, trajectory, and path fields
  in CSV packages and image overlays, including variant field names.
- Added direction reliability bins, ECE, Brier/NLL and deterministic bootstrap
  intervals to `ctx_run.py`; the manifest explicitly records that its current
  chronological single-run split is not an independent ID/OOD holdout.
- Corrected detector box-metric threshold semantics and added image-level and
  box confidence sweeps; the canonical rerun is
  `det-eval-web-bbox-20260812-r8`, while earlier threshold-inconsistent runs
  are superseded.
- Re-ran the 8-image Internet cohort with the context-overlay contract and
  removed the superseded duplicate detector package; the new run remains
  `candidate-not-evidence` and detector-only because no paired temporal context
  was available.
- Removed generated `__pycache__`, `.ruff_cache` and empty temporary output
  directories after QA; no generated build artifact remains in the active tree.
- Logged the PR01 connectivity audit: public endpoints were reachable, but a
  repeated Crossref ranked-cap request was throttled (HTTP 429); no canonical
  export or screening decision was changed.
- Refreshed the focused literature audit with Google/web primary-source checks
  for Mecanum dynamics, SFM-NMPC benchmarking, multi-sensor MPC with TIAGo
  experiments, and implicit social-cue learning; four Obsidian source notes
  record evidence levels and unresolved venue/Zotero boundaries.
- Removed superseded duplicate detector packages `det-eval-web-bbox-20260812-r5`,
  `r6` and `r7` from the active run directory after the reproducible canonical
  rerun `det-eval-web-bbox-20260812-r8`; their provenance is retained outside
  the active workspace only for audit recovery.
- Scope decision D-018: the active paper uses a focused Zotero/Obsidian
  literature audit, not a systematic literature review; frozen PR01 artifacts
  remain historical and are removed from the active work plan.
- Reconciled the active literature notes and Zotero queue with D-018: PR01/SLR
  language is now explicitly historical, while focused source-note and
  nearest-work checks remain the live research task; the historical decision
  record hash was updated only to match the current matrix text.
- Migrated active confirmatory contracts from the historical PR01 machine gate
  to a hashed focused-literature-audit record; PR01 schemas remain available
  only for provenance and no database-account export is required.
- Bumped `protocol-freeze-manifest.schema.json` to `1.3.0`; a frozen
  confirmatory protocol now requires the focused literature audit to be
  `COMPLETE`, while development templates may remain `IN_PROGRESS`.
- Bumped `focused-literature-audit.schema.json` to `1.1.0` and bound the
  evidence record to the hashed Obsidian research-gap note.
- Re-synchronized the historical PR01 decision record with the current
  nearest-work matrix hash so repository integrity checks remain consistent;
  this does not promote PR01 or open a confirmatory gate.
- Templates for environment capture, dataset design, evaluation, and simulation.
- Draft 2020-12 schemas for dataset, simulation, evaluation, physical-experiment,
  PR01-decision and real-frame trajectory-overlay configurations.
- Explicit Overleaf, Zotero, Obsidian, data-provenance, and immutable-backup policies.
- Read-only repository contract validation with strict JSON parsing, JSON Schema and
  YAML-instance checks, file-hash verification, Obsidian integrity checks, and an
  explicit fail-closed focused-audit preflight for confirmatory work; PR01 remains
  provenance-only.
- Curated 32 DOI-normalized Zotero items with one PDF attachment each and added a
  portable 32-entry BibTeX export plus a hash/count verification receipt.
- Recorded the current Zotero organization state explicitly: 32 items/32 PDFs,
  zero collections, read-only local-API inspection, and incomplete tag organization.

### Changed

- Removed the archived PR01 retrieval/promotion runner and their dedicated test
  modules from the active Python tree; PR01 manifests and schemas remain only as
  historical provenance, while the focused Zotero/Obsidian audit is the sole
  active literature workflow.
- Re-ran the MATLAB unit/property suite after the cleanup: 68 passed, 0 failed,
  0 incomplete; no long simulation campaign was started.
- Removed the unused trajectory dataset, multimodal-LSTM, prediction-adapter,
  and snapshot modules from `src/python`; the active code now exposes only
  perception, context, tracking, and map-control interfaces.
- Reframed the active LSTM contract as context-only (position, speed and direction),
  removed active human-trajectory overlay schemas, and retained the global-path-fixed
  robot local-path semantics in the map benchmark.
- Removed the MATLAB time-indexed human-position trajectory from the active scenario
  result; MATLAB now keeps static context positions and direction/speed alternatives.
- Declared prior datasets, models, simulations, and experiments ineligible as evidence
  for the redesigned study.
- Separated versioned metadata from ignored data, model, run, artifact, and paper payloads.
- Bumped the claim-to-evidence contract to schema version `2.0.0` and the
  protocol-freeze contract to `1.1.0`; `CLM-EMP-*` is now a first-class empirical
  claim namespace, while theory admission requires pinned assumptions, proof
  obligations and verified evidence.
- Canonicalized theory references as `A-NN` and proof obligations as `PO-NNN`
  across PR02 and the Obsidian theory ledger without reusing an identifier for two
  different meanings.
- Bumped dataset/model registries and Internet-media/trajectory-overlay contracts to
  `2.0.0`. Frozen person-detection tests now require licensed, audited real Internet
  media; frozen LSTM ID/OOD tests require real trajectories, retained frame/video hashes
  and a verified metric image-to-local transform.
- Bumped experiment, run and artifact contracts to `1.1.0`. Confirmatory execution now
  requires a hashed focused-literature-audit record and protocol freeze; all completed/failed
  runs retain scientific outcomes; physical work requires staged ethics/consent/safety
  and target-hardware evidence.
- Locked the six-strategy primary controller contrast (plain, uniform, optimized
  non-context, feasibility heuristic, learned fixed-budget and CCA fixed-budget) under
  common clearance, dynamics, constraints, reference, solver, tuning and paired seeds.
- Restricted confusion matrices to preregistered classification tasks with true class
  semantics; bounding-box detection and trajectory regression use their valid metrics.
- Removed the synthetic LSTM example and future human-path overlay from the active
  workflow. Internet-image perception now reports current context only; robot local
  paths remain artifacts of the Python map branch.
- Added the versioned `trajectory-overlay-render-config` 2.0.0 contract for frozen
  renderer inputs, separate from the generated/accepted overlay evidence manifest.
- Hardened real-frame overlay evidence with runtime JSON-Schema enforcement, UTC and ID
  checks, preregistered selection witnesses, five mandatory strata, optional-failure
  availability gates, portable all-parent hashes, protected inputs, and atomic output
  staging. Accepted manifests now retain audited image/local data and require independent
  schema, semantic, cross-link, reprojection, hash, and visual review. The renderer now
  independently validates all nine linked JSON roles and recomputes homography projection
  and Jacobian covariance before rendering; the deterministic cross-link report and
  figures are committed together through atomic staging after rendering succeeds.
- Reframed T1--T5 as elementary contract propositions rather than theoretical
  novelty; separated model-internal Gaussian/mixture bounds from empirically
  calibrated operational probability, including mode-partition, one-solve,
  zero-variance, geometry-containment and fail-closed evidence requirements.
- Withdrew/held analytic recursive-feasibility and stability claims for the current
  controller until actuator lag/delay/previous torque, bounded disturbance and
  terminal ingredients are represented and verified; retained empirical
  solve/fallback/tracking characterization under the provisional empirical pivot.
- Kept the archival paper snapshot under `backup/` and locked the active Overleaf
  manuscript during the clean research rebuild; no local manuscript build is part
  of the active workflow.
- Bound all 32 Zotero import PDFs by SHA-256, tracked the source manifest, marked 27
  inherited files with unresolved download origin instead of fabricating provenance,
  and added the hashed Zotero receipt directly to PR01 decision schema `1.1.0`. The
  receipt now also has a strict `1.1.0` JSON Schema plus cross-file hash/count checks.
- Froze PR01 search manifest `1.2.0` with a 2010--2026 window, five retained
  databases, six concept blocks and 30 database-specific queries. A pre-execution
  amendment records unavailable Scopus/WoS collection access and makes IEEE Xplore,
  Crossref and Semantic Scholar the three executable mandatory sources. Added a
  separate raw-export manifest `1.1.0` and database-specific completion semantics:
  a declared top-1000 relevance cap for Crossref, token exhaustion for Semantic
  Scholar and complete platform exports for UI sources. PR01 decision contract
  `1.2.0` binds both manifests. The raw status remains `IN-PROGRESS`: IEEE
  Xplore export is missing, WoS/Scopus are access-blocked, and the 2026-08-12
  public IEEE query displayed 227 unfiltered records but its export dialog
  required personal sign-in; the open-retrieval attempt produced only an
  incomplete candidate bundle. Version 3
  also freezes the Semantic Scholar screening-metadata projection and records
  the promotion validator/tooling. No candidate count is a PRISMA flow count or
  novelty evidence.
- Fixed direct execution of the six active Python entry points with one shared
  repository-path bootstrap; `--help`, Ruff, the Python suite, and
  `repo_check.py` pass. This is a tooling reproducibility fix only and does
  not promote any development run to scientific evidence.
- Re-ran the bounded Python map pilot with the path/tracking/torque/near-miss
  metric contract and retained the package as development-only; it uses the
  direct context adapter, score tuning, and no frozen LSTM checkpoint.
- Added a dated official Ultralytics YOLO26-pose documentation note to the
  focused Obsidian audit; 17-keypoint pose output is recorded as a perception
  interface only, with no detector, latency, or control novelty claim.
- Purged legacy COCO128/COCO8-Pose payloads, superseded detector/map/MATLAB
  run directories, and the empty generated `runs/` tree. Historical manifests
  remain metadata-only; the active payloads are the refreshed Internet-image
  diagnostic (`det-eval-web-bbox-20260812-r11`) and the new metric-contract
  map pilot.
