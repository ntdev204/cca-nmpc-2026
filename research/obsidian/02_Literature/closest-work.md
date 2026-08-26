---
domain: literature
type: note
status: locked
scope: focused-non-systematic-doi-audit
evidence: focused-doi-audit-nonexhaustive
tags: [closest-work, prior-art]
---

# Closest prior work

## Human-aware MPC and learning

| Work | Established capability | Boundary for this study |
|---|---|---|
| [Stefanini et al., 2024](https://doi.org/10.1109/LRA.2024.3461552) | Human pose/activity context and motion prediction in efficient MPC, including robot validation | Context-aware MPC itself is not new |
| [Akhtyamov et al., 2025](https://doi.org/10.1016/j.robot.2024.104830) | Uncertainty-aware social costs and constraints are evaluated in simulation and on a mobile robot with a perception--tracking--navigation pipeline | Human uncertainty can already enter constrained MPC directly; comparisons must respect the narrower current-direction context used here |
| [Chen et al., 2023](https://doi.org/10.1007/s10514-023-10103-x) | RGB--LiDAR human tracking and trajectory prediction modify both global planning and TEB command generation | It changes the global route and outputs commands, whereas the present global path is immutable and only NMPC may command the robot |
| [Kobayashi et al., 2022](https://doi.org/10.1007/s12369-021-00791-9) | An omnidirectional robot generates interaction-aware local-path candidates and selects among them in crowd experiments | This is a close local-planning anchor; the distinctions are the causal context interface, GA search, and downstream NMPC contract |
| [Perez et al., 2025](https://doi.org/10.1007/s12369-024-01135-z) | A Social Elastic Band deforms local paths using predicted motion and proxemic spaces for an omnidirectional robot | Context-conditioned local-path deformation is established; it is an eligible matched local-generator baseline after fixing the same global path and NMPC backend |
| [Boldrer et al., 2022](https://doi.org/10.1016/j.robot.2021.103979) | A multi-agent architecture separates global, local, and reactive navigation and incorporates near-future human motion | Global--local separation and predictive local adaptation are established; the retained question is the value of the exact two-rate CCA interface |
| [Ge et al., 2025](https://doi.org/10.1007/s12369-024-01193-3) | Continuous spatiotemporal routing changes a route using predicted crowd evolution | Continuously varying context in local routing is established broadly; novelty cannot rest on the word continuous |
| [Kang et al., 2024](https://doi.org/10.3390/s24154862) | Perceived social type changes asymmetric personal space and navigation costs | Context-shaped directional geometry is prior art and requires independent calibration before any comfort claim |
| [Stratton et al., 2026](https://doi.org/10.1145/3757279.3788664) | A controlled HRI study links human-motion prediction quality to downstream robot and human outcomes | ADE alone is not a navigation metric; the matched CCA test must report downstream outcomes |
| [Neggers et al., 2021](https://doi.org/10.1007/s12369-021-00805-6) | Robot-passing experiments show that personal-space shape and size depend on context and are asymmetric | Directional radii are a prior modeling choice; this study cannot claim comfort without its own calibration |
| [Zhao et al., 2021](https://doi.org/10.1109/ROBIO54168.2021.9739433) | An asymmetric Gaussian model incorporates human motion-related cues into navigation | The directional exclusion region is not new and is used only as an uncalibrated geometric context model |
| [Brito et al., 2019](https://doi.org/10.1109/LRA.2019.2929976) | Model-predictive contouring jointly optimizes local motion and commands around moving agents, with onboard experiments | Planner--controller integration and moving-agent ellipsoids are established; its authority differs from the separated CCA-to-NMPC contract |
| [SICNav, 2025](https://doi.org/10.1109/TRO.2024.3484634) | Interactive crowd navigation through bilevel MPC | Safe/interactive crowd MPC is not new |
| [SICNav-Diffusion, 2025](https://doi.org/10.1109/LRA.2025.3585713) | Learned multimodal trajectory prediction embedded in bilevel MPC | Learning plus predictive control is not new |
| [GO-MPC, 2021](https://doi.org/10.1109/LRA.2021.3068662) | A learned policy recommends subgoals while MPC computes commands | Bounded learning above MPC is not new |
| [Wang et al., 2025](https://doi.org/10.3390/s25072014) | A DWA local planner receives the global path, robot state and local sensing; MPC tracks the resulting local path, with simulation and robot experiments | A global-path-to-local-path-to-MPC hierarchy is not new; it is the closest interface baseline and must be matched at the system level |
| [Zhang et al., 2023](https://doi.org/10.1109/LRA.2023.3284354) | Reinforcement learning generates path points while a separate motion module fine-tunes execution, with simulation and hardware | Separating learned path generation from motion execution is not new; the active study differs only in context representation, GA search, Mecanum embodiment and NMPC backend |
| [Imad et al., 2022](https://doi.org/10.3390/s22218101) | Learned drivable space, robot state and a global plan enter NMPC local motion planning that outputs velocity commands | Learning, a global plan and NMPC in one local-navigation stack are established; the present CCA instead outputs a geometric path and cannot claim this integration |
| [Singamaneni et al., 2021](https://doi.org/10.1109/IROS51168.2021.9636613) | A tunable planner handles diverse human--robot interaction contexts and is evaluated in simulation and on a robot | Human-context-aware planning is not new; only the measured value of the exact current-context interface remains testable |
| [Crowd MPC, 2026](https://doi.org/10.3389/frobt.2026.1812386) | RGB-D/LiDAR fusion, crowd prediction, local planning, MPC, and hardware | Perception-integrated crowd MPC is not new |
| [Oleinikov et al., 2024](https://doi.org/10.1016/j.conengprac.2023.105769) | Scenario-tree NMPC uses probabilistic human predictions, proves recursive feasibility/stability and reports human-interaction experiments | This is stronger prior art for explicit human prediction; the present study tests a narrower current-context interface |
| [Nurbayeva and Rubagotti, 2025](https://doi.org/10.1016/j.conengprac.2024.106155) | Point/set-terminal NMPC for shared workspaces, with recursive-feasibility and stability results under a static-human assumption | Terminal constraints and their fixed-assumption stability analysis are not new contributions |
| [Li et al., 2026](https://doi.org/10.1016/j.ejcon.2026.101572) | A model predictive planner uses a participant-calibrated spring--mass human--robot interaction model for tethered guidance | HRI-aware model predictive planning and participant-level calibration are established; embodiment and interface differ |

## LSTM local planning

| Work | Established capability | Boundary for this study |
|---|---|---|
| [Guo et al., 2021](https://doi.org/10.3103/S014641162101003X) | An LSTM local planner is trained from fuzzy-controller samples for unknown environments | LSTM-based local planning is not new; the present LSTM estimates only current human context and does not output the path or commands |
| [Guo et al., 2021](https://doi.org/10.1155/2021/5524232) | LSTM, fuzzy control, and reinforcement learning are fused for mobile-robot local planning | Combining recurrent learning with an adaptive local planner is established; the active CCA uses GA only and requires a matched context-value test |
| [Molina-Leal et al., 2021](https://doi.org/10.3390/app112210689) | LiDAR, robot, and goal inputs are mapped by LSTM to linear and angular velocity in a dynamic simulated environment | Direct learned command generation is established but intentionally excluded; NMPC remains the sole command generator here |
| [Amirhosseini et al., 2025](https://doi.org/10.1007/s11063-024-11671-4) | CNN--LSTM imitation maps local sensing and a global-path segment to steering commands | LSTM command generation and computational savings are prior art; the present LSTM may estimate only current human context |
| [Yang et al., 2024](https://doi.org/10.1109/TCYB.2024.3359237) | Interaction-aware LSTM predicts full pedestrian trajectories on public datasets | This is a predictor reference, not a navigation baseline; direction classes require macro-F1 and a confusion matrix rather than ADE/FDE claims |

## Closest evolutionary and people-aware planning

| Work | Established capability | Precise distinction from this study |
|---|---|---|
| [UbiPaPaGo, 2011](https://doi.org/10.1016/j.eswa.2010.09.077) | Spatial conceptual maps and GA produce context-aware paths for human-centered ubiquitous-network services | It establishes context-plus-GA path planning, but not continuous current-context updating for Mecanum local navigation |
| [Bacchin et al., 2021](https://doi.org/10.1109/ECMR50962.2021.9568804) | GA trains a ROS navigation stack to produce people-aware trajectories under moving-person disturbances and proxemic objectives in Gazebo | It establishes people-aware trajectory adaptation with GA, but not the proposed fixed-global-path Mecanum local-path interface |
| [Sampathkumar et al., 2023](https://doi.org/10.1007/978-3-031-46778-3_15) | GA tunes artificial-potential-field parameters for human-aware autonomous-mobile-robot navigation | Human-aware objectives optimized by GA are not new; the planning representation and controller contract differ |
| [Bakdi et al., 2017](https://doi.org/10.1016/j.robot.2016.12.008) | GA path search, PCHIP smoothing, explicit robot/obstacle geometry, tracking control, sensor fusion, and physical-robot execution | A GA-to-smoothed-path-to-controller pipeline and footprint-aware validation are not new; the controller is not terminal NMPC and human context is not the conditioning variable |
| [Ou et al., 2025](https://doi.org/10.1016/j.asoc.2025.113167) | GPU evolutionary dynamic programming initializes local GA refinement in dynamic environments on an edge mobile robot, reporting approximately 0.1 s per path | Fast local GA and edge deployment are not new; continuously updated human context for fixed-path Mecanum local planning is not its focus |
| [Rodriguez Ramirez et al., 1999](https://doi.org/10.1109/ROBOT.1999.770473) | GA performs online nonlinear optimization inside model-based predictive control for mobile-robot navigation, including speed limits and robot experiments | GA-plus-predictive-control is not new; here GA is deliberately upstream of, rather than the solver inside, NMPC |
| [Song and Huh, 2021](https://doi.org/10.1177/16878140211027669) | A risk supervisor and micro-GA solve nonconvex MPC collision avoidance with moving obstacles and timing constraints | GA is inside Ackermann motion control rather than a Continuous Context-Aware Mecanum local-path layer |
| [Kim et al., 2024](https://doi.org/10.3390/robotics13030046) | Selective MPC, potential fields, and PSO generate local paths and are evaluated on a Jetson-equipped AGV | Population-search predictive local planning and embedded execution are not new; dynamic-human context, terminal admission, and Lyapunov-bounded NMPC differ |
| [Nam and Kim, 2024](https://doi.org/10.1007/s12555-024-0543-7) | MPPI and GA integrate task assignment, planning, and UGV control | GA/MPPI integration is established; the fixed global path, human-context genotype, Mecanum model, and terminal governor are absent |
| [Li et al., 2021](https://doi.org/10.1177/00202940211043070) | APF local planning is composed with tracking control and explicit MPC | Layered local planning and predictive tracking are not new; the planner, switching logic, embodiment, and evidence are materially different |

## Mecanum motion control

[Moreno et al., 2021](https://doi.org/10.1016/j.ifacol.2021.08.533)
already formulate Mecanum MPC with dynamics, actuator response, and obstacle
constraints. [Wang et al., 2024](https://doi.org/10.1016/j.isatra.2024.05.050)
combine a sliding-mode observer with constrained Mecanum MPC; their reported
Lyapunov proof concerns the observer, not a general proof for the complete MPC
loop. [Akbar et al., 2024](https://doi.org/10.1016/j.heliyon.2024.e26829)
demonstrate real-time dynamic-obstacle navigation for a Mecanum robot.
[Zhang et al., 2025](https://doi.org/10.1016/j.conengprac.2025.106587)
combine sparse-GP residual learning, disturbance estimation and MPC on a
Mecanum robot with indoor/outdoor tracking experiments. Learning-enhanced
Mecanum MPC and disturbance-aware tracking are therefore not contributions of
the present design.

[Cenerini et al., 2023](https://doi.org/10.1016/j.conengprac.2022.105406)
provide a stronger motion-control anchor: model-predictive path following for a
holonomic mobile robot with a rigorous closed-loop asymptotic-stability proof
and experimental validation. Stability of holonomic predictive path following
is therefore not a novelty claim for this study; the present Lyapunov result is
only a supporting fixed-reference property of its chosen terminal NMPC.

## Planning and control theory

Real-time GA obstacle avoidance is already investigated
[Gyenes et al., 2023](https://doi.org/10.3390/s23063039). Terminal-set NMPC
stability and tracking are classical results
[Chen and Allgower, 1998](https://doi.org/10.1016/S0005-1098(98)00073-9),
[Mayne et al., 2000](https://doi.org/10.1016/S0005-1098(99)00214-9),
[Kohler et al., 2020](https://doi.org/10.1109/TAC.2019.2949350).

Reference governors are a mature constrained-control architecture
[Garone et al., 2017](https://doi.org/10.1016/j.automatica.2016.08.013).
Terminal-set and terminal-state feasibility governors already provide formal
MPC/NMPC feasibility mechanisms
[Liao-McPherson et al., 2023](https://doi.org/10.1109/TAC.2022.3216967),
[Convens et al., 2024](https://doi.org/10.1109/TCST.2024.3365996). The latter is
not limited to a static target; it treats nonlinear terminal-state feasibility
over arbitrary horizons and is the stronger governor anchor for this study.

[PathFG, 2025](https://doi.org/10.48550/arXiv.2507.09134) is the closest
governor-architecture work in the focused set. It connects a path planner to NMPC through a path
feasibility governor, supports replanning, and establishes constraint
satisfaction, recursive feasibility, and asymptotic stability. It is currently
a preprint and its simulation platform is a quadrotor, but it invalidates any
claim that planner--governor--NMPC integration or command-authority separation
is new. A PathFG-style deterministic progression must be included as a matched
interface baseline.

Evolutionary and dynamically constrained trajectory generation also predates
this study. Evolutionary time scaling has handled actuator constraints
[Kim and Choi, 1999](https://doi.org/10.1016/S0020-0255(98)10052-X);
differential-drive trajectory planning has incorporated motor-input bounds
[Kim and Kim, 2015](https://doi.org/10.1016/j.robot.2014.11.001); and bounded
parametric search has treated obstacle, kinodynamic, and dynamic constraints for
a wheeled robot with a trailer
[Bouzar Essaidi et al., 2022](https://doi.org/10.1016/j.mechmachtheory.2021.104605).
Consequently, inverse model decoding, time scaling, constrained search, or
penalty handling alone cannot support novelty. The proposed bounded homotopy
repair must be compared against penalty-only and decoder-only variants and must
show downstream value, not merely produce feasible references.

Constraint handling and repair within evolutionary algorithms are mature topics
[Coello Coello, 2002](https://doi.org/10.1016/S0045-7825(01)00323-1),
[Salcedo-Sanz, 2009](https://doi.org/10.1016/j.cosrev.2009.07.001). Decoder-based
feasible mappings also predate this work
[Koziel and Michalewicz, 1999](https://doi.org/10.1162/evco.1999.7.1.19).
Likewise, predictive and generalized reference governors already modify or
interpolate references under constraints
[Bemporad et al., 1998](https://doi.org/10.1016/S0166-3615(97)00098-5),
[Gilbert and Kolmanovsky, 2002](https://doi.org/10.1016/S0005-1098(02)00135-8).
The finite homotopy used here is therefore an engineering mechanism, not a new
class of evolutionary repair or reference governor.

## Consequence

The study must make its case through continuous context updating, fixed-path
Mecanum local-path generation, holonomic ablation, and causal matched
comparisons. The path-to-control interface is a design boundary, not a
contribution. LSTM local planning, direct LSTM command generation,
context-plus-GA, people-aware evolutionary
planning, GA followed by a tracking controller, online GA inside predictive
control, micro-GA MPC, population-search predictive planning, and fast local GA
must also be treated as prior art. The remaining
position is a candidate systems mechanism, not an established novelty claim.

The locked context boundary uses only current position, speed, coarse direction,
confidence, and age. Dataset partitions, sample size, seed namespaces, search
budgets, statistical families, and timing gates are future preregistration items
in `IMPLEMENTATION_PLAN.md`; none is current evidence. Desktop Python and MATLAB
latencies cannot support a real-time claim.

This focused DOI set is non-exhaustive. It narrows and falsifies candidate
claims but does not establish that no closer work exists.

## Links

[[02_Literature/evidence-synthesis]] · [[02_Literature/core-doi-sources]] ·
[[01_Problem/research-gap]] · [[03_Theory/architecture]] ·
[[04_Evaluation/baseline-contract]]
