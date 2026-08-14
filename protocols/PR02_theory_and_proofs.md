# PR02 — Mô hình lý thuyết và protocol chứng minh

> **Trạng thái:** `PROOF-DRAFT`; T1--T5 đã được viết và kiểm cục bộ, nhưng review
> độc lập/parity với implementation vẫn còn mở; các mệnh đề này không phải kết quả
> hay novelty lý thuyết.  
> **Nguyên tắc:** mô hình đủ đơn giản để đọc và kiểm, nhưng không bỏ qua giả định
> cần thiết chỉ để công thức đẹp.

**Biên active-context:** implementation hiện tại nhận snapshot context gồm vị
trí, tốc độ, hướng, confidence và validity. CCA-NMPC có thể tích phân vận tốc
ngữ cảnh thành chuỗi vị trí tương lai nội bộ cho chance rows; chuỗi này không
được ghi vào ảnh, không xuất thành artifact và không phải ground-truth human
trajectory. Implementation không phát mode probabilities. Các ký hiệu
mode/mixture trong những đoạn accounting bên dưới chỉ là compatibility note cho
một amendment được duyệt; chúng không thuộc active code, dataset hay evidence
hiện tại.

## 1. Ký hiệu tối thiểu

Robot có trạng thái

\[
s=[x,y,\theta,v_x,v_y,\omega]^\top,
\]

và input vận tốc thân \(u=[v_x^{\rm cmd},v_y^{\rm cmd},
\omega^{\rm cmd}]^\top\). Mô hình rời rạc là

\[
s_{k+1}=f_d(s_k,u_k)+w_k,
\quad s_k\in\mathcal X,\;u_k\in\mathcal U,
\]

trong đó \(\mathcal X,\mathcal U\) chứa giới hạn pose, vận tốc, slew và tốc độ
bánh; \(w_k\) là sai số mô hình được mô tả trong Assumption ledger. Chi tiết
Mecanum nằm trong một appendix/model spec duy nhất, không lặp nhiều biến thể.

Derivation tối giản cho cập nhật first-order velocity, bound vận tốc và bound
bước dịch chuyển được ghi tại
`research/obsidian/05_Theory/position-state-derivation.md`. Đây là invariant
của mô hình danh định, không đóng PO-005/PO-006 và không tạo claim stability.

Tại update \(k\), ký hiệu \(\mathcal F_k\) là toàn bộ thông tin sẵn có trước
khi solve. Trong phần mở rộng lý thuyết (không phải output của active
pipeline), với người \(h\) và bước dự báo \(\ell\), LSTM có thể được mô tả bằng
biến mode rời rạc \(Z_e\in\mathcal M_e\) cho nhóm \(e=(h,\ell)\), cùng xác suất

\[
\pi_{em}=\Pr_{\mathrm{model}}(Z_e=m\mid\mathcal F_k)>0.
\]

Các biến cố \(\{Z_e=m\}\) phải loại trừ nhau và vét hết không gian của phân phối
dự báo điều kiện; không phải chỉ là danh sách trajectory hypotheses. Mỗi mode có
mean \(\mu_{em}\) và covariance tương đối
\(\Sigma^{\mathrm{rel}}_{em}\), với

\[
\sum_{m\in\mathcal M_e}\pi_{em}=1.
\]

Đơn vị phân bổ là nhóm người--bước, không phải từng mode. Context score
\(c_e\in[0,1]\) được tổng hợp bằng một quy tắc khóa trước
(mặc định: giá trị lớn nhất trên các mode giữ lại) và không phải xác suất va
chạm, covariance, detector confidence hay mode weight. Active implementation
chỉ dùng causal context velocity/direction. Với người động, active CCA dùng mô
hình tối giản

\[
\hat p^h_{k+\ell|k}=\hat p^h_k+\ell\Delta t\,\hat v^h_k,
\qquad \ell=1,\ldots,N,
\]

trong đó \(\hat p^h_k,\hat v^h_k\) là snapshot và vận tốc context hiện tại.
Chuỗi vị trí dự báo của CCA là dữ liệu nội bộ cho chance rows, không được lưu
hoặc vẽ lên camera; mode/mean/covariance
ở đây chỉ mở lại khi protocol calibration và evidence riêng được chấp thuận.

### 1.1. Encoder LSTM của giao diện context

Với cửa sổ đầu vào causal chuẩn hóa \(z_t\), encoder dùng recurrence LSTM chuẩn

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

Biểu diễn cuối cửa sổ tạo vận tốc context và bốn score hướng cố định:

$$
\hat v_k=W_vh_T+b_v,\qquad
\hat s_k=\|\hat v_k\|_2,\qquad
q_{k,j}=\frac{\hat v_k^{\mathsf T}a_j}
{\max(\|\hat v_k\|_2,\delta)}.
$$

Đây là interface của `ctx_lstm.py`, không phải decoder vị trí tương lai. Target
training là vận tốc quan sát ở bước kế tiếp; hướng chỉ được suy ra từ vector
vận tốc và không dùng nhãn hướng thủ công trong optimizer.

## 2. Cơ chế CCA đơn giản

Với tập nhóm đang hoạt động \(\mathcal E_k\), \(M=|\mathcal E_k|\), đặt

\[
w_e=\frac{\exp(-\beta c_e)}
{\sum_{j\in\mathcal E_k}\exp(-\beta c_j)},
\qquad
\varepsilon_e=\varepsilon_{\min}+
(\bar\varepsilon-M\varepsilon_{\min})w_e.
\]

Miền hợp lệ là

\[
0\le\varepsilon_{\min}<\bar\varepsilon/M,
\qquad 0<\bar\varepsilon<0.5,
\qquad 0\le\beta<\infty.
\]

Context cao nhận collision allowance nhỏ hơn theo thứ tự tương đối, trong khi
\(\sum_e\varepsilon_e=\bar\varepsilon\). Implementation phải dịch logit và
chặn dưới ở log của số dương chuẩn hóa nhỏ nhất của kiểu số để tránh
overflow/underflow; saturation số học ở \(\beta\) cực lớn phải được log. Giá trị
\(\beta\), floor, quy tắc tổng hợp context và cách xử lý active-set change phải
được khóa trước benchmark. Không gọi
\(\bar\varepsilon\) là xác suất joint chính xác; đó là cận union-bound có điều
kiện cho tập nhóm đã khai báo trong một lần cập nhật.

Trong so sánh xác nhận chính, mọi thành phần vật lý của
\(d_{\mathrm{req},em}\) phải giữ cố định giữa các allocator để cô lập tác động
của allocation.
Biến thể khoảng an toàn theo ngữ cảnh

\[
d_{\mathrm{safe}}(c)=d_{\min}+(d_{\max}-d_{\min})c.
\]

chỉ là comparator/ablation riêng; không được đồng thời thay đổi cùng allocation
trong primary contrast.

## 3. Hình học và deterministic surrogate

### 3.1. Clearance tất định

Với hướng chiếu đơn vị \(n_{em}\), đặt

\[
d_{\mathrm{req},em}=r_r(n_{em})+r_{h,em}(n_{em})+
d_{\mathrm{brake},\ell}+d_0,
\]

trong đó hai số hạng đầu là support footprint robot và ellipse người theo hướng
chiếu; các số hạng còn lại là quãng phanh và margin đã khóa. Không dùng
covariance thay cho footprint. Geometry contract phải kiểm rằng biến cố va chạm
\(C_e\) nằm trong biến cố vi phạm half-space \(V_e^{\mathrm{hs}}\):

\[
C_e\subseteq V_e^{\mathrm{hs}}.
\]

Công thức \(d_{\mathrm{req},em}\), hướng, frame và dấu phải có parity test với
implementation. Nếu containment chưa đạt, chỉ được báo half-space surrogate,
không được gọi là collision-probability bound.

### 3.2. Surrogate vô hướng nội tại

Mỗi mode giữ lại dùng cùng allowance và phải thỏa cận **của mô hình**

\[
\Pr_{\mathrm{model}}\{V_e^{\mathrm{hs}}\mid Z_e=m,\mathcal F_k\}
\le\varepsilon_e,
\qquad m\in\mathcal M_e.
\]

Đặt

\[
\sigma_{em}^2=n_{em}^\top\Sigma^{\mathrm{rel}}_{em}n_{em}.
\]

The active Python and MATLAB chance-row paths reject non-finite, asymmetric or
materially non-positive-semidefinite relative covariance before projection.
This is an input-domain guard for A-07, not evidence of covariance provenance,
calibration or an operational probability claim.

Ký hiệu \(\delta_{em}\) là sai số vị trí tương đối sao cho separation thật bằng
\(p_{r,e}^{0}-\mu_{em}-\delta_{em}\). Vì vậy
\(n_{em}^\top\delta_{em}\) là đại lượng vô hướng cần chặn; quy ước này khóa dấu
giữa derivation và implementation.

\[
V_e^{\mathrm{hs}}=
\bigcup_{m\in\mathcal M_e}
\left(
\{Z_e=m\}\cap
\left\{n_{em}^\top(p_{r,e}^{0}-\mu_{em}-\delta_{em})
<d_{\mathrm{req},em}\right\}
\right).
\]

Equality được xem là thỏa chance row. Hợp trên tạo một group event duy nhất trên
mixture space, còn mỗi nhánh dùng row của chính mode đó. Collision/contact metric
phải khóa cùng boundary convention và containment phải đúng theo mọi nhánh,
đặc biệt khi \(\sigma_{em}=0\).

Sau khi chọn \(n_{em}\) và giả định projected error Gaussian theo từng mode,
chance row cục bộ là

\[
n_{em}^\top(p_{r,e}^{0}-\mu_{em})+\xi_{em} \ge
d_{\mathrm{req},em}+
\Phi^{-1}(1-\varepsilon_e)
\sigma_{em},
\quad \xi_{em}\ge0.
\]

Đặt \(a_{em}=n_{em}^\top(p_{r,e}^{0}-\mu_{em})-d_{\mathrm{req},em}\). Nếu
\(\sigma_{em}>0\), \(a_{em}\ge\Phi^{-1}(1-\varepsilon_e)\sigma_{em}\) cho cận
Gaussian vô hướng phía trên. Nếu \(\sigma_{em}=0\), mô hình suy biến cho xác
suất vi phạm strict half-space bằng không khi \(a_{em}\ge0\). Đây là property
nội tại của \(\Pr_{\mathrm{model}}\), không phải bằng chứng calibration của
phân phối thật \(\Pr_\star\).

Trong mỗi solve, \(\mathcal F_k\), active set, context, geometry, direction,
mode probability và covariance được giữ cố định. Slack làm bài toán dễ khả thi
hơn nhưng chỉ nghiệm có mọi \(\xi_{em}=0\) và residual đạt tolerance bảo thủ đã
khóa mới đủ tiền đề cho cận model-internal.

### 3.3. Accounting mode và phạm vi thời gian

Vì giữ đủ mode và \(\sum_m\pi_{em}=1\), công thức xác suất toàn phần cho

\[
\Pr_{\mathrm{model}}(V_e^{\mathrm{hs}}\mid\mathcal F_k)
=\sum_{m\in\mathcal M_e}\pi_{em}
\Pr_{\mathrm{model}}(V_e^{\mathrm{hs}}\mid Z_e=m,\mathcal F_k)
\le\varepsilon_e.
\]

Sau đó, không cần giả thiết độc lập,

\[
\Pr_{\mathrm{model}}\!\left(
\bigcup_{e\in\mathcal E_k}V_e^{\mathrm{hs}}\middle|\mathcal F_k\right)
\le\sum_{e\in\mathcal E_k}\varepsilon_e=\bar\varepsilon.
\]

Đây là open-loop one-solve union bound cho predictive measure tại update \(k\).
Nó không phải xác suất closed-loop sau quan sát tương lai, cận mission-wide hay
xác suất joint chính xác. Muốn thay \(\Pr_{\mathrm{model}}\) bằng
\(\Pr_\star\) phải đóng PO-003 bằng calibration độc lập đúng đuôi; nếu thiếu
bất kỳ hash/domain/frame/time/age, mode completeness, covariance provenance,
geometry parity, slack hoặc residual nào thì claim xác suất fail closed.

NMPC tối ưu một cost dễ đọc:

\[
J=\sum_{\ell=0}^{N-1}
\bigl(\|x_\ell-x_\ell^{\mathrm{ref}}\|_Q^2+
\|u_\ell-u_\ell^{\mathrm{ref}}\|_R^2+
\|u_\ell-u_{\ell-1}\|_S^2\bigr)
+\rho\|\xi\|_2^2+\|x_N-x_N^{\mathrm{ref}}\|_{Q_f}^2.
\]

Không thêm term nếu không có ý nghĩa vật lý, unit, scale và ablation.

## 4. Assumption ledger

Các ID dưới đây là ID chuẩn dùng chung với
`research/obsidian/05_Theory/assumptions.md`; một ID không được đổi nghĩa giữa
protocol, claim matrix và ghi chú chứng minh.

| ID | Giả định cần kiểm | Cách kiểm/chứng cứ | Nếu sai |
|---|---|---|---|
| A-01 | Tập nhóm người--bước hữu hạn, không rỗng | schema/property test | từ chối snapshot/controller step |
| A-02 | \(0\le\varepsilon_{\min}<\bar\varepsilon/M\), \(0<\bar\varepsilon<0.5\) | algebra + schema/property test | từ chối allocation |
| A-03 | Context hữu hạn trong \([0,1]\), tổng hợp bằng quy tắc khóa trước và không dùng nhãn test | feature trace + leakage audit | thu hẹp claim context |
| A-04 | \(Z_e\) tạo partition dưới \(\Pr_{\mathrm{model}}(\cdot\mid\mathcal F_k)\); mọi mode dương được giữ, tổng probability bằng một, omitted mass bằng không | schema/property + semantic audit | từ chối snapshot/controller step |
| A-05 | Sai số chiếu có điều kiện theo mode là Gaussian zero-mean dưới \(\Pr_{\mathrm{model}}\), với phương sai \(\sigma_{em}^2\) | distribution diagnostic | chỉ gọi deterministic surrogate |
| A-06 | One-sided projected residual đạt tail coverage đã khóa trên calibration độc lập, mọi mode/horizon/context, ID/OOD và đủ sample support | PR12 calibration + exact one-sided CI | chặn mọi claim trên \(\Pr_\star\) |
| A-07 | Covariance tương đối horizon-indexed là PSD, hữu hạn, cùng frame/time và tính cả cross-covariance nếu có | schema/test runtime | fallback; snapshot không hợp lệ |
| A-08 | \(\mathcal F_k\), tập nhóm/mode, context, geometry, direction, probability và covariance cố định trong một solve | implementation trace | mệnh đề chỉ open-loop one-solve |
| A-09 | \(f_d\) danh định xác định, liên tục và Lipschitz cục bộ trên miền vận hành | bound/derivation + numerical sweep | thu hẹp miền, không claim stability |
| A-10 | State, track, LSTM và context đồng bộ; measurement/prediction age bị chặn | runtime log | safe stop/fallback, không dùng proof |
| A-15 | State/input/actuator set đúng; lag/delay của lệnh vận tốc xuất hiện trong state/history của model proof; \(w_k\) có miền bị chặn | identification + config hash + model parity | chỉ báo empirical outcomes |
| A-16 | Terminal construction tạo shifted feasible candidate cho đúng augmented model và disturbance | amendment + derivation + invariance test | CLM-T-03 vẫn withdrawn/held |
| A-17 | \(d_{\mathrm{req},em}\) gồm footprint supports, braking, margin và bảo đảm \(C_e\subseteq V_e^{\mathrm{hs}}\) | geometry derivation + parity test | không claim collision-probability bound |

Mọi mệnh đề trong Overleaf phải dẫn tới các assumption ID dùng thật. Giả định
không được ẩn trong proof hoặc thêm sau khi counterexample xuất hiện mà không có
amendment.

## 5. Proof obligations

ID nghĩa vụ dùng chung với
`research/obsidian/05_Theory/proof_obligations.md`. Các số không liên tục trong
mục này là chủ ý: PR02 chỉ triển khai chi tiết những nghĩa vụ trực tiếp tạo ra
các mệnh đề đang xét, không tái sử dụng ID của nghĩa vụ khác.

### PO-014 — bảo toàn budget, thứ tự và continuity cố định active set

**Mệnh đề hợp đồng T1--T3.** Với A-01--A-03, miền tham số hợp lệ và
\(0\le\beta<\infty\), trong số học thực mỗi allocation lớn hơn floor và có tổng đúng
budget; nếu
\(c_a>c_b\) thì \(\varepsilon_a<\varepsilon_b\) khi \(0<\beta<\infty\); nếu
\(\beta=0\) thì \(\varepsilon_e=\bar\varepsilon/M\).

**Derivation.** Hàm mũ dương nên mẫu dương; cộng các phân số cho tổng một.
Tính đơn điệu của \(\exp(-\beta c)\) cho thứ tự. Bản triển khai số chỉ yêu cầu
allocation không nhỏ hơn floor, tổng đúng trong tolerance và log saturation;
phải kiểm overflow, clipping và finite precision vì chúng có thể phá đẳng thức
hoặc tính nghiêm ngặt ở độ chính xác máy. Khi active set cố định và \(\beta\)
hữu hạn, thương các hàm liên tục có mẫu dương nên allocation liên tục theo
context. Cụ thể, đặt
\(B=\bar\varepsilon-M\varepsilon_{\min}\), ta có

\[
\frac{\partial\varepsilon_e}{\partial c_j}
=-B\beta w_e(\mathbf 1_{e=j}-w_j),
\qquad
\left|\frac{\partial\varepsilon_e}{\partial c_j}\right|
\le \frac{B\beta}{4}.
\]

Đây là kiểm hợp đồng, không phải novelty lý thuyết. Cận đạo hàm chỉ có nghĩa
trên cùng một active set. Khi thêm hoặc bỏ một nhóm, cả \(M\), residual budget và
mẫu softmax đều đổi; allocation của nhóm không đổi context có thể nhảy hữu hạn.
Kiểm thử counterexample phải giữ lại sự kiện này và không được diễn giải
continuity cố định active set thành continuity qua switching.

### PO-001 — scalar surrogate nội tại và geometry containment

**Mệnh đề hợp đồng T4.** Nếu projected prediction error có điều kiện theo mode
là Gaussian dưới \(\Pr_{\mathrm{model}}(\cdot\mid Z_e=m,\mathcal F_k)\),
direction/covariance/geometry được đóng băng, mọi slack bằng không và residual
hợp lệ, thì scalar surrogate cho
\(\Pr_{\mathrm{model}}(V_e^{\mathrm{hs}}\mid Z_e=m,\mathcal F_k)
\le\varepsilon_e\). Với \(\sigma_{em}=0\), yêu cầu nominal margin không âm và
xác suất strict violation của mô hình suy biến bằng không. Chỉ khi
\(C_e\subseteq V_e^{\mathrm{hs}}\) đã được kiểm mới truyền cận tới collision
event của mô hình.

**Derivation.** Chuẩn hóa biến vô hướng khi \(\sigma_{em}>0\), áp dụng quantile
Gaussian và chuyển vế; xử lý riêng phân phối suy biến khi \(\sigma_{em}=0\).
Phải kiểm dấu, support footprint, ellipse người, quãng phanh, margin và chiều
containment bằng parity test. PO-003 về calibration là cổng khác; không được
đánh tráo derivation nội tại với xác suất vận hành.

### PO-005 — recursive feasibility

Nghĩa vụ này ở trạng thái `HELD`; CLM-T-03 đã rút khỏi claim analytic hiện tại.
Mô hình sáu trạng thái chưa bao phủ tường minh actuator lag, command delay của
lệnh vận tốc và chưa có miền bị chặn đã xác minh cho \(w_k\). Chỉ mở lại bằng
amendment nếu A-15--A-16 được đóng cho đúng augmented model. Trước đó chỉ dùng
câu “solve feasibility, constraint violation và fallback được đo thực nghiệm”.

### PO-006 — practical stability/tracking

Nghĩa vụ này cũng `HELD`; không có theorem stability cho controller hiện tại.
Chỉ mở lại bằng amendment với model alignment, terminal ingredients, bounded
disturbance và Lyapunov/ISS domain đã nêu. Dynamic-human constraints có thể làm
reference tạm thời không khả thi; báo tracking/fallback/mode switching như kết
quả thực nghiệm, không đổi tên chúng thành practical stability.

### PO-015 — predictive-mixture và union-bound accounting

**Mệnh đề hợp đồng T5.** Nếu \(Z_e\) là partition dưới predictive measure, tất
cả mode được giữ, tổng probability bằng một và cận T4 hợp lệ cho mọi mode, công
thức xác suất toàn phần cho cận nhóm dưới
\(\Pr_{\mathrm{model}}(\cdot\mid\mathcal F_k)\); sau đó Boole cho hợp các nhóm
trong active set của một solve. Không giả định độc lập, không gọi bound là exact,
closed-loop hay mission-wide. Offline trajectory-level Monte Carlo ở PR20 đo
joint outcome và CI riêng, không phải proof cho T5.

### Ánh xạ claim

| Claim | Mệnh đề/nghĩa vụ | Phạm vi admission |
|---|---|---|
| CLM-T-01 | T1--T3 / PO-014 | đại số allocator; không novelty |
| CLM-T-02 | T4 / PO-001, PO-011, PO-013 | chỉ model-internal; muốn nói \(\Pr_\star\) phải đóng PO-003 |
| CLM-T-04 | T5 / PO-002, PO-008, PO-015 | predictive open-loop one-solve; muốn nói \(\Pr_\star\) phải đóng PO-003 |
| CLM-T-03 | PO-005, PO-006, PO-009 | withdrawn/held cho controller hiện tại |
| CLM-EMP-02 | PR20/PR21/PR30/PR40 | chỉ feasibility/fallback/tracking đo được |

## 6. Falsification trước khi duyệt mệnh đề hợp đồng

Mỗi PO phải có:

- symbolic/unit check cho dimension, sign, limit \(c=0,1\), \(\beta=0\), một
  event, \(\sigma=0\) và covariance gần singular;
- random property tests cho budget, monotonicity và numerical stability;
- counterexample search với active-set switch (tối thiểu: thêm một nhóm làm đổi
  allowance của các nhóm cũ dù context của chúng không đổi), late prediction, mode-probability
  miscalibration, covariance undercoverage, omitted mass và infeasible reference;
- closed-loop stress test cho solver failure, fallback transition, saturation,
  chattering và collision dù constraint nominal thỏa;
- ledger `assumption -> test -> artifact hash -> outcome`.

Counterexample không bị xóa. Nó thu hẹp mệnh đề/domain hoặc tạo amendment.

## 7. Multimodal và calibration

Không chọn ground-truth-best mode online. Confirmatory controller định nghĩa
\(Z_e\) như một random-variable partition, giữ **tất cả** mode, kiểm
\(\sum_m\pi_{em}=1\), dùng cùng \(\varepsilon_e\) cho mọi mode của nhóm \(e\),
và từ chối mọi omitted probability mass. Các biến thể top-mode hoặc truncation
chỉ là exploratory baselines với claim riêng, không được trộn vào cận mục 3.
`minADE` oracle chỉ là diagnostic và không chứng minh controller có thông tin đó.

Covariance scale/quantile được fit trên calibration split độc lập, không dùng
`valid` thay calibration và không chạm `test_id`/`test_ood`. Statistic phải là
**one-sided projected residual** đúng hướng/dấu của chance row, không phải chỉ
radial Mahalanobis coverage. Mọi mode phải tham gia; top-mode coverage không đủ.
Nếu conditional mode assignment/responsibility không audit được, không admission
claim xác suất điều kiện theo mode trên \(\Pr_\star\).

Coverage và one-sided tail CI phải báo theo horizon, context, behavior/density,
ID/OOD và mức allowance thật sự, gồm các giá trị khoảng \(0.0025\) và floor tới
\(10^{-4}\) nếu cấu hình dùng chúng. Protocol phải chứng minh sample size/effective
tail support đủ cho one-sided confidence bound đã khóa; pooled 90/95% coverage
không thể xác minh một đuôi hiếm hơn nhiều. Nếu không đủ support, kết quả chỉ là
model-internal surrogate và operational probability claim bị chặn.

`probability_claim_eligible` mặc định `false` và chỉ được bật khi cùng artifact
đã xác minh calibration hash/domain, frame/time/age, mode partition/completeness,
covariance provenance/PSD, geometry containment, zero slack và solver residual.
Implementation Python và MATLAB hiện kiểm tra fail-closed các trường provenance
này; vì chưa có calibration artifact hợp lệ trong active study, mọi run hiện tại
vẫn không đủ điều kiện cho operational probability claim.

## 8. Tách specification, implementation và paper

- PR02/companion model spec giữ phương trình chuẩn.
- Mã implementation phải có equation/assumption ID trong docstring hoặc test
  mapping, nhưng không copy một phiên bản toán khác.
- Overleaf diễn giải cùng phương trình và derivation đã `VERIFIED`; không tự sửa ký
  hiệu chỉ ở paper.
- Obsidian lưu derivation/counterexample; Zotero lưu nguồn phương pháp gần nhất.

## 9. Cổng chấp nhận

### Implementation checkpoint — 2026-08-13

Python/MATLAB parity and edge-case tests pass, including zero/near-singular
covariance and ellipse-support checks. These checks validate implementation
invariants only; they do not replace an independent proof review, calibration
provenance or operational probability evidence. PR02 remains `PROOF-DRAFT`.

PR02 chỉ đạt `VERIFIED` khi notation table không mâu thuẫn, unit/frame/time rõ,
mọi claim ánh xạ tới mệnh đề/PO/assumption, derivation được một reviewer control
độc lập kiểm, property/counterexample/geometry-parity tests có artifact hash,
MATLAB PSD validation có bằng chứng mới, và implementation kiểm fail-closed đầy
đủ các trường eligibility. Overleaf không được chứa “guarantee”, “stable”,
“feasible” hoặc “joint probability” rộng hơn phạm vi đã xác minh; T1--T5 không
được mô tả như novelty lý thuyết.

### Targeted second-pass QA — 2026-08-13

The combined Python risk-allocation, real-time NMPC and contract suites passed
63 tests. This is an implementation-invariant check only. The independent
proof/geometry review, covariance/calibration provenance, zero-slack residual
record and operational probability eligibility remain open; PR02 stays
`PROOF-DRAFT`.

### Numerical parity amendment — 2026-08-13

The Python and MATLAB chance rows now use the same explicit variance floor
\(10^{-12}\,\mathrm{m}^2\) for the CasADi/MATLAB numerical path. The floor is
recorded in `NmpcConfig.chance_variance_floor_m2` and
`cfg.safety.chanceVarianceFloorM2`; it only regularizes the zero/near-singular
evaluation and does not change the Gaussian derivation. The full Python suite
(`171 passed`), Ruff and the MATLAB suite pass after this synchronization. This closes a
software parity defect, not the independent proof, calibration or probability
evidence gates.

### Active position-state theorem checkpoint — 2026-08-13

The Obsidian theory ledger now contains T-PS1, a minimal theorem aligned with
the active six-state position/body-velocity interface. It combines the causal
internal human-position update, fixed-budget allocation and the one-solve
model-internal Gaussian/Boole bound without introducing modes, torque inputs,
recursive feasibility or stability claims. Its proof is recorded in
research/obsidian/05_Theory/proofs.md. This is a notation/scope alignment
checkpoint only; independent proof review, calibration and operational
probability evidence remain open, so PR02 stays PROOF-DRAFT.

### Numeric fail-closed and context-boundary amendment — 2026-08-13

The Python and MATLAB fixed-budget allocators reject non-finite softmax logits
before normalization. This prevents invalid finite-precision inputs from being
silently mapped to a uniform allocation; it does not alter the real-arithmetic
T1--T3 proof. The five-feature sigmoid implementation in MATLAB
`cca.score` remains the primary simulation context path. The Python map
runner's proximity/closing proxy is retained only for its context-only map
contract and is not a second PR02 formulation. Full Python QA is `179 passed`
and MATLAB `run_tests` is `70 passed, 0 failed, 0 incomplete`; PR02 remains
`PROOF-DRAFT`.
