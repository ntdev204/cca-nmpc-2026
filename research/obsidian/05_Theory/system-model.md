---
type: theory-model
status: draft
evidence_status: unknown
inheritance: legacy-hypothesis-reverify
---

# Mô hình hệ thống

## Luồng thông tin

```text
ảnh/depth thật hoặc phép đo mô phỏng
  -> detector/tracker người (giao diện đo snapshot)
  -> LSTM causal (vận tốc/hướng context kế tiếp)
  -> điểm ngữ cảnh và phân bổ ngân sách cố định
  -> CCA-NMPC điều khiển trạng thái vị trí bằng lệnh vận tốc thân
  -> plant Mecanum
```

Không khối upstream nào có quyền phát lệnh cơ cấu chấp hành.

Trong pipeline active, LSTM nhận cửa sổ snapshot hiện tại và trả vận tốc ngữ
cảnh, tốc độ, hướng và độ tin cậy/hiệu lực để CCA tính điểm. Với người động,
CCA-NMPC có thể tích phân vận tốc causal thành chuỗi vị trí tương lai nội bộ
cho chance rows. Chuỗi đó không được lưu thành artifact hoặc vẽ lên ảnh; pilot
direct-adapter không cung cấp ground-truth human path. Các ký hiệu mean,
covariance và mode bên dưới chỉ là compatibility notation cho một mở rộng cần
calibration.

## Dự đoán causal của CCA cho người động

Tại thời điểm \(k\), CCA chỉ dùng snapshot hiện tại \(\hat p^h_k\) và vận tốc
ngữ cảnh \(\hat v^h_k\) đã được kiểm tra từ history causal. Vị trí nội bộ tại
bước \(\ell\) được sinh bằng mô hình giữ vận tốc đơn giản

\[
\hat p^h_{k+\ell|k}=\hat p^h_k+\ell\Delta t\,\hat v^h_k,
\qquad \ell=1,\ldots,N .
\]

Chuỗi này chỉ là biến trung gian của chance rows trong CCA-NMPC. Ground-truth
tương lai không đi vào controller, và predictor không ghi chuỗi này vào
`context.csv`, manifest hoặc ảnh. Khi snapshot không hợp lệ hoặc quá cũ,
CCA không ngoại suy mà chuyển sang policy fallback đã khóa.

## LSTM như giao diện context của CCA

LSTM không phải bộ điều khiển độc lập và không sinh human path. Với cửa sổ
đầu vào chuẩn hóa $z_t$, một cell được viết ở dạng ngắn gọn

$$
\begin{aligned}
 i_t&=\sigma(W_i z_t+U_i h_{t-1}+b_i), &
 f_t&=\sigma(W_f z_t+U_f h_{t-1}+b_f),\\
 o_t&=\sigma(W_o z_t+U_o h_{t-1}+b_o), &
 \tilde c_t&=\tanh(W_c z_t+U_c h_{t-1}+b_c),\\
 c_t&=f_t\odot c_{t-1}+i_t\odot\tilde c_t, &
 h_t&=o_t\odot\tanh(c_t).
\end{aligned}
$$

Chỉ biểu diễn cuối cửa sổ được đưa qua đầu vận tốc

$$
\hat v_k=W_v h_T+b_v,\qquad \hat s_k=\|\hat v_k\|_2.
$$

Các score hướng của bốn trục cố định $a_j$ là

$$
q_{k,j}=\frac{\hat v_k^{\mathsf T}a_j}
{\max(\|\hat v_k\|_2,\delta)}.
$$

Đây là đúng giao diện hiện tại của `ctx_lstm.py`: vận tốc và score được dùng
để tạo snapshot context; không có decoder vị trí, không có nhãn hướng thủ công
trong loss, và không có human-trajectory field trong output.

## Động lực học robot

Dùng hợp đồng rời rạc đơn giản

$$
s_{k+1}=f_d(s_k,u_k)+w_k,
$$

với

$$
s=[x,y,\theta,v_x,v_y,\omega]^\top,\qquad
u=[v_x^{\rm cmd},v_y^{\rm cmd},\omega^{\rm cmd}]^\top.
$$

Đây là mô hình dự báo **danh định**. Với bước lấy mẫu $\Delta t$ và hằng số đáp
ứng $\tau_v$, phần vận tốc dùng cập nhật bậc nhất

$$
v_{k+1}=v_k+\alpha(u_k-v_k),\qquad
\alpha=\operatorname{clip}(\Delta t/\tau_v,0,1),
$$

trong đó $v=[v_x,v_y,\omega]^\top$; pose được tích phân từ vận tốc thân và
ma trận quay theo $\theta_k$. Nếu còn trễ lệnh, trạng thái/history tương ứng
phải được augment tường minh để mô hình dùng cho proof còn Markov. Hiện miền bị
chặn của $w_k$ và alignment này chưa được xác minh, nên các claim analytic đó
được giữ ngoài phạm vi.

Derivation của bound vận tốc và bước dịch chuyển nằm ở
[[05_Theory/position-state-derivation]]. Đây chỉ là invariant của mô hình rời
rạc danh định, không phải chứng minh ổn định hay recursive feasibility.

## Bài toán NMPC — reference formulation

Tại mỗi bước, bài toán tham chiếu của nghiên cứu được viết là

$$
\min_{u_{0:N-1}}\sum_{\ell=0}^{N-1}
\left(\|x_\ell-x_\ell^{\mathrm{ref}}\|_Q^2+
\|u_\ell-u_\ell^{\mathrm{ref}}\|_R^2+
\|u_\ell-u_{\ell-1}\|_S^2\right)
+\rho\|\xi\|_2^2+\|x_N-x_N^{\mathrm{ref}}\|_{Q_f}^2,
$$

với ràng buộc $f_d$, giới hạn vận tốc thân/slew, vật cản tĩnh và chance
surrogate cho người đang hoạt động. Trong primary contrast, cost, model,
reference, clearance và fallback policy được giữ giống nhau giữa mọi allocator.
Đây là formulation mục tiêu của phần lý thuyết; executable C++ hiện tại chưa
giải bài toán nonlinear program này. Nó thực hiện bounded candidate rollout,
CCA projected-risk correction và sampled commands cho DWA/MPPI. Vì vậy mọi
claim về nghiệm tối ưu, residual, slack hay solver convergence đều bị khóa cho
đến khi một solver tương ứng được triển khai và kiểm chứng.

## Hợp đồng hình học và chance surrogate

Với nhóm $e=(h,\ell)$ và mode $m$, định nghĩa clearance tất định đơn giản

$$
d_{\mathrm{req},em}=r_r(n_{em})+r_{h,em}(n_{em})+
d_{\mathrm{brake},\ell}+d_0,
$$

trong đó hai số hạng đầu là support footprint robot và ellipse người theo hướng
$n_{em}$; hai số hạng sau là quãng phanh và margin đã khóa. Các số hạng này
không được trộn với covariance. Phép dựng hình học phải kiểm
$C_e\subseteq V_e^{\mathrm{hs}}$ và khớp đúng code/config trước khi suy cận va
chạm. Chance row là

$$
n_{em}^\top(p_{r,e}^{0}-\mu_{em})+\xi_{em}\ge
d_{\mathrm{req},em}+\Phi^{-1}(1-\varepsilon_e)\sigma_{em},
\qquad
\sigma_{em}=\sqrt{n_{em}^\top\Sigma^{\mathrm{rel}}_{em}n_{em}}.
$$

Với A-04--A-08 và A-17 trong [[05_Theory/assumptions]], slack bằng không và
residual solver hợp lệ, đây là surrogate một chiều cho
$\Pr_{\mathrm{model}}(V_e^{\mathrm{hs}}\mid Z_e=m,\mathcal F_k)
\le\varepsilon_e$. Trường hợp $\sigma_{em}=0$ được xử lý như Gaussian suy biến:
nếu nominal margin không âm thì xác suất vi phạm strict half-space của mô hình
bằng không. Xác suất toàn phần và cận Boole chỉ áp dụng open-loop cho tập nhóm
đã đóng băng trong một solve.

Đây là tính chất **nội tại của mô hình**, không tự chứng nhận xác suất dưới
$\Pr_\star$. Muốn viết claim vận hành phải có calibration một phía độc lập đúng
đuôi $\varepsilon_e$, đầy đủ mode/horizon/context/ID/OOD và đủ tail support.
Thiếu calibration hash/domain, frame/time/age, mode completeness, covariance
provenance, geometry parity, slack hoặc residual thì claim xác suất fail closed.

## Hợp đồng giao diện

- Đầu ra detector/tracker: timestamp, frame, track ID, position, covariance/confidence và nguồn gốc.
- Đầu ra LSTM active: predicted context velocity, speed, direction probabilities,
  calibration ID/hash/domain và tuổi snapshot; không có future-position/path field.
  CCA-NMPC có thể tích phân velocity này thành các điểm dự báo nội bộ cho
  chance rows; các điểm đó không được ghi vào ảnh hoặc xuất như human path.
- Đầu ra LSTM mở rộng (chỉ compatibility notation): mode partition,
  mean/covariance horizon-indexed sau khi đã có calibration và protocol riêng.
- Đầu ra context: điểm bị chặn, quy tắc tổng hợp mode và feature trace; không ghi đè covariance/class confidence.
- Đầu vào NMPC: covariance tương đối horizon-indexed, gồm cross-covariance nếu có; không tự cộng thêm giả thiết độc lập.
- Đầu ra controller: body-velocity command, bounded rollout, reduced-margin
  violation, risk-budget field, reserved slack field, fallback/deadline status
  và timing. `maximum_risk_slack_m=0` hiện là trường dự trữ, không phải slack
  được tối ưu bởi solver.

Mọi chi tiết kiến trúc kế thừa là `legacy hypothesis` cho tới khi được kiểm tra
lại trong implementation thiết kế mới.

Related hub: [[00_MOC/project-map]]
