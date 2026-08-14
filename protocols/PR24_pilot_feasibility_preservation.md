# PR24 — Pilot feasibility preservation

> **Trạng thái:** `FROZEN-PILOT`; chỉ dùng chẩn đoán phát triển, không phải
> confirmatory study và không được dùng làm bằng chứng paper. Không kế thừa
> số liệu hoặc trace từ bất kỳ pilot cũ nào.

## Câu hỏi pilot

Pilot này tách hai khả năng có thể quan sát trong run mới: solver đánh mất một nghiệm
khả thi do iteration budget, hoặc chance rows thực sự không khả thi. Mỗi run
phải ghi residual của initial guess, residual của nghiệm trả về và nguyên nhân
fallback; không suy ra nguyên nhân từ một kết quả chưa có provenance.

## Hai thay đổi so với baseline pilot

1. Trước mỗi lần tối ưu, đánh giá initial guess bằng cùng objective và toàn bộ
   constraint. Giữ nó trong candidate set nếu residual không quá $10^{-4}$;
   chỉ thay bằng nghiệm solver khi nghiệm mới cũng khả thi và có objective thấp
   hơn. Công thức CCA, dynamics, bounds và risk budget không đổi.
2. Fallback dùng chuyển động tịnh tiến Mecanum theo hướng đẩy ra xa người/vật
   cản và đặt yaw-rate mong muốn bằng 0. Robot holonomic không cần quay thân về
   hướng thoát; yaw damping được ghi như một biến kiểm tra, không phải kết quả
   đã xác nhận.

Mọi strategy dùng cùng hai thay đổi. Pilot dùng map, seed, context score budget và
strategy ladder được đóng băng trước run. Không trộn pilot với bất kỳ artifact
legacy nào.

## Tiêu chí quyết định

- đủ số run đã đăng ký, không xóa failure;
- deterministic nominal solve success phải tăng mà collision không tăng;
- chance strategies chỉ được so allocation khi fallback không còn chi phối;
- báo completion, collision, signed margin, tracking RMSE, solver success,
  fallback rate, deadline miss và P95/P99 latency;
- nếu fallback vẫn vượt 20% hoặc completion vẫn bằng 0, chưa được mở rộng số
  seed và chưa được gọi là evidence;
- Bounded focused audit hiện đã `COMPLETE` cho phạm vi literature/claim logic;
  pilot vẫn chỉ là candidate vì chưa có freeze confirmatory, holdout và kiểm tra
  độc lập.
