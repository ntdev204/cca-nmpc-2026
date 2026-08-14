---
type: learning-design
status: design-only
scope: research-knowledge
---

# Học không giám sát và vòng chấm điểm

## Ranh giới học

Nhánh ảnh dùng mục tiêu tự giám sát theo thời gian: dự báo vận tốc context quan
sát được ở đoạn kế tiếp; hướng được suy ra bằng điểm với bốn trục cố định.
Nhánh map chỉ dùng score để chọn các tham số local-path bị chặn. NMPC vẫn là bộ
điều khiển pose bằng lệnh vận tốc và giữ hard constraints về state, command rate,
fallback và
deadline.

Không đưa nhãn hướng, future human path, collision label hoặc target command vào
optimizer. Annotation chỉ phục vụ kiểm tra độc lập sau khi giao thức đã khóa.

## Vòng score

1. Khóa đặc tả dữ liệu, feature, transform và safety gates.
2. Sinh một candidate LSTM hoặc một policy parameter trong miền bị chặn.
3. Tính score vô hướng đồng thời giữ vector metric đầy đủ.
4. Loại candidate vi phạm hard gate; giữ candidate tốt nhất theo validation.
5. Dừng ở ngưỡng định trước hoặc plateau; sau đó mới mở calibration và tập giữ
   lại.

Score chỉ là cơ chế chọn candidate, không thay thế confusion matrix, speed MAE,
missingness, clearance, collision, completion, fallback hay timing. RL nếu được
dùng chỉ tối ưu bounded allocation/trigger policy; không phát lệnh vận tốc trực
tiếp và
không thay đổi mô hình CCA--NMPC.

[[00_MOC/project-map]] · [[06_Methods/lstm-protocol]] · [[06_Methods/simulation-protocol]] · [[06_Methods/evaluation-protocol]]
