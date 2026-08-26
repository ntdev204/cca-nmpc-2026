# PR21 — Matched benchmark và ablation CCA–NMPC

> **Trạng thái goal hiện tại:** `DEFERRED — OUTSIDE CURRENT GOAL`.  
> **Trạng thái lưu vết:** `PROPOSED / AWAITING-APPROVAL / CONFIRMATORY-NOT-RUN`.
> **Nguyên tắc:** so sánh trong cùng causal layer; không dùng số công bố trên
> robot, map, predictor hoặc compute platform khác làm baseline định lượng.

## 1. Shared conditions

Trong mỗi layer, mọi method dùng cùng map, fixed global path, robot footprint,
plant, initial state, causal observation stream, physical constraints, sample
time, target device, thread count, warm-up, tuning allowance và denominator.
Physical look-ahead time được giữ chung khi có cùng ý nghĩa; discretization và
decision variable riêng của từng algorithm được freeze trước holdout. Context
chỉ gồm current position, current speed, coarse direction, confidence và age.
Global path không replan. Trong hệ P, chỉ CCA sinh robot local path; các
end-to-end baseline giữ nguyên native local decision và command semantics.

Ba namespace seed tách biệt: năm `training_seed` của LSTM, mười
`scenario_seed` của truth/observation stream và `algorithm_seed` của stochastic
search. Cùng package dùng cùng scenario seed cho mọi method; algorithm seed được
freeze riêng và GA ablations dùng paired search streams. Tối thiểu 300 package
được tạo bởi 3 scenario families × 10 frozen templates/family × 10 scenario
seeds. Timestep, candidate và decoder call không phải đơn vị độc lập.

## 2. Prediction layer

So sánh constant velocity, Kalman constant velocity và self-supervised LSTM.
Mọi phương pháp xuất cùng context interface, dùng participant/recording-disjoint
splits và OOD rule của PR11. Kết luận OOD suy diễn cần ít nhất hai held-out site;
một site chỉ cho phép kết quả exploratory. PR12 định nghĩa metrics và năm training
seeds. Inference có nominal budget 10 ms và hard deadline 15 ms.

## 3. CCA local-path layer

Primary comparison chỉ thay local-path generator. Mọi pipeline dùng cùng fixed
global path, robot state, causal observation stream, obstacles, scenarios,
constraints, compute budget và cùng terminal NMPC backend:

| ID | Pipeline |
|---|---|
| A0 | fixed global path → terminal NMPC |
| A1 | DWA local path → terminal NMPC |
| A2 | GA without context → terminal NMPC |
| A3 | constant-velocity context + GA → terminal NMPC |
| P | LSTM continuous context + GA → terminal NMPC |

DWA trong A1 chỉ sinh local path, không phát command theo native DWA. Continuous
context nghĩa là LSTM cập nhật ở mỗi valid observation, độc lập với event kích
hoạt GA. CCA chứa LSTM và GA, chỉ xuất geometric robot local path. Mọi GA cell
dùng paired algorithm seeds và cùng candidate, decoder, wall-clock budgets.

Primary causal contrasts là P−A3 và P−A2; P−A1 và P−A0 là matched architecture
contrasts. Metrics gồm package-level safe completion, collision, signed
swept-footprint clearance, valid-local-path yield, rejoin error, path length,
integrated curvature, tracking error, p50/p95/p99 latency và deadline miss.

DWA–MPC đã có matched architecture prior art
([10.3390/s25072014](https://doi.org/10.3390/s25072014)); planner–MPC cascade
không phải novelty.

## 4. Motion-control layer

Mọi controller nhận chính xác cùng tracking reference được motion-control layer
time-parameterize từ cùng local path:

| ID | Method | Vai trò |
|---|---|---|
| C0 | linearized MPC | constrained linear baseline |
| C1 | nominal NMPC | nonlinear baseline không terminal ingredients |
| C2 | terminal NMPC | proposed motion-control formulation |

So thêm unchecked-path và feasibility-checked-path như secondary interface
sensitivity. Một deterministic equilibrium-progression adapter inspired by
PathFG không phải drop-in reproduction hoặc primary matched baseline.
Terminal-NMPC proof
chỉ áp dụng với fixed admitted reference, nominal model, feasible initial state
và các step thuộc miền giả thiết của theorem. Switching, fallback và rejected
updates được đánh giá riêng, không suy rộng Lyapunov claim.

Các anchors gần gồm scenario-based NMPC với human prediction
([10.1016/j.conengprac.2023.105769](https://doi.org/10.1016/j.conengprac.2023.105769))
và set-terminal NMPC có recursive-feasibility/stability results
([10.1016/j.conengprac.2024.106155](https://doi.org/10.1016/j.conengprac.2024.106155)).
Vì vậy HRI-NMPC, terminal constraint và stability không phải novelty riêng.

## 5. End-to-end layer

Secondary system-level comparators:

| ID | System |
|---|---|
| S0 | native DWA |
| S1 | native MPPI |
| P | Continuous Context-Aware (LSTM + GA) local path + terminal NMPC |

DWA/MPPI giữ native sampling, local rollout và command-selection semantics; chúng
không nhận CCA local path. Chúng dùng cùng environment, fixed global path, causal
observations, footprint, command/wheel limits, target compute và tuning allowance
và chỉ được so ở task/safety/runtime outcomes. Do khác decision authority, S0/S1
không được dùng để quy kết hiệu quả cho CCA, LSTM hoặc GA và không được cứu một
primary A0–A3 failure. Một ablation riêng so full Mecanum với `$v_y=0$` trên P để
cô lập giá trị holonomic.

Residual-learning MPC trên Mecanum đã có experimental evidence
([10.1016/j.conengprac.2025.106587](https://doi.org/10.1016/j.conengprac.2025.106587)),
và HRI model-predictive planning với participant-calibrated interaction model
đã được báo cáo
([10.1016/j.ejcon.2026.101572](https://doi.org/10.1016/j.ejcon.2026.101572)).
Do đó learning-plus-Mecanum-MPC và model-predictive HRI không phải gap tự thân.

## 6. Primary outcomes và Holm families

### Family A — CCA mechanism

Family A có đúng bốn primary hypotheses: paired safe-completion difference
P−A0, P−A1, P−A2 và P−A3. P−A3 cô lập learned continuous context so với
constant-velocity context; P−A2 cô lập context so với no-context GA.

### Family B — motion control

Family B có đúng ba hypotheses:

1. fixed-reference feasibility-rate difference C2−C1;
2. tracking RMSE ratio C2/C1;
3. nominal-budget-overrun risk difference C2−C1 tại 60 ms.

### Family C — end-to-end

Family C là secondary system-level family gồm safe-completion difference P−S0
và P−S1. Holm correction ở $\alpha=0.05$ trong từng family. Family C chỉ hỗ trợ
system-level context; không hỗ trợ mechanism attribution. OOD contrasts ở family
riêng và không được dùng để cứu primary failure.

## 7. Timing budgets và metrics chung

- LSTM nominal/hard: 10/15 ms;
- asynchronous CCA regeneration nominal/hard: 100/150 ms;
- NMPC solve nominal/hard: 60/90 ms;
- full governed control step tại $T_s=0.1$ s có hard deadline 100 ms;
- báo p50/p95/p99/max, nominal-overrun và hard-deadline miss, không chỉ mean;
- safety/task: collision, safe completion, signed clearance, near miss
  `[0,0.10)` m, progress, completion time và stopped fraction;
- tracking/control: position/yaw RMSE, cross-track error, command variation,
  wheel saturation, constraints và fallback;
- mọi timeout, collision, infeasible và incomplete ở trong denominator.

CCA không được chạy đồng bộ nối tiếp với NMPC trong control step 100 ms. Active
fallback/reference tiếp tục được NMPC điều khiển trong khi CCA chạy ở event rate;
proposal hoàn thành được revalidate ở state hiện tại trước admission. Synchronous
MATLAB harness hiện tại chỉ là development evidence và không thể đóng timing gate
cho đến khi rate separation này được thực thi và log độc lập.

## 8. Cổng chấp nhận chính xác

### CCA mechanism gate

Tất cả điều kiện phải đúng:

1. P−A3 và P−A2 safe completion tăng ít nhất 5 percentage points, với lower
   paired 95% CI > 0;
2. P không kém A0 hoặc A1 quá 2 percentage points về safe completion: lower
   paired 95% CI của P−A0 và P−A1 $\geq-0.02$;
3. P−A3 tăng median minimum signed clearance ít nhất 0.05 m, lower paired 95% CI
   > 0, và không tăng collision risk;
4. p95 CCA $\leq100$ ms, p99 $\leq150$ ms và hard-deadline miss tại 150 ms
   $\leq1\%$;
5. Family-A Holm-adjusted tests pass.

### Motion-control gate

1. không state/input/footprint violation trên admitted fixed-reference runs;
2. numerical Lyapunov residual $\Delta V+\ell\leq10^{-8}$ chỉ tại step có fixed
   admitted reference, nominal model và thỏa toàn bộ theorem assumptions;
3. fixed-reference feasible rate $\geq99\%$;
4. p95 solve $\leq60$ ms, p99 $\leq90$ ms, hard-deadline miss tại 90 ms
   $\leq1\%$, và full-step miss tại 100 ms $\leq1\%$;
5. upper 95% CI tracking-RMSE ratio C2/C1 $\leq1.10$ và Family-B tests pass.

### Secondary system-level gate

P−S0 và P−S1 được báo cáo với paired 95% CI và Holm adjustment trên cùng paired
packages. Pass/fail ở đây chỉ giới hạn system-level superiority wording; không
thay đổi kết luận mechanism từ A0–A3.

Failure của CCA mechanism gate bác bỏ research-gap mechanism claim. Failure
secondary system-level gate chỉ cấm broad system-superiority wording. Failure
timing cấm từ `real-time`; failure motion gate cấm stability/constraint wording
vượt fixed-reference theorem. Không composite score.
