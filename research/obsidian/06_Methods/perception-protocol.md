---
type: perception-protocol
status: candidate
evidence_status: candidate-not-evidence
contribution_role: measurement-interface
---

# Protocol đo người

`yolo26s-pose.pt` là giao diện đo lường, không phải đóng góp. Mỗi quan sát phải
gồm hộp người, 17 keypoint, confidence/visibility, timestamp và định danh model.
Mục tiêu là định lượng sai số hộp, sai số pose, missing keypoint và ảnh hưởng
downstream của chúng lên tracking, LSTM và CCA-NMPC.

### Nguồn công cụ và giới hạn

Theo tài liệu chính thức của Ultralytics ([Pose Estimation with Ultralytics
YOLO](https://docs.ultralytics.com/tasks/pose), truy cập 2026-08-12), pose
output gồm các tọa độ keypoint 2-D, confidence/visibility và instance boxes;
mô hình pose COCO mặc định có 17 keypoint. Bảng tốc độ/mAP trên trang đó là
benchmark COCO của nhà cung cấp, không phải kết quả của robot này. Vì vậy
`yolo26s-pose.pt` chỉ được dùng làm tool version-pinned trong manifest; mọi
metric của cohort riêng phải dùng annotation mù và phần cứng/thiết lập đã khai
báo.

## Tập kiểm thử

Dùng Internet-image test cohort trong [[06_Methods/dataset-protocol]]: ảnh thật tải từ Internet, có
provenance và giấy phép cho tải, xử lý và annotation derivative. Ảnh lab,
simulator, ảnh tự tạo hoặc AI không được thay thế cohort này. Tập kiểm thử cuối
phải có cả ảnh có người và
không có người, đồng thời phân tầng theo mức che khuất, kích thước người, mật độ,
ánh sáng và miền trong/ngoài nhà. Calibration, test ID và test OOD đều held-out;
từng asset phải qua annotation audit mù và privacy/legal review theo manifest 2.0.0.

## Ghép cặp detection và pose

Đóng băng ngưỡng confidence và quy tắc ghép IoU trước khi mở kết quả test. Ghép
một-một tạo TP, FP và FN cho bounding box. Bài toán detection một lớp không có
TN tự nhiên nên không được ép thành ma trận nhầm lẫn 2x2. Nếu đăng ký trước một
bài toán hiện diện người ở cấp ảnh, ảnh âm tính thật cùng threshold đã đóng băng
mới cung cấp TN/FP/FN/TP cho bài toán phụ đó.

Với mỗi TP, keypoint được ghép theo instance người và đánh giá bằng Object
Keypoint Similarity (OKS). Annotation phải phân biệt visible, occluded và
unlabeled; joint không được gán nhãn không được tính như dự đoán sai. Không dùng
keypoint sinh tự động làm ground truth cuối.

## Chỉ số

- số đếm TP/FP/FN, precision, recall và F1 cùng khoảng tin cậy;
- AP tại các ngưỡng IoU đã khai báo và mAP@[.50:.95] khi annotation hỗ trợ;
- số dương tính giả trên mỗi ảnh và tỷ lệ bỏ sót;
- đường cong PR và độ nhạy theo ngưỡng confidence;
- chỉ số theo che khuất, tỷ lệ, mật độ, nguồn và domain;
- thời gian suy luận cùng bối cảnh phần cứng/phần mềm;
- phân loại định tính false positive/false negative.
- pose AP theo OKS, AP50/AP75, per-joint localization error và PCK đã định nghĩa;
- tỷ lệ keypoint thiếu/sai theo joint, che khuất, kích thước người và miền;
- calibration của confidence hộp/keypoint và độ trễ end-to-end.

`det_eval.py` ghi thêm nonparametric bootstrap 95% CI theo đơn vị ảnh cho
presence classification và các metric TP/FP/FN của bounding box. Seed, số lần
lặp và cờ `descriptive_only` nằm trong metrics/manifest; CI không thay thế
annotation audit mù, phân tầng theo source hoặc validation độc lập.

Chỉ với bài toán hiện diện ở cấp ảnh đã đăng ký trước, báo thêm ma trận nhầm lẫn
2x2 đầy đủ, sensitivity, specificity, balanced accuracy và khoảng tin cậy.

## Nghiên cứu lan truyền sai số

Tiêm các phân phối bỏ sót/dương tính giả/sai số hộp/keypoint đo được vào replay
hoặc mô phỏng sau khi lệnh tạm dừng được gỡ. Định lượng ảnh hưởng lên tính liên
tục của track, đầu vào LSTM, pose cue của context, thứ tự phân bổ và kết quả bộ
điều khiển. Đây là cầu nối bằng chứng từ giao diện đo lường tới CCA-NMPC.

## Overlay context trên ảnh

Manifest Internet hiện tại là cohort ảnh tĩnh với scene tags ở mức candidate;
chưa có nhãn hiện diện người đã được phê duyệt, annotation mù hoặc adjudication.
Vì một ảnh tĩnh không chứa lịch sử thời gian, cohort này không được
dùng để suy ra tốc độ hoặc hướng LSTM. `det_eval.py` chỉ tạo detector overlay
ở chế độ mặc định.

Khi có một bản ghi context đã ghép cặp với từng frame, có thể gọi thêm
`--context <context-overlay.json>`. Tệp này phải dùng schema
`cca-context-overlay-v1` và cung cấp đúng một snapshot cho mỗi `asset_id`:
`position_xy`, `heading_unit`, `speed_mps`, `direction`, `context_valid`,
`confidence`, `timestamp_ns`, `frame_id`, `track_id`, `coordinate_units`,
`source_sha256` và `model_sha256`. `direction` phải khớp với vector heading;
hash nguồn và checkpoint phải được ghi lại.

Overlay ghép context chỉ hiển thị vị trí hiện tại, tốc độ, hướng, confidence,
validity, track/frame ID, hash rút gọn và `LSTM_PATH=<local checkpoint path>`
khi `det_eval.py --lstm-checkpoint` được cung cấp. Tool kiểm tra SHA-256 của
checkpoint này khớp với `model_sha256`. Với ảnh tĩnh không có context ghép cặp,
`--lstm-checkpoint` chỉ tạo một dòng provenance `context=not-provided` và
`LSTM_PATH=<local checkpoint path>` trên ảnh; không điền tốc độ/hướng giả và
không tạo context record. Không truyền checkpoint thì ảnh ghi rõ
`LSTM_PATH=<not-provided>`. Loader từ chối các trường `path`, `trajectory`,
`future_positions` và `future_path`, vì ảnh không được dùng để vẽ quỹ đạo người.
Các biến thể tên trường có tiền tố `future_`, `trajectory_`, `path_` hoặc
`predicted_` cũng bị loader từ chối.
Local path của robot chỉ xuất hiện trên artifact map Python. Nếu chưa có chuỗi
frame/context đã ghép cặp, không được điền giá trị giả để tạo overlay LSTM.

## Ranh giới báo cáo

Không gọi detector là chính xác chỉ từ vài ảnh minh họa. Không claim real-time
từ timing trên máy phát triển. Phải định danh trọng số mô hình, giấy phép nguồn
và phiên bản tiền xử lý.

Related hub: [[00_MOC/project-map]]

