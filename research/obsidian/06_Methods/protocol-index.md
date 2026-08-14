---
type: methods-index
status: active
evidence_status: knowledge-only
tags: [protocol, provenance, workflow]
---

# Protocol index — phase IDs and execution order

`PRxx` is a stable phase identifier, not a continuous file counter. The tens
digit reserves a phase family so that a new protocol can be inserted without
renaming later records, manifests, hashes, or claim links. The `Order` column
is the execution order.

| Phase | Protocols | Scope | Order |
|---|---|---|---:|
| 00 | [PR00](../../../protocols/PR00_scope_and_claims.md) | scope, RQs, hypotheses, claims | 0 |
| 01 (archived) | [PR01](../../../protocols/PR01_literature_review.md) | historical SLR archive; not required and not an execution gate; active work uses focused audit | — |
| 02 | [PR02](../../../protocols/PR02_theory_and_proofs.md) | model, assumptions, theorems, proofs | 2 |
| 10 | [PR10](../../../protocols/PR10_person_data_acquisition.md) | Internet-image data acquisition | 3 |
| 11 | [PR11](../../../protocols/PR11_lstm_dataset.md) | context sequence dataset | 4 |
| 12 | [PR12](../../../protocols/PR12_lstm_training_evaluation.md) | self-supervised LSTM score loop | 5 |
| 20 | [PR20](../../../protocols/PR20_simulation.md) | confirmatory simulation | 6 |
| 21 | [PR21](../../../protocols/PR21_controller_benchmark.md) | controller benchmark | 7 |
| 22--24 | [PR22](../../../protocols/PR22_pilot_simulation.md) · [PR23](../../../protocols/PR23_pilot_stabilization.md) · [PR24](../../../protocols/PR24_pilot_feasibility_preservation.md) | pilot and feasibility checks | 7a--7c |
| 30 | [PR30](../../../protocols/PR30_physical_experiment.md) | direct robot experiment | 8 |
| 40 | [PR40](../../../protocols/PR40_statistics_and_qualitative_analysis.md) | statistical and qualitative analysis | 9 |
| 50 | [PR50](../../../protocols/PR50_evidence_release.md) | evidence release and review gate | 10 |

## Reading rule

Follow `Order` for execution. Cite the stable `PRxx` identifier in manifests,
analysis notes, and claim ledgers. Never infer that a phase is accepted merely
because an earlier or adjacent identifier has passed; acceptance is recorded by
the status and evidence gate of that protocol.

Current status ledger: [[07_Analysis/protocol-status-20260813]].

Related knowledge: [[06_Methods/execution-roadmap]],
[[01_Governance/status-and-provenance]], [[07_Analysis/completion-audit]],
[[00_MOC/project-map]].
