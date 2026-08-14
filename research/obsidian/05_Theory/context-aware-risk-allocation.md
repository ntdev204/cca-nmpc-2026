---
type: core-method
status: draft
evidence_status: contract-derivation-draft
novelty_role: narrow-candidate-at-risk-not-new-adaptive-allocation
---

# Phân bổ rủi ro theo ngữ cảnh

Ghi chú này định nghĩa allocator đóng dạng đang được kiểm tra. Ánh xạ được giữ
đơn giản để kiểm tra trực tiếp ý nghĩa, điều kiện đúng và failure mode. Không
được dùng riêng công thức này để claim adaptive risk allocation mới: nearest
work đã có cả risk adaptation trực tuyến và learned allocation dưới tổng budget
cố định. Giá trị ứng viên chỉ nằm ở tính không huấn luyện, human--step, giữ
clearance cố định và bằng chứng so sánh nhân quả sau focused literature audit.

## Điểm ngữ cảnh

Với mỗi nhóm $e=(h,\ell)$, tạo vector đặc trưng chuẩn hóa $q_e$ từ khoảng cách,
closing speed, time-to-closest-approach, góc cắt và mật độ cục bộ. Một scorer bị
chặn cho

$$
c_e=g(q_e)\in[0,1],
$$

trong đó $c_e$ lớn hơn nghĩa là nhóm cần mức vi phạm nghiêm ngặt hơn. Nếu đặc
trưng được tính theo từng mode, quy tắc xác nhận lấy giá trị lớn nhất trên mọi
mode giữ lại rồi đóng băng trong solve. $c_e$ không phải xác suất, covariance,
detector confidence hoặc LSTM mode weight.

## Phân bổ ngân sách cố định

Với $M$ nhóm đang hoạt động, đặt

$$
w_e=\frac{\exp(-\beta c_e)}{\sum_{j\in\mathcal E_k}\exp(-\beta c_j)},
$$

và

$$
\varepsilon_e=\varepsilon_{\min}+
(\bar\varepsilon-M\varepsilon_{\min})w_e.
$$

Diễn giải:

- ngữ cảnh nguy hiểm cao $\Rightarrow$ $\varepsilon_e$ nhỏ $\Rightarrow$ Gaussian margin lớn hơn;
- $\bar\varepsilon$ giữ cố định nên context chỉ phân phối lại mức bảo thủ;
- $\beta=0$ khôi phục phân bổ đồng đều;
- $\varepsilon_{\min}$ tránh mức vi phạm bằng không;
- miền hợp lệ là $0\le\varepsilon_{\min}<\bar\varepsilon/M$ và $0<\bar\varepsilon<0.5$.

**Active boundary:** mode không nhận ngân sách riêng và không được phát ra bởi
LSTM context hiện tại. Tại update $k$, $Z_e$ chỉ là compatibility notation của
phân phối dự báo điều kiện theo $\mathcal F_k$; các biến cố $\{Z_e=m\}$ phải loại trừ
nhau và vét hết không gian dự báo. Mọi mode dùng cùng $\varepsilon_e$ trong cận
nội tại
$\Pr_{\mathrm{model}}(V_e^{\mathrm{hs}}\mid Z_e=m,\mathcal F_k)
\le\varepsilon_e$. Khi partition đầy đủ và $\sum_m\pi_{em}=1$, xác suất toàn
phần cho cận nhóm dưới $\Pr_{\mathrm{model}}$. Điều này không tự suy ra cùng cận
dưới phân phối vận hành $\Pr_\star$.

Với active set cố định và $\beta$ hữu hạn, ánh xạ trên liên tục theo context.
Đặt $B=\bar\varepsilon-M\varepsilon_{\min}$, đạo hàm đơn giản là

$$
\frac{\partial\varepsilon_e}{\partial c_j}
=-B\beta w_e(\mathbf 1_{e=j}-w_j),
\qquad
\left|\frac{\partial\varepsilon_e}{\partial c_j}\right|
\le \frac{B\beta}{4}.
$$

Đây là một property triển khai thuộc PO-014, không phải novelty lý thuyết. Nó
không áp dụng qua thời điểm active set thay đổi: thêm một nhóm làm đổi $M$,
residual budget và mẫu softmax, nên allowance của các nhóm cũ có thể nhảy dù
context của chúng giữ nguyên. Counterexample này được khóa trong kiểm thử
Python/MATLAB; PO-004 về hysteresis/smoothing vẫn mở.

## Các bước online

1. Kiểm tra snapshot state/prediction và accounting đầy đủ mọi mode.
2. Tạo tập nhóm người-bước bằng quy tắc cố định có log.
3. Tính, tổng hợp và log $q_e,c_e$; đóng băng trong solve.
4. Phân bổ $\varepsilon_e$ bằng shifted-softmax có ngưỡng máy; kiểm tra
   positivity, saturation, miền và tổng budget. Cờ `softmax_clipped` (Python)
   hoặc `softmaxClipped` (MATLAB) phải được lưu trong trace; khi cờ bật, không
   dùng strict ordering dấu phẩy động làm bằng chứng cho T2.
5. Tạo một chance row cho mỗi mode với $d_{\mathrm{req},em}$, covariance tương
   đối đúng horizon và phép dựng hình học khớp implementation.
6. Giải NMPC; log slack, residual, eligibility của claim xác suất,
   solver/fallback và thời gian.
7. Snapshot sai phải bị từ chối, không được thay bằng predictor không khai báo;
   nếu CCA-NMPC tích phân velocity để tạo vị trí tương lai nội bộ thì phép
   tích phân phải causal, bounded và không được xuất thành ảnh/artifact.

Trong primary contrast, mọi thành phần của $d_{\mathrm{req},em}$, model,
predictor, reference và fallback policy phải giống nhau giữa các allocator.

## Ablation bắt buộc

- phân bổ đồng đều ($\beta=0$);
- điểm chỉ dùng khoảng cách;
- tắt context và hoán vị context;
- bộ phân bổ tối ưu không dùng context khi khả thi;
- bất định chưa hiệu chuẩn và đã hiệu chuẩn;
- active-set hysteresis/smoothing;
- fallback bật/tắt chỉ trong môi trường offline an toàn;
- context-dependent distance như comparator riêng, không trộn vào primary contrast.

## Trường hợp biên đã biết

- thay đổi $M$ có thể gây gián đoạn allocation;
- các nhóm có cùng context chia ngân sách bằng nhau;
- $\beta$ lớn có thể đẩy nhóm ít nguy hiểm sát floor;
- dự báo mất hiệu chuẩn làm mất ý nghĩa xác suất;
- omitted mode mass hoặc ground-truth-best-mode làm mất cận xác suất;
- slack dương hoặc residual không đạt làm nghiệm không đủ điều kiện cho claim xác suất;
- calibration radial/top-mode không kiểm được đuôi one-sided của mọi mode;
- thiếu calibration hash/domain, frame/time/age, covariance provenance hoặc
  containment hình học làm claim xác suất fail closed.

Các trường hợp này ánh xạ tới [[05_Theory/proof-obligations]].

Related hub: [[00_MOC/project-map]]
