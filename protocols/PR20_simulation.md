# PR20 — Mô phỏng xác nhận và stress test

> **Trạng thái goal hiện tại:** `DEFERRED — OUTSIDE CURRENT GOAL`.  
> **Trạng thái lưu vết:** `PROPOSED / AWAITING-APPROVAL / CONFIRMATORY-NOT-RUN`.
> **Mục tiêu:** kiểm chứng đúng mô hình trước, sau đó ước lượng hiệu quả của
> CCA–LSTM–GA + NMPC trên các package độc lập và ghép cặp.

## 1. Tầng bằng chứng

| Tầng | Mục đích | Quyền claim |
|---|---|---|
| S0 unit/property | equation, frame, constraint, footprint, parity | correctness cục bộ |
| S1 deterministic | tái lập lỗi và kiểm fallback | development only |
| S2 confirmatory | paired benchmark đã freeze | claim trong simulator |
| S3 OOD/stress | delay, noise, density, mismatch ngoài miền tune | robustness có giới hạn |

S0/S1 không thay S2. Pilot và confirmatory tách seed/package; mọi tune kết thúc
trước khi mở manifest S2. Mô phỏng không chứng minh perception người thật, an
toàn vật lý, hardware real time hoặc sim-to-real.

## 2. Mô hình và context quan sát

Robot dùng mô hình Mecanum sáu trạng thái $(x,y,\theta,v_x,v_y,\omega)$, footprint
$0.4\times0.4$ m và cùng actuator/wheel constraints cho mọi controller. Global
path bất biến. Chỉ hệ đề xuất P dùng CCA để sinh robot local path; các baseline
end-to-end giữ native local-decision/command semantics.

Người trong truth simulator có thể di chuyển để tạo tương tác động, nhưng input
controller tại bước $k$ chỉ gồm vị trí hiện tại, tốc độ hiện tại, hướng thô,
confidence và `age_ms`. Không controller nào nhận future person coordinates,
future rollout hoặc privileged truth. Observation invalid khi age vượt 150 ms.
Collision và clearance được tính từ swept footprint truth, không từ center point.

Namespace `truth/*` tách khỏi controller bus. Nó chỉ được ghi **sau** bước điều
khiển và chỉ chứa trạng thái người đã xảy ra tại hoặc trước timestamp hiện tại để
audit collision/clearance. Controller, tuning, overlay và figure không được đọc
`truth/*`; future truth không được xuất sang log phân tích hoặc figure. Quyền truy
cập này được kiểm bằng interface test và provenance hash.

GA là optimizer học/chấm điểm duy nhất trong CCA. Không có RL/DRL hoặc optimizer
học thứ hai. GA chỉ sinh robot local path; không sinh hay vẽ quỹ đạo người.

Lyapunov chỉ thuộc NMPC motion control khi local path đã được time-parameterize
thành reference cố định, state nằm trong miền khả thi/terminal và các giả thiết mô
hình–constraint của PR02 đúng. Kết quả đó không áp dụng cho CCA, LSTM, GA, human
motion, reference switching, governor hay toàn bộ switched closed loop.

Các công trình scenario-NMPC với probabilistic human prediction
([DOI 10.1016/j.conengprac.2023.105769](https://doi.org/10.1016/j.conengprac.2023.105769))
và model-predictive HRI planning
([DOI 10.1016/j.ejcon.2026.101572](https://doi.org/10.1016/j.ejcon.2026.101572))
là anchors mạnh hơn về explicit human-motion modeling. Thiết kế này kiểm một
câu hỏi hẹp hơn: current-context robot-reference generation dưới cùng budget.

## 3. Scenario families

S2 khóa đúng ba family, mỗi family có 10 template và mỗi template có 10
`scenario_seed`, tạo $3\times10\times10=300$ `scenario_package`:

1. F1 — crossing: left/right/forward/backward crossing và đổi tốc độ;
2. F2 — longitudinal interaction: head-on, overtaking và stop–go;
3. F3 — holonomic constrained: side-passing, narrow passage, multiple people,
   distractor track, dropout/stale context và infeasible proposal.

Mỗi template khóa map, start/goal, fixed global path, density, nominal speed,
coarse direction, confidence, observation age, noise, latency, actuator lag,
friction/payload, path curvature và obstacle clearance. Chỉ randomized event
stream/disturbance thay đổi theo `scenario_seed`; không chọn scene theo kết quả.

ID/OOD levels được chọn từ literature, physical calibration và pilot; không
chọn scene theo kết quả. OOD tách riêng khỏi primary ID family.

## 4. Đơn vị độc lập, pairing và cỡ mẫu

Đơn vị randomization độc lập là một immutable `scenario_package`: map,
start/goal, fixed global path, simulator-private truth event stream, causal
observation stream và plant disturbance. Timestep, candidate, decoder call và
algorithm repeat không phải mẫu độc lập. Mọi method chạy đúng cùng package;
common random numbers tạo paired contrasts và bootstrap giữ template cluster.

Ba namespace seed không được dùng thay nhau:

- `training_seed = [11, 23, 37, 53, 71]` chỉ huấn luyện LSTM;
- `scenario_seed = [1001,1002,1003,1004,1005,1006,1007,1008,1009,1010]`
  sinh 10 package cho từng template;
- `algorithm_seed = [101,211,307,401,503]` điều khiển GA/stochastic method.

Mỗi GA cell chạy cả năm `algorithm_seed` trên từng package; các seed này được
cross đầy đủ và cân bằng giữa methods. Kết quả được ghép/aggregate trong package
hoặc mô hình như repeated factor, không làm $n$ tăng từ 300 lên 1500.

Với tập primary Holm hypotheses $\mathcal H_{\rm sim}$ của PR40, cỡ mẫu là

\[
n_{\rm sim}=30\left\lceil
\frac{\max\!\left(300,\max_{h\in\mathcal H_{\rm sim}}n_{\rm power,h},
\max_{h\in\mathcal H_{\rm sim}}n_{\rm CI,h}\right)}{30}
\right\rceil .
\]

$n_{\rm power,h}$ dùng power 0.80 và ngưỡng Holm bảo thủ
$0.05/m_f$ của family chứa $h$; $n_{\rm CI,h}$ dùng các CI half-width số học đã
khóa ở PR40. Nếu kết quả lớn hơn 300, thêm cùng số `scenario_seed` đã đăng ký vào
cả 30 ô family–template trước khi mở holdout. Không giảm $n$ hoặc dừng sớm.

## 5. Ngân sách tính toán khóa trước

| Stage | Nominal budget | Hard deadline |
|---|---:|---:|
| LSTM context | 10 ms | 15 ms |
| CCA context-to-local-path | 100 ms | 150 ms |
| NMPC motion control | 60 ms | 90 ms |

`overrun=1` khi runtime vượt nominal budget. `hard_miss=1` khi không có output
hợp lệ tại hoặc trước hard deadline, hoặc runtime vượt hard deadline; hard miss
là một tập con của overrun. Hard deadline kích hoạt fallback/stop đã đăng ký.
Không gọi nominal overrun là deadline miss.

- CCA factorial: tối đa 448 proposed candidates, 448 decoder calls, nominal
  100 ms và hard deadline 150 ms;
- repair, rejection và failed decode đều tiêu cùng decode/wall-clock budget;
- cùng device, thread count, warm-up, compiler, horizon và measurement method.

Execution order được randomize/interleave. Timeout, empty feasible set, solver
failure và fallback ở nguyên mẫu số. Không rerun trừ infrastructure failure đã
định nghĩa trước; bản lỗi và rerun đều giữ manifest.

## 6. Logging và fidelity

Raw log tối thiểu gồm estimated robot state, CCA local path, NMPC reference, năm context
fields, age/validity, obstacles, footprint clearance, command, constraints,
solver/fallback, candidate/decode counts và stage latencies. Audit store
`truth/*` được mã hóa quyền riêng chỉ chứa robot truth và human state đã xảy ra
tại hoặc trước timestamp ghi log; nó không vào controller, tuning, overlay hoặc
figure. Tách truth plant khỏi controller model; khóa timestep/horizon convergence
trên development. MATLAB, Simulink và Python parity phải dùng cùng equation IDs.

Mỗi started run có `included_in_registered_denominator=true`, termination code,
collision, completion, deadline, fallback và missingness status. Figures/tables
được tái sinh từ raw trace, không nhập tay.

## 7. Cổng chấp nhận chính xác

PR20 chỉ đạt `VERIFIED` khi đồng thời:

1. S0 equation/frame/footprint/parity tests pass với residual $\leq10^{-8}$;
2. có đúng thiết kế $3\times10\times10$ hoặc balanced extension theo công thức,
   và đủ ba namespace seed đã khóa;
3. 100% package hash và invariant hash giống nhau giữa mọi method;
4. CCA cells có cùng giới hạn 448 candidate, 448 decode, nominal 100 ms và hard
   deadline 150 ms; năm algorithm seed được cross/balance nhưng không tăng $n$;
5. expected run count bằng observed count, kể cả mọi failure/timeout;
6. 100% started runs nằm trong registered denominator;
7. không controller input/figure nào chứa `truth/*`, future person coordinates
   hoặc rollout; audit store chỉ có current/past realized human state;
8. swept-footprint collision audit pass trên 100% package;
9. raw-to-summary replay khớp tolerance $10^{-9}$ và PR40 tái sinh được;
10. S2 và S3 tách manifest, estimand và multiplicity family;
11. Lyapunov residual chỉ được gắn `applicable=true` trong đúng fixed-reference
    terminal domain; không dùng nó làm bằng chứng ổn định cho switched pipeline.

Performance acceptance thuộc PR21; thiếu một integrity gate giữ campaign ở
`DEVELOPMENT-ONLY` bất kể kết quả đẹp.
