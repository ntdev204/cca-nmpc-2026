---
type: research-charter
status: active
scope: research-knowledge
---

# Hiến chương nghiên cứu

## Mục tiêu

Thiết kế và phân tích CCA--NMPC cho chuyển động Mecanum quanh người. LSTM là
interface ngữ cảnh bên trong CCA; YOLO26s-pose là công cụ đo perception. Hướng
context gồm vị trí, tốc độ và trái/phải/tiến/lùi, không phải quỹ đạo tương lai
của người.

## Câu hỏi nghiên cứu

- Ở cùng tổng budget và clearance, phân bổ theo context có thay đổi trade-off
  safety--tracking--feasibility so với phân bổ đồng đều và các bộ điều khiển
  đối chứng hay không?
- Những giả định nào đủ để bảo toàn budget và diễn giải điểm context?
- Lỗi perception, missingness và đổi hướng đi qua CCA như thế nào?
- Global path cố định và local-path trigger có tạo interface dễ kiểm tra không?

## Ranh giới đóng góp

1. Mô hình context đơn giản, ký hiệu rõ và đo được.
2. Allocator fixed-total trong CCA, không mở rộng sang detector hoặc kiến trúc
   LSTM mới.
3. Các mệnh đề algebra/model-internal với giả định được nêu rõ.
4. Protocol đánh giá có đối chứng và failure accounting được định nghĩa trước.

## Nguyên tắc

- Không tái sử dụng số liệu, dataset, checkpoint hoặc figure cũ.
- Không dùng ảnh tự tạo/AI-generated làm tập kiểm tra ảnh người thật.
- Không suy luận real-time, hardware safety hoặc stability từ thiết kế lý thuyết.
- Không viết `improves`, `outperforms` hoặc `guarantees` nếu claim register chưa
  được kiểm định.

[[00_MOC/project-map]] · [[01_Governance/claim-register]] · [[04_Research_Gap/research-gap]] · [[01_Governance/status-and-provenance]]
