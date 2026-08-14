---
type: tool-source
status: primary-documentation-verified
evidence_status: official-documentation
evidence_level: documentation
citekey: ultralytics2026yolo26pose
doi:
zotero_uri:
verified_date: 2026-08-14
---

# Ultralytics YOLO26-pose — công cụ đo lường

## Nguồn chính thức

- [YOLO26 model documentation](https://docs.ultralytics.com/models/yolo26)
- [Pose estimation documentation](https://docs.ultralytics.com/tasks/pose)
- Được kiểm tra lại ngày 2026-08-14; đây là tài liệu phần mềm, không phải nguồn
  chứng minh novelty của bộ điều khiển.

## Thông tin được dùng

Tài liệu xác nhận hậu tố `-pose`, các checkpoint YOLO26-pose và đầu ra pose
gồm tọa độ keypoint cùng confidence. Mô hình pose mặc định dùng 17 keypoint
COCO. Các thông tin này chỉ xác định giao diện perception của nghiên cứu:

```text
image -> bounding boxes/keypoints/confidence
      -> current position, speed, direction, validity
      -> CCA--LSTM context interface
```

Không dùng tài liệu này để suy ra accuracy, latency, generalization hoặc
real-time performance trên Astra S của nghiên cứu. Các giá trị đó phải được
đo trên cohort và target hardware của chính protocol.

## Ranh giới claim

YOLO26s-pose là công cụ “mắt” của robot, không phải đóng góp thuật toán. Ảnh
chỉ cung cấp context hiện tại; không tạo, lưu hoặc vẽ human future trajectory.
Robot local path được sinh trên map Python theo trigger của CCA.

## Liên kết tri thức

- [[03_Literature/source-index]]
- [[03_Literature/web-verified-gap-sources]]
- [[04_Research_Gap/research-gap]]
- [[06_Methods/perception-protocol]]
- [[08_Decisions/decision-register]]

Related hub: [[00_MOC/project-map]]
