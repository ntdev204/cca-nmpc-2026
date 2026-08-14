# PR01 — Archived literature-search plan

> **ARCHIVED — NOT AN ACTIVE GATE.** This file is retained for historical
> provenance only. The current work is one original research paper, so it does
> not require an SLR/PRISMA workflow or Scopus, Web of Science or IEEE Xplore
> database export. Use `research/metadata/focused_literature_audit.json` and the
> linked Zotero/Obsidian notes for the active literature condition.

> **Trạng thái:** `ARCHIVED — NOT AN ACTIVE GATE`; triage/full-text
> nearest-work của workflow cũ được giữ để truy vết, nhưng search database tái
> lập, screening ledger, collection/tag audit, snowballing hai vòng,
> correction/retraction check và review độc lập của SLR **không được tiếp tục**
> trong scope bài báo nghiên cứu gốc hiện tại. Active literature work dùng
> focused audit trong Zotero/Obsidian theo
> `research/obsidian/03_Literature/literature-review.md`.
> **Mục tiêu lịch sử:** ghi lại thiết kế SLR cũ để bảo toàn provenance; không
> dùng làm kế hoạch thực thi hoặc cổng nghiệm thu cho bài báo hiện tại.

## 1. Câu hỏi tổng quan

- **LRQ-01:** Continuous/context-aware adaptation đã được đưa vào MPC/NMPC cho
  robot di động quanh người theo cách nào?
- **LRQ-02:** Chance-constrained hoặc uncertainty-aware NMPC dùng dự báo chuyển
  động người, calibration và risk allocation ra sao?
- **LRQ-03:** LSTM trajectory prediction được đánh giá với split, OOD,
  uncertainty và closed-loop effect như thế nào?
- **LRQ-04:** Torque-input Mecanum NMPC đã xử lý actuator, feasibility, stability
  và computation đến mức nào?
- **LRQ-05:** Benchmark nào đủ gần để bác bỏ hoặc thu hẹp novelty dự kiến ở PR00?
- **LRQ-06:** Allocator đóng dạng/không huấn luyện còn tạo delta khoa học nào so
  với heuristic risk-adaptive CVaR và learned fixed-total allocation?
- **LRQ-07:** Elastic/adaptive chance levels và perception-aware MPC đã có những
  điều kiện closed-loop constraint satisfaction, recursive feasibility và
  stability nào mà proof budget đơn giản của dự án không hỗ trợ?

## 2. Tiền đăng ký tìm kiếm

Trước lần search chính thức, khóa vào `search_manifest`:

- ngày bắt đầu/kết thúc search và ngày cập nhật cuối;
- cơ sở dữ liệu được tiền đăng ký gồm Web of Science Core Collection, Scopus,
  IEEE Xplore, Crossref và Semantic Scholar Academic Graph; Google Scholar chỉ
  dùng snowballing. Sau kiểm tra UI trước lần search chính thức, tài khoản cá
  nhân không có entitlement cho WoS Core Collection và Scopus document search;
  hai nguồn này giữ exact query ở trạng thái `access-blocked` để chạy bổ sung
  khi có institutional access, không được tính là đã search;
- publication year từ 2010 đến hết ngày khóa search 2026-08-01. Mốc 2010 bao
  phủ giai đoạn MPC/NMPC xác suất và dự báo người hiện đại; bài nền tảng cũ hơn
  được thêm bằng backward snowballing và ghi lý do, không trộn vào database-flow
  count;
- trường tìm kiếm, ngôn ngữ, document type và exact query cho từng database;
- người screening, cách giải quyết bất đồng và phần mềm/phiên bản export.

Chuỗi tìm kiếm lõi được dịch đúng cú pháp từng database, không đổi khái niệm:

```text
("nonlinear model predictive control" OR NMPC OR MPC)
AND ("context aware" OR "continuous context" OR "human aware" OR social)
AND (robot* OR mobile OR mecanum)

(chance-constrain* OR "risk allocation" OR probabilistic OR uncertainty)
AND (NMPC OR MPC) AND (human OR pedestrian OR trajectory)

("adaptive risk" OR "risk adaptation" OR "risk allocation")
AND (context* OR threat OR feasibility OR learned)
AND (MPC OR NMPC OR CVaR OR "barrier function")

("elastic chance constraint" OR "adaptive probability level"
 OR "online risk value" OR "perception-aware chance-constrained")
AND (MPC OR SMPC) AND (feasibility OR stability OR "closed loop")

(LSTM OR "recurrent neural network") AND (pedestrian OR human)
AND (trajectory prediction OR motion prediction)
AND (uncertainty OR calibration OR covariance OR multimodal)
```

Một nhánh riêng dùng `(mecanum OR omnidirectional) AND (torque OR dynamic*) AND
(NMPC OR MPC)` để tránh gap giả do query đầu quá hẹp.

Manifest máy đọc được `research/metadata/pr01_search_manifest.json` khóa trước
lần search chính thức: 5 database, 6 concept block, 30 exact query, trường tìm
kiếm, filter, định dạng export, reviewer và quy tắc re-screen. IEEE Xplore,
Crossref và Semantic Scholar là ba nguồn bắt buộc trong execution hiện tại;
Scopus/WoS bị chặn quyền vẫn được giữ để audit giới hạn và chạy bổ sung. Crossref
không hỗ trợ cùng ngữ nghĩa Boolean/field như cơ sở dữ liệu chuyên ngành, nên
exact query của nó được khai báo là `query.bibliographic` và chỉ đóng vai trò
recall supplement xếp hạng. Mỗi query Crossref chỉ xuất 1.000 kết quả đầu theo
thứ tự relevance mặc định đã khóa; manifest vẫn giữ tổng hit do API báo và không
gọi phần export này là toàn bộ tập hit. Semantic Scholar bulk search dùng Boolean
title/abstract, lọc date/type và token pagination đến khi không còn continuation
token; trường `total` của API được ghi là ước lượng chứ không ép bằng số record
đã xuất. Projection metadata được khóa ngay trong exact query gồm `paperId`,
`title`, `abstract`, `authors`, `year`, `publicationDate`, `venue`, `externalIds`,
`publicationTypes`, `url` và `openAccessPdf`; runner không được âm thầm thêm hoặc
bớt trường. Hai nguồn mở không được dùng để tuyên bố rằng Scopus hoặc Web of
Science đã được thay thế tương đương.

## 3. Zotero là nguồn thư mục chính thức

Tạo collection có cấu trúc:

```text
CCA-Q1/
  00_Inbox
  01_Included_Core
  02_Nearest_Prior_Art
  03_Theory_Control
  04_Human_Prediction
  05_Experiments_Datasets
  06_Excluded_FullText
```

Trạng thái ngày 2026-08-01: thư viện dự án đã có 32 top-level items và 32 PDF,
không thiếu child attachment, không có nhóm DOI chuẩn hóa trùng và không thiếu
title/DOI/creator/date. Export portable và receipt nằm tại
`references/zotero/export/`. Manifest khóa SHA-256 của đủ 32 PDF; tuy nhiên 27
PDF kế thừa còn thiếu URL/thời điểm tải gốc và được ghi fail-closed là
`legacy-origin-unresolved`, không phải provenance đã xác minh. Connector cục bộ
đã nhập item/PDF, nhưng cây
collection phía trên chưa được tạo vì công cụ điều khiển UI chưa giữ được phiên
cửa sổ Zotero; đây vẫn là cổng mở cần kiểm bằng UI, không được suy thành PR01 đã
hoàn tất.

Mỗi item cần DOI/URL, venue, year, abstract, PDF nếu quyền cho phép, citation
key ổn định, tag `screen:*`, `role:*`, `evidence:*`, và note exclusion nếu bị
loại ở full text. Metadata được kiểm bằng trang publisher/DOI; không nhập một
reference chỉ từ citation của bài khác. Export BibTeX từ collection included là
nguồn duy nhất đồng bộ sang Overleaf.

Không thay citation key sau khi đã dùng trong Obsidian/Overleaf nếu không có
mapping migration được ghi log.

## 4. Screening và eligibility

### Inclusion

- peer-reviewed full paper có phương pháp hoặc bằng chứng trực tiếp cho một LRQ;
- mô tả đủ mô hình/thuật toán/dataset/experiment để mã hóa;
- ứng dụng robotics/control/human trajectory liên quan trực tiếp, hoặc là bài
  nền tảng về proof/calibration cần thiết;
- ngôn ngữ có thể được nhóm đọc và kiểm chứng.

### Exclusion

- abstract-only, poster, slide, patent, marketing hoặc bản trùng;
- chỉ nhắc “context-aware” nhưng không định nghĩa hoặc không dùng trong control;
- prediction paper không có đánh giá trajectory hoặc không thể xác định split;
- controller dùng ground-truth future mà không công bố, nếu được dùng làm bằng
  chứng thực tế;
- bài không lấy được full text sau quy trình truy cập hợp lệ; lý do vẫn được lưu.

Hai người screening độc lập là ưu tiên. Nếu chỉ có một người, phải re-screen
blinded ít nhất 20% theo mẫu phân tầng sau khoảng nghỉ và báo agreement; đây là
giới hạn, không được mô tả như dual review.

## 5. Luồng dữ liệu và chống cherry-pick

1. Export toàn bộ kết quả query ở dạng RIS/BibTeX/CSV và hash raw export.
2. Deduplicate bằng DOI, title chuẩn hóa và kiểm tra thủ công near-duplicate.
3. Screen title/abstract; giữ quyết định và lý do.
4. Screen full text; dùng reason code cố định.
5. Backward/forward snowballing cho mọi nearest-prior-art candidate.
6. Cập nhật search một lần ngay trước freeze bản thảo.
7. Tạo flow table kiểu PRISMA: found, deduplicated, screened, excluded, included.

Không xóa record bị loại khỏi evidence ledger. Không thay query để loại một
nhóm bài bất lợi mà không lưu query/version cũ.

## 6. Biểu mẫu trích xuất

| Nhóm trường | Nội dung bắt buộc |
|---|---|
| Bibliographic | Zotero key, DOI, venue/quartile theo năm và ngày kiểm tra |
| Problem | Robot, environment, người, sensor, control objective |
| Method | Dynamics/input, horizon, predictor, uncertainty, context definition |
| Theory | Assumptions, theorem, feasibility/stability/safety scope |
| Data | Synthetic/real, source, size, split unit, leakage/OOD |
| Experiment | Sim/hardware, baseline, ablation, trials/seeds, compute budget |
| Metrics | Safety, task, tracking, runtime, prediction, qualitative/statistics |
| Reproducibility | Code/data/config availability và artifact traceability |
| Limitations | Failure, negative result, external-validity boundary |

Một extractor điền; một reviewer audit toàn bộ nearest prior art và mẫu ngẫu
nhiên ít nhất 20% phần còn lại. Bất đồng được giải quyết trước khi tổng hợp gap.

## 7. Ma trận nearest prior art và kiểm tra gap

Mỗi candidate gần nhất có một dòng:

| Zotero key | CCA liên tục | Risk budget matched | Human--step allocation | Learned/closed-form | Clearance fixed | LSTM + calibrated uncertainty | Torque Mecanum | Proof | Paired closed-loop | Real robot | Khác biệt còn lại |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|

Research gap chỉ được giữ nếu:

1. không phải hậu quả của query hẹp hoặc thuật ngữ khác;
2. ít nhất ba bài gần nhất đã được đọc full text và snowball;
3. khác biệt là một cơ chế có thể falsify bằng ablation, không chỉ “chưa ai ghép”;
4. khoảng trống có ý nghĩa đối với safety/progress/robustness, không chỉ hình thức;
5. protocol PR20--PR30 thực sự có thể kiểm tra nó.

Mệnh đề “first” chỉ được dùng khi search đủ rộng và vẫn phải kèm ngày/miền tìm
kiếm. Mặc định dùng câu hẹp hơn: “chúng tôi chưa tìm thấy nghiên cứu nào đồng
thời kiểm tra X dưới hợp đồng Y”.

## 8. Tổng hợp cho proposal, gap và bài báo

Obsidian lưu một note cho mỗi bài theo template thống nhất, liên kết Zotero key,
LRQ và claim ID. Các note tổng hợp tạo:

- taxonomy của context, uncertainty, risk allocation và validation;
- bảng so sánh nearest prior art;
- danh sách contradiction/negative evidence;
- gap statement một đoạn, scope exclusions và testable novelty;
- danh sách baseline/metric/proof obligation chuyển sang PR02, PR12, PR21.

Overleaf chỉ nhận narrative và bảng đã trace tới extraction ledger. Không copy
đoạn văn từ abstract; trích dẫn ngắn tuân thủ bản quyền và cần kiểm tra trực tiếp.

## 9. Cổng chấp nhận lịch sử (không áp dụng cho scope hiện tại)

PR01 đạt `VERIFIED` khi raw search/export có hash, decision ledger đầy đủ, update
search hoàn tất, nearest-prior-art matrix được audit, mọi claim novelty trong
PR00 có ít nhất một đoạn evidence map, và không còn citation trong Overleaf thiếu
Zotero item/metadata đã kiểm. Cổng phải ghi một trong ba quyết định `GO-ALGORITHM`,
`PIVOT-EMPIRICAL` hoặc `STOP`, kèm lý do và người review. Nếu gap không sống,
PR00 phải thu hẹp trước khi tiếp tục; không được thiết kế experiment để cứu một
novelty đã bị bác bỏ.

### Bản ghi cổng máy đọc được

Trong scope comprehensive cũ, trước mọi confirmatory run, `protocol-freeze-manifest` phải chứa
`research_gap_gate` với `status: VERIFIED`; hash của PR01; hash decision record;
manifest của raw database exports; Zotero export và receipt đã hash trực tiếp;
nearest-work matrix; quyết định;
người/role review; thời điểm và lý do. Chỉ `GO-ALGORITHM` hoặc
`PIVOT-EMPIRICAL` được phép mở run. `STOP` vẫn phải được lưu như một quyết định
khoa học, nhưng không thể tạo freeze manifest cho confirmatory experiment.

Đối với scope comprehensive cũ, một ghi chú Markdown, số lượng bài tự khai hoặc
web-search triage không thay thế raw export từ các cơ sở dữ liệu đã tiền đăng ký.
Trong scope đó, thiếu bất kỳ hash/record nào sẽ giữ PR01 ở `IN-PROGRESS` và các
schema experiment phải từ chối trạng thái `running`/`completed`. Quy tắc này chỉ
là hồ sơ lịch sử; theo amendment ngày 2026-08-12, PR01 hiện tại là
`ARCHIVED — NOT AN ACTIVE GATE`, không chặn pipeline bài báo nghiên cứu gốc.
