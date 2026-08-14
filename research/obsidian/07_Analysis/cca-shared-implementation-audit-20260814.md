---
type: implementation-audit
status: candidate
evidence_status: software-qa-only
paper_edit: prohibited
---

# Shared implementation audit — 2026-08-14

## Decision

The fixed-width CCA CAN wire boundary is implemented in C++ and exposed
through the existing Python `src/shared.py` interface. The Linux target selects
`libcontrol_transport` automatically; `CCA_CAN_BACKEND=python` remains an
explicit compatibility fallback. This keeps one byte-level implementation for
the Jetson/Raspberry Pi deployment path without moving research orchestration
into C++.

The library resolver accepts single-configuration and multi-configuration
CMake layouts (`build/`, `build/Release/`, `build/Debug/`, and `build/lib/`),
so the target does not silently fall back to Python merely because the build
generator placed the shared object in a configuration subdirectory.

## Function-level allocation

| Shared function or concern | Implementation | Reason | Boundary |
|---|---|---|---|
| CRC-8, signed quantisation and CAN frame encode/decode | `src/control/src/can.cpp` and `src/control/src/stm_c_api.cpp` | fixed-size wire contract, repeated in the control/transport path | requires target-library build and device H0 verification |
| STM32 serial frame parser and zero-command latch | `src/control/src/stm_serial.cpp` through the same C ABI | deterministic byte I/O and fail-safe stop path | no serial device was opened in this QA pass |
| Five-feature CCA context score | `src/control/src/context.cpp` through `cca_context_score`; selected by `src/ai/context.py` | deterministic scalar math at the controller boundary; keeps Python as a typed facade | parity and software QA only |
| Calibration validation, contract loading and forbidden-field policy | Python `src/shared.py` and `src/repository.py` | JSON/schema/string policy and evidence provenance are not hot-loop kernels | software validation only |
| File hashing and manifest metadata | Python `hashlib`/JSON path | Python delegates hashing to optimized native code and keeps the evidence format readable | no scientific result is implied |

## Verification

- Ubuntu 22.04 WSL CMake Release build: pass.
- CTest: `control_tests` pass, including C ABI CAN round-trip.
- Linux Python smoke: `src/shared.py` selected the built shared library and
  reproduced header/body encode and decode values.
- Linux Python smoke: `src/ai/context.py` selected the C++ context scorer; its
  feature vector and score matched the explicit Python fallback to machine
  precision. A 64-case finite random parity sweep had maximum absolute error
  `4.44e-16`.
- Windows Python suite: `194` tests pass; Ruff and repository contract checks
  pass (`24` schemas, `16` instances, `115` notes, `1,026` wikilinks, no
  issues).
- Hardware preflight: `PASS` interface checks, `BLOCKED` admission because the
  user-supplied geometry is recorded but independent dimensional/sensor
  calibration, safety approval and a sealed direct run are still pending.

## Interpretation

This is an implementation and parity improvement, not a new control claim.
Python remains the correct boundary for Astra-S/OpenNI2, N10P packet
integration, YOLO26s-pose, score-trained LSTM, CCA-NMPC orchestration and
CSV/JSON evidence packaging. No paper, backup, dataset, model or experiment
result was modified or promoted.

## Active call-site check — 2026-08-14

The horizon context calculations in `scripts/python/tools/map_run.py` and
`scripts/python/tools/record_hardware.py` now call the single
`ai.context.context_score` facade. On Linux with the transport library
present this selects `cca_context_score` in C++; the Python implementation is
used only when the library is unavailable or when the explicit fallback
environment variable is set. This removes the duplicated Python feature-vector
and sigmoid code from the active map and hardware paths while preserving a
machine-checked fallback.

The final boundary remains intentionally narrow: moving vendor acquisition,
YOLO26s-pose, LSTM, NMPC orchestration or evidence serialization to C++ would
not reduce the fixed-width transport risk and would make the deployment
interface harder to audit. The C++ choice is therefore a kernel decision, not
a language preference.

Latest checks: Windows Python suite PASS; repository contract PASS; WSL C++
Release build and CTest PASS; C++/Python context parity PASS. These are
software checks only and do not admit hardware or scientific results.

## Knowledge links

[[07_Analysis/completion-audit]] · [[07_Analysis/protocol-status-20260813]] ·
[[07_Analysis/current-evidence-index]] · [[06_Methods/execution-roadmap]] ·
[[01_Governance/status-and-provenance]]
