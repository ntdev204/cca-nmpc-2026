# PR12 — Huấn luyện và đánh giá LSTM context

> **Trạng thái:** `DEVELOPMENT-EXECUTED / UNRELEASED`; self-supervised
> score-loop và fail-closed provenance design đã qua review, và một checkpoint
> simulation-only mới đã được huấn luyện từ đầu; chưa có kết quả admissible.
> **Ranh giới:** LSTM là một thành phần của CCA-NMPC, không phải bộ điều khiển
> độc lập và không dự đoán quỹ đạo tương lai của người.

## 1. Giao diện cố định

LSTM nhận cửa sổ lịch sử causal gồm vị trí tương đối, vận tốc sai phân và cờ
validity. Encoder xuất một vector vận tốc context $\hat v_k\in\mathbb R^2$;
tốc độ là $\hat s_k=\|\hat v_k\|_2$. Bốn score hướng được tính bằng tích vô
hướng với các trục trái/phải/tiến/lùi:

\[
q_{k,j}=\frac{\hat v_k^{\mathsf T}a_j}
{\max(\|\hat v_k\|_2,\delta)},
\qquad
a_j\in\{(-1,0),(1,0),(0,1),(0,-1)\}.
\]

Đầu ra runtime là `position`, `speed`, `direction`, `confidence` và
`context_valid`. Không có decoder vị trí tương lai, future human coordinates,
mode probability hoặc human-path overlay.
Tốc độ context phải nằm trong bound `max_speed_mps=2.0` đã khóa trong study
contract; output vượt bound là OOD, bị fail-closed và không được truyền vào
chance rows.

### 1.1 Recurrence tối giản dùng để mô tả LSTM

Với đầu vào chuẩn hóa $z_t$, encoder dùng recurrence chuẩn

$$
\begin{aligned}
 i_t&=\sigma(W_i z_t+U_i h_{t-1}+b_i), &
 f_t&=\sigma(W_f z_t+U_f h_{t-1}+b_f),\\
 o_t&=\sigma(W_o z_t+U_o h_{t-1}+b_o), &
 \tilde c_t&=\tanh(W_c z_t+U_c h_{t-1}+b_c),\\
 c_t&=f_t\odot c_{t-1}+i_t\odot\tilde c_t, &
 h_t&=o_t\odot\tanh(c_t).
\end{aligned}
$$

Từ biểu diễn cuối cửa sổ, đầu ra active là

$$
\hat v_k=W_vh_T+b_v,\qquad
\hat s_k=\|\hat v_k\|_2,\qquad
q_{k,j}=\frac{\hat v_k^{\mathsf T}a_j}
{\max(\|\hat v_k\|_2,\delta)}.
$$

Phần này chỉ đặc tả giao diện toán học của encoder trong `ctx_lstm.py`; nó
không thêm decoder vị trí hoặc một nhánh điều khiển mới.

Mỗi model có `model_id` ánh xạ tới dataset hash, split manifest, code/config,
seed, environment và checkpoint hash. Chỉ checkpoint được chọn bằng validation
rule đã khóa mới được đưa vào runtime.

## 2. Học tự giám sát theo score loop

Không dùng nhãn hướng thủ công trong optimizer. Target tự giám sát là vận tốc
quan sát ở bước kế tiếp. Loss tối giản là

\[
\mathcal L=\lambda_v\|\hat v_k-v_{k+1}\|_2^2
 +\lambda_s|\|\hat v_k\|_2-\|v_{k+1}\|_2|.
\]

Vòng score chỉ dùng tập validation để chọn checkpoint và ngưỡng validity. Mỗi
iteration ghi score, seed, learning rate, thời gian và failure reason; dừng khi
đạt target score hoặc plateau theo protocol. Không mở test để chỉnh model.

## 3. Baselines và công bằng

Baseline bắt buộc là constant-speed-direction và Kalman speed-direction. Mọi
phương pháp dùng cùng history, frame, train/validation/test split, chuẩn hóa và
ngân sách inference. Scaler chỉ fit trên train; calibration tách riêng. Ít nhất
năm training seeds độc lập cho LSTM; failed seed được giữ trong ledger.

## 4. Đánh giá định lượng

### Context classification

Direction accuracy, macro-F1, per-class precision/recall/support và confusion
matrix trên `test_id` và `test_ood`. Nhãn đánh giá được sinh từ vận tốc quan sát
độc lập, không lấy tên scenario làm nhãn.

### Context regression và validity

Speed MAE/RMSE, position error của frame hiện tại, context-valid rate, stale/dropout
rate và calibration error của confidence. Báo median, IQR, 95% CI và subgroup
theo direction, density, occlusion và site.

### Runtime

Parameter count, model size, memory, warm/cold latency P50/P95/P99/max,
throughput và deadline-miss rate trên phần cứng mục tiêu. Host timing không được
gọi là embedded hoặc hard real-time.

## 5. Ablation và kiểm định lỗi

Mỗi ablation chỉ thay một thành phần: position-only, box-derived, pose-aware,
history length, không calibration, context-off và direction permutation. Giữ
cùng seed/budget và không dùng test prediction để thiết kế lại model.

Failure taxonomy gồm missing detection, false positive, ID switch, stale history,
transform/timestamp error, wrong direction, speed error, invalid context,
under-confidence, OOD drift và deadline miss. Mỗi failure giữ source/model/
calibration hash.

## 6. Visual evidence

Overlay trên ảnh thật chỉ gồm bounding box/keypoints, vị trí, tốc độ, hướng,
confidence, validity và provenance/calibration warning. Không vẽ human trajectory,
future coordinate hoặc robot local path trên ảnh; robot path thuộc map benchmark.
Case selection phải có median, boundary, failure và OOD theo PR40, kèm source
image hash và parent manifest.

## 7. Liên kết tới CCA-NMPC

Open-loop context metric không tự động chứng minh lợi ích điều khiển. PR21 phải
so CCA-NMPC với MPC, NMPC, DWA và MPPI trên cùng map/context/seed, đồng thời giữ
invalid/stale fallback. Chỉ model đã calibration và pass context gate mới được
đưa vào run có claim controller.

## 8. Cổng claim fail-closed

`context_claim_eligible=false` mặc định. Chỉ bật khi dataset split không leakage,
real-frame provenance, confidence calibration, timestamp/frame audit, confusion
matrix support, speed metrics, latency target-hardware và hash chain đều pass.
Thiếu một trường thì giữ kết quả ở mức diagnostic, không thay bằng dữ liệu tương
lai hoặc nhãn thủ công.

Nhánh confirmatory chỉ nhận một thư mục direct CSV/JSON đã seal bằng
`final_pack.py`. `manifest.json` phải có structural integrity đã verify, nguồn
thuộc `hardware`, `hardware_in_loop` hoặc `real_offline`, hash của
`context.csv` trùng với file được đọc, đồng thời giữ `context_only=true` và
`human_trajectory_generated=false`. Chỉ có split manifest mà không có gói nguồn
đã seal thì vẫn là diagnostic; dữ liệu mô phỏng hoặc CSV rời bị từ chối. Checkpoint
được đưa vào confirmatory map run phải lưu đường dẫn tương đối tới manifest,
SHA-256 của chính file đó và source/flag metadata; runner phải mở file, kiểm hash
và kiểm lại `status`, `integrity_status`, `capture_source`, `context_only` và
`human_trajectory_generated`. Một hash sao chép không có file đối chứng không
đủ provenance.

Ngoài provenance của capture, checkpoint dùng cho confirmatory CCA-NMPC phải có
`calibration.status=fit`, `method=temperature_scaling_grid`,
`source_split=calibration`, đủ số mẫu tối thiểu và cờ độc lập với train,
validation và test. Checkpoint `not_fit` chỉ được phép dùng trong pilot để
phơi bày failure mode; nó bị từ chối trước confirmatory map run hoặc actuation
phần cứng.

Từ checkpoint 2026-08-13, gói có capture source khác `unknown` còn phải chứa
`calibration.json` theo schema `cca-capture-calibration-v1`, được bind bằng
SHA-256 trong `manifest.json`. Record phải có intrinsics camera, extrinsics
camera/LiDAR và residual calibration; `ctx_run.py` kiểm tra file, hash và tên
sensor trước khi admit training. Đây là cổng provenance, không phải kết quả
calibration của robot thật.

## 9. Cổng chấp nhận

PR12 đạt `VERIFIED` khi model registry là `person_context_sequence`, có tối thiểu
năm seed/log/checkpoint, ID/OOD metrics, confusion matrix, calibration, latency,
CI/effect size và failure strata; overlay context đã qua provenance/visual QA;
không còn human-path artifact và wording closed-loop được tách khỏi open-loop
context evidence.

## 10. Implementation checkpoint — 2026-08-13 06:06 ICT

The non-unknown capture branch now validates the calibration sidecar before a
confirmatory LSTM run. Focused and full Python QA pass (`169` tests); the
relevant source hashes are `ctx_run.py`
`B58A90E237F2615D53FA4D4D363818329DC4EFF9B372E0DEAA318B6EC12E356F`,
`map_run.py`
`B179F2467E51928F61C9294F3DF26473403EFE8F9F1CEAD4CC9C23F603DA02EC`, and
`analyze_run.py`
`258F17B2D56085745809DDB3C6B6F1B91283E1AB5B8507FDE1047E56A40672AD`.
No real context package or checkpoint was created; PR12 is `REVIEWED` for
design only and its execution/evidence gate remains open.

## 11. Multi-seed score-loop implementation checkpoint — 2026-08-13

`ctx_run.py` now accepts `--seed-count`, trains each requested seed independently,
keeps a completed/failed ledger, and selects the highest validation
self-supervised score with a deterministic lowest-seed tie-break. A
confirmatory split rejects fewer than five seeds; development runs may use one
seed while remaining candidate-only. The selected seed and full ledger are
stored in the checkpoint, `training.json`, `metrics.json` and `manifest.json`.
This changes the execution contract only; no real context package or checkpoint
was created and PR12 remains `REVIEWED`, not `VERIFIED`.

## 12. Confirmatory seed-completion recheck — 2026-08-13

The selector now fails closed if fewer than five confirmatory candidates
complete, while preserving the failure reason for each requested seed. Full
Python QA is `203 passed`; the current `ctx_run.py` SHA-256 is
`2CB7D67406519593F76B5ABAEF5E839AB9DFB73E195553FAE1385A41E9C1F652`. This is
still an implementation checkpoint: no real context capture or checkpoint is
available, and no predicted human trajectory is exported or drawn.

## 13. Clean-reset execution checkpoint — 2026-08-14

The replacement package under `experiments/runs/simulation-learning-20260814/`
contains 9,600 simulation-only observations in 40 episode groups with frozen
train/validation/calibration/test-ID/test-OOD assignments. The LSTM was
initialized and trained from scratch with five independent self-supervised
next-velocity score-loop seeds; temperature calibration used only the declared
calibration split. Direction labels were retained only for post-training
diagnostics and were not used as training targets. The local-path reinforcement
policy was learned separately with tabular Q-learning and score/penalty rewards.

The selected checkpoint and policy are hash-bound to the capture package, but
the capture source is simulation. The package is therefore
`candidate-development-only`; PR12 has not reached `VERIFIED`, and no real-data,
hardware, or paper claim follows from this checkpoint.
