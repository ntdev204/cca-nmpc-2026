---
type: technical-source-note
status: verified-source-boundary
scope: hardware-interface
paper_edit: prohibited
---

# Astra-S và N10P: nguồn kỹ thuật cho recorder

## Camera Astra-S

Nguồn hãng Orbbec mô tả Astra Series là camera structured-light dùng USB và
OpenNI SDK. Trang SDK của hãng còn công bố gói Astra SDK cho Linux x64 và
Linux ARM64, nhưng cũng ghi đây là dòng legacy; vì vậy runtime phải khóa đúng
SDK/binding và firmware đang có trước H0, không suy ra khả năng real-time từ
trang sản phẩm. Recorder dùng OpenNI2 trực tiếp và giữ frame gốc/khung depth,
không dùng middleware robot.

OpenNI 2 exposes a frame timestamp in microseconds. The recorder stores that
value (converted to nanoseconds) as `camera_device_t_ns` when the Python binding
exposes it, while `t_ns` remains the host receive timestamp used to align the
camera with serial and CAN streams. Color/depth device timestamps are compared
when both are available; a configured pair-skew limit can fail the capture.

- [Orbbec Astra Series](https://www.orbbec.com/products/structured-light-camera/astra-series/)
- [Orbbec Astra SDK](https://www.orbbec.com/developers/astra-sdk/)
- [Orbbec SDK documentation](https://orbbec.github.io/OrbbecSDK/)
- [OpenNI 2.0 frame timestamp API](https://documentation.help/OpenNI-2.0/classopenni_1_1_video_frame_ref.html)

## LiDAR N10P

Trang hãng LSLiDAR xác nhận dòng N10 dùng cho navigation/obstacle avoidance.
Mã model và firmware của thiết bị thực tế phải được đọc lại trước khi chạy;
`N10P` trong recorder là định danh cấu hình do protocol yêu cầu, không phải
bằng chứng rằng mọi thiết bị N10/ N10-P có cùng packet format.

Để viết decoder tối thiểu không ROS, implementation hiện đối chiếu nhánh
driver chính thức của LSLiDAR: packet `N10_P` dài 108 byte, 16 điểm, góc bắt
đầu tại offset 5, góc kết thúc tại offset 105, baud tham chiếu 460800 và checksum
additive ở byte cuối. Manual vendor của N10 lại công bố 230400 bps; vì vậy code
không dùng baud mặc định ẩn: cấu hình phải khai báo baud đã đo từ đúng N10P
firmware cùng profile `n10p-108b-v1`. Profile vẫn phải được đối chiếu với
manual/firmware của đúng thiết bị trước physical run. Đây là parity kỹ thuật để chuẩn bị H0; trước physical run
phải đối chiếu với manual/firmware của đúng thiết bị và lưu packet capture,
không gọi parity này là calibration hay measurement validation. Repo driver
được đọc nguồn nhưng không được import làm ROS/ROS2 runtime.

- [LSLiDAR N10 navigation and obstacle-avoidance product page](https://www.lslidar.com/product/n10-navigation-obstacle-avoidance-lidar/)
- [LSLiDAR N10 manual (vendor PDF)](https://www.lslidar.com/wp-content/uploads/2024/09/N10.pdf)
- [LSLiDAR N10/N10P driver source used for packet parity](https://github.com/Lslidar/Lslidar_ROS2_driver)

## Project robot model and sensor mounts

The project package `rai_robot_urdf` contains 37 URDF model files. The selected
runtime model is `mini_mec_robot`, whose four wheel links are `lf`, `rf`, `lb`
and `rb`. The intake binds each wheel joint origin, axis, mass and visual/
collision mesh, together with the body and controller links. `camera_link` and
`laser_link` are fixed mounts; their role mapping is Astra-S and N10P for the
target hardware, respectively. The URDF mount is not a calibration measurement.

The companion xacro records simulation-only sensor settings: ray lidar at 360
samples and 10 Hz, RGB camera at 640x480 and 30 Hz, depth camera at 640x480 and
10 Hz, and an IMU at 100 Hz. These settings describe the simulator source only;
physical identity, baud, intrinsics, extrinsics, clock skew and firmware remain
open H0 measurements.

The reproducible intake is
`research/metadata/hardware/mini_mec_intake_20260814.json`; the parser and
entrypoint are `scripts/python/tools/hardware_entry.py`. The record is a
source/provenance audit and currently reports no attached serial device.

## Liên kết

[[00_MOC/project-map]] · [[03_Literature/web-verified-gap-sources]] ·
[[06_Methods/final-run-data-package]] ·
[[06_Methods/perception-protocol]] · [[01_Governance/knowledge-boundary]]
