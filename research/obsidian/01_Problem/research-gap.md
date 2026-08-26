---
domain: problem
type: note
status: locked
scope: theory-only
claim_status: candidate
evidence: focused-doi-audit-nonexhaustive
tags: [research-gap, q1, falsifiable]
---

# Research gap

## What is already established

Context-aware MPC with human pose/activity and real-robot validation already
exists [Stefanini et al., 2024](https://doi.org/10.1109/LRA.2024.3461552).
Interactive crowd MPC and learned multimodal prediction inside MPC are also
established [Samavi et al., 2025](https://doi.org/10.1109/TRO.2024.3484634),
[SICNav-Diffusion, 2025](https://doi.org/10.1109/LRA.2025.3585713). Learning
above an MPC command layer is not new either
[GO-MPC, 2021](https://doi.org/10.1109/LRA.2021.3068662). Mecanum MPC and GA
obstacle avoidance are prior art
[Moreno et al., 2021](https://doi.org/10.1016/j.ifacol.2021.08.533),
[Gyenes et al., 2023](https://doi.org/10.3390/s23063039).
Scenario-based NMPC has already combined probabilistic human predictions,
recursive-feasibility/stability analysis and human-interaction experiments
[Oleinikov et al., 2024](https://doi.org/10.1016/j.conengprac.2023.105769).
Set-terminal NMPC for shared workspaces has also proved recursive feasibility
and closed-loop stability under a stated static-human assumption
[Nurbayeva and Rubagotti, 2025](https://doi.org/10.1016/j.conengprac.2024.106155).
A model predictive planner with an experimentally calibrated human--robot
interaction model further shows that HRI-aware planning and participant-level
validation are established
[Li et al., 2026](https://doi.org/10.1016/j.ejcon.2026.101572).
Residual learning plus disturbance rejection has been experimentally combined
with MPC on a Mecanum robot
[Zhang et al., 2025](https://doi.org/10.1016/j.conengprac.2025.106587).
Reference and feasibility governors are also established
[Garone et al., 2017](https://doi.org/10.1016/j.automatica.2016.08.013),
[Convens et al., 2024](https://doi.org/10.1109/TCST.2024.3365996). PathFG already
integrates path planning, a feasibility governor, and NMPC with recursive
feasibility, stability, and replanning
[Zhang et al., 2025](https://doi.org/10.48550/arXiv.2507.09134). Planner--NMPC
integration, reference admission, and exclusive MPC command authority are
therefore not research gaps by themselves.

The global-path-to-local-path-to-MPC hierarchy is directly established by an
integrated DWA--MPC framework with simulation and robot experiments
[Wang et al., 2025](https://doi.org/10.3390/s25072014). It is therefore an
interface-matched baseline, not an architectural novelty target.

Omnidirectional interaction-aware local planning
[Kobayashi et al., 2022](https://doi.org/10.1007/s12369-021-00791-9) and the
Social Elastic Band for anticipated human motion
[Perez et al., 2025](https://doi.org/10.1007/s12369-024-01135-z) also establish
human-conditioned local-path generation. They are closer local-generator
comparators than generic navigation controllers.

Continuous spatiotemporal routing
[Ge et al., 2025](https://doi.org/10.1007/s12369-024-01193-3), social-type-aware
asymmetric personal space
[Kang et al., 2024](https://doi.org/10.3390/s24154862), and multi-agent
global--local--reactive navigation
[Boldrer et al., 2022](https://doi.org/10.1016/j.robot.2021.103979) further rule
out broad novelty claims for continuous context, directional human regions, or
layered navigation. A controlled downstream study also shows that human-motion
prediction error alone does not reliably determine navigation or human
experience [Stratton et al., 2026](https://doi.org/10.1145/3757279.3788664).

Learned path generation followed by a separate motion module
[Zhang et al., 2023](https://doi.org/10.1109/LRA.2023.3284354), learned
perception plus global-plan NMPC local motion planning
[Imad et al., 2022](https://doi.org/10.3390/s22218101), and tunable planning for
diverse human--robot contexts
[Singamaneni et al., 2021](https://doi.org/10.1109/IROS51168.2021.9636613)
further rule out novelty for modularity, learning-to-control integration, or
human-context-aware planning alone.

LSTM local planning is established as well. Prior work trains an LSTM local
planner from fuzzy-controller samples
[Guo et al., 2021](https://doi.org/10.3103/S014641162101003X), combines LSTM
with fuzzy control and reinforcement learning for local planning
[Guo et al., 2021](https://doi.org/10.1155/2021/5524232), and maps LiDAR, robot,
and goal inputs through LSTM directly to velocity commands
[Molina-Leal et al., 2021](https://doi.org/10.3390/app112210689). Thus, neither
LSTM local planning nor learned command generation is a gap.

The intersection of context, people awareness, and evolutionary search is also
established. UbiPaPaGo combines a spatial context representation with GA path
planning [Wang et al., 2011](https://doi.org/10.1016/j.eswa.2010.09.077).
People-aware trajectories have been learned by GA through a ROS navigation
stack with moving people and proxemic objectives
[Bacchin et al., 2021](https://doi.org/10.1109/ECMR50962.2021.9568804), while
GA has tuned an artificial-potential-field formulation for human-aware
navigation [Sampathkumar et al., 2023](https://doi.org/10.1007/978-3-031-46778-3_15).
GA--PCHIP planning followed by a tracking controller, with explicit robot and
obstacle geometry, has physical-robot evidence
[Bakdi et al., 2017](https://doi.org/10.1016/j.robot.2016.12.008). Online
nonlinear predictive control solved by GA predates this study
[Rodriguez Ramirez et al., 1999](https://doi.org/10.1109/ROBOT.1999.770473),
and GPU local GA optimization in dynamic environments has been demonstrated on
an edge robot at approximately 0.1 s per path
[Ou et al., 2025](https://doi.org/10.1016/j.asoc.2025.113167).
Micro-GA MPC collision avoidance, selective MPC--PSO local planning, integrated
GA--MPPI planning/control, and APF-local-planner--MPC composition are also
established
[Song and Huh, 2021](https://doi.org/10.1177/16878140211027669),
[Kim et al., 2024](https://doi.org/10.3390/robotics13030046),
[Nam and Kim, 2024](https://doi.org/10.1007/s12555-024-0543-7),
[Li et al., 2021](https://doi.org/10.1177/00202940211043070).
Consequently, context-plus-GA, people-aware GA, GA followed by control,
GA-plus-predictive-control, population-search predictive planning, and fast
local GA are not gaps by themselves.

## Locked gap taxonomy

- **Temporal integration:** isolate observation-rate context updating from
  planning-event-only updating in the same frozen pipeline.
- **Representation:** use current position, velocity, coarse direction,
  confidence, and age without generating a displayed human trajectory.
- **Control contract:** convert only an admitted local robot path into an NMPC
  reference while NMPC retains sole command authority.
- **Evaluation:** keep the global path, predictor, GA budget, planning events,
  plant, constraints, and NMPC identical across the primary contrast.

## Focused contribution-gap matrix

| Gap | Closest evidence | Unresolved limitation | Proposed response | Falsification |
|---|---|---|---|---|
| Continuous context-aware local-path generation | LSTM local planners, direct LSTM command generation, context-aware GA, people-aware GA, GA--controller pipelines, micro-GA MPC, selective MPC--PSO, and GA--MPPI already exist | The focused set does not establish whether refreshing a limited current-human-context state at the observation rate improves fixed-global-path local planning over refreshing the same state only when replanning is triggered | CCA containing a frozen current-context LSTM and GA, with global path and current context as inputs and robot local path as its only output | Reject the continuous-update claim if the observation-rate and trigger-rate variants of the same LSTM--GA pipeline show no package-level local-path or downstream-navigation benefit |
| Causal evaluation | Within the focused set, integrated systems and component studies use different inputs, outputs, and authorities | Prediction quality, local-generation quality, tracking, and navigation are easily conflated | Layer-wise ablations plus a separately matched end-to-end benchmark | Reject component claims that do not survive their matched layer |
| Holonomic embodiment (secondary hypothesis) | Omnidirectional human-interaction planners already exist, while the Mecanum anchors emphasize tracking or generic obstacles | The value of lateral Mecanum motion under this exact CCA interface remains empirical | Same six-state/body-velocity Mecanum model for all control baselines | Reject the secondary hypothesis if a matched $v_y=0$ ablation shows no material effect |
| Context-to-navigation value | LSTM context estimation, probabilistic human prediction and learned social costs are established | Better context-estimation loss does not imply better navigation | Test current position/speed/coarse-direction/confidence/age utility on identical paired packages | Reject utility claim if the frozen-LSTM contrast against constant-velocity and no-context variants does not pass the registered downstream gate |

## Non-novel design and evidence obligations

| Obligation | Prior-art boundary | Required treatment |
|---|---|---|
| Path-to-control compatibility | Feasibility governors and PathFG already provide stronger general interface results | Keep time-parameterization and feasibility checking inside motion control; restrict the proof to fixed-reference terminal NMPC and reject unrestricted switched-system claims |
| Bounded search cost | Real-time GA obstacle avoidance and GPU local GA at approximately 0.1 s per path already exist | Use equal candidate/decode budgets, hard feasibility before selection, and revalidated fallback; treat desktop Python latency as telemetry and reject a real-time claim without target-device p50/p95/p99 and miss-rate evidence |

## Defensible position

After accounting for context-aware and interactive MPC, LSTM local planning,
learning-guided subgoal MPC, context- and people-aware GA planning,
GA--controller pipelines, established
feasibility governors, and PathFG, the unresolved question is not whether these
blocks can be combined. The candidate question is whether the exact causal,
continuously updated human context produces a reproducible benefit for a
fixed-global-path Mecanum local path under matched budgets. CCA contains LSTM and
GA and outputs only the robot local path; NMPC alone issues motion commands.

The registered context boundary is deliberately small: current position, speed,
coarse direction, confidence, and observation age only. Dataset partitioning,
sample size, random seeds, runtime budgets, and statistical gates belong to
`IMPLEMENTATION_PLAN.md`; none is current evidence.

No novelty is claimed for LSTM, GA, NMPC, the governor, or authority separation
individually. Evolutionary repair and scalar homotopy are also prior art. The
candidate technical contribution is restricted to continuous context updating
inside the fixed-path Mecanum local-path generator and a measured downstream
effect. Without matched empirical evidence, it remains a candidate systems
mechanism and must not use `first`, `novel framework`, `real-time`, or
`new governor`.

## Audit boundary

This is a focused, non-exhaustive DOI audit rather than a systematic literature
review. It supports exclusions and a falsifiable candidate question; it does not
establish universal priority. The literature boundary and falsifiable question
are locked for the present theory goal. The benefit claim remains `candidate`
until registered matched comparisons pass.

## Links

[[01_Problem/research-scope]] · [[02_Literature/closest-work]] ·
[[03_Theory/architecture]] · [[04_Evaluation/baseline-contract]] ·
[[04_Evaluation/claim-evidence-boundary]]
