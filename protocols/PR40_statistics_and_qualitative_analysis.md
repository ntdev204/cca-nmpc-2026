# PR40 — Thống kê, định tính và failure analysis

> **Trạng thái goal hiện tại:** `DEFERRED — OUTSIDE CURRENT GOAL`.  
> **Trạng thái lưu vết:** `PROPOSED / AWAITING-APPROVAL / HOLDOUT-NOT-OPENED`.
> **Nguyên tắc:** independent unit và paired estimand được khóa trước; estimate,
> 95% CI và effect size đứng trước p-value.

## 1. Population và đơn vị độc lập

- simulation primary: mọi started independent `scenario_package` trong S2;
- LSTM: recording nested trong participant và site; window/frame là repeated data;
- physical future phase: participant/recording/site cluster, không phải frame;
- ITT-like population gồm collision, timeout, solver failure, fallback và stop;
- per-protocol chỉ là sensitivity; safety population gồm mọi run có chuyển động.

Seed được tách theo chức năng: `scenario_seed` tạo package, `algorithm_seed` tạo
GA/stochastic repeat và `training_seed` tạo LSTM checkpoint. Năm algorithm seed
được cross đầy đủ với mọi package trong từng stochastic-method cell; năm
training seed được cross với mọi recording đánh giá. Hai loại seed này là
repeated factors, không phải independent $n$.
Candidate, decoder call, trigger, timestep, frame và window cũng không phải mẫu
độc lập.

Không bỏ outlier theo outcome. Infrastructure corruption giữ raw artifact,
reason code và worst/best-case sensitivity. Missing time-to-goal được xử lý như
censored/failed theo rule khóa trước, không xóa hàng.

## 2. Cỡ mẫu khóa trước

Pilot độc lập chỉ ước lượng variance/base rate. Ba family × 10 template × 10
scenario seed tạo 300 package ban đầu. Với $m_f$ là đúng số hypothesis trong
Holm family $f$, confirmatory simulation dùng

\[
n_{\rm sim}=30\left\lceil
\frac{\max\!\left(300,
\max_{h\in A\cup B\cup C}n_{\rm power,h},
\max_{h\in A\cup B\cup C}n_{\rm CI,h}\right)}{30}
\right\rceil .
\]

$n_{\rm power,h}$ bảo đảm power tối thiểu 0.80 tại ngưỡng hai phía bảo thủ
$\alpha_h=0.05/m_f$. $n_{\rm CI,h}$ là cỡ mẫu nhỏ nhất đạt 95% CI half-width đã
khóa dưới đây; pilot chỉ cung cấp correlation/variance, không đổi precision:

| Loại endpoint | Maximum CI half-width |
|---|---:|
| paired risk difference | 0.05 absolute probability = 5 percentage points |
| collision hoặc hard-miss risk difference | 0.03 absolute probability |
| log path/travel/tracking/curvature ratio | $\log(1.05)$ |
| signed-clearance difference | 0.02 m |

Nếu $n_{\rm sim}>300$, tăng `scenario_seed` đồng đều trong cả 30 ô
family–template trước khi mở holdout. Không giảm dưới 300 hoặc dừng sớm.

Với Family D, số recording `test_id` được khóa riêng:

\[
n_{\rm rec}=\max\!\left(30,
\max_{h\in D}n_{\rm power,h},
\max_{h\in D}n_{\rm CI,h}\right),
\]

với half-width tối đa 0.03 cho macro-F1 difference, 0.03 m/s cho speed-MAE
difference và 0.02 cho ECE difference. Nếu cần tăng, tăng recording độc lập và
participant/site coverage trước khi mở test; không tăng bằng window.

LSTM dùng đúng năm training seeds và participant/recording-disjoint splits. OOD
suy diễn cần ít nhất hai held-out site; nếu chỉ có một site, toàn bộ OOD result
mang nhãn exploratory. Sample size báo số site, participant, recording và package,
không dùng số seed, window hoặc timestep làm independent $n$.

## 3. Paired estimands và inference

Mọi method chạy cùng package/recording. Simulation bootstrap giữ family là fixed
stratum, resample template rồi resample package trong template; toàn bộ năm
algorithm seed đi cùng package và được aggregate hoặc fit như crossed random
factor. LSTM bootstrap resample site → participant → recording và resample độc
lập năm training seed, sau đó dựng lại Cartesian recording × training-seed cells.
Đây là crossed bootstrap, không phải coi $5n$ cells là độc lập.

Primary analyses:

| Outcome | Analysis | Effect và 95% CI |
|---|---|---|
| collision/safe completion | exact McNemar + paired cluster bootstrap | risk difference, risk ratio |
| clearance/tracking/path/runtime | paired difference or paired permutation | median/mean difference, ratio |
| timeout time-to-goal | RMST/competing-outcome model | RMST difference/time ratio |
| LSTM direction/speed/ECE | crossed hierarchical bootstrap recording × training seed | macro-F1, MAE, ECE difference |
| deadline/fallback/violation | paired rate model | risk/rate difference |

Bootstrap/permutation dùng 10,000 replicates với frozen RNG seed. Báo exact $n$,
all failures, raw distribution, estimate, CI và adjusted p-value. Assumption
failure kích hoạt robust method đã chỉ định, không chọn test theo p-value.

## 4. Multiplicity families

Các primary family có đúng 18 hypotheses, khóa direction/margin trước holdout:

- Family A ($m_A=4$): full-minus-decoder-only valid-local-path yield; full-minus-
  penalty-only safe completion; full/decoder-only path-length ratio; full/
  decoder-only integrated-curvature ratio.
- Family B ($m_B=3$): C2-minus-C1 fixed-reference feasibility; C2/C1 tracking
  RMSE ratio; C2-minus-C1 nominal-budget-overrun risk tại 60 ms.
- Family C ($m_C=8$): P-minus-B1 safe completion, collision risk và signed
  clearance; P/B1 travel-time ratio và tracking-RMSE ratio; safe-completion risk
  difference P-minus-B0, P-minus-B2 và P-minus-B3.
- Family D ($m_D=3$): LSTM-minus-strongest-frozen-baseline macro-F1, speed MAE
  và ECE. Baseline mạnh nhất được chọn trên development, không trên test.

OOD chỉ báo estimate và 95% CI exploratory; nó không có primary hypothesis và
không được dùng để thay đổi kết luận ID.

Holm correction riêng trong từng family tại family-wise $\alpha=0.05$; không
pool hoặc chọn lại endpoint. OOD hoặc subgroup result không được cứu failure ở
A–D.
Non-inferiority margins khóa tại PR21: path length 1.05, curvature 1.10,
tracking/travel 1.10. Không diễn giải `p>0.05` là equivalence.

## 5. Deadline analysis

| Stage | Nominal budget | Hard deadline |
|---|---:|---:|
| LSTM | 10 ms | 15 ms |
| CCA | 100 ms | 150 ms |
| NMPC | 60 ms | 90 ms |

Với runtime $T$, `overrun=1[T>B_nominal]`. `hard_miss=1` khi $T>D_hard$ hoặc
không có output hợp lệ tại hay trước $D_hard$; hard miss luôn là overrun và kích
hoạt fallback/stop. Báo riêng overrun count/rate và hard-miss count/rate; không
đổi tên nominal overrun thành deadline miss.

Mỗi stage báo p50/p95/p99/max, warm/cold status và target device. Exact gates:

- LSTM p95 ≤10 ms, p99 ≤15 ms, hard-miss rate ≤1%;
- CCA p95 ≤100 ms, p99 ≤150 ms, hard-miss rate ≤1%;
- NMPC p95 ≤60 ms, p99 ≤90 ms, hard-miss rate ≤1%.

Timeout ở nguyên denominator; host timing không được gọi là embedded hoặc hard
real-time evidence.

## 6. Confusion matrix

Direction classification bắt buộc có ontology/order
`[left,right,forward,backward,unknown]`, independent ground truth, raw counts,
normalized view, class support, precision, recall, F1 và CI. Bounding-box
detection không dùng confusion matrix; nó dùng TP/FP/FN, PR/AP và miss rate.

## 7. Qualitative analysis

Confirmatory set có đúng 45 clips: 5 controller `[B0,B1,B2,B3,P]` × 3 family
`[F1,F2,F3]` × 3 slot. Trong mỗi controller–family, slot 1 là một package chọn
bằng seeded hash-random, slot 2 có minimum clearance gần median nhất, slot 3 là
worst theo thứ tự khóa `collision > incomplete > hard_miss > lower clearance`.

Mọi tie được phá bằng SHA-256 của
`protocol_hash|controller_id|family_id|slot|package_id`, chọn hash nhỏ nhất. Nếu
một package trùng hai slot, slot sau lấy package kế tiếp theo hash/rank. Selection
manifest và hash được freeze trước khi unblind result; không thay clip lỗi bằng
clip đẹp. Overlay chỉ gồm bbox/keypoints, current position/speed/direction/
confidence/age, validity và provenance warning; không hiển thị `truth/*`, future
person coordinates, human trajectory hoặc robot local reference trên camera.

Hai coder dùng rubric khóa trước, blinded method khi khả thi. Codes gồm smooth
progress, freezing, oscillation, hesitation, switching, late avoidance, recovery
và failure attribution. Báo Cohen/weighted kappa hoặc Krippendorff alpha,
adjudication và anonymized descriptions. Qualitative evidence giải thích cơ chế,
không thay primary statistics.

## 8. Failure taxonomy

| Code | Nhóm |
|---|---|
| F-PER | miss, false positive, jitter, ID switch, occlusion |
| F-TIME | stale/out-of-order, clock/transform error |
| F-LSTM | wrong direction/speed/confidence, invalid or late context |
| F-CCA | no valid local path, repair/rejoin/deadline failure |
| F-NMPC | infeasible, residual, local minimum, deadline failure |
| F-GOV | rejected update, stale fallback, stop |
| F-ACT | slew/wheel saturation, plant mismatch |
| F-SAFE | collision, near miss, timeout, incomplete |
| F-INFRA | process/log/hash corruption |

Event có thể multi-label nhưng phải có adjudicated primary cause. Báo count,
rate, severity, stage, outcome và representative artifact.

## 9. Miền áp dụng Lyapunov

Lyapunov inference chỉ được ghi cho terminal NMPC tại những bước có
`lyapunov_applicable=true`: admitted reference cố định, state nằm trong miền
terminal/feasible và mọi giả thiết model/constraint của theorem đúng. Residual
numerical $\Delta V+\ell$ là verification của implementation trong miền này,
không phải proof cho CCA, LSTM, GA, người động, governor, reference switching hay
toàn bộ switched closed loop. Các bước ngoài miền vẫn ở denominator safety/task;
chúng không được xóa chỉ vì residual không áp dụng.

## 10. Exact acceptance gate

PR40 chỉ đạt `VERIFIED` khi:

1. timestamp của frozen plan trước holdout và hash chain hợp lệ;
2. cỡ mẫu thỏa công thức max-over-hypotheses, thiết kế 3×10×10 hoặc balanced
   extension, và mọi started package nằm trong denominator;
3. ba seed namespace tách biệt; algorithm/training seed được phân tích như
   crossed repeats, với zero candidate/timestep/window pseudoreplication;
4. Holm counts A=4, B=3, C=8 và D=3 tái sinh đúng từ raw data;
5. PR12/PR21 effect, CI, margin và deadline gates được đánh giá đúng nguyên văn;
6. confusion-matrix support và failure/missingness tables đầy đủ;
7. đúng 45 qualitative clips, tie/hash, coding và agreement tái lập được;
8. `truth/*` chỉ có realized current/past state để audit và không vào controller/
   figure; future human truth không lộ qua interface;
9. Lyapunov denominator chỉ gồm đúng miền fixed-reference terminal đã khóa;
10. raw-to-table/figure replay khớp tolerance $10^{-9}$.

Một gate không đạt giữ conclusion ở `diagnostic` hoặc `exploratory`; không đổi
threshold sau khi thấy holdout.
