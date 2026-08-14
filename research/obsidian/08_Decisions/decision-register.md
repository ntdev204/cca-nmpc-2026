---
type: decision-register
status: active
evidence_status: policy
---

# Sổ quyết định

| ID | Quyết định | Lý do | Trạng thái |
|---|---|---|---|
| D-001 | Xem phân bổ fixed-budget theo context của CCA là đóng góp chính ứng viên, chờ audit công trình gần nhất ở PR01. | Đã bị thay thế sau khi PA-06, PA-10 và PA-11 được đọc toàn văn. | superseded |
| D-002 | LSTM là giao diện dự báo, không phải novelty kiến trúc. | Bộ điều khiển dùng dự báo/bất định; phương pháp dự báo là bằng chứng hỗ trợ. | chấp nhận |
| D-003 | Dùng `yolo26s-pose.pt` thay Faster R-CNN; YOLO vẫn là giao diện đo lường. | Hộp người và 17 keypoint cung cấp pose cue cho LSTM/CCA, nhưng không claim detector mới. | chấp nhận; 2026-08-11 |
| D-004 | Học không giám sát/tự giám sát và RL được mở lại ở mức kế hoạch code; chưa là phương pháp hay đóng góp của bản thảo hiện tại. | Cho phép thiết kế pipeline chấm điểm-lặp nhưng không tạo kết quả hoặc overclaim trước khi protocol/gate được khóa. | superseded-by-D-017 |
| D-005 | Chỉ viết và biên dịch bản thảo trên Overleaf. | Kho cục bộ chỉ giữ một bản sao lưu; Obsidian chỉ chứa ghi chú nghiên cứu. | chấp nhận |
| D-006 | Toàn bộ dữ liệu/mô hình/kết quả cũ là `legacy` hoặc `unknown`. | Claim Q1 mới cần bằng chứng được tạo lại, có phiên bản và tuân thủ protocol. | chấp nhận |
| D-007 | Ảnh kiểm thử detector là ảnh thật tải từ Internet, có giấy phép và provenance. | Tránh bằng chứng vòng tròn hoặc ảnh tự sinh. | chấp nhận |
| D-008 | Tài liệu chính thức gửi giáo sư là PDF LaTeX tiếng Việt; ghi chú Obsidian tiếng Việt cũng có thể chia sẻ; chỉ `main.pdf` cuối của bài báo dùng tiếng Anh. | Tách tài liệu hướng dẫn nghiên cứu, ghi chú chia sẻ và bản thảo bài báo. | chấp nhận |
| D-009 | Quỹ đạo cục bộ của LSTM phải được hiển thị trên ảnh gốc đã hiệu chuẩn. | Quyết định cũ, trái với scope context-only mới. | superseded; image shows context only, robot path belongs to Python map |
| D-010 | Bác claim rộng “context-aware adaptive fixed-budget risk allocation là mới”; chỉ giữ ứng viên hẹp: allocator đóng dạng/không huấn luyện theo human--step trong position-state NMPC, clearance cố định. | PA-10 đã học $\beta_i$ dưới tổng budget cố định; PA-11 đã điều chỉnh risk online; PA-06 đã nêu hướng adaptive threat-based. | amended-by-D-021 |
| D-011 | PR01 phải cho quyết định `GO-ALGORITHM`, `PIVOT-EMPIRICAL` hoặc `STOP` trước khi mở confirmatory data/experiment. | Quyết định lịch sử của comprehensive scope; D-018 thay bằng focused audit cho bài báo hiện tại. | superseded-by-D-018 |
| D-012 | Primary contrast giữ physical clearance và tổng budget cố định; gồm plain, uniform, optimized non-context, heuristic/feasibility-adaptive, learned fixed-budget và CCA fixed-budget khi tái lập công bằng khả thi. | Tách tác động của context allocation khỏi adaptive margin, optimizer chất lượng cao và learned allocation; tránh baseline yếu. | chấp nhận |
| D-013 | Ghi khuyến nghị sơ bộ `PIVOT-EMPIRICAL-PROVISIONAL`; chưa coi softmax/human--step/training-free là novelty thuật toán. | PA-12--PA-23 cho thấy constraint--time IRA, optimal/online/elastic/feasibility-based allocation, finite-sample GMM chance planning, recursive-feasible GMM MPC, perception-aware chance MPC và LSTM/probabilistic-predictor--chance-NMPC integration đều đã có. | tạm thời; chờ focused audit và đọc chéo gap hẹp |
| D-014 | Dùng `research/metadata/pr01_gap_decision.json` và `research_gap_gate` trong freeze manifest làm cổng máy đọc được. | Quyết định lịch sử của comprehensive scope; không còn là cổng active sau D-018. | superseded-by-D-018 |
| D-015 | Dưới hướng `PIVOT-EMPIRICAL-PROVISIONAL`, T1--T5 chỉ là mệnh đề kiểm hợp đồng; CLM-T-03 bị rút/held cho controller hiện tại; mọi operational probability claim phải fail closed. | Model sáu trạng thái chưa khớp actuator lag/delay của body velocity và $w_k$; calibration radial/top-mode trên validation không kiểm đuôi one-sided nhỏ. Chỉ admission xác suất khi predictive-mode partition, independent calibration/tail support, provenance/frame/time/PSD, geometry, zero slack và residual đều có hash xác minh. | chấp nhận cho thiết kế; claim thực nghiệm vẫn blocked |
| D-016 | Giữ WoS Core Collection và Scopus trong search plan nhưng đánh dấu `access-blocked`; không tính là đã tìm. | Quyết định lịch sử; active focused audit không yêu cầu các chỉ mục thuê bao hoặc IEEE export. | superseded-by-D-018 |
| D-017 | Thiết kế learning toàn pipeline theo mô-đun: self-supervised perception/prediction; nếu dùng RL thì chỉ điều chỉnh tham số CCA/NMPC bị chặn; NMPC phát lệnh vận tốc thân và giữ hard constraints. | Tránh policy end-to-end phát lệnh trực tiếp trong bài safety-critical; mọi vòng lặp chỉ tối ưu validation score sau khi qua hard gate. LSTM score loop đã triển khai; RL còn mở. | amended-by-D-021 |
| D-018 | Không thực hiện PR01-SLR cho bài báo hiện tại; thay bằng focused literature audit trong Zotero/Obsidian. | Đây là một bài nghiên cứu gốc, không phải systematic review; tài khoản Scopus/WoS/IEEE Xplore không có và không cần biến việc đó thành claim bao phủ cơ sở dữ liệu. PR01 frozen được giữ làm lịch sử, không chặn code/simulation. Record máy đọc được: `research/metadata/focused_literature_audit.json`; nearest-work: [[03_Literature/nearest-work-matrix]]. | chấp nhận; 2026-08-12 |
| D-019 | Giữ SICNav, cooperative GP--MPC và dynamic risk-aware MPPI làm boundary/comparator candidates; SICNav đã được kiểm tra full text trong Zotero, còn GP--MPC/MPPI vẫn chưa được admitted cho định lượng. | Lượt Google/web 2026-08-13 và full-text audit cho thấy interaction-aware MPC, learned uncertainty và sampling risk control đã có; benchmark CCA phải giữ fairness, compute budget và failure accounting. | chấp nhận cho thiết kế; SICNav audited 2026-08-13 |
| D-020 | Tách mô hình mô-men lịch sử khỏi interface phần cứng hiện tại; không dùng nó làm yêu cầu triển khai khi firmware nhận body velocity. | Tránh trộn mã simulator cũ với triển khai STM cấp vận tốc. | superseded-by-D-021 |
| D-021 | Chuyển active physical scope sang position-state control với state `[x,y,theta,vx,vy,omega]` và body-velocity command; torque/current không phải yêu cầu. Giữ mã mô-men cũ chỉ ở compatibility/development boundary cho đến khi simulator được thay thế có kiểm soát. | Khớp yêu cầu giáo sư, giao diện STM và dữ liệu robot cần thu; giữ nguyên CCA-NMPC + LSTM, không mở thêm controller mới. | chấp nhận; 2026-08-13 |

Tạo mục mới bằng [[09_Templates/decision-note-template]]. Một quyết định có thể
đổi phạm vi nhưng tự nó không xác minh claim thực nghiệm.

Related hub: [[00_MOC/project-map]]

Scope amendment: [[08_Decisions/position-state-control-scope-20260813]]

