---
type: context-model-design
status: design-only
scope: research-knowledge
contribution_role: context-interface-inside-cca
---

# LSTM trong CCA

LSTM là một thành phần bên trong Context-Conditioned Allocation (CCA), không
phải một bộ điều khiển độc lập. Nó nén history quan sát ngắn thành context để
CCA phân bổ ngân sách rủi ro. LSTM chỉ xuất context snapshot; CCA-NMPC mới có
quyền tích phân vận tốc context thành chuỗi vị trí tương lai nội bộ cho chance
rows. Chuỗi đó không được lưu hoặc vẽ lên ảnh và không thay thế local planner.

## Giao diện perception--context

YOLO26s-pose chỉ là công cụ đo từ ảnh: hộp người, keypoint, vị trí tương đối,
độ tin cậy và thời gian. Tracker tạo history; LSTM nhận history gồm vị trí
tương đối, sai phân vận tốc và cờ hợp lệ. Đầu ra tối thiểu là vị trí quan sát
cuối, tốc độ quan sát/dự báo, một hướng trong bốn lớp và độ tin cậy. Khi
history không đủ hoặc perception mất tín hiệu, LSTM trả `context_valid=false`.
Tốc độ context bị chặn bởi `max_speed_mps=2.0` trong study contract; output vượt
ngưỡng bị coi là OOD và không được đưa vào chance rows.

## Học không giám sát theo điểm

Không dùng nhãn hướng thủ công cho mục tiêu tối ưu. Mục tiêu tự giám sát được
tạo từ vận tốc quan sát ở đoạn thời gian kế tiếp. Vector vận tốc dự báo được
chiếu lên bốn trục cố định để suy ra hướng; chênh lệch điểm giữa các trục tạo
độ tin cậy. Sau lần chạy robot, `scripts/python/tools/ctx_run.py` đọc
`context.csv` để tạo cửa sổ vận tốc quan sát kế tiếp. Vòng score chỉ dùng để
chọn checkpoint và ngưỡng; báo cáo học thuật
vẫn phải định nghĩa trước confusion matrix, speed error, missingness và
calibration.

Inference phải dùng loader schema
`cca-context-direction-lstm-score-trained-checkpoint-v2`, kiểm tra đầy đủ
`model_config`, `state_dict`, chế độ `self_supervised_score_loop` và cờ không
dùng nhãn hướng. Checkpoint sai schema hoặc không khớp state/config bị từ chối;
việc load thành công chỉ chứng minh software parity, không chứng minh chất
lượng dự báo. Nếu checkpoint có calibration metadata, loader chỉ chấp nhận
temperature scaling được fit từ split `calibration` độc lập và áp dụng chính
nhiệt độ đó khi suy ra direction confidence; metadata khai báo nguồn `test_id`
hoặc `test_ood` bị từ chối.

Sau inference, vector vận tốc một mẫu được chuẩn hóa thành heading hiện tại,
tốc độ và confidence rồi chuyển thành một `HumanHeadingObservation`. Adapter này
chỉ xuất snapshot hiện tại cho CCA; việc tích phân vector thành chuỗi vị trí
tương lai chỉ xảy ra bên trong CCA-NMPC khi lập chance rows, không tạo artifact
hoặc overlay.

Baseline kiến thức là dấu của vận tốc không đổi. Mô hình LSTM và baseline phải
dùng cùng history, chuẩn hóa chỉ fit trên train, validation để chọn checkpoint.
Sau khi checkpoint đã khóa, runner fit một nhiệt độ vô hướng bằng temperature
scaling trên các cửa sổ hợp lệ của split `calibration`; không dùng
`test_id`/`test_ood` để chọn nhiệt độ hay ngưỡng. Manifest ghi phương pháp,
nhiệt độ, số mẫu hợp lệ, NLL trước/sau và nguồn split. Nếu không có frozen
calibration split, runner chỉ ghi `status=not_fit` và các ECE/Brier/NLL là
chẩn đoán chưa hiệu chuẩn, không được diễn giải thành calibration độc lập.

Runner hiện hành cũng tính baseline constant-velocity và Kalman-velocity trên
cùng cửa sổ và target. Hai baseline không huấn luyện này chỉ dùng vận tốc quan
sát trong history; trường `direction` không đi vào optimizer.

Mỗi lần đánh giá còn ghi direction reliability bins, expected calibration error
(ECE), Brier score và negative log-likelihood sau khi áp dụng cùng nhiệt độ đã
khóa (nếu có). Khoảng tin cậy 95% của score,
speed MAE, macro-F1, direction accuracy, coverage, Brier và NLL được tính bằng
bootstrap lặp 400 lần với seed được ghi trong manifest. Đây là uncertainty của
đơn vị cửa sổ trong run; không thay thế bootstrap phân cấp theo recording,
subject hoặc source ở phân tích xác nhận. Chế độ mặc định của runner là
chronological single-run split, nên manifest của chế độ này luôn ghi
`independent_id_ood_holdout=false` và không được dùng để claim generalization.
Mỗi split cũng xuất confusion matrix và bảng `direction_class_metrics` gồm
precision, recall, F1 và support cho bốn hướng; các bảng này chỉ tính trên các
target có vận tốc đạt ngưỡng, còn sample đứng yên được ghi riêng trong coverage.

Để mở đánh giá xác nhận, `ctx_run.py` nhận thêm `--split-manifest` theo schema
`cca-context-split-manifest-v1`. Manifest phải khóa trước training, gán toàn bộ
recording/episode vào đúng một trong năm purpose `train`, `validation`,
`calibration`, `test_id`, `test_ood`, và xác nhận các group không giao nhau.
Runner tạo cửa sổ riêng theo từng group, không cho một recording rơi qua nhiều
split, dùng validation để chọn checkpoint, giữ calibration chỉ cho hiệu chuẩn,
và mở `test_id`/`test_ood` cho đánh giá độc lập. Calibration, `test_id` và
`test_ood` mỗi split phải có ít nhất 30 cửa sổ hợp lệ; thiếu assignment, thiếu
mẫu, split mâu thuẫn, trường ngoài schema hoặc manifest không hợp lệ đều bị từ
chối.

Từ checkpoint 2026-08-13, runner chuẩn hóa direction về sáu token hợp lệ
(`left`, `right`, `forward`, `backward`, `unknown`, `invalid`) và fail-closed
trên token khác. Nhánh có `--split-manifest` còn yêu cầu mỗi dòng có đủ
`recording_id`, `episode_id`, `source_id`, `scene_id`; các khóa này chỉ được
ghi từ recording thật, không được suy ra từ cửa sổ hoặc sinh tự động.

## Context-to-map contract

CCA nhận `position`, `speed`, `direction`, `confidence` và `context_valid`. Map
Python dùng các trường này để cập nhật footprint tại vị trí động quan sát được
và kiểm tra conflict. Chỉ CCA-NMPC có thể tích phân snapshot velocity thành
chuỗi vị trí tương lai nội bộ cho chance rows; chuỗi đó không được xuất hoặc
chiếu lên ảnh. Global path được lập một lần; local path chỉ được tạo lại khi
có conflict mới hoặc hướng thay đổi.

**Ranh giới artifact hiện tại.** Gói map candidate hiện tại truyền snapshot
direction/speed qua adapter để kiểm tra map và trigger; nó chưa nạp một
checkpoint LSTM đã huấn luyện. Vì vậy gói này không phải bằng chứng closed-loop
CCA--LSTM. Confirmatory run chỉ được mở khi có checkpoint từ `ctx_run.py`, hash
dataset/config/code, split `test_id` và `test_ood`, cùng log rằng đầu ra LSTM đã
đi vào CCA trước khi tạo local path. Checkpoint phải kèm đường dẫn tương đối,
SHA-256 và source/flag metadata của manifest capture; `map_run.py` phải mở
manifest, kiểm hash và xác nhận `verified`, `integrity_status`, `context_only`
và `human_trajectory_generated=false` trước khi nhận checkpoint. Với capture
source khác `unknown`, manifest còn phải bind `calibration.json`; sidecar này
được kiểm tra sensor identity, camera intrinsics, camera/LiDAR extrinsics và
residual calibration trước khi checkpoint được admit.

Nhánh confirmatory và nhánh CCA-NMPC online trên phần cứng còn yêu cầu
`calibration.status=fit` với temperature scaling từ split `calibration`, đủ
số mẫu tối thiểu và cờ độc lập với train/validation/test. Checkpoint
`not_fit` chỉ được phép chạy trong pilot candidate để phát hiện failure; loader
điều khiển từ chối nó trước khi mở thiết bị hoặc gửi lệnh vận tốc.

## External real-offline mechanics candidate — 2026-08-13

The NavWareSet scene-13 processed CSV is used once to exercise the score loop
with real recorded robot/person positions. The conversion keeps only the
current robot-local context and derives the next-velocity target inside
`ctx_run.py`; it does not create or export a human future path. Because the
source has no target camera frames, Astra-S/N10P calibration, Mecanum geometry
or independent ID/OOD groups, its five-seed checkpoint is candidate mechanics
output and cannot satisfy the target capture admission rule above.

## Liên kết

[[00_MOC/project-map]] · [[06_Methods/perception-protocol]] · [[06_Methods/dataset-protocol]] · [[05_Theory/context-aware-risk-allocation]] · [[06_Methods/evaluation-protocol]]
