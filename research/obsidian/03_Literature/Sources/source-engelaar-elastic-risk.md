---
type: source-note
status: included-provisional
evidence_status: full-text
evidence_level: full-text
citekey: engelaar2026elastic
doi: 10.1016/j.sysconle.2026.106474
zotero_uri:
verified_date: 2026-08-01
---

# Engelaar, Lazar và Haesaert (2026) — Elastic chance constraints trong SMPC

## Xác minh thư mục

- Nguồn chính: [Systems & Control Letters](https://doi.org/10.1016/j.sysconle.2026.106474).
- Tiêu đề: *Planning with elastic chance constraints in stochastic model predictive control*.
- Toàn văn: HTML open access của nhà xuất bản đã đọc ngày 01/08/2026.
- Metadata Zotero và trạng thái correction/retraction: chưa khóa; không dùng làm
  citation cuối cho tới khi focused-audit metadata và provenance được khóa.

## Bài toán và cơ chế

Bài báo xét hệ tuyến tính rời rạc với nhiễu cộng i.i.d. thuộc lớp central convex
unimodal. Các mức vi phạm trạng thái và đầu vào là biến quyết định. Chúng bị chặn
bởi mức individual và tổng risk; vì vậy controller có thể thay đổi risk values
giữa các lần MPC thay vì dùng một mức xác suất cứng.

Phương pháp đi từ bài toán stochastic infinite-horizon sang tube-based MPC hữu
hạn. Phần lý thuyết đưa ra sufficient conditions cho closed-loop constraint
satisfaction, recursive feasibility và stochastic stability; bằng chứng minh họa
gồm bộ biến đổi DC--DC và vehicle path planning.

## Phản bằng chứng đối với dự án

Nguồn này chiếm trực tiếp phát biểu rộng rằng adaptive probability levels dưới
total budget là mới. Nó cũng cho thấy mức proof cần thiết để claim closed-loop:
chỉ bảo toàn tổng budget và áp dụng Boole không đủ.

Hệ quả bắt buộc:

- CLM-T-01/02 chỉ nói về tính đúng đại số, thứ tự allowance và cận xác suất cục bộ;
- không claim recursive feasibility, closed-loop stability hoặc theory mới cho
  adaptive chance constraints;
- nếu dùng allocator softmax, định vị nó như heuristic minh bạch, chi phí thấp để
  kiểm định trong human-aware nonlinear CCA-NMPC;
- comparator/định vị phải thừa nhận optimized elastic-risk SMPC là lớp lý thuyết mạnh hơn.

## Vị trí kiểm chứng

- Eq. (8)--(10): elastic chance constraints, individual và total risk bounds;
- Sec. 3: finite-horizon tube-based approximation và risk variables online;
- Sec. 4--5, Appendix A: closed-loop constraint satisfaction, recursive
  feasibility và stability conditions;
- Sec. 6--7: hai ví dụ mô phỏng và phạm vi kết luận.

## Liên kết

- [[03_Literature/source-index]]
- [[03_Literature/nearest-work-matrix]]
- [[04_Research_Gap/research-gap]]
- [[05_Theory/proof-obligations]]

Related hub: [[00_MOC/project-map]]

