---
type: source-note
status: included-provisional
evidence_status: full-text
evidence_level: full-text
citekey: ren2023multimodal
doi: 10.1109/LCSYS.2022.3186269
zotero_uri: zotero://select/library/items/HIY2ZUHQ
verified_date: 2026-08-01
---

# Ren, Ahn và Kamgarpour (2023) — Chance constraint dưới bất định GMM

## Xác minh thư mục

- Nguồn chính: [IEEE Control Systems Letters](https://doi.org/10.1109/LCSYS.2022.3186269).
- Bản đã đọc: [arXiv 2503.06779](https://arxiv.org/abs/2503.06779), trang arXiv
  ghi rõ journal reference, DOI liên quan và giấy phép toàn văn.
- Metadata nhà xuất bản và arXiv đã đối chiếu ngày 01/08/2026; Zotero item/PDF
  đã nhập và kiểm; correction/retraction và provenance cuối vẫn cần kiểm độc
  lập trong focused audit.

## Bài toán và cơ chế

Bài báo dùng Gaussian mixture model cho trạng thái tương lai đa mode của chướng
ngại vật, rồi xây dựng xấp xỉ mixed-integer conic cho chance-constrained
trajectory planning. Với moment GMM ước lượng từ mẫu hữu hạn, bài đưa cận tập
trung để robustify mean/covariance và diễn giải confidence của nghiệm; một nhánh
CVaR được dùng để giới hạn mức độ vi phạm thay vì chỉ tần suất vi phạm.

Bằng chứng dùng predictor quỹ đạo hiện đại và dữ liệu lái xe thật, nhưng bài toán
 là hệ tuyến tính/chướng ngại vật đa diện, không phải position-state Mecanum NMPC
với lệnh vận tốc thân và
không dùng context xã hội để phân phối total budget.

## Phản bằng chứng đối với dự án

Nguồn này chiếm phát biểu rộng rằng đưa dự báo đa mode vào chance-constrained
planning hoặc xử lý moment ước lượng hữu hạn là mới. Nó còn đặt chuẩn cao hơn
Gaussian surrogate chưa calibration của dự án:

- phải tách confidence do ước lượng moment khỏi collision allowance;
- phải giữ mọi mode và ghi rõ phép accounting joint theo obstacle--horizon;
- không được suy cận dưới mô hình sang $\Pr_\star$ nếu thiếu independent
  one-sided calibration và tail support;
- comparator/giới hạn phải thừa nhận mixed-integer conic và CVaR là các lựa chọn
  mạnh hơn nhưng tốn tính toán hơn.

## Vị trí kiểm chứng

- Sec. 2.3, Theorem 1: deterministic reformulation và concentration bounds;
- Sec. 3, Theorem 2: trajectory-level chance accounting với moment ước lượng;
- Sec. 4: nuScenes/predictor case studies và so sánh chance--CVaR;
- phần conclusion: phạm vi tuyến tính, đa diện và hướng mở rộng.

## Liên kết

- [[03_Literature/source-index]]
- [[03_Literature/nearest-work-matrix]]
- [[03_Literature/literature-synthesis]]
- [[05_Theory/assumptions]]

Related hub: [[00_MOC/project-map]]

