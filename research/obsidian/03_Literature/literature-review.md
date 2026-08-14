---
type: literature-protocol
status: focused-audit-complete-bounded
evidence_status: zotero-focused; no-database-export-required; final-citation-reconciliation-open
inheritance: legacy-hypothesis-reverify
---

# Protocol tổng quan tài liệu

## Quyết định phạm vi — 2026-08-12

Đây là bài báo nghiên cứu gốc, không phải bài systematic review. Vì vậy không
thực hiện PR01-SLR, không cần tài khoản Scopus, Web of Science hoặc IEEE Xplore,
và không dùng PRISMA flow để mô tả mức bao phủ. Các file `PR01_*` và những
candidate export hiện có được giữ như hồ sơ audit lịch sử, không phải bằng chứng
đã hoàn tất và không được dùng để chặn code, mô phỏng hoặc thực nghiệm.

Workflow đang dùng là focused literature audit: chọn các công trình gần nhất có
DOI/toàn văn, kiểm metadata trong Zotero, ghi source note có liên kết, điền
nearest-work matrix và thu hẹp research gap thành mệnh đề có thể kiểm chứng.
Mọi claim phải chỉ rõ nguồn và giới hạn miền tìm kiếm; không dùng các cụm
“systematic search”, “PRISMA” hoặc “exhaustive database coverage”.

The bounded audit was reviewed on 2026-08-13. Remaining Zotero attachment,
collection/tag, correction/retraction and independent-review checks are release
and citation-promotion gates; they do not reopen PR01 or block the next dataset
and simulation design steps. See [[07_Analysis/focused-audit-review-20260813]].

### Definition of done cho focused audit

- mỗi câu gap có ít nhất một source note và một dòng trong nearest-work matrix;
- các công trình gần nhất được đọc đủ phương pháp, giả thiết và bằng chứng;
- baseline/ablation/metric cần kiểm tra được liên kết sang protocol tương ứng;
- citation metadata, DOI/URL và trạng thái full text được Zotero kiểm tra;
- narrative được viết theo phạm vi thực tế, kể cả prior art bất lợi và giới hạn.

### Quy tắc refresh Google và Google Scholar

Trong giai đoạn nghiên cứu đang hoạt động, thực hiện một lượt tìm kiếm Google
và Google Scholar-oriented trước mỗi thay đổi về research gap, mô hình, baseline,
metric hoặc protocol; tối thiểu lặp lại mỗi tuần và một lần ngay trước khi
đóng evidence freeze. Mỗi lượt phải lưu ngày giờ, exact query, bộ lọc năm/chủ đề,
URL kết quả và trạng thái kiểm tra vào [[03_Literature/web-verified-gap-sources]]
hoặc source note tương ứng.

Google/Google Scholar chỉ là lớp discovery. Không dùng snippet, số trích dẫn,
hoặc tiêu đề tìm kiếm làm bằng chứng; phải mở DOI, trang nhà xuất bản,
proceedings hoặc bản arXiv chính thức để kiểm tra tác giả, phiên bản, venue,
correction/retraction và nội dung phương pháp. Nếu Google Scholar không mở được
hoặc không có quyền truy cập, ghi rõ giới hạn đó và không gọi lượt tìm kiếm là
bao phủ Scholar/Scopus/WoS/IEEE. Công trình mới chỉ được đưa vào nearest-work
matrix sau khi metadata và mức bằng chứng đã được Zotero/Obsidian đối chiếu.

## Câu hỏi tổng quan

Trong điều hướng robot quanh người, công trình nào đã dùng context để điều chỉnh
MPC/NMPC, công trình nào phân bổ chance-risk budget, và có công trình nào dùng
context liên tục để tái phân bổ một fixed budget trong NMPC đối sánh hay chưa?
Sau khi claim rộng đã bị bác, câu hỏi bổ sung là allocator đóng dạng/không huấn
luyện còn khác gì có ý nghĩa so với risk-adaptive CVaR và learned fixed-total
allocation gần nhất.

## Chủ đề tổng hợp và đánh giá

1. MPC/NMPC human-aware, social hoặc context-aware;
2. chance constraint, joint risk và risk allocation;
3. dự báo quỹ đạo người học được/đa mode ghép với điều khiển;
4. hiệu chuẩn bất định và distribution shift;
5. NMPC Mecanum động lực học/điều khiển mô-men;
6. safety supervisor, fallback và lỗi solver;
7. đánh giá detector/tracker như giao diện đo;
8. bằng chứng real-time NMPC và chuẩn báo cáo.
9. pose/keypoint người như tín hiệu cho dự báo quỹ đạo và context;
10. biểu diễn tự giám sát và safe RL ghép với MPC/NMPC.

## Chuỗi truy vấn lịch sử (không phải workflow active)

```text
("context-aware" OR "human-aware" OR social OR interaction-aware)
AND (MPC OR NMPC) AND (human OR pedestrian OR crowd)

("risk allocation" OR "joint chance constraint" OR "chance-constrained")
AND (MPC OR NMPC) AND (collision OR navigation)

("adaptive risk" OR "risk adaptation" OR "risk level")
AND (context OR threat OR feasibility OR learned)
AND (MPC OR NMPC OR CVaR OR "barrier function")

(trajectory prediction OR multimodal prediction OR LSTM)
AND (calibration OR uncertainty OR covariance)
AND (robot navigation OR predictive control)

(Mecanum OR omnidirectional OR Swedish wheel)
AND (dynamic model OR torque OR NMPC OR MPC)

(human pose OR keypoint OR skeleton)
AND (trajectory prediction OR intention OR robot navigation)

(self-supervised OR unsupervised representation OR reinforcement learning)
AND (human-aware navigation OR dynamic human environment)
AND (MPC OR NMPC OR safety filter)
```

Năm khối trên là truy vấn lịch sử, không phải yêu cầu active. Nguồn máy đọc được
`research/metadata/pr01_search_manifest.json` đã khóa sáu khối khái niệm theo
cú pháp của từng nguồn, tổng cộng 30 exact query; không được thay một query đã
khóa mà không có amendment trước execution.

## Hồ sơ PR01 lịch sử — nguồn và mốc dừng

- Năm nguồn tiền đăng ký là Web of Science Core Collection, Scopus, IEEE Xplore,
  Crossref và Semantic Scholar; Google Scholar chỉ dùng snowballing.
- Kiểm tra UI trước execution xác nhận tài khoản cá nhân đã đăng nhập nhưng không
  có entitlement cho WoS Core Collection và Scopus document search. Hai nguồn
  này giữ nguyên exact query ở trạng thái `access-blocked`, không được tính là đã
  tìm và sẽ chạy bổ sung nếu có institutional access.
- Vòng execution của PR01 lịch sử từng yêu cầu đủ 18 truy vấn trên IEEE Xplore, Crossref và
  Semantic Scholar. Hai nguồn mở là recall supplement, không được mô tả như bản
  thay thế tương đương cho WoS/Scopus.
- Ưu tiên toàn văn đã phản biện có DOI; ghi preprint riêng.
- Publication year là 2010--2026, cutoff 2026-08-01; bài nền tảng cũ hơn chỉ vào
  qua backward snowballing có lý do. Chỉ đặt mốc dừng khi thực thi và ghi chính
  xác database/truy vấn/ngày.
- Snowballing xuôi/ngược đến khi hai vòng liên tiếp không thêm nguồn làm đổi gap, baseline hoặc ranh giới claim.

## Quy tắc active của focused audit

Không có database bắt buộc hoặc tài khoản thuê bao. Mỗi nguồn active phải có
Zotero key, DOI hoặc URL nhà xuất bản/arXiv, source note liên kết, và ghi rõ
phương pháp, giả thiết, comparator, bằng chứng cùng giới hạn. Mốc dừng là khi
không còn nguồn gần nhất làm thay đổi gap, comparator hoặc claim boundary trong
vòng đọc có mục tiêu; đây không phải tiêu chí bao phủ toàn bộ cơ sở dữ liệu.

## Zotero live checkpoint (2026-08-11)

The local Zotero API is reachable and the live metadata export contains 43
entries. Eleven items were added after the previous 32-entry portable receipt;
they are listed with citation keys and provenance limits in
[[03_Literature/zotero-live-inventory]]. The live export has not
replaced the frozen `library.bib`, because the new records have not yet passed
the attachment/provenance reconciliation.

The new records strengthen the negative audit of broad novelty claims: pose-aware
prediction, safe RL with chance-constrained MPC, unsupervised navigation
representations, online risk adaptation, elastic chance constraints and the
YOLO26 tool itself are all represented. They should refine the gap and baseline
set, not be presented as a database-coverage count.

A limited primary-source landing-page check is recorded in
[[03_Literature/web-verified-gap-sources]]. It is an audit aid, not a
substitute for full-text extraction or final citation admission.

The live Zotero inventory was rechecked on 2026-08-13 and still contains 43
items. Read-only title searches for the two newly screened 2026 learning/control
records returned no local match; they remain web-linked screening records and
were not imported into the frozen export.

## Hồ sơ PR01 lịch sử — open-retrieval attempt — 2026-08-12

The frozen open-source runner was executed with the unchanged historical PR01 manifest.
The candidate bundle
`references/literature/staging/pr01-open-20260812T030839067560Z/` contains one
complete ranked-cap Crossref query (1,000 records; source-reported hit count
543,064) and remains `IN-PROGRESS` because the next network request did not
finish before the 304 s execution limit. The bundle SHA-256 is
`A95651131062BE79230EBFB1FE5439D691E4866683A96A2827374FA4C3C03131`; the
completed raw part SHA-256 is
`337F419005CBCAB2B358E3DFA026B09144C9AD48E4F3520D4D5ADDAC04775EC7`.

This is a candidate retrieval artifact, not a completed database export. It
does not alter the canonical raw-export manifest or the PR01 decision, and it
cannot be used for PRISMA counts, novelty acceptance or manuscript citations.

## Hồ sơ PR01 lịch sử — IEEE Xplore export check — 2026-08-12

The public IEEE Xplore Command Search page accepted the frozen historical
`qry-ieee-xplore-context-human-nmpc` expression and displayed **227 results**.
The content-type facet controls could be selected, but the result total stayed
at 227, so a filtered journal/conference export was not certified. Selecting
`Export` opened a `Download Results` dialog that required an IEEE personal
sign-in; no CSV was downloaded and no local file was created. This is direct
evidence that the search page is reachable, not evidence that the IEEE database
export gate is complete. The remaining five IEEE queries are therefore not
marked executed. The historical raw-export record remains incomplete, while
the PR01 protocol itself is now `ARCHIVED — NOT AN ACTIVE GATE`.

A second open-source execution attempt started at `2026-08-12T04:02:20Z` with
the unchanged manifest and was stopped after the first network request remained
unresponsive for more than two minutes. The candidate bundle
`references/literature/staging/pr01-open-20260812T040220529472Z/bundle.json`
has SHA-256
`F5DD83575167268EB6F31FC3D407C225F922D947501082FCA12322FBCF53B78E`, zero
completed executions, and status `IN-PROGRESS`. It is retained only as an audit
record; it does not change the canonical raw-export manifest or PR01 decision.

A later connectivity probe reached both public endpoints, but a repeated
Crossref ranked-cap request was throttled with HTTP 429 after an earlier
response had completed. This probe is not an execution, does not amend the
frozen query, and cannot promote PR01.

## Tiêu chí nhận

- Trực tiếp thông tin cho câu hỏi nghiên cứu, comparator, giả thiết, chỉ số hoặc giới hạn.
- Có thể kiểm tra phương pháp và bằng chứng vượt quá search snippet.
- Muốn xác lập prior art sở hữu novelty phải đọc toàn văn.
- Với claim định lượng, phải trích được quần thể/scenario, chỉ số và thiết lập thực nghiệm.

## Tiêu chí loại

- Trùng từ khóa nhưng phương pháp không liên quan.
- Blog/trang nhà cung cấp dùng làm bằng chứng novelty học thuật.
- Không có toàn văn nhưng dùng cho claim chi tiết.
- Công trình bị rút/sửa mà không ghi trạng thái rõ.
- Thêm nguồn chỉ để tăng số tài liệu tham khảo.
- Dùng benchmark hoặc số liệu của nhà cung cấp như kết quả của hệ thống hiện tại.

## Amendment định hướng ngày 2026-08-11

Theo quyết định dùng `yolo26s-pose.pt`, vòng đọc mới tách ba câu hỏi:

1. YOLO26s-pose cung cấp hộp người, 17 keypoint và confidence như thế nào;
2. pose/keypoint đã được dùng ra sao để cải thiện dự báo quỹ đạo người;
3. học không giám sát/tự giám sát hoặc RL có thể tối ưu từng tầng mà vẫn giữ
   NMPC là tầng thực thi ràng buộc.

Nguồn kỹ thuật YOLO26 chỉ xác lập giao diện và protocol đánh giá, không xác lập
novelty. Salzmann et al. đã chứng minh pose/head orientation có thể đi vào dự
báo quỹ đạo trên robot; NavRep đã ghép biểu diễn không giám sát với RL trong
điều hướng có người; Pfrommer et al. đã ghép safe RL với chance-constrained
MPC. Vì vậy, các cụm “YOLO pose + LSTM”, “unsupervised navigation” và “RL +
chance-MPC” đều là prior art, không phải claim mới độc lập. Tổng hợp chi tiết:
[[03_Literature/pose-learning-gap]].

## Bản ghi focused audit

Với mỗi nguồn được dùng, ghi Zotero key, DOI hoặc URL có thẩm quyền, trạng thái
toàn văn, phương pháp, giả thiết, comparator, bằng chứng và giới hạn trong source
note liên kết. Không lập flow hoặc số đếm PRISMA; phạm vi tìm kiếm được mô tả
trung thực là có mục tiêu và không exhaustive.

## Trường đánh giá chất lượng

- giả thiết mô hình và bất định;
- định nghĩa context và vị trí đi vào điều khiển;
- semantics rủi ro và phạm vi bảo đảm;
- provenance/hiệu chuẩn predictor và dữ liệu;
- tính công bằng comparator và chất lượng ablation;
- thiết lập mô phỏng/robot và cỡ mẫu;
- xử lý thất bại và bằng chứng timing;
- giới hạn liên quan tới CCA-NMPC.

## Đầu ra

Mỗi nguồn được nhận có một [[09_Templates/source-note-template]]. Chỉ viết kết
luận xuyên bài tại [[03_Literature/literature-synthesis]]. Zotero là nguồn chuẩn cho
metadata; kho này lưu lập luận và bằng chứng cấp trang.

Related hub: [[00_MOC/project-map]]

