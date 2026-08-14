---
type: theory
status: draft
evidence_status: contract-draft
inheritance: legacy-hypothesis-reverify
---

# Ký hiệu

## Robot và miền dự báo

| Ký hiệu | Ý nghĩa |
|---|---|
| $k$ | bước điều khiển hiện tại |
| $\ell=1,\ldots,N$ | bước dự báo trong horizon |
| $s=[x,y,\theta,v_x,v_y,\omega]^\top$ | trạng thái pose và vận tốc thân của robot Mecanum |
| $u=[v_x^{\rm cmd},v_y^{\rm cmd},\omega^{\rm cmd}]^\top$ | lệnh vận tốc thân |
| $p_{r,e}^{0}$ | vị trí robot danh định tại nhóm $e=(h,\ell)$ trong lần solve hiện tại |
| $x^{\mathrm{ref}},u^{\mathrm{ref}}$ | trạng thái/input tham chiếu |
| $f_d$ | mô hình robot rời rạc |
| $\mathcal F_k$ | toàn bộ thông tin đo, track và dự báo sẵn có khi bắt đầu lần cập nhật $k$ |

## Giao diện dự báo người

Trong pipeline active, LSTM dùng cửa sổ causal của snapshot hiện tại:

$$
h_k=\operatorname{LSTM}_{\theta}(z_{k-L+1:k}),
\qquad
\hat v_{h,k+1}=W_vh_k+b_v,
$$

với $z_k$ chứa vị trí, vận tốc đo được và cờ hiệu lực. Từ
$\hat v_{h,k+1}$ suy ra tốc độ, hướng trái/phải/tiến/lùi và điểm context; không
suy ra một chuỗi vị trí tương lai. Các ký hiệu mode, mean và covariance dưới đây
chỉ được bật trong một protocol mở rộng đã calibration.

| Ký hiệu | Ý nghĩa |
|---|---|
| $h$ | chỉ số người được tracking |
| $e=(h,\ell)$ | nhóm người--bước dự báo đang hoạt động; mode không phải đơn vị phân bổ |
| $Z_e\in\mathcal M_e$ | biến mode rời rạc của phân phối dự báo, có các biến cố $\{Z_e=m\}$ loại trừ nhau và vét hết không gian dự báo điều kiện theo $\mathcal F_k$ |
| $\pi_{em}$ | $\Pr_{\mathrm{model}}(Z_e=m\mid\mathcal F_k)$, $\pi_{em}>0$ và $\sum_m\pi_{em}=1$ |
| $\mu_{em},\Sigma^h_{em}$ | mean/covariance dự báo LSTM có điều kiện theo mode |
| $\Sigma^r_{em},\Sigma^{hr}_{em}$ | covariance robot và cross-covariance người-robot tại đúng bước dự báo |
| $\Sigma^{\mathrm{rel}}_{em}$ | covariance tương đối $\Sigma^h+\Sigma^r-\Sigma^{hr}-(\Sigma^{hr})^\top$ |
| $n_{em}$ | hướng chiếu đơn vị từ mean người tới vị trí robot danh định |
| $\delta_{em}$ | sai số vị trí tương đối sao cho separation thật bằng $p_{r,e}^{0}-\mu_{em}-\delta_{em}$, xét có điều kiện trên $Z_e=m,\mathcal F_k$ |
| $\sigma_{em}^2$ | phương sai chiếu $n_{em}^\top\Sigma^{\mathrm{rel}}_{em}n_{em}$ |
| $d_{\mathrm{req},em}$ | clearance tất định gồm support robot, support ellipse người, quãng phanh và margin cố định |
| $V_e^{\mathrm{hs}}$ | biến cố vi phạm half-space chiếu của nhóm $e$ |
| $C_e$ | biến cố va chạm hình học; muốn suy cận va chạm phải kiểm $C_e\subseteq V_e^{\mathrm{hs}}$ |
| $\Pr_{\mathrm{model}}$ | xác suất nội tại của mô hình dự báo đã khai báo |
| $\Pr_\star$ | phân phối sinh dữ liệu/vận hành chưa biết; chỉ được nói tới sau calibration độc lập |

Trong recurrence LSTM, $z_t$ là vector snapshot đã chuẩn hóa, $h_t$ là trạng
thái ẩn, $c_t$ là trạng thái ô, còn $i_t,f_t,o_t$ lần lượt là cổng vào, quên và
ra; $\tilde c_t$ là ứng viên trạng thái ô. Các vector $a_j$ là bốn trục cố định
trái/phải/tiến/lùi dùng để tính score hướng, không phải nhãn huấn luyện.

Quy ước dấu được khóa bởi

$$
V_e^{\mathrm{hs}}=
\bigcup_{m\in\mathcal M_e}
\left(
\{Z_e=m\}\cap
\left\{n_{em}^\top(p_{r,e}^{0}-\mu_{em}-\delta_{em})
<d_{\mathrm{req},em}\right\}
\right).
$$

Dấu strict nghĩa là equality thỏa chance row. Định nghĩa theo hợp ở trên làm
$V_e^{\mathrm{hs}}$ thành một biến cố duy nhất trên mixture space dù mỗi mode có
row riêng. Collision/contact metric phải khóa cùng boundary convention;
geometry audit phải chứng minh $C_e\subseteq V_e^{\mathrm{hs}}$ theo từng nhánh
mode và theo chính quy ước đó.

Trong confirmatory controller, mọi mode phải được giữ lại, các biến cố mode phải
tạo thành một partition, tổng xác suất phải bằng một và omitted probability mass
phải bằng không. `minADE`/best-mode oracle chỉ dùng chẩn đoán offline, không được
đưa vào controller. Ký hiệu điều kiện luôn là
$\Pr(\,\cdot\mid Z_e=m,\mathcal F_k)$; viết tắt mơ hồ
`$\Pr(\,\cdot\mid m)$` không được dùng trong bản chính thức.

## Ngữ cảnh và rủi ro

| Ký hiệu | Ý nghĩa |
|---|---|
| $c_e\in[0,1]$ | điểm nguy hiểm ngữ cảnh của nhóm; lớn hơn nghĩa là ưu tiên nghiêm ngặt hơn |
| $q_e\in[0,1]^5$ | vector proximity, closing, CPA-time, crossing geometry và density, tính trên quỹ đạo robot nominal/reference đóng băng |
| $c_e=\max_m\sigma(b+\alpha^\top q_{em})$ | một context score của nhóm sau khi gộp bảo thủ qua mọi mode được giữ lại; calibration cố định có thể áp dụng sau sigmoid |
| $M=\lvert\mathcal E_k\rvert$ | số nhóm người-bước đang hoạt động tại một lần cập nhật NMPC |
| $\bar\varepsilon$ | tổng ngân sách vi phạm của tập nhóm đã khai báo |
| $\varepsilon_{\min}$ | floor không âm cho mỗi nhóm |
| $\varepsilon_e$ | mức vi phạm của nhóm, cũng là allowance có điều kiện dùng cho mọi mode trong nhóm |
| $0\le\beta<\infty$ | độ nhạy theo ngữ cảnh hữu hạn |
| $\xi$ | relaxation chẩn đoán chỉ dùng development; không thuộc primary chance formulation và run có $\xi>0$ không đủ điều kiện cho probability claim |
| $\Phi^{-1}$ | quantile của chuẩn tắc |

Mọi ký hiệu dự báo phía trên có nghĩa **open-loop, one-solve**: chúng được điều
kiện theo $\mathcal F_k$ và đóng băng trong lần solve tại $k$. Chúng không mô tả
phân phối closed-loop sau các phép đo tương lai và không tạo cận mission-wide.

## Ghi chú trạng thái

Hợp đồng sáu trạng thái/body-velocity là nguồn chuẩn cho physical scope. Mã
simulator đầu vào mô-men cũ chỉ là `legacy compatibility` và không đại diện cho
interface robot thật.

## Related notes

[[00_MOC/project-map]] · [[05_Theory/system-model]] · [[05_Theory/theorems]]
