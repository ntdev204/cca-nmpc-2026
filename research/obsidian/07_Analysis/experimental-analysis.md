---
type: evidence-analysis
status: awaiting-confirmatory-evidence
evidence_status: no-admissible-results; development-payloads-purged
raw_data_scope: external-only
updated_at: 2026-08-14
paper_edit: prohibited
---

# Phân tích thực nghiệm có provenance

Ghi chú này chỉ chứa khung phân tích và ranh giới admission cho các gói hiện
tại. Các payload legacy đã bị xóa theo
[[07_Analysis/development-artifact-purge-20260814]]. Hiện có các gói candidate
mới được mô tả bên dưới; không gói nào được giữ làm bằng chứng xác nhận.

## Điều kiện để mở phân tích

Mỗi gói mới phải có `run_id`, `manifest.json`, SHA-256 raw files, code/config/
protocol hash, map version, controller version, seed, clock, denominator và
deviation record. Thiếu một trường thì giữ `unknown`/`candidate` và không liên kết vào [[01_Governance/claim-register]].

## Khung phân tích bắt buộc

1. **Integrity:** kiểm tra package bằng `final_pack.py` và checksum.
2. **Primary control:** collision, safe completion, minimum clearance và
   constraint/fallback failures theo denominator đã khóa.
3. **Secondary control:** tracking, progress, control variation, local-path
   update và solver timing; không chọn riêng run thành công.
4. **Context:** direction confusion matrix, speed error, context-valid/stale
   rate và trigger latency; không tạo human trajectory.
5. **Qualitative:** chọn median, boundary, failure và OOD theo rule đã định
   trước, kèm provenance từng frame/map view.
6. **Statistics:** paired seed, effect size, CI, failure counts và deviations
   theo [[06_Methods/statistical-analysis]].

## Ranh giới

Không gọi pilot là bằng chứng Q1, không suy ra real-time hay an toàn phần cứng
từ timing phát triển, và không chuyển số liệu thành claim trước khi reviewer
độc lập xác minh gate `verified`. Global path giữ cố định; local path chỉ sinh
lại khi conflict/direction trigger được khai báo. Ảnh chỉ chứa context hiện tại,
không chứa human future trajectory.

## Development-result boundary

Former legacy controller metrics, collision counts, clearance values, confusion
matrices and artifact hashes were purged. The pre-reset bounded MATLAB and map
packages were also removed under [[07_Analysis/simulation-reset-20260814]]. The
post-reset packages below are separate candidate runs and must not be merged
with those historical records.

## Fresh learning campaign — 2026-08-14

The replacement package is
[[07_Analysis/simulation-learning-campaign-20260814]]. It contains a new
simulation-only capture package with group-disjoint
train/validation/calibration/test-ID/test-OOD splits, a five-seed
self-supervised LSTM score loop with temperature calibration, a tabular
Q-learning score/penalty policy, a five-replicate paired map benchmark and a
bounded MATLAB parity run. All artifacts are marked
`candidate-development-only`. The split/calibration contract is exercised, but
the source is simulated and no protocol freeze, real capture or hardware
evidence is present. The CCA-NMPC map rows are descriptive diagnostics; they do
not prove superiority, safety or real-time operation.

A confirmatory package under a frozen PR20/PR21 campaign is still required
before any number can enter the claim register.

## Real-image perception candidate — 2026-08-14

The seven-image Wikimedia cohort passed manifest-only structural checks. A stale
YOLO diagnostic was deleted, then the official YOLO26s-pose checkpoint was
downloaded again and run on all seven images in
`experiments/runs/person-web-inference-20260814/inference/`. The scene-tag
presence matrix is `[[2,0],[0,5]]` at confidence `0.25`, with CPU latency
P50/P95/max `313.43/505.37/544.43 ms`. These are plumbing diagnostics only:
scene tags are not blinded ground truth, box AP is unavailable, and the gallery
only records the local LSTM path with `context=not-provided`. No future human
trajectory is drawn.

## Public ground-truth box diagnostic — 2026-08-14

The separate COCO8-pose validation package under
`data/raw/coco8-pose-20260814/` contains four public images and 14 provider
person boxes. The fresh YOLO26s-pose run under
`experiments/runs/coco8-pose-inference-20260814/` records TP `11`, FP `1`, FN
`3`, precision `0.9167`, recall `0.7857`, F1 `0.8462`, and mean matched IoU
`0.8562` at confidence `0.25` and IoU `0.5`. CPU latency is P50/P95/max
`324.91/573.17/603.18` ms. The image-level matrix is `[[0,0],[1,3]]`; all
four images are positive, so specificity is not estimable. The intervals are
descriptive bootstrap diagnostics on four images.

The provider annotations were created before inference and are hash-bound, but
they are not independent human annotation/adjudication. The preflight is
therefore `PASS / admission BLOCKED`; the numbers cannot support a detector
claim, model selection, or Q1 result. No human future trajectory or robot
local path is drawn.

## MATLAB candidate — 2026-08-14

`experiments/runs/matlab-position-learning-20260814/manifest.json` is a fresh
bounded six-state/body-velocity comparison over four scenarios and five
controller labels. All 21 artifact hashes match the manifest and
`hardwareValidated=false`. It is a development comparator, not a confirmatory
result.

## Independent development benchmark — physical-spec rerun — 2026-08-14

The separate package
`experiments/runs/simulation-benchmark-400mm-20260814/` contains 10
replicates of each of three scenarios (30 paired units) with score tuning
disabled and the global path held fixed. All five listed data/plot artifact
hashes match the manifest. The descriptive outcome is MPC `19/30` collisions,
NMPC `20/30`, DWA `12/30`, MPPI `10/30`, and CCA-NMPC `0/30`; corresponding
safe-completion rates are `0.000`, `0.333`, `0.600`, `0.667` and `0.667`.
CCA-NMPC minimum context margin is `0.2194 m`. Because the LSTM source is
simulation-trained and the campaign has no protocol freeze or real capture,
this remains a development stability check rather than PR20/PR21 evidence.
The benchmark is bound to the current 400 x 400 mm user-supplied geometry;
independent measurement and sensor calibration remain open.

## Next admissible artifact

Sau khi PR11/PR12 có direct context CSV và checkpoint tự giám sát đã freeze,
PR20/PR21 mới được mở campaign confirmatory mới. Phân tích của campaign đó sẽ
được ghi bổ sung vào note này với run ID mới; không hồi sinh các package đã
purge.

[[07_Analysis/current-evidence-index]] · [[06_Methods/evaluation-protocol]] ·
[[06_Methods/statistical-analysis]] · [[01_Governance/status-and-provenance]]
