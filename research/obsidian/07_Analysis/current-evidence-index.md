---
type: evidence-index
status: candidate-development-campaign
evidence_status: candidate-development-only; no-admitted-results
updated_at: 2026-08-14
paper_edit: prohibited
---

# Chỉ mục artifact hiện hành

Chỉ mục này liệt kê artifact còn tồn tại sau lần reset. Các payload detector và
MATLAB output **legacy** đã bị xóa; hash trong
[[07_Analysis/development-artifact-purge-20260814]] chỉ giữ provenance của
việc purge, không phải dữ liệu có thể dùng lại. Các payload pilot position-state
v2--v4 đã được xóa vật lý sau khi xác nhận đây là kết quả phát triển đã lỗi
thời điểm; các mã run cũ chỉ còn trong ghi chú provenance và không được dùng
cho paper hoặc benchmark xác nhận.
`models/registry.json`, `data/registry.json`, `experiments/registry.json` và
`artifacts/registry.json` hiện đều rỗng; superseded candidate payloads đã được
purge theo [[07_Analysis/development-artifact-purge-20260814]]. Cohort ảnh
Internet mới và diagnostic YOLO26s-pose hiện được ghi riêng dưới đây ở trạng
thái `candidate-not-evidence`; chưa có artifact nào được admit cho paper hoặc
claim.

| Artifact | Phạm vi | Trạng thái |
|---|---|---|
| `experiments/runs/_invalidated/` | superseded v2--v4 map pilot payloads | `purged; identifiers retained only in provenance notes` |
| `experiments/runs/context-map-position-state-pilot-20260813-v7/` | five-replicate dynamic-context development pilot | `purged 2026-08-14; provenance hash only` |
| `experiments/runs/context-map-position-state-pilot-20260813-v8/` + `v9/` | candidate LSTM map pilots and fail-closed recheck | `purged 2026-08-14; provenance hash only` |
| `experiments/runs/person-detection-web-pilot-20260813/` + `experiments/runs/person-detection-web-refresh-20260813/` | YOLO26s-pose diagnostics on six Wikimedia images | `purged 2026-08-14; provenance hash only` |
| `data/raw/navwareset-candidate-20260813/` + `experiments/runs/lstm-navwareset-candidate-20260813/` | external context CSV and candidate self-supervised checkpoint | `purged 2026-08-14; provenance hash only` |
| `models/candidates/yolo26s-pose-candidate.pt` | external YOLO26s-pose measurement interface from the superseded perception cohort | `purged 2026-08-14; provenance-only` |
| `experiments/runs/person-web-inference-20260814/yolo26s-pose.pt` | official external YOLO26s-pose measurement interface bound to the fresh seven-image cohort; SHA-256 `a083adb42303728ae14c4bd6bd56d80da46f82fb2564dbd6f31dcc92ea321646` | `candidate-not-evidence; not in model registry` |
| `research/metadata/yolo26s_pose_acquisition_20260814.json` | checkpoint/source/runtime/hash record and fresh inference binding | `provenance-only; candidate payload retained outside registry` |
| `research/metadata/development-purge-20260814.json` | exact-path clean-reset audit for candidate payloads | `provenance-only; 55 files, 59,260,346 bytes removed` |
| `research/obsidian/07_Analysis/pr10-preflight-20260813.md` | PR10 gate definition and historical reset boundary; no current media or manifest is retained | `reset-before-acquisition` |
| `research/metadata/hardware/pr30_entry_preflight_20260814_current.json` | Refreshed PR30 static no-ROS entry: C++ CAN/STM boundary, position-state scope, URDF footprint/source hashes, N10P mapping, hash-bound user physical spec, calibration-sidecar contract, no-device preflight, H0 template and motion-safety gate; report hash `7F9DF16FB7EA6B7DD6C4D0A7E7EDB82575F2B5E44B11C53756B90517EC43D49A` | `PASS` interface gate; hardware admission `BLOCKED` |
| `research/metadata/hardware/mini_mec_intake_20260814.json` | `rai_robot_urdf` CAD/reference intake: 37 URDF model catalog, mini-Mecanum wheel components/axes/origins/masses/meshes, Astra-S/N10P target mounts and simulation-only xacro sensor settings; geometry is explicitly not measured | `source/provenance audit; no serial device; not hardware evidence` |
| `scripts/python/tools/stm_experiment.py` | Direct STM32 serial bring-up and CSV/JSON recorder; protocol parity with the bridge source, stop-flag latch, explicit zero tail and no-ROS runtime | `code-only; no device opened; no result` |
| `matlab/+cca/Simulation.m` + `matlab/+cca/StudyRunner.m` | Position-state comparator source with separate bounded MPC, NMPC, DWA, MPPI and CCA-NMPC branches under the shared body-velocity contract | `source/software QA; development export recorded separately` |
| `experiments/runs/simulation-position-state-20260814/` | bounded MATLAB position-state benchmark before the clean learning campaign | `purged 2026-08-14; provenance-only` |
| `experiments/runs/map-context-development-20260814/` | direct-adapter map pilot before the clean learning campaign | `purged 2026-08-14; provenance-only` |
| `experiments/runs/simulation-learning-20260814/manifest.json` | fresh 9600-row simulation-only context package, frozen episode groups, self-supervised LSTM (5 seeds), score/penalty tabular Q-learning and Python map benchmark | `candidate-development-only; no hardware or paper claim` |
| `experiments/runs/matlab-position-learning-20260814/manifest.json` | fresh bounded MATLAB position-state/body-velocity comparison for MPC, NMPC, DWA, MPPI and CCA-NMPC over four scenarios; source/configuration hashes retained | `candidate-development-only; hardwareValidated=false` |
| `experiments/runs/simulation-learning-20260814/model/metrics.json` | LSTM group-disjoint train/validation/calibration/test-ID/test-OOD evaluation, 1176 windows per split, fitted temperature `0.426`, test-ID score `0.837`, test-OOD score `0.792`; direction labels were not used for training | `candidate-development-only; simulation-only calibration; real-data gate open` |
| `experiments/runs/simulation-learning-20260814/rl_policy.json` | tabular Q-learning with score/penalty reward; 81 episodes, best rolling score `0.859`, learned lateral offset `1.70 m` | `candidate-development-only; policy not hardware validated` |
| `experiments/runs/simulation-learning-20260814/benchmark/manifest.json` + `summary.json` | paired MPC/NMPC/DWA/MPPI/CCA-NMPC map benchmark, 5 replicates × 3 dynamic-context scenarios using the calibrated simulation checkpoint; fixed global path and trigger-only local path | `candidate-development-only; descriptive diagnostics only` |
| `experiments/runs/simulation-benchmark-400mm-20260814/manifest.json` + `summary.json` | independent 10-replicate (30 paired units) development benchmark bound to `configs/physical_robot.json`; fixed global path, trigger-only local path, hash-bound LSTM and Q-learning policy, score tuning disabled | `candidate-development-only; no confirmatory or hardware claim` |
| `configs/physical_robot.json` | user-supplied 400 x 400 mm total footprint, interpreted 50 mm wheel radius, LiDAR/camera heights and front-edge offsets, and downward camera pitch; source hash is bound into the map contract | `user-supplied geometry input; independent dimensional and calibration verification pending` |
| `experiments/runs/matlab-position-learning-20260814/manifest.json` | bounded MATLAB position-state comparison over MPC, NMPC, DWA, MPPI and CCA-NMPC | `candidate-development-only; no hardware claim` |
| `experiments/runs/stm-motion-test-jetson/` (Jetson, remote) | one-second C++ STM smoke test with `vx_cmd=0.02 m/s`; serial loop completed, but applied telemetry remained zero | `candidate-not-evidence; superseded by controlled follow-up` |
| `experiments/runs/stm-motion-test-010-jetson/` + `experiments/runs/stm-stop-verification-jetson/` (Jetson, remote) | one-second `vx_cmd=0.10 m/s` direct C++ STM run followed by two-second zero-only stop verification; measured encoder response, clean zero tail, and operator-confirmed chassis motion | `candidate-not-evidence; commissioning motion confirmed by encoder and operator, independent metrology pending` |
| `src/hardware.py` + `scripts/python/tools/record_hardware.py` | Recorder trực tiếp Astra-S/OpenNI2, explicit N10P profile, CCA CAN/STM32 serial, pre-command STM stop latch, per-frame context overlay và online position-state CCA candidate rollout; overlay labels LSTM `disabled/active/warmup/invalid` and prints the resolved local checkpoint path; checkpoint optional for initial capture; CCA prediction remains internal and is not drawn; events expose status, iterations, reduced violation, risk bound and reserved zero-slack field | code QA only; chưa mở thiết bị |
| `src/shared.py` + `src/control/src/can.cpp` + `src/control/src/stm_c_api.cpp` | Shared CCA CAN boundary: C++ CRC/frame codec selected on Linux through the Python interface, with explicit Python fallback; schema/provenance functions remain Python | C ABI/CTest and Python parity QA; no device or result |
| `scripts/python/tools/map_run.py` + `src/ai/context.py` + `src/control/src/context.cpp` | Active CCA map prediction and scorer share the five-feature logistic context definition; the scorer selects the C++ core through the C ABI on Linux and retains a Python fallback | software-parity checkpoint; calibration and evidence gates remain open |
| `src/control/src/controller.cpp` + `src/runtime/controller.py` + `tests/python/tests/test_score_policy.py` | Compiled position-state controller is the sole implementation of the MPC/NMPC/DWA/MPPI/CCA-NMPC branches; Python is only the ctypes adapter and orchestration layer | software-parity checkpoint; residual, timing, calibration and hardware gates remain open |
| `scripts/python/tools/analyze_run.py` | Separate post-run analysis of sealed CSV/JSON packages, including CCA-NMPC event status/replan/deadline/risk diagnostics; raw package immutable and future human path explicitly absent | analysis capability; no physical package |
| `research/obsidian/07_Analysis/theory-parity-audit-20260813.md` | T1--T5 software/parity audit và numerical-floor synchronization | `candidate`; PR02 vẫn `PROOF-DRAFT` |
| `research/obsidian/05_Theory/proof-audit-20260814.md` | Internal theorem/proof consistency audit: allocator conditions, Gaussian-tail sign, one-direction containment, frozen-mode Boole bound and explicit claim limits | `review-open; derivation/static-parity only; PR02 remains PROOF-DRAFT` |
| `research/obsidian/03_Literature/current-research-refresh-20260814.md` | Focused Google/web refresh of recent ellipsoidal-obstacle MPC, Mecanum control and distributionally robust human-navigation prior art; local Zotero exact-title search returned no match | `screening-only; no paper edit; no gap claim promoted` |
| `research/metadata/development-purge-20260813.json` | Record của reset artifact trước campaign mới | provenance-only |
| `data/manifests/web_person_cohort_20260813.json` and refresh manifest | Six real Wikimedia candidate manifest records | `purged 2026-08-14; provenance notes only` |
| `data/raw/web-cohort-20260814/web-image-manifest.json` + `research/metadata/pr10-web-cohort-preflight-20260814.json` | seven new real Wikimedia candidates: one calibration, two test-ID, two test-OOD person scenes and two empty controls | `preflight PASS; admission BLOCKED; candidate-not-evidence` |
| `experiments/runs/person-web-inference-20260814/inference/` | YOLO26s-pose CPU diagnostic on the seven real images, scene-tag matrix `[[2,0],[0,5]]`, LSTM path provenance overlay | `candidate-not-evidence; no blind boxes or target timing` |
| `data/raw/coco8-pose-20260814/coco8-pose-manifest.json` + `coco8-pose-bbox-annotations.json` + `research/metadata/coco8_pose_preflight_20260814.json` | four public COCO8-pose validation images with provider bounding boxes; manifest/media/annotation schema and hash checks pass | `candidate-not-evidence; provider labels are not independent annotation; admission BLOCKED` |
| `experiments/runs/coco8-pose-inference-20260814/` | fresh YOLO26s-pose CPU box diagnostic at confidence `0.25`, IoU `0.5`: TP `11`, FP `1`, FN `3`, P/R/F1 `0.9167/0.7857/0.8462`, mean matched IoU `0.8562`, P50/P95/max `324.91/573.17/603.18` ms | `candidate-not-evidence; four-image descriptive diagnostic only` |
| `research/metadata/simulation-reset-20260814.json` | exact inventory and deletion audit: 51 files, 36,288,151 bytes; backup retained | `reset-complete; provenance-only` |

## Quy tắc đọc

- Không có checkpoint LSTM, `context.csv` robot thật, confirmatory simulation,
  robot package hoặc hardware result đang được admit. The new LSTM checkpoint
  is simulation-trained and candidate-only; it is not a verified model entry.
- Pilot v5--v9 payloads were physically purged on 2026-08-14; only the
  provenance audit and design lessons remain. None is a current result or
  confirmatory/paper evidence.
- Nhánh confirmatory của `ctx_run.py` fail-closed nếu thiếu sealed direct
  CSV/JSON, hash `context.csv`, calibration sidecar, split disjoint và
  `human_trajectory_generated=false`.
- Score loop xác nhận giữ ledger của từng seed, chọn điểm validation tự giám sát
  cao nhất với tie-break xác định, và chỉ tiếp tục khi có đủ năm seed hoàn tất;
  development một seed vẫn chỉ là candidate. Người động có thể được CCA-NMPC
  dự đoán nội bộ, nhưng không có quỹ đạo tương lai trong ảnh hoặc CSV/JSON.
- PR10 chỉ mở admission khi có annotator thứ hai, adjudicator độc lập,
  pretraining-overlap review và cohort ID/OOD đủ lớn. Fixture test không phải
  annotation dữ liệu.
- The 2026-08-13 Wikimedia and NavWareSet candidates are no longer local
  payloads. Their source notes remain literature/acquisition knowledge only;
  no metric, image, checkpoint or run result is retained.
- Không tái sử dụng tên run, model hash hoặc số liệu trong purge record cho
  campaign mới. Campaign mới phải có protocol freeze, code snapshot và run ID
  mới.

- Campaign `simulation-learning-20260814` là run phát triển mới duy nhất sau
  reset. Nó chỉ dùng để phát hiện lỗi code và đặt ngưỡng; mọi số liệu vẫn bị
  loại khỏi claim register cho tới khi có split độc lập, calibration, holdout
  và phân tích reviewer.

- Pilot v8/v9 notes are retained only as design lessons. Their checkpoints,
  metrics and result payloads were purged on 2026-08-14 and must not be
  reconstructed from hashes.

- NavWareSet scene 13 is a public real-offline context reference, not a target
  hardware dataset. Its local CSV and checkpoint were purged; only the
  data-design note remains, and no future human path is exported.

## Liên kết tri thức

[[00_MOC/project-map]] · [[07_Analysis/pr10-preflight-20260813]] ·
[[07_Analysis/pr10-web-source-candidates-20260813]] ·
[[07_Analysis/pr30-entry-preflight-20260813]] ·
[[07_Analysis/theory-parity-audit-20260813]] ·
[[07_Analysis/protocol-status-20260813]] ·
[[07_Analysis/web-cohort-acquisition-20260814]] ·
[[07_Analysis/yolo26s-pose-candidate-acquisition-20260814]] ·
[[07_Analysis/simulation-learning-campaign-20260814]] ·
[[07_Analysis/map-context-development-20260814]] ·
[[05_Theory/proof-audit-20260814]] ·
[[06_Methods/simulation-protocol]] · [[06_Methods/final-run-data-package]] ·
[[01_Governance/status-and-provenance]]
