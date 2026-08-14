---
type: literature-synthesis
status: in-progress
evidence_status: mixed-full-text-and-metadata; full-text-audit-open
date: 2026-08-11
---

# Delta nghiên cứu: YOLO26s-pose và learning pipeline

## Kết luận nhanh

YOLO26s-pose thay Faster R-CNN ở giao diện perception. Thay đổi này làm giàu
đầu vào CCA bằng keypoint/pose cue nhưng không tạo novelty thuật toán. Pose-aware
trajectory prediction, unsupervised navigation representation và safe RL ghép
chance-MPC đều đã có prior art trực tiếp.

## Ma trận nguồn

| Nguồn | Bằng chứng liên quan | Hệ quả cho dự án |
|---|---|---|
| Le et al., IROS 2024, DOI 10.1109/IROS58592.2024.10802371 | Social navigation kết hợp MPC với deep-learning human motion prediction; hiện mới khóa ở metadata/DOI trong Zotero live export. | Bổ sung một prior-art integration gần; không gọi LSTM--MPC hoặc social prediction là novelty trước khi đọc toàn văn. |
| Jocher et al., 2026, arXiv:2606.03748 | YOLO26 có end-to-end pose head và các scale n/s/m/l/x. | Dùng `yolo26s-pose.pt` như model có sẵn; không claim kiến trúc hoặc benchmark nhà cung cấp là kết quả của dự án. |
| Ultralytics Pose Docs, truy cập 2026-08-11 | Pose output gồm box, 17 keypoint và confidence; có protocol COCO/OKS. | Schema perception và metrics phải ghi riêng box/pose; latency phải đo lại trên phần cứng thật. |
| Salzmann et al., RA-L 2023, DOI 10.1109/LRA.2023.3312035 | Skeletal keypoints/head orientation đã được dùng cho human trajectory prediction trên robot. | Bắt buộc ablation position-only/box-derived/pose-aware; không claim pose-aware LSTM là mới. |
| Dugas et al., ICRA 2021, DOI 10.1109/ICRA48506.2021.9560951 | Unsupervised representations đã hỗ trợ RL navigation trong dynamic human environments. | Self-supervised latent learning là baseline/phương án triển khai, không phải novelty tự thân. |
| Pfrommer et al., L4DC 2022 | Policy-gradient RL đã được ghép với chance-constrained MPC safety guide. | RL phải bị giới hạn bởi hard constraints và so với non-learning CCA; không gọi RL+NMPC là mới. |
| Gers, Schmidhuber, and Cummins, Neural Computation 2000, DOI 10.1162/089976600300015015 | Forget gate là nền tảng LSTM; record thư mục đã xác minh trong Zotero, full-text project note chưa hoàn tất. | Chỉ dùng làm nguồn nền tảng cho phương trình LSTM; không xem kiến trúc LSTM là đóng góp. |
| Sun et al., arXiv:2506.14305, 2025 | LR-MPC học risk score từ nhãn heuristic, lọc candidate waypoint theo epistemic/aleatoric uncertainty và đưa waypoint được chọn cho MPC; có mô phỏng và robot thật. | Không claim rộng “online adaptive risk-aware MPC”. Khác biệt phải giới hạn ở fixed-total violation-allowance allocation trực tiếp giữa các chance-constraint events. |
| Wang et al., IROS 2025, DOI 10.1109/IROS60139.2025.11246134 | CVaR-BF điều chỉnh risk level online và đồng thời thay dynamic safety zone theo relative state. | Comparator phải tách thay risk allowance khỏi thay clearance; online risk adaptation không phải novelty. |
| Engelaar et al., SCL 2026, DOI 10.1016/j.sysconle.2026.106474 | Elastic chance constraints tối ưu probability levels dưới individual/total bounds và có kết quả closed-loop cho linear SMPC. | Softmax conservation/Boole proof chỉ là consistency result, không phải adaptive chance-constraint theory. |
| Wang et al., arXiv:2605.21257, 2026 | RL cùng differentiable CVaR safety layer học nominal action, risk level và safety margin, có OOD evaluation. | RL plan của dự án phải là comparator/extension bị chặn; không được dùng “RL + risk adaptation” làm novelty. |

## Vai trò trong bài báo

YOLO26s-pose chỉ là mắt của robot và phần triển khai chính nằm trong code. Bài
báo chỉ cần nêu model/version, định nghĩa ánh xạ toán học từ ảnh sang hộp người,
keypoint và confidence, rồi chuyển kết quả đã fusion/tracking vào CCA. Pose chỉ
được kiểm tra như một interface ablation để loại trừ nhiễu perception; nó không
được dùng để tái định nghĩa research gap, novelty, theorem hoặc proof.

Research gap tiếp tục tập trung vào CCA có LSTM bên trong, fixed-total allowance
allocation và position-state Mecanum NMPC với lệnh vận tốc thân dưới
comparator/ablation được ghép cặp.

LR-MPC là nearest prior art mới cho phần “risk adaptation”, nhưng khác cơ chế:
nó học điểm rủi ro để chọn waypoint, còn CCA dự kiến phân bổ lại một tổng
violation allowance đã cố định giữa các pedestrian--horizon constraints. Primary
ablation phải giữ sensing, prediction, clearance, dynamics, reference, solver
và failure handling giống nhau. Nếu lợi ích biến mất hoặc bị đánh đổi bởi
tracking, infeasibility hay deadline misses, novelty thực nghiệm bị bác bỏ.

## Nguồn Zotero

- `H3X52YUZ` / `jocher_ultralytics_2026`
- `552VM8FQ` / `le_social_2024`
- `359XM6X7` / `nair_predictive_2023`
- `ZEG5KQKH` / `gers_learning_2000`
- `5XFZZK2I` / `salzmann_robots_2023`
- `C8QJXHSN` / `dugas_navrep_2021`
- `NUXTSG34` / `pfrommer_safe_2022`
- `HSR6VLIH` / `sun_socially_2025`
- `GD55NENG` / `wang_safe_2025`
- `L6934LGI` / `engelaar_planning_2026`
- `2JNRX662` / `wang_reinforcement_2026`

## Related notes

[[00_MOC/project-map]] · [[03_Literature/literature-review]] ·
[[03_Literature/Sources/source-ghani-dyna-lflh-2025]] ·
[[04_Research_Gap/research-gap]]

