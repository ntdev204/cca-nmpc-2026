---
type: source-note
status: included-provisional
evidence_status: full-text
evidence_level: full-text
citekey: liu2026arms
doi: 10.48550/arXiv.2601.16686
zotero_uri:
verified_date: 2026-08-13
---

# Liu et al. (2026) — ARMS cho human--robot cooperative navigation

## Xác minh thư mục

- Bản đã đọc: [arXiv:2601.16686](https://arxiv.org/abs/2601.16686).
- Toàn văn preprint được đọc ngày 01/08/2026.
- Venue/phiên bản xuất bản và correction/retraction chưa được Zotero xác minh;
  chỉ dùng như preprint cho scope screening.
- Landing page was rechecked during the 2026-08-13 Google-oriented spot-check;
  this refresh does not upgrade the record to a peer-reviewed venue.

## Bài toán và cơ chế

ARMS dùng LSTM temporal encoder cho trạng thái chuyển động tương đối của người,
LiDAR spatial encoder, PPO follower và một QP safety filter được mô tả như MPC
một bước. Một neural switcher trộn mềm hai đầu ra theo risk-related context như
TTC và clearance. Bài có feature-dropout/hard-gating ablation, benchmark mô
phỏng, Gazebo và thử indoor sơ bộ mang tính định tính.

## Phản bằng chứng đối với dự án

ARMS không phân bổ một total chance budget, nên không phải comparator allocator
trực tiếp. Tuy nhiên, nó đủ để bác novelty kiểu tích hợp: LSTM + context-aware
adaptation + MPC/QP trong human--robot navigation đã có.

Hệ quả:

- LSTM vẫn là predictor interface, không phải đóng góp kiến trúc;
- context chattering/smoothing và hard-vs-soft transition là failure mechanism
  cần ghi trong PR20/PR40;
- bằng chứng dự án phải mạnh hơn ở calibration/OOD, matched fixed-budget
  contrast, target timing và physical trial định lượng;
- không dùng một demo indoor hoặc ảnh đẹp để thay aggregate evidence.

## Vị trí kiểm chứng

- Sec. 3.3: PPO follower, QP filter và soft gating;
- Sec. 4.3: training protocol;
- Sec. 5.2--5.4: benchmark, ablation, Gazebo và deployment discussion.

## Liên kết

- [[03_Literature/source-index]]
- [[03_Literature/nearest-work-matrix]]
- [[04_Research_Gap/research-gap]]
- [[06_Methods/simulation-protocol]]

Related hub: [[00_MOC/project-map]]

