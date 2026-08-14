---
type: source-note
status: included-provisional
evidence_status: full-text
evidence_level: full-text
citekey: dai2019pchekov
doi: 10.1109/ICRA.2019.8793660
zotero_uri:
verified_date: 2026-08-01
---

# Dai et al. (2019) — p-Chekov và phân phối lại risk theo tính khả thi

## Xác minh thư mục

- Nguồn chính: [ICRA 2019](https://doi.org/10.1109/ICRA.2019.8793660).
- Bản đã đọc: PDF `[28]` tải từ arXiv/author version ngày 01/08/2026.
- SHA-256: `F3EDFC33A4461DDBA777D1B804B0B03EDCF946B231CDFB7C25808480D12243B1`.
- Metadata Zotero và correction/retraction chưa khóa.

## Bài toán và cơ chế

p-Chekov dùng phân phối trạng thái LQG và Gauss--Hermite quadrature để ước lượng
xác suất va chạm tại waypoint. Risk được khởi tạo đều. Constraint được chia
thành violated, active và inactive; phần allowance dư của inactive constraints
được chuyển cho violated waypoints trong khi giữ tổng chance budget. Cơ chế này
hỗ trợ tìm nghiệm khả thi ban đầu, khác IRA dùng active constraints để cải thiện
một nghiệm đã khả thi.

Bài đánh giá hai môi trường Baxter 7-DOF, 500 query mỗi môi trường và 100 noisy
executions cho mỗi nghiệm. Báo planning time, path length, collision rate,
continuous/discrete satisfaction và tách success/failure cases.

## Phản bằng chứng đối với dự án

Nguồn này bác phát biểu rằng fixed-total feasibility-driven reallocation trong
robot planning là mới. Nó cũng đặt một baseline trực tiếp hơn heuristic tự tạo.

Hệ quả:

- PR21 phải có comparator p-Chekov-like `FEASIBILITY_REALLOCATION` với cùng
  budget, clearance, dynamics, reference và seed;
- CCA allocator phải được định vị là heuristic theo context, không phải optimal
  hoặc lần đầu phân phối lại risk;
- phải giữ failed/infeasible cases ở mẫu số và báo trade-off planning time;
- nhiều execution/query của p-Chekov là mức kiểm chứng tối thiểu cần vượt bằng
  power/sample-size rationale, không sao chép con số một cách máy móc.

## Vị trí kiểm chứng

- Sec. III: joint collision chance constraint và giả định;
- Sec. IV-B, Algorithm 1: risk reallocation;
- Algorithm 2: pipeline p-Chekov;
- Sec. V--VI, Table I: protocol, kết quả, failure và giới hạn.

## Liên kết

- [[03_Literature/source-index]]
- [[03_Literature/nearest-work-matrix]]
- [[04_Research_Gap/research-gap]]
- [[06_Methods/simulation-protocol]]

Related hub: [[00_MOC/project-map]]

