# PR10 — Thu thập dữ liệu ảnh/video người từ Internet

> **Trạng thái goal hiện tại:** `DEFERRED — OUTSIDE CURRENT GOAL`.  
> **Trạng thái lưu vết:** `CANDIDATE ACQUIRED (ADMISSION BLOCKED)`; diagnostic YOLO
> cũ đã được purge trước khi chạy lại ngày 2026-08-14. Cohort mới gồm bảy ảnh
> thật hiện tồn tại dưới `data/raw/web-cohort-20260814/`; tất cả vẫn là
> candidate và chưa có asset nào được admit làm evidence.
> **Phạm vi:** person detection/tracking, không nhận dạng danh tính hoặc khuôn mặt.

## 1. Mục tiêu

Tạo một tập kiểm tra perception có người thật **đã tải từ Internet** để đánh giá detector
suy ra context cho LSTM/CCA-NMPC sau tracking. Ảnh tự vẽ, ảnh
sinh bằng AI, ảnh render simulator và frame tạo bằng code không hợp lệ cho test
nhận diện người. Dữ liệu synthetic chỉ được dùng cho unit test và phải mang nhãn
`SYNTHETIC_NOT_EVALUATION`.

Dataset `person_detection` chỉ được chuyển sang `frozen` khi
`source_kind=internet_images`, có web manifest hợp lệ theo
`schemas/web-image-manifest.schema.json` phiên bản 2.0.0 và có cohort
`calibration/test_id/test_ood` giữ riêng. Ảnh chụp trong lab, simulator, ảnh tự
tạo và ảnh sinh bằng AI không được thay thế cohort test này.

PR10 không biến perception thành novelty. Detector/tracker là giao diện đo
lường; mọi lỗi của chúng phải được đưa vào phân tích end-to-end.

Raw media hiện tại chỉ là candidate package; mọi cohort mới phải được ghi bằng
manifest và run ID mới, không dùng lại URL/hash/annotation của cohort đã purge.
Admission vẫn khóa cho đến khi hoàn thành annotation mù độc lập, adjudication
và OOD expansion.

## 2. Điều kiện pháp lý, đạo đức và quyền riêng tư

Chỉ tải dữ liệu khi có license/terms cho phép cả tải xuống, xử lý và tạo
annotation derivative cho mục đích nghiên cứu và lưu trữ
dự kiến. Không suy luận rằng “công khai trên web” đồng nghĩa được phép tái phân
phối. Trước khi tải, ghi:

- landing-page URL và direct-file URL;
- tên tác giả/chủ sở hữu nếu có;
- license name/version, license URL và ngày kiểm tra;
- quyền download, processing, derivative annotation và redistribution;
- hạn chế attribution, non-commercial, share-alike hoặc no-derivatives;
- tình trạng người dễ nhận diện, trẻ em, bối cảnh nhạy cảm, cơ sở đạo đức/pháp
  lý khi asset chứa người và quyết định loại.

Không crawl trang cá nhân/social media, không dùng ảnh riêng tư/rò rỉ và không
thu identity/biometric label. Nếu license chỉ cho phép truy cập chứ không tái
phân phối, release manifest giữ URL/hash/processing code nhưng không đóng gói
raw media. Tham vấn ethics/legal nội bộ trước khi thu người thật hoặc release.

## 3. Source register bắt buộc

Mỗi nguồn có `source_id`; mỗi tệp có `asset_id`. Manifest tối thiểu:

| Trường | Ý nghĩa |
|---|---|
| `asset_id`, `source_id` | ID bất biến, không dùng tên tệp làm ID |
| `landing_url`, `download_url` | provenance có thể kiểm tra |
| `retrieved_at_utc`, `http_etag` | thời điểm/phiên bản tải nếu có |
| `license_name`, `license_url`, `license_checked_at` | quyền sử dụng tại lúc tải |
| `creator`, `required_attribution` | nghĩa vụ attribution |
| `sha256`, `byte_size`, `mime`, `width`, `height`, `fps` | toàn vẹn kỹ thuật |
| `source_split_group` | nhóm không được tách qua split |
| `real_media=true`, `ai_generated=false` | xác nhận loại media |
| `redistribution_allowed` | quyết định release |
| `annotation_status`, `reviewer_id` | trạng thái nhãn/QA |

Một record chỉ có `split_eligibility.approved=true` khi cả ba quyền
`download_allowed`, `processing_allowed`, `derivative_annotation_allowed` đều
đúng; `annotation_status=audited`; audit dùng guideline có phiên bản, ghi thời
điểm và thực hiện mù với prediction; và privacy review đã hoàn tất. Record chứa
người phải có `ethics_or_legal_basis` không rỗng. Record thuộc `calibration`,
`test_id` hoặc `test_ood` phải có `held_out=true`. Record bị loại phải có lý do
và không được đánh dấu approved.

Lưu raw manifest bất biến; sửa metadata bằng append-only correction record.
Hash được tính ngay sau tải và sau mọi derivative. URL chết về sau không làm
mất provenance nếu license snapshot/metadata và hash đã được lưu hợp lệ.

## 4. Sampling plan trước khi tìm ảnh

Đóng băng strata và quota trên tập development, không chọn ảnh dựa vào việc
model đoán đúng/sai. Tối thiểu bao phủ:

- indoor/outdoor, camera tĩnh/di động;
- sáng/tối/backlight, thời tiết và chất lượng nén;
- gần/xa, scale nhỏ/lớn, full/partial body;
- không che, che một phần, crowd/density cao;
- camera height/viewpoint khác robot;
- ảnh có người và negative image không có người;
- OOD source/domain chưa xuất hiện ở train/validation.

Test cuối phải là media thật tải từ Internet, không phải lab capture, sau khi
protocol/split/model đã khóa. Không tìm riêng các ảnh “đẹp” để minh họa rồi dùng chúng như estimate hiệu
năng. Ví dụ minh họa được chọn bằng quy tắc phân tầng ở PR40.

## 5. Chống trùng lặp và contamination

1. Group toàn bộ frame của cùng video/album/upload vào một `source_split_group`.
2. Loại exact duplicate bằng SHA-256; phát hiện near-duplicate bằng pHash/embedding
   chỉ trên dữ liệu, sau đó reviewer xác nhận thủ công.
3. Split theo source/recording/scene trước khi sinh frame hoặc crop.
4. Không để frame kề nhau, crop cùng ảnh hoặc re-encoding qua split.
5. Kiểm tài liệu model card/training provenance của detector. Nếu test source
   có khả năng nằm trong pretraining, gắn `PRETRAINING_OVERLAP_UNKNOWN/KNOWN` và
   không dùng để claim generalization; cần một external source sạch hơn.
6. Không điều chỉnh confidence/NMS sau khi xem final test/OOD.

## 6. Annotation và quality control

Bounding box dùng một convention duy nhất (`xyxy`, pixel origin và inclusive/
exclusive rõ ràng). Quy tắc phải nêu cho occlusion, truncation, reflection,
poster/mannequin và “ignore region”. Một tập negative thật sự không có người là
bắt buộc nếu đánh giá image-level presence classification.

- Hai annotator độc lập trên toàn test hoặc ít nhất một annotator + audit 100%
  disagreement/edge cases.
- Đo inter-annotator IoU và agreement cho presence/ignore labels.
- Adjudicator không nhìn prediction khi quyết định ground truth.
- Mọi sửa nhãn sau khi mở prediction có change log và đánh giá sensitivity.

Đối với video tracking, track ID không đổi trong một recording; không nối cùng
người qua camera/source nếu không có ground truth hợp lệ.

### 6.1 Hợp đồng đánh giá bounding box mù

Các chỉ số IoU, TP--FP--FN, precision/recall/F1 và average precision chỉ được
tính khi có manifest `schemas/person-bbox-annotation.schema.json` độc lập với
prediction. Manifest phải hash đúng web-image manifest, bao phủ đúng một record
cho mỗi asset, dùng tọa độ `xyxy` hợp lệ và được tạo khi annotator chưa xem
prediction. Prediction của YOLO, pseudo-label hoặc nhãn suy ra từ model không
được dùng làm ground truth. Khi chưa có annotation mù, `det_eval.py` chỉ được
ghi ma trận nhầm lẫn ở mức ảnh (person-present/person-absent) và phải giữ trạng
thái `candidate-not-evidence`.

Hiện có manifest/media candidate mới dưới
`data/raw/web-cohort-20260814/`; preflight manifest-only là `PASS` nhưng
admission vẫn `BLOCKED` vì chưa có annotation mù độc lập, adjudication, privacy
review hoàn tất, pretraining-overlap review và cohort expansion. Muốn mở
admission phải khóa split held-out, có second-annotator/adjudicator độc lập và
lưu change log cho mọi chỉnh sửa sau khi mở prediction. Diagnostic mới chỉ
được dùng để kiểm plumbing và giữ lại lỗi, không dùng chọn model hay viết
claim.

Schema `person-bbox-annotation.schema.json` hiện đã mô tả tùy chọn
`independent_annotation` và `adjudication` để không biến một cờ boolean thành
bằng chứng. Preflight chỉ mở gate này khi annotation thứ hai có cùng manifest,
cùng guideline, ID annotator khác, đủ toàn bộ asset; adjudicator mù có ID thứ
ba, liên kết đúng hai annotation và ghi `presence_agreement`/`mean_matched_iou`.
Các fixture kiểm tra chỉ tồn tại trong bộ test, không phải nhãn dữ liệu.

### 6.2 Mechanical preflight hiện tại

Lệnh `python -B scripts/python/tools/validate_web_cohort.py --manifest <new-manifest.json> --annotations <new-annotations.json> --output <new-preflight.json>` vẫn là cổng bắt
buộc cho cohort mới, kiểm schema manifest/annotation, hash và kích thước byte,
decode/dimensions, binding mù của bounding box, unique asset/SHA-256, disjoint
source group, cờ media thật/không AI, quyền xử lý và trường privacy. Report và
metric cũ đã bị xóa theo [[07_Analysis/development-artifact-purge-20260814]];
không có `PASS` hoặc metric cũ nào là evidence hiện hành.

## 7. Split và OOD

Các split riêng: `train`, `validation`, `calibration`, `test_id`, `test_ood`.
Final test chỉ được mở một lần cho model/threshold đã freeze. Group disjointness
được kiểm theo source, recording, scene và person/track khi biết. OOD được định
nghĩa trước theo camera/site/lighting/density chứ không gắn nhãn OOD sau khi thấy
model thất bại.

Nếu dùng public benchmark có official split, giữ split đó và thêm external OOD;
không trộn official test vào training. Mọi ảnh Internet ad-hoc thuộc external
cohort riêng, không dùng để sửa model sau khi mở.

## 8. Đánh giá đúng loại bài toán

### Person detection

Báo precision--recall, AP theo IoU và scale, recall, false positives per image,
miss rate, latency và stratified error. Matching prediction--GT dùng IoU threshold
đã khóa. Bounding-box detection không có một số true-negative tự nhiên, nên
không tạo confusion matrix 2x2 giả.

### Image-level person presence (chỉ khi tiền đăng ký)

Nếu định nghĩa riêng một classifier “ảnh có ít nhất một người / không có người”,
có positive/negative labels và threshold đóng băng, báo confusion matrix
TN/FP/FN/TP, sensitivity, specificity, precision, F1 và CI. Không dùng ma trận
này để thay cho detection AP.

### Multi-class detector (nếu thật sự có)

Chỉ báo class confusion matrix sau rule matching/ignore rõ. Với dự án chỉ có lớp
`person`, không quảng bá “classification accuracy”.

## 9. Artifact và cổng chấp nhận

Giữ download script/config, raw/processed manifests, data card, annotation
guideline, split manifest, dedup report, license report, test lock và error
gallery theo quy tắc PR40. Mọi derivative overlay có parent asset hash.

PR10 đạt `VERIFIED` khi registry dataset và web manifest đều qua schema 2.0.0;
100% asset approved thuộc calibration/test là media thật tải từ Internet, có
URL + SHA-256 + ba quyền sử dụng đúng + cơ sở privacy/legal phù hợp và
`held_out=true`; không có cross-split duplicate đã biết; split/OOD đã khóa trước
model selection; annotation audit mù hoàn tất; pretrained contamination được
công bố; và không có raw asset bị release trái license.

## 10. Fresh instrument run — 2026-08-14

The stale diagnostic directory was deleted before this run. The official
`yolo26s-pose.pt` checkpoint was downloaded again and verified with SHA-256
`A083ADB42303728AE14C4BD6BD56D80DA46F82FB2564DBD6F31DCC92EA321646`. Inference
was rerun on all seven real Internet images using CPU. The output is
`experiments/runs/person-web-inference-20260814/inference/` and remains
`candidate-not-evidence`.

At the manifest scene-tag boundary only, the image-level matrix at confidence
0.25 is `[[2,0],[0,5]]`; accuracy, precision, recall, specificity and F1 are
all 1.0 on these seven images. These numbers are descriptive plumbing output,
not detector accuracy: no blinded boxes, independent presence annotation or
adjudication was used. CPU latency was P50 313.43 ms, P95 505.37 ms and maximum
544.43 ms, and is not a Jetson target-device result.

Every gallery image includes the local LSTM checkpoint path as provenance with
`context=not-provided (static image)`. No speed, direction, future human path
or robot local path was fabricated or drawn.

## 11. Public ground-truth diagnostic — 2026-08-14

The official Ultralytics COCO8-pose release archive was downloaded to
`data/raw/coco8-pose-20260814/`. Four validation images were selected by the
provider split, and their provider bounding boxes were parsed without changing
the labels. The manifest and annotation records are
`data/raw/coco8-pose-20260814/coco8-pose-manifest.json` and
`data/raw/coco8-pose-20260814/coco8-pose-bbox-annotations.json`; the preflight
report is `research/metadata/coco8_pose_preflight_20260814.json`.

The fresh `det_eval.py` run is
`experiments/runs/coco8-pose-inference-20260814/`. At confidence `0.25` and
IoU `0.5`, it reports 14 provider boxes, TP `11`, FP `1`, FN `3`, precision
`0.9167`, recall `0.7857`, F1 `0.8462`, mean matched IoU `0.8562`, and CPU
latency P50/P95/max `324.91/573.17/603.18` ms. All four images are positive,
so the image-level matrix `[[0,0],[1,3]]` has no negative denominator and does
not support specificity. Bootstrap intervals are descriptive only.

The provider labels predate this inference and are mechanically bound to the
manifest, but they are not independent human annotation or adjudication. The
preflight is therefore `PASS` with `admission_status=BLOCKED`; these numbers
are plumbing diagnostics only. Independent blinded annotation/adjudication,
pretraining-overlap review, privacy release, a larger calibration/test-ID/
test-OOD cohort and target-device timing are still required before admission.
