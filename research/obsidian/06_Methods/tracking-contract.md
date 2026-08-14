---
type: tracking-design
status: design-only
scope: research-knowledge
---

# Hợp đồng tracking và chuyển đổi context

Note này định nghĩa giao diện, không chứa kết quả detector hoặc log tracking.
YOLO26s-pose cung cấp box/keypoint, timestamp và confidence; tracker duy trì
association trong ảnh; phép biến đổi sensor đưa vị trí hợp lệ về frame robot.

## Nguyên tắc association

So sánh tối thiểu gồm không tracker, greedy center/IoU và Kalman constant-
velocity. Quy tắc gate, xử lý miss, ID-switch, fragment, stale frame và
missingness phải được khóa trước khi mở tập giữ lại. Annotation chỉ dùng cho
đánh giá độc lập, không được làm history thay detector trong nhánh chính.

## Cảm biến và frame

Với Astra S và N10P, phải định nghĩa intrinsic/extrinsic, timestamp offset,
depth/LiDAR validity mask, frame convention và reprojection residual. Ảnh tĩnh
chỉ tạo image-plane context; không gọi proxy này là mét robot nếu chưa có hiệu
chuẩn cảm biến.

## Điều kiện hợp lệ

History không đủ, detector mất tín hiệu hoặc transform stale trả
`context_valid=false`. CCA chuyển cờ này thành fallback an toàn; CCA-NMPC có
thể nội suy vị trí tương lai nội bộ từ velocity đã kiểm tra, nhưng tracker
không ghi chuỗi đó vào ảnh hay raw context. Overlay chỉ hiển thị box, vị trí,
tốc độ, hướng và missing marker.

[[00_MOC/project-map]] · [[06_Methods/perception-protocol]] · [[06_Methods/lstm-protocol]] · [[06_Methods/dataset-protocol]]
