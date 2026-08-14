---
type: source-index
status: active
evidence_status: unknown
---

# Chỉ mục nguồn

The PR01 database/export paragraphs below are retained as historical provenance.
For the active single-paper scope, use the Zotero/Obsidian focused audit and do
not interpret the archived counts as systematic-review coverage or PRISMA flow.

## Mức bằng chứng

| Mức | Ý nghĩa |
|---|---|
| `lead` | Kế thừa từ ghi chú cũ; metadata/toàn văn chưa xác minh lại. |
| `metadata` | DOI/tiêu đề/tác giả đã kiểm tra. |
| `abstract` | Đã đọc abstract/bản ghi nhà xuất bản; không đủ cho claim chi tiết. |
| `full-text` | Đã đọc toàn văn, có ghi chú nguồn cấp trang. |
| `excluded` | Có mã lý do loại. |

## Nguồn dẫn cũ — phải xác minh lại bằng Zotero/nhà xuất bản

Các họ nguồn sau được kế thừa dưới dạng `legacy hypothesis`, không phải trích dẫn đang dùng:

| Nhóm | Mục đích dự kiến | Trạng thái |
|---|---|---|
| MPC theo context/hoạt động | comparator context gần nhất | lead |
| NMPC chủ động với dự báo đa mode | ghép dự báo--điều khiển | lead |
| lập kế hoạch chance-constrained và phân bổ rủi ro lặp | semantics budget/bộ phân bổ gần nhất | lead |
| tái lập Gaussian collision và joint scenario risk | phạm vi xác suất | lead |
| bất định quỹ đạo người đã hiệu chuẩn | chỉ số hiệu chuẩn LSTM | lead |
| động lực học, ma sát và MPC có ràng buộc cho Mecanum | hợp đồng plant/input | lead |
| NMPC nhúng/real-time | phương pháp đo timing | lead |
| safety/backup supervisor dự báo | ranh giới fallback | lead |

## Nguồn đang dùng có điều kiện

| Citekey | DOI | Mức | Ghi chú nguồn | Ô gap | Xác minh gần nhất |
|---|---|---|---|---|---|
| stefanini2024context | 10.1109/LRA.2024.3461552 | full-text | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | context-aware MPC | 2026-08-01 |
| akhtyamov2025uncertainty | 10.1016/j.robot.2024.104830 | full-text | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | uncertainty/adaptive constraint | 2026-08-01 |
| ryu2024drcc | 10.1109/ICRA57147.2024.10610404 | full-text | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | DR chance constraint | 2026-08-01 |
| degroot2025scenario | 10.1177/02783649251315203 | full-text | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | joint vs marginal risk | 2026-08-01 |
| nair2025risk | 10.1109/TCST.2024.3451370 | full-text preprint | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | multimodal mode-wise allocation | 2026-08-01 |
| ye2026scutmpc | 10.1049/csy2.70051 | full-text | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | uniform human--step risk + social MPC | 2026-08-01 |
| mohamed2025c2umppi | 10.1109/LRA.2025.3576071 | full-text preprint | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | chance-constrained sampling MPC | 2026-08-01 |
| sun2025lrmcp | arXiv:2506.14305 | full-text preprint | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | learned online risk waypoint selection | 2026-08-01 |
| wang2026neuralmpc | 10.1016/j.nahs.2026.101751 | full-text preprint | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | conformal chance-constrained neural MPC | 2026-08-01 |
| trepella2026sfmnmpc | arXiv:2607.10374 | full-text preprint | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | social-force NMPC benchmark | 2026-08-01 |
| catellani2025hmpcc | arXiv:2512.12717 | full-text preprint | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | human-aware chance-constrained coverage MPC | 2026-08-01 |
| wang2025riskadaptive | 10.1109/IROS60139.2025.11246134 | full-text preprint | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | adaptive CVaR risk level + dynamic zone | 2026-08-01 |
| wang2026differentiable | arXiv:2605.21257 | full-text preprint | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | learned context-aware fixed-total risk | 2026-08-01 |
| ono2008ira | 10.1109/CDC.2008.4739221 | full-text | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | constraint--time iterative risk allocation | 2026-08-01 |
| paulson2020joint | 10.1080/00207179.2017.1323351 | full-text | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | optimal risk allocation in SMPC | 2026-08-01 |
| barbosa2026online | arXiv:2604.04602 | full-text preprint | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | online risk allocation + feedback selection | 2026-08-01 |
| parimi2026ira | arXiv:2509.08157 | full-text author version | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | dynamic shared-budget allocation | 2026-08-01 |
| engelaar2026elastic | 10.1016/j.sysconle.2026.106474 | full-text | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | elastic/adaptive chance levels + closed-loop theory | 2026-08-01 |
| bonzanini2024pacmpc | 10.1016/j.automatica.2023.111418 | full-text author version | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | perception-dependent uncertainty + recursive feasibility/stability | 2026-08-01 |
| liu2026arms | arXiv:2601.16686 / DOI 10.48550/arXiv.2601.16686 | full-text preprint | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | LSTM + context-aware MPC/QP switching | 2026-08-13 |
| dai2019pchekov | 10.1109/ICRA.2019.8793660 | full-text author version | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | feasibility-driven fixed-total risk reallocation | 2026-08-01 |
| huang2023blstm | arXiv:2301.06201 | full-text preprint | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | Bayesian LSTM + risk-aware MPC on real trajectories | 2026-08-01 |
| zhang2021chance | 10.1109/TCYB.2020.3032711 | full-text author version | [[03_Literature/nearest-work-matrix#Đối chiếu theo cơ chế]] | probabilistic prediction + chance-constrained NMPC | 2026-08-01 |
| ren2023multimodal | 10.1109/LCSYS.2022.3186269 | full-text author version | [[03_Literature/Sources/source-ren-multimodal-risk]] | finite-sample multimodal chance/CVaR planning | 2026-08-01 |
| ren2025recursive | 10.1109/TCST.2024.3477089 | full-text author version | [[03_Literature/Sources/source-ren-feasibility]] | recursive-feasible GMM chance-MPC | 2026-08-01 |
| stratton2026hmpnavigation | 10.1145/3757279.3788664 | full-text author version | [[03_Literature/Sources/source-stratton-hmp-navigation-2026]] | prediction quality versus closed-loop/social outcomes | 2026-08-12 |
| alfayizi2026mecanumtraction | 10.18280/jesa.590406 | full-text | [[03_Literature/Sources/source-alfayizi-mecanum-2026]] | Mecanum traction, actuator feasibility and control activity | 2026-08-12 |
| chen2026saltd3 | 10.1038/s41598-026-45819-0 | abstract | [[03_Literature/Sources/source-chen-lstm-td3-2026]] | LSTM plus reinforcement-learning navigation boundary | 2026-08-12 |
| gravina2026crowdmpc | 10.3389/frobt.2026.1812386 | full-text | [[03_Literature/Sources/source-gravina-crowd-mpc-2026]] | multisensor crowd MPC and physical validation boundary | 2026-08-12 |
| luna2026mecanumunknowninput | 10.1016/j.ejcon.2026.101466 | publisher abstract | [[03_Literature/Sources/source-luna-mecanum-unknown-input-2026]] | Mecanum actuator/model uncertainty and unknown-input estimation | 2026-08-13 |
| ye2026scutmpc | 10.1049/csy2.70051 | publisher full-text landing page | [[03_Literature/Sources/source-ye-scu-t-mpc-2026]] | risk-aware social chance-constrained planning boundary | 2026-08-13 |
| pham2026mecanumhybrid | 10.1177/18758967251394861 | publisher abstract | [[03_Literature/Sources/source-pham-mecanum-hybrid-2026]] | Mecanum hybrid control and wheel-slip benchmark boundary | 2026-08-13 |
| kada2026pedestrianmpc | 10.7210/jrsj.44.196 | publisher full-text metadata | [[03_Literature/Sources/source-kada-pedestrian-aware-mpc-2026]] | human-centred MPC and interaction-quality evaluation boundary | 2026-08-13 |
| miyachi2026canempc | 10.1186/s40648-026-00345-6 | publisher full-text | [[03_Literature/Sources/source-miyachi-cane-mpc-2026]] | dynamic-obstacle accompanying-robot MPC and real-robot boundary | 2026-08-13 |
| unifiedlocalriskmap2026 | 10.3390/s26123900 | publisher abstract | [[03_Literature/Sources/source-unified-risk-map-2026]] | continuous contextual/uncertainty risk-map boundary | 2026-08-13 |
| gnimady2026integratednmpc | 10.1007/s11370-025-00661-7 | publisher full-text | [[03_Literature/Sources/source-integrated-estimation-nmpc-2026]] | multisensor estimation, embedded MPC and physical-validation boundary | 2026-08-13 |
| screeningrefresh20260813 | screening-only; six primary records | screening note | [[03_Literature/Sources/source-screening-refresh-20260813]] | dynamic human prediction, Mecanum hardware, interactive MPC, model-based RL, Safe-RL/CBF and self-supervised motion boundary | 2026-08-13 |
| mohamed2026transformersafrl | 10.3389/fnbot.2025.1697518 | screening-only; DOI landing record | [[03_Literature/Sources/source-screening-refresh-20260813]] | transformer human forecasting plus Safe-RL/CBF adjacent boundary | 2026-08-13 |
| han2025mecanumresidual | 10.1016/j.conengprac.2025.106587 | publisher record; screening-only | [[03_Literature/Sources/source-2026-mecanum-crowd-control-refresh]] | hardware Mecanum MPC and residual-learning boundary | 2026-08-13 |
| shafizadeh2024mecanumvo | [10.1016/j.heliyon.2024.e26829](https://doi.org/10.1016/j.heliyon.2024.e26829) | publisher DOI; screening-only | [[03_Literature/Sources/source-screening-refresh-20260813]] | Mecanum dynamic-obstacle planner comparator | 2026-08-13 |
| tsai2026fuzzytd3mecanum | [10.1007/s40815-025-02209-4](https://doi.org/10.1007/s40815-025-02209-4) | publisher full-text; screening-only | [[03_Literature/Sources/source-screening-refresh-20260813]] | omnidirectional Mecanum RL/local-control boundary | 2026-08-13 |

## Tài liệu công cụ được kiểm tra

| Citekey | Nguồn | Mức | Vai trò | Xác minh gần nhất |
|---|---|---|---|---|
| ultralytics2026yolo26pose | [Ultralytics YOLO26](https://docs.ultralytics.com/models/yolo26), [pose task](https://docs.ultralytics.com/tasks/pose) | official documentation | giao diện box/keypoint/confidence; không phải novelty hoặc evidence detector | 2026-08-12 |

## Screening candidates from the 2026-08-13 refresh

| Citekey | DOI/record | Mức | Ghi chú nguồn | Ô gap | Xác minh gần nhất |
|---|---|---|---|---|---|
| samavi_sicnav_2025 | [IEEE T-RO record](https://doi.org/10.1109/TRO.2024.3484634) | full text | [[03_Literature/Sources/source-samavi-sicnav-2026]] | interactive crowd MPC, ORCA/KKT, real-robot safety boundary; not a fixed-budget CCA allocator | 2026-08-13 |
| cooperativegpmpc2026 | [Springer full text](https://doi.org/10.1186/s13634-026-01306-2) | publisher full-text screening | [[03_Literature/Sources/source-cooperative-gp-mpc-2026]] | learned uncertainty and multi-agent MPC | 2026-08-13 |
| riskawaremppi2025 | [arXiv:2506.21205](https://arxiv.org/abs/2506.21205) | full-text preprint | [[03_Literature/Sources/source-dra-mppi-2025]] | risk-aware MPPI benchmark | 2026-08-13 |
| collaborative2026emergencyprotection | 10.1109/LRA.2026.3671537 | abstract | [[03_Literature/Sources/source-collaborative-emergency-protection-2026]] | interactive planning and emergency-protection boundary | 2026-08-13 |
| trevisan2025dramppi | [10.1109/IROS60139.2025.11246822](https://doi.org/10.1109/IROS60139.2025.11246822) | publisher record | [[03_Literature/web-verified-gap-sources#Search refresh — 2026-08-13 (risk-aware and real-robot boundary)]] | real-robot risk-aware MPPI and collision-probability benchmark | 2026-08-13 |
| busellato2026uapcbf | [10.1016/j.robot.2025.105291](https://doi.org/10.1016/j.robot.2025.105291) | publisher record | [[03_Literature/web-verified-gap-sources#Search refresh — 2026-08-13 (risk-aware and real-robot boundary)]] | probabilistic human forecast plus predictive safety control | 2026-08-13 |
| han2025drmpc | [DR-MPC publication page](https://leaf.utias.utoronto.ca/publication/han-2024-drmpc/) | author publication page | [[03_Literature/web-verified-gap-sources#Search refresh — 2026-08-13 (risk-aware and real-robot boundary)]] | real-world social navigation with MPC and residual learning | 2026-08-13 |
| aslam2025simpc | [Scitepress record](https://www.scitepress.org/PublishedPapers/2025/137104/) | publisher record | [[03_Literature/web-verified-gap-sources#Search refresh — 2026-08-13 (risk-aware and real-robot boundary)]] | physical SI-MPC versus CV and open-loop/closed-loop separation | 2026-08-13 |
| shafizadeh2024mecanumtvmpc | [10.1109/ICRoM64545.2024.10903625](https://doi.org/10.1109/ICRoM64545.2024.10903625) | IEEE landing page | [[03_Literature/Sources/source-position-state-boundary-20260813]] | position-level Mecanum MPC and velocity-level actuation boundary | 2026-08-13 |
| gao2026modelbasedrl | [10.1016/j.neucom.2026.132702](https://doi.org/10.1016/j.neucom.2026.132702) | publisher record | [[03_Literature/Sources/source-position-state-boundary-20260813]] | model-based RL, stochastic pedestrian prediction and real-robot boundary | 2026-08-13 |
| mecanumellipsoidmpc2025 | [10.1016/j.mechatronics.2025.103386](https://doi.org/10.1016/j.mechatronics.2025.103386) | publisher record | [[03_Literature/Sources/source-position-state-boundary-20260813]] | ellipsoidal obstacle MPC geometry boundary | 2026-08-13 |
| kada2026pedestrianmpc | [10.7210/jrsj.44.196](https://doi.org/10.7210/jrsj.44.196) | publisher full-text metadata | [[03_Literature/web-verified-gap-sources#Search refresh — 2026-08-13 (human-centred MPC and Mecanum boundary)]] | pedestrian-centred MPC and real interaction outcomes | 2026-08-13 |
| miyachi2026canempc | [10.1186/s40648-026-00345-6](https://doi.org/10.1186/s40648-026-00345-6) | publisher full text | [[03_Literature/web-verified-gap-sources#Search refresh — 2026-08-13 (human-centred MPC and Mecanum boundary)]] | dynamic-obstacle accompanying-robot MPC | 2026-08-13 |
| zhang2025physicalguided | [10.1016/j.jestch.2025.102008](https://doi.org/10.1016/j.jestch.2025.102008) | publisher record; screening-only | [[03_Literature/Sources/source-2026-mecanum-crowd-control-refresh]] | physical-guided pedestrian prediction boundary | 2026-08-13 |
| kada2026pedestrianaware | [10.7210/jrsj.44.196](https://doi.org/10.7210/jrsj.44.196) | publisher record; screening-only | [[03_Literature/Sources/source-2026-mecanum-crowd-control-refresh]] | pedestrian-aware MPC and interaction metric boundary | 2026-08-13 |
| eightwheelmecanum2026 | [10.3390/electronics15112441](https://doi.org/10.3390/electronics15112441) | publisher record; screening-only | [[03_Literature/Sources/source-2026-mecanum-crowd-control-refresh]] | Mecanum architecture and physical-validation boundary | 2026-08-13 |
| tadano2025attentioncollision | [10.1299/jsmermd.2025.2P1-E05](https://doi.org/10.1299/jsmermd.2025.2P1-E05) | publisher/project page; screening-only | [[03_Literature/Sources/source-tadano-pedestrian-attention-2025]] | attention-aware prediction and cost-map adaptation boundary | 2026-08-13 |
| agrawal2025rpidataset | [arXiv:2503.16481](https://arxiv.org/abs/2503.16481) | workshop/preprint; screening-only | [[03_Literature/Sources/source-agrawal-rpi-dataset-2025]] | robot–pedestrian interaction conditions and metadata boundary | 2026-08-13 |

## Dataset screening candidates — not admitted

| Candidate group | Note | Status | Gap/evaluation role |
|---|---|---|---|
| Oxford-IHM, JRDB/JRDB-Pose, SiT, NavWareSet, uB-VisioGeol | [[03_Literature/Sources/source-dataset-candidates-2026]] | screening; no Zotero admission or freeze; NavWareSet processed CSV/JSON route identified, but raw sensor release includes ROS bags and tutorial license is unresolved; JRDB download requires login | real context, robot-view OOD, overlay and direct CSV/JSON feasibility |

Ba mươi hai bản ghi dự án đã được nhập vào Zotero cùng 32 PDF và đã kiểm bằng local
API ở chế độ chỉ đọc: không thiếu child attachment, không có DOI chuẩn hóa trùng,
không thiếu title/DOI/creator/date. Portable BibTeX và receipt được khóa tại
`references/zotero/export/`. Đủ 32 PDF có SHA-256; 27 PDF kế thừa thiếu URL và
thời điểm tải gốc nên giữ trạng thái `legacy-origin-unresolved`. Tuy vậy, cây
collection hiện có 0 collection và việc tổ chức tag chưa hoàn tất; screening decision,
kiểm phiên bản, correction/retraction và independent review chưa hoàn tất; do đó
bounded focused audit đã được review; đây vẫn chưa phải tập trích dẫn cuối vì
collection/tag, correction/retraction, provenance và independent-review checks
được giữ như cổng phát hành riêng.

## Hồ sơ PR01 lịch sử (không phải workflow active)

Các đoạn dưới đây chỉ giữ provenance của kế hoạch systematic-search cũ. Chúng
không phải yêu cầu của bài báo nghiên cứu gốc và không được dùng để chặn code,
mô phỏng hoặc thực nghiệm.

Search plan `pr01-search-v3` đã được khóa trước execution: năm database, sáu
concept block và 30 exact query. IEEE Xplore, Crossref và Semantic Scholar là
ba nguồn bắt buộc của vòng hiện tại, tương ứng 18 query. WoS Core Collection và
Scopus giữ query đã khóa nhưng ở trạng thái `access-blocked`: đăng nhập tài khoản
cá nhân không cung cấp quyền Core Collection/document search. Trạng thái này là
giới hạn truy cập, không phải bằng chứng đã tìm hai database đó và cũng không cho
phép tuyên bố nguồn mở thay thế tương đương.

Tại thời điểm cập nhật, Crossref và Semantic Scholar đã hoàn tất **12/18
execution** và bundle đã qua kiểm tra hash/byte/count/pagination trước khi promote
vào `references/literature/raw/`. Manifest raw vẫn giữ `IN-PROGRESS` vì sáu truy
vấn IEEE chưa xuất được CSV toàn bộ; hộp Export trên giao diện yêu cầu tài khoản
cá nhân. Sáu truy vấn IEEE đã được xem ở mức screening theo cửa sổ năm và không
được đưa vào flow count cuối. WoS/Scopus vẫn access-blocked. Với Semantic Scholar,
search plan v3 đã khóa rõ các trường
sàng lọc phải giữ: `paperId`, `title`, `abstract`, `authors`, `year`,
`publicationDate`, `venue`, `externalIds`, `publicationTypes`, `url` và
`openAccessPdf`.

## Chênh lệch screening hiện tại

Xem [[03_Literature/prior-art-delta]]. Ghi chú này nhận diện hai mươi
ba nguồn ưu tiên cao; ma trận toàn văn mở rộng chứa hai mươi lăm nguồn
gần/phạm vi/cơ chế. Dòng Ono--Paulson--Barbosa đã chiếm allocation theo
constraint--time/online SMPC; Wang 2025--2026 chiếm adaptive/learned fixed-total
allocation; Parimi--Williams chiếm transparent shared-budget redistribution;
Engelaar--Lazar--Haesaert chiếm adaptive probability levels dưới total budget
cùng closed-loop theory; Bonzanini--Mesbah--Di Cairano đặt chuẩn mạnh cho
perception-aware chance-constrained feasibility/stability.
P-Chekov cung cấp comparator fixed-total feasibility reallocation trực tiếp;
Huang--Jafari và Zhang et al. tiếp tục bác novelty tích hợp predictor--MPC/NMPC;
Ren et al. đặt thêm chuẩn finite-sample GMM và recursive-feasibility có điều kiện.
Không nguồn screening-only nào được gọi là trích dẫn cuối. Tập citation cuối
chỉ mở sau khi collection/tag, correction/retraction, provenance và independent
review checks của từng nguồn được trích dẫn đạt; đây là cổng phát hành, không
phải lý do để khôi phục PR01/SLR.

## Nhật ký truy vấn

| ID truy vấn | Database | Truy vấn chính xác | Ngày | Số hit | Export/manifest | Ghi chú |
|---|---|---|---|---:|---|---|
| Q-20260801-WEB-01 | Triage web nhà xuất bản/arXiv | context-aware and chance-constrained MPC; risk allocation; human prediction; 2023--2026 | 2026-08-01 | chỉ screening | [[03_Literature/prior-art-delta]] | Không phải số hit từ database hệ thống; chỉ dùng để nhận diện công trình gần nhất cần audit gấp. |
| Q-20260801-WEB-02 | Full-text snowballing có mục tiêu | risk-adaptive CVaR; context-aware fixed total risk budget; human--horizon risk allocation; 2024--2026 | 2026-08-01 | không dùng làm flow count | [[03_Literature/nearest-work-matrix]] | Tìm thấy PA-10 và PA-11; đủ để bác claim rộng nhưng chưa thay cho search database tái lập. |
| Q-20260801-WEB-03 | Snowballing dòng risk allocation | adaptive/online/iterative risk allocation; constraint--time; shared global budget | 2026-08-01 | không dùng làm flow count | [[03_Literature/nearest-work-matrix]] | Tìm thấy PA-12--PA-15; củng cố khuyến nghị `PIVOT-EMPIRICAL`. |
| Q-20260801-WEB-04 | Triage web theo domain nhà xuất bản/arXiv | `("risk allocation" OR "adaptive risk") AND (MPC OR NMPC) AND (robot OR human OR pedestrian)`; nhánh exact-title/full-text | 2026-08-01 | không dùng làm flow count | [[03_Literature/nearest-work-matrix]] | Tìm thấy PA-16--PA-18; bác theory/integration claim rộng. Không thay thế 18 execution bắt buộc trên IEEE Xplore, Crossref và Semantic Scholar; WoS/Scopus là query plan bị chặn truy cập. |
| Q-20260801-WEB-05 | Full-text targeted snowballing | `risk allocation chance constrained MPC trajectory planning`; `human trajectory prediction chance constrained MPC LSTM`; exact-title full text | 2026-08-01 | không dùng làm flow count | [[03_Literature/nearest-work-matrix]] | Tìm thấy PA-19--PA-21 và tải bản toàn văn `[28]`--`[30]`; không thay thế database export. |
| Q-20260801-WEB-06 | Triage web nguồn sơ cấp | `risk allocation MPC human trajectory`; `multimodal chance-constrained MPC`; `mecanum torque NMPC`; exact-title/DOI | 2026-08-01 | không dùng làm flow count | [[03_Literature/nearest-work-matrix]] | Tìm thấy PA-22--PA-23; củng cố việc rút claim probability/recursive feasibility. Không thay thế raw database export. |

Related hub: [[00_MOC/project-map]]

## Search refresh log — 2026-08-12

The following candidates were found or rechecked during the Google/web refresh
and are linked to the focused-source note. They are screening updates only;
they do not add a systematic-review count or replace the full-text/Zotero audit.

| Candidate | Landing page | Current use | Boundary |
|---|---|---|---|
| Liu et al. 2026, ARMS | [arXiv:2601.16686](https://arxiv.org/abs/2601.16686) | boundary comparator for LSTM context, MPC safety filtering and DWA | preprint; venue and independent reproduction still open |
| Akhtyamov et al. 2026, neural chance-constrained MPC | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1751570X26000774) | boundary comparator for learned prediction, robust conformal uncertainty and chance-constrained control | publisher record/abstract refresh; detailed extraction remains open |
| Busellato et al. 2026, UA-PCBF | [Robotics and Autonomous Systems](https://www.sciencedirect.com/science/article/pii/S0921889025003884) | adjacent safety-filter comparator for probabilistic human forecasting and real HRI | not yet admitted to the full-text nearest-work matrix |
| Engelaar et al. 2026, elastic chance constraints | [DOI landing page](https://doi.org/10.1016/j.sysconle.2026.106474) | nearest prior art for adaptive risk values under a total bound | full-text note exists; correction/retraction audit remains open |
| Dyakov and Fedorov 2024/online 2025, Mecanum dynamics | [Publisher record](https://journal.hep.com.cn/2074-0530/EN/10.17816/2074-0530-629873) | plant and drive-torque boundary prior | metadata/abstract note; no CCA or human-aware NMPC |
| Trepella et al. 2026, SFM-NMPC | [Accepted IROS version](https://arxiv.org/abs/2607.10374) | benchmark and human-aware NMPC boundary prior | accepted preprint; final proceedings and correction audit open |
| Crowd navigation in a multi-room environment 2026 | [Frontiers full text](https://doi.org/10.3389/frobt.2026.1812386) | multi-sensor MPC and real-robot boundary prior | differential-drive TIAGo, not Mecanum; Zotero admission open |
| HumAIN 2026 | [arXiv record](https://arxiv.org/abs/2607.07357) | learned social-cue/perception boundary prior | abstract-only preprint; not a control or allocator comparator |
| Chen et al. 2026, SAL-TD3 | [Scientific Reports](https://doi.org/10.1038/s41598-026-45819-0) | LSTM plus reinforcement-learning dynamic-navigation boundary prior | abstract-level refresh; full-text/Zotero and independent reproduction open |
| Direction-aware TTC with pose-guided LiDAR grounding 2026 | [Engineering Applications of Artificial Intelligence](https://doi.org/10.1016/j.engappai.2026.115660) | embedded direction/TTC and camera--LiDAR association boundary for Astra-S/N10P measurement design | early-online screening only; full-text, dataset and pretraining-overlap audit open |
| Ghani et al. 2025, Dyna-LfLH | [author-maintained IROS record](https://www.cs.utexas.edu/~pstone/Papers/bib2html/b2hd-dyna_lflh_icra_2025.html) | self-supervised motion-planner and sim/real evaluation boundary | screening-only; not imported into Zotero or used as quantitative evidence |
| OA-MPC; model-free safety-critical MPC; Mecanum AVPSMO-MPC; MPC-DMP (2024--2025) | [[03_Literature/web-verified-gap-sources]] · [TCST DOI](https://doi.org/10.1109/TCST.2024.3520462) · [T-IV DOI](https://doi.org/10.1109/TIV.2024.3389111) · [ISA DOI](https://doi.org/10.1016/j.isatra.2024.05.050) · [RAS DOI](https://doi.org/10.1016/j.robot.2025.105027) | four-way overlap audit for safety MPC, Mecanum control and learning-plus-MPC | 2026-08-14 screening-only; exact-title Zotero searches had no local match; no citation or evidence admission |
| Gravina et al. crowd MPC; Pham--Han hybrid Mecanum control; official YOLO26-pose documentation | [[03_Literature/web-verified-gap-sources]] · [Frontiers DOI](https://doi.org/10.3389/frobt.2026.1812386) · [SAGE DOI](https://doi.org/10.1177/18758967251394861) · [Ultralytics pose docs](https://docs.ultralytics.com/tasks/pose) | current overlap audit for multisensor crowd MPC, Mecanum control architecture and perception-tool semantics | 2026-08-14 screening-only; no Zotero write; no manuscript or evidence admission |

Related: [[03_Literature/web-verified-gap-sources]] · [[04_Research_Gap/research-gap]]

## Search refresh log — 2026-08-14 (uncertainty-aware MPC and Mecanum benchmark check)

The current Google/web refresh checked recent uncertainty-aware obstacle MPC,
holonomic/Mecanum control, and human-aware navigation records. They remain
screening-only knowledge links; no Zotero export, manuscript citation, or
experimental evidence is admitted from this refresh.

| Candidate boundary | Landing page | Screening consequence |
|---|---|---|
| Prediction-uncertainty-aware obstacle MPC (IFAC 2025) | [DOI](https://doi.org/10.1016/j.ifacol.2025.10.245) | supports uncertainty as an established comparator; does not establish matched CCA allocation |
| Ellipsoidal-obstacle MPC with wheeled-robot validation (Mechatronics 2025) | [DOI](https://doi.org/10.1016/j.mechatronics.2025.103386) | supports geometric/real-robot benchmarking; platform and risk interface differ |
| Social navigation through constrained optimization (RAS 2025) | [DOI](https://doi.org/10.1016/j.robot.2024.104830) | supports human-aware uncertainty comparison; not the same Mecanum/CCA pipeline |
| Holonomic-robot MPC obstacle avoidance (CCE 2025) | [DOI](https://doi.org/10.1109/CCE67728.2025.11272001) | supplies a Mecanum-relevant baseline boundary; does not replace matched hardware data |
| Mecanum obstacle-avoidance MPC | [DOI](https://doi.org/10.1016/j.ifacol.2021.08.533) | confirms the plant/control baseline; no context-aware learned risk allocation |

Related: [[03_Literature/web-verified-gap-sources]] · [[04_Research_Gap/research-gap]]

## Search refresh log — 2026-08-14 (real-robot metrics and MPPI overlap)

| Candidate | Landing page | Current use | Boundary |
|---|---|---|---|
| Cane-robot accompaniment with dynamic cost maps and MPC (2026) | [ROBOMECH Journal](https://doi.org/10.1186/s40648-026-00345-6) | real-robot clearance and timing protocol comparator | different platform and task; screening-only |
| Mecanum MPPI with barrier-function constraints (2025/2026 record) | [Journal of Robotics and Control](https://doi.org/10.18196/jrc.v6i6.27770) | MPPI/CBF baseline boundary | simulation-oriented record; not admitted as physical evidence |
| HOFA-LESO omnidirectional/Mecanum tracking control (2026) | [ScienceDirect DOI](https://doi.org/10.1016/j.robot.2026.105492) | disturbance-rejection and tracking comparator | not CCA or human-context control; screening-only |
| Decentralized physical MPC for cooperative transport (2026) | [Scientific Reports](https://doi.org/10.1038/s41598-026-41881-w) | experimental reporting and timing-pattern comparator | differential-drive/ROS 2 platform; not matched hardware evidence |

Related: [[03_Literature/web-verified-gap-sources]] · [[04_Research_Gap/research-gap]]

## Search refresh log — 2026-08-14 (hardware and Mecanum overlap)

These records are screening-only additions from the current Google/web refresh.
They are linked for knowledge synthesis and are not manuscript citations or
experimental evidence until the full-text and Zotero checks are complete.

| Candidate | Landing page | Current use | Boundary |
|---|---|---|---|
| Model predictive control with residual learning and real-time disturbance rejection (2025) | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0967066125003491) | Mecanum experimental-control comparator | publisher abstract screened; full-text extraction and independent reproduction remain open |
| Gnimady et al., integrated estimation and predictive control for safe industrial mobile-robot navigation (2026) | [Springer DOI](https://doi.org/10.1007/s11370-025-00661-7) | LiDAR/RADAR/IMU estimation and NMPC integration boundary | not Mecanum-specific; quantitative claims are not admitted |
| Cipriano et al., singularity-free trajectory tracking for steerable wheeled mobile robots (2025) | [IEEE RA-L DOI](https://doi.org/10.1109/LRA.2025.3564209) | geometric/control benchmark boundary | steerable-wheel platform, not CCA-NMPC; full-text comparison remains open |
| Chance-Constrained Sampling-Based MPC for Collision Avoidance in Uncertain Dynamic Environments (IEEE RA-L, 2025) | [IEEE Xplore](https://ieeexplore.ieee.org/abstract/document/11021391) · [[03_Literature/Sources/source-c2u-mppi-2025]] | direct chance-constrained MPPI comparator; reinforces matched MPPI, timing and real-world evaluation requirements | publisher abstract only; exact Zotero/full-text reconciliation remains open |

Related: [[03_Literature/web-verified-gap-sources]] · [[04_Research_Gap/research-gap]]



