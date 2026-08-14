# PR00 — Phạm vi, câu hỏi nghiên cứu và hợp đồng claim

> **Trạng thái:** `REVIEWED` — scope/claim logic đã qua focused-audit review;
> chưa phải claim được chứng minh và chưa mở holdout.  
> **Phụ thuộc:** focused literature audit quyết định ranh giới novelty; PR02 quyết định claim lý thuyết;
> PR10--PR40 quyết định claim thực nghiệm.

## 1. Phạm vi khoa học bất biến

Nghiên cứu xét robot Mecanum điều khiển theo trạng thái vị trí trong môi trường
có người. Trạng thái gồm `[x,y,theta,vx,vy,omega]`; lệnh cấp thấp là vận tốc
thân. LSTM nén lịch sử quan sát thành context gồm vị trí, tốc độ, hướng và độ
tin cậy; Continuous Context-Aware (CCA) phân bổ mức thận trọng/rủi ro trong bài toán NMPC. Đóng góp
trọng tâm ứng viên là một allocator CCA đóng dạng/không huấn luyện trong một so
sánh matched, không phải YOLO, tracking, LSTM tiêu chuẩn, global planner hoặc
việc ghép nhiều module có sẵn. Claim rộng về context-aware fixed-budget risk
adaptation đã bị nearest work 2025--2026 bác; focused audit phải ghi rõ liệu delta
hẹp còn đủ cho `GO-ALGORITHM` hay chỉ phù hợp `PIVOT-EMPIRICAL`/`STOP`.

Không được mở rộng sang transformer, reinforcement learning, foundation model,
nhận dạng danh tính, social scoring hay một bộ điều khiển hoàn toàn mới nếu
không có amendment được duyệt. Một baseline hiện đại được thêm chỉ để so sánh
không trở thành một nhánh đóng góp.

## 2. Câu hỏi nghiên cứu

- **RQ-01 — cơ chế:** Khi mô hình robot, predictor, tổng risk budget, đường đi,
  horizon và solver budget được giữ matched, CCA có phân bổ sự thận trọng đúng
  cho tương tác quan trọng hơn so với phân bổ uniform/permuted, heuristic
  risk-adaptive và learned-risk hay không?
- **RQ-02 — hiệu quả closed-loop:** CCA-NMPC + LSTM có cải thiện trade-off giữa
  an toàn, hoàn thành nhiệm vụ và độ ổn định bám đường mà không tạo mức fallback
  hoặc deadline miss không chấp nhận được hay không?
- **RQ-03 — vai trò LSTM:** Context LSTM tự giám sát có cải thiện direction
  macro-F1, speed error, validity/calibration và quyết định local-path trigger
  so với constant-speed-direction/Kalman speed-direction trong các miền ID/OOD
  hay không?
- **RQ-04 — chuyển miền:** Kết luận nào còn giữ từ mô phỏng sang robot thật dưới
  perception, delay, actuator và hành vi người không lý tưởng?

## 3. Giả thuyết tiền đăng ký

Các margin định lượng, estimand và cỡ mẫu được đóng băng trong PR40 trước khi
mở confirmatory holdout.

- **H-01:** CCA matched-budget cải thiện context-weighted physical margin so
  với uniform allocation, đồng thời collision rate không xấu hơn quá margin
  non-inferiority đã định trước.
- **H-02:** CCA đúng ngữ nghĩa tốt hơn permuted-context trên paired seeds; nếu
  không, tín hiệu context chưa chứng minh giá trị nhân quả.
- **H-03:** Context LSTM đã calibration cải thiện direction macro-F1, speed MAE
  và timing/validity của trigger so với baseline context, không giả định ưu thế
  ở mọi miền.
- **H-04:** Full CCA-NMPC không vượt budget về actuator, wheel speed, fallback
  và deadline so với ngưỡng đã khóa.
- **H-05:** Xu hướng chính lặp lại trên robot thật với CI phù hợp; nếu không, bài
  báo báo sim-to-real gap thay vì giữ claim mô phỏng như claim vật lý.
- **H-06:** Ở cùng tổng budget và physical clearance, allocator đóng dạng không
  thua kém quá margin khóa trước về safety so với nearest risk-adaptive methods,
  đồng thời cải thiện ít nhất một thuộc tính auditability, runtime hoặc OOD đã
  định nghĩa trước.

Không hợp nhất các kết quả trên thành một điểm “overall superiority”. An toàn,
bám đường, tiến độ, độ mượt, feasibility và computation là các kết quả riêng.

## 4. Hợp đồng mô hình tối giản

Mô hình chi tiết nằm ở PR02, nhưng bản chất không đổi:

\[
s_k=[x_k,y_k,\theta_k,v_{x,k},v_{y,k},\omega_k]^\top,
\qquad u_k=[v^{\rm cmd}_{x,k},v^{\rm cmd}_{y,k},\omega^{\rm cmd}_k]^\top .
\]

Mô hình cập nhật pose dùng vận tốc thân và nhiễu/bất định được nêu rõ; không
yêu cầu mô-men hoặc dòng điện. LSTM là một thành phần của CCA, cung cấp vector ngữ cảnh
theo thời gian (vị trí, tốc độ, hướng) cùng độ tin cậy và trạng thái hợp lệ.
CCA chỉ dùng score liên tục \(c\in[0,1]\) để điều chỉnh khoảng an toàn, trọng số
hoặc risk allocation đã định nghĩa; không sửa global path. Với người động,
chỉ CCA-NMPC được phép tích phân context velocity thành chuỗi vị trí tương lai
nội bộ cho chance rows. Chuỗi này không được xuất thành artifact hoặc vẽ lên
ảnh; các baseline chỉ dùng snapshot hiện tại.

Mọi “guarantee” phải nói rõ điều kiện. T1--T5 của PR02 chỉ là các mệnh đề hợp
đồng sơ cấp, không phải novelty lý thuyết. Chance constraint cục bộ trước hết chỉ
cho cận dưới predictive measure $\Pr_{\mathrm{model}}$, điều kiện theo thông tin
$\mathcal F_k$ và active set đóng băng của một solve. Chỉ được nói về phân phối
vận hành $\Pr_\star$ khi calibration one-sided độc lập đúng tail, đầy đủ mode,
horizon/context, ID/OOD và sample support đã đạt. Thiếu calibration/provenance,
frame/time/age, geometry parity, zero slack hoặc solver residual thì claim xác
suất fail closed.

Mô hình sáu trạng thái hiện chưa ánh xạ đầy đủ actuator lag, command delay và
miền bị chặn của $w_k$. Vì vậy CLM-T-03 được rút/giữ ngoài
phạm vi analytic; soft constraint và fallback chỉ được báo như kết quả thực
nghiệm, không được trình bày như recursive feasibility hoặc stability.

## 5. Claim ledger ban đầu

| Claim ID | Câu được phép kiểm chứng | Bằng chứng tối thiểu | Câu bị cấm trước khi có bằng chứng |
|---|---|---|---|
| CLM-NOV-01 | Claim rộng “context-aware adaptive fixed-budget risk allocation là mới” đã bị bác | PA-06/PA-10/PA-11 full-text equation/experiment matrix | Không được hồi sinh claim bằng đổi tên/platform |
| CLM-NOV-02 | Delta ứng viên chỉ còn allocator đóng dạng, không huấn luyện, theo human--step trong position-state Mecanum CCA-NMPC, giữ clearance cố định | Focused Zotero/Obsidian audit + nearest-work matrix + đọc chéo novelty | “Lần đầu tiên” hoặc “novel adaptive allocation” khi cổng chưa đạt |
| CLM-EMP-01 | Allocator minh bạch có trade-off thực dụng/nhân quả so với uniform, optimized non-context, heuristic và learned fixed-budget allocation | Paired benchmark, OOD/runtime/failure analysis, CI/effect size | Dùng baseline yếu hoặc platform khác làm bằng chứng novelty |
| CLM-T-01 | T1--T3 kiểm bảo toàn fixed budget, thứ tự context và trường hợp uniform dưới active set cố định | PR02 PO-014 + property/numerical tests | Gọi các đẳng thức sơ cấp là novelty/theorem mới hoặc “an toàn tuyệt đối” |
| CLM-T-02 | T4 kiểm scalar Gaussian surrogate và geometry containment dưới $\Pr_{\mathrm{model}}$ | PR02 PO-001/011/013; PO-003 nếu nói về $\Pr_\star$ | Đánh tráo model-internal surrogate với xác suất vận hành |
| CLM-T-04 | T5 kiểm accounting predictive-mode và cận Boole open-loop one-solve | PR02 PO-002/008/015; PO-003 nếu nói về $\Pr_\star$ | “Joint safety toàn horizon/closed-loop/mission-wide” |
| CLM-T-03 (`WITHDRAWN/HELD`) | Không có claim recursive feasibility/practical stability cho controller hiện tại | Chỉ mở lại bằng amendment đóng PO-005/006/009 trên augmented actuator model | Suy stability/recursive feasibility từ nominal six-state model, simulation hoặc fallback |
| CLM-EMP-02 | Báo empirical solve feasibility, fallback, constraint và tracking trên miền thử đã khóa | PR20/PR21/PR30/PR40, đầy đủ mẫu số và CI | Đổi tên các tỷ lệ đo được thành theorem stability/feasibility |
| CLM-ML-01 | Context LSTM tốt hơn baseline cụ thể trên holdout đã khóa về direction/speed/validity | PR11--PR12, ≥5 training seeds, CI/effect size, OOD | “Hiểu ý định người”, ADE/FDE hoặc “generalizes” vô điều kiện |
| CLM-ML-02 | Detector cung cấp đo lường người trong các domain thật đã kiểm | PR10, detection AP/PR/miss metrics; presence confusion matrix chỉ khi task đó được tiền đăng ký | Gọi một vài ảnh minh họa là robust detection |
| CLM-ML-03 | Ngữ cảnh LSTM (vị trí, tốc độ, hướng) được đồng bộ đúng với frame ảnh/video thật | Calibration/frame-transform audit, timestamp audit và overlay có parent hash | Overlay vẽ tay hoặc thiếu frame/scale |
| CLM-SIM-01 | CCA cải thiện một estimand closed-loop trong simulator/configuration đã nêu | PR20--PR21, paired seeds, CI, ablation | “Tốt nhất” dựa vào một seed hoặc RMSE |
| CLM-SIM-02 | Full method đáp ứng budget software trên host được ghi | P50/P95/P99/max, misses, hardware/software manifest | “Hard real-time” |
| CLM-SIM-03 | Lợi ích an toàn không che degradation không chấp nhận được về tracking, fallback hoặc runtime | Multi-outcome trade-off, failure analysis và non-inferiority margins khóa trước | “Overall superior” từ một metric |
| CLM-HW-01 | Xu hướng và giới hạn trên robot thật | PR30, ethics, ground truth độc lập, repeated trials | Dùng simulation hoặc video minh họa để claim hardware |

Với khuyến nghị hiện tại `PIVOT-EMPIRICAL-PROVISIONAL`, CLM-T chỉ là contract
validation hỗ trợ cho empirical characterization. Không thay từ ngữ để biến
allocator, Gaussian quantile hoặc Boole bound chuẩn thành novelty lý thuyết.

## 6. Đối tượng và biến số

- **Đơn vị ML:** recording/context episode, không phải mỗi sliding window độc
  lập.
- **Đơn vị mô phỏng:** một scene--seed--controller run hoàn chỉnh.
- **Đơn vị vật lý:** participant/scene/order block; frame không phải replicate.
- **Biến can thiệp chính:** risk allocation/context semantics và predictor.
- **Primary outcomes:** collision/safe completion, signed physical margin,
  completion/time-to-goal và deadline/fallback theo PR21/PR40.
- **Secondary outcomes:** tracking error, path length, stopped fraction, command
  variation, wheel/constraint violations, calibration và qualitative behavior.

## 7. Phân tầng bằng chứng và cách viết

| Tầng | Nguồn | Cách diễn đạt tối đa |
|---|---|---|
| E0 | Derivation/unit test | “đúng dưới các giả định đã nêu” |
| E1 | Synthetic/open-loop | “trên dataset/simulator synthetic này” |
| E2 | Internet/public recorded data | “trên các source/recording đã nêu” |
| E3 | Closed-loop simulation | “trong các kịch bản mô phỏng đã khóa” |
| E4 | Robot thật, target hardware | “trong cấu hình robot/site/participant đã thử” |
| E5 | External multi-site replication | Chỉ khi thật sự có replication độc lập |

Không nâng claim từ E1/E3 lên E4. “Real-time” chỉ dùng khi deadline, target
hardware, jitter, worst-case và tỷ lệ miss đã được đo; nếu không dùng “measured
software latency”. “Safety” luôn kèm định nghĩa metric và miền kiểm chứng.

## 8. Quy tắc đóng băng và chấp nhận

### Focused-audit checkpoint — 2026-08-13

The 2026-08-13 publisher refresh and Google Scholar discovery-only spot-check
added no directly matched primary record that changes the bounded gap. Risk-aware
MPPI, Mecanum MPC/hardware disturbance rejection and uncertainty-aware predictive
safety remain explicit nearest-work boundaries. PR00 is now `REVIEWED` for scope
and claim logic; the audit is not claimed to be systematic or exhaustive. The
review record is
`research/obsidian/07_Analysis/focused-audit-review-20260813.md`. A versioned
preregistration freeze is still required before confirmatory holdout execution.

PR00 được `FROZEN` khi:

1. Focused literature audit đã xác định nearest prior art, giới hạn claim và
   hướng `PIVOT-EMPIRICAL`/`STOP` nếu delta không đủ;
2. mỗi claim có estimand, protocol, artifact dự kiến và câu giới hạn;
3. primary/secondary/exploratory outcomes được gắn nhãn;
4. không có novelty claim cho YOLO/LSTM tiêu chuẩn hoặc integration đơn thuần;
5. hội đồng nội bộ ký scope version trước khi mở test;
6. SHA-256 của PR00 và claim ledger được ghi trong preregistration manifest.
