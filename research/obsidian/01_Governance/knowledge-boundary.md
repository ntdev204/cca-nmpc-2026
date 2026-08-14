---
type: vault-governance
status: active
scope: research-knowledge
---

# Ranh giới tri thức của vault

Obsidian là bản đồ tri thức nghiên cứu: nguồn tài liệu, khoảng trống, giả
thuyết, ký hiệu, mô hình, chứng minh, giao diện phương pháp, quyết định phạm
vi và phân tích đã kiểm tra của các thí nghiệm. Nó không phải kho dataset,
checkpoint, log chạy, biểu đồ, bảng kết quả gốc hay nhật ký thực nghiệm.

## Quy tắc lưu trữ

- File Markdown có thể chứa phân tích phương pháp, diễn giải, thống kê đã được
  kiểm tra và bài học rút ra; mỗi con số phải trỏ tới gói kết quả bên ngoài qua
  run ID, manifest và SHA-256. Không chép raw log hay bảng kết quả gốc vào vault.
- Ảnh Internet, manifest, model, raw log, seed, figure và bảng kết quả nằm ở
  kho dữ liệu riêng khi triển khai; Obsidian lưu liên kết provenance và phân
  tích, không nhân bản artifact.
- Không dùng ghi chú cũ để phục hồi số liệu đã xóa. Mọi tuyên bố trong paper
  phải được duyệt riêng theo claim register và nguồn trích dẫn.
- Tên file dùng lower-kebab-case, một file một khái niệm, không nhúng ngày,
  revision hoặc trạng thái vào tên; ngày và trạng thái chỉ ở front matter.

## Luồng tri thức

`source -> gap -> theory -> method -> evidence-analysis -> decision`.
Các node phải có ít nhất một liên kết tới hub [[00_MOC/project-map]] và liên kết
tới node trước/sau trong chuỗi khi phù hợp. Template chỉ dành cho ghi chú tri
thức và phân tích có provenance; không tạo note `experiment` hoặc `result` để
thay thế kho artifact riêng.

## Phạm vi hiện tại

Khoảng trống, mô hình CCA--NMPC, LSTM như một interface trong CCA, YOLO26s-pose
như công cụ perception, map Python với global path cố định và local-path trigger
đã được mô tả ở các note liên quan. Kết quả thực nghiệm gốc được quản lý ngoài
vault; phần phân tích và diễn giải có liên kết provenance được ghi trong
[[07_Analysis/experimental-analysis]] để sau này có thể chọn lọc đưa vào
Overleaf.

[[00_MOC/project-map]] · [[01_Governance/research-charter]] · [[01_Governance/status-and-provenance]]
