# PR21 — Benchmark và ablation controller

> **Trạng thái:** `DEVELOPMENT-EXECUTED / UNRELEASED`; fairness/estimand design
> đã qua review và một campaign development mới đã chạy; chưa phải benchmark
> confirmatory. Campaign confirmatory chỉ chạy sau focused audit, PR20 và
> protocol freeze được duyệt.
> **Nguyên tắc:** cùng map, plant, global path và context; chỉ thay controller.
> **Phiên bản hợp đồng máy:** `1.1.0`.

## 1. So sánh chính

| ID | Controller | Mục đích |
|---|---|---|
| B0 | MPC | baseline tuyến tính/đơn giản |
| B1 | position-state NMPC | baseline phi tuyến không phân bổ context |
| B2 | DWA | baseline local-velocity phổ biến |
| B3 | MPPI | baseline sampling-based |
| P | CCA-NMPC | phương pháp mục tiêu, dùng context score |

Mọi controller nhận cùng robot Mecanum, map, state đầu, global path cố định,
context position/speed/direction, footprint, clearance, horizon, thời gian mẫu,
solver budget và scenario--seed. Global path không được replan. Chỉ local path
của robot được tạo lại khi footprint context xung đột hoặc hướng thay đổi.
Người là đối tượng động: chỉ CCA-NMPC được phép dùng chuỗi vị trí tương lai
nội bộ do LSTM/context velocity cung cấp trong chance rows. Baseline không được
nhận chuỗi tương lai; chúng dùng snapshot hiện tại và direction/speed cho policy
local của mình. Chuỗi CCA không được xuất ra ảnh hoặc raw context CSV.
Manifest mỗi campaign phải ghi implementation class, control domain, context
usage và risk strategy của từng controller; thiếu mapping thì campaign không
được promote. Nếu campaign dùng LSTM, manifest phải ghi checkpoint hash cùng
hash/source của sealed `context.csv` capture; checkpoint diagnostic hoặc không
có provenance không được vào confirmatory comparison.

## 2. Hợp đồng CCA và clearance

Với $M$ context event đang hoạt động, tổng budget $\bar\epsilon$ và floor
$\epsilon_{\min}$, baseline uniform (nếu được bật trong ablation) dùng

\[
\epsilon_e=\epsilon_{\min}+
\frac{\bar\epsilon-M\epsilon_{\min}}{M}.
\]

CCA dùng score $c_e\in[0,1]$ từ context branch:

\[
w_e=\frac{\exp(-\beta c_e)}{\sum_{j=1}^{M}\exp(-\beta c_j)},
\qquad
\epsilon_e=\epsilon_{\min}+
(\bar\epsilon-M\epsilon_{\min})w_e.
\]

LSTM chỉ cung cấp context position/speed/direction và confidence/validity.
Người là đối tượng động; chỉ CCA-NMPC được phép tích phân context velocity
thành chuỗi vị trí tương lai nội bộ cho chance rows. Chuỗi này không được
lưu, xuất hoặc vẽ lên ảnh. Một giá trị physical
clearance $d_0$ (m) được khóa cho toàn bộ primary comparison; thay đổi clearance
chỉ thuộc factorial phụ.

## 3. Fairness ledger

Mỗi method có equation ID, semantic version, hash, tuning budget và failure
ledger. Giữ cố định dynamics, actuator limits, collision geometry, reference,
sample time/horizon, solver/deadline, environment, random seeds và thứ tự paired
scenario. DWA/MPPI được ghi rõ khác biệt thuật toán; không dùng chúng làm causal
contrast nếu không thể ghép cùng state/reference contract.

## 4. Primary estimands

- **E-01:** paired difference P--B1 về minimum signed clearance, collision và
  safe completion.
- **E-02:** P--B0/B2/B3 về completion, progress, path length và stopped fraction.
- **E-03:** P với context permutation/context-off để kiểm tra giá trị semantic
  của context.
- **E-04:** non-inferiority của P về tracking và runtime dưới cùng deadline,
  fallback và actuator limits.
- **E-05:** độ nhạy với context dropout, stale frame, sai hướng và OOD map.

Không tạo composite score thay cho các estimand trên. Nếu safety tăng nhưng
tracking, latency hoặc fallback xấu đi, báo trade-off riêng.

## 5. Metrics bắt buộc

### Safety và task

Collision rate, safe completion, minimum signed clearance, near-miss count,
completion time, timeout, path length, progress và stopped-time fraction. The
development runner defines a near miss as a non-collision margin in
`[0, 0.10) m`; this threshold must be frozen before confirmatory execution.

### Tracking và control

Position/yaw RMSE, cross-track error, command variation, jerk,
wheel-speed saturation, constraint residual và local-path generation count. The
map runner records path length, progress ratio, cross-track RMSE, yaw RMSE,
mean/total command variation and fallback duration per episode; these
are descriptive outputs until the full metric contract is frozen.

### Context và computation

Direction confusion matrix, macro-F1, speed MAE, context-valid rate, stale/dropout
rate, solver status, iterations, P50/P95/P99/max latency, deadline miss và
fallback rate/duration.

## 6. Execution và báo cáo

Giữ paired seeds, randomize/interleave controller order, freeze tune/test scenes
tách biệt và giữ mọi failed/incomplete/collision run trong mẫu số. Báo per-scene
distribution, paired confidence interval/effect size, failure taxonomy và một
figure đại diện cho mỗi controller; không vẽ toàn bộ đường lặp lên hình chính.

## 7. Cổng chấp nhận

PR21 đạt `VERIFIED` khi fairness/tuning ledger đầy đủ, năm strategy trong
`schemas/simulation-config.schema.json` khớp manifest, ablation cô lập từng
claim, metrics/failures được báo đầy đủ và phân tích PR40 tái sinh được. Không
gọi kết quả mô phỏng là bằng chứng perception thật, an toàn vật lý hoặc hard
real-time.

## 8. Development execution checkpoint — 2026-08-14

The fresh development benchmark is bound to the self-supervised LSTM checkpoint
and the tabular score/penalty Q-learning policy under
`experiments/runs/simulation-benchmark-400mm-20260814/`. It contains the five
predeclared strategies (MPC, NMPC, DWA, MPPI and CCA-NMPC), 10 paired
replicates for each of three dynamic-context scenarios, a fixed global path and
trigger-only local-path generation. The separate MATLAB position-state export
uses the same six-state/body-velocity interface.

The raw-to-summary replay and controller pairing pass, but score tuning is
development-only, the source context is simulated, and no protocol-freeze or
independent review is attached. The benchmark therefore remains
`candidate-development-only`; no superiority, safety, real-time or sim-to-real
claim is released.
