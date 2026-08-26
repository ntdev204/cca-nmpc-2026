---
domain: literature
type: note
status: locked
scope: focused-non-systematic-doi-audit
evidence: synthesis
tags: [evidence, synthesis]
---

# Evidence synthesis

## Synthesis by research function

### Context and prediction

Social LSTM established recurrent human-trajectory prediction
[Alahi et al., 2016](https://doi.org/10.1109/CVPR.2016.110). Later systems place
context or multimodal prediction inside predictive navigation
[Stefanini et al., 2024](https://doi.org/10.1109/LRA.2024.3461552),
[SICNav-Diffusion, 2025](https://doi.org/10.1109/LRA.2025.3585713).
Scenario-based NMPC also integrates probabilistic human predictions with formal
recursive-feasibility/stability results and experiments
[Oleinikov et al., 2024](https://doi.org/10.1016/j.conengprac.2023.105769).
Consequently, prediction loss is an intermediate metric; it cannot support a
navigation or safety claim without downstream tests.

A controlled human--robot interaction study further shows that predictor
displacement error need not rank downstream navigation performance or human
experience consistently
[Stratton et al., 2026](https://doi.org/10.1145/3757279.3788664). This directly
supports the evaluation gap: prediction, local-path quality, tracking, and
human response must remain separate evidence layers.

Continuous spatiotemporal routing already adapts routes to predicted crowd
changes [Ge et al., 2025](https://doi.org/10.1007/s12369-024-01193-3), while
social-type-aware navigation already changes asymmetric personal space from
perceived context [Kang et al., 2024](https://doi.org/10.3390/s24154862).
Multi-agent navigation has also separated global, local, and reactive functions
while using near-future human motion
[Boldrer et al., 2022](https://doi.org/10.1016/j.robot.2021.103979). Thus,
continuous routing, context-shaped exclusion geometry, and a global--local
architecture are established ingredients rather than standalone novelty.

The present LSTM has a narrower role: it estimates current position, speed,
coarse direction and confidence and propagates observation age. It does not
export future person coordinates. That restriction is a systems boundary, not
a novelty claim or evidence of superiority to predictive-human models. Its
self-supervised target is an independently derived current velocity, not a
future person state.

LSTM-based local navigation is also established. One method trains an LSTM
local planner from fuzzy-controller samples
[Guo et al., 2021](https://doi.org/10.3103/S014641162101003X); another combines
LSTM, fuzzy control and reinforcement learning for mobile-robot local planning
[Guo et al., 2021](https://doi.org/10.1155/2021/5524232). An LSTM has also been
used to map LiDAR, robot and goal inputs directly to velocity commands in a
dynamic simulated environment
[Molina-Leal et al., 2021](https://doi.org/10.3390/app112210689). Therefore,
neither LSTM local planning nor LSTM-derived navigation commands support the
present gap. The testable distinction is the limited current-context role of
LSTM inside CCA and the downstream effect of that context on a GA-generated
geometric local path while NMPC retains command authority.

### Context and evolutionary planning

Context-plus-GA path planning predates this study: UbiPaPaGo uses a spatial
conceptual map and GA for human-centered context-aware path selection
[Wang et al., 2011](https://doi.org/10.1016/j.eswa.2010.09.077). It is not a
mobile-robot controller study, so it limits the combination claim without
answering the present controller-interface question. More directly, GA has been
used to train a ROS navigation stack for people-aware trajectories under moving
people and proxemic objectives
[Bacchin et al., 2021](https://doi.org/10.1109/ECMR50962.2021.9568804), and to
tune an artificial-potential-field formulation for human-aware robot navigation
[Sampathkumar et al., 2023](https://doi.org/10.1007/978-3-031-46778-3_15).
Human awareness, directional or proxemic costs, and GA therefore cannot support
novelty individually or merely by co-occurrence.

### Reference authority

GO-MPC demonstrates that an upstream component can recommend a subgoal while MPC
retains command authority
[Brito et al., 2021](https://doi.org/10.1109/LRA.2021.3068662). Reference and
feasibility governors already modify references to preserve constraints or MPC
feasibility
[Garone et al., 2017](https://doi.org/10.1016/j.automatica.2016.08.013),
[Convens et al., 2024](https://doi.org/10.1109/TCST.2024.3365996). PathFG goes
further by integrating path progression, feasibility governance, and NMPC with
replanning and formal properties
[Zhang et al., 2025](https://doi.org/10.48550/arXiv.2507.09134). The present
governor and authority split are therefore interface requirements, not novelty.

A directly matched mobile-robot architecture also exists: an integrated DWA--MPC
framework maps a fixed global path, robot state and local sensing to a DWA local
path and then uses MPC for tracking, with simulation and robot experiments
[Wang et al., 2025](https://doi.org/10.3390/s25072014). This invalidates novelty
for the two-layer planner--controller arrangement and makes DWA--MPC the primary
interface-matched end-to-end comparator.

Learned path generation followed by a separate motion module has likewise been
demonstrated in simulation and hardware
[Zhang et al., 2023](https://doi.org/10.1109/LRA.2023.3284354). A deep
perception representation, global plan and robot state have also been integrated
directly into NMPC local motion planning
[Imad et al., 2022](https://doi.org/10.3390/s22218101). The present separation
and perception-to-control composition are therefore design choices, not novelty.

### Local search

GA can address nonconvex local path search, including LiDAR obstacle avoidance
[Gyenes et al., 2023](https://doi.org/10.3390/s23063039). GPU evolutionary
dynamic programming with local GA refinement has also produced paths in dynamic
environments on an edge robot at approximately 0.1 s per path
[Ou et al., 2025](https://doi.org/10.1016/j.asoc.2025.113167). Fast local GA
and edge execution are therefore prior art, and the present implementation
cannot use real-time wording without its own p95/p99 evidence.

The broader planner--controller composition is established as well. GA path
search followed by PCHIP smoothing and adaptive fuzzy tracking control has been
validated with explicit geometry, sensing, and a physical mobile robot
[Bakdi et al., 2017](https://doi.org/10.1016/j.robot.2016.12.008). Conversely,
GA has performed online nonlinear optimization inside model-based predictive
control for mobile-robot navigation
[Rodriguez Ramirez et al., 1999](https://doi.org/10.1109/ROBOT.1999.770473).
Micro-GA has also solved a supervised nonconvex MPC collision-avoidance problem
[Song and Huh, 2021](https://doi.org/10.1177/16878140211027669), while selective
MPC with PSO/potential fields has generated local paths on an embedded AGV
[Kim et al., 2024](https://doi.org/10.3390/robotics13030046). Integrated
GA--MPPI planning/control and APF-local-planner--MPC compositions further bound
the architecture claim
[Nam and Kim, 2024](https://doi.org/10.1007/s12555-024-0543-7),
[Li et al., 2021](https://doi.org/10.1177/00202940211043070).
Placing GA upstream of NMPC is a defensible authority and timing choice, but the
separation itself is not established as novel by the present focused audit.

A remaining candidate claim requires more than weighted fitness. The continuous
context update must produce a measurable benefit in the fixed-path Mecanum local
path, and that benefit must survive matched context, decoder, repair, and
initialization ablations under equal budgets.

### Motion control

Mecanum MPC is established
[Moreno et al., 2021](https://doi.org/10.1016/j.ifacol.2021.08.533),
[Wang et al., 2024](https://doi.org/10.1016/j.isatra.2024.05.050). Standard
terminal ingredients support nominal NMPC stability
[Mayne et al., 2000](https://doi.org/10.1016/S0005-1098(99)00214-9), but an
arbitrary local-reference switch is outside the ordinary fixed-reference proof.
More recent work proves recursive feasibility and closed-loop stability for
point/set-terminal NMPC under an explicit static-human assumption
[Nurbayeva and Rubagotti, 2025](https://doi.org/10.1016/j.conengprac.2024.106155).
Residual learning and real-time disturbance rejection have also been integrated
with MPC and evaluated experimentally on a Mecanum robot
[Zhang et al., 2025](https://doi.org/10.1016/j.conengprac.2025.106587).

Model-predictive path following for holonomic robots already has a rigorous
closed-loop asymptotic-stability proof and experimental validation
[Cenerini et al., 2023](https://doi.org/10.1016/j.conengprac.2022.105406).
Accordingly, the fixed-reference terminal-NMPC Lyapunov result is supporting
theory and cannot be presented as theoretical novelty.

Human--robot interaction planning itself has a strong 2026 comparator: a model
predictive tethered-guide planner uses a spring--mass interaction model calibrated
through participant experiments
[Li et al., 2026](https://doi.org/10.1016/j.ejcon.2026.101572). The present work
must therefore avoid broad claims about model-predictive HRI or human modeling.

### Evaluation

The strongest unresolved methodological issue is causal attribution around the
Continuous Context-Aware local-path generator. The study must isolate context,
GA local-path search, path repair, motion-layer conversion, tracking, and
end-to-end behavior under aligned interfaces. Reported values from other maps,
robots, predictors, and compute platforms are context, not fair baselines.

Future evaluation must use participant/recording-disjoint LSTM splits,
site-held-out assessment, matched randomization, equal candidate/decode budgets,
paired statistics, and a predeclared multiplicity correction. Exact sample
sizes, seeds, budgets, and timing gates are deferred to
`IMPLEMENTATION_PLAN.md`. No composite score may rescue a failed primary
mechanism gate.

### Audit boundary

This synthesis is based on a focused, non-exhaustive DOI set. It supports a
candidate and falsifiable mechanism question, not a universal priority claim.
The theory manuscript uses a curated 34-item DOI bibliography drawn from this
larger evidence registry; bibliography size is coverage metadata, not proof of
novelty.

## Links

[[02_Literature/closest-work]] · [[02_Literature/core-doi-sources]] ·
[[01_Problem/research-gap]] ·
[[03_Theory/cca-trajectory-generation]] · [[03_Theory/lyapunov-stability]] ·
[[04_Evaluation/baseline-contract]]
