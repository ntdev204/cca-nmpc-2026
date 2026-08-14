---
type: proposal-note
status: novelty-at-risk
evidence_status: full-text-expanded
inheritance: legacy-hypothesis-reverify
overleaf_manuscript: false
---

# Đề xuất nghiên cứu — CCA-NMPC với giao diện dự báo LSTM

> Đây là ghi chú nghiên cứu, không phải bản thảo bài báo. Những khái niệm kế thừa từ ghi chú cũ chỉ là `legacy hypothesis` và phải được kiểm tra lại bằng tổng quan tài liệu/protocol mới.

## Tên dự kiến

**Phân bổ rủi ro theo ngữ cảnh, đóng dạng và minh bạch trong CCA-NMPC trạng thái vị trí cho robot Mecanum hoạt động quanh người**

Tên tiếng Anh tạm thời: *Transparent Closed-Form Context Risk Allocation in
Position-State CCA-NMPC with an LSTM Context Interface*.

## Bài toán

Một robot Mecanum phải theo đường tham chiếu trong không gian có người, trong khi
trạng thái tương tác sắp tới không chắc chắn và mức độ nguy hiểm không chỉ phụ
thuộc khoảng cách hiện tại. Perception/LSTM chỉ cung cấp snapshot ngữ cảnh hiện tại
(vị trí, tốc độ, hướng và độ tin cậy). Trong CCA--NMPC, vận tốc ngữ cảnh nhân quả
được tích phân nội bộ cho các hàng ràng buộc chance; phần dự đoán này không được
xuất thành quỹ đạo, lưu thành artifact hoặc vẽ lên ảnh. Các controller đối chứng
chỉ dùng snapshot quan sát hiện tại. Phân bổ cùng một mức rủi ro cho mọi event
người--bước có thể lãng phí budget ở sự kiện ít liên quan và thiếu thận trọng ở
tương tác khẩn cấp.

## Ý tưởng trung tâm

Giữ tổng violation budget cố định, nhưng phân phối budget đó giữa các sự kiện
người--bước theo một context score liên tục, giải thích được. Context score không
thay thế xác suất, covariance hay detector confidence. Mô hình điều khiển dùng
trạng thái \([x,y,\theta,v_x,v_y,\omega]\) và phát lệnh vận tốc thân
\([v_x^{\mathrm{cmd}},v_y^{\mathrm{cmd}},\omega^{\mathrm{cmd}}]\). Không yêu cầu
điều khiển mô-men hoặc dòng điện trong thực nghiệm.

Đây không còn là claim “adaptive risk allocation mới”. Prior art 2025--2026 đã
có risk adaptation trực tuyến và learned allocation dưới tổng budget cố định.
Câu hỏi của proposal chỉ còn là liệu một allocator đóng dạng, không cần huấn
luyện, giữ clearance cố định có tạo giá trị nhân quả, OOD, runtime và khả năng
audit đủ mạnh hay không.

## Mục tiêu cụ thể

1. Xây dựng một context score từ các đại lượng quan sát được như khoảng cách, closing speed, time-to-closest-approach, crossing geometry và local density.
2. Thiết kế risk allocator đơn giản, bảo toàn tổng budget và giảm violation allowance cho event có context risk cao, không thay đổi physical clearance.
3. Đánh giá giao diện LSTM có calibration cho hướng, tốc độ và độ hiệu lực ngữ
   cảnh khi điều chỉnh context margin/chance interface, mà không biến LSTM thành
   đóng góp thuật toán; đầu ra phân phối mode/covariance là nhánh mở rộng và
   không phải output của pipeline active.
4. Đánh giá cơ chế qua safety, tracking, feasibility, smoothness và computation
   bằng matched baselines/ablations, gồm uniform, heuristic risk-adaptive và
   learned-risk khi có thể tái lập công bằng.
5. Đánh giá perception/prediction interfaces riêng để tránh quy công nhầm cho controller.

## Các giả thuyết phải có khả năng bị bác bỏ

- **H1 — allocation:** Ở cùng tổng risk budget và clearance, allocator đóng dạng cải thiện safety metrics so với uniform allocation.
- **H2 — trade-off:** Lợi ích safety không đi kèm suy giảm không chấp nhận được về tracking, solver success, fallback hoặc latency.
- **H3 — mechanism:** Khi permute hoặc loại context, lợi ích giảm; khi giữ context nhưng bỏ allocation, lợi ích không còn; hiệu ứng không phải do adaptive clearance.
- **H4 — prediction interface:** Calibration của confidence hướng và cờ hiệu lực
  LSTM làm tăng độ tin cậy của context-triggered margins so với confidence chưa
  calibration, khi giữ nguyên detector, clearance và risk budget.
- **H5 — robustness:** Kết luận giữ chiều hiệu ứng qua scenario, seed, mật độ, occlusion và injected perception error.
- **H6 — nearest methods:** Allocator đóng dạng không thua kém quá margin đã
  khóa về safety và tốt hơn về ít nhất một thuộc tính audit/runtime/OOD so với
  heuristic risk-adaptive và learned-risk gần nhất.

Tất cả H1–H6 hiện là `unknown`; không kế thừa kết luận từ kết quả cũ.

## Phạm vi và các nội dung không tuyên bố là đóng góp

- Trong phạm vi: position-state NMPC với body-velocity command cho robot Mecanum, phân bổ ngân sách cố định theo ngữ cảnh, giao diện vận tốc/hướng LSTM, giao diện đo người, lan truyền bất định, mô phỏng và thực nghiệm theo từng tầng.
- Chỉ là giao diện: detector/YOLO, tracking và kiến trúc LSTM.
- Ngoài phạm vi đóng góp: RL, Transformer, CBF, tính mới của global planner, detector mới hoặc sensor fusion mới.

## Các gói công việc

| WP | Ghi chú/bằng chứng đầu ra | Điều kiện qua cổng |
|---|---|---|
| WP1 | Focused literature audit và ma trận công trình gần nhất | mọi gap/claim có source note, DOI/URL, giới hạn miền tìm kiếm và phản biện novelty nội bộ; không gọi là systematic review |
| WP2 | Ký hiệu, giả thiết, bộ phân bổ và chứng minh đã kiểm tra | không đánh đồng xác suất với ngữ cảnh |
| WP3 | Dataset card, manifest nguồn và kiểm tra leakage | đóng băng split trước khi train |
| WP4 | Train/hiệu chuẩn LSTM và test trên tập đã đóng băng | đủ baseline, calibration và metric bất định |
| WP5 | Benchmark mô phỏng ghép cặp | seed/scenario đăng ký trước; nearest comparator; giữ mọi lần thất bại |
| WP6 | Đánh giá detector trên ảnh web và overlay perception/context | ảnh thật có giấy phép; ma trận nhầm lẫn khi hợp lệ; truy vết hiệu chuẩn; local path chỉ đánh giá trên map |
| WP7 | Nghiên cứu replay/HIL/robot nếu được cho phép | ghi rõ tầng bằng chứng; có phê duyệt an toàn |
| WP8 | Phản biện Q1 và sửa trên Overleaf | không còn blocker nghiêm trọng về luận điểm/chứng minh/bằng chứng |

## Đầu ra dự kiến

- kho tài liệu đã xác minh trong Zotero và ghi chú nguồn trong Obsidian;
- hợp đồng toán học và sổ theo dõi chứng minh;
- dataset/model mới có phiên bản cùng manifest bất biến ngoài vault này;
- bằng chứng thực nghiệm thô và artifact phân tích được lập chỉ mục bằng hash;
- các đoạn claim đã được duyệt mới chuyển sang Overleaf;
- giữ đầy đủ giới hạn và kết quả âm.

## Tiêu chí thành công

Thành công không phải “CCA thắng mọi controller”. Thành công là chỉ ra rõ điều
kiện mà allocator minh bạch tạo hoặc không tạo safety value, định lượng
trade-off, nhận diện failure modes và giới hạn external validity bằng bằng chứng
tái lập. Nếu delta thuật toán không đủ mạnh, đầu ra trung thực là
`PIVOT-EMPIRICAL` hoặc `STOP`, không đổi tên claim để giữ novelty.

## Related notes

[[00_MOC/project-map]] · [[03_Literature/literature-review]] · [[04_Research_Gap/research-gap]]

