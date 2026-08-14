# PR40 — Phân tích thống kê, định tính và failure taxonomy

> **Trạng thái:** `REVIEWED`; analysis plan đã qua review nhưng phải freeze
> trước khi mở holdout.  
> **Nguyên tắc:** estimate + uncertainty trước, p-value sau; run/participant là
> đơn vị, không phải frame.
> **Phiên bản hợp đồng máy:** `1.1.0`
> (`schemas/evaluation-config.schema.json`).

## 1. Analysis populations và missingness

- `ITT-like`: mọi run/trial đã khởi động theo assignment, gồm collision, timeout,
  solver failure, safe stop và incomplete; là phân tích chính.
- `Per-protocol`: chỉ run không có deviation định trước; là sensitivity.
- `Safety population`: mọi run có robot chuyển động.

Không loại outlier theo kết quả. Corrupt log do hạ tầng có reason code, raw artifact
và sensitivity worst-case/best-case. Failed run không có time-to-goal được xử lý
như censored/failure theo model đã khóa, không bỏ khỏi bảng.

Run manifest `completed/failed` phải giữ cùng một cấu trúc outcome: inclusion vào
mẫu số, primary-outcome status, termination/failure, collision, fallback,
constraint/slack và deadline/timing. `not applicable` là một giá trị có lý do,
không phải field bị thiếu. Run confirmatory đã bắt đầu bắt buộc
`included_in_registered_denominator=true`.

## 2. Cỡ mẫu và repeated paired design

Pilot độc lập ước lượng variance/base rate; không dùng để test hypothesis chính.
Cỡ mẫu chọn theo power hoặc CI-width cho primary estimand, effect tối thiểu có ý
nghĩa từ focused audit/use case, alpha 0.05 và power tối thiểu 0.8. Simulation có sàn 30
paired seeds mỗi primary stratum; LSTM có ít nhất 5 training seeds; physical
trial tính theo participant/scene cluster. Nếu không đạt, ghi exploratory.

Mọi controller/predictor so trên cùng seed/sample/scene. Model thống kê chứa
scenario/site/participant/training-seed effects khi cần; không coi hàng nghìn
timestep/window của một run là independent.

## 3. Estimand và tests

| Outcome | Phân tích chính | Effect/CI |
|---|---|---|
| Collision/safe completion paired | McNemar hoặc mixed logistic model | risk difference/ratio, 95% CI |
| Margin/tracking/control/runtime | paired difference, cluster bootstrap hoặc permutation | median/mean difference + standardized/robust effect |
| Time-to-goal có timeout | survival/competing outcome hoặc predeclared penalty sensitivity | time ratio/RMST difference + CI |
| Context LSTM direction/speed/validity | paired sample, hierarchical bootstrap qua recording và seed | macro-F1, speed MAE, validity/calibration difference + 95% CI |
| Deadline/fallback/violations | paired count/rate model phù hợp | rate/risk difference + CI |

Kiểm distribution/model assumptions bằng residual/diagnostic. Nếu assumption
sai, dùng robust/permutation/bootstrap đã định, không chọn test theo p-value.
Report exact n, failures, estimate, CI và raw distribution.

## 4. Multiplicity và margins

H-01--H-04 và primary outcomes tạo family được khóa; điều chỉnh Holm (hoặc một
phương pháp khác đã biện minh) trong family. Secondary/exploratory p-values ghi
rõ và không dùng để cứu primary null. Non-inferiority/equivalence margins được
đặt từ ý nghĩa an toàn/literature trước holdout; không dùng observed variance để
nới margin sau kết quả.

Không diễn giải `p>0.05` là hai phương pháp tương đương. Không dùng nhiều biểu đồ,
seed hoặc subgroup rồi chỉ báo subgroup có lợi. Subgroup phải tiền đăng ký hoặc
gắn exploratory.

## 5. Confusion matrix

Chỉ tạo confusion matrix khi `classification.enabled=true` và có contract máy đọc
được: `task_id`, loại task, ontology, class order cố định, ground truth, decision
rule/matching rule đã hash, genuine negative examples và support. Báo raw counts,
normalized view, support, precision/recall/specificity/F1 và CI. Artifact chỉ được
`accepted` khi `classification_semantics` trong artifact registry khớp contract.

Với đánh giá LSTM đã bật, direction là một task phân loại của mô hình học; vì vậy
ma trận nhầm lẫn direction là bắt buộc, không phải lựa chọn trình bày. Schema
`evaluation-config` buộc `direction_classification.enabled=true`,
`confusion_matrix_required=true` và contract ontology/decision/ground-truth đã
hash trước khi mở confirmatory run. Bounding-box detection vẫn không dùng ma trận
nhầm lẫn; nó dùng TP/FP/FN, PR/AP và miss metrics.

`bbox_detection_confusion_matrix_required` luôn bằng `false`. Detection dùng
TP/FP/FN, PR/AP/miss metrics; direction context là classification task riêng và
có thể dùng confusion matrix khi ground truth độc lập, class order và support
đã khóa. Không dùng confusion matrix để thay metric của detection.

## 6. Phân tích định tính tiền đăng ký

Chọn video bằng sampling rule trước kết quả: first eligible + random stratified
theo controller/scenario/outcome, median case, worst safety margin, collision,
fallback/deadline, prediction undercoverage và mỗi OOD stratum. Không chọn chỉ
video đẹp.

Context overlay chỉ được nhận khi artifact liên kết selection protocol và source
manifest đã hash; frame phải là media thật, bbox/keypoint, position/speed/direction,
validity và calibration warning phải hiển thị đúng source image. Không được vẽ
human trajectory hoặc robot local path trên ảnh. Một hình không có task semantics
chỉ là diagnostic, không phải qualitative evidence được chấp nhận.

Hai coder dùng rubric khóa trước, blinded method khi có thể. Code gồm smooth
progress, freezing, avoid--brake--return oscillation, hesitation, active-track/
mode switching, passing-side reversal, late avoidance, recovery và human
deviation. Báo agreement (Cohen kappa/weighted kappa hoặc Krippendorff alpha),
disagreement/adjudication và quote/description đã anonymize. Định tính giải thích
cơ chế, không thay statistical outcome.

## 7. Failure taxonomy bắt buộc

| Nhóm | Ví dụ |
|---|---|
| F-PER | miss/false positive, bbox jitter, ID switch, occlusion |
| F-TIME/FRAME | stale/out-of-order, clock offset, transform sai |
| F-LSTM | wrong direction, speed error, invalid context, stale output |
| F-CCA | ranking sai, active-set churn, risk/context chattering |
| F-NMPC | infeasible, numerical failure, local minimum, residual cao |
| F-FB | fallback muộn/chattering/không recovery |
| F-ACT | command/slew/wheel saturation, model mismatch |
| F-SAFE/TASK | collision, near miss, timeout, incomplete/freezing |
| F-RT | deadline miss, jitter, resource contention |
| F-HUMAN | participant deviation hoặc unexpected interaction |

Một event có thể multi-label nhưng có primary root-cause theo adjudication. Báo
count/rate, severity, stage, outcome và representative artifact; không đổ mọi
lỗi end-to-end cho LSTM hoặc controller mà không có trace.

## 8. Reproducibility và cổng chấp nhận

Analysis script đọc immutable raw manifest và sinh machine-readable tables,
figures và claim rows. Khóa package versions, random/bootstrap seeds và decimal
rounding. Một verifier chạy lại từ raw tới table và so hash/numeric tolerance.

PR40 đạt `VERIFIED` khi analysis plan/time stamp trước test được chứng minh,
sample-size rationale rõ, pairing/clustering/multiplicity đúng, mọi failure và
missingness được xử lý, qualitative selection/coding tái lập, và conclusions
không vượt CI/effect size hoặc tầng bằng chứng. Evaluation config phải validate
bằng `schemas/evaluation-config.schema.json`; confusion/overlay artifact phải
validate semantic gate trong `schemas/artifact-registry.schema.json`.
