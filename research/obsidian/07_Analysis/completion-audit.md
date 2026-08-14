---
type: completion-audit
status: active
evidence_status: knowledge-only
paper_edit: prohibited
---

# Completion audit — research rebuild

This note is the internal source-of-truth for the current gap between the
requested Q1 research package and the evidence that is actually admissible. It
does not promote candidate outputs into paper claims and it does not unlock the
Overleaf manuscript.

## Requirement-to-evidence map

| Requirement | Current evidence | Status | Next admissible gate |
|---|---|---|---|
| Remove legacy datasets, models, and results | The 2026-08-14 clean reset physically purged the superseded media, manifests, NavWareSet payloads, weights, detector outputs and development map runs; the post-reset seven-image cohort and fresh simulation packages are explicitly retained as candidate-only outputs; all four registries remain empty | `verified-policy; current candidates not admitted` | Acquire only under a new protocol freeze and run ID |
| Reset Git provenance | The new repository has branch `codex/repository-bootstrap` but no project commit, tag or remote; unreachable objects were pruned and only the new staged snapshot remains | `verified-policy` | Create a project commit only after the first reviewed research snapshot |
| Literature protocol scope | PR01-SLR is explicitly archived and not an active gate; the current paper uses a bounded focused Zotero/Obsidian audit and does not claim PRISMA or subscription-database coverage. The 2026-08-13 bounded review records the gap limits, nearest-work links and comparator obligations; Scholar spot-checks remain discovery-only | `verified-policy` | Freeze the reviewed scope with version/SHA-256 before confirmatory holdout; final citation attachment reconciliation remains separate |
| Preserve one paper backup and lock local manuscript | `backup/paper-current-2026-08-01/` hash audit 12/12; Overleaf/local paper boundary recorded | `verified-policy` | Edit only in Overleaf after evidence is admitted |
| Narrow, current research gap | Nearest-work matrix and 2026-08-12/13 web refreshes, including HRI/control, SHARP CVaR/Bonferroni and context-preference boundary passes; Zotero API is reachable with 43 items, SICNav has a matched full-text audit, and Stefanini et al. (item `8T4BRJA4`) is re-matched with a dated refresh note while the existing NW-01 full-text extraction is retained; GP-MPC, MPPI, ARMS, RCSP and emergency-protection candidates are explicitly screening-only; bounded review is recorded in [[07_Analysis/focused-audit-review-20260813]] | `reviewed-bounded` | Freeze the reviewed scope with version/SHA-256 before confirmatory holdout; reconcile attachments before final manuscript citation |
| CCA–LSTM–NMPC mathematical model | `[[05_Theory/system-model]]`, `[[05_Theory/position-state-derivation]]`, `[[05_Theory/context-aware-risk-allocation]]`, `[[05_Theory/theorems]]`, `[[05_Theory/proofs]]`, `[[07_Analysis/theory-parity-audit-20260813]]` | `proof-draft` | T1–T6 plus the position-state P-PS1/P-PS2 derivations have software parity checks and local QA; probability eligibility now fails closed without hashed provenance; independent sign/geometry review, covariance provenance and proof review remain open. The active physical contract is the six-state position/velocity model with body-velocity input; the older torque simulator is compatibility code only. |
| Perception using real Internet images | Seven-image Wikimedia candidate cohort remains retained under `data/raw/web-cohort-20260814/`; a separate four-image COCO8-pose public ground-truth diagnostic now has manifest/annotation/hash/decode preflight PASS and fresh YOLO26s-pose box metrics | `candidate-acquired; admission blocked` | Independent annotations/adjudication, held-out split, detector-overlap review, cohort expansion/OOD and paired context records |
| LSTM as a CCA context interface | Fresh simulation-only 9,600-row context package and self-supervised score-loop checkpoint are hash-bound; no target-robot capture exists | `candidate-development-only; simulation-only` | Confirmatory `ctx_run.py` requires a sealed target-compatible direct CSV/JSON capture manifest with matching `context.csv` hash, frame/calibration provenance, frozen checkpoint, calibration and independent ID/OOD test |
| Python simulation and controller benchmark | Active runner retains the six-state position model with distinct MPC, NMPC, DWA, MPPI and CCA–NMPC bindings; a fresh 40-episode learning campaign and the physical-spec-bound 30-unit map benchmark are retained as development-only | `candidate-development-only` | Freeze PR20/PR21 and repeat with a provenance-linked real-context checkpoint before any confirmatory claim |
| MATLAB simulation | Added the active position-state entry point `cca.Simulation.simulatePosition` and paired `cca.StudyRunner.runPositionState`; a fresh bounded four-scenario export is retained under `experiments/runs/matlab-position-learning-20260814/` | `candidate-development-only` | Freeze PR20/PR21, run the confirmatory MATLAB campaign, and record an independent manifest before scientific interpretation |
| Direct robot experiment without ROS/ROS2 | CSV/JSON contract plus PR30 static no-ROS entry preflight `PASS`; user-supplied 400 x 400 mm geometry and sensor mounts are recorded in `configs/physical_robot.json`; non-unknown packages require hash-bound `calibration.json`; no AstraS/N10P device package captured | `verified-policy; geometry supplied, not independently verified` | Capture final six-state robot-state, body-velocity control, context, events, map and calibration files with provenance. Physical admission remains blocked until H0 safety, dimensional/sensor calibration, ground truth and stage records are supplied. |
| Q1 claim/evidence release | Claim matrix is draft and all empirical claims remain blocked/withdrawn | `blocked-by-evidence` | Complete evidence manifests, independent reproduction, and review |
| Final Q1 peer review | `$q1-reviewer-ee` not yet invoked | `pending` | Invoke only after the manuscript and evidence package are complete |

## Theory boundary

T1–T3 and the fixed-budget proposition establish allocator algebra for a fixed
active set. T4–T5 are conditional, one-update bounds under
`Pr_model`; they require geometry containment, covariance provenance, zero
slack, and mode-accounting parity. T6 only states that a feasible candidate is
selected in one solve. None of these derivations establishes closed-loop
stability, recursive feasibility, calibration on `Pr_star`, real-time
performance, or physical safety.

The active perception-to-control chain remains:

`camera/LiDAR -> pose/context snapshot -> LSTM context -> CCA risk allocation -> position-state CCA-NMPC -> body velocity`.

## Current host checkpoint — 2026-08-14

The direct STM recorder now latches an STM-reported stop flag before selecting
the next command, forces zero body velocity, records `stm_stop_latched`, and
keeps the normal zero-command tail. The Python suite, Ruff and repository
validation pass, and MATLAB R2025a host tests remain software checks. The four
evidence registries remain empty; no sensor, STM, CAN or robot device was
opened. The retained real-image and simulation packages are explicitly
candidate-only, and no claim or paper file was promoted.

The next research gate is independent annotation/adjudication for the retained
Internet cohort plus a new frozen target-compatible context acquisition. After
that, the LSTM split/checkpoint, paired controller benchmark, and only then the
physical H0 stage can be executed. See [[06_Methods/execution-roadmap]],
[[06_Methods/dataset-protocol]], [[06_Methods/final-run-data-package]] and
[[07_Analysis/pr30-entry-preflight-20260813]].

## Perception checkpoint — 2026-08-14 continuation

The public COCO8-pose validation subset adds a reproducible provider-label box
diagnostic without fabricating annotations. Four images contain 14 provider
person boxes; the detector run records TP `11`, FP `1`, FN `3`, precision
`0.9167`, recall `0.7857`, F1 `0.8462`, mean matched IoU `0.8562` and CPU
P50/P95/max latency `324.91/573.17/603.18` ms. Because all images are positive,
the image-level matrix `[[0,0],[1,3]]` has no negative denominator. The labels
are blinded to this run in the mechanical sense, but they are provider labels,
not independent annotator/adjudicator ground truth. The package remains
`candidate-not-evidence`; no metric was promoted to the claim register or
paper, and target-device timing/OOD/model-overlap review remain open.

## Requirement audit continuation — 2026-08-14

The current state was checked against the full rebuild objective rather than
against the development package alone:

| Requirement | Current proof | Verdict |
|---|---|---|
| Purge legacy data/models/runs | Clean-reset inventory plus empty data/model/experiment/artifact registries; only post-reset candidates and one backup snapshot remain | `PASS — policy/provenance` |
| New repository provenance | Fresh branch `codex/repository-bootstrap` and staged snapshot; no commit/tag/remote yet | `PARTIAL — commit awaits explicit Git approval` |
| Overleaf-only manuscript | Local paper firewall and backup hash audit; no active manuscript build | `PASS — boundary` |
| Research gap and literature | Focused Zotero/Obsidian audit plus dated Google/web screening; latest records remain screening-only | `PASS — bounded, not exhaustive` |
| Theory/theorems/proofs | Simple position-state model, allocator derivations and parity tests; independent proof/geometry review absent | `DRAFT — not verified` |
| Unsupervised/RL learning | Five-seed self-supervised next-velocity LSTM, calibration, score/penalty Q-learning and hash-bound simulation package | `EXECUTED — simulation-only` |
| Simulation/benchmark | Paired MPC/NMPC/DWA/MPPI/CCA-NMPC development runs, fixed global path and trigger-only local path; MATLAB bounded export | `EXECUTED — unreleased` |
| Internet-image perception | Wikimedia cohort plus COCO8-pose provider-label diagnostic, overlays and confusion/box metrics | `CANDIDATE — independent annotation/OOD open` |
| Hardware experiment | No ROS/ROS2 runtime; no Astra-S/N10P/STM32 device opened; no measured geometry/calibration | `PENDING — external hardware gate` |
| Final paper and Q1 review | Paper remains locked; final English `main.pdf` and `$q1-reviewer-ee` review do not exist | `PENDING — evidence and manuscript required` |

This table is an internal audit only. It does not promote any candidate metric,
does not modify the manuscript, and does not redefine completion around the
simulation package.

## Status checkpoint — 2026-08-13

The bounded focused literature audit is `COMPLETE` and PR00 is `REVIEWED` for
scope/claim logic. PR11, PR12, PR20, PR21, PR30 and PR40 are `REVIEWED` for
design only; PR02 remains `PROOF-DRAFT`. These transitions do not admit any
data or result. The repository contract, Ruff and 206-test Python suite pass;
the current repository count is 23 schemas, 15 instances, 98 Obsidian notes and
836 wikilinks. A later 2026-08-13 attention/interaction refresh added two
screening-only source notes and raised the current repository count to 23
schemas, 15 instances, 100 Obsidian notes and 850 wikilinks; the added records
remain outside final citation claims. The subsequent web-cohort refresh is
limited to two additional real Wikimedia assets because the source endpoint
returned HTTP 429; both remain candidate-only. Repository validation after the
refresh reports 23 schemas, 15 instances, 101 Obsidian notes and 857 wikilinks;
the subsequent literature and hardware-intake notes bring the latest count to
863 wikilinks.
The next admissible work is
real-context acquisition and protocol freeze, followed by confirmatory
simulation; physical hardware remains later.

See [[07_Analysis/focused-audit-review-20260813]] and
[[07_Analysis/protocol-design-review-20260813]].

The human is dynamic, but no ground-truth future trajectory is supplied to any
controller. Only CCA-NMPC may keep a causal future-position prediction
internally for its chance rows; that sequence is not exported or drawn on an
image. The global robot path remains fixed; a local robot path is regenerated
only when the declared conflict or direction-change trigger fires.

An external NavWareSet scene-13 context candidate was previously inspected
without ROS playback. Its local payload and score-loop output were purged on
2026-08-14; only the data-design lesson remains and no result is retained.

All superseded map payloads and the later v7--v9 development pilots were
physically purged on 2026-08-14. Their identifiers and hashes remain only in
the purge audit; they are not a replacement for a future confirmatory campaign.

The dated checkpoints that follow are frozen historical audit entries. They
document why implementation decisions changed, but any pre-reset payload,
metric, model or run named there is invalidated by the 2026-08-14 purge. The
current status is defined only by the requirement table above and the latest
post-reset checkpoint below.

## Position-state simulation boundary — 2026-08-14

The active Python and MATLAB entry points retain the six-state/body-velocity
design and distinct MPC/NMPC/DWA/MPPI/CCA bindings. All superseded simulation
payloads, metrics and plots were purged. The fresh learning and bounded MATLAB
packages are retained only as candidate-development outputs and are not
promoted. A confirmatory campaign must start after PR20/PR21 freeze.

## Current verification after clean reset — 2026-08-14

The current host checks establish code/provenance hygiene only: Python tests,
Ruff and repository validation pass. Dataset/model/experiment/artifact
registries are empty. The post-reset candidate packages remain outside those
registries and outside the claim register; no hardware package exists.
Confirmatory simulation, physical capture and final Q1 review remain pending.

## Position-state QA checkpoint — 2026-08-13

The physical contract was amended to `[x,y,theta,vx,vy,omega]` with body-
velocity commands. The direct recorder, metadata, packager, physical schema
`1.3.0`, PR30 and linked Obsidian notes are synchronized. Current software QA
is Python `198 passed`, Ruff `PASS`, MATLAB `72 passed, 0 failed, 0 incomplete`,
and repository validation `PASS`. These are implementation checks only; no
device was opened and no physical package or scientific result was admitted.

## Numerical-parity checkpoint — 2026-08-13 00:31 UTC

The Python/MATLAB chance-row variance-floor mismatch was removed by exposing the
same \(10^{-12}\,\mathrm{m}^2\) regularizer in both configurations. Focused
Python tests, Ruff, MATLAB (`70 passed, 0 failed, 0 incomplete`), repository
contract validation and `git diff --check` pass. This closes a software parity
defect only. PR02 is still `proof-draft`; independent proof/geometry review,
calibration provenance, confirmatory data and all physical evidence remain open.

## Acceptance rule

Only a `verified` artifact with a protocol, immutable code revision, dataset or
hardware provenance, raw-output hash, QA record, and independent reproduction
may enter `[[01_Governance/claim-register]]`. Candidate, design-only,
proof-draft, screening, and policy records remain research notes.

## Latest implementation checkpoint — 2026-08-13

PR02 gained a directly testable numeric ellipse-support helper and a sampled
rotated-boundary check in addition to the existing zero/near-singular covariance
tests. PR10 now has an explicit second-annotation/adjudication contract, and
PR11 rejects unsupported direction tokens and missing leakage-group metadata on
the confirmatory path. Current QA evidence is Python `198 passed`, MATLAB `72
passed`, Ruff `PASS`, STM host `PASS`, and repository contract `PASS`. These are
implementation and data-contract checks only; independent proof review,
annotation, physical calibration results, physical specification and all
confirmatory evidence gates remain open.

## Links

[[00_MOC/project-map]] · [[01_Governance/status-and-provenance]] ·
[[01_Governance/claim-register]] · [[07_Analysis/current-evidence-index]] ·
[[07_Analysis/experimental-analysis]] · [[05_Theory/theorems]] ·
[[05_Theory/proofs]] · [[06_Methods/protocol-index]] ·
[[08_Decisions/decision-register]]

## MATLAB recheck after online CCA branch — 2026-08-13

`src/matlab/run_tests.m` was rerun with MATLAB R2025a after the no-ROS online
CCA-NMPC integration and protocol-boundary updates: `72 passed, 0 failed,
0 incomplete`. The Python suite remains `202 passed`, with Ruff and repository
validation passing. These are host-software regression checks only; no
simulation campaign was promoted and no hardware/device evidence was created.

The bounded MATLAB position-state smoke was also executed in memory (20
controller/scenario rows). All five controller labels produced the same
context-free nominal response, so this run is explicitly an interface smoke
and not a dynamic-human controller comparison; no output directory or claim
artifact was created.

The direct-recorder regression also covers a moving-person direction change:
CCA-NMPC increments only the local-path generation counter, preserves the
immutable global path and returns a three-component body-velocity command.
The test explicitly rejects a predicted-human-state sequence in the controller
detail payload; the current Python suite is `202 passed`.

## Multi-seed LSTM and dynamic-human boundary recheck — 2026-08-13

The active score-loop runner now records every independent seed outcome,
selects the highest validation self-supervised score with a deterministic
tie-break, and fails closed when a confirmatory run has fewer than five
successfully completed seeds. Development runs remain candidate-only. Current
verification is Python `203 passed`, Ruff `PASS`, repository contract `PASS`,
and PR30 static preflight `PASS`/`BLOCKED`; MATLAB remains `72 passed` from the
same host-software regression. No sealed hardware package, real context
checkpoint, or dynamic-human performance result exists. The CCA-NMPC-only
boundary is unchanged: future human positions may exist only in controller
memory, never in image overlays or exported context data.

The position-state map and hardware entry points now share
`cca_sim.benchmark_v3.NmpcPrediction`; the legacy torque-NMPC module is no
longer imported by either active entry point. This is an interface cleanup
only and does not open any evidence gate. The latest active-entrypoint
regression brings the full Python suite to `204 passed`.

The separate sealed-package analysis now summarizes CCA-NMPC event details
without modifying raw data or exporting a human future path. Its parser
regression is included in the latest full suite (`206 passed`); this remains a
provenance/analysis capability, not a physical result.

## Corrected verification closure for this cycle — 2026-08-13

The corrected position-state source was rechecked end to end: Python `206
passed`, MATLAB R2025a `72 passed, 0 failed, 0 incomplete`, Ruff `PASS`,
repository validation `PASS`, and `git diff --check` `PASS`. This closes the
current host-software regression cycle only. It does not close PR02 proof
review, PR10/PR11 real-data admission, PR12 LSTM calibration, confirmatory
simulation, or PR30 hardware evidence. The only retained map campaign is v7;
v5/v6 were superseded and deleted. The dynamic-human rule remains explicit:
CCA-NMPC alone may use an internal causal prediction, while no predicted human
trajectory is drawn on the image or exported as a path artifact.

## Projected-covariance implementation checkpoint — 2026-08-13

`PositionStateNmpc._risk_adjustment` now uses the predicted covariance projected
onto the robot--person normal and the corresponding fixed-budget normal
quantile. A regression test verifies monotonic growth of the active CCA margin
with projected covariance. This does not change the position-state interface,
does not give future human state to the baselines, and does not create a
trajectory overlay. The latest Python host suite has `207` passing tests;
Ruff, repository validation and `git diff --check` pass. This remains
development-only software evidence, not calibrated LSTM or hardware evidence.

## LSTM-in-CCA boundary — 2026-08-14

The former candidate LSTM pilots and checkpoints were purged. The reusable
contract is retained in code and protocol: LSTM is an interface inside CCA,
out-of-domain output is rejected before actuation, and no human future path is
exported or drawn. A target-compatible checkpoint and independent calibration/
ID/OOD evidence are still required.

## MATLAB position-state export closure — 2026-08-14

The MATLAB default export was corrected to write only the active six-state /
body-velocity contract; the legacy torque Gate-A exporter is now explicit
compatibility mode. MATLAB R2025a reports `73 passed, 0 failed, 0 incomplete`;
Python reports `214 passed`, Ruff and repository validation pass, and
`git diff --check` is clean. This closes the host software consistency item
only. No simulation campaign, calibrated LSTM, physical capture or manuscript
claim is promoted.

## Full-URDF map-footprint correction — 2026-08-14

The map controller contract was audited against the complete
`rai_robot_urdf` intake. The active footprint now uses the selected
`mini_mec_robot` base, controller, four wheels, camera mount and laser mount,
with half-extents `(0.1348093152, 0.1150890935) m` and circumscribed radius
`0.1772541986 m`. The map runner verifies the source URDF SHA-256 before
import, passes the radius to DWA/MPPI, and records the geometry in its
manifest. Candidate runs made with the previous generic radius are not
comparable and remain unpromoted. This is a provenance and implementation
closure only; physical measurement and simulation evidence remain open.

Post-correction host checks are Python `220` passing tests, MATLAB R2025a `73`
passing tests, Ruff `PASS`, repository validation `PASS`, and hardware
preflight `PASS/BLOCKED`. These checks do not promote a map campaign or close
the physical admission gate.

## Online clearance parity correction — 2026-08-14

The direct hardware `OnlineCcaNmpc` path now consumes the prepared
URDF-derived footprint and rejects a stale explicit clearance based on the
former `0.32 m` radius. Its default is the same position-state clearance used
by the map contract. Runtime metadata carries the footprint. This is a
pre-actuation contract correction; no device, calibration, or physical result
was created.

## Runtime URDF provenance sidecar — 2026-08-14

The recorder now verifies and writes the selected URDF source, URDF/xacro hashes, wheel
radius and wheel spans, and the mesh-derived footprint to `capture.json` beside
the frame data. The final CSV/map payload is unchanged; the sidecar gives each
future physical capture a direct provenance link to the model parsed before
device access. The new contract tests and full Python suite pass (`222` tests),
while PR30 remains `REVIEWED` with admission `BLOCKED` because no physical
package exists.

The recorder and final packager now also preserve complete N10P scans in
`lidar.csv` (one timestamped JSON point set per scan). Hardware packages are
rejected when this sensor table is absent or contains no valid points; unknown
development packages may remain sensor-free.

## Literature refresh checkpoint — 2026-08-14 (real-robot metrics)

The latest focused Google/web screening pass added four boundary records for
real-robot clearance/timing reporting, Mecanum MPPI/CBF comparison,
omnidirectional disturbance rejection and physical MPC evaluation. They are
linked in [[03_Literature/web-verified-gap-sources]] and
[[03_Literature/source-index]], remain screening-only, and were not imported to
Zotero or the manuscript. The defensible gap is unchanged. Repository
validation after the refresh reports 23 schemas, 15 instances, 103 Obsidian
notes and 899 wikilinks; no dataset, model, simulation result or hardware
package was promoted.

## Operator preflight checkpoint — 2026-08-14

`hardware_entry.py preflight` now performs the same no-device validation as the
record command for the concrete config, calibration, map, target Jetson
YOLO26s-pose manifest, optional LSTM path, schedule and output paths. It does
not open Astra-S, N10P or STM32 and does not create a run. The static PR30
report remains `PASS`/`BLOCKED` with SHA-256
`53132D9ADB67E2CCC49C45D24FB84843910BBA82DCDB330FDAE35D1462AF340B`;
the full Python suite has 223 collected tests. This reduces pre-capture
configuration failures but does not provide physical evidence.

## Shared context-score parity correction — 2026-08-14

`scripts/python/tools/map_run.py` now evaluates the same five-feature logistic
context score used by the CCA scorer and MATLAB path. The previous
proximity/closing-only proxy is no longer active. A horizon-level regression
test compares the map prediction with `ContextScorer`; the full Python suite
collects 224 tests and the focused suite passes. This is a theory-to-code
consistency correction only; score calibration, confirmatory data and hardware
admission remain open.

## Position-state candidate-rollout checkpoint — 2026-08-14 correction

The active implementation is the compiled C++ bounded candidate rollout, not a
direct finite-horizon multiple-shooting solver. It validates the six-state/body-
velocity input, uses the supplied nominal robot geometry for the CCA reduced
risk correction, clips the command, and records a finite horizon rollout.
`maximum_risk_slack_m=0` is a reserved output field; no optimized slack or
solver residual is exposed. The Python layer is an ABI/orchestration adapter.
Python QA, Ruff and repository validation pass. No simulation campaign,
calibration result, hardware motion or paper claim is promoted by this
checkpoint.

## Frozen prediction geometry checkpoint — 2026-08-14

The position-state reduced-risk builder now consumes the prediction's
`nominal_robot_xy` field and fails closed when it is incomplete or non-finite;
the reference path is no longer an implicit substitute. A dedicated regression
passes, and repository validation and Ruff remain green. This is a parity
correction only; full chance-row solver eligibility, physical admission,
calibration, residual/deadline evidence and the locked paper are unchanged.

## Clean-reset purge checkpoint — 2026-08-14

The retained candidate payloads were physically removed after an exact-path
audit: 55 files and 59,260,346 bytes covering web-image manifests/media,
NavWareSet raw/processed data, three position-state pilot runs, detector and
LSTM outputs, YOLO26s-pose weights, and the generated preflight artifact. The
four registries are empty again. The purge record is
[[07_Analysis/development-artifact-purge-20260814]]; no paper or backup file
was modified. A future dataset or run must start from a new protocol freeze.

## Post-reset host QA — 2026-08-14

After the purge and provenance-parity correction, Python collected and passed
`228` tests, Ruff passed, repository validation passed with 23 schemas, 15
instances, 104 Obsidian notes and 911 wikilinks, and `git diff --check` passed.
MATLAB R2025a `src/matlab/run_tests.m` also passed all 74 tests with zero
failures/incomplete cases. These are host/software checks only; no simulation
campaign, calibration, detector model, dataset, robot motion or paper claim is
admitted.

## Covariance-domain guard — 2026-08-14

The position-state chance-row path now fails closed for non-finite, asymmetric
or materially non-positive-semidefinite relative covariance. Focused regression
tests pass. This strengthens the implementation boundary for PO-013 but does
not close covariance provenance, calibration, geometry review, residual/slack
eligibility or physical evidence.

## Direct STM recorder and measured-geometry correction — 2026-08-14

The direct bring-up path is now isolated in
`scripts/python/tools/stm_experiment.py`. It reuses the audited STM32 serial
frame, writes direct telemetry/control CSV and hash-bound JSON metadata, and
zeros the body-velocity command on every exit path. It is a commissioning
subset, not a final Astra-S/N10P evidence package.

The current `rai_robot_urdf` intake is explicitly `cad_reference_only`.
`hardware_entry.py prepare` leaves physical dimensions unresolved unless a
separate measured `cca-physical-robot-v1` record is supplied, and
`RobotGeometry.from_json` rejects any other authority. No hardware device was
opened and no result was promoted. The locked paper and its backup remain
untouched.

The direct STM recorder also latches the STM stop flag before selecting a
nonzero command; a stop forces zero, records the event and exits through the
zero-command tail. The regression fixture passes. This remains software
fail-safe QA, not target-robot safety evidence.

The post-change Python suite passes `237` tests; Ruff and repository validation
remain green. No hardware device or experiment output was created.

The full recorder also performs the STM stop check before command selection, so
the full-stack path no longer has a one-cycle stale-command window after a
reported stop. The regression suite passes `238` Python tests; this remains
software QA and does not create hardware evidence.

## MATLAB comparator implementation checkpoint — 2026-08-14

The MATLAB position-state smoke entry now dispatches distinct bounded
implementations for MPC, NMPC, DWA, MPPI and CCA-NMPC rather than reusing one
nominal command law. Its six-state/body-velocity contract is unchanged, and
the CCA branch explicitly reports that context is not supplied by this
interface. The full MATLAB R2025a suite passes `74` tests; a short in-memory
five-controller smoke is finite for every branch. This is code/interface QA
only: no campaign output, physical result, or paper edit was created.

## Current motion gate and preflight — 2026-08-14

Any full-recorder motion now requires a validated `--safety-record` confirming
approval, emergency stop, remote disable and watchdog; `observe` remains
zero-command only. The regenerated no-device report is
`status=PASS/admission_status=BLOCKED`, SHA-256
`A8337AD6F08CE46C9CD5D42622DB7FB3280A53EC056A8BF3CF11B876EDEBBADA`.
The Python suite passes `239` tests, Ruff and repository validation pass, and
no physical device or data package exists. This is not hardware evidence.

## C++ transport split and parity checkpoint — 2026-08-14

The low-level boundary is no longer Python-only. The C++ core now owns the
STM32 serial encoder/decoder, stop-safe zero command and C ABI shared transport
(`src/cpp/src/stm_c_api.cpp`), plus the CCA CAN CRC/frame codec. The Python
`Stm32SerialSource` automatically selects `libcca_ai_transport` when built on
the target; `CCA_STM_BACKEND=python` is an explicit compatibility fallback.
Python remains the appropriate layer for Astra-S/OpenNI2, N10P integration,
YOLO26s-pose, LSTM/CCA-NMPC and evidence packaging.

The C++ Release build and CTest both pass in Ubuntu 22.04 WSL; Python tests,
Ruff and repository checks also pass. The static hardware preflight is
`PASS/BLOCKED` and records the C++ source hashes in
`research/metadata/hardware/pr30_entry_preflight_20260814_cpp.json`. No serial
device was opened, no motion occurred and no hardware result was promoted.

## `cca_shared` hot-path allocation — 2026-08-14

The fixed-width CCA CAN CRC and frame codec now use the C++ transport library
through the existing Python `cca_shared` boundary on Linux. Calibration,
contract, hash and manifest policy remain Python because they are data/schema
operations rather than control-loop kernels. CMake/CTest, the Linux C ABI
round-trip smoke, and the five-feature context-score parity smoke pass. The
239-test Python suite and repository checks pass.
The context scorer is exposed through the same C ABI and selected by
`cca_ai.context`; `CCA_CONTEXT_BACKEND=python` remains an explicit fallback.
This is software parity only; no device, dataset, result package or paper was
modified. Detailed allocation is recorded in
[[07_Analysis/cca-shared-implementation-audit-20260814]].

## Real-image acquisition checkpoint — 2026-08-14

A new seven-image Wikimedia cohort was acquired with explicit source page IDs
and direct local paths under `data/raw/web-cohort-20260814/`. The manifest-only
validator reports `PASS/BLOCKED`: all media hashes, dimensions, decoding,
rights fields and real/non-AI flags pass, while annotation, privacy,
pretraining-overlap and cohort-expansion gates remain open. Visual screening
was recorded as source-quality review only; no detector metric, label or
confusion-matrix value was produced. See
[[07_Analysis/web-cohort-acquisition-20260814]].

The official external YOLO26s-pose checkpoint is retained as the separate
candidate `experiments/runs/person-web-inference-20260814/yolo26s-pose.pt`
with a hash-linked acquisition record. It remains outside the model registry
and outside all claims because the image cohort has no independent annotation,
adjudication, privacy approval, pretraining-overlap review or target-device
timing. See [[07_Analysis/yolo26s-pose-candidate-acquisition-20260814]].

## Continuation audit — 2026-08-14

The active source layout was rechecked after the runtime consolidation. There
is no active `src/ros2` tree, no filename/folder matching `cca_*` or `_vN`, and
the old Python torque-controller modules are absent. `src/hardware.py`,
`src/shared.py` and `src/repository.py` remain live dependencies; the latter is
the flattened repository acceptance gate formerly named `repo_contracts.py`.
The read-only `reference/robot` snapshot remains because the no-device
preflight still hashes the URDF, xacro and legacy STM frame contract.

`validate_hardware_entry.py` was rerun and produced
`research/metadata/hardware/pr30_entry_preflight_20260814_current.json`,
`PASS/BLOCKED`, hash
`7F9DF16FB7EA6B7DD6C4D0A7E7EDB82575F2B5E44B11C53756B90517EC43D49A`.

A fresh bounded MATLAB position-state package now exists at
`experiments/runs/matlab-position-learning-20260814/`. Its manifest declares
`candidate-development-only`; the package is hash-verified and linked from
[[07_Analysis/simulation-position-state-20260814]]. Repeated controller rows
and the short horizon are diagnostics, not evidence of superiority or
real-time/hardware performance. Paper editing remains prohibited.

Current repository QA: `repo_check.py` PASS (24 schemas, 16 instances, 115
notes, 1,026 links), Ruff PASS and the full Python suite PASS. These checks do
not close PR02, PR10/12, PR20/21,
PR30 or PR40; independent proof review, calibrated perception evidence,
confirmatory simulation, physical specifications and a sealed robot package
remain open.

## Dynamic-map adapter correction and pilot audit — 2026-08-14

The first same-name dynamic-map output was removed after review found that the
Python adapter flattened a state-major reference while the C++ controller
expects interleaved six-state rows. The corrected adapter has a regression test
and the replacement package is recorded in
[[07_Analysis/map-context-development-20260814]]. All five package artifact
hashes match the manifest. The pilot is explicitly development-only: it uses a
direct direction/speed context adapter, not a fitted LSTM; it has no ground-
truth human path, no image overlay and no hardware capture. It therefore does
not close the confirmatory simulation, LSTM calibration or physical-device
gates.

## Active-name and candidate provenance correction — 2026-08-14

The external pose checkpoint is retained at the descriptive
`experiments/runs/person-web-inference-20260814/yolo26s-pose.pt`; the two
retained pilot lesson notes were renamed without embedded run/version suffixes.
The purge audit's old path remains absent, while the current candidate
acquisition has its own hash-bound path and metadata. Detection, web-cohort
and repository contract tests pass after the correction.

## Simulation reset and fresh learning campaign — 2026-08-14

The superseded Internet cohort, detector checkpoint and all prior experiment
payloads were deleted under [[07_Analysis/simulation-reset-20260814]] before a
new run was opened. The new package
`experiments/runs/simulation-learning-20260814/` contains a 9,600-row
simulation-only context stream in 40 episode groups, a frozen disjoint
train/validation/calibration/test-ID/test-OOD split, a five-seed
self-supervised LSTM score loop with independent temperature calibration, a
tabular Q-learning score/penalty policy and a paired Python map benchmark. Its
root and nested manifests are
hash-bound and all status fields remain `candidate-development-only`.

The test-ID/test-OOD self-supervised scores were `0.837`/`0.792`, with speed
MAE `0.068`/`0.088 m/s` and direction macro-F1 `0.914`/`0.783`; the RL rolling
score was `0.859` after 81 episodes. The data are simulated, and no real image,
hardware device, protocol freeze or paper file was used. These facts keep
PR10/PR12/PR20/PR21 open and prevent the numbers from entering the claim
register.

## Independent 30-unit development benchmark — physical-spec rerun — 2026-08-14

The separate Python map package
`experiments/runs/simulation-benchmark-400mm-20260814/` completed 30
replicate-by-scenario units using the calibrated simulation-only LSTM/RL policy.
Its five data/plot artifacts match the manifest; score tuning is disabled and
the manifest excludes itself from the artifact list. The run is explicitly
`completed-development-map-context`, not confirmatory, because the checkpoint
is simulation-trained and no real capture or protocol freeze is present. It is
bound to the user-supplied 400 x 400 mm footprint, 50 mm interpreted wheel
radius, LiDAR height 240 mm, camera height 200 mm, LiDAR front-edge offset
100 mm, camera front-edge offset 35 mm and downward camera pitch 20 degrees.
Its descriptive CCA-NMPC safe completion is `0.667`, with zero collisions and
minimum context margin `0.2194 m`; no superiority or safety claim is opened.
The radius interpretation and all sensor dimensions still require independent
commissioning verification.

[[07_Analysis/simulation-learning-campaign-20260814]] ·
[[07_Analysis/current-evidence-index]] ·
[[07_Analysis/simulation-reset-20260814]]

## PR10 fresh cohort and perception diagnostic — 2026-08-14

The current post-reset PR10 cohort is the seven-image manifest at
`data/raw/web-cohort-20260814/web-image-manifest.json`; manifest-only
validation is `PASS`, while admission is `BLOCKED` with zero approved records.
The stale YOLO26s-pose checkpoint and diagnostic were deleted before the fresh
run. The current checkpoint and diagnostic are retained separately at
`experiments/runs/person-web-inference-20260814/`. The scene-tag diagnostic
matrix is `[[2,0],[0,5]]` at confidence `0.25`; this is not blind ground truth
and cannot support a detector claim. CPU P50/P95/max latency is
`313.43/505.37/544.43 ms`, not target-device timing.

The gallery overlay visibly records the local LSTM checkpoint path and
`context=not-provided`; it contains no fabricated speed/direction, human future
trajectory or robot local path. Independent annotation, adjudication, privacy
review, pretraining-overlap review and OOD expansion remain open. See
[[07_Analysis/web-cohort-acquisition-20260814]] and
[[07_Analysis/yolo26s-pose-candidate-acquisition-20260814]].

## Active-source path audit — 2026-08-14

The active implementation references were checked after the clean reset. The
direct recorder is `src/hardware.py`; the fixed-budget and chance-row core is
`src/control/src/controller.cpp`, exposed to Python through
`src/runtime/controller.py`; the position-state prediction contract is
`src/simulation/model.py`; and the MATLAB counterparts are under
`matlab/+cca/`. Historical notes may retain former paths for provenance, but
no executable entry point uses them. `repo_check.py` passed with 24 schemas,
16 instances, 115 notes and 1,026 wikilinks; focused LSTM/RL/controller and
repository tests passed (100%). No paper file was modified.
