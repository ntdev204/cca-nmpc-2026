# PR12 — Huấn luyện và đánh giá LSTM context

> **Trạng thái goal hiện tại:** `DEFERRED — OUTSIDE CURRENT GOAL`.  
> **Trạng thái lưu vết:** `PROPOSED / AWAITING-APPROVAL / NOT-EXECUTED`.
> **Ranh giới:** LSTM nằm trong tầng CCA và chỉ ước lượng context hiện tại; nó
> không sinh reference, không điều khiển robot và không xuất tọa độ người tương lai.

## 1. Giao diện toán học

Đầu vào là cửa sổ causal của vị trí robot-local, vận tốc sai phân, confidence,
validity và age. Với đặc trưng chuẩn hóa $z_t$, LSTM dùng recurrence chuẩn:

\[
\begin{aligned}
i_t&=\sigma(W_i z_t+U_i h_{t-1}+b_i),&
f_t&=\sigma(W_f z_t+U_f h_{t-1}+b_f),\\
o_t&=\sigma(W_o z_t+U_o h_{t-1}+b_o),&
\tilde c_t&=\tanh(W_c z_t+U_c h_{t-1}+b_c),\\
c_t&=f_t\odot c_{t-1}+i_t\odot\tilde c_t,&
h_t&=o_t\odot\tanh(c_t).
\end{aligned}
\]

Đầu ra nội bộ $\hat v_k=W_vh_T+b_v$ ước lượng vận tốc hiện tại. `position` và
`age_ms` là pass-through từ observation hiện tại đã kiểm tra timestamp; LSTM
không dự đoán hai trường này. `speed` bằng $\|\hat v_k\|_2$. Với bốn vector đơn
vị $u_d$ theo thứ tự cố định `left/right/forward/backward` và scale khóa trước
$s_0=1\ \mathrm{m/s}$, logits không thứ nguyên là

\[
\ell_{k,d}=\frac{u_d^{\mathsf T}\hat v_k}{s_0},\qquad
p_{k,d}=\operatorname{softmax}(\ell_k/T)_d.
\]

Temperature $T>0$ và ngưỡng reject $\tau_{\mathrm{unk}}$ chỉ được fit trên
`calibration`: $T$ tối thiểu hóa multiclass negative log-likelihood trên các
sample có hướng xác định, còn $\tau_{\mathrm{unk}}$ tối đa hóa macro-F1 năm lớp
trên grid khóa trước; hòa điểm chọn ngưỡng thấp hơn. `confidence` bằng
$\max_d p_{k,d}$; `coarse_direction` là argmax khi confidence
$\geq\tau_{\mathrm{unk}}$, ngược lại là `unknown`. Output runtime vẫn đúng sáu
trường `position`, `speed`, `coarse_direction`, `confidence`, `age_ms` và
`context_valid`. Context invalid, confidence dưới ngưỡng hoặc `age_ms > 150`
làm CCA chuyển sang fallback đã đăng ký.

## 2. Học tự giám sát và lựa chọn checkpoint

Target là vận tốc current-context $v^{\mathrm{ref}}_k$ tại timestamp $k$ từ
reference độc lập quy định trong PR11; không dùng $v_{k+1}$ hoặc future
coordinate. Nhãn direction đánh giá được suy ra từ $v^{\mathrm{ref}}_k$ theo
cùng bốn trục và dead zone khóa trước. Loss tính sau khi đưa vận tốc về đơn vị
m/s và khóa trước:

\[
\mathcal L=\|\hat v_k-v^{\mathrm{ref}}_k\|_2^2
+0.25\bigl(\|\hat v_k\|_2-\|v^{\mathrm{ref}}_k\|_2\bigr)^2.
\]

Hai số hạng đều có đơn vị $(\mathrm{m/s})^2$ và hệ số 0.25 không thứ nguyên.
Train đúng năm `lstm_training_seed` riêng `[11, 23, 37, 53, 71]`; namespace này
không dùng lại split seed hoặc simulation-scenario seed. Mọi seed, kể cả seed
lỗi, ở trong ledger. Mỗi seed chọn một checkpoint bằng validation loss của chính
seed đó; không chọn seed thắng cuộc, và cả năm checkpoint đi vào phân tích.
Temperature $T$ và $\tau_{\mathrm{unk}}$ chỉ fit trên `calibration`. Không mở
`test_id`/`test_ood` trước khi model, preprocessing, calibrator và checkpoint
hash được freeze.

## 3. Đơn vị thống kê và chống leakage

Split tuân PR11: participant/recording disjoint trong mọi split, còn `test_ood`
giữ site hoàn toàn chưa thấy. Recording là đơn vị độc lập; window là repeated
observation. CI dùng hierarchical bootstrap site → participant → recording, sau
đó tổng hợp qua năm training seed. Không báo window count như sample size.
Cỡ mẫu eligible tối thiểu là 60 train, 20 validation, 20 calibration, 30 test ID
và 30 test OOD recording. OOD inferential cần ít nhất hai site chưa thấy; nếu
chỉ có một site, mọi metric OOD phải mang nhãn exploratory.

## 4. Baseline công bằng

So sánh `constant velocity`, `Kalman constant velocity` và LSTM trên cùng causal
history, split, transform, scaler, age rule và target-hardware thread budget.
Mỗi phương pháp xuất cùng sáu trường context. CV và Kalman dùng cùng phép ánh xạ
bốn logits, temperature scaling và unknown-reject rule đã đăng ký cho LSTM.
Calibrator có cùng dạng và cùng calibration split, nhưng tham số $T$ và
$\tau_{\mathrm{unk}}$ được fit riêng cho từng phương pháp rồi freeze trước test.
Không cấp thêm feature, future coordinate hoặc test-derived threshold cho bất
kỳ phương pháp nào.

## 5. Metrics và artifacts

- direction: macro-F1, per-class precision/recall/support và confusion matrix;
- speed: MAE, RMSE và signed bias;
- confidence/validity: ECE, Brier score, stale/dropout và valid coverage;
- runtime: model size, peak memory, p50/p95/p99/max latency, exceedance ở nominal
  budget 10 ms và miss rate tại hard deadline 15 ms;
- strata: site, direction, speed, distance, density, occlusion và lighting.

Mỗi artifact giữ dataset, split, calibration, model, code và environment hashes.
Overlay ảnh thật chỉ hiển thị bbox/keypoints cùng sáu trường context; không vẽ
đường người, future coordinate hoặc robot local path.

## 6. Analysis family

Primary family LSTM gồm ba contrasts so với baseline mạnh nhất đã khóa:
direction macro-F1, speed MAE và ECE. Dùng paired hierarchical bootstrap theo
recording và Holm tại $\alpha=0.05$. ID và OOD được báo tách biệt; OOD là
robustness evidence, không dùng để cứu gate ID.

## 7. Cổng chấp nhận chính xác

PR12 chỉ đạt `VERIFIED` khi tất cả điều kiện sau đúng:

1. cả năm seed hoàn thành hoặc mọi failure được tính fail trong gate;
2. split audit participant/recording và cỡ mẫu 60/20/20/30/30 đều pass; OOD chỉ
   là inferential khi có ít nhất hai held-out site, còn một site là exploratory;
3. trên `test_id`, macro-F1 có lower 95% CI $\geq0.80$, speed-MAE upper 95% CI
   $\leq0.20$ m/s và ECE upper 95% CI $\leq0.10$;
4. LSTM cải thiện macro-F1 và speed MAE so với baseline mạnh nhất với
   Holm-adjusted $p<0.05$; nếu không, claim chỉ là parity/diagnostic;
5. confusion matrix có class order cố định và support từng lớp;
6. trên target hardware, p95 latency $\leq10$ ms, p99 $\leq15$ ms và miss rate
   tại hard deadline 15 ms $\leq1\%$ sau warm-up khóa trước;
7. không artifact nào xuất future coordinate hoặc predicted person path;
8. raw-to-metric replay tái sinh đúng trong numeric tolerance $10^{-9}$.

Không đạt một gate thì checkpoint không được dùng trong confirmatory CCA-NMPC.
Kết quả simulation-only không đóng gate dữ liệu người thật.
