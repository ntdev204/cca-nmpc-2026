---
type: statistical-analysis-plan
status: planned
evidence_status: unknown
---

# Kế hoạch phân tích thống kê

Đóng băng kế hoạch này trước khi mở dữ liệu xác nhận.

## Đơn vị và sự phụ thuộc

Đơn vị thực nghiệm là scenario/seed độc lập hoặc recording/subject độc lập,
không phải mỗi timestep quỹ đạo hay frame video. Ghép cặp bộ điều khiển trong
cùng scenario/seed. Dùng resampling/mô hình phân cấp khi quan sát lồng trong
subject, scene hoặc source.

Run confirmatory đã bắt đầu luôn có
`included_in_registered_denominator=true`. Manifest `completed/failed` phải giữ
termination/failure, collision, fallback, constraint và deadline blocks; block
không áp dụng có reason thay vì bị xóa. Nhờ vậy ITT-like denominator được kiểm
bằng máy thay vì suy ra từ CSV còn sót.

## Cỡ mẫu

Chọn cỡ mẫu xác nhận từ hiệu ứng thực tiễn nhỏ nhất có ý nghĩa và độ rộng khoảng
tin cậy/power mong muốn. Pilot mới có thể ước lượng phương sai nhưng phải loại
khỏi test cuối. Không suy power từ độ lớn kết quả legacy.

## Phân tích

- kết quả nhị phân ghép cặp: chênh lệch hiệu ứng ghép cặp với CI và McNemar/mixed model phù hợp;
- clearance/tracking/runtime: chênh lệch ghép cặp với hierarchical bootstrap CI; dùng thống kê robust cho timing lệch;
- chỉ số detector/predictor: bootstrap theo nguồn ảnh hoặc nhóm sequence/subject;
- hiệu chuẩn: CI của coverage thực nghiệm, biểu đồ reliability và proper score;
- dị biệt scenario: báo interaction/effect theo hình học, mật độ, che khuất và domain.

Đối với map benchmark, runner ghi paired nonparametric bootstrap 95% CI với
đơn vị `replicate × scenario` cho các metric mô tả chính. Đây là CI mô tả của
artifact; phân tích xác nhận vẫn phải giữ denominator, dùng hierarchical model
hoặc kiểm định ghép cặp phù hợp và không được suy ưu thế từ CI chồng lấn.
Runner cũng ghi effect-size CI của CCA-NMPC so với từng baseline với quy ước
dấu cố định; effect size không thay thế kiểm định hoặc bằng chứng phần cứng.

## Đa kiểm định và báo cáo

Khai báo một đối sánh chính và số ít đầu ra chính. Hiệu chỉnh các so sánh phụ
xác nhận, ví dụ Holm; gắn nhãn phân tích thăm dò. Báo kích thước hiệu ứng và bất
định, không chỉ p-value. Giữ run thất bại/va chạm/timeout trong mẫu số; định
nghĩa cách xử lý chỉ số liên tục sau khi kết thúc sớm.

## Kiểm tra độ vững

- ngưỡng va chạm/clearance thay thế được cố định trước phân tích;
- gồm mọi thất bại so với gán worst-case bảo thủ;
- phân tích leave-one-group-out theo seed/scenario;
- sweep ngưỡng confidence/IoU cho detector;
- độ nhạy hiệu chuẩn và domain shift của LSTM;
- độ nhạy theo budget/temperature/đặc trưng context của CCA.

## Semantics của confusion matrix

Bounding-box detection và trajectory regression có cờ confusion matrix bằng
`false`. Chỉ classification task riêng có ontology, class order, decision rule,
ground truth và genuine negatives đã freeze mới sinh ma trận; báo cả counts,
rates, support và CI. Semantic contract của artifact phải khớp evaluation config.

## Khả năng tái lập

Mã phân tích đọc raw artifact bất biến và tạo bảng kết quả máy đọc được, dữ liệu
hình cùng bản ghi phiên/môi trường. Sửa bảng tính thủ công không phải bước phân tích.
Config validate theo `schemas/evaluation-config.schema.json`; run outcome theo
`schemas/run-manifest.schema.json` phiên bản `1.1.0`.

## Related notes

[[00_MOC/project-map]] · [[06_Methods/methods-overview]] · [[06_Methods/evaluation-protocol]]

