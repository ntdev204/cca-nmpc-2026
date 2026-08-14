---
type: source-note
status: included-provisional
evidence_status: full-text
evidence_level: full-text
citekey: ren2025recursive
doi: 10.1109/TCST.2024.3477089
zotero_uri: zotero://select/library/items/PDIZT8XG
verified_date: 2026-08-01
---

# Ren et al. (2025) — Recursive-feasible chance-constrained MPC dưới GMM

## Xác minh thư mục

- Nguồn chính: [IEEE Transactions on Control Systems Technology](https://doi.org/10.1109/TCST.2024.3477089).
- Bản đã đọc: [arXiv 2401.03799v2](https://arxiv.org/abs/2401.03799), trang
  arXiv ghi journal reference vol. 33, no. 4, 2025 và DOI liên quan.
- Metadata/toàn văn đối chiếu ngày 01/08/2026; Zotero item/PDF đã nhập và kiểm;
  correction/retraction và provenance cuối vẫn cần kiểm độc lập trong focused
  audit.

## Bài toán và cơ chế

Bài báo xây ba planner chance-constrained dưới GMM: nominal, robust và
contingency. Nhánh robust siết chance constraints theo giả thiết về thay đổi mean
và covariance giữa hai lần lập kế hoạch, dùng terminal/control-invariant
ingredients và chứng minh recursive feasibility khi bài toán ban đầu khả thi.
Nhánh contingency giảm bảo thủ nhưng chỉ có bảo đảm khi chính planner đó tiếp
tục khả thi.

Risk allowance được giữ đồng đều giữa các mode và không đổi qua planning step
trong proof. Thực nghiệm gồm các kịch bản lái xe mô phỏng, 10 lần mỗi scenario,
predictor đa mode và bảng so sánh nhiều risk formulation; không phải robot
Mecanum hoặc thực nghiệm người thật.

## Phản bằng chứng đối với dự án

Nguồn này là comparator lý thuyết trực tiếp cho CLM-T-03 đã rút. Nó cho thấy
recursive feasibility cần nhiều hơn budget conservation:

- mô hình Markov, terminal construction và invariant set phải khớp plant;
- luật propagation prediction giữa hai solve phải được giả định và kiểm;
- risk parameter dùng trong proof phải nhất quán qua mode/time;
- fallback hoặc nghiệm ở một vài simulation không thể thay thế shifted-candidate
  proof.

Vì CCA thay allowance theo context/active set và controller hiện có actuator
lag/delay/previous torque chưa được đưa đầy đủ vào model proof, dự án không được
mượn kết quả này để claim recursive feasibility. Giá trị còn lại chỉ là empirical
characterization hoặc một amendment lý thuyết riêng trong tương lai.

## Vị trí kiểm chứng

- Sec. III-A--B, Assumptions 1--3, Proposition 1--2: nominal/robust planner,
  transition và recursive-feasibility conditions;
- proof của Proposition 1: allowance/margin giữ cố định giữa planning steps;
- Sec. IV: 10 lần mỗi scenario và so nominal/robust/contingency;
- Appendix A: known-GMM, moment-robust, scenario, CVaR và DR comparison.

## Liên kết

- [[03_Literature/source-index]]
- [[03_Literature/nearest-work-matrix]]
- [[03_Literature/literature-synthesis]]
- [[05_Theory/proof-obligations]]

Related hub: [[00_MOC/project-map]]

