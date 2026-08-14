---
type: limitations
status: active
evidence_status: unknown
---

# Sổ đăng ký giới hạn

| ID | Giới hạn/rủi ro | Hệ quả | Biện pháp dự kiến | Trạng thái |
|---|---|---|---|---|
| L-001 | Bằng chứng hiện tại thuộc loại legacy hoặc chưa xác định. | Không được sử dụng bất kỳ tuyên bố định lượng nào. | Xây dựng lại dataset và chạy lại các protocol. | mở |
| L-002 | Điểm ngữ cảnh có thể chứa trọng số mang tính chủ quan. | Phát sinh vấn đề về độ nhạy và công bằng. | Định nghĩa biến quan sát; đăng ký trước trọng số; phân tích độ nhạy. | mở |
| L-003 | Cận Boole có thể bảo thủ. | Chi phí bám quỹ đạo/thời gian tính có thể tăng. | Báo cáo slack và ablation về mức sử dụng ngân sách. | mở |
| L-004 | Phân phối LSTM có thể mất hiệu chuẩn khi lệch miền; radial/top-mode 95% coverage không kiểm đuôi one-sided ở allowance khoảng 0.0025 hoặc floor $10^{-4}$. | Chance constraint có thể quá tự tin dù metric pooled đẹp. | Calibration split độc lập; projected one-sided residual cho mọi mode/horizon/context, ID/OOD; exact tail CI và sample-support audit. | mở |
| L-005 | Lỗi detector lan truyền xuống controller. | Bỏ sót hoặc báo nhầm người làm thay đổi phân bổ rủi ro. | Ma trận nhầm lẫn khi đúng loại bài toán, quét ngưỡng confidence và nghiên cứu bơm lỗi. | mở |
| L-006 | Mô phỏng có thể không phản ánh va chạm, độ trễ hoặc nhiễu cảm biến. | Giá trị ngoại suy yếu. | Phân tầng bằng chứng simulation - replay - hardware và ghi nhãn riêng. | mở |
| L-007 | Lỗi solver/fallback có thể chi phối kết quả. | Lợi ích an toàn có thể đến từ phanh fallback, không phải CCA. | Ghi solver status/fallback; ablation chuyên biệt. | mở |
| L-008 | Ảnh Internet có thể mất cân bằng giấy phép/miền. | Rủi ro tái lập và đạo đức. | Sổ nguồn gốc, giấy phép cho phép, khử trùng lặp và báo cáo theo nhóm. | mở |
| L-009 | Nearest work đã có context-aware fixed-total risk adaptation. | Delta đóng dạng/human--step có thể chỉ là gia tăng, không đủ novelty Q1. | Hoàn tất focused audit và review độc lập trước khi chốt novelty; nếu cần, giữ `PIVOT-EMPIRICAL`. | mở |
| L-010 | Code/data của learned-risk gần nhất có thể chưa công khai hoặc dùng oracle uncertainty. | Comparator trực tiếp có thể không tái lập công bằng. | Liên hệ/tìm artifact hợp lệ; nếu không, tái lập tối thiểu có audit và báo sai khác, không hạ comparator để tạo ưu thế giả. | mở |
| L-011 | Prior art 2024--2026 đã có adaptive risk values và perception-aware chance-constrained MPC với recursive-feasibility/stability conditions. | T1--T5 của dự án chỉ là contract propositions; chúng không hỗ trợ novelty hoặc claim closed-loop. | Giữ CLM-T-01/02/04 ở phạm vi algebra/model-internal/open-loop; CLM-T-03 withdrawn; trung tâm là empirical characterization sau focused audit. | mở |
| L-012 | `probability_claim_eligible` vẫn không thể thay thế bằng chứng vận hành độc lập. | Một boolean có thể admission claim xác suất sai nếu thiếu provenance. | Implementation hiện fail-closed: bắt buộc SHA-256 calibration, domain, tail coverage, frame/time/age, mode partition, covariance provenance và geometry containment; solver vẫn phải không slack/vi phạm. | mitigated-in-code; evidence open |
| L-013 | Mô hình sáu trạng thái chưa biểu diễn tường minh velocity-command lag, command delay và previous body-velocity command; miền $w_k$ chưa bị chặn/validated. | Shifted-candidate hoặc Lyapunov proof danh định không áp dụng cho controller thật. | Giữ PO-005/006 held, chỉ báo solve/fallback/tracking thực nghiệm; muốn mở lại phải amendment augmented model + identification. | mở |
| L-014 | $d_{\mathrm{req},em}$, chiều half-space và ellipse support chưa có geometry/implementation parity evidence; MATLAB PSD validation cũng đang chờ bằng chứng mới. | Cận half-space có thể không chứa collision event hoặc dùng covariance không hợp lệ. | Đóng PO-001/013 bằng geometry parity, frame/sign test và PSD/provenance audit trước mọi collision-probability claim. | mở |
| L-015 | MATLAB bounded profile rút ngắn thời gian nên settling-time không xác định; `fmincon` NMPC trên host có P95 lớn hơn deadline 50 ms. | Các bounded package cũ đã bị purge; chúng không thể đóng Gate-A, không hỗ trợ real-time claim hoặc thay thế Python confirmatory benchmark. | Giữ kết luận ở mức design-only; tối ưu solver/đo target hardware riêng rồi chạy full profile từ run ID mới sau protocol freeze. | mở |
| L-016 | Screening refresh 2026-08-13 thêm interactive crowd MPC, learned GP uncertainty và risk-aware MPPI prior art. | Interaction, learned uncertainty và sampling control phải được xem là comparator boundaries; baseline yếu có thể làm sai trade-off CCA. | Đọc/nhập Zotero khi API hoạt động; kiểm fair implementation, compute budget và failure accounting trước confirmatory benchmark. | mở |

Cập nhật ghi chú này mỗi khi một kết quả được chấp nhận làm bằng chứng. Giới hạn là một phần của kết quả, không phải phần bổ sung mang tính thủ tục ở cuối bài.

## Related notes

[[00_MOC/project-map]] · [[01_Governance/research-charter]] · [[01_Governance/status-and-provenance]]

