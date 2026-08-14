---
type: prior-art-screening
status: novelty-at-risk
evidence_status: full-text-expanded
screened_at: 2026-08-01
---

# Chênh lệch prior art — 2026-08-01

Đây chưa phải systematic review hoàn tất. Metadata và nội dung có khả năng bác
claim đã được kiểm trên trang nhà xuất bản hoặc bản toàn văn có thẩm quyền; đối
chiếu phương trình/thực nghiệm nằm tại
[[03_Literature/nearest-work-matrix]]. Search plan PR01 chỉ là hồ sơ lịch sử;
focused audit hiện dùng Zotero và nguồn sơ cấp có liên kết. Snowballing có mục
tiêu, screening, correction/retraction và collection/tag audit vẫn còn mở.

Phần mô tả PR01 ở trên là lịch sử của comprehensive workflow. Active scope dùng
focused audit; các dòng prior-art và giới hạn claim vẫn có giá trị khi được
Zotero/source note kiểm tra, nhưng không được trình bày như systematic review.

## Công trình mới hoặc mới trở nên đặc biệt gần

| ID | Nguồn chính | Phần đã bị prior art chiếm | Hệ quả cho dự án | Tiếp nhận |
|---|---|---|---|---|
| PA-01 | [Stefanini et al., RA-L 2024](https://doi.org/10.1109/LRA.2024.3461552) | MPC theo context dùng hoạt động/tư thế người, có mô phỏng và robot thật. | “Context-aware MPC cho human-aware navigation” không còn là novelty. Khác biệt phải nằm ở ánh xạ context vào mức phân bổ của fixed chance budget. | full-text; Zotero item/PDF/metadata đã kiểm; correction/provenance còn mở |
| PA-02 | [Akhtyamov et al., RAS 2025](https://doi.org/10.1016/j.robot.2024.104830) | Objective theo bất định và adaptive constraint trong social MPC, đánh giá mô phỏng và robot thật. | Adaptive safety constraint và uncertainty-aware MPC đã có. Context phải tách khỏi covariance; bắt buộc allocator uncertainty-only đối sánh. | full-text; Zotero item/PDF/metadata đã kiểm; correction/provenance còn mở |
| PA-03 | [Nair et al., TCST 2025](https://doi.org/10.1109/TCST.2024.3451370) | SMPC với dự báo đa mode và phân bổ rủi ro theo mode. | Risk allocation, kể cả theo mode, đã có. Bài báo không được claim việc phân phối risk budget là mới. | full-text; Zotero item/PDF/metadata đã kiểm; version/correction còn mở |
| PA-04 | [Mohamed et al., RA-L 2025](https://doi.org/10.1109/LRA.2025.3576071) | U-MPPI chance-constrained trong môi trường động bất định, có mô phỏng và đánh giá thực tế chung không gian với người. | Chance constraint + sampling MPC + đánh giá dynamic obstacle ngoài thực tế đã có. Thêm làm comparator an toàn cấp hệ thống khi khả thi. | full-text; Zotero item/PDF/metadata đã kiểm; version/correction còn mở |
| PA-05 | [Sun et al., arXiv 2506.14305](https://arxiv.org/abs/2506.14305) | Thích nghi rủi ro học online theo bất định để chọn waypoint cho socially aware MPC. | Cách viết chung “online/adaptive risk-aware MPC” không an toàn. Phải so cơ chế, semantics rủi ro, phụ thuộc huấn luyện và tầng bằng chứng. | đã audit full-text; preprint |
| PA-06 | [Ye và Ren, IET CSR 2026](https://doi.org/10.1049/csy2.70051) | Chance constraint joint được tách thành mức đều theo người--bước; social preference ảnh hưởng topological selection. Bài nêu adaptive risk allocation theo threat level là hướng tương lai. | Dự án không được claim phát hiện nhu cầu adaptive allocation. Uniform event allocation là baseline bắt buộc và delta chỉ còn ở cách hiện thực hóa/kiểm định. | full-text; Zotero item/PDF/metadata đã kiểm; correction/provenance còn mở |
| PA-07 | [Wang et al., NAHS 2026](https://doi.org/10.1016/j.nahs.2026.101751) | Dự báo neural trong chance-constrained MPC với cận conformal robust theo vùng dưới distribution shift do policy. | Dự báo học máy + chance-constrained MPC đã có ở mức bảo đảm bất định mạnh hơn. LSTM phải là interface; nêu rõ giới hạn calibration/distribution shift. | full-text; Zotero item/PDF/metadata đã kiểm; version/correction còn mở |
| PA-08 | [Trepella et al., arXiv 2607.10374](https://arxiv.org/abs/2607.10374) | Dự báo/ngữ cảnh người trong động lực học NMPC, social cost, nhiều baseline, mô phỏng lặp và phân tích định tính. | Human-aware NMPC có predictor/social cost đã có. Dùng độ chặt baseline/chỉ số/ablation làm mức so sánh tối thiểu. | đã audit full-text; trạng thái IROS 2026 chờ proceedings |
| PA-09 | [Catellani et al., arXiv 2512.12717](https://arxiv.org/abs/2512.12717) | MPC coverage human-aware với dự báo quỹ đạo xác suất và chance constraint. | Dự báo + human chance constraint đã có cả ngoài navigation-to-goal. Đây là comparator phạm vi, không phải allocator gần nhất. | đã audit full-text; preprint |
| PA-10 | [Wang et al., arXiv 2605.21257](https://arxiv.org/abs/2605.21257) | RL actor học mức rủi ro theo chướng ngại vật và safety margin; ràng buộc tổng \(\sum_i\beta_i\leq\beta_{\max}\); dùng cùng allowance cho mọi mode GMM. | Claim rộng “context-aware adaptive fixed-budget risk allocation” đã bị chiếm. Delta còn lại chỉ là đóng dạng/không học, human--step, position-state Mecanum NMPC, clearance cố định và bằng chứng thực nghiệm. | đã audit full-text; preprint |
| PA-11 | [Wang et al., IROS 2025](https://doi.org/10.1109/IROS60139.2025.11246134) | Risk-adaptive CVaR-BF chọn mức \(\beta_k\) nhỏ nhất còn khả thi và mở rộng dynamic safety zone theo trạng thái tương đối. | Điều chỉnh risk online và context động học đã có ở venue peer-reviewed. Cần đối sánh heuristic trực tiếp và tách allocation khỏi thay đổi clearance. | full-text; Zotero item/PDF/metadata đã kiểm; version/correction còn mở |
| PA-12 | [Ono và Williams, CDC 2008](https://doi.org/10.1109/CDC.2008.4739221) | IRA phân phối joint budget theo constraint--time, chuyển risk từ ràng buộc inactive sang active trong MPC. | Human--step allocation là một trường hợp ứng dụng của ý tưởng constraint--time cũ; softmax đóng dạng không đủ tự thân làm novelty Q1. | full-text; Zotero item/PDF/metadata đã kiểm; correction/provenance còn mở |
| PA-13 | [Paulson et al., IJC 2020](https://doi.org/10.1080/00207179.2017.1323351) | Tối ưu feedback gain và risk allocation bằng chuỗi bài toán lồi; so trực tiếp fixed uniform. | Dự án phải định vị allocator là heuristic nhanh/minh bạch, không phải optimal risk allocation. | full-text; Zotero item/PDF/metadata đã kiểm; correction/provenance còn mở |
| PA-14 | [Barbosa và Löfberg, arXiv 2604.04602](https://arxiv.org/abs/2604.04602) | Online risk allocation trong SMPC path planning, tổng risk bị chặn, đồng thời chọn feedback law. | Cách diễn đạt “online allocation theo gần/xa obstacle” đã có; delta chỉ còn chi phí/audit/evidence trong human-aware position-state NMPC. | đã audit full-text; preprint |
| PA-15 | [Parimi và Williams, ICAPS 2026](https://arxiv.org/abs/2509.08157) | Dynamic global-budget allocation qua nhiều agent bằng greedy surplus--deficit và market mechanism; có HIL. | Transparent/training-free shared-budget allocation cũng đã có ngoài MPC; không được dùng thuộc tính này một mình làm novelty. | đã audit full-text; accepted ICAPS 2026 theo project page |
| PA-16 | [Engelaar, Lazar và Haesaert, SCL 2026](https://doi.org/10.1016/j.sysconle.2026.106474) | Elastic chance constraints tối ưu risk values thích nghi dưới cận individual/total và đưa ra điều kiện closed-loop constraint satisfaction, recursive feasibility, stochastic stability. | Softmax budget proof chỉ là tính đúng phân bổ; không được gọi là adaptive chance-constraint theory hoặc closed-loop guarantee. | full-text; Zotero item/PDF/metadata đã kiểm; correction/provenance còn mở |
| PA-17 | [Bonzanini, Mesbah và Di Cairano, Automatica 2024](https://doi.org/10.1016/j.automatica.2023.111418) | Perception-aware chance-constrained MPC mô hình hóa uncertainty phụ thuộc control và chứng minh probabilistic recursive feasibility/stability dưới thiết kế cost/terminal. | Phải tách context khỏi covariance/perception và cấm suy diễn từ cận Boole cục bộ sang stability/feasibility. | full-text author version; Zotero item/PDF/metadata đã kiểm; correction/provenance còn mở |
| PA-18 | [Liu et al., arXiv 2601.16686](https://arxiv.org/abs/2601.16686) | LSTM temporal encoder cùng context-aware soft switching giữa PPO và MPC/QP safety filter cho human--robot navigation. | LSTM + context + MPC integration không tạo novelty; cần calibration, matched allocator contrast và bằng chứng robot định lượng. | đã audit full-text preprint; venue chờ xác minh |
| PA-19 | [Dai et al., ICRA 2019](https://doi.org/10.1109/ICRA.2019.8793660) | p-Chekov khởi tạo risk đều rồi phân phối phần dư từ inactive constraints sang violated waypoints dưới cùng tổng Δ; đánh giá 500 query x 100 execution mỗi môi trường. | Feasibility-based risk reallocation là comparator bắt buộc và fixed-total redistribution trong robot planning không mới. | PDF `[28]` đã audit; Zotero item/PDF/metadata đã kiểm; correction/provenance còn mở |
| PA-20 | [Huang và Jafari, arXiv 2301.06201](https://arxiv.org/abs/2301.06201) | Bayesian LSTM dùng trajectory camera thật để tạo conflict-risk field cho MPC/DFS chọn hành động. | LSTM bất định + risk-aware MPC đã có; dự án phải tạo khác biệt bằng calibration/OOD, matched closed-loop evidence và real-frame overlay audit được. | PDF `[29]` đã audit; preprint |
| PA-21 | [Zhang et al., TCYB 2021](https://doi.org/10.1109/TCYB.2020.3032711) | Probabilistic multi-modal predictor được đưa vào chance-constrained nonlinear MPC; có deterministic reformulation, stability condition, slack và backup. | Predictor + chance NMPC + theorem/fallback integration không mới; proof allocator của dự án chỉ được claim ở phạm vi budget/local bound. | PDF `[30]` đã audit; Zotero item/PDF/metadata đã kiểm; version/correction còn mở |
| PA-22 | [Ren, Ahn và Kamgarpour, L-CSS 2023](https://doi.org/10.1109/LCSYS.2022.3186269) | Chance-constrained trajectory planning dưới GMM, robustification moment từ mẫu hữu hạn và nhánh CVaR; kiểm với predictor/dữ liệu lái xe thật. | Multimodal uncertainty + finite-sample chance planning không mới; phải tách confidence ước lượng khỏi violation allowance và cấm claim $\Pr_\star$ khi calibration chưa đạt. | full-text arXiv đối chiếu DOI; Zotero item/PDF `[31]` đã kiểm |
| PA-23 | [Ren et al., TCST 2025](https://doi.org/10.1109/TCST.2024.3477089) | Nominal/robust/contingency chance-MPC dưới GMM; robust planner có recursive-feasibility result với terminal, initial-feasibility và prediction-propagation assumptions. | CLM-T-03 phải giữ withdrawn; budget conservation không thay thế augmented Markov model, invariant/terminal construction và shifted-candidate proof. | full-text arXiv v2 đối chiếu DOI; Zotero item/PDF `[32]` đã kiểm |

## Ảnh hưởng lên khoảng trống

Khoảng trống rộng đã bị bác. Các mục sau không thể là đóng góp độc lập có thể
bảo vệ: context-aware MPC, adaptive constraint, chance-constrained MPC, risk
allocation, dự báo quỹ đạo người trong MPC, context-aware risk adaptation dưới
tổng budget cố định, hoặc tổ hợp chung của chúng.

Ứng viên hẹp hơn còn có thể kiểm tra nhưng có nguy cơ chỉ là gia tăng:

> một allocator đóng dạng, không cần huấn luyện, dùng điểm context liên tục tách
> khỏi bất định predictor để phân phối lại tổng violation budget giữa các nhóm
> người--bước trong position-state Mecanum NMPC với body-velocity command; giữ physical clearance, mọi mode
> LSTM và cùng conditional allowance trong nhóm; được đánh giá nhân quả với
> uniform, optimized non-context, feasibility/heuristic risk-adaptive và
> learned-risk ở cùng budget.

Cách diễn đạt này không được nâng thành claim novelty chỉ vì khác controller hay
robot. Với PA-12--PA-23, khuyến nghị hiện tại là `PIVOT-EMPIRICAL`: giá trị chính
nằm ở benchmark nhân quả minh bạch, calibration/OOD, failure analysis và bằng
chứng robot. `GO-ALGORITHM` chỉ hợp lệ nếu phản biện độc lập chỉ ra một cơ chế
hoặc định lý thực sự không bị dòng IRA/online/learned allocation chiếm; `STOP`
nếu không thể xây dựng câu hỏi thực nghiệm đủ mạnh.

## Thay đổi thiết kế bắt buộc do screening

1. So sánh phân bổ đồng đều, thích nghi chỉ theo bất định, chỉ theo khoảng cách,
   context-off/permuted-context, heuristic risk-adaptive kiểu PA-11,
   learned-risk kiểu PA-10, p-Chekov feasibility reallocation kiểu PA-19 và ánh
   xạ đề xuất ở cùng tổng budget/clearance.
2. Xem chứng minh softmax allocator là kiểm tra đúng semantics budget, không phải
   ổn định vòng kín hay định lý chance constraint mới.
3. Thêm hiệu chuẩn dự báo và giới hạn policy shift; ADE/FDE không đủ cho claim xác suất.
4. Benchmark với cả NMPC tối ưu hóa và một sampling controller risk-aware mạnh
   khi khả thi tính toán; không dùng khác biệt Mecanum làm novelty thay thế.
5. Đạt mức báo cáo trial lặp, phân phối, thất bại và định tính của các bài gần đây;
   một map hoặc quỹ đạo đại diện không đủ qua phản biện Q1.
6. Không claim real-time hoặc sẵn sàng ngoài thực tế nếu thiếu bằng chứng target hardware và sensing tích hợp.
7. Không claim closed-loop stability, recursive feasibility hoặc theory mới từ
   allocator; các claim đó đòi hỏi model/terminal/propagation assumptions riêng
   và đã có prior art mạnh hơn ở PA-16--PA-17 cùng PA-23.

## Hành động screening tiếp theo

- Hoàn thiện collection/tag Zotero cho PA-01 đến PA-23. Toàn bộ item/PDF đã có;
  phần còn mở là screening tag, venue/version, correction/retraction và
  provenance gốc của 27 PDF kế thừa.
- Ghi DOI, phiên bản, venue, trạng thái correction/retraction và quyền truy cập toàn văn.
- Tạo một source note có vị trí trang/section cho mỗi công trình được nhận.
- Hoàn tất ma trận công trình gần nhất trong [[03_Literature/literature-synthesis]].
- Hoàn tất hai vòng backward/forward snowballing không làm đổi gap/baseline.
- Xin phản biện novelty độc lập trước khi mở confirmatory data/experiment.

Related hub: [[00_MOC/project-map]]

