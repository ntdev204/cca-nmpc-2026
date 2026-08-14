---
type: claim-register
status: design-only
scope: research-knowledge
---

# Sổ đăng ký luận điểm

Đây là danh sách luận điểm có thể kiểm định, chưa phải bảng kết quả. Một luận
điểm chỉ được chuyển sang bài báo khi nguồn tài liệu, định nghĩa, protocol và
phân tích tương ứng đã được duyệt.

| ID | Luận điểm dự kiến | Điều kiện kiểm định |
|---|---|---|
| C-NOV | CCA phân bổ fixed-total risk theo context trong position-state Mecanum CCA-NMPC với clearance giữ cố định. | nearest-work matrix, phương trình đối chiếu và phản biện novelty độc lập |
| C-ALG | Allocator bảo toàn tổng allowance, thứ tự ưu tiên và trường hợp uniform dưới active set cố định. | giả định, định lý và property checks nhất quán |
| C-CTX | LSTM bên trong CCA cung cấp position/speed/coarse direction từ history mà không dùng direction label trong optimizer. | protocol tự giám sát, confusion matrix bốn lớp, speed error và missingness |
| C-PATH | Global path giữ cố định; chỉ local path của robot thay đổi khi conflict hoặc hướng context đổi. | contract map/controller và trace trigger không mâu thuẫn |
| C-BENCH | So sánh công bằng với MPC, NMPC, DWA và MPPI dùng cùng map, footprint, reference, clearance và ngân sách tuning. | benchmark protocol và denominator được khóa trước |
| C-ROBUST | Context invalid, dropout hoặc direction uncertainty kích hoạt fallback rõ ràng; chỉ CCA-NMPC giữ dự đoán vị trí người nội bộ, không xuất hoặc vẽ chuỗi đó. | state machine, stale rule và failure accounting |
| C-HW | Astra S, N10P và body-velocity interface chỉ được mô tả trong miền phần cứng thực sự hiệu chuẩn. | calibration, timing, safety-stop và provenance riêng |

## Tuyên bố bị cấm khi chưa có kiểm định

Không dùng `novel`, `real-time`, `hardware-ready`, `universally safer`,
`guaranteed stability`, superiority tổng thể, detector mới, LSTM architecture
mới hoặc human-trajectory forecasting từ ảnh tĩnh. Dự đoán nội bộ causal của
CCA-NMPC trên context động không được mô tả như một ảnh overlay hoặc như dữ
liệu ground-truth được cấp cho controller.

[[00_MOC/project-map]] · [[04_Research_Gap/research-gap]] · [[05_Theory/proof-obligations]] · [[01_Governance/status-and-provenance]]
