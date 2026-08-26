# PR50 — Đóng băng bằng chứng, phát hành và cổng phản biện Q1

> **Trạng thái goal hiện tại:** `DEFERRED — OUTSIDE CURRENT GOAL`.  
> **Trạng thái lưu vết:** `DRAFT-DESIGN`; không được phát hành như completed evidence.  
> **Điều kiện vào:** với profile `comprehensive_q1`, PR00, PR02, PR10,
> PR11, PR12, PR20, PR21, PR30 và PR40 đều phải `VERIFIED`. `NOT RUN` không
> phải đường thoát. Chỉ một scope amendment do chủ nhiệm nghiên cứu duyệt trước
> khi mở holdout mới được đổi profile; khi đó title/abstract/conclusion và claim
> matrix phải hạ scope tương ứng.

## 1. Release inventory

Mỗi release có version/tag, UTC timestamp và immutable manifest bao gồm:

- protocol versions/hashes và amendment/deviation ledger;
- code commit, dirty-state report, environment/container lock và hardware;
- raw/processed dataset manifests, source URLs, licenses/consent và split hashes;
- model configs, training seeds/logs, first/best/last checkpoints và hashes;
- simulation/physical run registry: expected, observed, failed, excluded + reason;
- raw traces, predictions, calibration, statistical tables và figure source data;
- generated overlays/video với parent hashes;
- claim--evidence matrix và known limitations;
- `SHA256SUMS`/machine-readable manifest plus verifier report.

Không xóa run/model xấu trước release. Artifact không được redistrib theo license
chỉ có metadata/hash/retrieval instruction. Dữ liệu người thật tuân thủ consent,
anonymization, access control, retention và takedown.

## 2. Claim--evidence matrix cuối

Mỗi dòng có `claim_id`, exact wording trong Overleaf, evidence tier, protocol,
dataset/model/run IDs, analysis/table/figure IDs, hash, assumptions, limitations
và verifier status. Script kiểm:

- mọi số/CI/n trong Overleaf xuất hiện trong generated table;
- mọi hình truy tới raw trace và script;
- mọi theory claim truy tới PO/assumption ledger;
- simulation/hardware wording đúng tier;
- unsupported row làm release fail, không được điền bằng “TBD”.

## 3. Đồng bộ ba công cụ

- **Overleaf:** nguồn manuscript duy nhất; freeze source/PDF revision ID và hash
  tại review. Không viết/build paper local.
- **Zotero:** collection included đã metadata/DOI audit; export BibTeX hash khớp
  Overleaf và không có citation mồ côi/uncited padding.
- **Obsidian:** snapshot read-only của gap matrix, decision log, preregistration,
  deviations và claim links; loại private/PII notes trước release.

Một sync report ghi revision/hash/thời điểm của cả ba. Thay đổi sau review làm
invalid review và phải tạo release candidate mới.

Tài liệu chính thức gửi giáo sư là LaTeX/PDF tiếng Việt trên Overleaf; note tiếng
Việt trong Obsidian cũng có thể chia sẻ trực tiếp với giáo sư. Markdown ngoài
vault chỉ dùng nội bộ. Chỉ final journal `main.pdf` là tiếng Anh; release manifest
phải ghi rõ document role và language để không đồng bộ nhầm.

## 4. Independent verification

Verifier không phải người tạo artifact chính thực hiện:

1. checksum và schema validation;
2. split leakage/dedup/license audit;
3. rerun sample training/inference và full analysis khi khả thi;
4. đối chiếu expected/observed failures;
5. tái sinh tables/figures/overlays;
6. kiểm target-hardware timing provenance;
7. tìm selective reporting và claim vượt evidence.

Sai số phải sửa ở nguồn rồi tái sinh toàn chuỗi; không sửa số trực tiếp trong
Overleaf.

## 5. Cổng `q1-reviewer-ee` bắt buộc

Chạy skill trên **toàn bộ manuscript Overleaf đã freeze + supplement + evidence
release**, không chỉ abstract. Panel tối thiểu:

- Novelty Skeptic;
- Statistics & Reproducibility Reviewer;
- Control Theory Reviewer;
- Robotics & Systems Integration Reviewer;
- Machine Learning / Deep Learning Reviewer;
- Human-Robot Interaction / Context-Awareness Reviewer;
- Writing, Clarity & Presentation Reviewer nếu notation/presentation ảnh hưởng
  khả năng kiểm chứng.

Báo cáo phải theo đúng format của skill, nêu lý do chọn panel; mỗi reviewer tìm
ít nhất ba weakness cụ thể, kiểm novelty/prior art và cho verdict độc lập. Fatal
flaw gồm proof sai/thiếu assumption, leakage/test contamination, strawman hoặc
unfair baseline, experiment không hỗ trợ central claim, novelty đã tồn tại, hay
mâu thuẫn giữa method và artifact.

Quy tắc quyết định:

- `Reject`: dừng release; sửa thiết kế/chạy lại nếu cần, không chỉ sửa văn phong.
- `Weak Accept`: lập issue ledger, sửa và review lại trên release candidate mới.
- `Accept`: chỉ pass khi không còn fatal/major blocker và mọi yêu cầu đã được
  verify; panel tối thiểu 4/5 Accept/Weak Accept với Novelty Skeptic không bác
  novelty, theo aggregation của skill.

Không ép reviewer thay verdict. Phản biện chỉ được đóng bằng evidence, sửa claim
hoặc thu hẹp scope; mỗi issue ánh xạ commit/Overleaf revision/artifact.

## 6. Release states và publication boundary

- `RC`: nội bộ, chưa phải public result.
- `SUBMISSION-FROZEN`: Q1 gate pass; manuscript/evidence hash bất biến.
- `PUBLIC`: archive có DOI/URL nếu license/ethics cho phép.
- `SUPERSEDED`: giữ truy cập và link version mới, không ghi đè.

Nếu PR30 chưa chạy, abstract/conclusion phải ghi simulation-only. Nếu detector
chỉ được test trên Internet cohort, không claim deployment robustness. Nếu LSTM
OOD/calibration fail, giữ failure và thu hẹp claim. Không dùng “Q1-ready” chỉ vì
format đẹp hoặc test code xanh.

## 7. Checklist phát hành

- [ ] Mọi protocol bắt buộc của `comprehensive_q1` là `VERIFIED`; không có `NOT RUN`.
- [ ] Internet-image person test, real-context LSTM dataset và OOD cohort đã khóa.
- [ ] Detector metrics hợp lệ và context overlay trên frame thật đã verify.
- [ ] PR30 physical experiment và target-hardware timing đã verify.
- [ ] Claim--evidence matrix không có ô trống/overclaim.
- [ ] Dataset/model/run/analysis manifests và SHA-256 đầy đủ.
- [ ] Leakage, license, privacy, ethics và safety audits pass.
- [ ] Baseline/ablation/fair-budget và paired statistics được verify.
- [ ] Confusion matrix chỉ dùng cho classification hợp lệ.
- [ ] Simulation và hardware claims tách rõ.
- [ ] Context overlay có sequence/video, bbox/keypoints, position/speed/direction,
      confidence/validity và provenance; không có human future path.
- [ ] Overleaf--Zotero--Obsidian sync report khớp.
- [ ] Independent reproduction report pass.
- [ ] Final `q1-reviewer-ee` verdict là `Accept`; issue ledger bằng 0 blocker.

Chỉ khi toàn bộ checklist pass mới đổi trạng thái sang `SUBMISSION-FROZEN`.
