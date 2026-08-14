---
type: simulation-design
status: design-only
scope: research-knowledge
---

# Thiết kế mô phỏng trên map Python

Đặc tả này mô tả cách kiểm tra giả thuyết, không chứa seed, log, biểu đồ hay
kết quả. Mỗi lần triển khai phải tạo manifest và dữ liệu riêng ngoài Obsidian.

## Phạm vi context

Mỗi bước thời gian nhận context người gồm vị trí, tốc độ và hướng. Người được
biểu diễn trên map bằng footprint tại vị trí quan sát hiện tại và di chuyển
theo các event vận tốc đã định nghĩa. Chỉ CCA-NMPC được phép tích phân context
velocity thành các vị trí tương lai nội bộ cho chance rows; chuỗi này không
được ghi hoặc vẽ. Global path được lập một lần và giữ cố định trong episode.
Local path chỉ được sinh lại khi footprint tạo conflict mới hoặc hướng thay
đổi. Context thiếu, cũ hoặc không hợp lệ không được nội suy và không kích hoạt
local replanning.

## So sánh công bằng

Các bộ điều khiển chính gồm MPC, position-state NMPC, DWA, MPPI và CCA-NMPC. CCA
dùng context score để phân bổ budget; các baseline không dùng score đó. Tất cả
giữ cùng map, reference, footprint, clearance, dynamics, constraints, horizon,
solver và ngân sách tuning. Mọi bộ điều khiển nhận cùng plant, trạng thái đầu,
context, global path và gói scenario--seed; không được replan global path riêng
cho một phương pháp.

Robot footprint checkpoint — 2026-08-14: the `rai_robot_urdf` intake is kept as
a read-only reference for link and sensor roles. The current map contract is
bound to the user-supplied physical specification: 400 mm by 400 mm total
footprint including wheels, an interpreted 50 mm wheel radius, LiDAR height
240 mm, camera height 200 mm, LiDAR front-edge distance 100 mm and camera
front-edge distance 35 mm. With robot-frame `+x` forward, the corresponding
sensor positions are `x_L=100 mm` and `x_C=165 mm`, so the camera is 65 mm
ahead of the LiDAR and pitched 20 degrees downward. The circumscribed footprint
radius used by the current map run is `0.2828427125 m`, and the physical-spec
SHA-256 is recorded in the run manifest. Independent dimensional and sensor
calibration remain pending; this is a geometry/provenance input, not a hardware
result. Earlier URDF-derived or generic-radius runs are not comparable and are
not promoted.

`map_run.py --campaign pilot` chỉ dùng cho plumbing/debug và mặc định có năm
replicate. `--campaign confirmatory` là profile riêng, yêu cầu tối thiểu 30
paired replicate theo contract, bắt buộc `--no-score-tune`, và ghi trạng thái
`completed-confirmatory-unreleased` cho đến khi protocol freeze, phân tích và
review độc lập hoàn tất. Profile này còn bắt buộc `--protocol-freeze` trỏ tới
manifest hợp lệ có PR20/PR21 và focused audit ở trạng thái COMPLETE.
Confirmatory execution must also pass `--lstm-checkpoint`; the runner then uses
the score-trained LSTM inside CCA from a causal five-feature history. A pilot
without a checkpoint is labelled `direct_direction_speed_adapter` and cannot
support a CCA--LSTM claim. The confirmatory checkpoint must carry the SHA-256
and capture source of a sealed real `context.csv` package; a structurally valid
but provenance-free checkpoint is rejected.

The development runner also accepts an explicit `--simulation-only` package
with a sealed episode-group split and simulation calibration sidecar. This
path is intentionally labelled simulation-only and remains outside hardware
evidence, real-data claims and the frozen confirmatory release gate; omitting
the flag still rejects `capture_source=simulation`.

## Yếu tố và chỉ số định trước

Map gồm vùng mở, hành lang, giao lộ, lối rẽ và vật cản. Các yếu tố stress gồm
đổi hướng, nhiều footprint động, dropout context, nhiễu đo, trễ và sai lệch
actuator. Chỉ số cần định nghĩa trước gồm collision, minimum clearance,
completion, progress, local-generation count, fallback, constraint residual,
solver deadline và thời gian tính. Chỉ số perception gồm context-valid rate,
direction confusion matrix và sai số tốc độ; không trộn chúng với chỉ số điều
khiển.

Runner metric contract — 2026-08-12: the map benchmark records per-episode
path length, progress ratio, cross-track RMSE, yaw RMSE, command variation and
command slew, near-miss count, fallback duration, and the existing collision,
clearance, completion and timing fields. A near miss is a non-collision signed
margin in `[0, 0.10) m`. The former development packages that exercised this
contract were purged before the new campaign; the contract is retained as
design-only and no prior metric is active. The historical v2--v9 run
identifiers are retained only as provenance labels; no run directory or metric
payload remains in the workspace and none is a confirmatory source.

The paired bootstrap summary also reports comparator-minus-CCA effects for path
length, tracking/yaw RMSE, command variation and fallback duration when those
fields are present. Positive values mean the reference CCA outcome is lower for
the corresponding error/activity metric; this sign convention is recorded with
the effect interval.

The full-URDF footprint correction on 2026-08-14 invalidates all v7--v9
development outputs because they were generated under the former generic
radius. Those outputs were purged; only the design decision and purge audit
remain, so they cannot seed a confirmatory comparison.

## Cổng tái lập

Manifest phải ghi protocol version, map geometry, initial state, reference,
scenario, seed, controller version, solver settings, environment fingerprint
và hash của raw log. Failure, timeout, infeasibility, NaN và fallback vẫn thuộc
mẫu số với mã nguyên nhân; không thay context bằng dữ liệu tương lai khi LSTM mất tín hiệu.

MATLAB có profile `bounded` chỉ để kiểm tra plumbing và failure inspection; phần
so sánh controller chính nằm ở Python map runner. Các
gói bounded MATLAB trước đây đã bị xóa trong clean reset; không có MATLAB result
package hoạt động được giữ lại. Profile `full` vẫn là cấu hình duy nhất có thể
mở Gate-A, và mọi kết quả MATLAB đều chỉ hỗ trợ claim mô phỏng, không hỗ trợ
claim robot thật hoặc real-time.

Nhánh MATLAB legacy dùng snapshot context cho các kiểm tra risk-row tương thích;
nó không phải nguồn claim dynamic-human của nghiên cứu position-state. Dynamic
human motion, CCA-only internal future-position prediction và local-path logic
được thực thi trong map Python. Không có mảng `humanPositionsM` được xuất ra;
prediction nội bộ không trở thành artifact hoặc ảnh overlay.

[[00_MOC/project-map]] · [[06_Methods/methods-overview]] · [[06_Methods/evaluation-protocol]] · [[05_Theory/system-model]]
