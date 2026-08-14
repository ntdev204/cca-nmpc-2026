---
type: theory-parity-audit
status: candidate
evidence_status: software-qa-only
paper_edit: prohibited
---

# Theory–implementation parity audit — 2026-08-13

## Scope

This audit checks whether the written T1–T6 contracts have matching software
paths. It is not an independent mathematical review and it does not promote a
probability, stability, real-time or hardware claim.

## Checks

| Contract | Active implementation | MATLAB path | Result | Boundary |
|---|---|---|---|---|
| T1–T3 fixed-budget allocation | C++ core `src/control/src/controller.cpp` (called through `src/runtime/controller.py`) | `matlab/+cca/Risk.m` | software tests pass | finite-precision/fixed active set only |
| T4 Gaussian half-space row | C++ risk-row implementation in `src/control/src/controller.cpp`, with the Python ABI adapter in `src/runtime/controller.py` | `matlab/+cca/Nmpc.m` | row/gradient, zero/near-singular covariance and sampled ellipse-support tests pass; Python/MATLAB probability eligibility now fails closed | independent geometry review, covariance provenance and zero-slack evidence remain open |
| T5 mode/accounting and union bound | prediction contract `src/simulation/model.py` and scenario assembly in `scripts/python/tools/map_run.py` | `matlab/+cca/Risk.m` and `matlab/+cca/Scenario.m` | accounting tests pass | model-internal one-update bound only; no `Pr_star` or mission-wide claim |
| T6 feasible-candidate selection | C++ candidate selection in `src/control/src/controller.cpp`, called through `src/runtime/controller.py` | `matlab/+cca/Simulation.m` candidate command selection | regression tests pass | one solve; no recursive feasibility, deadline or fallback guarantee |

## Context-interface boundary

The five-feature sigmoid score in `matlab/+cca/score.m` is the primary
MATLAB simulation implementation of the PR02 context specification; the
per-human/per-stage maximum in `cca.Scenario` supplies the mode-invariant group
score required by the allocator. `src/ai/context.py`, the direct
hardware recorder and the current Python map runner now share the same feature
map and fixed logistic coefficients. The horizon-level regression checks this
definition at every stage. This is a software-definition parity result only;
calibration and operational-probability evidence remain open.

## Evidence run

- Focused Python risk/NMPC/context-contract tests: pass.
- Repository schema/link/hash audit: pass (`repo_check.py`).
- Ruff static check: pass.
- MATLAB unit/property suite rerun on 2026-08-13: 72 passed, 0 failed and 0
  incomplete (25.2537 s testing time); this is host software QA and not a
  physical or scientific campaign.

The active position-state implementation is covered separately by
`TestPositionState` and the Python position-state model tests. These checks
cover interface shape and finite propagation only; they do not promote the
position model to a calibrated plant or prove closed-loop properties.

## Causal human-position interface checkpoint — 2026-08-13

The active dynamic-context runner now has one explicit parity check for
\(\hat p^h_{k+\ell|k}=\hat p^h_k+\ell\Delta t\hat v^h_k\). The test verifies
the expected position sequence from the current snapshot and confirms that
only the CCA-NMPC branch calls the internal prediction builder. The time-series
schema contains no future/path trajectory fields, and the v5 manifest records
`human_prediction_overlay=false` and
`ground_truth_human_trajectory_provided_to_controller=false`. This is a causal
interface and artifact-boundary check only; it does not validate prediction
accuracy, calibration, collision probability or human behavior.

## Edge-case continuation — 2026-08-13 05:18 ICT

The T4 implementation was rerun with a zero covariance and a rank-one
near-singular covariance. Both Python and MATLAB accepted the finite
deterministic limit and produced finite chance rows with no relaxation. The
Python suite passed `154` tests, the MATLAB suite passed `69` tests, Ruff and
`repo_check.py` passed, and `git diff --check` was clean. This closes the
   zero-σ numerical test obligation only; it does not establish Gaussian
calibration, footprint containment, independent geometry review, or an
operational probability claim. The protocol remains `PR02=PROOF-DRAFT`.

The source/test hashes for this checkpoint are recorded in
[[07_Analysis/protocol-status-20260813]].

The sampled support-boundary check closes only a finite geometry sanity check;
it is not an independent proof review or a collision-probability result.

The Python numeric support helper is recorded in the implementation snapshot;
its addition does not alter the CasADi chance-row model or the stated claim
boundary.

## Open obligations

1. Independent sign/geometry review of the half-space containment and footprint
   mapping.
2. Populate and independently verify covariance provenance, calibration
   eligibility and zero-slack residual records for every chance row.
3. A reviewer other than the implementer for the proof ledger.
4. The Python eligibility gate now requires all provenance fields and a
   SHA-256 calibration record; this is an implementation guard, not evidence
   that those records exist for the active study.
5. Do not change `PROOF-DRAFT` to `VERIFIED` until the above obligations and an
   immutable code snapshot are recorded.

## Position-state derivation checkpoint — 2026-08-13

The active six-state/body-velocity update now has a separate derivation note at
[[05_Theory/position-state-derivation]]. P-PS1 proves the componentwise velocity
bound for the first-order velocity blend, and P-PS2 bounds one-step pose/yaw
increments. The proof uses only the declared discrete model and command bounds;
it does not close actuator identification, delay augmentation, recursive
feasibility, stability, physical safety or any operational probability claim.

## Targeted second-pass QA — 2026-08-13

The risk-allocation, real-time NMPC and contract suites were rerun together
(`63` tests passed). This confirms the current Python implementation invariants
after the protocol/literature refresh. It does not close the independent proof,
geometry, calibration or operational-probability obligations; PR02 remains
`PROOF-DRAFT`.

## Bounded mathematical self-audit — 2026-08-13 00:31 UTC

This is a derivation check by the implementation author, not the independent
control reviewer required by the protocol. The five active contracts were
reduced to the following checks:

1. For (B=\bar\varepsilon-M\varepsilon_{\min}>0), positive softmax weights
   give (\sum_e[\varepsilon_{\min}+Bw_e]=\bar\varepsilon) and preserve the
   floor. The sign of (\partial\varepsilon_e/\partial c_j) confirms that a
   larger context score receives a smaller allowance for (\beta>0).
2. With (Y=n^\top\delta\sim\mathcal N(0,\sigma^2)), the strict
   half-space violation is (Y>a), where
   (a=n^\top(p_r^0-\mu)-d_{\rm req}). Thus
   (a\ge\Phi^{-1}(1-\varepsilon)\sigma) is the correct one-sided model
   condition; when \(\sigma=0\), (a\ge0) makes the strict event empty.
3. The mixture step requires a complete mode partition and the Boole step is
   applied only to the frozen groups in one solve; neither step implies a
   closed-loop or mission-wide probability.
4. Python and MATLAB now expose the same chance-row variance floor
   (`1e-12 m^2`) through configuration. This removes the prior hidden
   implementation mismatch at zero/near-singular covariance; it is a numerical
   regularizer, not a new theoretical assumption.

The self-audit closes only this software/notation consistency item. It does
not close independent sign/geometry review, calibration provenance, zero-slack
residual records, or the reviewer gate. PR02 therefore remains `PROOF-DRAFT`.

## Numeric fail-closed amendment — 2026-08-13

The fixed-budget allocator now rejects non-finite logits before the shifted
softmax in both Python and MATLAB. This covers floating-point overflow caused
by an otherwise finite but excessively large `beta`; it prevents an invalid
snapshot from silently becoming a uniform allocation. The new Python regression
test covers this boundary. The finite-precision contract is therefore
fail-closed, while the real-arithmetic T1--T3 derivation and the independent
proof/calibration gates are unchanged.

## Active theorem alignment — 2026-08-13

The active theory ledger now includes T-PS1 and its proof: a minimal
six-state/body-velocity statement that combines causal internal human-position
prediction, fixed-budget allocation and a one-solve model-internal Gaussian
union bound. This avoids importing inactive multimode/torque notation into the
active interface. It is a scope-alignment artifact, not an independent proof
review or operational probability evidence; PR02 remains PROOF-DRAFT.

## Links

[[05_Theory/theorems]] · [[05_Theory/proofs]] · [[05_Theory/proof-obligations]] ·
[[07_Analysis/completion-audit]] · [[01_Governance/claim-register]]

Related hub: [[00_MOC/project-map]]

## Projected-covariance margin parity checkpoint — 2026-08-13

The active Python position-state CCA branch now applies the same scalar
projection used by the theory note, followed by the fixed-budget quantile
margin:

$$
\sigma_\ell=\sqrt{\max\left(0,n_\ell^\mathsf{T}\Sigma_\ell n_\ell\right)}.
$$

The
implementation is `PositionStateNmpc._risk_adjustment` and the regression
test compares zero covariance with a finite diagonal covariance. MATLAB is
unchanged because its position-state contract does not yet admit a calibrated
LSTM covariance stream. Therefore this is interface parity for a candidate
software path, not a claim of Python--MATLAB experimental equivalence.

The CCA-only and no-overlay conditions remain enforced: baselines do not call
the internal predictor, and no predicted human-position sequence is written
to image, CSV or JSON path fields. The current host regression is `207`
passing Python tests and `72` passing MATLAB tests; independent proof review,
calibration and hardware capture remain open.

## Position-state/no-torque interface parity — 2026-08-14

The MATLAB position-state export now carries the same active interface as the
hardware and Python branches: state
`[x,y,theta,vx,vy,omega]` and body-velocity command
`[vx_cmd,vy_cmd,wz_cmd]`. The export path does not require or serialize torque,
wheel-current or wheel-input fields. Legacy torque-oriented MATLAB routines
remain only as explicit regression-compatibility code and are not called by
the default position-state entrypoint. The test suite checks both the six-state
shape and the absence of torque-named export artifacts.

This closes a source/interface inconsistency, not the physical-model or proof
obligations. The generated manifest remains synthetic and
`candidate-development-only`; no real-time, stability, safety or hardware
claim follows from this parity check.

## URDF-derived footprint parity — 2026-08-14

The position-state map path now uses a footprint derived from the complete
`rai_robot_urdf` inventory rather than an untraced generic radius. The selected
`mini_mec_robot` bounds, including wheel and sensor mounts, give
`r_robot=0.1772541986 m`; the URDF source hash is checked by the map runner.
The same radius is passed to DWA and MPPI obstacle/human margins, while the
CCA-NMPC clearance row uses the matching position-state contract. This aligns
the implementation geometry with the supplied robot description. It is not a
proof of physical dimensions, collision safety, stability or experimental
performance; dimensional validation remains a hardware prerequisite.

## Shared context-score parity — 2026-08-14

The map runner's internal CCA prediction now uses the shared five-feature
context definition (`proximity`, `closing`, `cpa_time`, `crossing_geometry`,
and `density`) and the same fixed logistic coefficients exposed by the
Python CCA scorer and MATLAB score path. The earlier two-term proximity/closing
proxy has been removed from the active map path. A regression test compares
each horizon stage with `ContextScorer`; 224 Python tests are collected and the
focused score-policy suite passes.

This closes a software-definition mismatch only. It does not establish score
calibration, LSTM validity, MATLAB numerical equivalence, stability, safety or
physical performance; those gates remain open.

## Position-state candidate rollout — 2026-08-14

The active C++ position-state branch performs a bounded finite-horizon
candidate rollout over the six-state model and body-velocity commands. It
validates the input arrays, forms a nominal command, applies the CCA projected
risk correction when a valid context snapshot is present, clips the command,
and records the resulting rollout. DWA and MPPI use bounded command samples;
there is no exposed multiple-shooting nonlinear-program solver or optimized risk
slack in this executable. The Python layer is only the ABI/orchestration adapter.

This is a software implementation boundary, not a stability, recursive
feasibility, optimality, timing, calibration or hardware result. MATLAB's
position-state study is a separate comparator path and direct solver parity is
not claimed.

## Frozen prediction geometry parity — 2026-08-14

The candidate controller takes `nominal_robot_xy` from the validated
`NmpcPrediction` when constructing the reduced risk-correction normals and
margins. It rejects a malformed or incomplete nominal sequence instead of
silently substituting reference waypoints. The regression
`test_position_nmpc_uses_prediction_nominal_robot_geometry` changes only that
prediction field and verifies a corresponding change in the frozen row. The
host suite remains green.

This closes one software provenance mismatch. It does not close PO-001,
PO-003, PO-011 or PO-013: geometric containment, calibration, solver residual
traces, optimized-slack eligibility, target timing and independent review are
still required.

## Post-reset host QA — 2026-08-14

After the clean-reset purge, the host checks collect and pass 228 Python tests;
Ruff, repository validation and `git diff --check` are green. MATLAB R2025a
passes 74 unit/property tests with zero failures or incomplete cases. The
registries are empty and no dataset, checkpoint, simulation output or physical
capture is admitted. These results verify software/provenance hygiene only.

## Relative-covariance input-domain guard — 2026-08-14

The active position-state NMPC now rejects non-finite, materially asymmetric or
non-positive-semidefinite relative covariance before constructing a chance row.
The projection still uses the symmetric PSD matrix and does not silently turn a
negative variance into zero. Two regression cases cover asymmetric and
non-PSD inputs. This closes an input-domain ambiguity only; covariance
provenance, frame/time alignment, calibration, MATLAB parity and independent
review remain open.

## LSTM recurrence/interface parity — 2026-08-14

The theory notes now state the standard gated LSTM recurrence, velocity head and
fixed-axis direction score used by `ctx_lstm.py`. The causal boundary is explicit:
only the observed history window enters the encoder, the self-supervised target
is the next observed velocity, and no future human position is decoded or
exported. This closes notation/source-interface parity (PO-016) only; checkpoint
selection, ID/OOD performance, calibration and target-hardware timing remain
unverified.
