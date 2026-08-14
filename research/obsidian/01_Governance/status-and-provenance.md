---
type: governance
status: active
evidence_status: verified-policy
---

# Chính sách trạng thái và nguồn gốc

## Từ vựng trạng thái được kiểm soát

| Trạng thái | Ý nghĩa |
|---|---|
| `unknown` | Chưa kiểm tra hoặc thiếu provenance. Đây là mặc định. |
| `planned` | Có protocol nhưng chưa chạy. |
| `in-progress` | Đang tạo artifact; chưa được claim. |
| `candidate` | Có artifact nhưng chưa qua QA độc lập. |
| `novelty-at-risk` | Claim novelty đã gặp prior art trực tiếp và phải thu hẹp hoặc đổi hướng trước khi xác nhận. |
| `full-text-expanded` | Literature set đã được mở rộng bằng đọc toàn văn nhưng systematic database workflow chưa đóng. |
| `verified` | Đủ manifest, hash, protocol, QA và truy vết claim. |
| `legacy` | Tạo trước chương trình tái thiết kế; chỉ giữ lịch sử, cấm dùng làm bằng chứng mới. |
| `invalid` | Vi phạm protocol/leakage/corruption hoặc không thể tái tạo. |
| `retired` | Từng hợp lệ nhưng không còn thuộc scope hiện tại. |

Các status dùng cho tài liệu thiết kế (không phải evidence acceptance) cũng được
kiểm soát: `active`, `draft`, `hypothesis`, `proof-draft`, `proposed`, `screening`
và `awaiting-evidence`. Chúng lần lượt chỉ trạng thái quản trị đang dùng, bản nháp,
giả thuyết cần bác bỏ/kiểm chứng, proof chưa review, quyết định chưa duyệt, literature
screening chưa đóng và trang kết quả chưa có evidence. Không status nào trong nhóm này
tương đương `verified`.

## Từ vựng trạng thái bằng chứng được kiểm soát

| Trạng thái bằng chứng | Ý nghĩa |
|---|---|
| `unknown` | Chưa có provenance đủ để phân loại. |
| `policy` | Quy tắc thiết kế; không phải kết quả. |
| `verified-policy` | Quy tắc đã kiểm tính nhất quán; vẫn không phải evidence thực nghiệm. |
| `abstract-and-publisher-screen` | Chỉ screening metadata/abstract; chưa đủ xác nhận novelty. |
| `proof-draft` | Có derivation nhưng chưa review độc lập và chưa ánh xạ code. |
| `no-new-dataset` | Chưa thu/freeze dataset mới. |
| `no-new-model` | Chưa train/freeze model mới. |
| `no-new-results` | Chưa có kết quả mới được admit. |

## Tường lửa đối với dữ liệu legacy

1. Mọi file cũ, số liệu cũ, checkpoint cũ và figure cũ mặc định `legacy`.
2. Không copy artifact legacy vào cấu trúc evidence mới.
3. Chỉ được tái chạy code/ý tưởng sau khi protocol mới được freeze; output mới phải có run ID và hash riêng.
4. Kết quả không rõ ngày, seed, split, config hoặc code revision là `unknown`, không phải `verified`.

## Nguồn gốc tối thiểu của một artifact mới

- artifact ID và work package;
- ngày giờ UTC, người chạy và môi trường;
- code revision/immutable snapshot;
- dataset version + manifest hash;
- config hash, seed và command/workflow ID;
- raw output URI + SHA-256;
- analysis script revision;
- protocol deviations;
- QA reviewer và ngày xác minh.

## Chấp nhận bằng chứng

Một kết quả chỉ được liên kết vào [[01_Governance/claim-register]] sau khi được ghi tại [[06_Methods/evaluation-protocol]] với status `verified`. Missing evidence phải ghi `unknown`; không được dùng ô trống để ngụ ý đã hoàn thành.

## Acceptance ledger — 2026-08-14 (post-reset)

| Gate | Trạng thái hiện tại | Bằng chứng/điều kiện còn lại |
|---|---|---|
| Repository schemas, instances và Obsidian links | `verified` | `repo_check.py --require-focused-audit-complete` PASS; 24 schemas, 16 instances, 115 notes, 1,026 links |
| Python code quality và unit tests | `verified` | Full Python suite PASS after the position-state runner/model update, dynamic-context CCA prediction, no-prediction overlay contract, direct-recorder hardening, measured-geometry fail-closed guard, clean-reset regression and covariance-domain guards; Ruff PASS; `repo_check.py` PASS; đây là software QA, không phải kết quả khoa học |
| STM CAN/telemetry host test | `verified` | `src/stm/tests/run_host_tests.ps1` PASS; kiểm tra protocol/telemetry trên host, không phải hardware evidence |
| MATLAB unit/property tests | `verified` | Re-run `matlab -batch ... run_tests` on 2026-08-14 PASS: 74 passed, 0 failed, 0 incomplete; includes position-state step/simulation contract checks plus ellipse-support, covariance-domain and zero/near-singular chance-row edge cases; đây là code QA, không phải campaign mô phỏng/hardware |
| Direct CSV/JSON final-run package contract | `verified-policy` | Contract/validator and PR30 static no-ROS entry preflight pass; `final_pack.py` rejects duplicate/non-increasing timestamps and requires a hash-bound `calibration.json` for non-unknown capture sources; `record_hardware.py` + `hardware.py` provide direct Astra-S/OpenNI2, N10P serial, STM32 serial and optional CCA CAN paths under the six-state position/body-velocity contract; URDF/xacro are read-only references under `reference/robot` and runtime geometry requires a measured physical-spec hash; manifest records capture source, declared Astra-S/N10P/firmware identity when supplied, and keeps structural integrity separate from scientific evidence; current Windows session has no detected serial/CAN/Astra/N10P device and no robot package has been captured |
| Dataset/model/checkpoint reset audit | `verified-policy` | Toàn bộ candidate dataset, manifest, model weight, checkpoint và run payload còn lại đã purge theo [[07_Analysis/development-artifact-purge-20260814]]. Bốn registry hiện rỗng; chỉ metadata/provenance được giữ |
| Proposal--theory active-model alignment | `amended-policy` | LSTM vẫn là thành phần của CCA ở giao diện context (vị trí/tốc độ/hướng/confidence/validity); CCA-NMPC được phép giữ future-position prediction nội bộ, nhưng không ghi/vẽ path trên ảnh. Phạm vi vật lý dùng state `[x,y,theta,vx,vy,omega]` và body-velocity command để bám vị trí; mô-men/dòng điện không phải yêu cầu. Nhánh torque trong simulator cũ nếu còn giữ chỉ là compatibility/development code, không phải physical evidence |
| Internet-image media and blind-bbox integrity | `candidate-acquired; admission blocked` | Seven fresh Wikimedia candidates and four COCO8-pose provider-label diagnostics pass mechanical manifest/media checks; independent annotation/adjudication, privacy release, OOD expansion and admission remain open |
| YOLO26s-pose Internet-image diagnostics | `candidate-not-evidence` | The detector remains a replaceable perception instrument; current CPU diagnostics are descriptive only and not target-device or blind-ground-truth evidence |
| Context LSTM score loop | `candidate-development-only` | Fresh 9,600-row simulation context, five-seed self-supervised checkpoint and score/penalty policy are hash-bound; `ctx_run.py` still requires a sealed target-compatible direct capture and independent calibration/test rerun |
| Python map controller comparison | `candidate-development-only` | Fresh physical-spec-bound 30-unit map benchmark is retained with fixed global path, trigger-only local regeneration and matched MPC/NMPC/DWA/MPPI/CCA-NMPC labels; confirmatory execution still requires PR20/PR21 freeze and real-context provenance |
| MATLAB bounded simulation | `candidate-development-only` | Fresh bounded position-state export is retained at `experiments/runs/matlab-position-learning-20260814/`; it is a software comparator only and does not support physical or superiority claims |
| User-supplied physical geometry | `candidate-input; independent verification pending` | `configs/physical_robot.json` is hash-bound into the map contract and runtime preflight; dimensions and sensor offsets are recorded, but wheel-radius interpretation, dimensional measurement, sensor calibration and commissioning remain open |
| Backup snapshot integrity | `verified-policy` | `backup/paper-current-2026-08-01.sha256` đối chiếu 12/12 file, 0 mismatch; snapshot chỉ đọc và không dùng làm evidence mới |
| Git reset boundary | `verified-policy` | Repository mới trên branch `codex/repository-bootstrap`, chưa có project commit/tag/remote; snapshot hiện đã stage nhưng chưa commit. Các object/history cũ không được dùng làm project provenance |
| Focused literature audit | `reviewed-bounded` | PR01-SLR không còn là yêu cầu của bài báo này; focused Zotero/Obsidian audit đã review xong trong phạm vi bounded, không gọi là systematic review hoặc PRISMA. Các lượt Google/web refresh đến 2026-08-14 đã ghi HRI/control boundary, SHARP/context-preference/ARMS, official YOLO26-pose tool, DRA-MPPI, Mecanum hardware, uncertainty-aware safety, model-based RL, neural chance-constrained MPC và C2U-MPPI; Scholar spot-check chỉ là discovery, không phải coverage claim. Zotero Desktop 9.0.6/API v3/connector reachable, inventory 43 item; C2U-MPPI exact-title search hiện không có match local và chưa import. Metadata PR01 lịch sử là `ARCHIVED`; review record là [[07_Analysis/focused-audit-review-20260813]]. |
| Overleaf manuscript | `locked` | Không sửa hoặc build local trong giai đoạn code/research |

`verified` ở đây chỉ có nghĩa gate kỹ thuật hoặc chính sách đã kiểm tra. Không
được đổi `candidate`, `design-only`, `planned` hay `in-progress` thành
`verified` nếu chưa có artifact và QA tương ứng. Bảng này là source-of-truth
cho việc quyết định khi nào phân tích trong
[[07_Analysis/experimental-analysis]] có thể được promote vào claim register.

## Runtime layout decision — 2026-08-14

The active runtime has one implementation per boundary: the compiled C++
controller and transport live under `src/control`; Python keeps the thin
perception, hardware, packaging, and adapter layers under `src/ai`,
`src/simulation`, `src/runtime`, `src/hardware.py`, and `src/shared.py`.
The obsolete Python torque NMPC, torque EKF, and torque safety-supervisor
modules were removed from the active tree; the position-state command path is
the only runtime controller boundary.
The one-file repository gate is `src/repository.py`; it validates schemas,
provenance, forbidden manuscript writes, and web-image records, so it remains
an acceptance gate rather than an experiment module. The former `src/ros2`
tree is now a read-only `reference/robot` snapshot used only for URDF, sensor
mount, and legacy serial-contract hashes. No ROS process, ROS message, or
rosbag is part of the active path. These boundaries connect to
[[00_MOC/project-map]], [[06_Methods/execution-roadmap]], and
[[01_Governance/knowledge-boundary]].

Related hub: [[00_MOC/project-map]]

## No-device hardware preflight refresh — 2026-08-14

`validate_hardware_entry.py` was rerun after the source-layout consolidation. The
report `research/metadata/hardware/pr30_entry_preflight_20260814_current.json`
has SHA-256
`7F9DF16FB7EA6B7DD6C4D0A7E7EDB82575F2B5E44B11C53756B90517EC43D49A` and reports
`status=PASS`, `admission_status=BLOCKED`. The interface checks pass, but no
device, independent dimensional verification, sensor calibration, safety
approval, or sealed hardware package was created. The user-supplied physical
specification is recorded and hash-bound, but it is not yet independently
verified. This is a source/preflight record only and cannot be used as
experimental evidence.

Related: [[07_Analysis/current-evidence-index]] · [[06_Methods/execution-roadmap]]
