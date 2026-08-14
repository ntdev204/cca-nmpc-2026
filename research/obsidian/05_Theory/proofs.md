---
type: contract-derivations
status: proof-draft
evidence_status: contract-derivation-draft
reviewed_by: null
---

# Các derivation cho mệnh đề hợp đồng

> **Active boundary:** các derivation mode/mixture chỉ giữ để truy vết lý thuyết
> và prior-art compatibility. Active implementation không xuất human future
> coordinates thành artifact, không vẽ trajectory lên ảnh và không phát mode
> probabilities; CCA-NMPC chỉ giữ prediction sequence nội bộ cho chance rows.

T1--T5 là các derivation sơ cấp để kiểm specification, không phải đóng góp lý
thuyết. Chúng vẫn cần kiểm độc lập về sign, geometry và parity với
implementation. T4--T5 dùng $\Pr_{\mathrm{model}}$; không derivation nào tự
chuyển thành claim trên phân phối vận hành $\Pr_\star$. T6 là invariant lựa
chọn nghiệm khả thi của implementation và không phải claim xác suất.

## Kiểm P-CTX — causal internal-position interface

Tại thời điểm \(k\), hai biến đầu vào \(\hat p^h_k\) và \(\hat v^h_k\) thuộc
\(\mathcal F_k\). Với \(\Delta t>0\) và số bước hữu hạn, phép đệ quy

\[
\hat p^h_{k+\ell|k}=\hat p^h_{k+(\ell-1)|k}+\Delta t\,\hat v^h_k,
\qquad \hat p^h_{k|k}=\hat p^h_k,
\]

cho nghiệm đóng

\[
\hat p^h_{k+\ell|k}=\hat p^h_k+\ell\Delta t\,\hat v^h_k .
\]

Vì mọi hạng bên phải đã có trước solve, chuỗi là causal và không sử dụng
ground-truth tương lai. Kết luận này chỉ xác nhận giao diện tính toán; nó không
cho biết sai số dự báo, độ bao phủ xác suất hay hành vi closed-loop. Quy tắc
không ghi/vẽ chuỗi là artifact contract được kiểm bằng schema và regression test,
không phải hệ quả của công thức toán.

## Chứng minh T1

Nghĩa vụ liên quan: [[05_Theory/proof-obligations|PO-014]].

Mỗi hàm mũ đều dương nên $w_e>0$. Đồng thời,

$$
\sum_e w_e=
\frac{\sum_e\exp(-\beta c_e)}{\sum_j\exp(-\beta c_j)}=1.
$$

Vì $\bar\varepsilon-M\varepsilon_{\min}>0$ nên
$\varepsilon_e>\varepsilon_{\min}$. Cuối cùng,

$$
\sum_e\varepsilon_e=M\varepsilon_{\min}+
(\bar\varepsilon-M\varepsilon_{\min})\sum_e w_e=\bar\varepsilon.
$$

## Chứng minh T2

Nghĩa vụ liên quan: [[05_Theory/proof-obligations|PO-014]].

Với $\beta>0$, điều kiện $c_a>c_b$ kéo theo

$$
\exp(-\beta c_a)<\exp(-\beta c_b).
$$

Hai số hạng có cùng mẫu dương nên $w_a<w_b$. Nhân với phần budget còn lại
dương và cộng cùng một floor không đổi thứ tự, do đó
$\varepsilon_a<\varepsilon_b$.

## Chứng minh T3

Nghĩa vụ liên quan: [[05_Theory/proof-obligations|PO-014]].

Khi $\beta=0$, mọi hàm mũ bằng một nên $w_e=1/M$. Vì vậy,

$$
\varepsilon_e=\varepsilon_{\min}+
\frac{\bar\varepsilon-M\varepsilon_{\min}}{M}
=\frac{\bar\varepsilon}{M}.
$$

## Chứng minh mệnh đề gộp fixed-budget

Đặt $w_e=\exp(-\beta c_e)/\sum_j\exp(-\beta c_j)$. Mẫu số dương nên
$w_e>0$ và $\sum_e w_e=1$. Vì $B>0$, suy ra

$$
\sum_e\varepsilon_e
=M\varepsilon_{\min}+B\sum_e w_e
=\bar\varepsilon,
\qquad
\varepsilon_e>\varepsilon_{\min}.
$$

Khi $\beta=0$, mọi $w_e=1/M$. Khi $\beta>0$ và $c_a>c_b$, tính đơn điệu
của hàm mũ cho $w_a<w_b$, nên $\varepsilon_a<\varepsilon_b$. Chứng minh chỉ
dùng active set đã đóng băng; khi thêm/bớt nhóm, $M$, $B$ và mẫu số đổi nên
không được kéo kết luận liên tục qua active-set switching. Mệnh đề cũng không
chuyển từ $\Pr_{\mathrm{model}}$ sang $\Pr_\star$.

## Chứng minh T4

Nghĩa vụ liên quan: PO-001, PO-011 và PO-013 trong
[[05_Theory/proof-obligations]].

Đặt $Y_{em}=n_{em}^\top\delta_{em}$ và
$a_{em}=n_{em}^\top(p_{r,e}^{0}-\mu_{em})-d_{\mathrm{req},em}$. Vi phạm
strict half-space xảy ra khi $Y_{em}>a_{em}$. Với $\sigma_{em}>0$, A-05 cho
$Y_{em}/\sigma_{em}\sim\mathcal N(0,1)$ dưới
$\Pr_{\mathrm{model}}(\cdot\mid Z_e=m,\mathcal F_k)$. Do đó nếu

$$
a_{em}\ge\Phi^{-1}(1-\varepsilon_e)\sigma_{em},
$$

thì

$$
\Pr_{\mathrm{model}}(Y_{em}>a_{em}\mid Z_e=m,\mathcal F_k)
\le 1-\Phi\!\left(\Phi^{-1}(1-\varepsilon_e)\right)
=\varepsilon_e.
$$

Nếu $\sigma_{em}=0$, Gaussian suy biến cho $Y_{em}=0$ gần như chắc chắn. Khi
$a_{em}\ge0$, biến cố strict $Y_{em}>a_{em}$ có xác suất bằng không. Nếu
$C_e\subseteq V_e^{\mathrm{hs}}$ theo A-17 thì tính đơn điệu của xác suất cho
cùng cận model-internal có điều kiện đối với $C_e$. Chiều bao hàm và công thức
$d_{\mathrm{req},em}$ phải được geometry-parity test; không được suy từ hình vẽ.
Slack dương hoặc residual vượt tolerance làm mất tiền đề $a_{em}$ của derivation.
Trong implementation position-state, covariance tương đối phải hữu hạn, đối
xứng và positive semidefinite trước khi được chiếu lên normal; covariance vi
phạm bị từ chối thay vì bị kẹp âm. Regression tương ứng chỉ là kiểm tra miền
đầu vào, không thay thế provenance, calibration hoặc review độc lập.

### Bổ sung hình học cho PO-001

Để kiểm dấu và chiều bao hàm, đặt robot center là $p_r$, tâm ellipse người là
$\mu$, và $n=(p_r-\mu)/\|p_r-\mu\|$ là normal từ người tới robot. Với

$$
E=\{\mu+R(\psi)Dq:\|q\|_2\le1\},
\qquad D=\operatorname{diag}(a,b),
$$

support của ellipse theo $n$ là

$$
h_E(n)=\sqrt{n^\top R(\psi)D^2R(\psi)^\top n}.
$$

Footprint robot được xấp xỉ bởi đĩa bán kính $r_R$, nên support của tổng
Minkowski $E\oplus B_{r_R}$ là $h_E(n)+r_R$. Vì vậy, với mọi điểm $q$ trong
footprint tổng,

$$
n^\top(q-\mu)\le h_E(n)+r_R.
$$

Nếu chance row thỏa

$$
n^\top(p_r-\mu)\ge h_E(n)+r_R+d,
$$

với $d\ge0$ gồm clearance, braking và quantile margin, thì

$$
n^\top(p_r-q)\ge d
$$

cho mọi $q\in E\oplus B_{r_R}$. Đây là containment một chiều của footprint
trong half-space đã chọn; nó không phải chứng minh collision probability cho
mọi hướng, mọi thời điểm hoặc closed loop. Kiểm tra số phải dùng cùng $R,D,n$
với implementation, kiểm cả $\sigma=0$, covariance PSD, slack bằng không và
residual solver. Nếu normal không đóng băng hoặc $d$ bị giảm bởi slack, mệnh đề
trên không được dùng.

## Chứng minh T5

Nghĩa vụ liên quan: PO-002, PO-008 và PO-015 trong
[[05_Theory/proof-obligations]].

A-04 cho các biến cố $\{Z_e=m\}$ là một partition của phân phối dự báo điều kiện
theo $\mathcal F_k$. Công thức xác suất toàn phần và cận T4 cho mọi mode cho

$$
\begin{aligned}
\Pr_{\mathrm{model}}(V_e^{\mathrm{hs}}\mid\mathcal F_k)
&=\sum_{m\in\mathcal M_e}\pi_{em}
\Pr_{\mathrm{model}}(V_e^{\mathrm{hs}}\mid Z_e=m,\mathcal F_k)\\
&\le\sum_{m\in\mathcal M_e}\pi_{em}\varepsilon_e
=\varepsilon_e.
\end{aligned}
$$

Bất đẳng thức Boole có điều kiện cho active set đã đóng băng cho

$$
\Pr_{\mathrm{model}}\!\left(
\bigcup_e V_e^{\mathrm{hs}}\middle|\mathcal F_k\right)
\le\sum_e\varepsilon_e=\bar\varepsilon,
$$

trong đó đẳng thức cuối dùng T1. Không cần giả thiết độc lập. Kết quả này không
tích lũy qua các lần receding-horizon update và không nói về $\Pr_\star$.

T1--T5 dùng số học thực chính xác. Bản triển khai dịch logit và chặn dưới để
tránh underflow; vì số học dấu phẩy động có thể làm một mức rất nhỏ làm tròn về
floor, kiểm thử triển khai dùng $\varepsilon_e\ge\varepsilon_{\min}$, kiểm tổng
trong tolerance và ghi saturation. Cờ `softmax_clipped`/`softmaxClipped` được
bật khi logit dịch phải chặn ở log của số dương chuẩn hóa nhỏ nhất; khi đó không
đòi strict ordering trong số học máy.

Với active set cố định, đặt
$B=\bar\varepsilon-M\varepsilon_{\min}$, vi phân trực tiếp cho

$$
\frac{\partial\varepsilon_e}{\partial c_j}
=-B\beta w_e(\mathbf 1_{e=j}-w_j).
$$

Vì $w_e(1-w_e)\le1/4$ và $w_ew_j\le1/4$, mỗi thành phần có độ lớn không quá
$B\beta/4$. Điều này cho continuity và một cận nhiễu đơn giản để kiểm số. Khi
active set đổi, $M$ và mẫu số đổi; counterexample thêm một nhóm cho thấy
allowance của nhóm cũ nhảy dù context không đổi. Do đó property PO-014 không
được kéo dài qua active-set switching; PO-004 vẫn mở.

### Counterexample số cho active-set switching

Lấy $\bar\varepsilon=0.10$, $\varepsilon_{\min}=0.01$ và ba nhóm có cùng
context score. Với active set gồm hai nhóm, mỗi nhóm nhận

$$
\varepsilon^{(2)}_e=0.01+\frac{0.10-2(0.01)}{2}=0.05.
$$

Khi nhóm thứ ba xuất hiện mà score của hai nhóm cũ không đổi, mỗi nhóm nhận

$$
\varepsilon^{(3)}_e=0.01+\frac{0.10-3(0.01)}{3}=0.033\overline{3}.
$$

Vì vậy allowance của nhóm cũ đổi $-0.016\overline{6}$ tại một lần thay đổi
active set. Tổng ngân sách vẫn bằng $0.10$, nhưng continuity theo context
không thể suy ra qua thay đổi cardinality. Đây là lý do PO-004 yêu cầu
hysteresis/smoothing và stress test riêng; test
`activeSetChangeIsGlobalContinuityCounterexample` chỉ xác nhận counterexample
trên miền số học, không chứng minh rằng một supervisor thực tế đã an toàn.

## Chứng minh T6

Nghĩa vụ liên quan: [[05_Theory/proof-obligations|PO-011]].

Vì $z^{(0)}\in\mathcal C_k$, tập $\mathcal C_k$ không rỗng. Theo định nghĩa,
mọi phần tử của $\mathcal C_k$ đều có $r(z)\le\tau$. Do controller chỉ chọn một
phần tử trong tập này, candidate trả về cũng thỏa $r(z)\le\tau$. Việc chọn
objective nhỏ nhất không thay đổi kết luận về feasibility.

Tiền đề không còn đúng nếu initial guess vi phạm chance row, wheel limit hoặc
obstacle row. T6 cũng không giới hạn thời gian solver đã dùng trước khi quay về
initial guess; deadline phải được đánh giá riêng. Đây là invariant lựa chọn
candidate trong một solve, không phải recursive-feasibility proof qua các bước
thời gian.

## Danh sách kiểm tra phản biện

- [ ] Ký hiệu khớp [[05_Theory/notation]].
- [ ] Giả thiết đủ và không có luận điểm vượt phạm vi.
- [ ] $\Pr_{\mathrm{model}}$, $\Pr_\star$, $\mathcal F_k$ và phạm vi open-loop one-solve được tách rõ.
- [ ] Mode là random-variable partition; mọi mode, tổng probability và omitted mass được kiểm tra.
- [ ] Dấu của scalar surrogate, trường hợp $\sigma=0$ và $C_e\subseteq V_e^{\mathrm{hs}}$ đã được kiểm.
- [ ] $d_{\mathrm{req},em}$ gồm footprint robot, ellipse người, quãng phanh và margin, khớp implementation.
- [ ] Slack bằng không, residual, covariance PSD/provenance và calibration eligibility được kiểm fail-closed.
- [ ] Có người phản biện độc lập và ngày phản biện.

## Implementation-parity audit — 2026-08-12

The derivations have been checked against the current static contracts, but this
is not an independent proof review. MATLAB `run_tests` passed 68/68 tests,
including budget ordering/uniformity, fixed-active-set continuity, Gaussian
chance-row gradients, multimodal accounting, and candidate-feasibility selection.
The Python repository tests and Ruff checks also pass. These results support
implementation consistency only; they do not close calibration, recursive
feasibility, closed-loop stability, hardware safety, or any claim under
\(\Pr_\star\). The unchecked items above therefore remain open before a theory
claim can be admitted to a final evidence release.

## Deterministic contract coverage — 2026-08-12

The current test suite gives direct implementation checks for the following
limited statements:

| Statement | Software check | Boundary |
|---|---|---|
| T1: positive allocation and fixed total | `test_domain_sum_ordering_and_high_context_quantile_direction`, MATLAB `TestRisk/domainSumOrderingAndQuantileDirection` | finite-precision property only |
| T2: ordering for fixed active set | `test_domain_sum_ordering_and_high_context_quantile_direction`, MATLAB `TestRisk/domainSumOrderingAndQuantileDirection` | does not cover active-set changes or calibration |
| T3: uniform special case | `test_uniform_is_exact_special_case`, `test_cca_beta_zero_is_the_same_uniform_special_case`, MATLAB `TestRisk/uniformIsExact` | does not establish optimality |
| Fixed-budget proposition T1--T3 | same ordering/uniform tests plus `test_allocation_is_continuous_for_a_fixed_active_set` | finite-precision contract only; active-set switching remains excluded |
| T6: feasible-candidate selection | Python `test_realtime_nmpc_preserves_feasible_guess_when_rti_deteriorates`; MATLAB `TestNmpc/solvesFeasibleHumanFreeProblem` | one solve only; no recursive feasibility or deadline guarantee |

These checks support parity between the declared formulas and the current
software paths. They are not an independent mathematical review, a stability
proof, a safety guarantee, or evidence under the operational distribution
\(\Pr_\star\). T4--T5 remain blocked by geometry containment, covariance and
mode-accounting evidence; all probability claims therefore remain fail-closed.

Related hub: [[00_MOC/project-map]]

## Proof of active position-state theorem T-PS1

The causal-position equation follows by summing the constant measured velocity
over \(\ell\) intervals. Every term on its right-hand side belongs to
\(\mathcal F_k\), so the construction uses no future observation and creates no
exported human path.

For the risk allocation, each exponential is positive, hence \(w_e>0\) and

$$
\sum_{e\in\mathcal E_k}w_e=1 .
$$

Writing \(B=\bar\varepsilon-M\varepsilon_{\min}>0\),

$$
\sum_e\varepsilon_e=M\varepsilon_{\min}+B\sum_e w_e=\bar\varepsilon .
$$

For each event, the Gaussian tail condition gives

$$
\Pr_{\rm model}(Y_e>a_e\mid\mathcal F_k)
\le 1-\Phi\left(\Phi^{-1}(1-\varepsilon_e)\right)
=\varepsilon_e .
$$

Boole's inequality then yields

$$
\Pr_{\rm model}\left(\bigcup_e\{Y_e>a_e\}\middle|\mathcal F_k\right)
\le\sum_e\varepsilon_e=\bar\varepsilon .
$$

No independence assumption is used. If \(\sigma_e=0\), the strict event is
empty whenever \(a_e\ge0\), which is the corresponding degenerate limit. The
proof is an open-loop one-solve model statement; it is not an operational
probability result and requires independent calibration before any claim under
the true distribution is considered.

Parity audit: [[07_Analysis/theory-parity-audit-20260813]]

## Static proof-contract recheck — 2026-08-12

The risk-allocation property suite was rerun after the pose/data additions:
Python `tests/python/tests/test_risk_allocation.py` passed 27/27, and MATLAB
`run_tests` passed 68/68. The checks cover positivity/floor, fixed total,
ordering, uniform special case, fixed-active-set continuity, the active-set
counterexample, permutation equivariance, numerical saturation and complete
mode accounting. This is a repeatable implementation sanity check, not an
independent mathematical review and not evidence for calibration,
recursive-feasibility, closed-loop stability, hardware safety or
\(\Pr_\star\) claims.

The Python NMPC probability-eligibility plumbing now fails closed unless the
calibration and geometry/provenance fields required by PR02 are present and
hashed. The gate test confirms this behavior; it does not create the missing
calibration or independent-review evidence.

## T4 edge-case continuation — 2026-08-13

The implementation parity check now includes zero-variance and rank-one
near-singular covariance inputs in both Python and MATLAB. The Python suite
passed `154/154` tests and MATLAB `run_tests` passed `70/70`; these are finite
numerical-limit checks only. Geometry containment, covariance calibration,
zero-slack residual records and independent proof review remain open, so the
T4 statement is still a model-internal contract and PR02 remains
`PROOF-DRAFT`.

## Proof of P-PS3 — frozen-row bounded candidate rollout

The executable first validates dimensions and finiteness. The nominal command
is obtained from the current six-state error and is passed through the declared
speed, yaw-rate and command-change limits. In the CCA branch, each horizon row
uses the supplied nominal robot location and human mean to form a unit normal;
the covariance is projected onto that normal, the context-weighted allowance
is bounded, and a positive reduced margin violation adds a finite correction.
The command is clipped again before the rollout.

For finite inputs and a positive finite horizon, the velocity blend is a convex
combination of the current velocity and the bounded command. Induction therefore
keeps each velocity component finite and within the configured blend envelope;
the pose update is a finite sum of bounded products. The stored rollout is thus
finite. The output records the maximum reduced violation and the risk budget;
the risk-slack output is explicitly zero because no optimized slack variable
exists in the candidate implementation.

This proves only the bounded-rollout and provenance invariant. It does not prove
that a nonlinear program was solved, that any chance row is feasible, that the
reduced margin is a geometric containment bound, or that the fallback/deadline
path is safe. The regression
`test_position_nmpc_uses_prediction_nominal_robot_geometry` verifies that
changing `nominal_robot_xy` changes the frozen-row normal rather than silently
using a reference waypoint.
