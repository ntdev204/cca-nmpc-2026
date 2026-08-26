# PR30 — Thực nghiệm robot vật lý

> **Trạng thái goal hiện tại:** `DEFERRED — OUTSIDE CURRENT GOAL`.  
> **Trạng thái lưu vết:** `REVIEWED`; static no-ROS hardware-entry preflight đã
> `PASS` và design đã qua review, nhưng physical admission vẫn `BLOCKED` và
> chỉ được thực thi sau phê duyệt an toàn/đạo đức.  
> **Mục tiêu:** kiểm sim-to-real trong miền cụ thể, không trình diễn để thay dữ liệu.
> **Phiên bản hợp đồng máy:** `1.3.0`
> (`schemas/physical-experiment-config.schema.json`, position-state revision
> `1.3.0`).

## 1. Các giai đoạn bắt buộc

1. **H0 bench/static:** kiểm sensor clock/frame, e-stop, watchdog, velocity
   command, pose feedback, actuator lag và independent pose; không có người
   trong vùng chạy.
2. **H1 repeatable target:** mannequin/robotic target hoặc replay an toàn để có
   paired repeatability và kiểm full stack.
3. **H2 controlled human study:** người trưởng thành có consent, protocol ethics
   được duyệt, safety operator và vùng thoát.
4. **H3 external site (nếu có):** site/camera/floor mới; là bằng chứng external
   chứ không bắt buộc được gộp với H2.

Không chuyển giai đoạn nếu stage trước còn collision, watchdog, frame/timestamp
lỗi, uncontrolled motion hoặc deadline/fallback vượt stop criterion.

### Cổng máy trước khi chuyển sang `running`

Config vật lý phải validate và giữ hash của protocol-freeze record, stage-gate
record, safety plan, stop-rule record, target-hardware manifest, ground-truth
calibration/uncertainty, evaluation config và environment manifest. Với run
confirmatory còn phải có focused-literature-audit record, SHA-256 của record,
người duyệt và thời điểm duyệt. Schema từ chối `running/completed` nếu thiếu
focused-audit record hoặc protocol-freeze record.

H0/H1 có thể ghi ethics/consent `not_required` khi không có người tham gia, nhưng
safety, stop rules, stage approval và target-hardware manifest vẫn bắt buộc. H2/H3
chỉ chạy khi ethics là `approved/exempt`, consent ledger là
`participant_complete`, privacy/retention plan đã hash và safety operator độc lập
đã được phân công.

## 2. Ethics và safety case

Trước H2 cần mã phê duyệt/miễn trừ ethics có thẩm quyền, consent form, privacy/
retention plan và procedure rút dữ liệu. Không thu trẻ em/nhóm dễ tổn thương nếu
không có phê duyệt riêng. Raw video được mã hóa/quản lý truy cập; publication
overlay được anonymize theo consent/license.

Safety plan khóa speed/acceleration, command saturation, minimum separation, physical barrier
khi cần, emergency stop, remote disable, safety operator độc lập và adverse-event
procedure. Stop ngay khi contact/near-contact nghiêm trọng, mất localization,
sensor stale, actuator bất thường, e-stop lỗi hoặc operator yêu cầu. Sự kiện vẫn
được log, không chạy tiếp để đủ mẫu. Stop-rule record còn phải khóa ngưỡng
deadline/fallback; e-stop, remote disable và watchdog đều phải được xác minh bằng
máy trước mỗi stage.

## 3. Thiết kế đo

Robot, compute board, sensors, firmware/OS, battery, payload, floor/site, camera
calibration, controller/model hash và thermal/power mode được ghi. Ground truth
độc lập dùng motion capture, calibrated overhead camera hoặc hệ đo có uncertainty
định lượng; estimator đang đánh giá không được tự làm ground truth.

Phải ghi rõ interface điều khiển thực tế trong hardware manifest. Phạm vi vật lý
dùng điều khiển pose/trạng thái sáu biến

\[
s=[x,y,\theta,v_x,v_y,\omega]^{\mathsf T},
\]

và lệnh vận tốc thân
\(u=[v_x^{\rm cmd},v_y^{\rm cmd},\omega^{\rm cmd}]^{\mathsf T}\). STM chỉ
nhận lệnh vận tốc; bộ điều khiển cấp cao chịu trách nhiệm bám pose và tạo lệnh
này. Không yêu cầu đo hoặc hiệu chuẩn mô-men/dòng điện cho PR30.

H1 dùng các trajectory lặp lại để paired controller comparison. H2 dùng
within-participant/crossover block khi phù hợp; controller order randomize và
counterbalance, có washout/rest. Participant không được yêu cầu đi vào tình huống
nguy hiểm để tạo failure. Deviations của người được đo, không chỉnh tay path sau
khi biết controller.

Cỡ mẫu được tính từ pilot/precision trong PR40; frame/timestep không phải sample
độc lập. Báo participant, scene, trial và run counts cùng attrition/reason.

## 4. Kịch bản và outcomes

Kịch bản vật lý là subset an toàn của PR20: crossing, head-on/counterflow, stop--
go, occluded emergence và multi-human chỉ sau staged clearance. Kích thước/hình
học/speed được đo và version hóa.

Đo cùng safety/task/tracking/runtime outcomes ở PR21, cộng independent clearance,
pose/velocity tracking error, perception detection/track failures, network/sensor
latency, battery/temperature và e-stop/watchdog events.
Timing báo P50/P95/P99/max và miss rate trên target hardware; không suy ra hard
real-time chỉ từ mean.

Mỗi trial `completed` hoặc `failed` có một run manifest riêng. Trường
`scientific_outcome` luôn ghi việc trial có nằm trong mẫu số hay không,
termination/failure code, collision/clearance, fallback, constraint/slack và
deadline/timing. Field không áp dụng phải ghi rõ `applicable=false` và lý do;
không được bỏ trial sau collision, e-stop, timeout hoặc lỗi phần cứng.

## 5. Visual và qualitative evidence

Mỗi retained trial có synchronized raw logs/video khi việc lưu trữ được phê
duyệt. Overlay ngữ cảnh trên chuỗi ảnh/video gồm bounding box/keypoints, vị trí,
tốc độ, hướng trái/phải/tiến/lùi, độ tin cậy, trạng thái hợp lệ và controller
state/fallback. Chỉ CCA-NMPC được phép giữ dự đoán vị trí người nội bộ cho
chance rows; recorder không xuất hoặc vẽ chuỗi đó trên ảnh. Local path chỉ là
quỹ đạo của robot và được ghi trong log điều khiển. Ví dụ được chọn
theo PR40, gồm median, boundary, failure và OOD; video đẹp không thay aggregate
statistics.

Hai coder blinded với controller khi khả thi đánh giá freezing, hesitation,
oscillation, passing-side change, uncomfortable approach và recovery theo rubric
tiền đăng ký. Không gọi đây là comfort/user experience nếu không hỏi participant
bằng instrument đã xác định.

## 6. Claim boundary và cổng chấp nhận

### 6.1 Static entry preflight hiện tại

`python -B scripts/python/tools/validate_hardware_entry.py` đã kiểm tra CAN ID/
CRC contract, STM32 serial frame bridge và decoder parity với STM, mini-Mecanum
URDF binding, position-state/body-velocity boundary, commissioning lock, direct
CSV/JSON mapping, no-ROS runtime path và H0 template. Report
`research/metadata/hardware/pr30_entry_preflight_20260813.json` có
`status=PASS` nhưng `admission_status=BLOCKED`: chưa có package hardware thật,
physical specification/calibration/ground truth, stage-gate hoặc target-hardware
manifest đã duyệt. Đây là software/interface preflight, không phải hardware
evidence.

Gói direct có `capture_source` khác `unknown` hiện phải kèm
`calibration.json` đã hash trong manifest. File này khóa model Astra-S/N10P,
intrinsics/extrinsics và residual calibration; thiếu hoặc lệch hash thì
`final_pack.py` và `ctx_run.py` từ chối gói trước khi training/benchmark.

H0/H1 chỉ hỗ trợ integration/repeatability, không phải human-safety claim. H2 chỉ
hỗ trợ cấu hình/site/population đã thử. Không tuyên bố hệ thống an toàn ngoài
miền, autonomous deployment hay regulatory compliance.

PR30 đạt `VERIFIED` khi ethics/safety approvals và consent hợp lệ, stage gates có
chữ ký, calibration/ground-truth audit pass, expected/observed trial ledger giữ
mọi failure/attrition, raw-to-summary tái sinh được, adverse events được báo và
claim sim/hardware trong Overleaf tách rõ. Config và từng run phải validate lần
lượt bằng `schemas/physical-experiment-config.schema.json` và
`schemas/run-manifest.schema.json`; timing claim phải trỏ đúng target-hardware
manifest, không dùng host timing thay thế.

## 7. Implementation checkpoint — 2026-08-13 06:06 ICT

`final_pack.py`, `ctx_run.py`, `map_run.py` và `analyze_run.py` now share a
hash-bound calibration-sidecar contract. A non-unknown capture source is
rejected unless `calibration.json` contains the declared camera/LiDAR identity,
camera intrinsics, both sensor-to-robot extrinsics and nonnegative calibration
residuals; the manifest and checksum file must bind the same digest. This is a
software gate only. No physical package, calibration record or motion trial is
present, so PR30 is `REVIEWED` for design only and hardware admission remains
blocked.

## 8. Implementation checkpoint — direct recorder scaffold

The no-middleware entry path is now implemented in
`src/hardware.py` and `scripts/python/tools/record_hardware.py`.
The recorder opens Astra-S through OpenNI2, decodes only the explicitly declared
N10P serial packet profile, and supports both the existing CCA CAN telemetry
contract and the legacy STM32 serial bridge. The STM32 path
reproduces the 11-byte body-velocity command and 24-byte telemetry frames. For
dynamic-human trials, actuation is admitted only through the explicit
`--controller cca_nmpc` mode, which computes
position-state body-velocity commands online from a sealed LSTM checkpoint,
fixed global path and current context, with zero-command fail-safe on warmup,
invalid context, deadline miss or STM stop. Direct CSV/JSON evidence contains `context.csv`,
`robot_state.csv`, `control.csv`, `lidar.csv`, `events.csv`, `map.json`, and
`calibration.json`; capture metadata and JPEG overlays remain in the adjacent
frame sidecar. A validated YOLO26s-pose TensorRT engine provides the person
measurement. The first context-only capture may omit the LSTM checkpoint so
that its real `context.csv` can become the initial training data; in that mode
each overlay is explicitly marked `LSTM=disabled`. A supplied frozen
self-supervised LSTM checkpoint provides the causal context overlay and uses
`warmup/active/invalid` status labels. The recorder enforces the
frozen 0.1 s context sampling interval, records the raw OpenNI device timestamp
when exposed, keeps the host receive timestamp as the cross-sensor `t_ns`, and
can reject color/depth pairs beyond a configured skew limit. It rejects
unaligned color/depth frames rather than inventing a projection. The recorder
itself never exports or draws a human trajectory; CCA-NMPC may maintain an
 internal future-position prediction for chance rows; that estimate is never
exported or drawn. The external mode is capture-only unless explicitly used for
commissioning; without a schedule it sends only zero velocity and is not an
admitted controller for a dynamic-human final trial. The logged robot state is
`[x_m,y_m,theta_rad,vx_mps,vy_mps,omega_radps]`; `robot_state.csv` keeps
`yaw_rad`/`wz_radps` as compatibility aliases. This physical scope requires no
torque/current channel.

Every saved Astra-S frame must have a paired overlay. The overlay explicitly
labels `LSTM=disabled` when no checkpoint is supplied, `LSTM=active` after the
causal history window is available, and `LSTM=warmup` or `LSTM=invalid` before
that point; this prevents a checkpoint-free or startup frame from being
misrepresented as a model prediction. The overlay contains only
the current measured context and pose/keypoints, never a human future
trajectory or the robot local path. The CCA internal prediction is not part of
the image overlay or raw context CSV.

The overlay also prints `LSTM_PATH=<local checkpoint path>` (wrapped across
lines when necessary). A missing checkpoint is rendered as
`LSTM_PATH=<not-configured>`, so every frame makes the model provenance visible
without implying that the model was active during warmup.

The implementation is an integration scaffold, not physical evidence. It has
decoder, geometry, odometry, CSV, metadata, and context-interface tests, but no
device was opened in this checkpoint. The template intentionally leaves serial
ports, CAN channel, firmware, robot dimensions, calibration, engine, checkpoint,
and map as unresolved values. Therefore PR30 is `REVIEWED` for design only,
hardware admission remains blocked, and no timing, sensing, safety, or
robot-performance claim is promoted.

The `rai_robot_urdf` intake remains a read-only reference for link and sensor
roles. Its mesh-derived footprint is not treated as the physical robot
measurement. The current user-supplied runtime specification records a
400 mm by 400 mm total footprint (including wheels), a 50 mm wheel-radius
interpretation, LiDAR height 240 mm, camera height 200 mm, LiDAR front-edge
distance 100 mm, and camera front-edge distance 35 mm. With robot-frame
`+x` forward and a 200 mm half-length, the implied sensor positions are
`x_L=100 mm` and `x_C=165 mm`; the camera is therefore 65 mm ahead of the
LiDAR and is pitched 20 degrees downward. These values are hash-bound in
`configs/physical_robot.json`, but independent dimensional measurement and
sensor calibration remain H0 prerequisites.

The online CCA entry now rejects a checkpoint whose calibration metadata is
`not_fit` or is not independent of the training, validation and test splits.
This gate is evaluated before a device is opened or any actuation command is
sent. An uncalibrated checkpoint may be used only in a development pilot whose
manifest explicitly remains candidate-only.

The online position-state controller also consumes the URDF-derived footprint
from the prepared hardware config. Its human-clearance default is tied to
that radius, and a stale explicit clearance is rejected before capture. This
pre-actuation parity check does not replace H0 dimensional measurement.

## 8. Dynamic-human and software recheck — 2026-08-13

The direct path remains CCA-NMPC-only for a moving-person final trial. Its
future-position estimate is controller-internal; the exported CSV/JSON and
image overlay contain current observations only. The associated score-loop
and recorder regressions are covered by Python `203 passed`; this does not
open physical admission or constitute a robot experiment.

## 9. Single no-ROS operator path — 2026-08-14

Use `scripts/python/tools/hardware_entry.py` as the only operator entrypoint.
It first reads the complete `rai_robot_urdf` package and writes an intake record
with hashes for the package, all 37 URDF model files, the selected wheel/body/
sensor meshes, wheel origins and camera/laser mounts. For `mini_mec_robot`, the
record exposes four wheel components, their joint axes and link masses, the
Astra-S/N10P target mount roles, and the xacro sensor contract (ray lidar,
RGB/depth camera and IMU) as simulation-only metadata. The generic mesh assets
do not establish the identity or calibration of the physical sensors. The
intake also derives a reference map footprint from transformed mesh bounds and
fixed mounts, but that value is not the physical-unit authority. Runtime map
geometry is instead bound to the user-supplied hash in
`configs/physical_robot.json`: 400 mm by 400 mm including wheels, with
`r=0.2828427125 m` as the circumscribed half-diagonal implied by that
footprint. The 50 mm wheel-radius interpretation and all sensor offsets still
require target-unit commissioning verification.
It then creates a runtime config only when a separate measured physical spec is
supplied; without that file the geometry fields remain null and preflight fails
closed. The entrypoint can create a zero-terminated body-velocity commissioning
schedule and does not start any middleware node.

```bash
export PYTHONPATH=src:scripts/python
python3 -B scripts/python/tools/hardware_entry.py inspect \
  --output research/metadata/hardware/mini_mec_intake_<UTC>.json
python3 -B scripts/python/tools/hardware_entry.py prepare \
  --output configs/hardware_runtime.<run>.json \
  --stm-port /dev/rai_controller --lidar-port /dev/rai_lidar \
  --lidar-baud <measured-N10P-baud> --firmware <STM32-firmware-id> \
  --physical-spec configs/physical_robot.<run>.json
python3 -B scripts/python/tools/hardware_entry.py schedule \
  --output experiments/commands/<run>.csv --kind forward \
  --duration-s 5 --step-s 0.1 --speed-mps 0.05
```

Before any device access, run the no-device preflight with the concrete config,
calibration, map, target Jetson TensorRT manifest and planned output path:

```bash
python3 -B scripts/python/tools/hardware_entry.py preflight \
  --config configs/hardware_runtime.<run>.json \
  --calibration <calibration.json> --map <map.json> \
  --pose-engine <yolo26s-pose.engine> \
  --pose-manifest <pose-manifest.json> \
  --output experiments/runs/<run-id> --duration-s <seconds> \
  --report experiments/runs/<run-id>-preflight.json
```

The command checks inputs and provenance only; it does not open Astra-S, N10P
or STM32 and does not send a command. `record` repeats the same checks before
opening devices.

After H0 approval, calibration, map and target Jetson YOLO26s-pose engine
provenance are present, call `hardware_entry.py record` with the recorder's
calibration/map/engine arguments. `--confirm-motion` and a validated
`--safety-record` are mandatory before a nonzero command; without either the
recorder remains zero-velocity. The safety record must verify approval,
emergency stop, remote disable and watchdog. For a moving
person trial use `--controller cca_nmpc` and omit `--command-csv`. The only
future-person estimate is CCA-internal; it is never written to CSV/JSON or
drawn on an image. This entrypoint is code/interface evidence only until a
real device package is sealed.

The current host validation for this entrypoint is Python `214` passing tests,
Ruff `PASS`, repository validation `PASS`, and hardware-entry preflight
`PASS/BLOCKED`; these are software/interface checks and not a physical result.

## 10. Direct STM32 bring-up and capture script — 2026-08-14

For the first hardware connection, use the smaller direct recorder before the
full Astra-S/N10P/CCA-NMPC stack:

```bash
python3 -B scripts/python/tools/stm_experiment.py \
  --port <stm-serial-port> --baud 115200 \
  --duration-s 30 --period-s 0.05 --pattern observe \
  --operator <operator-id> --firmware-id <firmware-id> \
  --output experiments/runs/<new-bringup-id>
```

This path uses the audited legacy serial frame from the bridge source in
`reference/robot/turn_on_rai_robot`: 11-byte body-velocity commands, 24-byte
telemetry, big-endian signed millimetre units and XOR checksum. It does not
launch ROS/ROS 2. It writes only direct CSV/JSON data and integrates the
reported body velocity into the six-state position record. It never infers
wheel dimensions from URDF and marks physical geometry as pending.

Use `--pattern observe` first. A moving commissioning pattern is permitted
only after the H0 safety record has verified emergency stop, remote disable and
watchdog, and requires both `--allow-actuation` and `--safety-record`:

```bash
python3 -B scripts/python/tools/stm_experiment.py \
  --port <stm-serial-port> --baud 115200 \
  --duration-s 10 --period-s 0.05 --pattern forward --speed-mps 0.03 \
  --allow-actuation --safety-record <h0-safety.json> \
  --operator <operator-id> --firmware-id <firmware-id> \
  --map-json <existing-map.json> \
  --output experiments/runs/<new-commissioning-id>
```

Acceptance for this bring-up is limited to: serial open/close, valid frame
checksum, nonempty telemetry (if the firmware publishes it), explicit zero
command on exit, and a self-contained manifest with bridge-source hashes. A
missing telemetry frame is recorded as `telemetry_missing`; it is not replaced
with a fabricated state. The output is not a Q1 result and cannot open H1/H2.
After the robot dimensions are measured, create a versioned physical spec from
`configs/physical_robot.template.json`, pass it to `hardware_entry.py prepare
--physical-spec`, and then run the no-device preflight before the full recorder.

The current direct recorder also latches an STM stop flag before selecting a
nonzero command; a latched stop forces zero and is recorded in `events.csv`.
This is a software fail-safe only and does not replace H0 e-stop/watchdog
verification on the target robot.

## 11. Low-level transport ownership — 2026-08-14

The low-level STM32 serial boundary is now implemented in the host-buildable
C++ core at `src/control/include/control/stm_serial.hpp` and
`src/control/src/stm_serial.cpp`. It reproduces the 11-byte body-velocity command,
the 24-byte telemetry frame, signed big-endian quantization and XOR checksum
from the reference bridge. `src/control/stm_probe.cpp` is the direct commissioning
executable and writes only CSV/JSON capture files without ROS or ROS 2.

The wire-level CCA CAN CRC and frame codec are likewise in
`src/control/include/control/can.hpp` and `src/control/src/can.cpp`. Python
retains calibration, evidence metadata, perception, LSTM and CCA-NMPC
orchestration; the Python wire codec is a compatibility path for offline
analysis, not the preferred low-level transport implementation. No C++ binary
has been run on the target robot in this checkpoint, and no physical evidence
or timing claim is promoted.
