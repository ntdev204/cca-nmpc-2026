---
type: internal-proof-audit
status: review-open
evidence_status: derivation-and-static-parity-only
reviewer: internal-continuation-audit
updated_at: 2026-08-14
paper_edit: prohibited
---

# Internal proof audit — 2026-08-14

This is a bounded consistency audit of the current theorem and proof notes. It
is not an independent peer review, a stability proof, or evidence under the
operational distribution. The audited sources are
[[05_Theory/assumptions]], [[05_Theory/theorems]], [[05_Theory/proofs]] and
[[05_Theory/notation]].

## Findings

### T1--T3: fixed-budget allocation

The derivations are valid for a nonempty frozen active set with
\(M=|\mathcal E_k|\), finite context scores, finite \(\beta\), and
\(M\varepsilon_{\min}<\bar\varepsilon\). Positivity of the exponential weights
gives a strict floor and their normalized sum gives exact budget conservation in
real arithmetic. The finite-precision implementation may only claim tolerance-
based conservation and must report saturation. No optimality result follows.

### T4: scalar Gaussian surrogate

The tail direction is internally consistent if
\(Y_{em}=n_{em}^{\mathsf T}\delta_{em}\), the violation is \(Y_{em}>a_{em}\),
and \(a_{em}=n_{em}^{\mathsf T}(p_r^0-\mu_{em})-d_{\mathrm{req},em}\).
The proof requires the conditional zero-mean Gaussian assumption, positive
\(\sigma_{em}\) or the explicitly degenerate \(\sigma_{em}=0\) case, zero slack,
and an accepted solver residual. A nonzero conditional mean, an undefined
relative-error sign, or a clipped covariance invalidates the stated tail step.

The ellipse-to-half-space argument is one-directional support containment. It
does not prove collision avoidance for every normal, every horizon step, every
mode, or the receding-horizon closed loop. The active implementation must either
use a mode-specific support orientation or declare an orientation-invariant
conservative bound; a single top-mode yaw is not enough for A-17.

The current C++ candidate rollout is intentionally weaker than this T4
formulation: it projects the supplied covariance and applies a reduced
clearance correction, but it does not expose the full support term,
$d_{\mathrm{req},em}$, optimized slack or a nonlinear-program residual. This is
an implementation boundary, not a proof failure; it means T4 remains a
reference/theory contract and cannot be reported as executed probability logic.

### T5: mixture and Boole accounting

The law-of-total-probability step is valid only when A-04 is a genuine exhaustive
partition with zero omitted mass and every retained mode uses the same event
allowance. Boole's inequality then applies to the finite active set frozen for
one solve. The result is not a multi-step, mission-wide, calibrated, or
closed-loop safety guarantee.

### T6, P-PS3 and T-PS1

T6 is a selection invariant: choosing from a nonempty feasible candidate set
preserves the configured residual tolerance. It does not establish that the set
is nonempty, that the solver meets its deadline, or that fallback is safe.
P-PS3 has the same boundary because a reported numerical status describes one
finite transcription only. T-PS1 correctly composes the causal constant-velocity
internal interface with fixed-budget accounting and a one-update model bound;
it makes no statement about prediction accuracy, recursive feasibility, or
physical safety. The internal human-position sequence remains forbidden in
CSV/JSON and image overlays.

## Admission ledger

The following ledger is the single decision table for the current theory package.

| Item | Required assumptions | Checked evidence | Admission |
|---|---|---|---|
| P-CTX | A-08 and snapshot causality | recurrence and source-boundary checks | contract only |
| T1 | A-01--A-03 | fixed-budget property tests | static only |
| T2 | A-01--A-03 | ordering property tests | static only |
| T3 | A-01--A-03 | uniform-case property tests | static only |
| T4 | A-05, A-07, A-08, A-17 | scalar-tail derivation and covariance guards | blocked |
| T5 | A-01, A-04, A-05, A-08 | mode/Boole derivation and accounting checks | blocked |
| T6 | A-08 and a feasible candidate | candidate-selection regression | one-solve only |
| P-PS3 | A-08 and frozen rows | direct-transcription regression | one-solve only |
| T-PS1 | T1, T4, T5 and A-08 | composed derivation | blocked |

“Static only” means that the implementation agrees with the stated algebra on
finite test inputs. “Blocked” means that at least one assumption still lacks
geometry, provenance, calibration, or independent review. “One-solve only” is an
implementation contract and must not be described as recursive feasibility,
stability, or physical safety. The fresh simulation campaign does not change
any row in this table: it is simulation-only development evidence and cannot
close PO-001--PO-003, PO-005--PO-009, PO-011, or PO-013.

## Minimal review packet before manuscript unfreeze

An independent reviewer should check, in order: (1) the sign of
\(\delta_{em}\), \(n_{em}\), and the strict half-space event; (2) the
ellipse/footprint support containment for every retained mode; (3) the
exhaustiveness of the mode partition and omitted mass; (4) the zero-slack and
residual preconditions; and (5) the distinction between
\(\Pr_{\mathrm{model}}\) and \(\Pr_\star\). Until those checks are recorded,
PR02 remains `PROOF-DRAFT` and no theorem-derived probability statement is
eligible for the locked paper.

## Required notation cleanup before manuscript unfreeze

1. Define \(M=|\mathcal E_k|\) at the first allocator equation and keep
   \(e\in\mathcal E_k\) distinct from mode \(m\).
2. Use one sign convention for \(\delta_{em}\), \(n_{em}\), the signed margin and
   the strict violation event in every theorem and implementation record.
3. Keep \(d_{\mathrm{req},em}\) separate from covariance and quantile terms; do
   not hide braking distance or slack inside \(\Sigma^{\mathrm{rel}}\).
4. State \(\xi=0\), residual tolerance, frozen active set and conditional
   probability space next to T4/T5 rather than only in a later limitation.
5. Reserve \(\Pr_{\mathrm{model}}\) for the conditional model statement and
   \(\Pr_\star\) for the unverified operational distribution. The latter remains
   blocked until PO-003 is closed.

## Closure gates

The proof package remains PROOF-DRAFT until an independent control reviewer
checks signs and assumptions, a geometry-parity replay passes for every retained
mode, covariance provenance/calibration and zero-slack residual records exist,
and the implementation snapshot is hash-bound. Existing Python/MATLAB tests
support static parity only; they do not close these gates.

## Static parity recheck — 2026-08-14 continuation

The MATLAB R2025a test harness was rerun after the current theory and repository
snapshot: all reported tests passed, including the fixed-active-set allocation
properties, the active-set switching counterexample, Gaussian covariance edge
cases, ellipse-support sampling and the six-state position/body-velocity
contract. This confirms finite-input implementation parity only. It does not
close the independent sign/geometry review, covariance calibration, zero-slack
residual evidence, recursive feasibility, closed-loop stability or any
probability statement under $\Pr_\star$.

[[05_Theory/proof-obligations]] · [[05_Theory/implementation-parity]] ·
[[07_Analysis/theory-parity-audit-20260813]] ·
[[01_Governance/status-and-provenance]]
