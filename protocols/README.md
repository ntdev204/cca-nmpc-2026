# Bộ protocol nâng cấp nghiên cứu CCA-NMPC + LSTM

> **Loại tài liệu:** protocol thiết kế và tiền đăng ký, không phải bài báo và
> không phải bằng chứng kết quả.
> **Trạng thái ban đầu:** `DRAFT-DESIGN`; chưa protocol nào được xem là đã chạy.
> **Ngày khởi tạo:** 2026-08-01.

## 1. Mục đích và ranh giới

Bộ tài liệu này quy định cách nâng cấp nghiên cứu lên mức có thể được đánh giá
nghiêm túc tại tạp chí Q1 SCIE. Hệ thống vẫn là **Continuous Context-Aware
Nonlinear Model Predictive Control (CCA-NMPC)** dùng context do **LSTM** nén từ
lịch sử quan sát (vị trí, tốc độ, hướng và độ tin cậy). Người là đối tượng
động; chỉ CCA-NMPC được phép tích phân context velocity thành vị trí tương lai
nội bộ cho chance rows. LSTM chỉ cung cấp context snapshot, còn chuỗi nội bộ
này không được lưu hoặc vẽ lên ảnh. Không bổ sung một nhánh AI hoặc một bộ điều khiển mới chỉ để tạo cảm
giác mới lạ.

Phạm vi điều khiển vật lý dùng state `[x,y,theta,vx,vy,omega]` và lệnh vận tốc
thân để bám vị trí; không yêu cầu điều khiển hoặc đo mô-men/dòng điện.

Các tệp trong `protocols/` là hợp đồng trước khi thu thập dữ liệu, huấn luyện,
mô phỏng hoặc thử nghiệm. Chúng không được trích dẫn như kết quả. Mọi số liệu cũ
trong `backup/` chỉ là ảnh chụp lịch sử, không phải bằng chứng cho nghiên cứu mới.

Các mục trong phần “Nhật ký cập nhật” là audit log bất biến của các checkpoint
trước lần clean-reset. Sau checkpoint purge 2026-08-14, mọi dataset, model, run
và result candidate đã bị xóa vật lý; các số cũ trong nhật ký chỉ để truy nguyên
quyết định, không phải kết quả hiện hành và không được dùng cho paper.

Không viết hoặc build bài báo ở local. Bản thảo và quá trình biên dịch thuộc
Overleaf. Local chỉ chứa protocol, mã, cấu hình, dữ liệu được phép lưu, manifest,
log và artifact tái lập.

Mọi tài liệu chính thức gửi giáo sư phải được soạn bằng LaTeX, build thành PDF
trên Overleaf và viết bằng tiếng Việt. Ngoại lệ: ghi chú tiếng Việt trong vault
Obsidian có thể chia sẻ trực tiếp với giáo sư. Markdown ngoài vault chỉ phục vụ
nghiên cứu nội bộ. Chỉ manuscript tạp chí cuối cùng `main.pdf` được viết bằng tiếng Anh.

## 2. Bốn nguồn sự thật theo miền

| Miền | Nguồn sự thật | Quy tắc |
|---|---|---|
| Thiết kế nghiên cứu | Các protocol đã `FROZEN` trong thư mục này | Thay đổi sau khi mở holdout phải có amendment và phiên bản mới |
| Tài liệu chính thức gửi giáo sư | Overleaf | LaTeX/PDF tiếng Việt |
| Ghi chú nghiên cứu gửi giáo sư | Obsidian | Vault note tiếng Việt có thể chia sẻ trực tiếp |
| Manuscript tạp chí cuối | Overleaf | Chỉ `main.pdf` bằng tiếng Anh; không duy trì bản local song song |
| Thư mục tài liệu, metadata, PDF và citation key | Zotero | Không tự gõ tài liệu tham khảo không có Zotero item đã kiểm tra |
| Ghi chú đọc, lập luận research gap và nhật ký quyết định | Obsidian | Mỗi kết luận phải liên kết tới Zotero key hoặc claim ID |
| Dữ liệu, model, kết quả | Manifest có hash của evidence release | Tên tệp hoặc ảnh chụp màn hình không thay thế SHA-256 và provenance |

Khi có xung đột, nguồn sự thật của đúng miền được ưu tiên. Ví dụ, Zotero quyết
định metadata trích dẫn nhưng manifest quyết định model nào đã sinh ra một bảng.
Mọi số trong Overleaf phải truy ngược được tới `claim_id`, `artifact_id`, protocol
version và SHA-256.

## 3. Vòng đời protocol

```text
DRAFT-DESIGN -> REVIEWED -> FROZEN -> EXECUTED -> VERIFIED -> RELEASED
                         \-> AMENDED-vN (không ghi đè lịch sử)
```

- `DRAFT-DESIGN`: được phép sửa, không được chạy như nghiên cứu xác nhận.
- `REVIEWED`: đã kiểm tra logic, đạo đức, khả năng thực thi và leakage.
- `FROZEN`: có version, commit, SHA-256, người duyệt và thời điểm trước khi mở
  test/holdout.
- `EXECUTED`: đã chạy đúng protocol; sai lệch được ghi, không che giấu.
- `VERIFIED`: người/tiến trình độc lập đã kiểm manifest, hash và phân tích.
- `RELEASED`: gói bằng chứng đã phát hành theo PR50.

Mọi amendment phải ghi: lý do, thời điểm, dữ liệu nào đã được nhìn thấy, ảnh
hưởng tới giả thuyết, và quyết định giữ hay hủy tính confirmatory. Không thay
seed, metric, baseline, ngưỡng hoặc tiêu chí sau khi biết kết quả mà vẫn gọi là
tiền đăng ký.

## 4. Trạng thái thực thi hiện tại — 2026-08-14 (sau clean-reset)

Status dưới đây là status của protocol, không phải status của paper claim. `FROZEN`
chỉ có nghĩa thiết kế đã khóa; `VERIFIED` còn cần artifact, hash và kiểm tra độc
lập. Không nâng status của PR10--PR12 hoặc PR20--PR21 khi chưa có dữ liệu/holdout
 và phân tích tương ứng.

| Protocol | Status hiện tại | Đã hoàn tất | Việc còn lại trước khi chuyển bước |
|---|---|---|---|
| PR00 | `REVIEWED` | RQ, hypothesis, claim boundary và scope amendment đã ghi; focused audit bounded đã review logic, nearest-work và comparator implications, không đổi gap hẹp | preregistration version/SHA-256 và phê duyệt nội bộ trước holdout; chưa phải claim được chứng minh |
| PR01 | `ARCHIVED — NOT AN ACTIVE GATE` | Đã loại SLR/PRISMA khỏi bài nghiên cứu gốc | chỉ giữ provenance lịch sử; không chạy tiếp |
| PR02 | `PROOF-DRAFT` | model, assumptions, T1--T5, explicit ellipse--disk half-space containment derivation và code parity/fail-closed checks đã ghi | review độc lập, geometry/parity audit trên snapshot bất biến, calibration và giới hạn claim |
| PR10 | `CANDIDATE-ACQUIRED / BLOCKED` | fresh seven-image Wikimedia cohort passed manifest-only schema/hash/decode/rights preflight; YOLO26s-pose CPU diagnostic and LSTM-path provenance overlays were generated without fabricated context | independent blinded annotation/adjudication, privacy/legal approval, pretraining-overlap review, held-out/OOD expansion and approval |
| PR11 | `REVIEWED` | schema context, causal window, strict direction tokens, confirmatory split requires all leakage-group keys, no-human-trajectory contract and static code checks đã qua design review; candidate NavWareSet đã purge | permitted target-compatible real context recording, calibration and dataset freeze |
| PR12 | `DEVELOPMENT-EXECUTED / UNRELEASED` | self-supervised score loop, five-seed LSTM, independent calibration and score/penalty policy were rerun from the clean reset; package remains simulation-only | target-compatible context, checkpoint freeze, ID/OOD test and independent rerun |
| PR20 | `DEVELOPMENT-EXECUTED / UNRELEASED` | fresh simulation learning package, fixed-global/local-trigger map package and bounded MATLAB position-state export completed with hash replay | protocol freeze, S2/S3 confirmatory campaign and independent analysis |
| PR21 | `DEVELOPMENT-EXECUTED / UNRELEASED` | five-controller position/body-velocity benchmark completed on paired development units with tuning disabled and raw-to-summary replay | frozen fairness ledger, confirmatory paired benchmark and PR40 analysis |
| PR22 | `PURGED (development-only)` | pilot cũ đã xóa trước campaign mới; purge record giữ hash/provenance, global-path/local-trigger contract vẫn còn trong protocol | tạo run mới chỉ sau PR20/PR21 freeze; không khôi phục số liệu cũ |
| PR23 | `FROZEN-PILOT` | stabilization design và 24-run assignment đã khóa | chạy đúng assignment nếu còn cần chẩn đoán |
| PR24 | `FROZEN-PILOT` | feasibility-preservation design và fallback criteria đã khóa | chạy pilot mới; giữ failure trong mẫu số |
| PR30 | `REVIEWED` | static no-ROS hardware-entry preflight `PASS` và direct design đã qua review (position-state `[x,y,theta,vx,vy,omega]`, body-velocity STM32 serial bridge, optional CAN contract, mini-Mecanum URDF binding, commissioning lock, strict direct CSV/JSON timestamp validation and hash-bound calibration sidecar contract); admission chưa mở | physical specs, approvals, calibration, stage gate and direct hardware package |
| PR40 | `REVIEWED` | ITT-like populations, paired metrics, CI, confusion-matrix semantics, qualitative rubric và failure taxonomy đã qua design review | freeze trước holdout; independent analysis |
| PR50 | `DRAFT-DESIGN` | release inventory, claim matrix và Q1 review gate đã viết | chỉ mở sau khi PR10--PR40 đạt yêu cầu |

### Nhật ký cập nhật status — 2026-08-13

- `PR00` đã chuyển từ `DRAFT-DESIGN` sang `REVIEWED` cho scope/claim logic sau
  focused-audit review bounded tại
  `research/obsidian/07_Analysis/focused-audit-review-20260813.md`. Đây không
  phải systematic review và không mở bất kỳ cổng dữ liệu, mô phỏng hay robot
  thật nào; preregistration freeze vẫn còn trước confirmatory holdout.
- Thiết kế PR11, PR12, PR20, PR21, PR30 và PR40 đã qua design review và được
  đồng bộ thành `REVIEWED`. Đây chỉ là review thiết kế; các protocol vẫn chờ
  dataset/checkpoint/holdout/hardware artifact tương ứng và không được gọi là
  `EXECUTED` hay `VERIFIED`.

- `PR01` đã được đồng bộ nhất quán ở mọi manifest/schema: `ARCHIVED — NOT AN
  ACTIVE GATE`. Các dòng `IN-PROGRESS` còn lại trong file PR01 chỉ mô tả cổng
  của scope comprehensive lịch sử.
- `PR02` đã hoàn tất phần viết T1--T5, property/counterexample tests hiện có,
  parity Python--MATLAB ở mức phần mềm và probability gate fail-closed. Status
  vẫn là `PROOF-DRAFT` vì chưa có reviewer control độc lập, geometry review và
  calibration artifact bất biến.
- `PR10` từng hoàn tất mechanical preflight (`PASS`) cho cohort mười ảnh thật;
  cohort và report đó đã bị purge. Sau clean-reset, status hiện tại là
  `RESET-BEFORE-ACQUISITION`; mọi media/diagnostic candidate không còn local và
  phải thu lại với annotation độc lập, overlap review và holdout/OOD.
- `PR22` đã được `PURGED (development-only)` theo reset boundary; các package
  pilot và model payload cũ không còn trong workspace. `PR23` và `PR24` vẫn là
  `FROZEN-PILOT` ở mức thiết kế, không có số liệu cũ được phục hồi.
- `PR30` đã hoàn tất static no-ROS entry preflight (`PASS`), bao gồm kiểm tra
  timestamp tăng nghiêm ngặt của gói CSV/JSON; hardware admission
  vẫn `BLOCKED` vì chưa có package robot thật, calibration và stage-gate.
- Bản ghi trước đó về việc PR00 chưa đủ điều kiện là lịch sử tại thời điểm
  focused audit còn `IN_PROGRESS`. Sau closure checkpoint, PR00 đã là
  `REVIEWED`; design review downstream cũng đã chuyển PR11/12/20/21/30/40
  thành `REVIEWED`. Các status này chỉ phản ánh review thiết kế, không thay thế
  freeze, execution hoặc verification.
- Focused audit vừa ghi thêm lượt Google/web screening ngày 2026-08-13 cho
  SHARP (CVaR/Bonferroni), context-aware preference learning và ARMS; các bản
  ghi chỉ là screening-only, chưa import Zotero và không thay đổi gap hẹp.
- Lượt refresh tiếp theo ngày 2026-08-13 ghi thêm DRA-MPPI (IROS 2025),
  uncertainty-aware predictive CBF, DR-MPC (RA-L 2025) và SI-MPC trên robot
  thật vào Obsidian. Đây là boundary/comparator screening-only; không import
  Zotero, không nâng PR00 và không sửa manuscript.

### Nhật ký tiếp tục — 2026-08-13, 22:05 UTC

- `repo_check.py` và `git diff --check` đã chạy lại: repository contract `PASS`
  (`23` schemas, `17` instances, `86` notes, `696` wikilinks, không có issue).
- `PR02` đã xác nhận lại bằng Python suite `152 passed`, Ruff `PASS`, STM host
  `PASS` và MATLAB `68 passed, 0 failed, 0 incomplete` trong `25.2537 s`;
  đây vẫn chỉ là software QA, không nâng `PROOF-DRAFT`.
- Ở checkpoint lịch sử này, `PR10` giữ `ACQUIRING` và r12 mechanical preflight
  vẫn `PASS`; candidate đó sau đó đã bị purge. Status hiện tại là
  `RESET-BEFORE-ACQUISITION`.
- `PR30` đã siết `final_pack.py` để từ chối timestamp trùng/không tăng; regression
  test mới pass và preflight report được sinh lại với hash mới. Đây chỉ là
  interface QA; hardware admission vẫn bị chặn.
- `PR02` đã bổ sung kiểm tra T4 cho covariance bằng không và covariance gần
  suy biến ở cả Python và MATLAB; Python suite hiện `155 passed`, MATLAB
  `70 passed, 0 failed, 0 incomplete`. Đây là parity/edge-case QA có hash mã
  kiểm, không phải calibration, geometry review độc lập hay bằng chứng
  operational probability.
- Bổ sung derivation containment ellipse--disk trong PO-001 và test boundary
  mẫu ở MATLAB; suite MATLAB hiện `70 passed, 0 failed, 0 incomplete`. Đây
  vẫn chỉ là parity/geometry QA, chưa phải review độc lập hay calibration.
- Checkpoint `2026-08-13 05:32 ICT`: sau khi sửa SHA derivation ledger,
  `repo_check.py`, `git diff --check` và Ruff đều `PASS`; Python full suite
  `154 passed`, MATLAB `70 passed, 0 failed, 0 incomplete`. Không có protocol
  nào được promote.
- Checkpoint `2026-08-13 05:33 ICT`: Python có thêm một helper kiểm tra
  ellipse-support và test parity số học; chưa có claim xác suất/collision nào
  được promote. Status PR02 vẫn `PROOF-DRAFT`.
- Checkpoint `2026-08-13 05:34 ICT`: full Python QA `155 passed`, Ruff,
  `repo_check.py`, `git diff --check` và STM host tests đều `PASS`; MATLAB vẫn
  `70 passed, 0 failed, 0 incomplete`. Không có protocol nào được promote.
- `PR00` focused audit đã ghi thêm web recheck về YOLO26-pose (chỉ là công cụ
  perception) và DRA-MPPI (comparator MPPI risk-aware); research-gap không đổi,
  không import Zotero mới và không mở rộng claim. Audit vẫn `IN_PROGRESS`.
- `PR12`/`PR20` đã siết checkpoint provenance: confirmatory `map_run.py` phải
  đọc được manifest capture thật, kiểm hash và các cờ context-only; chỉ có hash
  sao chép trong checkpoint không còn đủ.
- `PR11`/`PR12` tiếp tục `DRAFT-DESIGN`: NavWareSet chỉ là candidate
  processed CSV/JSON; chưa tải, chưa xác minh điều khoản dữ liệu, chưa có
  frame/calibration provenance và chưa có checkpoint admissible.
- `PR20`--`PR24` không mở campaign mới trong checkpoint này; `PR22` vẫn là
  `EXECUTED (development-only)` và không được promote. `PR30` chưa mở vì
  chưa có package robot/calibration thật; `PR40` và `PR50` tiếp tục chờ các
  protocol bằng chứng phía trước.

### Nhật ký tiếp tục — 2026-08-13, 05:45 ICT

- Ở checkpoint lịch sử 05:45 ICT, `PR10` giữ `ACQUIRING`; schema/validator đã
  thêm cổng độc lập cho annotation thứ hai và adjudication mù; fixture
  accept/reject chỉ chạy trong test. Cohort mười ảnh thật khi đó `PASS` ở
  mechanical preflight nhưng `BLOCKED` ở admission, rồi được purge trước
  campaign mới. Report SHA-256 lịch sử:
  `CC40F0E3A4ACFE8B437CFED42727295D17327033897FF91824C6888B032F0E95`;
  validator SHA-256:
  `85AEDE25ADD67A1354B958C4F6963FCEC972659FD78FED1E9378E49905418AF9`.
- `PR11` giữ `DRAFT-DESIGN`. Đường confirmatory context hiện từ chối direction
  ngoài tập `left/right/forward/backward/unknown/invalid` và yêu cầu đủ
  `recording_id`, `episode_id`, `source_id`, `scene_id` trước khi sinh window.
  Không có dữ liệu thật hoặc checkpoint mới được tạo.
- Full Python QA `169 passed`; Ruff, `repo_check.py`, `git diff --check` đều
  `PASS`. Repository contract hiện có `23` schemas, `17` instances, `86` notes,
  `696` wikilinks. MATLAB giữ checkpoint `70 passed, 0 failed, 0 incomplete`;
  không có MATLAB source nào đổi. Không protocol nào được promote.
- `PR00` giữ `DRAFT-DESIGN` sau lượt Google/Scholar-oriented refresh lúc
  `2026-08-13 05:52 ICT`: risk-aware MPPI, Mecanum MPC/hardware disturbance
  rejection và uncertainty-aware predictive safety được ghi thành screening
  boundaries trong Obsidian (note SHA-256
  `381282E54BC3F0FD2CA392DC8A7AD73F1D4A791D1B9F06853B9E6A2F995AFB23`). Gap
  vẫn là matched CCA interface comparison; không import Zotero mới và không
  sửa manuscript.
- `PR30` giữ `DRAFT-DESIGN`: `final_pack.py`, `ctx_run.py` và `analyze_run.py`
  hiện từ chối capture source khác `unknown` nếu thiếu `calibration.json` có
  intrinsics/extrinsics/residuals và SHA-256 khớp manifest. Static preflight
  `PASS`, report SHA-256
  `2B7F8733618806D6BD3C3332817FC5887E09549AA6737B26770A1A34909A54AE`, nhưng
  hardware admission vẫn `BLOCKED` vì chưa có robot package, physical specs,
  stage gate hay calibration thật.
- `PR12` giữ `DRAFT-DESIGN`: calibration-sidecar SHA-256 được lưu trong
  checkpoint metadata và kiểm lại trong `map_run.py`; full Python QA hiện
  `169 passed`. Chưa có context CSV, calibration record hoặc checkpoint thật.

### Nhật ký tiếp tục — 2026-08-13, 06:06 ICT

- PR12/PR30 hiện dùng chung cổng calibration-sidecar: mọi capture source khác
  `unknown` phải có `calibration.json` với sensor identity, camera intrinsics,
  camera/LiDAR extrinsics, residuals và hash-bind trong manifest/checksum.
- Đây là provenance/interface QA, không phải calibration hay hardware evidence.
  Python `169 passed`, Ruff/`repo_check.py`/`git diff --check` `PASS`; MATLAB
  giữ `70 passed, 0 failed, 0 incomplete`. Không protocol nào được promote.

### Nhật ký tiếp tục — 2026-08-13, direct hardware recorder

- `PR30` có thêm scaffold code `src/hardware.py` và
  `scripts/python/tools/record_hardware.py`: Astra-S/OpenNI2, N10P serial,
  CCA CAN, context-only LSTM overlay và direct CSV/JSON writer. Template
  `configs/hardware_runtime.template.json` vẫn để trống port/CAN/firmware và
  kích thước robot để fail-closed trước khi mở thiết bị.
- Decoder, geometry, odometry, CSV và context interface test đã pass; đây là
  software/integration QA. Chưa mở thiết bị, chưa có physical CSV/map package,
  calibration, safety approval hay robot timing. `PR30` vẫn
  `DRAFT-DESIGN` và hardware admission vẫn `BLOCKED`.

- N10P baud không còn có giá trị template mặc định. Manual N10 công bố
  230400 bps trong khi parity driver tham chiếu 460800; cấu hình physical phải
  khai báo baud đo từ đúng model/firmware cùng `n10p-108b-v1`, nếu không
  recorder dừng trước khi mở serial.

### Nhật ký tiếp tục — 2026-08-13, direct timing/profile gate

- Recorder không còn chọn layout N10P ngầm: bản cấu hình thực phải khai báo
  `lidar.protocol_profile=n10p-108b-v1`, và profile này vẫn phải đối chiếu với
  revision/firmware của thiết bị trước H0.
- Astra-S ghi `camera_device_t_ns` khi OpenNI2 expose timestamp thiết bị; `t_ns`
  trong CSV vẫn là host receive time để đồng bộ với CAN/serial. Nếu khai báo
  `camera.max_pair_skew_us`, cặp màu--depth vượt ngưỡng sẽ bị từ chối. Metadata
  sidecar lưu số frame có timestamp và skew quan sát được.
- Đây là fail-closed interface QA, không phải đo timing hay bằng chứng phần
  cứng. Chưa mở thiết bị, chưa tạo CSV/map/checkpoint mới; PR30 vẫn
  `REVIEWED` và admission `BLOCKED`.

## 5. Thứ tự thực hiện

**Amendment phạm vi ngày 2026-08-12:** workspace này phục vụ một bài báo nghiên
cứu gốc, không phải systematic literature review. PR01 frozen vẫn được giữ để
truy vết lịch sử nhưng không còn là deliverable active và không được dùng để
chặn code, mô phỏng hay thực nghiệm. Active literature task là focused audit
trong Zotero/Obsidian; không được gọi kết quả đó là PRISMA, systematic search
hoặc exhaustive database coverage. Nếu sau này chọn journal yêu cầu systematic
review riêng, phải tạo amendment và scope mới trước khi thực hiện.

Các số hàng chục trong tên file là **mã pha ổn định**, không phải số thứ tự
liên tục: `00--02` là phạm vi/lý thuyết, `10--12` là dữ liệu và LSTM,
`20--24` là mô phỏng, `30` là robot thật, `40` là phân tích và `50` là phát
hành. Cột **Thứ tự** dưới đây mới là thứ tự thực thi. Không đổi mã `PRxx` tùy
ý vì mã này đã được dùng trong manifest, schema, hash và claim ledger.

| Thứ tự | Protocol | Đầu ra chính |
|---:|---|---|
| 0 | [PR00](PR00_scope_and_claims.md) | Phạm vi, RQ, giả thuyết và claim ledger |
| 1 | Focused audit ([PR01 archive](PR01_literature_review.md)) | Zotero/Obsidian nearest-work matrix, source notes và gap giới hạn |
| 2 | [PR02](PR02_theory_and_proofs.md) | Mô hình tối giản, định lý có điều kiện, proof ledger |
| 3 | [PR10](PR10_person_data_acquisition.md) | Dữ liệu ảnh/video người từ Internet có license và hash |
| 4 | [PR11](PR11_lstm_dataset.md) | Dataset chuỗi quỹ đạo, split chống leakage và OOD |
| 5 | [PR12](PR12_lstm_training_evaluation.md) | Huấn luyện, calibration và đánh giá LSTM |
| 6 | [PR20](PR20_simulation.md) | Chiến dịch mô phỏng xác nhận và stress/OOD |
| 7 | [PR21](PR21_controller_benchmark.md) | Benchmark controller/ablation với ngân sách công bằng |
| 8 | [PR30](PR30_physical_experiment.md) | Thử nghiệm robot thật an toàn và có đạo đức |
| 9 | [PR40](PR40_statistics_and_qualitative_analysis.md) | Phân tích định lượng, định tính và lỗi |
| 10 | [PR50](PR50_evidence_release.md) | Đóng băng bằng chứng và cổng phản biện Q1 |

Focused literature audit phải hoàn tất trước khi đóng băng claim novelty của bài
báo hiện tại. PR10--PR12 phải hoàn tất trước khi dùng LSTM trong kết luận
closed-loop. PR20 là bằng chứng mô phỏng; PR30 mới có thể hỗ trợ tuyên bố robot
thật. PR40 phải được đóng băng trước khi mở holdout tương ứng.

PR01-SLR frozen là hồ sơ lịch sử và không còn là cổng active của scope này. Freeze
manifest và preflight active đã trỏ trường research-gap tới focused-audit record,
Zotero export và nearest-work matrix;
không được yêu cầu database export từ Scopus/WoS/IEEE Xplore nếu bài báo không
tuyên bố systematic review. Nếu đổi sang review article hoặc journal yêu cầu
PRISMA, phải tạo amendment scope riêng.

## 6. Quy ước ID và truy vết

- `RQ-xx`: câu hỏi nghiên cứu.
- `H-xx`: giả thuyết xác nhận.
- `CLM-NOV/EMP/T/ML/SIM/HW-xx`: claim novelty, thực nghiệm tổng hợp, lý thuyết,
  học máy, mô phỏng hoặc phần cứng. `CLM-EMP-*` dùng cho estimand thực nghiệm
  xuyên nhiều tầng bằng chứng, không thay thế claim mô phỏng hay phần cứng cụ thể.
- `ds-*`, `model-*`, `exp-*`, `run-*`, `art-*`: dataset, model, campaign,
  run và artifact; ID phải khớp schema machine-readable.
- `DEV-xx`: sai lệch protocol; `FAIL-xx`: sự kiện lỗi.

Mỗi claim phải có một dòng trong claim--evidence matrix của PR00/PR50. Claim
không có bằng chứng phù hợp sẽ bị xóa hoặc viết lại thành giới hạn/future work.

## 7. Quy tắc toàn cục không thương lượng

1. Giữ nguyên hạt nhân CCA-NMPC + LSTM; perception chỉ cung cấp đo lường và
   LSTM chỉ cung cấp dự báo, không được quảng bá thành novelty nếu focused audit
   không có bằng chứng cho điều đó.
2. Công thức phải dùng ký hiệu ít nhất cần thiết, định nghĩa ngay khi xuất hiện,
   và tách giả định khỏi kết luận.
3. Test nhận diện người phải dùng ảnh/video thật tải từ Internet; mỗi tệp có URL
   nguồn, URL license, thời điểm tải, SHA-256 và quyết định quyền sử dụng. Ảnh
   sinh bằng AI không hợp lệ cho test này.
4. Kết quả LSTM phải có overlay trên ảnh/video thật gồm bbox, keypoint, track
   ID/history, vị trí hiện tại, tốc độ, hướng, độ tin cậy, trạng thái hợp lệ và
   cảnh báo calibration/provenance. Không vẽ quỹ đạo tương lai của người; local
   path của robot chỉ xuất hiện trong artifact map.
5. Split theo source/recording/scene/person; không để cửa sổ chồng lấn hoặc bản
   sao gần giống đi qua các split. Có holdout OOD độc lập.
6. Confusion matrix chỉ xuất hiện cho một bài toán classification có nhãn lớp,
   luật quyết định và TN/FP/FN/TP hợp lệ. Trajectory regression không có
   confusion matrix. Person detection không được giả tạo true negative theo
   bounding-box.
7. Baseline và ablation dùng cùng dữ liệu, seed, đường đi, giới hạn actuator,
   deadline và ngân sách tuning/compute thích hợp. Chênh lệch không thể khớp
   phải được công bố.
8. Run lỗi, collision, timeout, fallback và incomplete luôn ở mẫu số. Không xóa
   outlier chỉ vì bất lợi.
9. Mô phỏng chỉ hỗ trợ claim mô phỏng. Timing trên máy phát triển không phải
   hard real-time; thử nghiệm robot không tự động chứng minh an toàn ngoài miền.
10. Kết quả âm tính được lưu và viết. Không đổi hypothesis sau khi xem holdout.

## 8. Definition of done toàn chương trình

Chương trình chỉ được gọi là hoàn tất khi tất cả protocol bắt buộc đạt
`VERIFIED`, claim--evidence matrix không còn ô trống, dữ liệu/model/result có
manifest và hash, các giới hạn được ghi đúng trong Overleaf, và cổng
`q1-reviewer-ee` ở PR50 trả về `Accept` sau vòng sửa cuối. `Weak Accept` là yêu
cầu sửa và review lại; `Reject` dừng phát hành.

### Checkpoint mới nhất — 2026-08-13 00:06 UTC

`repo_check.py --require-focused-audit-complete`, Ruff và toàn bộ Python suite
đều `PASS` (`169` tests). Repository hiện có `23` schemas, `15` instances,
`91` Obsidian notes và `755` wikilinks. Đây là kiểm tra cấu trúc/QA; không phải
evidence khoa học. PR00 là `REVIEWED`; PR11/12/20/21/30/40 là `REVIEWED` ở mức
thiết kế; PR02 vẫn `PROOF-DRAFT`, PR10 vẫn admission-blocked, và PR50 chưa thể
release.

### Numerical-parity checkpoint — 2026-08-13 00:31 UTC

PR02 vẫn `PROOF-DRAFT`. Sàn phương sai của chance row đã được khai báo chung ở
Python và MATLAB (`1e-12 m^2`), sau đó full Python suite `171 passed`, MATLAB `70 passed,
0 failed, 0 incomplete`, Ruff, `repo_check.py` và `git diff --check` đều `PASS`.
Đây là sửa lỗi parity triển khai, không phải calibration, proof review độc lập
hay bằng chứng xác suất/hardware. Hash PR02 trong claim--evidence matrix đã
được cập nhật. Không protocol nào được promote.

### Hardware-literature refresh — 2026-08-13 01:12 UTC

Vendor/platform checks for Astra-S/OpenNI2, Jetson Orin Nano, Raspberry Pi 4
and the N10/N10P serial family were recorded in the linked Obsidian screening
note. They do not admit hardware evidence: exact unit identity, firmware/SDK
branch, N10P revision/baud, ARM64 runtime fingerprint, calibration and measured
serial/CAN availability remain PR30 gates. PR30 remains `REVIEWED` with
admission `BLOCKED`.

### Hardware-entry recheck — 2026-08-13 02:14 UTC

`validate_hardware_entry.py` returned static `PASS` with
`admission_status=BLOCKED`; report SHA-256:
`44588A1246E308CE4E1C54431C90841F10520DD3B2C2F6D14F77CE771838D9D4`.
The active recorder path has no ROS/ROS2 import, but no device was opened and
no physical package was captured.

### Position-state implementation checkpoint — 2026-08-13

The active Python runner and MATLAB entry point now use
`state=[x,y,theta,vx,vy,omega]` with body-velocity commands. Python QA is
`198 passed`; Ruff is `PASS`; MATLAB QA is `72 passed, 0 failed, 0 incomplete`. The fresh
five-replicate development pilot is stored at
`experiments/runs/context-map-position-state-pilot-20260813-v3/` and remains
unregistered development plumbing; no paper claim or hardware evidence is
opened.

### Reset-path checkpoint — 2026-08-13 02:20 UTC

`det_eval.py` và `validate_web_cohort.py` hiện bắt buộc nhận đường dẫn
manifest/model/annotation/output mới; không còn mặc định trỏ tới cohort, model
hoặc run đã purge. Đây chỉ là dọn execution pointer, không tạo dữ liệu hay
evidence mới; PR10 vẫn `RESET-BEFORE-ACQUISITION`.

`176` Python tests, Ruff, `repo_check.py` và `git diff --check` hiện `PASS`.
Đây là software QA; PR30 vẫn chưa có thiết bị hoặc package vật lý.

### Hardware QA refresh — 2026-08-13 02:26 UTC

Full Python QA hiện `178 passed`; direct tests cover N10P profile selection,
OpenNI device-time conversion, color/depth skew rejection and optional camera
timestamp validation in `final_pack.py`. Static PR30 preflight vẫn `PASS` với
`admission_status=BLOCKED`; report SHA-256 mới nhất là
`A207B3D74879F861D47FD7A292301136FF6A86720C2211F7537E46E7031AB984`.
Không mở thiết bị và không tạo physical package.

### N10P baud provenance — 2026-08-13 02:32 UTC

Manual N10 công bố 230400 bps, còn parity driver tham chiếu 460800. Template
đã chuyển `lidar.baudrate` thành unresolved; recorder từ chối null/nonpositive
baud trước khi mở serial. Physical config phải bind baud đo từ đúng N10P và
firmware cùng profile `n10p-108b-v1`.

### Learning/control literature refresh — 2026-08-13 02:45 UTC

Google/web screening added model-based RL for uncertain social navigation and
neural chance-constrained MPC under uncontrollable agents. Zotero local
read-only search returned no matching items; both remain screening-only and
were not imported. They further constrain RL/neural MPC/chance learning to
comparator boundaries; the gap remains `PIVOT-EMPIRICAL`.

### PR02 numeric-boundary checkpoint — 2026-08-13

The Python/MATLAB fixed-budget allocator now rejects non-finite logits before
the shifted softmax; the correction is fail-closed finite-precision QA and does
not promote PR02. Full Python QA is `179 passed`; MATLAB `run_tests` is `70
passed, 0 failed, 0 incomplete`; Ruff, `repo_check.py` and `git diff --check`
pass. The MATLAB five-feature `cca.score` remains the
primary simulation context score; the Python map runner's simpler
proximity/closing proxy is context-only and is not treated as a theory-parity
or paper result. PR02 remains `PROOF-DRAFT`, and PR30 remains
`REVIEWED` with admission `BLOCKED`.

### PR10 acquisition checkpoint — 2026-08-13 03:03 UTC

A new four-asset Wikimedia Commons cohort is stored under
`data/raw/web_cohort_20260813/` with manifest and annotation scaffold under
`data/manifests/`. Structural preflight is `PASS` (schema, hash, decode,
dimensions, binding, rights/privacy fields and source-group disjointness), but
`admission_status=BLOCKED` and `approved_count=0`. The scaffold has no
independent annotator/adjudicator and its empty person lists are not ground
truth. No detector/model/metric was run; PR10 is an acquiring candidate with
admission blocked.

### Hardware-entry recheck — 2026-08-13 00:57 UTC

`validate_hardware_entry.py` trả về `PASS` cho static no-ROS interface nhưng
`admission_status=BLOCKED`. Report SHA-256 là
`D7D607D571B1D170890D514A022843738390F9F4700C89B620489229AE47F3B1`.
Không mở thiết bị và không gửi lệnh chuyển động; PR30 vẫn chỉ là design review
cho đến khi có thông số robot, calibration, stage approval và package trực tiếp
được niêm phong.

### PR10 preflight refresh — 2026-08-13 03:14 UTC

The same candidate manifest was rechecked after the protocol-ledger update.
Structural `status=PASS` and `admission_status=BLOCKED` are unchanged; the
report SHA-256 is
`C03A0AC1D79E5CB0C07510EECD4BE7BB9242C930FD20F66D3B1FB0D9F17240D5`.
There are still four assets, zero approved records, no independent
annotator/adjudicator, no detector inference and no metric result.

### PR30 direct STM bridge position-state checkpoint — 2026-08-13

The direct recorder now mirrors the legacy STM32 serial bridge with tested
11-byte body-velocity commands and 24-byte telemetry decoding, while retaining
the optional CCA CAN transport. The mini-Mecanum URDF wheel spans are parsed and
checked whenever `urdf_path` is declared. A nonzero command requires a monotonic
command CSV and explicit `--allow-actuation`; otherwise only zero velocity is
sent. No device or command schedule was executed. Static PR30 preflight remains
`PASS`/`BLOCKED`; report SHA-256 is
`7BE114E7C242A4F35368E6DF418E49A8A180FF2988C9323EBC6F9CCAF7B0F28C`.

The physical-data packager now rejects `wheel_torque` when the capture source
is `hardware`, `hardware_in_loop` or `real_offline`; only the body-velocity
position-state interface can label a physical package. The regenerated static
preflight remains `PASS`/`BLOCKED` with report SHA-256
`CA9217115937DC4C5D22DF9DE701A6FC37D7DA58D70AF667073F56009010D971`.

### PR10 real-image diagnostic checkpoint — 2026-08-13 05:45 UTC

The four-image Wikimedia candidate was relabelled at the image-presence level
before inference (three positive, one negative) and revalidated. Structural
preflight remains `PASS`, while admission remains `BLOCKED`; report SHA-256 is
`A74E742609D4CE8E9D3902BACBBF390A770BF830BC4FCF6EB43806ECF4448131`. The
official `yolo26s-pose.pt` candidate (SHA-256
`A083ADB42303728AE14C4BD6BD56D80DA46F82FB2564DBD6F31DCC92EA321646`) was run
on CPU through `det_eval.py`; its retained candidate output is
`experiments/runs/person-detection-web-pilot-20260813/`. At confidence 0.25,
the image-level matrix is `[[1,0],[1,2]]`; P50/P95/max latency is
307.8/608.6/648.6 ms. This is diagnostic plumbing only: no blind bbox AP,
independent adjudication, contamination review or cohort expansion is present,
so no detector metric is admissible for a claim.

### PR10 refresh cohort checkpoint — 2026-08-13

Two additional real Wikimedia assets were acquired under the separate refresh
manifest `data/manifests/web_person_cohort_refresh_20260813.json`. Structural
preflight is `PASS`, but admission remains `BLOCKED`: the two records are not
approved, primary boxes are pending, independent annotation/adjudication and
pretraining-overlap review are absent, and the cohort is too small for an
ID/OOD holdout. Further category requests returned HTTP 429 and are recorded as
an acquisition limitation. The two-image YOLO26s-pose result is descriptive
only (no negative class or blind boxes, so specificity/localization cannot be
estimated). The moving-person rule is unchanged: only CCA-NMPC may use an
internal causal future-position estimate; no future human path is exported or
drawn.

### Position-state CCA covariance checkpoint — 2026-08-13

The active position-state CCA branch now applies a fixed-budget normal
quantile to the predicted covariance projected along the robot--person normal.
The change is limited to `PositionStateNmpc._risk_adjustment`; MPC, NMPC, DWA
and MPPI remain current-observation baselines. The internal CCA prediction is
not written to image, CSV or JSON path fields, and global-path geometry remains
fixed while only the local robot path may be regenerated.

The new covariance-margin regression test and the full Python suite pass (`207`
tests); MATLAB remains `72 passed, 0 failed, 0 incomplete`, with Ruff and
repository validation passing. This updates implementation status only; PR02
stays `PROOF-DRAFT`, PR21 stays `REVIEWED`, and PR30 hardware admission remains
`BLOCKED` because no Astra-S/N10P/STM device was present on the host.

### Pilot v8 LSTM failure checkpoint — 2026-08-13

The fresh five-replicate moving-person map run loaded the external NavWareSet
LSTM candidate inside CCA-NMPC. It recorded 10/15 CCA-NMPC collision episodes
and safe completion `0.333`; the checkpoint was `calibration.status=not_fit`
with no independent ID/OOD holdout. The run is retained only as failure
analysis. Confirmatory map and online hardware CCA now fail closed unless the
checkpoint has an independently fitted calibration split; no protocol status
or paper claim is promoted by this run.

### Pilot v9 OOD-bound recheck — 2026-08-13

The candidate LSTM output exceeded the frozen `max_speed_mps=2.0` context
bound, so CCA-NMPC rejected it and used the current observed velocity. The
same 15 paired units then produced `0/15` CCA-NMPC collision episodes and
minimum context margin `0.0875 m`. This is a fail-closed implementation
recheck only; the checkpoint remains uncalibrated and no confirmatory or
hardware status is promoted.

### Position-state MATLAB export correction — 2026-08-14

The default MATLAB study path now exports the active six-state/body-velocity
contract without requiring the legacy compatibility torque studies. The
position export contains the state columns
`x,y,theta,vx,vy,omega`, the command columns
`vx_cmd,vy_cmd,wz_cmd`, and a hashed candidate manifest. The compatibility
Gate-A exporter remains opt-in and is not the physical position-state path.

The focused export test and complete MATLAB suite pass (`73 passed, 0 failed,
0 incomplete`). Python QA is `214 passed`; Ruff, repository validation and
`git diff --check` pass. This updates host software status only. No simulation
result is promoted, no protocol is advanced, no device is opened, and PR30
admission remains `BLOCKED`.

### PR30 runtime geometry provenance checkpoint — 2026-08-14

The direct recorder now verifies and writes the selected URDF source, URDF/xacro hashes,
wheel radius and wheel spans, and the mesh-derived footprint into the adjacent
`capture.json` sidecar. The CSV/map payload remains unchanged, while a future
physical capture can be traced to the exact robot geometry loaded before device
access. Static preflight remains `PASS` with admission `BLOCKED`; the current
report SHA-256 is
`909D652DEC602CEA1490EF24FCA4ADD192F45462140B3DA66E93292CB2ECF85D`.
The full Python suite remains green (`222` collected), but no device was opened
and no hardware evidence was created. PR30 status remains `REVIEWED`.

### PR30 no-device operator preflight — 2026-08-14

`hardware_entry.py preflight` now validates the prepared runtime config,
URDF/Xacro hashes, calibration, map, ARM64 YOLO26s-pose TensorRT manifest,
optional LSTM path, schedule and empty output directories without opening a
device. `record` repeats this validation before device access. The regenerated
static report SHA-256 is
`53132D9ADB67E2CCC49C45D24FB84843910BBA82DCDB330FDAE35D1462AF340B`;
the Python suite contains 224 tests, and PR30 admission remains `BLOCKED`.

### PR30 motion safety-record gate — 2026-08-14

The direct full recorder and `hardware_entry.py` now require a validated
`--safety-record` whenever motion is requested. The record must confirm
approval, emergency stop, remote disable and watchdog; the no-device preflight
checks it before device access and runtime metadata stores its path and hash.
The static report remains `PASS/BLOCKED`; no device or hardware package was
created. The current Python regression suite passes 239 tests.

### Shared context-score parity correction — 2026-08-14

The active map runner now uses the shared five-feature logistic context score
for CCA prediction, matching the Python scorer and MATLAB definition. The
former proximity/closing-only proxy is removed; a horizon-level regression
test covers the parity. This is a software consistency update only and does
not admit simulation, calibration or hardware evidence.

### Position-state candidate-rollout checkpoint — 2026-08-14 correction

The active implementation is the compiled C++ bounded candidate rollout, not a
finite-horizon multiple-shooting solver. It uses six-state dynamics,
body-velocity commands, validated nominal robot geometry and a reduced CCA risk
correction, then clips and rolls out the command. The reserved
`maximum_risk_slack_m=0` field is not an optimized slack and no nonlinear
program residual is exposed. The direct hardware adapter uses the same
five-feature context score. Host QA is green; this checkpoint does not admit
simulation or physical evidence.

### Frozen prediction geometry parity — 2026-08-14

The candidate rollout now uses the `nominal_robot_xy` carried by the CCA
prediction when forming reduced-risk geometry and rejects malformed input
before command generation. The regression and full Python suite pass. This
does not promote a simulation result, calibration, timing result, or physical
capture; PR02 and PR30 remain open/blocked at their existing evidence gates.

### Clean-reset purge — 2026-08-14

All retained candidate/development payloads were physically removed after an
exact-path inventory: 55 files and 59,260,346 bytes covering web media and
manifests, NavWareSet data, development map runs, detector/LSTM outputs,
YOLO26s-pose weights and generated preflight output. Dataset, model,
experiment and artifact registries are empty. The provenance-only record is
`research/metadata/development-purge-20260814.json`; no paper or backup file
was edited.

Post-reset host QA: Python `228` tests passed; MATLAB R2025a `74` passed with
zero failures/incomplete cases; Ruff, repository validation and
`git diff --check` are `PASS`. No dataset, model, simulation result or physical
capture was created by these checks.

### PR30 direct STM and physical-spec correction — 2026-08-14

`stm_experiment.py` is now the staged direct STM32 serial recorder. It reuses
the legacy 11-byte body-velocity command and 24-byte telemetry frame, writes
the six-state CSV/control/events package plus hash-bound metadata, and sends a
zero command on normal exit, interruption or serial failure. It has no ROS
runtime dependency. Nonzero motion requires an explicit actuation flag and an
H0 safety record.

The current `rai_robot_urdf` intake is CAD/reference-only. Runtime dimensions,
wheel signs and footprint are accepted only from a separate measured
`cca-physical-robot-v1` record; a pending or unlabelled geometry config is
rejected before device access. No device or physical dataset is present, so
PR30 remains `REVIEWED` with hardware admission `BLOCKED`.

### PR10 new candidate cohort and model gate — 2026-08-14

Seven real Wikimedia images were acquired under the new cohort ID and passed
manifest-only hash/decode/rights checks. The official YOLO26s-pose checkpoint
was downloaded as a separate external measurement interface and returned the
required 17-keypoint tensor on all seven images in a CPU sanity check. No
annotation, detector metric, confusion matrix, LSTM overlay or target-device
timing was generated. PR10 remains `CANDIDATE-ACQUIRED / BLOCKED` until blind
annotation/adjudication, privacy/legal review, pretraining-overlap review and
held-out expansion are complete. The model registry remains empty by design.

### Runtime consolidation — 2026-08-14

The active implementation was reduced to one controller boundary. The C++
runtime in `src/control` owns position-state control, transport, and the
compiled C ABI; Python `runtime/controller.py` only marshals arrays and
records outputs. Obsolete Python torque NMPC, torque EKF, torque supervisor,
and duplicate risk-controller modules were removed. `src/hardware.py`,
`src/shared.py`, and `src/repository.py` remain because they are shared
hardware/protocol/provenance gates, not alternate controllers. The former
`src/ros2` tree was moved to the read-only `reference/robot` snapshot; no ROS
process is started. C++ CTest, STM host tests, full Python tests, Ruff, and
repository validation pass. This is structural/software QA only; no dataset,
simulation result, or physical evidence is admitted.

### PR30 no-device preflight refresh — 2026-08-14

`validate_hardware_entry.py` was rerun after the source-layout consolidation.
The refreshed report is
`research/metadata/hardware/pr30_entry_preflight_20260814_current.json` with
SHA-256
`7F9DF16FB7EA6B7DD6C4D0A7E7EDB82575F2B5E44B11C53756B90517EC43D49A`.
Interface checks remain `PASS`; hardware admission remains `BLOCKED` because no
target device, independent dimensional/sensor calibration, safety approval, or
sealed direct CSV/JSON package is present. The user-supplied physical
specification is recorded but not independently verified. This refresh does not
change any paper content or evidence status.

### PR20/PR21 bounded position-state run — 2026-08-14 (purged)

A fresh MATLAB package was generated at
`experiments/runs/simulation-position-state-20260814/` using the five locked
controller labels (MPC, NMPC, DWA, MPPI and CCA-NMPC) and four set-point
scenarios. The manifest SHA-256 is
`EAEAD8F27ADA0E26673B68C670F1860C6DEC745F37C6EFEFFC0F382431614B6C` and the
summary SHA-256 is
`C008D53E013BCDD3C82477D2A3B441EFE6A23A1E51F07990C18CBA48D2DF34D3`.
The package was explicitly `candidate-development-only` and was physically
purged before the new learning campaign. Its hashes remain only as historical
provenance; PR20/PR21 remain unpromoted until a frozen confirmatory campaign is
run and independently reviewed.

### Dynamic-map context pilot — 2026-08-14 (purged)

The corrected Python reference-layout adapter was exercised with three
context-change scenarios, three replicates each, and five compiled controller
branches. The global path stayed fixed and the local path was regenerated only
on a context conflict or direction-change trigger. The package is
`experiments/runs/map-context-development-20260814/`; its manifest SHA-256 is
`D13BA2C6F6BFFE5A386673C41E7F46B4BFDE1A2C76ADF7B5B78DBCB9192431EA` and the
episode table SHA-256 is
`122980A51D82A485A5C922E2A79CED62CA49D85D45FD84FDB2196984D68A7E28`.

This is a development-only map diagnostic. It uses the direct direction/speed
adapter because a sealed LSTM checkpoint and calibration sidecar are absent;
`human_trajectory_generated=false`, `human_trajectory_provided_to_controller=false`,
and `human_prediction_overlay=false`. The first same-name package was removed
after a reference-memory-order bug was found; the regression test now checks
the interleaved six-state reference contract. No paper content was edited and
no confirmatory or hardware claim was admitted. The package was physically
purged before the new campaign; see
`research/obsidian/07_Analysis/map-context-development-20260814.md`.

### PR02 internal proof audit — 2026-08-14

An internal consistency audit was added at
research/obsidian/05_Theory/proof-audit-20260814.md. T1--T3 are valid only
for a nonempty frozen active set and finite-precision tolerance; T4 requires
the declared zero-mean projected Gaussian, zero slack, valid residual and
mode-specific or conservative geometry; T5 is a one-solve conditional Boole
bound; T6/P-PS3 remain implementation invariants rather than feasibility or
safety theorems. The audit explicitly keeps PR02=PROOF-DRAFT and records the
notation, sign, geometry, calibration and independent-review gates still open.
It does not edit the manuscript.

### Naming cleanup — 2026-08-14

Active candidate paths were normalized to descriptive names without embedded
run/version suffixes before the reset: models/candidates/yolo26s-pose-candidate.pt,
research/obsidian/07_Analysis/context-map-position-state-pilot-context-lesson.md
and research/obsidian/07_Analysis/context-map-position-state-pilot-fallback-lesson.md.
The model bytes and metadata hashes were rechecked after the rename, then the
candidate payload was purged as part of the next reset. Historical purge logs
may retain superseded identifiers solely for provenance.

### Fresh simulation-learning campaign — 2026-08-14

After the exact reset recorded in
`research/metadata/simulation-reset-20260814.json`, a new campaign was run at
`experiments/runs/simulation-learning-20260814/`. It generated 9,600
simulation-only current-context rows in 40 episode groups, froze disjoint
train/validation/calibration/test-ID/test-OOD partitions, trained the LSTM from
scratch with five self-supervised score-loop seeds and an independent
temperature calibration, learned a local-path policy with tabular Q-learning
and explicit reward/penalty terms, then ran the paired Python map benchmark.
The root manifest is marked `candidate-development-only` and binds the model,
calibration, split, RL policy and Python benchmark by SHA-256. Test-ID/test-OOD
self-supervised scores were `0.837`/`0.792`; the RL rolling score remained
`0.859`. No real image or hardware device was used. PR10, PR12, PR20 and PR21
therefore remain open for real-data, confirmatory and independent-review gates.

### MATLAB bounded position-state run — 2026-08-14

A separate fresh MATLAB bounded export was executed at
`experiments/runs/matlab-position-learning-20260814/` for MPC, NMPC, DWA, MPPI
and CCA-NMPC across `x`, `y`, `diagonal` and `yaw` scenarios. Its manifest is
`candidate-development-only`, uses the six-state/body-velocity contract and
records `hardwareValidated=false`. It is a development comparator, not a
confirmatory PR20/PR21 result; its artifact hashes are retained for later audit.

### Extended development benchmark — 2026-08-14

The same calibrated simulation-trained LSTM and score/penalty Q-learning policy
were run on a separate ten-replicate Python map campaign, giving 30
replicate-by-scenario units at
`experiments/runs/simulation-benchmark-400mm-20260814/`. The global path was
held fixed, local regeneration remained trigger-only, and `--no-score-tune`
made the selected policy immutable. The run is bound to the current user-
supplied 400 x 400 mm footprint and its physical-spec hash. The manifest is
`completed-development-map-context`, not confirmatory; no PR20/PR21 freeze,
real capture or hardware calibration provenance was supplied.

The descriptive aggregate was MPC `19/30` collisions; NMPC `20/30`; DWA
`12/30`; MPPI `10/30`; and CCA-NMPC `0/30` with safe completion `0.667` and
minimum context margin `0.2194 m`. These values remain candidate development
diagnostics and are excluded from the claim register.

### PR10 fresh real-image diagnostic — 2026-08-14

After the simulation reset, seven real Wikimedia Commons images were acquired
at `data/raw/web-cohort-20260814/`. Manifest-only validation is `PASS` with
seven unique real non-AI records, valid rights/privacy fields and zero approved
records; the preflight report is
`research/metadata/pr10-web-cohort-preflight-20260814.json` and admission is
`BLOCKED`.

The official `yolo26s-pose.pt` checkpoint (SHA-256
`A083ADB42303728AE14C4BD6BD56D80DA46F82FB2564DBD6F31DCC92EA321646`) was run
on CPU. The diagnostic package is
`experiments/runs/person-web-inference-20260814/inference/`; its descriptive
scene-tag image-level matrix is `[[2,0],[0,5]]` at confidence `0.25`, with
P50/P95/max latency `313.43/505.37/544.43 ms`. It is not blind annotation or
detector evidence. Each gallery image displays the local LSTM checkpoint path
with `context=not-provided`; no human future trajectory or robot local path is
drawn. Independent annotation, adjudication, privacy/ethics, overlap review
and held-out expansion remain mandatory before PR10 can advance.

### Literature boundary refresh — 2026-08-14

The latest Google/Google-Scholar-oriented pass screened a learning-based social
navigation benchmark review, uncertainty-aware social MPC, online risk
adaptation, deep-residual MPC with hardware trials and social-force NMPC. The
linked knowledge record is
`research/obsidian/03_Literature/Sources/source-social-navigation-refresh-20260814.md`.
It further rejects standalone novelty claims for RL, LSTM--MPC integration,
risk adaptation and benchmark construction. Read-only Zotero matching found
Akhtyamov (`PTJ74J2E`) and Sun (`HSR6VLIH`); no unverified record was imported.
This refresh changes no protocol status and does not admit any result.

### PR30 operator-console implementation — 2026-08-15

`scripts/python/tools/robot_console.py` now provides the single Jetson service
and laptop operator surface for STM32, N10P, Astra-S preview, 2-D/3-D sensor
display, teleoperation, watchdog, and map/data saving. Static self-test,
repository contracts, and the Python test suite pass. PR30 remains
`REVIEWED` with hardware admission `BLOCKED`: no device was opened and no
physical capture package was created in this implementation step.
