---
type: source-note
status: included-provisional
evidence_status: full-text
evidence_level: full-text
citekey: huang2023blstm
doi: 10.48550/arXiv.2301.06201
zotero_uri:
verified_date: 2026-08-01
---

# Huang và Jafari (2023) — Bayesian LSTM kết hợp MPC

## Xác minh thư mục

- Nguồn chính: [arXiv:2301.06201](https://arxiv.org/abs/2301.06201).
- Bản đã đọc: PDF `[29]` tải từ arXiv ngày 01/08/2026.
- SHA-256: `3731C66F9B17FEBA0B97B53FDCEEA1570E8DD83D798E40345E0A562118D8E4A4`.
- Chưa nhận diện bản peer-reviewed; dùng như preprint cho scope screening.

## Bài toán và cơ chế

Bayesian LSTM dùng MC dropout để dự báo phân phối vị trí xe từ ba frame và 23
đặc trưng trajectory/road. Mean--variance tạo conflict-risk field. Một hybrid
automaton có năm action và MPC giải bằng depth-first search chọn chuỗi năm bước
có tổng risk nhỏ nhất.

Dữ liệu gồm 1.800 trajectory thật trích từ 40 phút video camera đường phố. Bài
báo coverage theo trục của khoảng 95%, nhưng không tách calibration, test ID/OOD
hay so CV/Kalman. Control simulation chọn hai xe có nhiều xe xung quanh nhất và
so risk với cruise/human trace.

## Phản bằng chứng đối với dự án

LSTM bất định + risk-aware MPC trên trajectory camera thật đã có; vì vậy tích
hợp LSTM--MPC không phải novelty. Evaluation còn tạo đúng khoảng trống thực
nghiệm mà dự án phải xử lý nghiêm hơn, không phải khoảng trống thuật toán.

Hệ quả:

- split theo source/scene/track, calibration riêng và test ID/OOD;
- baseline CV/Kalman-CV, nhiều seed và CI/effect size;
- không chọn vài trajectory thuận lợi sau khi xem kết quả;
- overlay phải gắn đúng frame, timestamp, track, calibration và local path;
- open-loop coverage không được gọi là closed-loop safety.

## Vị trí kiểm chứng

- Sec. III-B--C: Bayesian LSTM và conflict risk;
- Sec. IV-B: MPC/DFS năm bước;
- Sec. V-A--C: dữ liệu, coverage và control simulation;
- Sec. VI: giới hạn.

## Liên kết

- [[03_Literature/source-index]]
- [[03_Literature/nearest-work-matrix]]
- [[04_Research_Gap/research-gap]]
- [[06_Methods/lstm-protocol]]

Related hub: [[00_MOC/project-map]]

