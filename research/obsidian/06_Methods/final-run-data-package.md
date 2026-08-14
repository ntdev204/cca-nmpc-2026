---
type: physical-data-protocol
status: planned
evidence_status: knowledge-only
scope: final-run-data-package
---

# Gói dữ liệu cho một lần chạy robot

Đây là protocol thu thập dữ liệu, không phải kho dữ liệu và không phải báo cáo
kết quả. Gói final và mọi file xuất ra phải nằm ngoài Obsidian. MATLAB/Python
không cần chạy trong lúc robot hoạt động; recorder của bộ điều khiển hoặc
firmware ghi dữ liệu theo đúng schema dưới đây.

## Deliverable tối thiểu

```text
final-run-<UTC>/
  robot_state.csv
  control.csv
  context.csv
  lidar.csv
  events.csv
  map.json
  calibration.json
  manifest.json
  checksums.sha256
```

`map.yaml` và `map.pgm` chỉ là tệp phụ tùy chọn khi cần giữ ảnh occupancy
nguyên bản; chúng không phải deliverable bắt buộc. Với capture source khác
`unknown`, `calibration.json` là bắt buộc và phải chứa calibration Astra-S/N10P
đã hash-bind trong manifest.

The direct STM bring-up package is a commissioning subset: it contains
`robot_state.csv`, `control.csv`, `events.csv`, the command schedule and
capture/manifest metadata only. It is not a final sensor package and cannot be
used as a Q1 result until the full Astra-S/N10P, calibration and map contract is
sealed.

`robot_state.csv` có state sáu biến `t_ns,x_m,y_m,theta,vx,vy,omega`; trong CSV
triển khai, `theta` và `omega` được ghi lần lượt là `yaw_rad` và `wz_radps`, và
nếu có thì thêm trạng thái bốn bánh. `control.csv` có timestamp và nhóm lệnh
vận tốc thân `vx_cmd_mps,vy_cmd_mps,wz_cmd_radps`. Các nhóm wheel/torque không
thuộc yêu cầu của PR30. `context.csv`
có `t_ns,position_x_m,position_y_m,
speed_mps,direction,confidence,context_valid`; không lưu hay sinh quỹ đạo của
người. `lidar.csv` có một dòng cho mỗi scan N10P với
`t_ns,point_count,points_json`; `points_json` giữ các điểm
`[angle_rad,range_m,intensity,return_id]` để có thể tái dựng phép đo cảm biến.
`events.csv` có tối thiểu `t_ns,event_type` và ghi
`local_path_generation`, `fallback`, `collision`, `solver_status`, `solve_ms`
cùng `iterations`, `risk_bound`, `risk_slack_m` và các mốc stop. Mọi bảng dùng robot time hoặc system time đã khai báo thống
nhất, đơn vị SI và frame ghi trong manifest.

Để huấn luyện/đánh giá LSTM theo split xác nhận, `context.csv` có thể bổ sung
`recording_id` (hoặc `episode_id`) và `split`; các assignment chính thức nằm ở
manifest `cca-context-split-manifest-v1` riêng, được khóa trước training. Gói
raw vẫn giữ nguyên các cột tùy chọn này và không được tự suy ra group từ thứ tự
dòng. Validator từ chối mọi cột `future_*`, `trajectory_*`, `path_*` hoặc biến
thể tương đương; context package chỉ được chứa snapshot hiện tại.

`map.json` phải chứa `frame_id`, `resolution_m`, `width`, `height`, `origin`
(`[x_m,y_m,yaw_rad]`) và mảng occupancy row-major (`-1` unknown, `0` free,
`100` occupied). Nếu dùng map server chuẩn, có thể giữ thêm `map.yaml` và
`map.pgm` để không mất thông tin hiển thị, nhưng hai tệp này không bắt buộc.

`manifest.json` phải ghi `run_id`, thời gian UTC, frame gốc, tên robot, phiên bản
controller/firmware, `control_interface=body_velocity`,
`control_mode=position_state`, state definition sáu biến, tên camera và LiDAR
(hoặc ghi rõ `not-declared`), map hash, calibration hash khi có capture thật,
schema version và số dòng của từng CSV.
`checksums.sha256` niêm phong toàn bộ CSV, map và manifest. Đây là gói dữ liệu
ngoài Obsidian; không cần chạy MATLAB/Python để replay hay dựng lại mô phỏng.

Cấu hình và điều kiện kiểm tra máy đọc được nằm trong
`configs/physical_experiment.template.yaml` và
`schemas/physical-experiment-config.schema.json` dưới trường
`final_data_package`.

## Ghi dữ liệu trên robot

Recorder độc lập phải bắt đầu trước controller và dừng sau khi robot đã dừng
an toàn. Nó đọc trực tiếp các bộ đệm trạng thái, lệnh điều khiển, ngữ cảnh từ
Astra S, dữ liệu tránh vật cản từ N10P và occupancy map; không phụ thuộc
runtime message layer hay file ghi lại toàn bộ phiên. Nếu recorder không nhận được map, copy map file vào cùng
thư mục run trước khi đóng gói.

### Hardware intake checkpoint — 2026-08-12

The current Windows session reported no serial port and no present STM/CAN,
Astra S or N10P device. No hardware CSV/JSON package was created or inferred
from this check. The protocol remains ready for the first physical capture;
until then, all context and controller outputs remain development-only.

### Hardware intake recheck — 2026-08-13 22:47 ICT

A direct Windows device scan again found no COM port, CAN adapter, STM bridge,
Astra-S/OpenNI2 device or N10P device. Only an unrelated UVC webcam was present;
the Python environment has `pyserial` and Ultralytics but no OpenNI2 or
`python-can` module. No device was opened, no command was sent, and no CSV/JSON
package was created. This is an intake observation for PR30, not a hardware
result or timing measurement.

### Direct recorder implementation checkpoint — 2026-08-13

The active no-ROS recorder is `scripts/python/tools/record_hardware.py`, with
sensor adapters and the CSV contract in `src/hardware.py`. It opens
Astra-S through OpenNI2, N10P through a serial stream, and CCA telemetry through
the direct CAN interface. The command requires a concrete hardware config,
calibration sidecar, copied Python map and validated YOLO26s-pose TensorRT
engine before opening any device. The first context-only capture may omit the
score-trained LSTM checkpoint; each such overlay is marked `LSTM=disabled` so
the resulting real `context.csv` can be used to train the first checkpoint.
When a checkpoint is supplied, the overlay records its `warmup/active/invalid`
state. The recorder stores context snapshots and the LSTM text overlay in an
adjacent frame sidecar; it does not generate or log a human path. The sidecar
verifies and records the selected URDF source and URDF/xacro hashes. Wheel
radius, wheel-span geometry and footprint are recorded only from the separately
measured physical-spec file; the mesh-derived CAD footprint is reference
metadata and cannot bind a physical capture by itself.
The direct transport dependencies are declared in the optional `hardware`
extra (`pyserial` and `python-can`); OpenNI2 remains a vendor SDK/runtime
binding and must be installed and hash-recorded for the supplied Astra-S unit.
The recorder enforces the frozen context sample period of `0.1 s`; a different
period requires a new dataset/model contract and is rejected.
The `external` mode is read-only for a final run; any scheduled actuation is
reserved for commissioning and is not an admitted dynamic-human result. The
explicit `cca_nmpc` mode computes body-velocity commands
online from the six-state odometry and current context. It requires a sealed
LSTM checkpoint, a map carrying the fixed global path and CCA settings, STM32
serial transport and `--allow-actuation`; warmup, invalid context, deadline
miss or STM stop produces a zero command. The CCA future-position estimate
remains in memory only.

The physical state contract is `[x,y,theta,vx,vy,omega]`; the direct STM
interface accepts body-velocity commands for position tracking and does not
require torque/current feedback. For `hardware`, `hardware_in_loop`, and
`real_offline` capture sources, the packager rejects `wheel_torque`; that
interface is retained only as legacy compatibility code and cannot label a
physical position-state package.

The template `configs/hardware_runtime.template.json` deliberately contains
`null` values for the serial port, CAN channel, firmware and robot dimensions.
Until these values and H0 safety records are supplied, this is executable
integration code and not a hardware result. No run, CSV, map or checkpoint is
created by the template itself.

### User-supplied physical specification — 2026-08-14

`configs/physical_robot.json` records the supplied 400 mm by 400 mm total
envelope, the 50 mm radius interpreted as wheel radius, LiDAR height 240 mm,
camera height 200 mm and a 20 degree downward camera pitch. With the robot
frame origin at the footprint centre and positive $x$ pointing forward, the
LiDAR is 100 mm behind the front edge ($x=+100$ mm) and the camera is 35 mm
behind the front edge ($x=+165$ mm). The record also stores the two original
front-edge distances so that the derived coordinates can be checked. This is a
user-supplied specification, not yet an independently verified calibration;
the H0 and physical-admission gates remain closed.

### Direct STM bridge checkpoint — 2026-08-14

`scripts/python/tools/stm_experiment.py` is the minimal no-ROS bring-up path
for the legacy serial bridge described by the read-only reference snapshot
`reference/robot/turn_on_rai_robot/src/rai_robot.cpp` and
`reference/robot/turn_on_rai_robot/include/turn_on_rai_robot/rai_robot.h`. It sends the 11-byte body-velocity
frame and decodes the 24-byte telemetry frame through
`src/hardware.py`; it does not launch a ROS node. The recorder
stores `robot_state.csv`, `control.csv`, `events.csv`, an exact command
schedule, `capture.json` and `manifest.json`, and always terminates with a
zero-velocity command. It also latches a telemetry stop flag before selecting a
subsequent nonzero command and records `stm_stop_latched`. A nonzero command is
fail-closed without an explicit actuation flag and a signed safety record.

The current URDF/xacro intake is CAD/reference metadata only. The runtime
recorder marks `physical_geometry_status: pending_measurement` and does not
derive wheel radius, wheel spans or footprint from that intake. A measured
`configs/physical_robot.<run>.json` with `status: measured` is required before
the full Astra-S/N10P/CCA-NMPC recorder can be admitted. No hardware run or
result is present in this checkpoint.

Knowledge links: [[06_Methods/tracking-contract]] ·
[[07_Analysis/pr30-entry-preflight-20260813]] ·
[[07_Analysis/current-evidence-index]]

### Ánh xạ telemetry CAN sang CSV

Với firmware STM hiện tại, recorder đọc frame CAN trực tiếp và gắn cùng một
đồng hồ đơn điệu `t_ns` cho mọi bảng:

| Nguồn | Bảng đích | Trường tối thiểu |
|---|---|---|
| `0x191` body command | `control.csv` | `vx_cmd_mps`, `vy_cmd_mps`, `wz_cmd_radps` |
| `0x199` applied command | `control.csv` | applied body setpoint và sequence |
| `0x19A` + `0x19B` wheel telemetry | `robot_state.csv` | bốn wheel speed; battery/PWM/fault nếu có |
| `0x198` status | `events.csv` | status, sequence, deadline và event stop/fallback |

Pose, vận tốc thân và yaw-rate trong `robot_state.csv` phải do estimator
odometry/IMU phía host ghi cùng timestamp; không được suy diễn rằng STM đã đo
trực tiếp các đại lượng này. Astra S và N10P chỉ cung cấp context/cảm biến cho
recorder, không tạo artifact quỹ đạo người; nếu CCA-NMPC dự đoán vị trí tương
lai thì chuỗi đó chỉ tồn tại nội bộ trong bộ điều khiển. `context.csv` giữ thêm
`camera_device_t_ns` khi OpenNI2 cung cấp timestamp thiết bị; `t_ns` vẫn là
host receive time để dùng chung với CAN và serial. `map.json` là occupancy map Python đã khóa
trước run và được chép nguyên vẹn vào thư mục final.

Trước khi chạy, kiểm tra clock, frame, calibration camera--LiDAR, dung lượng
đĩa và quyền ghi. Recorder phải ghi lệnh vận tốc thân và event
stop/fallback/collision. Giá trị
`control_interface` phải phản ánh interface thực tế, không phải chỉ tên của
mô hình NMPC.

## Kiểm tra và niêm phong gói final

Recorder trên robot ghi các CSV/map/calibration cần thiết. Sau khi robot đã dừng an toàn, chạy một
lần công cụ đóng gói trên chính máy robot hoặc chép thư mục sang máy nghiên cứu:

```bash
python3 scripts/python/tools/final_pack.py \
  --input final-run-<UTC> \
  --run-id final-run-<UTC> \
  --robot mecanum \
  --controller cca_nmpc \
  --clock robot_time \
  --camera "Astra-S" \
  --lidar "N10P" \
  --firmware "<firmware-version>" \
  --control-interface body_velocity \
  --capture-source hardware
```

Nếu logger đã ghi trực tiếp vào thư mục final thì không cần bước sao chép; công
cụ chỉ kiểm tra dữ liệu và tạo `manifest.json`, `checksums.sha256`. Manifest
phân biệt `integrity_status=verified` (đúng schema/hash) với
`evidence_status=captured-unverified` (đã khai báo nguồn thu nhưng chưa qua QA
độc lập); không trạng thái nào tự biến dữ liệu thành bằng chứng Q1.

Sau khi niêm phong, tạo phân tích ở thư mục riêng, không đặt vào gói raw:

```bash
python3 scripts/python/tools/analyze_run.py \
  --input final-run-<UTC> \
  --output experiments/analyses/final-run-<UTC>
```

`analysis.json` chỉ chứa số liệu dẫn xuất, giới hạn và liên kết hash tới gói
nguồn. Nếu thiếu ground truth độc lập, công cụ không sinh tracking error hoặc
confusion matrix; phân tích giữ trạng thái candidate cho đến khi QA độc lập.
`analyze_run.py` cũng kiểm tra checksum không trùng, tập file trong manifest
khớp đúng payload, map hash khớp và manifest có đủ identity camera--LiDAR--
firmware; package sai một điều kiện sẽ bị từ chối.

## Một entrypoint cho phần cứng mini-Mecanum

Không chạy ROS/ROS2 nodes; `reference/robot` chỉ là snapshot tham chiếu. Trên
Jetson/Raspberry Pi, dùng
`hardware_entry.py`; lệnh `inspect` đọc toàn bộ package `rai_robot_urdf` và
ghi hash của URDF/xacro, bốn bánh, mesh thân, camera, laser và thư viện asset
cảm biến. Lệnh `prepare` chỉ ghi geometry khi nhận một file physical spec đã
đo và có `status: measured`; URDF/xacro không phải nguồn thay thế. Lệnh
`schedule` tạo bài commissioning có hàng zero cuối. Các lệnh mẫu:

```bash
export PYTHONPATH=src:scripts/python
python3 -B scripts/python/tools/hardware_entry.py inspect \
  --output research/metadata/hardware/mini_mec_intake_<UTC>.json
python3 -B scripts/python/tools/hardware_entry.py prepare \
  --output configs/hardware_runtime.<run>.json \
  --stm-port /dev/rai_controller --lidar-port /dev/rai_lidar \
  --lidar-baud <baud-da-do> --firmware <stm32-firmware>
python3 -B scripts/python/tools/hardware_entry.py schedule \
  --output experiments/commands/<run>.csv --kind forward \
  --duration-s 5 --step-s 0.1 --speed-mps 0.05
```

Sau H0 và khi đã có `calibration.json`, map, engine TensorRT YOLO26s-pose và
manifest engine hợp lệ, gọi `hardware_entry.py record` với cùng các đối số của
`record_hardware.py`. Phải có cả `--confirm-motion` và `--safety-record` đã
kiểm tra approval, emergency stop, remote disable và watchdog; thiếu một trong
hai thì recorder chỉ gửi zero;
không có checkpoint LSTM thì chỉ được capture context ban đầu và overlay ghi
`LSTM=disabled`. Với trial người động, dùng `--controller cca_nmpc`, không dùng
`--command-csv`; chỉ CCA được giữ dự đoán vị trí người nội bộ và không xuất/vẽ
chuỗi đó.

## Tối thiểu phải có trong gói final

| Nhóm | Dữ liệu cần có |
|---|---|
| Đồng bộ | timestamp tăng nghiêm ngặt, không trùng, và clock dùng trong run |
| Khung tọa độ | frame gốc, frame robot và transform calibration trong `calibration.json` |
| Robot | state `[x,y,theta,vx,vy,omega]` và trạng thái bánh/IMU nếu có |
| Điều khiển | lệnh vận tốc thân phục vụ bám pose |
| Tránh vật cản | toàn bộ scan N10P trong `lidar.csv` theo timestamp recorder |
| Nhận diện | context từ Astra S và camera calibration trong `calibration.json` |
| Bản đồ | `map.json` bắt buộc; `map.yaml` + `map.pgm` là bản phụ tùy chọn |

Các cảm biến và bộ điều khiển chỉ là nguồn nội bộ của recorder; chúng không cần
được xuất thành những file riêng trong gói final. Recorder chuyển chúng thành
năm CSV, một `map.json` và một `calibration.json` khi capture source là thật.

Sau khi công cụ đóng gói kết thúc, kiểm tra timestamp tăng nghiêm ngặt, không có
dòng rỗng, frame/đơn vị khớp manifest, map hash khớp và số dòng không bằng
không. Không tạo file replay.
Nếu có cột `camera_device_t_ns`, `final_pack.py` kiểm tra mỗi giá trị là số
nguyên không âm; cột này không thay thế clock chung `t_ns`.
Không ghi token, mật khẩu hay dữ liệu cá nhân không cần cho nghiên cứu.

## Liên kết

[[00_MOC/project-map]] · [[06_Methods/methods-overview]] ·
[[06_Methods/evaluation-protocol]] · [[01_Governance/status-and-provenance]]
· [[03_Literature/hardware-sensor-sources]]
