---
type: proof-obligations
status: active
evidence_status: unknown
---

# Nghĩa vụ chứng minh

Các ID `PO-NNN` là canonical và phải giữ nguyên nghĩa trong PR02, claim matrix
và mọi note chứng minh.

| ID | Nghĩa vụ | Điều kiện đóng | Trạng thái |
|---|---|---|---|
| PO-001 | Xác nhận scalar Gaussian surrogate nội tại và containment hình học. | Derivation đúng dấu cho $\sigma>0$ và $\sigma=0$; $d_{\mathrm{req},em}$ gồm support robot/human, braking, margin; hướng/support phải mode-specific hoặc orientation-invariant bảo thủ; test $C_e\subseteq V_e^{\mathrm{hs}}$ và parity với implementation. | Python mode-specific yaw đã sửa và focused regression pass; geometry containment/replay/physical validation còn mở |
| PO-002 | Xác nhận predictive-mode partition đầy đủ. | Định nghĩa $Z_e$ dưới $\Pr_{\mathrm{model}}(\cdot\mid\mathcal F_k)$; các mode loại trừ nhau/vét hết, tổng probability bằng một, omitted mass bằng không và cùng conditional allowance; paper head/loss phải đúng mixture implementation. | static implementation pass; paper parity đang sửa; runtime test/evidence mở |
| PO-003 | Xác lập hiệu chuẩn để claim trên $\Pr_\star$. | Calibration split độc lập; one-sided projected residual; mọi mode, horizon/context strata, ID/OOD; calibration hash/domain và one-sided tail CI/sample support tại allowance kể cả floor. Radial/top-mode/`valid` coverage không đủ. | mở; chặn mọi operational probability claim |
| PO-004 | Đo/chặn hành vi khi active set thay đổi. | Thiết kế hysteresis/smoothing + stress test gián đoạn. | mở |
| PO-005 | Recursive feasibility của controller thật. | Chỉ mở lại qua amendment với mô hình Markov đã gồm actuator lag/delay của lệnh vận tốc, $w_k$ bị chặn và terminal shifted-candidate proof. | held; CLM-T-03 withdrawn |
| PO-006 | Ổn định vòng kín/ISS của controller thật. | Chỉ mở lại qua amendment với cùng model alignment, Lyapunov/ISS domain và terminal ingredients. | held; CLM-T-03 withdrawn |
| PO-007 | An toàn fallback. | Supervisor model, invariant set/reachability và giả thiết latency. | mở |
| PO-008 | Semantics xác suất theo thời gian. | Điều kiện theo $\mathcal F_k$; tham số đóng băng; phân biệt open-loop one-solve, update kế tiếp, closed-loop và mission risk. | đặc tả; implementation audit mở |
| PO-009 | Độ trung thực model/actuator. | Identification và validation held-out; actuator lag, command delay của body velocity và miền $w_k$ phải xuất hiện đúng trong model dùng cho claim. | mở; chặn CLM-T-03 |
| PO-010 | Hiệu lực và ý nghĩa đơn điệu của context score. | Khóa năm feature `proximity/closing/CPA-time/crossing/density`, normalization, logistic scorer, isotonic calibration, nominal/reference path đóng băng, max-mode aggregation, độ nhạy và counterfactual test; Python/C++ phải có golden-vector parity. | Python/C++ formula now aligned statically; build, golden vectors, calibration and counterfactual evidence còn mở |
| PO-011 | Ảnh hưởng của solver inexactness/slack. | Nếu dùng solver tối ưu đầy đủ thì phải log residual/tolerance/slack và xử lý infeasibility; claim xác suất chỉ khi mọi slack bằng không và residual đạt tolerance bảo thủ đã khóa. | Current C++ candidate rollout validates `nominal_robot_xy`, reports reduced violation/deadline fields and reserves `maximum_risk_slack_m=0`; no optimized slack or solver residual exists, so chance eligibility and physical deadline evidence remain open |
| PO-012 | Lan truyền lỗi detector/tracker. | Versioned YOLO26s-pose contract, model/calibration/domain hash, ảnh Internet thật, injected-error study và đánh giá lan truyền box/keypoint/track error tới LSTM--CCA--NMPC. | plan-only; code vẫn detection-only |
| PO-013 | Covariance tương đối. | Truy vết $\Sigma^h,\Sigma^r,\Sigma^{hr}$ theo horizon, test PSD/frame/time, provenance và ablation giả thiết independence. | Python position-state path now rejects non-finite, asymmetric and materially non-PSD covariance before a chance row; provenance/frame/time, MATLAB parity and physical validation remain open |
| PO-014 | Bảo toàn budget, thứ tự context và continuity khi active set cố định. | Derivation tổng allocation bằng $\bar\varepsilon$, miền floor, thứ tự khi $\beta>0$, uniform khi $\beta=0$, continuity cố định active set và property test số học. | PASS-STATIC trong Python/MATLAB suites; evidence hash và review độc lập vẫn mở |
| PO-015 | Cận mixture và cận Boole nội tại. | Từ partition A-04 và cận T4 hợp lệ cho mọi mode, chứng minh bằng xác suất toàn phần rồi Boole dưới $\Pr_{\mathrm{model}}(\cdot\mid\mathcal F_k)$; paper dùng mixture notation/NLL và nêu đúng phạm vi one-solve. | derivation + static full-mode runtime pass; paper/calibration/runtime evidence mở |
| PO-016 | Parity và causal boundary của LSTM context interface. | Recurrence chỉ nhận cửa sổ history đã có trước update; đầu ra là velocity/speed/direction score; không có future-position decoder, human-path artifact hoặc hướng dẫn thủ công trong loss; source/test parity với `ctx_lstm.py`. | recurrence/interface notation và leakage guards đã ghi; checkpoint, ID/OOD metrics, calibration và target-hardware timing còn mở |

## Ánh xạ claim--mệnh đề--nghĩa vụ

| Claim | Mệnh đề hợp đồng | Nghĩa vụ bắt buộc | Trạng thái admission |
|---|---|---|---|
| CLM-T-01 | T1--T3 | PO-014 | blocked; không phải novelty |
| CLM-T-02 | T4, chỉ $\Pr_{\mathrm{model}}$ | PO-001, PO-011, PO-013; thêm PO-003 nếu nói về $\Pr_\star$ | blocked |
| CLM-T-04 | T5, chỉ open-loop one-solve | PO-002, PO-008, PO-015; thêm PO-003 nếu nói về $\Pr_\star$ | blocked |
| CLM-T-03 | không có mệnh đề đang theo đuổi | PO-005, PO-006, PO-009 | withdrawn/held |
| CLM-EMP-02 | không phải theorem | PR20/PR21/PR30/PR40: solve status, fallback, constraints, tracking, CI | blocked |

## Chính sách luận điểm

T1--T5 chỉ là mệnh đề hợp đồng sơ cấp và không được trình bày như novelty lý
thuyết. Không được suy PO-005--PO-007 từ collision-rate trong mô phỏng. Nếu thiếu
bất kỳ bằng chứng nào của PO-001--PO-003, PO-008, PO-011, PO-013 hoặc PO-015,
claim xác suất tương ứng fail closed: chỉ được gọi là deterministic/model-internal
surrogate. Nghĩa vụ chưa đóng phải xuất hiện ở [[01_Governance/limitations]] và
phần giới hạn trên Overleaf.

Related hub: [[00_MOC/project-map]]
## Checkpoint P-PS3 — 2026-08-14

The compiled candidate rollout consumes the nominal robot geometry carried by
the CCA prediction rather than reconstructing it from the reference path. A
malformed or incomplete nominal sequence fails closed before command
generation. The regression covers the frozen-row normal, and the hardware event
schema preserves status, iteration count, reduced violation, deadline and the
reserved risk-slack field. This closes the provenance mismatch only; no direct
nonlinear-program solver, optimized slack, residual certificate or chance-row
eligibility is implemented, so PO-011 remains open.
