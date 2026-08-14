# PR22 — Pilot mô phỏng CCA-NMPC theo ngữ cảnh

> **Trạng thái:** `PURGED` (development-only); pilot cũ đã bị xóa trước campaign
> mới vì không phải bằng chứng xác nhận và không được dùng để viết số liệu cho
> bài báo. Purge record: `research/metadata/development-purge-20260813.json`.

## Mục đích

Pilot kiểm tra một pipeline điều khiển tối giản trên map Python: global path
được giữ cố định, còn local path của robot chỉ được tạo lại khi footprint ngữ
cảnh hiện tại xung đột với path hoặc hướng quan sát thay đổi. Ảnh chỉ cung cấp
position, speed, direction, confidence và validity; không tạo, lưu hoặc vẽ
quỹ đạo tương lai của người.

## Bộ điều khiển so sánh

Mọi bộ điều khiển dùng cùng map, global path, mô hình Mecanum, giới hạn vận tốc/
torque, thời gian lấy mẫu và điều kiện dừng:

| ID | Vai trò |
|---|---|
| `mpc` | baseline tuyến tính có ràng buộc |
| `nmpc` | baseline phi tuyến không phân bổ ngữ cảnh |
| `dwa` | baseline tìm kiếm vận tốc cục bộ |
| `mppi` | baseline sampling-based |
| `cca_nmpc` | bộ điều khiển đề xuất với CCA và fixed risk budget |

LSTM là giao diện context bên trong CCA. Vòng score tự giám sát chỉ tối ưu
vận tốc quan sát kế tiếp; các lớp hướng chỉ dùng cho chẩn đoán và quyết định
trigger. Không có logistic checkpoint cũ, dữ liệu synthetic cũ hoặc nhãn hướng
được tái sử dụng.

## Kịch bản và đầu vào

Mỗi kịch bản khóa map, global path, seed và dynamic context event tại các
điểm quan sát. Chỉ CCA-NMPC nhận chuỗi vị trí tương lai nội bộ từ context
velocity; baseline không nhận human future sequence. Prediction không được vẽ
trên ảnh hoặc ghi vào raw context. Các đầu vào context
phải có provenance từ `context.csv` của run thật hoặc một manifest mô phỏng
được tạo mới và ghi riêng là development-only. Không chọn kịch bản sau khi xem
kết quả.

## Chỉ số và failure policy

Mỗi run giữ trong mẫu số, kể cả run lỗi: safe completion, collision, minimum
clearance, path-length ratio, tracking RMSE, control variation, local-path
update count, fallback count và solver latency P50/P95/P99/max. Confusion
matrix chỉ áp dụng cho nhánh nhận diện/ngữ cảnh; không áp dụng cho regression
điều khiển. Không suy ra real-time, an toàn phần cứng hoặc hiệu quả Q1 từ
pilot này.

## Cổng trước confirmatory study

Trước khi mở holdout phải khóa protocol, map, controller versions, seeds,
failure rules, statistical analysis và provenance. Số liệu robot thật chỉ được
đưa vào bài sau khi thư mục final đã được đóng gói bằng
`scripts/python/tools/final_pack.py`; chỉ gói dữ liệu CSV/JSON trực tiếp từ
recorder của bộ điều khiển hoặc firmware được chấp nhận.
