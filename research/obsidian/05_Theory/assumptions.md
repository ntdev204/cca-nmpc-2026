---
type: theory-assumptions
status: draft
evidence_status: unknown
inheritance: legacy-hypothesis-reverify
---

# Các giả thiết

Giả thiết là điều kiện phạm vi, không phải sự thật mặc định. Mỗi giả thiết phải
liên kết tới test, báo cáo identification hoặc giới hạn trước khi duyệt luận điểm.
Các ID `A-NN` là canonical và phải giữ nguyên nghĩa trong PR02, claim matrix và
mọi note chứng minh.

## Giả thiết toán học

- **A-01 — tập hữu hạn:** Ở mỗi lần cập nhật, tập nhóm $\mathcal E_k$ gồm các cặp $e=(h,\ell)$ là hữu hạn và $M\ge1$.
- **A-02 — miền ngân sách hợp lệ:** $0\le\varepsilon_{\min}<\bar\varepsilon/M$ và $0<\bar\varepsilon<0.5$.
- **A-03 — ngữ cảnh và độ nhạy hữu hạn:** Mỗi $c_e\in[0,1]$ và $\beta\in[0,\infty)$ là hữu hạn. Context dùng năm feature proximity, closing, CPA-time, crossing geometry và density; scorer/calibration được khóa trước, tính trên quỹ đạo robot nominal/reference đóng băng và lấy maximum qua mọi mode được giữ lại. Không dùng nhãn test.
- **A-04 — partition dự báo đa mode đầy đủ:** Tại lần cập nhật $k$, $Z_e$ là biến ngẫu nhiên rời rạc dưới $\Pr_{\mathrm{model}}(\cdot\mid\mathcal F_k)$; các biến cố $\{Z_e=m\}$ loại trừ nhau, vét hết không gian dự báo, mọi mode có $\pi_{em}>0$ được giữ lại, $\pi_{em}=\Pr_{\mathrm{model}}(Z_e=m\mid\mathcal F_k)$, $\sum_m\pi_{em}=1$ và omitted mass bằng không.
- **A-05 — mô hình chiếu có điều kiện:** Với từng mode, $n_{em}^\top\delta_{em}$ dưới $\Pr_{\mathrm{model}}(\cdot\mid Z_e=m,\mathcal F_k)$ là Gaussian zero-mean với phương sai $\sigma_{em}^2=n_{em}^\top\Sigma^{\mathrm{rel}}_{em}n_{em}$. Đây chỉ là giả thiết của mô hình nội tại, không phải phát biểu về $\Pr_\star$.
- **A-06 — hiệu chuẩn vận hành độc lập:** Muốn chuyển từ $\Pr_{\mathrm{model}}$ sang claim trên $\Pr_\star$, one-sided projected residual phải được calibration trên split độc lập với validation/test, dùng tất cả mode, và đạt cận đuôi đã khóa theo horizon, context, ID/OOD cùng bằng chứng sample-size/tail support. Training loss, radial Mahalanobis coverage hoặc top-mode coverage không đủ.
- **A-07 — covariance tương đối đúng:** $\Sigma^{\mathrm{rel}}_{em}=\Sigma^h_{em}+\Sigma^r_{em}-\Sigma^{hr}_{em}-(\Sigma^{hr}_{em})^\top$ là hữu hạn, đối xứng, PSD và horizon-indexed.
- **A-08 — phạm vi open-loop một lần solve:** $\mathcal F_k$, tập nhóm/mode, context, probability, direction, geometry và covariance được đóng băng trong một solve. Mệnh đề không bao phủ update $k+1$, switching closed-loop hoặc mission risk.
- **A-09 — tính chính quy của mô hình danh định:** $f_d$ xác định, liên tục và locally Lipschitz trên miền state/input được thử; điều này không tự bao phủ actuator lag, command delay hoặc disturbance thật.
- **A-10 — snapshot đồng bộ:** State, track, LSTM và context dùng cùng frame/update với tuổi dữ liệu bị chặn. Observation age là freshness gate, không phải một context feature.
- **A-15 — alignment với actuator:** Các tập state/input và giới hạn body-velocity là đúng, không rỗng và nhất quán với cấu hình đã băm. Nếu plant/controller có actuator lag hoặc command delay, các trạng thái/history đó phải xuất hiện trong mô hình Markov dùng cho proof; $w_k$ phải có miền bị chặn được xác minh.
- **A-16 — terminal construction chưa có:** Terminal set/controller và shifted feasible candidate phải được chứng minh cho đúng mô hình đã gồm actuator lag/delay, constraints và disturbance. Dự án hiện không giả định A-16 và không theo đuổi claim recursive feasibility/stability nếu chưa có amendment.
- **A-17 — containment hình học:** Clearance $d_{\mathrm{req},em}$ gồm support footprint robot, support ellipse người theo $n_{em}$, quãng phanh và margin đã khóa; hình học/hướng người phải riêng cho từng mode hoặc dùng support orientation-invariant bảo thủ. Phép dựng phải bảo đảm $C_e\subseteq V_e^{\mathrm{hs}}$ theo mọi nhánh mode và khớp implementation. Runtime dùng yaw top-mode chung cho mọi mode chưa thỏa giả thiết này.

## Giả thiết đánh giá

- **A-11 — so sánh ghép cặp:** Baseline dùng cùng plant, phép đo, người, map/path, định nghĩa va chạm, seed và quy tắc báo thời gian tính.
- **A-12 — mẫu số đầy đủ:** Va chạm, solver failure, timeout, fallback và lần chạy không hoàn tất đều nằm trong mẫu số.
- **A-13 — split độc lập:** Các partition tách theo subject, scene, source và near-duplicate khi phù hợp.
- **A-14 — ranh giới đo lường:** Detector/YOLO chỉ tạo phép đo; LSTM chỉ tạo dự báo; chỉ NMPC được phát lệnh body velocity cho mục tiêu bám vị trí.

## Không giả định

Không giả định recursive feasibility, ổn định vòng kín, xác suất va chạm joint
chính xác, detector hoàn hảo, mode LSTM đúng, hard real-time hay an toàn robot
vật lý. Với controller hiện tại, claim analytic về recursive feasibility/stability
được giữ ngoài phạm vi; chỉ báo các đại lượng feasibility/fallback/tracking đo
được. Nếu A-04--A-08, A-17, calibration hash/domain hoặc implementation parity
không được xác minh, mọi claim xác suất trên $\Pr_\star$ phải **fail closed**.

## Related notes

[[00_MOC/project-map]] · [[05_Theory/system-model]] · [[05_Theory/theorems]]
