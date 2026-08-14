---
type: evaluation-protocol
status: planned
evidence_status: unknown
---

# Protocol đánh giá

Kế hoạch máy đọc được dùng `schemas/evaluation-config.schema.json` phiên bản
`1.2.0` và phải freeze trước confirmatory run cùng focused-audit/protocol-freeze hashes.

## Kết quả chính của bộ điều khiển

- tỷ lệ va chạm và hoàn thành an toàn, với định nghĩa chính xác;
- clearance vật lý nhỏ nhất và vi phạm safety margin;
- mọi kết quả được tính trên toàn bộ mẫu số đăng ký trước.

`map_run.py` phải tạo đúng một summary và ít nhất một time-series row cho mỗi
cặp `replicate × scenario × controller`. Runner từ chối campaign thiếu baseline,
trùng cặp, thay đổi global path hoặc có trường human-trajectory; vì vậy một
file aggregate không thể che giấu thiếu episode hoặc benchmark không paired.
Aggregate cũng ghi paired nonparametric bootstrap 95% CI theo đơn vị
`replicate × scenario` cho collision rate, safe-completion rate, final goal
error và P95 compute time; CI này là mô tả của campaign và không thay thế
phân tích hierarchical hoặc kiểm định confirmatory.
Artifact còn ghi effect-size CI ghép cặp của CCA-NMPC so với từng baseline.
Quy ước dấu được khóa: giá trị dương nghĩa là CCA-NMPC có completion cao hơn,
collision thấp hơn, goal error thấp hơn hoặc P95 compute time thấp hơn.

## Kết quả phụ của bộ điều khiển

- sai số bám vị trí/yaw và mức hoàn thành đường đi;
- thời gian di chuyển/tiến độ/freezing;
- độ lớn lệnh vận tốc thân, biến thiên/slew lệnh và vi phạm tốc độ bánh;
- slack/residual ràng buộc và lần solve không khả thi;
- số lần/thời lượng fallback và lý do kết thúc;
- thời gian solve P50/P95/P99, deadline miss và bối cảnh phần cứng/phần mềm.

Không suy diễn ưu thế tổng thể từ một chỉ số. Báo safety, tracking và runtime
như một hồ sơ trade-off.

## Kết quả context LSTM

Confusion matrix 4 x 4 cho `left/right/forward/backward`, accuracy, precision,
recall, macro-F1 (all/support-only), speed MAE, context-valid rate, missingness,
timing và subgroup/domain shift. Không vẽ ADE/FDE lên ảnh; nếu đánh giá sai số
dự báo, CCA có thể tính metric prediction riêng trong không gian bản đồ từ nhãn
tương lai độc lập, tách khỏi overlay và controller safety claim. Chất lượng
context phải được nối với độ nhạy local-path trigger, không báo như leaderboard
tách rời.

Confidence direction phải được kiểm bằng reliability bins, ECE, Brier score và
NLL. Runner ghi bootstrap 95% CI cho metric chính, nhưng CI của cửa sổ trong một
recording không thay thế phân tích phân cấp theo recording/subject/source.
Chronological single-run split chỉ là candidate; ID/OOD holdout độc lập mới đủ
để đánh giá generalization.

### Ưu tiên direction-context hiện hành

Với phạm vi né người mới, báo direction accuracy/macro-F1, speed MAE,
context-valid rate, stale/missing rate, thời gian từ thay đổi hướng đến trigger
và thời gian từ trigger đến local-path update. Không tạo ground-truth human path
để cứu một metric; baseline map dùng snapshot footprint, còn CCA-NMPC có thể
dùng prediction nội bộ từ context velocity mà không xuất path lên ảnh.

## Kết quả detector

Với detection bounding box, báo precision/recall/F1, AP/mAP, đường PR, tỷ lệ bỏ
sót, false positive trên mỗi ảnh, sai số subgroup, timing và số đếm TP/FP/FN.
Chỉ báo ma trận nhầm lẫn 2x2 cho bộ phân loại hiện diện người ở cấp ảnh đã đăng
ký riêng, có ảnh âm tính thật và threshold đóng băng.

Hai cờ machine contract luôn là
`bbox_detection_confusion_matrix_required=false` và
`trajectory_regression_confusion_matrix_required=false`. Confusion matrix chỉ
được bật cho classification task có `task_id`, ontology, class order, decision
rule, ground truth và genuine negatives đã hash; artifact phải mang cùng
`classification_semantics`.

## Đánh giá định tính

Dùng các tầng chọn khách quan: run trung vị, clearance xấu nhất, tracking xấu
nhất, lỗi solver/fallback, perception bỏ sót và dự báo quá tự tin. Mỗi panel phải
có ID run/ảnh và provenance. Phải có trường hợp âm; không tạo gallery chỉ chọn
thành công.

Overlay context được chấp nhận phải trỏ selection protocol và source manifest;
box/track, điểm position, speed, direction/confidence và missing marker phải
hiển thị trên frame thật. Không vẽ predicted human path; observation hiện tại
chỉ được hiển thị như điểm/box. Local robot path chỉ xuất hiện trong map
artifact có run ID và dynamic-context semantics.

## Quy thuộc bằng ablation

Tối thiểu so sánh uniform, distance-only, context-off, permuted-context và CCA
đầy đủ ở cùng tổng budget. Tách việc chọn nhóm hoạt động khỏi phân bổ rủi ro và
tách dự báo đã hiệu chuẩn khỏi context.

## Related notes

[[00_MOC/project-map]] · [[06_Methods/methods-overview]] · [[06_Methods/evaluation-protocol]]

## Guard ma trận nhầm lẫn cho LSTM

Khi `lstm_context.enabled=true`, direction classification phải có ontology,
class order, decision rule và ground truth độc lập đã hash; ma trận nhầm lẫn là
artifact bắt buộc cùng raw counts, normalized rates, support và khoảng tin cậy.
Schema `schemas/evaluation-config.schema.json` chặn cấu hình bật LSTM nhưng tắt
task direction hoặc bỏ ma trận. Detection hộp người vẫn báo TP/FP/FN và AP/PR,
không giả định có true-negative pixel/box hợp lệ.

