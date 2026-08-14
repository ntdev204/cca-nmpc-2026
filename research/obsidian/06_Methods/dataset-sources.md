---
type: dataset-decision
status: reset-before-new-acquisition
evidence_status: provenance-only
decision_date: 2026-08-01
---

# Quyết định nguồn dữ liệu thật — 2026-08-01

## Kết luận tạm thời

Thiết kế tối thiểu phù hợp nhất hiện nay là:

1. **Open Images V7** cho person detection in-domain và auxiliary image-level
   person presence có positive/negative thật;
2. **JRDB/JRDB-Traj** cho robot-view detection OOD và track history trong ảnh/
   panorama thật;
3. **Oxford-IHM** làm external calibrated OOD nếu quyền truy cập được duyệt;
4. **CrowdHuman** chỉ là crowd/occlusion stress cohort tùy chọn, không phải nguồn
   chính và không được phân phối lại raw images.

Đây là quyết định thiết kế. Cohort smoke media thật của vòng trước đã được
xóa trong reset; registry chính chưa admit dataset và chưa có model/result mới
được công bố. Cohort Wikimedia bốn asset tải ngày 2026-08-13 chỉ là candidate
acquisition và vẫn bị khóa admission theo [[07_Analysis/protocol-status-20260813]].

## D4 — Cohort Internet smoke (acquiring, not evidence)

Manifest và raw media của cohort smoke trước đây đã bị xóa theo reset record.
Cohort Wikimedia hiện tại có acquisition ID, license snapshot, source/scene
split và mechanical preflight, nhưng chưa có independent annotation/adjudication
hoặc pretraining-overlap review; vì vậy chưa được dùng làm số liệu Q1 hoặc thay
cho cohort robot-view/OOD.

## D0 — Open Images V7

Nguồn chính thức:

- <https://storage.googleapis.com/openimages/web/index.html>
- <https://storage.googleapis.com/openimages/web/download_v7.html>
- <https://storage.googleapis.com/openimages/web/factsfigures_v7.html>

Lý do chọn:

- có bounding boxes và image-level labels;
- label được human-verified là vắng mặt có `Confidence=0`, nên có thể tạo
  genuine negatives cho task person presence;
- metadata có original URL, landing page, author và license;
- official train/validation/test và công cụ tải theo image ID.

Ràng buộc:

- annotation của Google là CC BY 4.0; ảnh được liệt kê CC BY 2.0 nhưng Google
  không bảo đảm license từng ảnh, nên phải kiểm landing page/license từng asset;
- không dùng thumbnail sinh động làm source-of-truth vì nội dung/resolution có
  thể đổi; tải original/CVDF asset rồi tính SHA-256;
- ảnh không có bbox và không có explicit negative label là `UNKNOWN`, không phải TN;
- phải audit pretraining overlap của detector trước khi gọi đây là external evidence.

Đánh giá detection dùng AP/PR/miss rate và TP/FP/FN. Confusion matrix 2x2 chỉ dùng
cho auxiliary image-level presence task đã tiền đăng ký, với genuine negatives và
threshold khóa trước.

## D1 — JRDB/JRDB-Traj

Nguồn chính thức:

- <https://jrdb.erc.monash.edu/dataset/>
- <https://jrdb.erc.monash.edu/>
- paper trajectory: <https://arxiv.org/abs/2311.02736>

Lý do chọn:

- robot-view indoor/outdoor, camera/LiDAR, 2D/3D boxes và track IDs;
- history quan sát trong robot/sensor frame;
- phù hợp kiểm tra detector/tracker--LSTM context interface;
- đủ thông tin để tạo overlay perception/context trên panorama/frame thật khi
  calibration và pose được kiểm đúng.

Ràng buộc:

- license CC BY-NC-SA 3.0 và download cần tài khoản;
- phải giữ official split, sau đó tách calibration theo whole sequence/site từ
  phần train; không chia sliding windows ngẫu nhiên;
- mọi history point phải ego-motion compensate về cùng anchor
  `base_chassis(t0)`; không ghép trực tiếp tọa độ robot-relative ở các timestamp;
- projection QA báo reprojection error median/P95 và đánh dấu out-of-FOV.

## D2 — Oxford Indoor Human Motion (external OOD)

Nguồn chính thức:

- <https://ori.ox.ac.uk/publications/datasets/oxford-indoor-human-motion-dataset-2024>
- <https://ori-arg.github.io/oxford-indoor-human-motion-dataset/downloads/>

Dataset có static và robot-mounted RGB-D, motion capture 100 Hz và pose của
người/sensor/robot. Nó phù hợp kiểm coordinate transform, context position/speed/
direction và external OOD. Tuy nhiên cần access request/GDPR approval; quy mô
người và site nhỏ, nên không được dùng để claim population generalization.

## D2b — NavWareSet (processed CSV/JSON candidate)

Nguồn chính thức: <https://anr-navware.github.io/navwareset/>.

NavWareSet công bố các gói `x_poses.zip` chứa robot/participant pose CSV và
occupancy JSON, cùng các gói annotated point cloud cho nhiều kịch bản social
navigation. Đây là candidate gần với context/map contract hiện tại. Tuy nhiên
recording cảm biến gốc được phân phối dưới dạng ROS bag; workspace này không
ingest, replay hoặc giữ rosbag. Chỉ một processed CSV/JSON release có điều
khoản cho phép, image/frame hash, calibration và reference audit đầy đủ mới có
thể được xem xét cho PR11. Hiện source này chưa được tải, chưa được admit và
chưa được dùng để huấn luyện.

## D3 — CrowdHuman (tùy chọn)

Nguồn chính thức: <https://www.crowdhuman.org/download.html>.

Chỉ dùng cho stress test crowd/occlusion. Terms giới hạn non-commercial
research/education và cấm phân phối ảnh. Vì cohort này không cung cấp genuine TN
theo protocol presence, chỉ báo AP/miss/error-by-occlusion, không tạo confusion
matrix 2x2.

## Split và leakage contract

- `train`: chỉ dữ liệu được phép huấn luyện;
- `validation`: architecture/checkpoint selection;
- `calibration`: uncertainty/threshold calibration, tách khỏi validation;
- `test_id`: official in-domain test, mở một lần;
- `test_ood`: source/site độc lập, tuyệt đối không tuning.

Group theo source/album/video/recording/site/track trước khi tạo frame, crop hoặc
sliding window. SHA-256 loại exact duplicate; near-duplicate cluster không được
đi qua split. Cỡ mẫu và quota chỉ được khóa sau power/precision rationale tại PR40.

## Overlay context bắt buộc

Mỗi ảnh/chuỗi được chọn theo quy tắc khóa trước phải có source frame, bbox + track
ID, vị trí quan sát, tốc độ, hướng, độ tin cậy, cờ hợp lệ, timestamp, frame/unit
và hash của source/model/calibration. Overlay không vẽ quỹ đạo người. Local path
của robot chỉ được hiển thị trong artifact map Python riêng và không trộn vào
ảnh perception.

## Cổng trước khi tải

- [ ] kiểm account/access của JRDB và Oxford-IHM;
- [ ] khóa source/license manifest và privacy review;
- [ ] khóa sampling quota mà chưa chạy detector;
- [ ] kiểm model pretraining overlap;
- [ ] hai schema ảnh web và context overlay vượt kiểm tra hợp lệ;
- [ ] protocol amendment nếu thay một source.

## Related notes

[[00_MOC/project-map]] · [[06_Methods/methods-overview]] · [[06_Methods/evaluation-protocol]]

## Dataset screening refresh — 2026-08-13

The current candidate comparison is recorded in
[[03_Literature/Sources/source-dataset-candidates-2026]]. The user's own final
robot capture is the primary route. Oxford-IHM is reference-only while its
official raw release is rosbag; it can enter only through an authorized direct
CSV/JSON export that does not require ROS/ROS2 replay. JRDB/JRDB-Pose is an
OOD/perception candidate that requires account and license review. Datasets
whose public workflow depends on ROS or whose terms restrict derivatives remain
outside the active protocol. No candidate is frozen or used for LSTM training.

