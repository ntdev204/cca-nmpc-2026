# PR23 — Stabilization pilot design

> **Trạng thái:** `FROZEN-PILOT`; đây là protocol thiết kế, không phải bảng kết
> quả. Mọi trace và số liệu của các lần chạy trước đã bị loại khỏi active
> workspace và không được dùng làm evidence mới.

## Mục đích

Pilot này kiểm tra hai failure stratum đã được khóa trước khi chạy: solver không
giữ được nghiệm khả thi trong ngân sách tính toán và fallback không tạo được
chuyển động thoát phù hợp. Không gán tần suất hoặc latency cho hai stratum khi
chưa có run mới.

## Thay đổi được kiểm tra

1. Giữ nguyên identity và thứ tự của tối đa bốn active context slots trong một
   run; không remap warm start sang người khác khi khoảng cách đổi thứ tự.
2. Mọi strategy dùng cùng directional safety fallback, chỉ dùng current
   measurement/LSTM context và map obstacle để thoát điểm tiếp xúc. Nó không
   thay predictor và phải được báo riêng bằng fallback rate/duration.

Plant, clearance, total budget, prediction horizon, solver budget, map--seed
packages và strategy ladder phải giữ matched. Vì cả fallback lẫn active-slot
policy thay đổi cho toàn bộ ladder, pilot chỉ trả lời liệu recovery có hoạt
động hay không; nó không chứng minh lợi thế CCA allocation.

## Tiêu chí stabilization pilot

- giữ đủ 24 run: 2 map × 2 seed × 6 strategy;
- không bỏ collision/fallback/deadline/solver failure;
- báo safety, tracking, fallback, latency và slot churn;
- nếu collision giảm nhưng tracking hoặc fallback xấu, ghi trade-off; không
  gọi đó là superiority;
- Pilot vẫn là candidate và không dùng cho paper claim khi focused audit chưa
  `COMPLETE`.
