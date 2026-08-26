# PR11 — Dataset context causal cho LSTM

> **Trạng thái goal hiện tại:** `DEFERRED — OUTSIDE CURRENT GOAL`.  
> **Trạng thái lưu vết:** `PROPOSED / AWAITING-APPROVAL / NOT-EXECUTED`.
> **Phạm vi:** dữ liệu thật dùng để ước lượng context hiện tại cho CCA; không
> chứa target điều khiển, local path của robot hoặc tọa độ người ở tương lai.

## 1. Đơn vị độc lập và dữ liệu đầu vào

Đơn vị lấy mẫu độc lập là một `recording` hoàn chỉnh, được định danh đồng thời
bởi `participant_id`, `recording_id` và `site_id`. Frame và sliding window chỉ
là repeated observations trong recording, không được tính như các mẫu độc lập.
Mọi nguồn phải có consent/license, raw hash, camera calibration và timestamp.

Một record causal chỉ chứa:

- vị trí người hiện tại trong robot-local frame, đơn vị mét;
- tốc độ quan sát hiện tại, đơn vị m/s;
- hướng thô `left/right/forward/backward/unknown`;
- confidence, validity và tuổi quan sát `age_ms`;
- bbox/keypoints, track quality và provenance cần để tái lập context.

Không lưu future coordinates, rollout, predicted path hoặc đường di chuyển của
người. Không dùng tên scenario làm nhãn hướng.

Target current-context là $v^{\mathrm{ref}}_k$ tại chính timestamp $k$, đo bằng
reference độc lập đã calibration và đồng bộ thời gian với camera. Reference
không được suy ra từ detector, track hoặc cửa sổ đặc trưng dùng làm đầu vào mô
hình. Nếu không có reference độc lập hợp lệ, recording chỉ được dùng cho
diagnostic và không vào train, validation, calibration hoặc test confirmatory.

## 2. Frame và thời gian

Vị trí robot-local được tính từ phép biến đổi đã calibration:

\[
p^{r}_{h,k}=R(\psi_{r,k})^{\mathsf T}
\bigl(p^{w}_{h,k}-p^{w}_{r,k}\bigr).
\]

Timestamp phải monotonic và cùng clock domain hoặc có offset đã đo. Record giữ
`capture_time`, `processing_time`, `age_ms`, dropped/duplicated-frame flags và
calibration hash. Context bị đánh dấu invalid khi `age_ms > 150` hoặc transform,
track, confidence hay timestamp không hợp lệ; không nội suy bằng dữ liệu tương
lai để cứu record.

## 3. Schema tối thiểu

- dataset/source/recording/participant/site/scene/track/frame IDs;
- image hash, raw-parent hash, capture timestamp và age;
- camera intrinsics/extrinsics, robot pose và calibration hash;
- current position, speed, coarse direction, confidence và validity;
- causal history indices và independent current-velocity target
  $v^{\mathrm{ref}}_k$;
- reference source, reference timestamp, synchronization residual và hash;
- split label, OOD label, exclusion reason và processing commit.

Output của detector hoặc LSTM không được ghi đè raw record. Mọi biến phát sinh
được lưu ở derived artifact có parent hash.

## 4. Split khóa theo participant–recording–site

Năm split là `train`, `validation`, `calibration`, `test_id`, `test_ood`. Split
được tạo trước khi cắt window. Cỡ mẫu tối thiểu sau mọi exclusion là 60, 20, 20,
30 và 30 recording độc lập tương ứng. `test_ood` giữ trọn site chưa xuất hiện ở
bốn split còn lại. Sau khi khóa site OOD, connected components
participant–recording phải nằm trọn trong đúng một split; cùng participant hoặc
recording không thể qua hai split. `train`/`validation`/`calibration`/`test_id`
được stratify trong các site ID đã thấy nhưng dùng participant và recording
khác nhau.

OOD inferential yêu cầu ít nhất hai site hoàn toàn chưa thấy và ít nhất 30
recording trong `test_ood`. Nếu chỉ có một site chưa thấy, kết quả OOD chỉ là
exploratory, không được dùng để đóng gate inferential hoặc hỗ trợ claim tổng
quát hóa qua site. Không có site độc lập thì dataset không đủ điều kiện OOD.

Scaler, imputation, temperature và ngưỡng validity chỉ được fit trên split đã
chỉ định. Test ID/OOD không được dùng để chọn checkpoint, feature, window length
hoặc threshold. Synthetic data chỉ được dùng cho unit/development và không vào
split confirmatory.

## 5. Strata và kiểm soát chất lượng

Metadata phải bao phủ crossing, head-on, side-passing, stop–go, turning, group,
occlusion, speed, distance, density, lighting, camera motion và sensor quality.
Các kiểm tra bắt buộc gồm:

- schema, unit, range, timestamp, image hash và transform round trip;
- calibration residual, duplicate/near-duplicate, ID switch và impossible speed;
- intersection participant/recording bằng 0 giữa mọi split và site-OOD bằng 0;
- flow count từ raw đến eligible, kèm mọi exclusion;
- license, consent, privacy, retention và prohibited-use audit.

## 6. Overlay và ranh giới bằng chứng

Overlay chỉ hiển thị bbox/keypoints, track ID, vị trí hiện tại, tốc độ, hướng
thô, confidence, validity, age và cảnh báo calibration/provenance. Không vẽ
đường người, future coordinate hay robot local path lên ảnh. Dữ liệu không có
calibration metric chỉ hỗ trợ image-plane diagnostics và không được dùng cho
clearance theo mét.

## 7. Cổng chấp nhận chính xác

PR11 chỉ đạt `VERIFIED` khi đồng thời:

1. 100% record eligible qua schema, hash, unit và monotonic-time checks;
2. giao participant/recording giữa mọi cặp split bằng 0;
3. năm split có tối thiểu 60/20/20/30/30 recording eligible theo thứ tự đã khóa;
4. OOD inferential giữ ít nhất hai site không giao với bốn split còn lại; một
   site chỉ cho phép nhãn `EXPLORATORY-OOD`;
5. 100% record metric có calibration hash hợp lệ, `age_ms` và independent
   current-velocity reference với synchronization residual hợp lệ;
6. mọi raw-to-window count và exclusion tái sinh đúng từ manifest;
7. không có trường future coordinate, rollout hoặc predicted person path;
8. overlay median/boundary/failure/OOD tái sinh đúng từ raw hashes.

Thiếu bất kỳ gate nào giữ PR11 ở `NOT-VERIFIED`; không thay dữ liệu thật bằng
simulation để đóng gate.
