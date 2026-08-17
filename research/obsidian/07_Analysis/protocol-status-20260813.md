---
type: protocol-status
status: active
evidence_status: knowledge-and-historical-ledger
paper_edit: prohibited
updated_at: 2026-08-15
---

# Protocol status ledger — current snapshot after clean reset (2026-08-14)

This note is the compact Obsidian view of the status table in
`protocols/README.md`. A protocol is promoted only when its stated acceptance
gate has an immutable artifact and the required independent check. A passed
mechanical or software check updates the completed-component column; it does
not silently promote a protocol to `VERIFIED`.

The current table and the post-reset checkpoint are authoritative. Entries in
the historical log below are frozen audit records from before the 2026-08-14
clean reset. Their datasets, models, runs and numerical outputs were purged and
must not be interpreted as current evidence or reconstructed for the paper.

| Protocol | Current status | Completed component | Remaining gate |
|---|---|---|---|
| [PR00](../../../protocols/PR00_scope_and_claims.md) | `REVIEWED` | RQ, hypothesis, claim limits and scope amendment; bounded focused-audit review added risk-aware MPPI, Mecanum MPC/hardware and uncertainty-aware safety boundaries without changing the narrow gap | versioned preregistration/SHA-256 and internal approval before holdout |
| [PR01](../../../protocols/PR01_literature_review.md) | `ARCHIVED — NOT AN ACTIVE GATE` | historical search provenance retained; SLR/PRISMA removed from active scope | no active execution |
| [PR02](../../../protocols/PR02_theory_and_proofs.md) | `PROOF-DRAFT` | T1–T5 ledger, explicit ellipse–disk half-space containment derivation, Python/MATLAB parity checks and fail-closed probability eligibility | independent geometry/proof review on an immutable snapshot and calibration evidence |
| [PR10](../../../protocols/PR10_person_data_acquisition.md) | `CANDIDATE ACQUIRED — ADMISSION BLOCKED` | prior payloads purged; seven Wikimedia candidates plus four COCO8-pose provider-label diagnostics pass mechanical manifest/media checks | independent annotation/adjudication, detector-overlap review, privacy release, larger ID/OOD cohort and approval |
| [PR11](../../../protocols/PR11_lstm_dataset.md) | `REVIEWED` | causal context schema, strict timestamp/direction contract, confirmatory split requires all leakage keys, no-human-trajectory contract and design review; NavWareSet candidate purged | permitted target-compatible real context recording, calibration and dataset freeze |
| [PR12](../../../protocols/PR12_lstm_training_evaluation.md) | `DEVELOPMENT-EXECUTED / UNRELEASED` | fresh five-seed self-supervised LSTM, calibration and score/penalty policy completed from the clean reset; simulation-only | sealed target-compatible context, checkpoint freeze, ID/OOD and independent rerun |
| [PR20](../../../protocols/PR20_simulation.md) | `DEVELOPMENT-EXECUTED / UNRELEASED` | fresh simulation learning package, fixed-global/local-trigger map run and bounded MATLAB position-state export replayed with hashes | protocol freeze, S2/S3 confirmatory campaign and independent analysis |
| [PR21](../../../protocols/PR21_controller_benchmark.md) | `DEVELOPMENT-EXECUTED / UNRELEASED` | paired MPC/NMPC/DWA/MPPI/CCA-NMPC development benchmark completed with score tuning disabled and raw-to-summary pairing checks | frozen fairness ledger, confirmatory paired benchmark and PR40 analysis |
| [PR22](../../../protocols/PR22_pilot_simulation.md) | `PURGED (development-only)` | pilot cũ đã xóa; contract fixed-global/local-trigger còn trong protocol và purge record giữ provenance | chỉ tạo run mới sau freeze PR20/PR21 |
| [PR23](../../../protocols/PR23_pilot_stabilization.md) | `FROZEN-PILOT` | stabilization pilot assignment and criteria | execute only if diagnostic evidence is needed |
| [PR24](../../../protocols/PR24_pilot_feasibility_preservation.md) | `FROZEN-PILOT` | feasibility/fallback criteria | new pilot only; keep failures in denominator |
| [PR30](../../../protocols/PR30_physical_experiment.md) | `REVIEWED` | direct no-ROS position-state `[x,y,theta,vx,vy,omega]` with STM32 body-velocity/CAN/CSV/JSON interface preflight `PASS`, mini-Mecanum URDF binding and design review, including strict timestamp validation and hash-bound calibration sidecar in `final_pack.py`/`ctx_run.py` | physical specification, calibration, approval, stage-gate, hardware package |
| [PR40](../../../protocols/PR40_statistics_and_qualitative_analysis.md) | `REVIEWED` | ITT-like populations, paired CI, confusion-matrix semantics, qualitative rubric và failure taxonomy đã qua design review | freeze before holdout and independent analysis |
| [PR50](../../../protocols/PR50_evidence_release.md) | `DRAFT-DESIGN` | release inventory, claim matrix and Q1 gate written | PR00/PR02/PR10–PR40 verified |

## Current implementation paths and physical-spec checkpoint — 2026-08-14

The active no-ROS recorder is `src/hardware.py` with the entrypoint
`scripts/python/tools/record_hardware.py`; the C++ transport/controller lives
under `src/control/`, and Python calls it through `src/runtime/controller.py`.
The current measured-spec input is `configs/physical_robot.json`, whose hash
is bound by `configs/study_contract.json`. The read-only robot snapshot is
under `reference/robot/`; historical `src/ros2`, `src/python/` and `src/matlab/`
paths below are retained only as audit provenance and are not active entry
points.

The compact `scripts/python/tools/robot_console.py` is now the operator surface
for PR30 commissioning: one Jetson service streams STM32/N10P/Astra-S state to
one laptop window and saves the direct CSV/map package. Its self-test and
repository checks pass, but the protocol remains `REVIEWED` and hardware
admission remains blocked until an approved physical run is sealed.

## Evidence pointers

- [[07_Analysis/theory-parity-audit-20260813]] — PR02 software-QA boundary.
- [[07_Analysis/pr10-preflight-20260813]] — PR10 mechanical preflight and
  admission blocker.
- [[07_Analysis/pr30-entry-preflight-20260813]] — PR30 no-ROS entry preflight.
- [[07_Analysis/focused-audit-review-20260813]] — bounded PR00 focused-audit
  review and status transition to `REVIEWED`.
- [[07_Analysis/protocol-design-review-20260813]] — downstream design review
  for PR11/12/20/21/30/40.
- [[03_Literature/Sources/source-kada-pedestrian-aware-mpc-2026]] — new
  human-centred MPC/interaction boundary from the latest audit.
- [[03_Literature/Sources/source-miyachi-cane-mpc-2026]] — new real-robot
  dynamic-obstacle MPC boundary.
- [[03_Literature/Sources/source-stefanini-context-aware-mpc-2024]] — PR00 focused-audit continuation: Zotero-matched context-aware MPC prior art.
- [[07_Analysis/completion-audit]] — cross-protocol completion audit.
- [[01_Governance/status-and-provenance]] — repository-wide provenance and test
  counts.

## Validation checkpoint — 2026-08-13

- Python suite: `152 passed`.
- Ruff: `All checks passed`.
- STM host tests: `CCA STM host tests: PASS`.
- Repository contract audit: `PASS` (`23` schemas, `17` instances, `86` notes,
  `682` wikilinks, no issues).
- Focused audit continuation: Zotero API/connector `PASS`; item `8T4BRJA4`
  re-matched to the Stefanini et al. context-aware MPC refresh note while the
  existing NW-01 full-text extraction is retained; audit remains `IN_PROGRESS`
  because the independent claim review is still open.
- A further Google/web screening refresh recorded SHARP, context-aware
  preference learning and ARMS as boundary records only; no Zotero import or
  novelty promotion was made.
- MATLAB unit/property suite rerun: `68 passed, 0 failed, 0 incomplete` in
  25.2537 s testing time. This is software QA only; no campaign or hardware
  evidence is implied.

## Continuation checkpoint — 2026-08-13 22:05 UTC

- `repo_check.py` and `git diff --check` were rerun with no repository issues.
- No protocol was promoted in this checkpoint. PR10 remains admission-blocked;
  PR11/PR12 have no sealed real context package or admissible checkpoint; PR20–
  PR24 have no new campaign; PR30 has no physical robot package; PR40/PR50 wait
  for upstream evidence.
- PR30's direct packager now rejects duplicate or non-increasing `t_ns`; the
  regression test and the regenerated preflight report pass. This is interface
  QA only and does not open physical admission.
- PR12/PR20 confirmatory LSTM provenance now checks the sealed capture manifest
  file itself (workspace-contained path, SHA-256, capture source and
  context-only flags), not only a copied hash in checkpoint metadata.
- The NavWareSet processed CSV/JSON route remains screening-only because its
  public page documents raw ROS-bag products and the tutorial repository has no
  machine-readable license record. The no-ROS rule is unchanged.

## Focused-audit closure checkpoint — 2026-08-13 00:01 UTC

- PR00 scope/claim logic was reviewed against the bounded source and
  nearest-work graph. The audit is now `COMPLETE` in
  `research/metadata/focused_literature_audit.json`; this is not SLR/PRISMA
  coverage and does not admit data or evidence.
- PR00 protocol status is `REVIEWED`, with preregistration version/SHA-256 and
  internal approval still required before confirmatory holdout execution.
- PR02, PR10--PR12, PR20--PR21, PR30, PR40 and PR50 were not promoted. Their
  remaining gates still require proof/data/holdout/hardware artifacts.

## Downstream design-review checkpoint — 2026-08-13 00:06 UTC

- PR11, PR12, PR20, PR21, PR30 and PR40 are now `REVIEWED` for design only;
  the checklist is [[07_Analysis/protocol-design-review-20260813]].
- No execution status changed. PR10 remains admission-blocked; PR11/PR12 have
  no sealed real context/checkpoint; PR20/PR21 have no frozen confirmatory
  campaign; PR30 has no physical package; PR40 has no holdout analysis.

## Continuation checkpoint — 2026-08-13 05:18 ICT

- `PR02` received explicit T4 edge-case coverage for zero-variance and
  rank-one near-singular relative covariance. The Python test
  `test_chance_rows_accept_zero_and_near_singular_covariance` and MATLAB test
  `TestSafety/chanceRowHandlesZeroAndNearSingularCovariance` both pass.
- Python suite: `154 passed`; MATLAB suite: `69 passed, 0 failed, 0 incomplete`.
  Ruff and `repo_check.py` remain `PASS`; repository counts remain `23` schemas,
  `17` instances, `86` notes and `696` wikilinks.
- Source/test snapshot hashes: `risk.py`
  `5F4102E278F8A659B0ECE84A8445F57B2C09DA1163B62169CB4BE30187FFBAE4`,
  `realtime_nmpc.py`
  `447532503839D717385398D8577D8DD4C81FD82276F46E843E22F0FBBD8A4B23`,
  `Nmpc.m`
  `40B85A85E164C6895E7555C7F4B44967E68E2E6416154BFFDA61BCB2491D592E`,
  Python tests `F4EA202F4D975ED7B4A6D5DB4594A8DE3570B7402581742135B8918015668094`
  and `C34B6F6D07D3935CF8A994282FDD792837F020A49452694EE45587F00CEBEEED`,
  MATLAB tests `B4C348FC7C03E62D671E9825DBBCCEF5533CF1FBD0F768FACA9ABDF85ED02BC7`
  and `27B6F2B0F899C07E6A32C5F35A7BA5B683A0A786C5C3F806FDC4127E558AB942`.
- PO-001 now includes an explicit ellipse–disk half-space containment
  derivation, and MATLAB `TestSafety/ellipseSupportContainsSampledBoundary`
  passes. The MATLAB suite is now `70 passed, 0 failed, 0 incomplete`; the
  updated `TestSafety.m` hash is
  `9856658A6FFF77F5ADB93AE78F4960263293943FA36ED97306A3E3B327EAB1B1` and the
  derivation note hash is
  `445CB6A0550F030FD2B2625892F547C54E4B1083C24053098A3993B3F305C7C6`.
- `PR00` focused audit was refreshed with an official YOLO26-pose tool check and
  a DRA-MPPI comparator boundary. The audit record remains `IN_PROGRESS`; its
  web-screening note hash is
  `AC702356E485C35758FBC2FA9C33D9B2D6E15409E136582E2BB3C6EF03492463` and the
  official YOLO26-pose source-note hash is
  `91E098BF8072D73BDDD328236AF80F15ED35A39DAA7761A0250DDEB03AC3518D`.
- `PR02` remains `PROOF-DRAFT`: these tests close only the stated numerical
  edge-case component. Independent sign/geometry review, calibration and
  reviewer identity are still open. No protocol is promoted.

## Continuation checkpoint — 2026-08-13 05:32 ICT

- The derivation-ledger SHA mismatch introduced while adding the PO-001
  containment paragraph was corrected. `repo_check.py` is `PASS`, with `23`
  schemas, `17` instances, `86` notes and `696` wikilinks; `git diff --check`
  and Ruff are also clean.
- The full Python suite passes `154` tests. MATLAB `run_tests` passes `70`
  tests with zero failures/incomplete cases. This is the current software-QA
  checkpoint; no simulation campaign, LSTM checkpoint, or hardware package was
  created.
- PR02 remains `PROOF-DRAFT`; the new ellipse-support test is not an
  independent reviewer sign-off and does not close calibration, residual or
  operational-probability obligations.

## Continuation checkpoint — 2026-08-13 05:33 ICT

- The Python T4 implementation now exposes one numeric ellipse-support helper
  used by the geometry audit test; this keeps the normal, rotated semiaxes and
  support calculation directly testable without changing the CasADi controller
  model. Focused Python NMPC tests pass, and the new source/test hashes are
  `4688375E82286D5B52F754B87B54CB9CE04412FF9FCB502EB910A829E6B73F43` and
  `799805925946E0CE7AC33274759AED60FF301A4D7227521280AB106CFD854BC0`.
- This is a software geometry-parity improvement only; PR02 remains
  `PROOF-DRAFT`, and no probability or collision claim is promoted.

## Continuation checkpoint — 2026-08-13 05:34 ICT

- Full Python QA passes `155 passed`; Ruff, `repo_check.py` and
  `git diff --check` pass. Repository counts remain `23` schemas, `17`
  instances, `86` notes and `696` wikilinks.
- STM host protocol/kinematics tests pass (`CCA STM host tests: PASS`). MATLAB
  remains at the latest `70 passed, 0 failed, 0 incomplete` checkpoint.
- These are implementation checks only. PR02 remains `PROOF-DRAFT`; PR10,
  PR11/12 and PR30 remain blocked/design-only until independent data, review,
  calibration and hardware gates are actually supplied.

## Continuation checkpoint — 2026-08-13 05:45 ICT

- At this historical checkpoint, `PR10` was `ACQUIRING`. The schema and
  validator represented a second blinded annotation plus adjudication; the
  ten-image candidate then had neither, so its mechanical report was `PASS` but
  admission was `BLOCKED`. That candidate and report were later purged; the
  current status is `RESET-BEFORE-ACQUISITION`. Historical report SHA-256 was
  `CC40F0E3A4ACFE8B437CFED42727295D17327033897FF91824C6888B032F0E95` and
  validator SHA-256 is
  `85AEDE25ADD67A1354B958C4F6963FCEC972659FD78FED1E9378E49905418AF9`.
  This candidate and report were later purged; the current PR10 status is
  `RESET-BEFORE-ACQUISITION`.
- `PR11` remains `DRAFT-DESIGN`. The confirmatory context path now rejects
  unsupported direction tokens and requires all four leakage-group keys before
  split-window construction. No context data or checkpoint was generated.
- Full Python QA is `169 passed`; Ruff, `repo_check.py`, and `git diff --check`
  pass. MATLAB remains at the latest `70 passed, 0 failed, 0 incomplete`
  checkpoint because no MATLAB source changed in this step. Repository
  contract is `PASS` with `23` schemas, `17` instances, `86` notes and `696`
  wikilinks. No protocol was
  promoted: PR02 is still `PROOF-DRAFT`, PR10 is admission-blocked, PR11/PR12
  have no sealed real context package, and PR20--PR50 remain downstream gates.

- `PR00` remains `DRAFT-DESIGN` after the 05:52 ICT Google/Scholar-oriented
  refresh. Risk-aware MPPI, Mecanum MPC/hardware disturbance rejection and
  uncertainty-aware predictive safety are now explicit screening boundaries in
  [[03_Literature/web-verified-gap-sources]] (note SHA-256
  `381282E54BC3F0FD2CA392DC8A7AD73F1D4A791D1B9F06853B9E6A2F995AFB23`); the
  research gap remains the bounded matched CCA interface comparison and no
  manuscript file changed.
- `PR30` remains `DRAFT-DESIGN`. The direct package path now requires and
  verifies `calibration.json` for every non-unknown capture source; no package
  or calibration record was admitted. Static preflight remains `PASS` and
  `BLOCKED` for hardware admission; report SHA-256 is
  `2B7F8733618806D6BD3C3332817FC5887E09549AA6737B26770A1A34909A54AE`.
- `PR00` remains `DRAFT-DESIGN`. The repeated Google Scholar spot-check was
  logged as discovery only; it returned no stable directly matched primary
  record, so the nearest-work matrix and narrow gap are unchanged.
- `PR12` remains `DRAFT-DESIGN`. The same sidecar hash is now propagated into
  the LSTM checkpoint metadata and checked again by `map_run.py`; full Python
  QA is `169 passed`. No real context CSV, calibration record or checkpoint was
  created.

- The 2026-08-13 literature refresh added DRA-MPPI, uncertainty-aware
  predictive CBF, DR-MPC and a physical SI-MPC comparison as screening-only
  boundary records in [[03_Literature/web-verified-gap-sources]]. The matched
  CCA position-state NMPC gap is unchanged; no Zotero import or manuscript edit was
  made.

## Continuation checkpoint — 2026-08-13 06:06 ICT

- `PR12` and `PR30` implementation contracts now share the calibration-sidecar
  validator. Non-unknown capture sources require `calibration.json` with sensor
  identity, camera intrinsics, sensor-to-robot extrinsics, residuals and a
  manifest/checksum SHA-256 binding. This closes a provenance loophole; it does
  not constitute a real calibration or hardware result.
- Full Python QA is `169 passed`; Ruff, `repo_check.py` and `git diff --check`
  pass. Repository contract remains `PASS` (`23` schemas, `17` instances,
  `90` notes, `751` wikilinks). MATLAB remains at `70 passed, 0 failed,
  0 incomplete`; no MATLAB source changed.
- PR30 static preflight remains `PASS`/`BLOCKED` with report SHA-256
  `2B7F8733618806D6BD3C3332817FC5887E09549AA6737B26770A1A34909A54AE`.
  No context CSV, calibration record, LSTM checkpoint, hardware package,
  simulation campaign or paper edit was created. No protocol was promoted.

## Direct recorder checkpoint — 2026-08-13

- `PR30` now has the executable no-ROS recorder scaffold in
  `src/python/cca_hardware.py` and `scripts/python/tools/record_hardware.py`.
  Its interfaces cover Astra-S/OpenNI2 frames, N10P serial packets, CCA CAN
  command/applied/status/wheel telemetry, context-only LSTM overlay and direct
  CSV/JSON output. Decoder/geometry/odometry/CSV/context tests pass.
- The device template intentionally leaves ports, CAN channel, firmware,
  calibration and robot dimensions unresolved. No device was opened and no
  physical package was generated; therefore `PR30` is `REVIEWED` for design
  only and hardware admission remains `BLOCKED`.

## Latest design-review/QA checkpoint — 2026-08-13 00:06 UTC

- `repo_check.py --require-focused-audit-complete`, Ruff and the full Python
  suite are `PASS` (`169` tests). Repository contract now reports 23 schemas,
  15 instances, 91 notes and 755 wikilinks.
- PR00 is `REVIEWED`; PR11/12/20/21/30/40 are `REVIEWED` for design only.
  PR02 remains `PROOF-DRAFT`; PR10 remains admission-blocked; no context
  package, checkpoint, confirmatory simulation, hardware package or paper edit
  was created.

## Literature refresh checkpoint — 2026-08-13 00:20 UTC

- Google/Scholar-oriented discovery added three publisher-checked screening
  records (human-centred AMR MPC, accompanying-robot MPC and Mecanum hybrid
  control). The bounded research gap is unchanged; none was imported into the
  frozen Zotero export or used as quantitative evidence.
- The focused-audit notes now distinguish `COMPLETE` bounded gap review from
  final-citation attachment/correction/retraction checks. PR01 remains archived.

## Literature refresh checkpoint — 2026-08-13 00:31 UTC

- Google/web discovery added the HRI 2026 prediction-quality study and a
  self-supervised pedestrian-motion preprint to the screening log. The records
  sharpen the separation between self-supervised LSTM metrics, closed-loop
  navigation outcomes and human-centred outcomes; they do not change the
  bounded gap or reopen PR01.
- The web-screening note hash is
  `185E9C637435EC3F35A38FECA8F0EF9B1766D018580ADB58629E076DC0C742E0`.
  No Zotero item, dataset, checkpoint, simulation, hardware package or paper
  file was changed.

## Hardware-literature refresh checkpoint — 2026-08-13 01:12 UTC

- Primary vendor/platform records for Astra-S/OpenNI2, Jetson Orin Nano,
  Raspberry Pi 4 and the N10/N10P serial family were added to the screening
  note. They sharpen deployment prerequisites only: exact firmware/SDK branch,
  N10P revision/baud, ARM64 TensorRT fingerprint and measured serial/CAN
  availability must come from the supplied hardware.
- No Zotero item, model, dataset, simulation, hardware package or paper file
  was changed; the bounded gap and PR01 archived status are unchanged.

## Learning/control literature refresh — 2026-08-13 02:45 UTC

- Google/web screening added two 2026 boundary records: model-based RL for
  uncertain social navigation and neural chance-constrained MPC under
  uncontrollable agents. They are screening-only; read-only Zotero searches
  found no matching local items, so no import was performed.
- The linked web note hash is
  `0549B2F3489F862CA3DD32FFD34BFE57982E7EB6819BF8B7E2865EE8785F83D9`.
  The gap remains `PIVOT-EMPIRICAL`: RL/neural MPC/chance-constrained learning
  are comparator boundaries, not standalone novelty claims.

## Update rule

When a component is completed, update both this note and the matching row in
`protocols/README.md`, record the artifact/hash, and distinguish design review
from execution and verification. Never convert a pilot,
synthetic run, software unit test, or static preflight into a real-robot or
confirmatory claim.

## Numerical-parity checkpoint — 2026-08-13 00:31 UTC

- PR02 remains `PROOF-DRAFT`; a bounded author self-audit is recorded in
  [[07_Analysis/theory-parity-audit-20260813]]. It verifies the signs and limits
  of T1--T5 but is not the independent proof/geometry review.
- The chance-row variance floor is now explicit and identical in Python and
  MATLAB (`1e-12 m^2`). The full Python suite (`171 passed`), Ruff, MATLAB tests (`70 passed,
  0 failed, 0 incomplete`) and `git diff --check` pass. This is implementation
  parity only; no probability, calibration or hardware claim is promoted.
- The PR02 protocol hash in
  `research/metadata/claim_evidence_matrix.draft.json` was refreshed to
  `F02901106D64A9BB83839A3888B2BC9A0C67B21204C2949EB4F8F816591D4934`.
- PR24's stale historical wording was corrected: the bounded focused audit is
  complete, but the pilot remains candidate-only until confirmatory freeze and
  independent checks. No protocol status was promoted.

## Development-artifact reset checkpoint — 2026-08-13 00:48 UTC

- In accordance with the reset boundary, the six development-only run packages
  (Python context-map, Internet-image detector diagnostics and bounded MATLAB)
  and the local `yolo26s-pose.pt` payload were deleted. The exact targets,
  file counts, byte counts and prior manifest/model hashes are recorded only in
  [[07_Analysis/development-artifact-purge-20260813]].
- The purge record SHA-256 is
  `4AA7BBF738E4F21701171073C2230F1256543669AD52DFCE6A6AFDAD5C11826A`.
- `PR22` is therefore `PURGED (development-only)`, not an executed result.
  `PR23`/`PR24` remain design freezes; no old trajectory, metric, detector
  prediction, MATLAB output or checkpoint may be reused for the new campaign.
- At this historical pre-acquisition checkpoint, no Internet-image cohort or
  source/annotation manifest was active. The current four-asset candidate is
  recorded in the later PR10 acquisition checkpoint below and remains blocked
  from evidence admission.

## Hardware-entry recheck — 2026-08-13 00:57 UTC

- `validate_hardware_entry.py` re-ran after the purge and returned `PASS` for
  the static interface contract, with `admission_status=BLOCKED`. The report
  SHA-256 is
  `D7D607D571B1D170890D514A022843738390F9F4700C89B620489229AE47F3B1`.
- No device was opened and no command was sent. Physical dimensions, sensor
  calibration, independent ground truth, stage approval, and a sealed direct
  package are still absent; PR30 therefore remains design-reviewed only.

## Direct-recorder robustness checkpoint — 2026-08-13 01:05 UTC

- The no-ROS recorder was corrected before any device run: output initialization
  precedes map/calibration copy, and wheel/command/applied source timestamps are
  separated so repeated CAN snapshots cannot create duplicate CSV timestamps.
- Python full suite and Ruff pass. The recorder remains capture-only and sends
  no actuator command; PR30 is still design-reviewed with admission blocked.

## Direct-sensor timing/profile checkpoint — 2026-08-13 01:35 UTC

- The N10P decoder now requires the explicit `n10p-108b-v1` profile instead of
  silently assuming a packet layout. The profile is still a preparation parity
  record and must be checked against the supplied unit's revision and firmware
  before H0.
- Astra-S/OpenNI2 frames retain the host receive timestamp as canonical `t_ns`
  and record the device timestamp in `context.csv` as `camera_device_t_ns`
  when the binding exposes it. Optional color/depth pair-skew rejection and
  sidecar timing counters are implemented; no physical timing was measured.
- Focused hardware QA passed (`9` tests plus the static preflight); full Python
  QA is `174 passed`; no device
  was opened, no CSV/map/checkpoint was created, and PR30 remains `REVIEWED`
  with admission `BLOCKED`.

## Hardware-entry recheck — 2026-08-13 02:14 UTC

- `validate_hardware_entry.py` again returned static `PASS` with
  `admission_status=BLOCKED`; the refreshed report SHA-256 is
  `44588A1246E308CE4E1C54431C90841F10520DD3B2C2F6D14F77CE771838D9D4`.
- The no-ROS scan found no active ROS/ROS2 import in the recorder path. No
  device was opened, no command was sent, and no physical package was created.

## Hardware QA refresh — 2026-08-13 02:26 UTC

- Full Python QA is `178 passed`, Ruff/repository contract/diff checks pass, and
  the direct hardware-focused tests now cover N10P profile selection, OpenNI
  timestamp conversion, Astra color/depth skew rejection and context-sidecar
  propagation.
- The refreshed static preflight remains `PASS` with
  `admission_status=BLOCKED`; report SHA-256 is
  `A207B3D74879F861D47FD7A292301136FF6A86720C2211F7537E46E7031AB984`.
  No device was opened and no physical package was created.

## Reset-path checkpoint — 2026-08-13 02:20 UTC

- `det_eval.py` and `validate_web_cohort.py` no longer default to the purged
  Internet-image manifest, model payload or old run directory. New cohort
  commands must supply explicit input/output paths; the reset tests pass.
- This removes stale execution pointers only. PR10 remains
  `RESET-BEFORE-ACQUISITION`; no new image, annotation, model or result was
  created.

## N10P baud provenance checkpoint — 2026-08-13 02:32 UTC

- Vendor N10 documentation lists 230400 bps, whereas the packet-parity source
  used 460800. The runtime template now leaves `lidar.baudrate` unresolved and
  rejects null/nonpositive values before opening serial; the physical config
  must bind measured baud, firmware and `n10p-108b-v1` to the supplied N10P.
- This is a fail-closed configuration correction based on vendor documentation,
  not a measurement of the user's unit. No device or package was created.

## PR10 new Internet cohort checkpoint — 2026-08-13 03:03 UTC (superseded metadata)

- Four real Wikimedia Commons JPEGs were downloaded into the new acquisition
  root `data/raw/web_cohort_20260813/`; the immutable source manifest is
  `data/manifests/web_person_cohort_20260813.json` and the annotation scaffold
  is `data/manifests/web_person_annotations_20260813.json`.
- `validate_web_cohort.py` returned `status=PASS` for schema, byte/hash,
  decoding, dimensions, source-group disjointness, rights/privacy fields and
  dynamic manifest binding. The report is
  `research/metadata/web_cohort_20260813/preflight.json`; it records
  `admission_status=BLOCKED`, `approved_count=0` and no independent
  annotator/adjudicator. At that checkpoint the person lists were empty
  scaffolds, not ground truth, detector input or metric evidence; the manifest
  was later amended only with pre-inference image-level presence tags and
  revalidated.
- At that historical checkpoint PR10 was `ACQUIRING-CANDIDATE (ADMISSION
  BLOCKED)` pending blind bbox annotation, a second annotator/adjudicator,
  pretraining-overlap review and ID/OOD expansion. The cohort and report were
  subsequently purged on 2026-08-14; current status is
  `RESET-BEFORE-ACQUISITION`, with no detector result retained.

The same candidate manifest was rechecked at 03:14 UTC. The refreshed
preflight report SHA-256 is
`C03A0AC1D79E5CB0C07510EECD4BE7BB9242C930FD20F66D3B1FB0D9F17240D5`; the
status and admission gate are unchanged.

## PR02 numeric-boundary checkpoint — 2026-08-13

- The fixed-budget allocator now rejects non-finite softmax logits in both
  Python and MATLAB instead of silently converting an invalid input into a
  uniform allocation. This is a finite-precision fail-closed correction only;
  it does not change the T1--T3 real-arithmetic derivation.
- Full Python QA is `179 passed`; MATLAB `run_tests` is `70 passed, 0 failed,
  0 incomplete`; Ruff and `git diff --check` pass. The current
  implementation hashes are `risk.py=
  FB1B990C75D093FA8D39C24A3AD01A92392F5EEFA7A520CABD927DB61A357570`,
  `Risk.m=F9F093CEA9E7A3171BA6C82342D783813276311E399647CDB34B66916D3FC07C`,
  and the regression test is
  `152AC520193406CCAAF51650AF0DD4ECE2D570E81B10BBDEB28B7FA088F6D68F`.
- The context-interface boundary is recorded in
  [[07_Analysis/theory-parity-audit-20260813]]: MATLAB `cca.score` is the
  five-feature primary simulation score, while the Python map runner's
  proximity/closing proxy remains context-only and is not a parity or paper
  claim. PR02 remains `PROOF-DRAFT`; independent proof, geometry, calibration,
  zero-slack and operational-probability obligations remain open.

[[00_MOC/project-map]] · [[07_Analysis/completion-audit]] ·
[[01_Governance/claim-register]]

## PR30 position-state direct-STM bridge checkpoint — 2026-08-13

- The direct recorder now contains a tested Python implementation of the
  legacy STM32 serial contract: 11-byte body-velocity command frames,
  XOR checksum, 24-byte signed telemetry frames, IMU/voltage decoding and
  stream resynchronization. `record_hardware.py` selects
  `transport=stm32_serial` without importing ROS/ROS2.
- `mini_mec_robot.urdf` is parsed for the four wheel-joint spans. When
  `urdf_path` is declared, supplied half-length/half-width values are checked
  against the URDF; conflicting geometry is rejected. The wheel radius remains
  an explicit physical configuration value because the vendor URDF stores the
  wheel as a mesh.
- Nonzero commands require a monotonic command CSV and explicit
  `--allow-actuation`; absent that flag, the recorder sends zero velocity only.
  The captured state is `[x,y,theta,vx,vy,omega]`; CSV compatibility names are
  `yaw_rad` and `wz_radps`. Position tracking is the physical control objective;
  a torque/current channel is not required.
  No device was opened and no command schedule was executed in this checkpoint.
- Static preflight is `PASS`/`BLOCKED`; the refreshed report SHA-256 is
  `CA9217115937DC4C5D22DF9DE701A6FC37D7DA58D70AF667073F56009010D971`.

## Position-state QA checkpoint — 2026-08-13

The physical state/input amendment is synchronized across the recorder,
packager, schema `1.3.0`, PR30 and Obsidian. Python QA is `198 passed`, Ruff
and repository validation pass, and MATLAB QA is `72 passed, 0 failed, 0 incomplete`.
These checks do not open hardware admission; no device, command schedule or
physical result exists.

## Position-state simulation pilot checkpoint — 2026-08-13

The active Python map runner now uses the six-state position model and
body-velocity commands (`vx_cmd_mps,vy_cmd_mps,wz_cmd_radps`) for distinct MPC,
NMPC, DWA, MPPI and CCA–NMPC bindings. The current three-scenario pilot (one
paired replicate per controller) is sealed at
`experiments/runs/context-map-position-state-pilot-20260813-v2/`. It recorded no
collision, while completion was controller-dependent and the linear-MPC
diagnostic did not meet the completion dwell. It is development plumbing only;
the retained failure does not replace the PR20/PR21 freeze, independent
confirmatory replicates, or hardware evidence. The earlier pilot directory was
purged after the MPC/NMPC binding correction.

### Position-state pilot v3 checkpoint — 2026-08-13

The same development runner completed five replicates across the three
context-only scenarios and five matched body-velocity controllers (75 episodes)
at `experiments/runs/context-map-position-state-pilot-20260813-v3/`. Score
tuning was disabled. There were zero collisions and zero controller/deadline
failures; safe completion was 15/15 for CCA-NMPC, NMPC and DWA, 14/15 for MPPI,
and 0/15 for MPC. The failed MPC episodes remain in the denominator. This is a
development-only diagnostic with no LSTM checkpoint, no protocol-freeze record,
and no independent reproduction; PR20/PR21 therefore remain `REVIEWED`, not
`VERIFIED`.

MATLAB now exposes the matching `cca.Simulation.simulatePosition` and
`cca.StudyRunner.runPositionState` entry points. A 20-row in-memory smoke
campaign passed; no exported MATLAB package or claim was created.

The theory graph now includes [[05_Theory/position-state-derivation]], with
P-PS1 (componentwise velocity bound) and P-PS2 (one-step pose/yaw increment
bound). They are nominal-model invariants only; PR02 remains `PROOF-DRAFT`.

## Position-state control-scope audit — 2026-08-13

The active implementation boundary is now explicit in both runtimes:
`state=[x,y,theta,vx,vy,omega]` and
`command=[vx_cmd,vy_cmd,wz_cmd]`. Python exports only
`PositionStateMpc`/`PositionStateNmpc`; the older wheel-torque solver remains
module-local compatibility code for regression tests and is not an active
hardware or paper interface. The final-data packager now rejects
`wheel_torque` for `hardware`, `hardware_in_loop` and `real_offline` sources,
so a physical package cannot be mislabeled as position-state control. MATLAB
`run_studies` executes the position-state
comparison by default; wheel-input foundation studies require the explicit
compatibility flag. Python QA remains `198 passed`, repository validation is
`PASS`, and no manuscript file was edited or built locally.

The simulation schema now fails closed on any confirmatory controller contract
that is not `actuation=body_velocity` with
`state_definition=[x,y,theta,vx,vy,omega]`; MATLAB defaults expose the same
contract. This is an interface guard, not a new empirical result.

## Context-only human-footprint correction — 2026-08-13

The map benchmark now models a moving context position from the active
direction/speed event. Only CCA-NMPC receives the internally propagated future
positions for its chance rows. DWA and MPPI use the footprint at the latest
observed position for candidate scoring; speed and direction remain context
inputs for scoring and local-path triggers. No predicted human path is exported
or drawn on a camera overlay. Regression tests cover both the dynamic context
and the latest-observation baseline footprint contracts; this does not promote development
runs to scientific evidence.

The unreferenced root-level `yolo26s-pose.pt` payload was removed after a hash
audit; the only retained detector candidate is
`models/candidates/yolo26s-pose-candidate.pt` with the manifest-bound SHA-256 recorded in
PR10. The direct recorder now records `lstm_active` and labels every saved
camera overlay as `LSTM=active`, `LSTM=warmup`, or `LSTM=invalid`; this makes
the causal-history warm-up state explicit without drawing a human future path.
This is a code-contract improvement only and does not open PR10, PR12, or PR30.

The MATLAB suite was rerun after the position-state audit: 72 tests passed, with
0 failures and 0 incomplete tests. `TestPositionState` passed both the
six-state body-velocity step and the position-simulation contract. This remains
host software QA, not a confirmatory simulation or physical result.

After the recorder overlay change, the PR30 static no-ROS preflight was
regenerated at `research/metadata/hardware/pr30_entry_preflight_20260813.json`.
It remains `status=PASS` with `admission_status=BLOCKED`; the current report
SHA-256 is `CA921711...`. All interface checks pass, but no device or sealed
hardware package exists.

## Current preflight recheck — 2026-08-13 05:12 UTC

- PR10 web-cohort preflight returned structural `PASS` with
  `admission_status=BLOCKED`: four real Wikimedia assets remain candidate-only;
  no independent annotation, adjudication, detector-overlap review or adequate
  ID/OOD expansion is present.
- PR30 hardware-entry preflight returned static `PASS` with
  `admission_status=BLOCKED`: the no-ROS position-state/body-velocity contract,
  STM bridge, URDF binding and commissioning lock are present, but no device,
  calibration, stage approval or sealed direct package exists.
- The active gap wording is now consistently position-state Mecanum NMPC with
  body-velocity commands. Historical torque-input wording remains only in
  prior-art/search or compatibility records and is not an active physical
  requirement.

## PR10 real-image diagnostic checkpoint — 2026-08-13 05:45 UTC

The four-image Wikimedia candidate was relabelled at the image-presence level
before inference (three positive, one negative) and revalidated. The structural
preflight remains `PASS`/`BLOCKED`; report SHA-256 is
`A74E742609D4CE8E9D3902BACBBF390A770BF830BC4FCF6EB43806ECF4448131`.
`det_eval.py` then ran YOLO26s-pose on CPU. The candidate output is
`experiments/runs/person-detection-web-pilot-20260813/` with manifest SHA-256
`1EFDB631D5F136AC882D421989D9A126FDD14E08F0DC1EA7664E56EBF11FA466`. At
confidence 0.25, the image-level matrix is `[[1,0],[1,2]]`, and the recorded
latencies are P50 307.8 ms, P95 608.6 ms and max 648.6 ms. This is a
four-image, candidate-only diagnostic; the false negative is retained, bbox
AP is unavailable, and PR10 remains admission-blocked pending independent
annotation/adjudication, contamination review and cohort expansion.

## Literature boundary refresh — 2026-08-13

The Google/web and Google-Scholar-oriented refresh added a screening note for
position-level Mecanum MPC, social-force NMPC, model-based RL, uncertainty-aware
predictive safety and ellipsoidal-obstacle MPC:
[[03_Literature/Sources/source-position-state-boundary-20260813]]. The local
Zotero API was reachable and exact-title searches were run read-only; no new
record was imported or promoted to final citation status. The research gap is
unchanged and the source hashes were synchronized in
`research/metadata/focused_literature_audit.json` and
`research/metadata/pr01_gap_decision.json`. This refresh strengthens comparator,
calibration and geometry obligations but does not open any data or experiment
gate.

## CCA-only internal prediction audit — 2026-08-13

The runner now calls and resets the LSTM adapter only for `cca_nmpc`. MPC, NMPC,
DWA and MPPI receive the current context snapshot/footprint but never consume a
future human position. The CCA branch may integrate the causal context velocity
internally for chance rows; no future human path is written to CSV/JSON or drawn
on an image. The focused regression test and full Python suite pass (`199`
tests), Ruff and repository validation pass. This closes an interface ambiguity
only; PR12/PR20 remain design/candidate gates without a sealed real capture,
calibrated checkpoint or confirmatory run.

## Checkpoint-free initial context capture — 2026-08-13

`record_hardware.py` no longer requires an LSTM checkpoint before opening the
devices for the first context-only capture. This removes the circular dependency
where a checkpoint was needed to create the real `context.csv` used to train it.
With no checkpoint, the processor records `lstm_configured=false` and every
overlay explicitly says `LSTM=disabled`; with a checkpoint it retains the
`warmup/active/invalid` states. No human future path is produced, and the
position-state/body-velocity/no-ROS boundary is unchanged. Focused hardware
tests, Ruff, regenerated PR30 static preflight and repository validation pass;
the preflight remains `PASS`/`BLOCKED`, with no device opened or physical package
created.

## Superseded-run purge checkpoint — 2026-08-13

The old v2--v4 position-state pilot payloads under
`experiments/runs/_invalidated/` were physically deleted after verifying that
the directory was inside the workspace and contained only superseded
development outputs. No backup paper, current four-image candidate cohort,
model candidate or active v5 directory was touched. The old run IDs remain in
this note only as provenance labels; they are not reusable data or evidence.

The direct recorder now also contains an optional online CCA-NMPC branch. It
uses the six-state odometry and body-velocity interface, keeps the global path
fixed, regenerates only a local detour on the declared conflict/direction
trigger, and fails to zero command during LSTM warmup, invalid context, solve
deadline miss or STM stop. This is executable integration code only; the
preflight remains `PASS`/`BLOCKED`, with no device package or timing evidence.

## Dynamic-human controller boundary — 2026-08-13

For a moving-person final trial, the only admitted actuator/controller path is
the explicit online `cca_nmpc` branch. The external path remains available for
read-only capture or commissioning and is not a final dynamic-human result.
CCA-NMPC receives the LSTM-derived context and may keep a future-position
estimate in memory for its chance constraints; no predicted human trajectory
is written to CSV/JSON or drawn on any image.

## MATLAB regression recheck — 2026-08-13

MATLAB R2025a `src/matlab/run_tests.m` was rerun after the direct online
CCA-NMPC branch and controller-boundary documentation were synchronized:
`72 passed, 0 failed, 0 incomplete`. Python remains `202 passed`; Ruff,
repository validation and the no-ROS static preflight remain passing. This is
host-software QA only and does not promote the development map pilot, create a
checkpoint, or open physical admission.

The bounded MATLAB position-state smoke was run in memory with 20 rows. The
five controller labels were identical in the context-free nominal scenarios;
this confirms only the six-state/body-velocity entry contract and is not a
dynamic-human benchmark. No MATLAB output package was written or retained.

The direct recorder regression now also covers a moving-person direction change:
CCA-NMPC increments only the local-path generation counter, preserves the
immutable global path and returns only a three-component body-velocity command.
The test asserts that the controller detail payload contains no predicted human
state sequence; Python QA is `202 passed` after this addition.

## LSTM score-loop seed ledger — 2026-08-13

The LSTM runner now supports independent multi-seed training and retains failed
seed reasons instead of silently dropping them. The confirmatory split requires
at least five seeds; development mode can remain one-seed candidate-only. The
selected seed and ledger are hash-bound into the checkpoint and run metadata.
Current `ctx_run.py` SHA-256 is
`26983ED0B34F691AA7DDA7FB41E9AA4F1875153A882864B446D1849C546890DE`.
The implementation regression passes, but no real context capture/checkpoint
exists, so PR12 and all LSTM evidence gates remain open.

## Multi-seed and dynamic-human boundary recheck — 2026-08-13

Full Python QA is now `203 passed`; Ruff and repository validation remain
`PASS`. `ctx_run.py` keeps a ledger for every independent score-loop seed,
selects the maximum validation self-supervised score with a lowest-seed
tie-break, and requires five successfully completed seeds on the confirmatory
split. The current source hash is
`2CB7D67406519593F76B5ABAEF5E839AB9DFB73E195553FAE1385A41E9C1F652`; the
PR30 preflight was regenerated and remains `PASS`/`BLOCKED` because no sealed
hardware package or physical calibration exists.

The moving-person controller boundary remains strict: only online CCA-NMPC
may use an internal future-position estimate. The recorder exports measured
context only and image overlays show current observations, not a predicted
human path. No LSTM checkpoint, detector holdout, or dynamic-human performance
claim is admitted by this checkpoint.

## Position-state dependency cleanup — 2026-08-13

The active map runner and direct recorder now import the shared
`NmpcPrediction` contract from `cca_sim.benchmark_v3`; they no longer depend on
the legacy torque-NMPC module for the position-state execution path. The legacy
module remains available only for regression compatibility. This is an interface
cleanup, not a new controller or evidence result. Python QA remains `204
passed`, and all release gates are unchanged. Source hashes are
`benchmark_v3.py=1F0B3DDBBE2F43CEF362F6A9904D55E04B4D2EC53C8D6ECD48492BC59A43CF43`,
`realtime_nmpc.py=645E9CDF572090D265118D8038E33E339E9A72205A881FD1A0FE6FA0E6413117`,
`map_run.py=474EB9B43CF82EB41DDF7BB50F94185836B7D8800A9E41524D90C9FD7469BD81`,
and `record_hardware.py=ECA10FB21C2A258D3FA606D9DD3A78CA468252F694DAA1BBD113A49CC9AA5F03`.

The subsequent active-entrypoint import-contract regression brings the full
suite to `204 passed`; this is still host-software QA only.

MATLAB R2025a was rerun after the dependency cleanup: `72 passed, 0 failed,
0 incomplete` in `18.9105 s`. No output package was written and no physical
device was opened.

## Provenance-linked hardware analysis checkpoint — 2026-08-13

`analyze_run.py` now summarizes structured `cca_nmpc_step` events in the
separate `analysis.json`: status counts, local-path generation/replan counts,
deadline misses, solve-time/risk/constraint statistics and malformed-detail
counts. It explicitly records `future_human_path_exported=false` and never
modifies the sealed raw package. Full Python QA is `205 passed`; the analysis
script hash is
`1BB6D4B3CB5262BC1BE4AF5E1E19C3378EC39E5560563C778A22613CB30C19AB`.
This prepares the post-run analysis contract but does not create a physical
run, calibration, ground truth or Q1 evidence.

## Minimal active theorem alignment — 2026-08-13

The theory ledger now contains T-PS1 and its proof for the active six-state
position/body-velocity interface. It states only causal internal human-position
prediction, fixed-budget allocation and a one-solve model-internal Gaussian
union bound; it does not introduce inactive torque/mode notation or claim
stability, recursive feasibility or operational probability. PR02 remains
PROOF-DRAFT pending independent review and calibration. The claim-evidence
matrix hashes were refreshed after this append-only theory update.

## Dynamic-human boundary regression — 2026-08-13

The moving-person contract was rechecked across every benchmark comparator.
Only `cca_nmpc` calls the causal LSTM adapter and constructs an internal
future-position estimate for its chance rows. `mpc`, `nmpc`, `dwa`, and `mppi`
receive only the current context snapshot/footprint; none receives a future
human position. The time-series and hardware-overlay contracts still reject
future human-path fields, and the overlay contains only current bbox/keypoints,
position, speed, direction, confidence, and LSTM status. The focused boundary
tests and full Python suite pass (`206 passed`); Ruff, repository validation,
and `git diff --check` also pass. This is an interface regression result only:
no dynamic-human hardware run, LSTM checkpoint, or performance claim is
promoted, and the locked Overleaf paper was not edited or built.

## Targeted literature refresh — 2026-08-13

A new Google/web and read-only Zotero pass checked recent Mecanum hardware MPC,
multisensor crowd MPC with physical validation, and prediction-quality effects
on social navigation. The source note is
[[03_Literature/Sources/source-2026-mecanum-crowd-control-refresh]]; the gap
remains unchanged and the source records remain screening-only because exact
title searches returned no matching Zotero items. This refresh only tightens
the comparator and metric obligations; it does not edit or build the locked
paper and does not open any data, model, simulation or hardware gate.

## Pilot footprint-parity correction — 2026-08-13

The first five-replicate development pilot exposed a real controller/evaluator
mismatch: CCA-NMPC used an internal human-clearance radius below the declared
robot-plus-context footprint. The active position-state controller now receives
the declared `0.92 m` combined clearance in the Python map runner and the direct
hardware wrapper accepts the same value as an explicit map setting (defaulting
only for the uncommissioned scaffold). The superseded v5/v6 payloads were
deleted; only `experiments/runs/context-map-position-state-pilot-20260813-v7/`
remains. In v7, CCA-NMPC records 0/15 collisions and 15/15 safe completions in
the development scenarios, while all baseline traces remain paired. This is a
development diagnostic, not confirmatory evidence: no real LSTM checkpoint,
protocol freeze, independent rerun or paper claim is admitted. Full regression
and repository QA pass against the corrected source. The corrected source
hashes are recorded by the v7 manifest; the run remains development-only.

## Corrected position-state verification — 2026-08-13

After the footprint-parity correction, the complete host-side verification was
repeated. Python reports `206 passed`; MATLAB R2025a reports `72 passed, 0
failed, 0 incomplete` in `19.6123 s` of test time; Ruff, repository contract
validation and `git diff --check` pass. The retained v7 campaign remains a
development-only map diagnostic. It contains no calibrated LSTM checkpoint,
independent annotation, protocol freeze, physical run or paper-ready result.
The moving-person boundary is unchanged: only CCA-NMPC may keep a causal future
position estimate internally; no future human path is generated in the image,
CSV or JSON exports.

## External real-offline context candidate — 2026-08-13

NavWareSet scene 13 was acquired from its public tutorial repository under the
stated CC BY-SA 4.0 license. A single participant track was transformed into
robot-local context without ROS playback. The derived CSV contains 2,498 real
rows and `ctx_run.py` produced 2,405 windows with five completed
self-supervised score-loop seeds, direction confusion matrices, bootstrap
intervals and constant/Kalman baselines. The candidate is recorded in
[[07_Analysis/navwareset-context-candidate-20260813]] and remains outside the
claim register.

This does not open PR11/PR12: the source has no target Mecanum robot, Astra-S or
N10P frames, verified image-to-local calibration, independent ID/OOD split or
target-platform hardware provenance. It is a mechanics check for the causal
LSTM score loop only. No future human path was generated or exported, and the
locked manuscript was not edited.

## Verification rerun after candidate-data refresh — 2026-08-13

The host-side regression was rerun after the external candidate and knowledge
graph updates. MATLAB R2025a reports `72 passed, 0 failed, 0 incomplete` in
`17.3756 s`; the full Python suite exits successfully, Ruff passes, the
repository contract reports `23` schemas, `15` instances, `98` Obsidian notes
and `836` wikilinks, and `git diff --check` passes. The nine retained
NavWareSet/source/run hashes were rechecked with SHA-256 and all match their
provenance manifest. This is reproducibility and software QA only: no protocol
is promoted, no hardware was opened, and the locked paper was not edited or
built. The dynamic-human rule remains unchanged—only CCA-NMPC may retain a
causal future-position estimate internally; the image and exported context
artifacts contain current observations only.

## Literature refresh and knowledge-link closure — 2026-08-13

The Google/web pass added screening-only notes for pedestrian-attention-aware
collision avoidance and robot–pedestrian influence data. Exact-title Zotero
searches returned no local matches, so neither record was imported or used as a
verified citation. The notes are linked from the source index, research-gap
note and project map; repository validation remains `PASS` with `100` Obsidian
notes and `850` wikilinks before the candidate-data note. The refresh tightens interaction-condition,
privacy, annotation and closed-loop evaluation requirements but does not alter
any protocol status or the locked manuscript.

## PR10 web-cohort refresh — 2026-08-13

Two additional real Wikimedia images were downloaded into the separately named
refresh cohort and bound to
`data/manifests/web_person_cohort_refresh_20260813.json`. Structural media,
hash, decode and annotation-binding checks pass, but the admission report is
`BLOCKED`: both records remain unapproved, primary boxes are still pending,
independent annotation/adjudication and pretraining-overlap review are absent,
and the cohort is too small for an ID/OOD evaluation. The endpoint returned
HTTP 429 for subsequent category requests, which is retained as an acquisition
limitation rather than silently treated as completed sampling.

The two-image YOLO26s-pose run is a candidate diagnostic only. It records an
image-level presence matrix and CPU latency, but has no negative image, blind
bounding-box ground truth or localization metric; specificity therefore cannot
be estimated. No future human trajectory is generated, exported or drawn. PR10
remains admission-blocked and no paper claim is changed.
Repository validation after this note reports `23` schemas, `15` instances,
`101` Obsidian notes and `857` wikilinks.

The semantic contract was rechecked after the refresh: the moving person is a
current-observation input; only the `cca_nmpc` branch invokes the causal LSTM
context prediction used internally by the CCA chance rows. MPC, NMPC, DWA and
MPPI receive no future human state. The internal sequence is neither serialized
nor drawn; image overlays remain limited to current pose/context fields. The
full Python suite reports 206 passing tests, Ruff and repository validation
pass, and MATLAB reports 72 passed with zero failures/incomplete tests. These
are software/provenance checks only and do not admit PR10 or any hardware
claim.

## Literature boundary refresh — 2026-08-13 (physical crowd-MPC baselines)

The read-only Google/web and Zotero pass checked DR-MPC, SI-MPC on a physical
robot, a Mecanum A*--velocity-obstacle planner, and an omnidirectional Mecanum
RL/local controller. Exact-title Zotero searches returned no local matches;
the records remain screening-only in
[[03_Literature/Sources/source-screening-refresh-20260813]]. They tighten the
matched comparator, open-loop/closed-loop metric separation and target-hardware
timing requirements but do not change the gap, open a protocol, or edit the
locked paper.

## PR30 hardware-intake recheck — 2026-08-13 22:47 ICT

The Windows host scan found no COM port, CAN adapter, STM bridge, Astra-S/
OpenNI2 device or N10P device. Only an unrelated UVC webcam was present;
`pyserial` and Ultralytics are installed, while OpenNI2 and `python-can` are
not. No device was opened and no command was sent. PR30 remains `REVIEWED` for
design with physical admission blocked; this observation does not create a
hardware result and does not change the locked paper.

After the dependency/documentation refresh, the full Python suite was rerun
(`206` passing tests); Ruff, repository validation (`23` schemas, `15`
instances, `101` Obsidian notes, `863` wikilinks) and `git diff --check` pass.
No simulation, detector, model or physical-data registry was promoted by this
rerun.

## Position-state projected-covariance checkpoint — 2026-08-13

The active CCA-NMPC position-state branch now converts each predicted
human-position covariance into a one-dimensional normal-direction margin,
then adds the fixed-budget normal quantile to the clearance radius. This is
implemented only in `PositionStateNmpc._risk_adjustment`; MPC, NMPC, DWA and
MPPI do not receive the internal future estimate. The internal prediction is
not serialized, exported as a path, or drawn on the camera image. Global path
geometry remains immutable and only the local-path generation counter may
change when the observed person moves.

The regression test checks that a larger projected covariance produces a
larger CCA constraint margin. The latest host checks are Python `207` passing
tests, Ruff `PASS`, repository validation `PASS` and `git diff --check` `PASS`;
MATLAB remains `72 passed, 0 failed, 0 incomplete` from the unchanged
position-state implementation. This is a software-contract checkpoint only:
the covariance is still a development candidate, no calibration or sealed
hardware capture exists, and no evidence gate is promoted.

## Pilot v8 failure checkpoint — 2026-08-13

The fresh five-replicate map campaign with the candidate LSTM inside CCA-NMPC
completed as a development run. CCA-NMPC recorded 10 collision episodes out of
15 paired units and a safe-completion rate of `0.333`; the candidate checkpoint
declares `calibration.status=not_fit` and has no independent ID/OOD holdout.
This is retained as a failure-analysis artifact in
[[07_Analysis/context-map-position-state-pilot-context-lesson]], not as a result
that supports superiority or safety.

The control-entry contract was tightened after this failure: confirmatory map
runs and online hardware CCA now reject an LSTM checkpoint unless its
calibration is independently fitted on the declared calibration split. Pilot
runs may still load an uncalibrated checkpoint only to expose failure modes;
they remain candidate-only. The no-human-trajectory-overlay and fixed-global/
local-only path contracts are unchanged.

The calibration-gate regression adds two Python tests; the latest focused
control/LSTM tests pass, and repository validation now reports `102` Obsidian
notes and `871` wikilinks. This remains implementation QA, not calibration or
hardware evidence.

## Pilot v9 OOD-bound recheck — 2026-08-13

The same five-replicate moving-person campaign was rerun after the context
speed bound. The candidate LSTM output was rejected as OOD and CCA-NMPC used
the current observation; its descriptive collision count became `0/15`, safe
completion `0.667`, and minimum context margin `0.0875 m`. This is a
fail-closed software recheck, not a calibrated-LSTM or superiority result.
The v8 failure and v9 recheck are linked from
[[07_Analysis/context-map-position-state-pilot-fallback-lesson]].

The OOD-bound regression is now covered by the full Python suite (`211` tests
collected and passing); Ruff and repository validation remain `PASS`. This
still records software behavior only and does not admit the candidate LSTM.

Final host recheck for this cycle: Python `211` tests pass, MATLAB `72 passed,
0 failed, 0 incomplete`, Ruff `PASS`, repository validation `PASS`, and no
device was opened. These checks do not promote PR02, PR10--PR12, PR20--PR21 or
PR30 to evidence status.

## Moving-person controller boundary reaffirmed — 2026-08-13

The active dynamic-person contract is now explicit: the person moves in the
scene, but only the CCA-NMPC branch is admitted as the controller for a final
moving-person trial. The LSTM/context module may provide CCA-NMPC with a causal
internal future-position sequence for its chance constraints. MPC, NMPC, DWA
and MPPI remain comparison baselines only; they receive the current context
snapshot and never receive that future sequence. The sequence is runtime
memory only: it is not exported to CSV/JSON and is not rendered on a camera
image. The overlay contains the current detection/keypoints, position, speed,
direction and validity state. The global path stays fixed; only the robot's
local path may be regenerated on a registered context conflict or direction
change. Focused regression tests for this boundary pass; this is a protocol
decision and software check, not a physical result.

## Full `rai_robot_urdf` intake and single hardware entrypoint — 2026-08-13

The direct hardware path now has one operator entrypoint,
`scripts/python/tools/hardware_entry.py`. Before capture it parses the complete
`rai_robot_urdf` mini-Mecanum source: all links/joints, visual and collision
meshes, the four wheel origins, camera/laser mounts, the sensor asset library,
and the mini-Mecanum xacro wheel radius. The generated intake binds both source
files and mesh assets by SHA-256. It derives `r=0.0363 m`,
`L/2=0.08595 m`, `W/2=0.099012 m`; camera mount
`(0.107095,0.000317,0.21) m` with pitch `-0.349066 rad`; laser mount
`(0.031631,0.000091,0.095024) m`; and the URDF mass-field sum `1.049433 kg`.
The DAE/STL sensor-library files are recorded as geometry assets only and do
not substitute for measured Astra-S/N10P identity.

`hardware_entry.py inspect` produced
`research/metadata/hardware/mini_mec_intake_20260813.json` with status
`no_serial_device_detected`. `prepare` emits a path-independent config bound to
the URDF source; `schedule` emits a zero-terminated body-velocity CSV; and
`record` forwards one final no-ROS capture path to `record_hardware.py`, with
`--confirm-motion` required before any nonzero command. Focused hardware tests,
full Python QA and Ruff pass; the static PR30 preflight remains `PASS` with
admission `BLOCKED` because no physical device, calibration, safety approval or
sealed package is present. The final host run for this entrypoint change is
Python `214` passing tests, Ruff `PASS`, repository validation `PASS`, and
hardware-entry preflight `PASS/BLOCKED`. Paper remains untouched.
The intake also records `rai_robot_urdf` package name/version, package/CMake
hashes and the installed `meshes`/`rviz`/`urdf` directories plus available
URDF variants; the selected physical model remains `mini_mec_robot`.
The intake also hashes the supplied udev rule source; it records the legacy
`/dev/rai_controller` alias as a reference and does not install or assume that
rule on the target computer.

## URDF link-mesh coverage recheck — 2026-08-14

The `rai_robot_urdf` intake was rerun after adding the omitted
`controller_link.STL` to the selected mini-Mecanum mesh inventory. The source
coverage now includes the base, controller, all four wheel links, camera and
laser visual/collision assets, in addition to the generic sensor-library
records. This is a provenance/intake correction only; generic `astra.dae`,
`lds.stl` and `r200.dae` assets do not establish the physical Astra-S/N10P
identity or calibration.

Focused and full Python QA remain `214 passed`, Ruff and repository validation
remain `PASS`, and static PR30 preflight remains `PASS/BLOCKED`. No device was
opened and no physical package or paper claim was created.

## LSTM overlay provenance correction — 2026-08-14

The direct frame overlay now displays the local LSTM checkpoint path in a
wrapped `LSTM_PATH=...` label. Unconfigured captures explicitly show
`LSTM_PATH=<not-configured>`; warmup and invalid frames therefore cannot be
mistaken for active model inference. The path is provenance text only: no
future human trajectory is exported or drawn.

Focused hardware/runtime tests and Ruff pass after the correction. No device
was opened and PR30 admission remains `BLOCKED`.

## Static Internet-image overlay provenance recheck — 2026-08-14

`det_eval.py` now accepts `--lstm-checkpoint` when a current-snapshot context
overlay is supplied. It verifies the checkpoint SHA-256 against each
`model_sha256` record and prints the resolved local path on every gallery image;
without the argument it prints `LSTM_PATH=<not-provided>`. The loader still
rejects future-position, trajectory and path fields. Full Python QA remains
passing and no detector or dataset admission status changed.

## Focused literature refresh — 2026-08-14

A current Google/web pass checked OA-MPC, model-free safety-critical MPC,
disturbance-observer MPC for Mecanum robots, and MPC-based dynamic movement
primitives. The source-level consequences are recorded in
[[03_Literature/web-verified-gap-sources]]: occlusion-aware safety, model-free
safety, Mecanum disturbance rejection and learning-plus-MPC obstacle avoidance
are all adjacent prior art. The defensible gap remains the transparent
fixed-budget context allocator inside CCA-NMPC for the position-state Mecanum
platform, not perception, generic MPC, self-supervision or safety claims in
isolation.

Exact-title Zotero searches returned no local matches on 2026-08-14. This is a
screening update only: no Zotero item, dataset, model, experiment or manuscript
was modified, and no protocol was promoted.

## Position-state MATLAB export correction — 2026-08-14

The active MATLAB entrypoint was corrected so that
`run_studies(Profile="bounded", ExportResults=true)` exports the six-state
position contract directly. It no longer forces the legacy compatibility
studies before export. The active export writes one summary CSV, one
controller/scenario CSV with
`[x,y,theta,vx,vy,omega]` and `[vx_cmd,vy_cmd,wz_cmd]`, and a hashed JSON
manifest marked `candidate-development-only`. No torque/current channel is
written. The older Gate-A exporter remains available only when the explicit
`IncludeCompatibilityStudies=true` flag is supplied and is not part of the
active physical interface.

Focused MATLAB export tests and the complete MATLAB suite pass (`73 passed,
0 failed, 0 incomplete`). The complete host QA for this correction is Python
`214 passed`, Ruff `PASS`, repository validation `PASS`, and `git diff --check`
`PASS`. This is an interface/regression correction only: no simulation result
was promoted, no device was opened, and PR30 admission remains `BLOCKED`.

## Current control/perception boundary refresh — 2026-08-14

A further primary-source check re-read the 2026 crowd-MPC paper by Gravina et
al., the 2026 Mecanum hybrid-control paper by Pham and Han, and the official
YOLO26-pose documentation. The records reinforce three restrictions: multisensor
human-aware MPC and real-robot validation are already prior art; Mecanum MPC and
slip compensation are not standalone novelty; and YOLO26s-pose documentation
defines a measurement interface but cannot establish Astra-S/N10P accuracy or
target-hardware timing. The gap remains the matched fixed-budget CCA interface
comparison. No Zotero record, dataset, model, experiment, protocol status or
manuscript was promoted.

## Full-URDF footprint parity correction — 2026-08-14

The active Python map contract no longer uses the former generic `0.32 m`
robot radius. It is now bound to the complete `rai_robot_urdf` intake for
`mini_mec_robot`, including the base, controller, four wheel meshes, camera
mount and laser mount. The conservative planar bounds are half-extents
`(0.1348093152, 0.1150890935) m` with circumscribed radius `0.1772541986 m`;
the source URDF SHA-256 is checked at map-run import and copied into every
manifest. DWA and MPPI receive the same footprint explicitly and the human
margin uses the contract's `0.34 m` person radius.

This correction makes the geometry used by the local-path baselines traceable
to the supplied robot description. It invalidates comparison with candidate
map outputs generated under the former radius; no candidate output is
promoted, no simulation campaign is rerun in this checkpoint, and physical
dimensional validation remains pending.

The post-correction host check is Python `220` passing tests, MATLAB R2025a
`73` passing tests, Ruff `PASS`, repository validation `PASS`, and hardware
preflight `PASS/BLOCKED`. These are contract and regression checks only; they
do not admit simulation, calibration, or physical evidence.

## Online CCA clearance parity — 2026-08-14

The direct no-ROS `OnlineCcaNmpc` path previously retained the superseded
`0.92 m` default clearance. It now receives the URDF-derived footprint from
the prepared hardware config and derives the position-state human clearance
as `0.1772541986 + 0.60 m`; an explicit map value inconsistent with that
radius is rejected before device opening. The runtime metadata records the
same footprint. This closes an online/configuration mismatch only; no device
was opened and no motion result was generated.

## Shared context-score parity correction — 2026-08-14

The active Python map prediction now calls the shared five-feature context
definition and fixed logistic score rather than the former two-term proxy.
The regression suite checks all prediction stages against `ContextScorer`;
224 Python tests are collected and the focused score-policy suite passes. This
updates implementation parity only. It does not promote a simulation result,
calibrated LSTM checkpoint or physical run; PR02 and PR30 gates remain open.

## Position-state candidate-rollout checkpoint — 2026-08-14 correction

The active implementation is the compiled C++ bounded candidate rollout, not a
direct finite-horizon multiple-shooting solver. It uses six-state dynamics and
body-velocity commands, applies the CCA reduced risk correction from the
validated nominal robot geometry, clips the command and records the finite
rollout. The reserved `maximum_risk_slack_m=0` field is not an optimized slack,
and no nonlinear-program residual is exposed. The no-ROS adapter shares the
five-feature context score with the map path. Host QA remains green; this does
not advance PR02, PR20, PR21 or PR30 because chance-row geometry, calibration,
solver evidence and hardware evidence remain open.

## Clean-reset purge checkpoint — 2026-08-14

The user-requested reset was applied after an exact-path inventory. All local
candidate media/manifests, NavWareSet raw and processed payloads, development
map pilots, detector diagnostics, LSTM output/checkpoint, YOLO26s-pose weight,
and generated preflight artifact were deleted (55 files; 59,260,346 bytes).
The four registries are empty. The audit is
[[07_Analysis/development-artifact-purge-20260814]]; the next acquisition must
use a new protocol freeze and run ID. Paper/Overleaf and the backup snapshot
were not edited.

Host QA after the reset is Python `226` tests passed, MATLAB R2025a `73`
passed with zero failures/incomplete cases, Ruff `PASS`, repository validation
`PASS` (23 schemas, 15 instances, 104 notes, 908 wikilinks), and
`git diff --check` `PASS`. These checks do not open PR10/PR20/PR30 or admit any
result.

## Covariance-domain parity checkpoint — 2026-08-14

The position-state chance-row implementations in Python and MATLAB now reject
non-finite, asymmetric and materially non-positive-semidefinite relative
covariance before projection. Focused regression cases pass. The full current
host QA is Python `228` tests and MATLAB `74` tests with zero failures or
incomplete cases; Ruff, repository validation and `git diff --check` are green.
This is an input-domain and parity guard only. Covariance provenance, frame/time
alignment, calibration, zero-slack residual evidence and independent review
remain open; no dataset, simulation result or hardware package is admitted.

## LSTM interface-theory checkpoint — 2026-08-14

The theory contract now writes the standard gated LSTM recurrence, the velocity
head, and the four fixed-axis direction score in one compact notation. The
notation is synchronized with `src/python/cca_ai/ctx_lstm.py`: the encoder sees
only a causal history window, the self-supervised target is the next observed
velocity, and the runtime adapter returns context velocity/speed/direction
without decoding or exporting a human future path. This closes only the
notation/source-interface gap (PO-016); it does not close training, ID/OOD
metrics, calibration, target-hardware timing, or any controller probability
claim. PR02 remains `PROOF-DRAFT`, PR12 remains `REVIEWED`, and no model or
dataset artifact is admitted.

## LSTM classification-evidence guard — 2026-08-14

PR40 now distinguishes box detection metrics from classification evidence at
the machine-contract level. When `lstm_context.enabled=true`,
`schemas/evaluation-config.schema.json` requires the direction task to be
enabled, requires `confusion_matrix_required=true`, and requires hashed
ontology, decision-rule and independent ground-truth references. The template
remains intentionally planned/disabled until the real context dataset and
labels are frozen. The guard is covered by
`test_evaluation_schema_requires_lstm_direction_confusion_contract`.

Current hashes: schema
`E2DF64709B31E419C0F721149540B26EF0DC985F2BD0DE5711E4DBF4C17B17AA`, PR40
`9CF7CD4EF7BE662C6CE2AA41659DD89BB44F2D51548A5E13A3E4BA99FB22B2BE`, and
the repository check remains `PASS` (23 schemas, 15 instances, 104 notes,
911 wikilinks). This is a design/validation gate only; no LSTM result,
confusion matrix or paper claim is admitted.

## Direct STM serial capture checkpoint — 2026-08-14

The first hardware-facing implementation is now the compact no-ROS
`scripts/python/tools/stm_experiment.py`. It binds the legacy STM32 serial
frame documented by `src/ros2/turn_on_rai_robot` through the tested Python
decoder, writes the six-state position CSV, command CSV, events and
hash-bound capture/manifest files, and sends a zero command on every exit
path. Nonzero motion is fail-closed without an explicit actuation flag and a
safety record verifying emergency stop, remote disable and watchdog.

The URDF intake was relabelled `cad_reference_only`; no CAD wheel radius,
wheel span or footprint is promoted to the runtime. `hardware_entry.py
prepare` now requires a separate measured `cca-physical-robot-v1` file for
full-stack preflight. The direct STM bring-up can therefore collect raw
telemetry without inventing physical dimensions, while the full
Astra-S/N10P/CCA-NMPC run remains blocked until the physical specification,
calibration, H0 gate and target-hardware manifest are supplied. Tests and
repository checks pass; no device was opened and no CSV/JSON result exists.

Implementation hashes: `stm_experiment.py`
`F6F28CE85368E23849D78FDD1810DB25C415B91ABC5463C1379B8CA2E02DC823`,
`cca_hardware.py`
`699511D6178423FFDE85424282032B191A970CF90DC21683ED51B80ED97F5371`, and
the CAD/reference intake
`B69F8373C28E17549CD6F8602D32C9BE8BD98FA299B60F3489C522EFE0E1C602`.

## MATLAB position-state comparator correction — 2026-08-14

`cca.Simulation.simulatePosition` no longer sends the same nominal command law
for every comparator. The position-state smoke path now has separate bounded
implementations for MPC, candidate-search NMPC, DWA velocity sampling, MPPI
sequence sampling and CCA-NMPC candidate selection. The CCA branch is labelled
`CCA_NMPC_CONTEXT_NOT_SUPPLIED` in this MATLAB interface smoke because context
is supplied by the Python dynamic-context path; it is not presented as a
validated human-aware controller result.

The complete MATLAB R2025a suite passes `74` tests with zero failures or
incomplete cases. A five-controller in-memory smoke produced finite six-state
trajectories and controller-specific status labels; no output package was
written, no simulation result was promoted, and no device or paper file was
opened or modified. The matched dynamic-human benchmark remains the Python
map path under PR20/PR21.

## STM stop-flag fail-safe — 2026-08-14

The direct STM recorder now latches the STM-reported stop flag before choosing
the next command. A latched stop forces a zero body-velocity command, records
`stm_stop_latched`, writes the final telemetry row and exits through the normal
zero-command tail. A regression fixture covers this path. This is a software
fail-safe check only; e-stop, watchdog and wheel-loop verification still must be
performed on the target robot before any actuation.

The post-change Python suite passes `237` tests, Ruff and repository validation
remain `PASS`, and no capture directory was created.

## Pre-command STM stop latch in full recorder — 2026-08-14

The full `record_hardware.py` path now checks the latest STM telemetry stop flag
before selecting and sending each command. A previously asserted flag therefore
cannot be followed by one stale nonzero command. The event is recorded once,
the latch remains active, and all subsequent commands are zero. The focused
hardware-entry and STM tests pass; the full Python suite collects and passes
`239` tests. Updated `record_hardware.py` SHA-256 is
`0DCDAEB01D45E2135668DE6FB98E07C1AC768C8198FE00D7B9A2AB792960411C`.

### Full-recorder motion safety gate — 2026-08-14

The direct full recorder and `hardware_entry.py` now require a validated
`--safety-record` for any requested motion. The record must set approval,
emergency-stop, remote-disable and watchdog checks to true. The no-device
preflight validates this before device access and stores only the record path
and digest in runtime metadata. The current preflight report hash is
`A8337AD6F08CE46C9CD5D42622DB7FB3280A53EC056A8BF3CF11B876EDEBBADA`;
status is `PASS`, admission remains `BLOCKED`, and no hardware package exists.
The full Python suite passes `239` tests, Ruff and repository validation pass.
This is a software fail-safe correction only; no device was opened and PR30
admission remains `BLOCKED`.

Current source hashes after this gate are `record_hardware.py`:
`B60AF3E7AE19DB67D4F8CE8D5E9D287C1BA008A4C42346BCF8B23A249C55C89C` and
`hardware_entry.py`:
`3F6BFC31811F277E2B8C1F0756D2264498C7DB0495392BEAB1B2B950635F7393`.

## C++ low-level transport split — 2026-08-14

The transport boundary was re-audited after the requirement that STM
communication should not be implemented entirely in Python. The active C++
core now owns the STM32 serial frame encoder/decoder and the CCA CAN CRC/frame
codec; `stm_probe` is the direct no-ROS commissioning executable. Python keeps
the higher-level camera/LiDAR acquisition, self-supervised LSTM, CCA-NMPC,
calibration and evidence packaging. This is an implementation split, not a
hardware run: the current host has no serial device and no C++ compiler, so the
new C++ target still requires target-side build and H0 verification before
motion.

The source reference package used by the hardware intake was restored under
`src/ros2` from the existing CAD/ROS reference workspace: all 37 URDF files,
the selected mini-Mecanum meshes and sensor assets, the xacro sensor contract,
and the legacy STM bridge source. This restores source provenance only; no
dataset, checkpoint, simulation result or paper file was restored.

The C++ Release build produced `libcca_ai_transport.so` and `stm_probe`; CTest
passed. Python QA remains green and the new static preflight report is
`research/metadata/hardware/pr30_entry_preflight_20260814_cpp.json` with
`status=PASS` and `admission_status=BLOCKED`. No target serial port was opened.

## `cca_shared` C++ boundary — 2026-08-14

The `cca_shared` audit is now explicit: CRC-8, signed CAN quantisation and
fixed-frame encode/decode select the C++ shared library on Linux, with an
explicit Python fallback for hosts without that library. Calibration,
contract loading, forbidden-field checks, hashing and manifest work remain
Python. C ABI round-trip, CTest, 239 Python tests, Ruff and repository checks
pass. This closes only the implementation-allocation checkpoint; PR30 remains
`PASS/BLOCKED` and no hardware result is admitted. See
[[07_Analysis/cca-shared-implementation-audit-20260814]].

The same split now covers the five-feature CCA context score: the C++ core is
exposed through `cca_context_score`, and `cca_ai.context` selects it on the
Linux target while retaining `CCA_CONTEXT_BACKEND=python` as an explicit
fallback. The C++/Python score and feature vector agree in the focused smoke;
the 64-case finite parity sweep had maximum absolute error `4.44e-16`. This
remains software parity evidence, not a hardware or scientific result.

## Real-image cohort acquisition — 2026-08-14

The fresh Internet-image acquisition contains seven Wikimedia candidates: one
calibration scene, two test-ID person scenes, two test-OOD person scenes and two
empty controls. `validate_web_cohort.py --manifest-only` passes the
manifest/hash/decode/rights checks and writes
`research/metadata/pr10-web-cohort-preflight-20260814.json`; admission remains
`BLOCKED` because no independent blinded annotation, adjudication, privacy
review or pretraining-overlap review exists. This is candidate data only and
does not create admissible detector evidence. Details:
[[07_Analysis/web-cohort-acquisition-20260814]].

## YOLO26s-pose candidate checkpoint — 2026-08-14

The stale external diagnostic was purged before replay. The official external
`yolo26s-pose.pt` asset is now retained at
`experiments/runs/person-web-inference-20260814/yolo26s-pose.pt` with SHA-256
`A083ADB42303728AE14C4BD6BD56D80DA46F82FB2564DBD6F31DCC92EA321646`.
The checkpoint is a measurement interface only; no local training, detector
claim or target-device timing has been created. A scene-tag diagnostic package
exists at `experiments/runs/person-web-inference-20260814/inference/`; its
matrix `[[2,0],[0,5]]` and CPU timing are descriptive only (P50/P95/max
`313.43/505.37/544.43 ms`). Gallery images show
the local LSTM path with `context=not-provided`, without a fabricated context
snapshot or future trajectory. The model registry stays empty until the
candidate data pass receives blinded annotation/adjudication and the licensing,
privacy, pretraining-overlap and held-out-cohort gates are reviewed. See
[[07_Analysis/yolo26s-pose-candidate-acquisition-20260814]].
The checkpoint-only CPU sanity check returned the required `[N,17,2]` pose
shape for all seven images; its box counts are diagnostic outputs, not
evaluation evidence.

## COCO8-pose provider-label diagnostic — 2026-08-14

The official public COCO8-pose archive contributed four validation images and
14 provider person boxes under `data/raw/coco8-pose-20260814/`. A fresh
YOLO26s-pose CPU evaluation at confidence `0.25` and IoU `0.5` recorded TP
`11`, FP `1`, FN `3`, precision `0.9167`, recall `0.7857`, F1 `0.8462`, mean
matched IoU `0.8562`, and P50/P95/max latency `324.91/573.17/603.18` ms. The
image-level matrix `[[0,0],[1,3]]` has no negative images, so specificity is
not estimable. The boxes are provider labels created before prediction, not
independent human annotation/adjudication. The preflight report
`research/metadata/coco8_pose_preflight_20260814.json` is `PASS` with
`admission_status=BLOCKED`; the metrics remain candidate-only and are not
available for claims or model selection. See
[[07_Analysis/yolo26s-pose-candidate-acquisition-20260814]].

## Current MATLAB regression recheck — 2026-08-14

MATLAB R2025a `src/matlab/run_tests.m` was executed after the current repository
changes: `74 Passed, 0 Failed, 0 Incomplete` in `32.2397` seconds. No
simulation export, result package or manuscript file was written. This is
software QA only; PR20/PR21 remain design-reviewed and no confirmatory
simulation evidence is admitted.

The no-device PR30 static validator was regenerated at
`research/metadata/hardware/pr30_entry_preflight_20260814_cpp.json` after the
candidate/model and C++ boundary updates. It remains `status=PASS`,
`admission_status=BLOCKED`, report SHA-256
`2C9985AF4854345390F15EA9F7866B3D1F096A449D6F2B40EB1B364E9F573079`; no
serial device or actuation command was accessed.

## Simulation learning split refresh — 2026-08-14

The replacement campaign was rerun from scratch after replacing the
chronological-only split. Its simulation-only capture contains 9,600 rows in
40 episode groups with frozen train/validation/calibration/test-ID/test-OOD
assignments and 1,176 usable windows per partition. The five-seed LSTM score
loop fit temperature only on the calibration partition; test-ID/test-OOD
self-supervised scores were `0.837`/`0.792`. The score/penalty Q-learning policy
and an independent 30-unit paired map benchmark bound to the current
400 x 400 mm physical specification were rerun with score tuning disabled.
All artifacts remain `candidate-development-only`; the simulation calibration
sidecar does not open the real-capture, protocol-freeze or hardware gate. See
[[07_Analysis/simulation-learning-campaign-20260814]] and
[[07_Analysis/experimental-analysis]].

## Development execution status refresh — 2026-08-14 continuation

PR12, PR20 and PR21 now record `DEVELOPMENT-EXECUTED / UNRELEASED` in the
current table. This is a status correction for the fresh simulation campaign,
not a promotion to `VERIFIED`: the LSTM was self-supervised from next observed
velocity, the local-path policy used score/penalty Q-learning, and the five
controller branches were paired on the fixed-global/local-trigger map contract.
The replayed artifacts remain simulation-only and candidate-only. A protocol
freeze, independent confirmatory analysis, real context provenance and hardware
evidence are still separate gates.
