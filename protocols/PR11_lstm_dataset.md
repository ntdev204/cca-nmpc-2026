# PR11 — Dataset context cho LSTM

> **Trạng thái:** `REVIEWED`; thiết kế schema/causal/split/no-human-path và
> strict timestamp đã qua review, nhưng dataset thật chưa được sinh/freeze.  
> **Đầu vào:** ảnh/chuỗi ảnh thật từ PR10 hoặc recording có consent, license và
> calibration riêng.

## 1. Bài toán và đơn vị dữ liệu

Dataset lưu các cửa sổ context causal của người: vị trí, tốc độ, hướng
trái/phải/tiến/lùi, confidence và validity. LSTM học vector vận tốc ở bước kế
tiếp theo bằng mục tiêu tự giám sát; dataset không lưu hoặc sinh quỹ đạo người.

Đơn vị độc lập là `recording/context episode`, không phải sliding window. Tất
cả window từ cùng recording, scene, participant/track và near-duplicate source
phải ở cùng split.

## 2. Frame, thời gian và context reference

Mỗi record ghi camera/image frame và, khi claim dùng mét, robot-local frame cùng
calibration hash. Vị trí hiện tại được chuyển về robot frame bằng

\[
p^{\mathrm{local}}_{h,t}=R(\psi_{r,t})^{\mathsf T}
(p^{\mathrm{world}}_{h,t}-p^{\mathrm{world}}_{r,t}).
\]

Ảnh không có depth/homography/calibration chỉ hỗ trợ image-plane context và
không được nối vào safety metric theo mét. Timestamp dùng clock đã xác định;
ghi dropped/duplicated frame, offset, latency và validity thay vì nội suy tương
lai. Context reference độc lập với detector/LSTM đang đánh giá.

## 3. Schema tối thiểu

Mỗi frame/track record có:

- `dataset_version`, `source_id`, `recording_id`, `scene_id`, `track_id`;
- `frame_id`, timestamp, image hash và quan hệ frame trước/sau;
- bbox, keypoints, detector confidence, occlusion và validity mask;
- robot pose, camera intrinsics/extrinsics và calibration hash;
- current position, observed speed/direction và quality flag;
- observed history, self-supervised next-velocity target, split/group/OOD labels;
- parent raw hashes và processing-code commit.

Không ghi output LSTM đè lên dataset gốc. Prediction artifact chỉ chứa context
position/speed/direction/confidence/validity, latency và failure code.

## 4. Nội dung và strata

Giữ các điều kiện crossing, side-passing, stop--go, turning, group và occlusion
như metadata để bao phủ context; tên behavior không tự động là intent claim.
Strata bắt buộc gồm speed, distance, density, occlusion, camera motion, lighting,
site, sensor quality và direction class. Synthetic sequences chỉ dùng debug hoặc
pretraining riêng; không được vào `test_id`/`test_ood` và không hỗ trợ claim người
thật.

## 5. Split chống leakage

Khóa năm mục đích `train`, `validation`, `calibration`, `test_id`, `test_ood`.
Split group được tạo trước khi trích cửa sổ; cùng person, recording, scene,
camera burst, background burst hoặc synthetic seed không được qua hai split.
Scaler/imputation chỉ fit trên train. OOD phải là shift thật đã khóa (site/camera,
density, occlusion, lighting hoặc sensor), không dùng để chọn model.

## 6. Kiểm soát chất lượng

- schema, đơn vị, range, timestamp monotonic và image/frame hash;
- transform round-trip, calibration residual và image-to-local provenance;
- ID switch, gap, impossible speed và duplicate frame;
- split intersection, label/reference independence và license/consent;
- flow count từ raw tới eligible từng split, không im lặng loại lỗi.

## 7. Context overlay

Mỗi case giữ frame thật đã hash và hiển thị bbox/keypoint, track ID, vị trí hiện
tại, tốc độ, hướng, confidence, `context_valid`, timestamp và cảnh báo
calibration/model/data version. Không vẽ human trajectory, future coordinate,
robot local path hoặc đường dự báo lên ảnh. Robot local path chỉ xuất hiện trong
map benchmark. Chọn trước các case median, boundary, failure và OOD; mọi frame
phải có `real_media=true`, `ai_generated=false` và parent manifest.

## 8. Registry và versioning

Data card ghi source/license/consent, thiết bị, preprocessing, split logic, bias,
privacy, retention và prohibited use. Dataset version đổi khi source, frame
transform, split, annotation/reference hoặc exclusion rule đổi.

Registry task là `person_context_sequence`. `context_sequence_contract` phải có
`test_id`/`test_ood` là context thật, không synthetic, frame/video hash, reference
độc lập, image-to-local calibration và output fields `position/speed/direction`.
`source_kind: simulation` bị từ chối cho dataset context đóng băng.

## 9. Cổng chấp nhận

PR11 đạt `VERIFIED` khi registry qua schema 2.0.0, split-disjoint và provenance
audit pass, data card/license/consent đầy đủ, OOD khóa trước kết quả và context
overlay tái sinh được với bbox/keypoint, position/speed/direction, validity và
hash. Không có human-path artifact trong dataset hoặc overlay.

## 10. Implementation checkpoint — 2026-08-13 05:45 ICT

The ingestion path now normalizes direction tokens and rejects values outside
`left/right/forward/backward/unknown/invalid`. A confirmatory split also requires
nonempty `recording_id`, `episode_id`, `source_id`, and `scene_id` metadata on
every row before window construction; this prevents a split manifest from
appearing valid while its other leakage keys are absent. The check is applied
only to the confirmatory path and does not manufacture or infer missing groups.

Source hash: `scripts/python/tools/ctx_run.py` SHA-256
`85EA3C2F7F1673662CB6FB1F5D480E13C57D3CC8356EC254214E2F33F21C7E91`.
Focused replay tests and the full Python suite pass. PR11 is `REVIEWED` for
design only: no permitted real context recording, calibrated transform, frozen
split, or dataset card has been admitted.

## 11. Continuation checkpoint — 2026-08-13 06:06 ICT

The same ingestion contract is now used by the hash-bound calibration-sidecar
path. `ctx_run.py` validates the capture manifest, sensor identity and
`calibration.json` digest before confirmatory window construction; it does not
infer a missing recording group or calibration record. Current source hash:
`B58A90E237F2615D53FA4D4D363818329DC4EFF9B372E0DEAA318B6EC12E356F`.
Full Python QA is `169 passed`; no permitted real context recording or frozen
dataset has been admitted, so the execution gate remains open despite the
`REVIEWED` design status.
