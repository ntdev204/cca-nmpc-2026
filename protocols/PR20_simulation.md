# PR20 — Thiết kế mô phỏng xác nhận và stress test

> **Trạng thái:** `DEVELOPMENT-EXECUTED / UNRELEASED`; design S0--S4 đã qua
> review và campaign mới đã chạy trong miền mô phỏng; chưa phải confirmatory
> evidence. Mọi kết quả mô phỏng cũ không thuộc protocol này.
> **Mục tiêu:** falsify cơ chế trước, sau đó mới ước lượng hiệu quả.
> **Phiên bản hợp đồng máy:** `1.1.0` (`schemas/simulation-config.schema.json`).

## 1. Tầng mô phỏng

| Tầng | Mục đích | Được dùng cho claim |
|---|---|---|
| S0 unit/property | phương trình, frame, risk budget, constraint sign | correctness cục bộ |
| S1 deterministic regression | tái lập lỗi và kiểm thay đổi mã | không dùng population claim |
| S2 stochastic confirmatory | kiểm H-01--H-04 trên seed đã khóa | claim mô phỏng trong miền |
| S3 OOD/stress | noise, delay, behavior và density ngoài miền tune | robustness có giới hạn |
| S4 offline context replay | event-level Monte Carlo và joint-event estimate | empirical risk trong simulator |

Không dùng S0/S1 như bằng chứng Q1 chính. S2/S3 chỉ được chạy khi registry và
config cùng lưu SHA-256 của focused-literature-audit record, người duyệt, thời
điểm duyệt và SHA-256 của protocol-freeze record. Trạng thái focused audit có
thể là `IN_PROGRESS` trong giai đoạn code/development; chỉ được đóng claim
novelty khi record chuyển `COMPLETE`.
Thiếu một trường thì schema phải từ chối `running/completed`; `STOP` cấm mở
confirmatory campaign. Config, nearest comparator, seed, primary outcomes và
PR40 phải freeze trước lệnh chạy đầu tiên.

## 2. Scenario families

Giữ một regression crossing đơn giản, nhưng confirmatory campaign phải có:

- dynamic context events at crossing, head-on and side-passing locations; the
  footprint is evaluated at the latest observed person position;
- direction changes between left/right and forward/backward;
- multiple context footprints with relevant and distractor tracks;
- narrow turn/passage with context dropout;
- stop--go context and invalid/stale observations.

Factor được thiết kế theo ma trận: context count/density, speed, direction,
position, confidence/dropout, measurement noise, sensor latency, actuator
lag/friction/payload và path curvature. Miền ID/OOD và mức factor được khóa từ
focused audit, calibration vật lý và pilot; không chọn chỉ các scene thuận lợi.

## 3. Matched randomization

Mỗi `scenario--seed` tạo một ground-truth package bất biến: map, robot initial
state, global path, dynamic context-event sequence, observed context
footprints, sensor/estimation noise và disturbance. Tất cả controller nhận cùng package;
common random numbers cho paired analysis. Seed list sinh và hash trước
confirmatory run.

Không cấp ground-truth human future cho controller. CCA-NMPC có thể dùng chuỗi
vị trí dự báo nội bộ được suy ra từ context velocity/direction để tính chance
rows; baseline chỉ nhận snapshot hiện tại theo hợp đồng của mình. Chuỗi dự báo
này không được xuất ra hoặc vẽ lên ảnh camera. Execution order controller được
randomize/interleave để giảm drift do machine load. Failed run không được chạy
lại trừ lỗi hạ tầng được định nghĩa trước; cả bản lỗi và rerun có `RUN`/`DEV`
record.

For DWA and MPPI, the human-safety score uses the footprint at the latest
observed position for every candidate stage. Speed and direction remain context
features for scoring and trigger logic; these baselines do not extrapolate a
human position sequence.

Primary comparison gồm năm chiến lược: MPC, NMPC, DWA, MPPI và CCA-NMPC mục
tiêu. CCA-NMPC là phương pháp duy nhất dùng context score để phân bổ budget;
các baseline giữ footprint, clearance và policy tương ứng cố định. Cả năm giữ
cùng dynamics, constraints, reference, solver/tolerance, tuning budget, sample
time/horizon, scenario--seed package và **một giá trị physical clearance có số
và đơn vị mét**. Mỗi comparator có `equation_id`, semantic version và SHA-256
của equation record; manifest cũng khóa phiên bản invariant. Một nhánh factorial
riêng mới được thay đổi clearance. Cross-family reproduction phải có fairness
ledger và không được dùng làm causal contrast nếu model/path/perception không thể
ghép.

## 4. Fidelity và numerical verification

- Mô hình robot/actuator, collision geometry và unit phải khớp PR02.
- Tách truth plant khỏi controller model; báo mismatch.
- Kiểm timestep/horizon convergence trên development, không chọn bằng test.
- Collision dùng footprint swept/interpolated đủ mịn, không chỉ center point.
- Timestamp/frame/latency được mô phỏng và log; không cấp dữ liệu tương lai.
- Solver status, residual, iterations, warm start, fallback và deadline được lưu
  từng bước.

S4 replay các chuỗi context event và footprint quan sát được theo từng
scenario--seed. Chỉ CCA-NMPC được phép tích phân vận tốc context thành chuỗi vị
trí tương lai nội bộ cho chance rows; chuỗi này không được ghi ra raw CSV,
manifest, figure hoặc ảnh. Các baseline chỉ dùng footprint tại vị trí quan sát
mới nhất. Báo empirical probability với binomial/bootstrap 95%
CI và so với union-bound ledger; không gọi hai đại lượng là giống nhau.

## 5. Outcomes

Primary/secondary được khóa trong PR21/PR40. Raw log tối thiểu gồm robot truth và
estimate, reference, context position/speed/direction/confidence/validity, observed
footprint, context/risk, position/velocity state, constraints/slack, collision/margin,
solver/fallback và stage latency.

Run completion, collision, timeout, infeasible, deadline miss và safe stop có
định nghĩa máy kiểm. Collision dù tới goal vẫn là collision; collision-free stop
không phải completion. Mọi run ở mẫu số.

Mỗi run `completed` hoặc `failed` phải có `scientific_outcome` theo
`schemas/run-manifest.schema.json`: trạng thái thuộc mẫu số, primary outcome,
termination/failure code, collision/clearance, fallback, constraint/slack và
deadline/timing. Tầng không áp dụng vẫn phải ghi `applicable=false` cùng lý do;
không được bỏ trường. Run confirmatory đã khởi động luôn ở mẫu số, kể cả process
exit khác không, collision hoặc lỗi solver.

## 6. Pilot, confirmatory và cỡ mẫu

Pilot chỉ chọn numerical settings và ước lượng variance; seed pilot không đi
vào confirmatory. PR40 khóa cỡ mẫu theo power/precision, với sàn 30 paired seeds
cho mỗi primary simulation stratum trừ khi có biện minh mạnh hơn. Không dừng sớm
khi p-value đẹp. Sensitivity/OOD có nhãn exploratory nếu thiếu power.

## 7. Reproducibility và claims

Mỗi campaign có immutable config, container/environment, code commit, seed
manifest, raw traces, summaries và hashes. Figure/table sinh từ raw traces bằng
script; không nhập tay. Mô phỏng không chứng minh detector trên ảnh thật, hành vi
người thật, safety vật lý hay hard real-time. Câu kết quả luôn nêu simulator,
scenario, sample size và uncertainty.

## 8. Cổng chấp nhận

PR20 đạt `VERIFIED` khi S0 falsification pass, seed/scenario/config đã freeze,
paired package hashes khớp giữa controllers, expected run count bằng observed
kể cả failures, raw-to-summary tái sinh được, S2/S3 tách rõ và không có claim
sim-to-real vượt bằng chứng. Config phải validate bằng
`schemas/simulation-config.schema.json`; mọi run phải validate bằng
`schemas/run-manifest.schema.json` và khớp experiment registry snapshot.

## 9. Development execution checkpoint — 2026-08-14

The clean-reset replacement campaign is recorded in
`experiments/runs/simulation-learning-20260814/` and
`experiments/runs/simulation-benchmark-400mm-20260814/`. It generated the
simulation-only current-context stream, trained the LSTM with a
self-supervised next-velocity score loop, learned the local-path policy with
score/penalty Q-learning, and evaluated the five locked controller labels on
paired map scenarios. The global path remained fixed and local regeneration
was trigger-only. A bounded six-state MATLAB export is retained separately at
`experiments/runs/matlab-position-learning-20260814/`.

All package hashes and paired keys replay successfully, but the run has no
protocol-freeze record, no real capture source, no physical calibration and no
independent confirmatory review. It is therefore `development-only` and
excluded from the claim register. The next gate is a frozen S2/S3 campaign
with the required provenance and independent analysis; no sim-to-real or
hardware claim follows from this checkpoint.
