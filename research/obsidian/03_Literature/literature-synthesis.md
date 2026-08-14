---
type: literature-synthesis
status: novelty-at-risk
evidence_status: full-text-expanded
---

# Tổng hợp tài liệu

Không viết diễn giải từ trí nhớ. Mỗi ô phải trỏ tới ít nhất một ghi chú
`full-text` có vị trí trang/section.

Focused audit trong
[[03_Literature/prior-art-delta]] đã bác cách diễn đạt novelty rộng.
Hai mươi lăm nguồn gần/phạm vi/cơ chế đã được đọc ở mức full-text trong
[[03_Literature/nearest-work-matrix]]. Kết luận hiện tại là claim rộng đã bị
bác và delta còn lại có nguy cơ gia tăng. Hai nguồn Ren mới đã được nhập kèm PDF
và kiểm qua Zotero. Search plan PR01-SLR được giữ như hồ sơ lịch sử; các con số
database/export của nó không được dùng làm flow count hay claim coverage. Audit
đang hoàn thiện collection/tag, correction/retraction của nguồn được trích dẫn
và đọc chéo gap hẹp.

## Ma trận công trình gần nhất

| Nguồn | Định nghĩa context | Context đổi risk budget? | Tổng budget cố định? | Bất định predictor | Torque Mecanum? | Ablation đối sánh? | Mức bằng chứng | Khoảng trống còn lại |
|---|---|---|---|---|---|---|---|---|
| Stefanini et al. 2024 | hoạt động, tư thế, hình học người | không; đổi desired velocity/ràng buộc | không phải cơ chế được báo | dự báo chuyển động 2D | không | không theo semantics của dự án | mô phỏng lặp + robot | context-to-fixed-budget vẫn chưa xác nhận |
| Akhtyamov et al. 2025 | bất định dự báo | đổi biên/ràng buộc thích nghi | mức xác suất do designer đặt | có dùng bất định; calibration cần đối chiếu sâu hơn | không | nhiều objective/constraint, không cùng allocator | mô phỏng + robot + khảo sát | tách context khỏi uncertainty và giữ clearance cố định |
| Ryu và Mehr 2024 | không có social context allocator | không | mức biên cố định theo người/thời điểm | DRCC theo ambiguity set | không | sensitivity theo mức rủi ro | 300 mô phỏng trên chuỗi ETH | cơ chế context allocation; bảo đảm yếu hơn DRCC |
| de Groot et al. 2025 | không | không | joint risk trực tiếp; nêu prior fixed-total marginal allocation | distribution-agnostic bằng scenario | không | so với phương pháp joint/marginal | mô phỏng/real-time theo bài | allocator context đóng dạng nhưng mang độ bảo thủ Boole |
| Nair et al. 2025 | không theo định nghĩa CCA | tối ưu risk theo mode | tổng/ràng buộc risk trong SMPC | đa mode | xe, không Mecanum | fixed-risk/open-loop ablation | mô phỏng + xe với tác nhân ảo | phân bổ theo nhóm người--bước, cùng allowance cho mọi mode |
| Ye và Ren 2026 | social preference từ winding number | không; context đổi lựa chọn topology | tổng joint budget tách đều theo người--bước | đa mode | Jackal vi sai | baseline + sensitivity | ROS 2/Gazebo + user study | chính hướng adaptive allocation đã được nêu; chỉ còn cách hiện thực hóa/kiểm định |
| Wang et al. IROS 2025 | relative position/velocity qua dynamic zone và feasibility | chỉnh một mức \(\beta_k\) online | có trần \(\beta_u\), không phân phối human--step | sampling distribution bất kỳ | không | fixed risk + zone ablation | 120 cấu hình mô phỏng | phân phối budget với clearance cố định, cần comparator trực tiếp |
| Wang et al. 2026 | state context đi vào RL actor | có; học \(\beta_i\) và margin | \(\sum_i\beta_i\leq\beta_{\max}\) | GMM đa mode, oracle trong sim | không | nhiều family baseline + OOD | 10 seed x 50 episode; mô phỏng | chỉ còn allocator đóng dạng/không học theo human--step; novelty rất hẹp |
| Ono--Williams 2008 | trạng thái active/inactive của constraint | có; IRA theo constraint--time | joint budget cố định | Gaussian | không | uniform/ellipsoid/particle | 237 bài toán ngẫu nhiên | human--step là specialization; công thức đóng dạng chỉ là heuristic |
| Paulson et al. 2020 | activity/performance của constraint | có; optimal iterative allocation | joint budget cố định | arbitrary distribution, hai moment | không | fixed uniform + certainty equivalent | ứng dụng process control | phải so/định vị với optimized allocation |
| Barbosa--Löfberg 2026 | proximity/performance trong OCP | có; online decision variables | \(\sum_\ell\gamma_\ell\leq\xi\) | Gaussian | không | nhiều conic formulations | path planning + Monte Carlo/timing | online risk allocation trong SMPC đã bị chiếm |
| Parimi--Williams 2026 | utility/feasibility của agent | có; greedy/market redistribution | shared global \(\Delta\) | learned visual risk | không | static/initialization ablations | 2D + photorealistic + HIL | training-free shared-budget allocation đã có ngoài MPC |
| Engelaar et al. 2026 | trạng thái/lịch sử closed loop | có; elastic risk values tối ưu online | cận individual và total | probabilistic reachable tubes | không | rigid/non-adaptive cases | theory + hai mô phỏng | adaptive risk levels và closed-loop theory đã có |
| Bonzanini et al. 2024 | chất lượng perception phụ thuộc control | covariance/ràng buộc đổi theo action | không phải allocator | estimator mean/covariance | không | perception-aware vs fixed perception | theory + mô phỏng | tách context khỏi covariance; không claim feasibility/stability |
| Liu et al. 2026 | LSTM, TTC, clearance và clutter | soft switching control authority | không | LSTM temporal encoder | không | feature dropout + hard gating | mô phỏng, Gazebo, indoor sơ bộ | LSTM + context + MPC integration đã có |
| Samavi et al. 2025 (SICNav) | ORCA-based human response and interactive crowd state | bilevel MPC safety constraints; no context fixed-budget allocator in the audited full text | not reported as a shared human--step budget | explicit response model with KKT reformulation | not established | 500-scenario ORCA/social-force simulations plus real-robot interaction | Zotero full text | interactive crowd MPC and physical safety validation are boundary prior art |
| Cooperative GP-MPC 2026 | learned residual/multi-agent state | uncertainty-aware chance constraints; no CCA allocator in the screened full text | not established as the proposed fixed budget | Gaussian-process residual uncertainty | not established | ADMM multi-agent coordination and simulation comparisons | publisher full text; screening candidate | learned uncertainty plus MPC is not standalone novelty |
| Dynamic risk-aware MPPI 2025 | moving-obstacle crowd context | sample-level collision-risk handling in MPPI | not the proposed event-level fixed budget | non-Gaussian/sample-based risk handling | not established | sampling/scenario controller comparisons | full-text preprint; screening candidate | MPPI is a required risk-aware benchmark boundary |
| Dai et al. 2019 | activity/violation của constraint | có; chuyển risk inactive sang violated waypoint | tổng Δ cố định | LQG + quadrature collision risk | không | deterministic Chekov; success/failure strata | 500 query x 100 execution mỗi môi trường mô phỏng | comparator feasibility reallocation trực tiếp |
| Huang--Jafari 2023 | đặc trưng xe/đường từ camera | conflict-risk field đi vào MPC, không allocator | không | Bayesian LSTM/MC dropout | không | cruise và human trace | 1.800 trajectory thật; control sim hai xe | LSTM + risk-aware MPC đã có nhưng evaluation yếu hơn protocol dự kiến |
| Zhang et al. 2021 | không social context | threshold riêng theo obstacle | không phải total allocator | vBGMM mean/covariance | quadcopter, không Mecanum | prediction vs no prediction | simulation + theorem/fallback | probabilistic prediction + chance NMPC đã có |
| Ren et al. 2023 | không social context | không; robustify chance/CVaR dưới GMM | confidence joint khác total context budget | GMM moment ước lượng hữu hạn | không | chance/CVaR và moment-robust variants | theory + dữ liệu lái xe thật | context allocator còn hẹp; probability claim phải mạnh hơn về calibration |
| Ren et al. 2025 | không social context | không; risk đồng đều/fixed trong proof | allowance giữ nhất quán qua mode/time | GMM với propagation assumptions | không | nominal/robust/contingency | theory + 10 lần/scenario mô phỏng | recursive feasibility đã có với terminal/propagation contract; dự án không có contract tương đương |

## Tổng hợp theo chủ đề

### Điều khiển theo ngữ cảnh

- Phần đã có: activity/body-pose context đã đi vào MPC và đã có mô phỏng lẫn robot.
- Giới hạn liên quan: context đó chủ yếu đổi vận tốc/hình học, không chứng minh cơ chế fixed-budget của dự án.
- Hệ quả: bắt buộc `CONTEXT_OFF` và `PERMUTED_CONTEXT` trong cùng thiết lập.

### Phân bổ rủi ro

- Phần đã có: fixed-total marginal allocation, mode-wise allocation, risk level
  thích nghi theo feasibility và learned context-aware allocation dưới tổng
  budget đều đã xuất hiện; elastic chance levels với closed-loop conditions
  cũng đã xuất hiện trong SMPC.
- Chuẩn theory gần nhất còn gồm GMM chance-MPC với risk đồng đều giữ nhất quán,
  terminal/invariance và prediction-propagation assumptions cho recursive
  feasibility; đây không phải kết quả có thể suy từ softmax allocator.
- Giới hạn liên quan: cận Boole của dự án bảo thủ hơn joint scenario risk.
- Hệ quả: chỉ claim tính đúng của budget/order và cận trên có điều kiện, không
  claim định lý chance constraint mới, khái niệm adaptive allocation mới,
  recursive feasibility hoặc closed-loop stability.
  P-Chekov còn cung cấp một comparator fixed-total feasibility reallocation trực
  tiếp; vì vậy không thể chỉ so CCA với uniform.

### Dự báo học máy và hiệu chuẩn

- Phần đã có: dự báo đa mode và Bayesian LSTM đã được tích hợp với
  MPC/NMPC/chance constraints trên cả trajectory thật và simulation.
- Stratton et al. (HRI 2026) further show that ADE alone is not a sufficient
  proxy for navigation or human-experience outcomes in constrained interaction;
  this reinforces the separation between LSTM metrics and closed-loop control
  outcomes ([[03_Literature/Sources/source-stratton-hmp-navigation-2026]]).
- Giới hạn liên quan: Gaussian LSTM interface yếu hơn DRCC/conformal dưới distribution shift.
- Hệ quả: ADE/FDE không đủ; phải có NLL, coverage, calibration curve và OOD test.

### Động lực học Mecanum và runtime

- Phần đã có: hình học, tiếp xúc lăn, vận tốc bánh/xe và mô-men dẫn động của
  Mecanum đã được mô hình hóa trong nguồn động lực học gần đây
  ([[03_Literature/Sources/source-dyakov-mecanum-dynamics]]).
- Giới hạn liên quan: nguồn này không cung cấp CCA, human-aware NMPC, LSTM hay
  bằng chứng điều khiển trên đúng platform; khác biệt Mecanum không tự tạo
  novelty thuật toán.
- Hệ quả: phải nhận dạng/đối chiếu plant và giao diện body-velocity của robot
  thực, báo giới hạn vận tốc/pose, độ trễ và runtime trên target hardware,
  không chuyển timing từ nguồn khác.
- The 2026 Mecanum traction benchmark independently reinforces this requirement:
  wheel limits, traction variation, terminal error, saturation and control
  activity must be reported as separate outcomes
  ([[03_Literature/Sources/source-alfayizi-mecanum-2026]]).

### 2026 search-refresh boundaries

- Chen et al. place a self-attention LSTM inside a TD3 navigation policy and
  report dynamic-environment validation. This makes LSTM-plus-learning a
  comparator/interface boundary, not a standalone CCA contribution
  ([[03_Literature/Sources/source-chen-lstm-td3-2026]]).
- Gravina et al. combine LiDAR/RGB-D semantics, human-state estimation, MPC
  and discrete-time barrier constraints with TIAGo validation. Multisensor
  perception plus MPC and physical testing are therefore established system
  components; the proposed comparison must isolate the CCA allocation and
  position-state Mecanum plant ([[03_Literature/Sources/source-gravina-crowd-mpc-2026]]).
- Luna et al. formulate a convex qLPV unknown-input observer for coupled
  actuator faults, wheel slip and model uncertainty in a Mecanum platform. This
  raises the required actuator/model-mismatch audit but is not a CCA or NMPC
  contribution ([[03_Literature/Sources/source-luna-mecanum-unknown-input-2026]]).
- Ye and Ren's SCU-T-MPC provides another risk-aware social-planning boundary;
  its chance-constrained topological planning reinforces that generic
  uncertainty-aware/social MPC is not the gap. It is already listed as NW-06;
  the new note records the 2026 publisher refresh
  ([[03_Literature/Sources/source-ye-scu-t-mpc-2026]]).
- Pham and Han report a Mecanum SMO--MPC--PID--fuzzy architecture with slip
  compensation and separate tracking/control-activity outcomes. This further
  supports treating the platform and hybrid controller as baseline context,
  not as the CCA novelty ([[03_Literature/Sources/source-pham-mecanum-hybrid-2026]]).
- Samavi et al.'s 2025 SICNav full text adds interactive crowd MPC with an ORCA
  response model, KKT reformulation and real-robot validation to the boundary
  set. This raises the required interaction/failure comparator bar but does not
  establish the proposed fixed-budget CCA mechanism
  ([[03_Literature/Sources/source-samavi-sicnav-2026]]).
- The cooperative GP--MPC record adds learned residual uncertainty and
  multi-agent chance-constrained control, while the dynamic risk-aware MPPI
  preprint supplies a direct sampling-controller benchmark boundary. Both are
  screening candidates and require fair implementation/compute checks before
  numerical comparison ([[03_Literature/Sources/source-cooperative-gp-mpc-2026]],
  [[03_Literature/Sources/source-dra-mppi-2025]]).
- The 2026 collaborative-optimization record adds another boundary prior for
  interactive motion planning coordinated with emergency protection under
  stochastic MPC. It reinforces that interaction and fallback architecture
  cannot be claimed as standalone novelty; its publisher page was only
  abstract-level in this session and it remains screening-only
  ([[03_Literature/Sources/source-collaborative-emergency-protection-2026]]).
- The dataset refresh identifies Oxford-IHM and JRDB/JRDB-Pose as potentially
  useful real-context sources, but the Oxford-IHM landing page describes its raw
  release as rosbag and JRDB requires access/licence review. SiT, NavWareSet
  and uB-VisioGeoloc remain screening candidates with different runtime or
  viewpoint limitations. None can enter the no-ROS experiment until a direct
  CSV/JSON export and provenance audit are available
  ([[03_Literature/Sources/source-dataset-candidates-2026]]).

The 2026-08-13 control/uncertainty/Mecanum refresh adds four screening
boundaries: CVaR risk-aware MPPI, Mecanum MPC tracking under disturbances,
Mecanum hardware disturbance rejection, and uncertainty-aware predictive CBF
with probabilistic human forecasting ([[03_Literature/web-verified-gap-sources]]).
They raise the comparator and calibration requirements but do not change the
bounded empirical gap or justify a stand-alone novelty claim for MPPI, Mecanum
MPC, uncertainty handling, or LSTM forecasting.

## Quy tắc tổng hợp

Một câu research gap chỉ được chấp nhận khi ma trận cho thấy: prior art đã sở
hữu từng thành phần; công trình gần nhất đã được nhận diện; khác biệt có ý nghĩa
và được kiểm thử; câu chữ không tuyên bố "đầu tiên" khi chưa có rà soát đầy đủ.

## Kết luận tạm thời và cổng quyết định

Ứng viên hiện tại không còn là “context-aware fixed-budget risk allocation”.
Cả allocation theo constraint--time, online optimization, learned context,
training-free shared-budget redistribution và elastic adaptive risk levels có
closed-loop theory đều đã có. Vì vậy khuyến nghị sơ bộ
là `PIVOT-EMPIRICAL`: kiểm tra liệu allocator đóng dạng, giữ clearance cố định
 trong position-state Mecanum NMPC có tạo giá trị nhân quả, OOD, runtime và khả năng
audit đủ lớn so với uniform, optimized/heuristic và learned risk adaptation hay
không. Không được cứu novelty bằng tên robot, softmax hoặc integration LSTM.
Đây là kết luận của focused audit, không phải kết quả của một systematic review.

Related hub: [[00_MOC/project-map]]

