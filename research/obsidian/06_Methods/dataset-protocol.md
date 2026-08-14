---
type: dataset-design
status: design-only
scope: research-knowledge
---

# Thiết kế dữ liệu nghiên cứu

Đây là đặc tả thiết kế, không phải kho dữ liệu và không phải báo cáo kết quả.
Payload, ảnh, checkpoint, manifest chạy và số liệu đánh giá không được lưu trong
Obsidian. Khi triển khai, registry và kho lưu trữ riêng phải tham chiếu đúng đặc
tả này.

## Các lớp dữ liệu

| Lớp | Vai trò tri thức | Nguồn được phép | Đầu ra cần thiết |
|---|---|---|---|
| Ảnh nhận diện | kiểm tra giao diện perception | ảnh người thật tải từ Internet, có giấy phép phù hợp | hộp giới hạn, keypoint, độ tin cậy, provenance |
| Chuỗi ngữ cảnh | tạo history cho LSTM | video/chuỗi công khai hoặc ghi nhận có quyền sử dụng | vị trí tương đối, vận tốc quan sát, cờ hợp lệ |
| Map điều khiển | kiểm tra CCA--NMPC trên bản đồ Python | map được mô tả bằng hình học và seed | context footprint động, conflict và local-path trigger |
| Hiệu chuẩn cảm biến | xác định quy đổi camera--LiDAR--robot | phép đo Astra S và N10P có quy trình | extrinsic, thời gian, đơn vị và sai số đo |

Ảnh nhận diện phải là ảnh thật trên Internet; ảnh tự tạo, ảnh tổng hợp và ảnh
được sinh bằng AI không thay thế tập kiểm tra này. Ảnh tĩnh chỉ đánh giá giao
diện nhận diện, không được diễn giải thành quỹ đạo người. Quỹ đạo di chuyển của
robot được sinh trên map; context của người chỉ gồm vị trí, tốc độ và hướng
(`left`, `right`, `forward`, `backward`).

## Provenance tối thiểu

Mỗi mẫu triển khai phải có URL trang gốc, URL asset, tác giả/nhà cung cấp, giấy
phép, ngày truy cập, tên tệp, SHA-256, kích thước, miền cảnh, số người, che
khuất, điều kiện ánh sáng, nguồn annotation và trạng thái kiểm tra thủ công.
Không tải hoặc tái phân phối nguồn có điều khoản cấm sử dụng. Chỉ bản ghi đã
kiểm tra quyền tải, xử lý và annotation mới được đưa vào tập được phê duyệt.

## Phân vùng và rò rỉ

- Đóng băng `train`, `validation`, `calibration`, `test_id` và `test_ood` trước
  khi chọn mô hình hoặc ngưỡng.
- Chia theo subject, recording, scene và source; các frame kề nhau hoặc near-
  duplicate phải ở cùng partition.
- Hiệu chuẩn tách khỏi validation và test. Test chỉ mở sau khi protocol,
  checkpoint và threshold đã khóa.
- Mỗi thay đổi ảnh, annotation, phép biến đổi hoặc partition tạo một phiên bản
  mới và một hash mới.

## Annotation và hợp đồng context

Annotation kép trên tập con phân tầng, quy tắc giải quyết bất đồng và mã lý do
cho trường hợp mơ hồ phải được định nghĩa trước. Hợp đồng context gồm
`position`, `speed`, `direction`, `confidence`, `timestamp` và `context_valid`.
History thiếu hoặc detector mất tín hiệu trả `context_valid=false`; không nội
suy và không tự sinh local path từ dữ liệu thiếu.

## Liên kết

[[00_MOC/project-map]] · [[06_Methods/dataset-sources]] · [[06_Methods/perception-protocol]] · [[06_Methods/lstm-protocol]] · [[07_Analysis/web-cohort-acquisition-20260814]] · [[01_Governance/status-and-provenance]]
