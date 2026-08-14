---
type: source-note
status: included-provisional
evidence_status: full-text
evidence_level: full-text
citekey: bonzanini2024pacmpc
doi: 10.1016/j.automatica.2023.111418
zotero_uri:
verified_date: 2026-08-01
---

# Bonzanini, Mesbah và Di Cairano (2024) — Perception-aware chance-constrained MPC

## Xác minh thư mục

- Nguồn chính: [Automatica](https://doi.org/10.1016/j.automatica.2023.111418).
- Bản đã đọc: [author/MERL PDF](https://shadow.merl.com/publications/docs/TR2023-147.pdf).
- Toàn văn đối chiếu ngày 01/08/2026; Zotero và correction/retraction còn chờ.

## Bài toán và cơ chế

PAC-MPC mô hình hóa trực tiếp việc trạng thái và hành động điều khiển làm thay
đổi chất lượng cảm biến, mean/covariance của estimator môi trường và do đó mức
tightening của chance constraints. Estimator được xem như module cho trước;
controller khai thác sự phụ thuộc action--perception thay vì thiết kế lại estimator.

Với cost và terminal ingredients phù hợp, bài báo thiết lập probabilistic
recursive feasibility và stability; trường hợp tuyến tính có construction cụ
thể. Bằng chứng là phân tích lý thuyết và các nghiên cứu mô phỏng, không phải
human-aware robot experiment trực tiếp.

## Phản bằng chứng đối với dự án

Nguồn này bác cách diễn đạt chung rằng coupling giữa context/perception
uncertainty và chance-constrained MPC là mới. Nó cũng yêu cầu dự án tách hai yếu
tố trong primary contrast:

- covariance/perception state phải được giữ cố định khi so UNIFORM với
  CCA_FIXED_BUDGET;
- lỗi detector/LSTM được đánh giá ở nhánh robustness riêng;
- proof budget không được nâng thành recursive-feasibility/stability claim;
- nếu sau này context thay đổi sensing/covariance, đó là một factorial branch
  khác, không được trộn vào hiệu ứng allocator.

## Vị trí kiểm chứng

- Sec. 1--2: control-dependent sensing và estimator assumptions;
- Sec. 3: chance-constrained formulation;
- Sec. 4--6, Theorem 1--3: feasibility/stability và construction;
- phần simulation: bằng chứng định lượng trong miền mô hình của bài.

## Liên kết

- [[03_Literature/source-index]]
- [[03_Literature/nearest-work-matrix]]
- [[04_Research_Gap/research-gap]]
- [[05_Theory/assumptions]]

Related hub: [[00_MOC/project-map]]

