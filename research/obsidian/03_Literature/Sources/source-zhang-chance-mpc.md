---
type: source-note
status: included-provisional
evidence_status: full-text
evidence_level: full-text
citekey: zhang2021chance
doi: 10.1109/TCYB.2020.3032711
zotero_uri:
verified_date: 2026-08-01
---

# Zhang et al. (2021) — Probabilistic prediction trong chance-constrained NMPC

## Xác minh thư mục

- Nguồn chính: [IEEE TCYB](https://doi.org/10.1109/TCYB.2020.3032711).
- Bản đã đọc: PDF `[30]` từ [arXiv:2006.07907](https://arxiv.org/abs/2006.07907),
  đối chiếu tiêu đề/tác giả/DOI ngày 01/08/2026.
- SHA-256: `2B156ADB717E37FD9B2E24395919741AA65AF940E142CCD5029D3D944D49190C`.
- Metadata Zotero và correction/retraction chưa khóa.

## Bài toán và cơ chế

vBGMM học phân phối có điều kiện của trajectory tương lai, sau đó mean/covariance
được dùng để tạo ellipsoid và half-space chance constraint. Các constraint này
đi vào nonlinear MPC bằng multiple shooting. Bài còn đưa stability condition,
slack và backup controller; các claim đó dựa trên giả định feasibility, terminal
set/cost và Lyapunov argument riêng, không xuất phát từ risk-budget identity.

Bằng chứng là simulation quadcopter; predictor dùng 1.000 trajectory 3D sinh,
không phải dữ liệu người thật. Mỗi obstacle dùng một threshold riêng, không có
fixed-total context allocator.

## Phản bằng chứng đối với dự án

Probabilistic multi-modal prediction + chance-constrained nonlinear MPC,
deterministic reformulation và fallback đã có. Vì vậy dự án không được claim
integration/theory rộng.

Hệ quả:

- chỉ giữ proof đơn giản về budget/order và local conditional probability bound;
- recursive feasibility/stability phải có terminal/shifted-candidate proof độc
  lập hoặc bị hạ thành outcome thực nghiệm;
- chance slack làm mất probability claim nếu khác không;
- LSTM là predictor interface và phải được kiểm calibration bằng dữ liệu thật.

## Vị trí kiểm chứng

- Sec. II, Lemma 1: predictor đa mode;
- Sec. III-B--C, Theorem 1: chance reformulation;
- Sec. III-D--E, Theorem 2 và Algorithm 1: stability condition, slack, backup;
- Sec. IV: simulation quadcopter và dataset sinh.

## Liên kết

- [[03_Literature/source-index]]
- [[03_Literature/nearest-work-matrix]]
- [[04_Research_Gap/research-gap]]
- [[05_Theory/proof-obligations]]

Related hub: [[00_MOC/project-map]]

