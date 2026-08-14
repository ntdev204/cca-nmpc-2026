---
type: contract-proposition-ledger
status: proof-draft
evidence_status: contract-derivation-draft
---

# Sổ mệnh đề hợp đồng T1--T6

> **Active boundary:** LSTM hiện chỉ cung cấp context snapshot; CCA-NMPC có thể
> tạo chuỗi vị trí dự báo nội bộ cho chance rows. Chuỗi này không trở thành
> artifact ảnh và không được dùng để phát mode/trajectory overlay; mọi
> mode/mixture equation bên dưới là compatibility note chưa được bật.

## Ánh xạ sang bản báo Overleaf

Bản báo tiếng Anh giữ hai proposition đại số (budget/ordering và smooth
fixed-set response) cùng một theorem về one-update joint chance bound. Theorem
trên Overleaf là bản nén của T4--T5 cho một Gaussian projected error trên mỗi
event; nó không mang mixture-mode accounting nếu mô hình được triển khai không
phát multi-mode distribution. Mọi claim vẫn chỉ thuộc
$\Pr_{\mathrm{model}}(\cdot\mid\mathcal F_k)$, zero slack và một lần cập nhật.
Việc đổi nhãn từ proposition sang theorem chỉ phản ánh vai trò cấu trúc trong
bài báo, không nâng nó thành novelty hoặc closed-loop guarantee.

T1--T5 là các phép kiểm hợp đồng sơ cấp cho specification trong
[[05_Theory/context-aware-risk-allocation]]; chúng **không phải novelty lý
thuyết**. T1--T3 là đại số của allocator. T4--T5 chỉ nói về
$\Pr_{\mathrm{model}}$ trong một lần solve open-loop đã điều kiện theo
$\mathcal F_k$. Không mệnh đề nào chứng minh recursive feasibility, ổn định
vòng kín, calibration trên $\Pr_\star$ hoặc an toàn vật lý. T6 là một invariant
chọn nghiệm trong implementation, không phải mệnh đề xác suất hay claim mới.

## P-CTX — Causal internal-position interface

Với snapshot hữu hạn \((\hat p^h_k,\hat v^h_k)\), bước mẫu \(\Delta t>0\) và
horizon hữu hạn \(N\), CCA-NMPC dùng

\[
\hat p^h_{k+\ell|k}=\hat p^h_k+\ell\Delta t\,\hat v^h_k
\]

cho các chance rows. Công thức là phép tích phân vận tốc không đổi trong một
solve, nên chỉ dùng thông tin có trước solve và không cần ground-truth tương
lai. P-CTX là contract của giao diện, không phải theorem về độ chính xác dự
báo, an toàn hoặc ổn định. Chuỗi được giữ trong bộ nhớ của CCA-NMPC và bị cấm
trong ảnh, CSV và manifest.

## T1 — Dương và bảo toàn ngân sách

Trong số học thực chính xác, với A-01--A-03,
$M\varepsilon_{\min}<\bar\varepsilon$ và $0\le\beta<\infty$, mỗi mức phân bổ thỏa
$\varepsilon_e>\varepsilon_{\min}$ và

$$
\sum_{e\in\mathcal E_k}\varepsilon_e=\bar\varepsilon.
$$

Ánh xạ claim: CLM-T-01. Derivation:
[[05_Theory/proofs#Chứng minh T1]]; nghĩa vụ PO-014.

## T2 — Thứ tự theo ngữ cảnh

Với hai nhóm trong cùng active set, nếu $0<\beta<\infty$ và $c_a>c_b$ thì
$\varepsilon_a<\varepsilon_b$.

Ánh xạ claim: CLM-T-01. Derivation:
[[05_Theory/proofs#Chứng minh T2]]; nghĩa vụ PO-014.

## T3 — Trường hợp đồng đều

Nếu $\beta=0$ thì $\varepsilon_e=\bar\varepsilon/M$ với mọi nhóm đang hoạt động.

Ánh xạ claim: CLM-T-01. Derivation:
[[05_Theory/proofs#Chứng minh T3]]; nghĩa vụ PO-014.

## Mệnh đề gộp — fixed-budget allocator

Với cùng các điều kiện của T1--T3, đặt

$$
B=\bar\varepsilon-M\varepsilon_{\min}>0.
$$

Khi đó ánh xạ

$$
\varepsilon_e=\varepsilon_{\min}+B
\frac{\exp(-\beta c_e)}{\sum_j\exp(-\beta c_j)}
$$

vừa bảo toàn đúng tổng ngân sách, vừa giữ mọi mức phân bổ lớn hơn floor.
Nếu $\beta=0$, mọi nhóm nhận cùng một mức; nếu $\beta>0$, nhóm có $c_e$ lớn
hơn nhận mức nhỏ hơn. Đây là một proposition hợp đồng, không phải claim
novelty hay bảo đảm xác suất.

Proof ngắn nằm tại [[05_Theory/proofs#Chứng minh mệnh đề gộp fixed-budget]];
kiểm tra số học tương ứng thuộc PO-014.

## T4 — Surrogate vô hướng nội tại và containment

Đặt

$$
a_{em}=n_{em}^\top(p_{r,e}^{0}-\mu_{em})-d_{\mathrm{req},em},
\qquad
\sigma_{em}^2=n_{em}^\top\Sigma^{\mathrm{rel}}_{em}n_{em}.
$$

Với A-05, A-07, A-08 và $0<\varepsilon_e<0.5$, nếu $\sigma_{em}>0$ và

$$
a_{em}\ge\Phi^{-1}(1-\varepsilon_e)\sigma_{em},
$$

thì
$\Pr_{\mathrm{model}}(V_e^{\mathrm{hs}}\mid Z_e=m,\mathcal F_k)
\le\varepsilon_e$. Nếu $\sigma_{em}=0$ và $a_{em}\ge0$, xác suất vi phạm
strict half-space của mô hình suy biến bằng không. Nếu A-17 còn cho
$C_e\subseteq V_e^{\mathrm{hs}}$, cùng cận áp dụng cho $C_e$ dưới
$\Pr_{\mathrm{model}}(\cdot\mid Z_e=m,\mathcal F_k)$. Mệnh đề chỉ được dùng khi slack bằng không và residual
solver đạt tolerance bảo thủ đã khóa.

Ánh xạ claim: CLM-T-02. Derivation:
[[05_Theory/proofs#Chứng minh T4]]; nghĩa vụ PO-001, PO-011 và PO-013. Claim trên
$\Pr_\star$ vẫn bị khóa bởi PO-003.

Ranh giới parity: T4 là chance-row formulation của theory/reference path. C++
candidate rollout hiện dùng projected covariance và một reduced clearance
correction để chọn lệnh; nó chưa triển khai đầy đủ support containment,
$d_{\mathrm{req},em}$, optimized slack hoặc solver residual của T4. Vì vậy T4
được giữ ở trạng thái proof-draft và không được gọi là property đã thực thi.

## T5 — Accounting mode và cận Boole trong một solve

Với A-01, A-04 và A-08, nếu cận điều kiện của T4 hợp lệ cho **mọi** mode, thì

$$
\Pr_{\mathrm{model}}(V_e^{\mathrm{hs}}\mid\mathcal F_k)
\le\varepsilon_e,
$$

và

$$
\Pr_{\mathrm{model}}\!\left(
\bigcup_{e\in\mathcal E_k}V_e^{\mathrm{hs}}\middle|\mathcal F_k\right)
\le\bar\varepsilon.
$$

Đây là union bound cho predictive-mode partition và active set đã đóng băng,
không phải đẳng thức, closed-loop probability sau update kế tiếp hoặc cận
mission-wide. Nếu A-17 đạt cho mọi nhóm, cận model-internal cũng truyền xuống
hợp các biến cố $C_e$.

## T6 — Bất biến chọn nghiệm tham chiếu (không phải solver đang chạy)

T6 is retained as a compatibility proposition for a future full numerical
solver. The current C++ executable does not expose the candidate set
\(\mathcal C_k\), objective \(J\), residual \(r\), or a nonlinear-program
selection step; its active invariant is P-PS3 below.

Gọi $z^{(0)}$ là initial guess và $z^{(1)},\ldots,z^{(L)}$ là các candidate do
solver trả về. Với tolerance $\tau>0$, đặt

$$
\mathcal C_k=\{z^{(i)}:\ r(z^{(i)})\le\tau,\ J(z^{(i)})<\infty\},
$$

trong đó $r(z)$ là vi phạm ràng buộc lớn nhất. Nếu $z^{(0)}\in\mathcal C_k$ và
controller trả về candidate có objective nhỏ nhất trong $\mathcal C_k$, thì
candidate được trả về cũng có $r(z)\le\tau$. Điều này chỉ giữ một nghiệm khả
thi đã có; nó không chứng minh recursive feasibility, optimality, deadline hay
an toàn fallback.

Ánh xạ: nghĩa vụ PO-011. Derivation:
[[05_Theory/proofs#Chứng minh T6]].

T6 không ánh xạ vào CLM-T-04. Nó chỉ là invariant của solver tham chiếu dưới
PO-011; derivation nằm tại [[05_Theory/proofs#Chứng minh T6]]. Vì vậy T6 không
được dùng để mô tả executable hiện tại hoặc suy ra cận xác suất, recursive
feasibility, deadline hay an toàn.

## Property không đánh số

Với active set cố định và $\beta$ hữu hạn, $\varepsilon_e(c)$ liên tục theo
context; từng đạo hàm riêng có độ lớn không quá
$(\bar\varepsilon-M\varepsilon_{\min})\beta/4$. Đây là property thuộc PO-014,
không phải một theorem/claim novelty và không nói gì về active-set switching.
Trong số học máy, chỉ được báo các kiểm tra finite, floor, tổng trong tolerance
và cờ saturation thực đo. Counterexample thêm/bớt nhóm được giữ lại để ngăn diễn
giải continuity này thành một claim qua switching.

Related hub: [[00_MOC/project-map]]

## P-PS3 — Frozen-row bounded candidate rollout

The current compiled controller is a bounded candidate-rollout implementation,
not a direct-transcription nonlinear-program solver. For a validated finite
input, positive sample time, positive horizon and finite limits, it first forms
a nominal body-velocity command from the current six-state error. In the CCA
branch it computes a frozen normal from the supplied nominal robot and human
means, projects the supplied covariance, allocates the fixed risk budget, and
adds a bounded correction when the reduced margin is violated. It then clips
the command and applies the declared velocity-blend/pose update for each
horizon step.

Consequently, every returned command is within the configured speed and yaw
limits, the stored rollout is finite for finite validated inputs, and the
output records the maximum reduced margin violation, risk bound, timing and
the reserved risk-slack field. The current field
`maximum_risk_slack_m=0` is a bookkeeping value; no optimized slack variable
is exposed by this implementation.

This proposition is an implementation invariant for one bounded rollout. It
does not assert nonlinear-program convergence, recursive feasibility, optimality,
zero violation, stability, deadline satisfaction or physical safety. A future
full chance-constrained solver may use the direct-transcription equations as a
design target, but that target is not evidence of the current executable.

Related: [[05_Theory/proofs#Proof of P-PS3 — frozen-row bounded candidate rollout]] and
[[05_Theory/proof-obligations|PO-011]].

## Active position-state theorem — T-PS1

This is the minimal theorem that matches the active CCA-NMPC interface. It
replaces no controller and does not add a stability claim.

At update \(k\), let the measured human context be
\((\hat p_k^h,\hat v_k^h)\), let \(\Delta t>0\), and let the active set
\(\mathcal E_k\) be fixed during one solve. CCA forms only the internal causal
sequence

$$
\hat p_{k+\ell|k}^h=\hat p_k^h+\ell\Delta t\,\hat v_k^h,
\qquad \ell=1,\ldots,N .
$$

The robot state and command are

$$
s_k=[x_k,y_k,\theta_k,v_{x,k},v_{y,k},\omega_k]^\top,
\qquad
u_k=[v_{x,k}^{\rm cmd},v_{y,k}^{\rm cmd},\omega_k^{\rm cmd}]^\top .
$$

Assume \(0\le\varepsilon_{\min}<\bar\varepsilon/M\),
\(0<\bar\varepsilon<0.5\), and fixed context scores \(c_e\in[0,1]\). Define

$$
w_e=\frac{e^{-\beta c_e}}{\sum_{j\in\mathcal E_k}e^{-\beta c_j}},
\qquad
\varepsilon_e=\varepsilon_{\min}+
(\bar\varepsilon-M\varepsilon_{\min})w_e .
$$

Let \(Y_e\sim\mathcal N(0,\sigma_e^2)\) be the projected relative-position
error for event \(e\), and let \(a_e\) be its nominal signed clearance. If

$$
a_e\ge\Phi^{-1}(1-\varepsilon_e)\sigma_e
\quad\text{for every }e\in\mathcal E_k,
$$

then the model-internal one-update bound is

$$
\Pr_{\rm model}\left(\bigcup_{e\in\mathcal E_k}\{Y_e>a_e\}\middle|\mathcal F_k\right)
\le \bar\varepsilon .
$$

The statement is conditional on the fixed active set, zero slack and valid
residuals. It does not imply calibration under \(\Pr_\star\), recursive
feasibility, closed-loop stability, mission-wide safety or a human trajectory
artifact. The future-position sequence exists only inside CCA-NMPC memory.
