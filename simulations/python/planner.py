from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

import numpy as np
from numpy.typing import NDArray
from scipy.interpolate import PchipInterpolator


FloatArray = NDArray[np.float64]


@dataclass(slots=True)
class Observation:
    position: FloatArray
    feature: FloatArray
    age_ms: float = 0.0
    valid: bool = True


@dataclass(slots=True)
class LstmState:
    hidden: FloatArray
    cell: FloatArray

    @classmethod
    def zeros(cls, width: int) -> LstmState:
        return cls(np.zeros(width), np.zeros(width))


@dataclass(slots=True)
class LstmWeights:
    gates: FloatArray
    bias: FloatArray
    velocity: FloatArray
    velocity_bias: FloatArray


@dataclass(slots=True)
class Context:
    position: FloatArray
    direction: FloatArray
    speed: float
    confidence: float
    age_ms: float
    valid: bool

    @classmethod
    def invalid(cls, position: FloatArray, age_ms: float) -> Context:
        return cls(
            np.asarray(position, dtype=np.float64).copy(),
            np.zeros(2),
            0.0,
            0.0,
            float(age_ms),
            False,
        )


@dataclass(slots=True)
class PlannerMemory:
    chromosome: FloatArray = field(default_factory=lambda: np.empty(0))
    path: FloatArray = field(default_factory=lambda: np.empty((0, 2)))
    rejoin_index: int = -1


@dataclass(slots=True)
class PlannerConfig:
    population: int = 28
    generations: int = 16
    candidate_budget: int = 448
    decode_budget: int = 448
    waypoint_count: int = 7
    path_samples: int = 41
    elite_count: int = 6
    max_offset_m: float = 0.42
    mutation_sigma_m: float = 0.06
    safe_distance_m: float = 0.05
    max_curvature_inv_m: float = 35.0
    half_length_m: float = 0.20
    half_width_m: float = 0.20
    human_forward_radius_m: float = 0.24
    human_rear_radius_m: float = 0.12
    human_lateral_radius_m: float = 0.15
    human_speed_horizon_s: float = 0.30
    context_scale: float = 0.30
    context_enabled: bool = True
    fitness_weights: tuple[float, ...] = (1.0, 0.01, 1.0, 0.4, 0.3)
    repair_beta: float = 0.5
    repair_steps: int = 6
    repair_mode: str = "decoder_repair"
    initialization_mode: str = "shifted"
    violation_penalty: float = 1.0e4
    rejoin_tolerance_m: float = 1.0e-9
    max_context_age_ms: float = 150.0
    stationary_speed_mps: float = 1.0e-4
    minimum_direction_confidence: float = 0.5
    temperature: float = 1.0
    lookahead_distance_m: float = 1.5
    rejoin_index: int | None = None
    start_index: int | None = None

    @property
    def footprint_radius_m(self) -> float:
        return float(np.hypot(self.half_length_m, self.half_width_m))

    def validate(self) -> None:
        counts = (
            self.population,
            self.generations,
            self.candidate_budget,
            self.decode_budget,
            self.waypoint_count,
            self.path_samples,
            self.elite_count,
            self.repair_steps + 1,
        )
        if min(counts) < 1:
            raise ValueError("planner counts must be positive")
        if self.waypoint_count < 3 or self.path_samples < 3:
            raise ValueError("at least three control and path points are required")
        if self.elite_count > self.population:
            raise ValueError("elite count cannot exceed population")
        if self.repair_mode not in {
            "penalty_only",
            "decoder_only",
            "decoder_repair",
        }:
            raise ValueError("unknown repair mode")
        if self.initialization_mode not in {"shifted", "random"}:
            raise ValueError("unknown initialization mode")
        if not 0.0 < self.repair_beta < 1.0:
            raise ValueError("repair beta must lie in (0,1)")
        positive = (
            self.max_curvature_inv_m,
            self.half_length_m,
            self.half_width_m,
            self.human_forward_radius_m,
            self.human_rear_radius_m,
            self.human_lateral_radius_m,
            self.context_scale,
            self.temperature,
            self.violation_penalty,
            self.lookahead_distance_m,
        )
        nonnegative = (
            self.max_offset_m,
            self.mutation_sigma_m,
            self.safe_distance_m,
            self.human_speed_horizon_s,
            self.max_context_age_ms,
            self.stationary_speed_mps,
            self.rejoin_tolerance_m,
        )
        if not np.isfinite(positive).all() or min(positive) <= 0.0:
            raise ValueError("positive planner parameters are invalid")
        if not np.isfinite(nonnegative).all() or min(nonnegative) < 0.0:
            raise ValueError("nonnegative planner parameters are invalid")
        weights = np.asarray(self.fitness_weights, dtype=np.float64)
        if weights.shape != (5,) or not np.isfinite(weights).all():
            raise ValueError("fitness requires five finite weights")
        if np.any(weights < 0.0):
            raise ValueError("fitness weights must be nonnegative")
        if not np.isfinite(self.minimum_direction_confidence):
            raise ValueError("direction confidence threshold must be finite")
        if not 0.0 <= self.minimum_direction_confidence <= 1.0:
            raise ValueError("direction confidence threshold must lie in [0,1]")
        for name, index in (
            ("start index", self.start_index),
            ("rejoin index", self.rejoin_index),
        ):
            if index is not None and (not isinstance(index, int) or index < 0):
                raise ValueError(f"{name} must be a nonnegative integer")


@dataclass(slots=True)
class PlanResult:
    status: str
    path: FloatArray
    chromosome: FloatArray
    terms: FloatArray
    score: float
    feasible: bool
    fallback_available: bool
    path_source: str
    constraint_violation: float
    rejoin_error_m: float
    minimum_obstacle_clearance_m: float
    minimum_context_metric: float
    maximum_curvature_inv_m: float
    candidate_count: int
    decode_count: int
    pre_repair_feasible_count: int
    post_repair_feasible_count: int
    repaired_feasible_count: int
    repair_level: int
    generations_completed: int
    segment_start_index: int
    segment_rejoin_index: int
    global_path_unchanged: bool
    elapsed_ms: float


@dataclass(slots=True)
class _Segment:
    base: FloatArray
    normal: FloatArray
    start_index: int
    rejoin_index: int
    rejoin_point: FloatArray


@dataclass(slots=True)
class _Geometry:
    feasible: bool
    violation: float
    rejoin_error_m: float
    minimum_obstacle_clearance_m: float
    minimum_context_metric: float
    maximum_curvature_inv_m: float


@dataclass(slots=True)
class _Candidate:
    path: FloatArray = field(default_factory=lambda: np.empty((0, 2)))
    chromosome: FloatArray = field(default_factory=lambda: np.empty(0))
    terms: FloatArray = field(default_factory=lambda: np.full(5, np.inf))
    selection_cost: float = np.inf
    geometry: _Geometry | None = None
    repair_level: int = -1
    decode_count: int = 0
    pre_repair_feasible: bool = False


DIRECTION_BASIS = np.asarray(
    ((1.0, 0.0, -1.0, 0.0), (0.0, 1.0, 0.0, -1.0)),
    dtype=np.float64,
)


def observe_context(
    observation: Observation,
    previous: LstmState,
    weights: LstmWeights,
    config: PlannerConfig,
) -> tuple[Context, LstmState]:
    config.validate()
    position = _vector(observation.position, 2, "human position")
    if not np.isfinite(observation.age_ms) or observation.age_ms < 0.0:
        raise ValueError("context age must be finite and nonnegative")
    if not observation.valid or observation.age_ms > config.max_context_age_ms:
        return Context.invalid(position, observation.age_ms), previous
    feature = np.asarray(observation.feature, dtype=np.float64).reshape(-1)
    hidden = np.asarray(previous.hidden, dtype=np.float64).reshape(-1)
    cell = np.asarray(previous.cell, dtype=np.float64).reshape(-1)
    if hidden.shape != cell.shape or hidden.size == 0:
        raise ValueError("LSTM hidden and cell states must have equal width")
    joined = np.concatenate((feature, hidden))
    gates = np.asarray(weights.gates, dtype=np.float64)
    bias = np.asarray(weights.bias, dtype=np.float64).reshape(-1)
    if gates.shape != (4 * hidden.size, joined.size):
        raise ValueError("LSTM gate matrix shape is invalid")
    if bias.shape != (4 * hidden.size,):
        raise ValueError("LSTM gate bias shape is invalid")
    if not np.isfinite(gates).all() or not np.isfinite(bias).all():
        raise ValueError("LSTM gate parameters must be finite")
    gate_value = gates @ joined + bias
    width = hidden.size
    forget = _sigmoid(gate_value[:width])
    input_gate = _sigmoid(gate_value[width : 2 * width])
    output_gate = _sigmoid(gate_value[2 * width : 3 * width])
    candidate = np.tanh(gate_value[3 * width :])
    next_cell = forget * cell + input_gate * candidate
    next_hidden = output_gate * np.tanh(next_cell)
    velocity_matrix = np.asarray(weights.velocity, dtype=np.float64)
    velocity_bias = np.asarray(weights.velocity_bias, dtype=np.float64).reshape(-1)
    if velocity_matrix.shape != (2, width) or velocity_bias.shape != (2,):
        raise ValueError("LSTM velocity head shape is invalid")
    if not np.isfinite(velocity_matrix).all() or not np.isfinite(velocity_bias).all():
        raise ValueError("LSTM velocity parameters must be finite")
    velocity = velocity_matrix @ next_hidden + velocity_bias
    context = context_from_velocity(position, velocity, observation.age_ms, config)
    return context, LstmState(next_hidden, next_cell)


def context_from_velocity(
    position: FloatArray,
    velocity: FloatArray,
    age_ms: float,
    config: PlannerConfig,
) -> Context:
    config.validate()
    position = _vector(position, 2, "human position")
    velocity = _vector(velocity, 2, "human velocity")
    speed = float(np.linalg.norm(velocity))
    logits = DIRECTION_BASIS.T @ velocity / max(config.temperature, np.finfo(float).eps)
    probability = _softmax(logits)
    index = int(np.argmax(probability))
    confidence = float(probability[index])
    direction = DIRECTION_BASIS[:, index].copy()
    if speed <= config.stationary_speed_mps:
        direction.fill(0.0)
    if confidence < config.minimum_direction_confidence:
        direction.fill(0.0)
    valid = bool(np.isfinite(age_ms) and 0.0 <= age_ms <= config.max_context_age_ms)
    if not valid:
        return Context.invalid(position, age_ms)
    return Context(position, direction, speed, confidence, float(age_ms), True)


def plan_local_path(
    global_path: FloatArray,
    robot_state: FloatArray,
    context: Context,
    obstacles: FloatArray,
    config: PlannerConfig,
    *,
    seed: int,
    memory: PlannerMemory | None = None,
) -> PlanResult:
    started = perf_counter()
    config.validate()
    path_input = _path(global_path, "global path")
    original_path = path_input.copy()
    state = _vector(robot_state, 6, "robot state")
    obstacle_array = _obstacles(obstacles)
    _validate_context(context)
    active_memory = memory if memory is not None else PlannerMemory()
    if config.context_enabled and not context.valid:
        return _failure_result(
            "invalid_context",
            path_input,
            original_path,
            active_memory,
            started,
        )
    segment = _fixed_segment(path_input, state, config)
    anchor = _shifted_seed(active_memory, segment, config)
    rng = np.random.default_rng(seed)
    population = _initial_population(anchor, config, rng)
    best = _Candidate()
    best_cost = np.inf
    candidates = 0
    decodes = 0
    pre_feasible = 0
    post_feasible = 0
    repaired_feasible = 0
    generations_completed = 0
    for generation in range(config.generations):
        costs = np.full(config.population, np.inf)
        evaluated = np.zeros(config.population, dtype=bool)
        for member in range(config.population):
            if candidates >= config.candidate_budget:
                break
            if decodes >= config.decode_budget:
                break
            candidates += 1
            audit = _repair_candidate(
                population[member],
                anchor,
                path_input,
                state,
                context,
                obstacle_array,
                segment,
                config,
                config.decode_budget - decodes,
                active_memory.path,
            )
            decodes += audit.decode_count
            pre_feasible += int(audit.pre_repair_feasible)
            evaluated[member] = True
            if np.isfinite(audit.selection_cost):
                population[member] = audit.chromosome
                costs[member] = audit.selection_cost
            if audit.geometry is None or not audit.geometry.feasible:
                continue
            post_feasible += 1
            repaired_feasible += int(audit.repair_level > 0)
            if audit.selection_cost < best_cost:
                best = audit
                best_cost = audit.selection_cost
        if evaluated.all():
            generations_completed = generation + 1
        if candidates >= config.candidate_budget or decodes >= config.decode_budget:
            break
        population = _next_population(population, costs, evaluated, config, rng)
    if best.geometry is None or not np.isfinite(best_cost):
        result = _failure_result(
            "no_feasible_candidate",
            path_input,
            original_path,
            active_memory,
            started,
            segment,
        )
        result.candidate_count = candidates
        result.decode_count = decodes
        result.pre_repair_feasible_count = pre_feasible
        result.post_repair_feasible_count = post_feasible
        result.repaired_feasible_count = repaired_feasible
        result.generations_completed = generations_completed
        return result
    geometry = best.geometry
    return PlanResult(
        status="proposal_ready",
        path=best.path,
        chromosome=best.chromosome,
        terms=best.terms,
        score=float(best_cost),
        feasible=True,
        fallback_available=False,
        path_source="new_feasible_path",
        constraint_violation=geometry.violation,
        rejoin_error_m=geometry.rejoin_error_m,
        minimum_obstacle_clearance_m=geometry.minimum_obstacle_clearance_m,
        minimum_context_metric=geometry.minimum_context_metric,
        maximum_curvature_inv_m=geometry.maximum_curvature_inv_m,
        candidate_count=candidates,
        decode_count=decodes,
        pre_repair_feasible_count=pre_feasible,
        post_repair_feasible_count=post_feasible,
        repaired_feasible_count=repaired_feasible,
        repair_level=best.repair_level,
        generations_completed=generations_completed,
        segment_start_index=segment.start_index,
        segment_rejoin_index=segment.rejoin_index,
        global_path_unchanged=np.array_equal(path_input, original_path),
        elapsed_ms=1000.0 * (perf_counter() - started),
    )


def path_curvature(path: FloatArray) -> FloatArray:
    points = _path(path, "path")
    dx = np.gradient(points[:, 0])
    dy = np.gradient(points[:, 1])
    ddx = np.gradient(dx)
    ddy = np.gradient(dy)
    numerator = dx * ddy - dy * ddx
    denominator = np.maximum((dx * dx + dy * dy) ** 1.5, 1.0e-9)
    return numerator / denominator


def path_length(path: FloatArray) -> float:
    points = _path(path, "path")
    return float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())


def _repair_candidate(
    chromosome: FloatArray,
    anchor: FloatArray,
    global_path: FloatArray,
    robot_state: FloatArray,
    context: Context,
    obstacles: FloatArray,
    segment: _Segment,
    config: PlannerConfig,
    decode_allowance: int,
    previous_path: FloatArray,
) -> _Candidate:
    result = _Candidate()
    levels = config.repair_steps if config.repair_mode == "decoder_repair" else 0
    for level in range(levels + 1):
        if result.decode_count >= decode_allowance:
            break
        if config.repair_mode != "decoder_repair":
            factor = 1.0
        elif level < config.repair_steps:
            factor = config.repair_beta**level
        else:
            factor = 0.0
        repaired = _canonicalize(anchor + factor * (chromosome - anchor), config)
        path = _decode(robot_state, repaired, segment, config)
        geometry = _geometric_audit(path, context, obstacles, segment, config)
        terms = _fitness_terms(path, global_path, context, config, previous_path)
        result.decode_count += 1
        if level == 0:
            result.pre_repair_feasible = geometry.feasible
        result.path = path
        result.chromosome = repaired
        result.terms = terms
        result.geometry = geometry
        result.repair_level = level
        base_cost = float(terms @ np.asarray(config.fitness_weights))
        if config.repair_mode == "penalty_only":
            result.selection_cost = base_cost + config.violation_penalty * geometry.violation
            return result
        if geometry.feasible:
            result.selection_cost = base_cost
            return result
        if config.repair_mode == "decoder_only":
            return result
    return result


def _fixed_segment(
    global_path: FloatArray,
    robot_state: FloatArray,
    config: PlannerConfig,
) -> _Segment:
    if config.start_index is None:
        distances = np.linalg.norm(global_path[:-1] - robot_state[:2], axis=1)
        start = int(np.argmin(distances))
    else:
        start = int(config.start_index)
    if not 0 <= start < len(global_path) - 1:
        raise ValueError("start index must precede the final global-path point")
    if config.rejoin_index is None:
        remaining = global_path[start:]
        cumulative = np.concatenate(
            ([0.0], np.cumsum(np.linalg.norm(np.diff(remaining, axis=0), axis=1)))
        )
        offset = int(np.searchsorted(cumulative, config.lookahead_distance_m))
        rejoin = min(start + max(offset, 1), len(global_path) - 1)
    else:
        rejoin = int(config.rejoin_index)
    if not start < rejoin < len(global_path):
        raise ValueError("rejoin index must lie after the segment start")
    source = global_path[start : rejoin + 1]
    distance = np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(source, axis=0), axis=1))))
    keep = np.concatenate(([True], np.diff(distance) > np.finfo(float).eps))
    source = source[keep]
    distance = distance[keep]
    if len(distance) < 2 or distance[-1] <= np.finfo(float).eps:
        raise ValueError("fixed global-path segment has zero length")
    query = np.linspace(0.0, distance[-1], config.waypoint_count)
    base = np.column_stack(
        (
            np.interp(query, distance, source[:, 0]),
            np.interp(query, distance, source[:, 1]),
        )
    )
    tangent = np.column_stack((np.gradient(base[:, 0]), np.gradient(base[:, 1])))
    tangent_norm = np.maximum(np.linalg.norm(tangent, axis=1), np.finfo(float).eps)
    normal = np.column_stack((-tangent[:, 1], tangent[:, 0])) / tangent_norm[:, None]
    return _Segment(base, normal, start, rejoin, global_path[rejoin].copy())


def _decode(
    robot_state: FloatArray,
    chromosome: FloatArray,
    segment: _Segment,
    config: PlannerConfig,
) -> FloatArray:
    controls = segment.base.copy()
    controls[1:-1] += chromosome[:, None] * segment.normal[1:-1]
    controls[0] = robot_state[:2]
    controls[-1] = segment.rejoin_point
    source = np.arange(config.waypoint_count, dtype=np.float64)
    query = np.linspace(0.0, config.waypoint_count - 1, config.path_samples)
    return np.column_stack(
        (
            PchipInterpolator(source, controls[:, 0])(query),
            PchipInterpolator(source, controls[:, 1])(query),
        )
    )


def _geometric_audit(
    path: FloatArray,
    context: Context,
    obstacles: FloatArray,
    segment: _Segment,
    config: PlannerConfig,
) -> _Geometry:
    curvature = path_curvature(path)
    maximum_curvature = float(np.max(np.abs(curvature)))
    curvature_violation = max(
        0.0,
        maximum_curvature / config.max_curvature_inv_m - 1.0,
    )
    minimum_obstacle_clearance = np.inf
    obstacle_violation = 0.0
    for obstacle in obstacles:
        clearance = obstacle[2] + config.footprint_radius_m + config.safe_distance_m
        distance = _polyline_point_distance(path, obstacle[:2])
        minimum_obstacle_clearance = min(
            minimum_obstacle_clearance,
            distance - clearance,
        )
        obstacle_violation = max(
            obstacle_violation,
            max(0.0, (clearance - distance) / max(clearance, np.finfo(float).eps)),
        )
    if config.context_enabled:
        minimum_context_metric = _minimum_context_metric(path, context, config)
        context_violation = max(0.0, 1.0 - minimum_context_metric)
    else:
        minimum_context_metric = np.inf
        context_violation = 0.0
    rejoin_error = float(np.linalg.norm(path[-1] - segment.rejoin_point))
    rejoin_violation = max(
        0.0,
        (rejoin_error - config.rejoin_tolerance_m)
        / max(config.rejoin_tolerance_m, np.finfo(float).eps),
    )
    violation = max(
        curvature_violation,
        obstacle_violation,
        context_violation,
        rejoin_violation,
    )
    return _Geometry(
        feasible=violation <= 0.0,
        violation=violation,
        rejoin_error_m=rejoin_error,
        minimum_obstacle_clearance_m=float(minimum_obstacle_clearance),
        minimum_context_metric=float(minimum_context_metric),
        maximum_curvature_inv_m=maximum_curvature,
    )


def _fitness_terms(
    path: FloatArray,
    global_path: FloatArray,
    context: Context,
    config: PlannerConfig,
    previous_path: FloatArray,
) -> FloatArray:
    length_term = path_length(path)
    curvature = path_curvature(path)
    segment_length = np.linalg.norm(np.diff(path, axis=0), axis=1)
    smoothness_term = float(
        np.sum(
            0.5
            * (curvature[:-1] * curvature[:-1] + curvature[1:] * curvature[1:])
            * segment_length
        )
    )
    distances = np.asarray(
        [_polyline_point_distance(global_path, point) for point in path]
    )
    global_term = float(np.mean(distances * distances))
    context_term = 0.0
    if config.context_enabled:
        metric = _context_metric(path, context, config)
        context_term = float(
            np.mean(
                np.exp(-np.maximum(metric - 1.0, 0.0) / config.context_scale)
            )
        )
    continuity_term = 0.0
    previous = np.asarray(previous_path, dtype=np.float64)
    if previous.size:
        previous = _path(previous, "previous path")
        remaining = _remaining_polyline(previous, path[0])
        current = _resample_polyline(path, len(path))
        prior = _resample_polyline(remaining, len(path))
        continuity_term = float(np.mean(np.linalg.norm(current - prior, axis=1)))
    return np.asarray(
        (length_term, smoothness_term, global_term, context_term, continuity_term),
        dtype=np.float64,
    )


def _minimum_context_metric(
    path: FloatArray,
    context: Context,
    config: PlannerConfig,
) -> float:
    relative = path - context.position
    direction = np.asarray(context.direction, dtype=np.float64)
    forward, rear, lateral = _human_radii(context, config)
    if np.linalg.norm(direction) <= np.finfo(float).eps:
        radius = max(forward, rear, lateral)
        distance = _polyline_point_distance(path, context.position)
        return float((distance / radius) ** 2)
    direction = direction / np.linalg.norm(direction)
    normal = np.asarray((-direction[1], direction[0]))
    coordinates = np.column_stack((relative @ direction, relative @ normal))
    minimum = np.inf
    for first, second in zip(coordinates[:-1], coordinates[1:], strict=True):
        if first[0] * second[0] < 0.0:
            ratio = -first[0] / (second[0] - first[0])
            crossing = first + ratio * (second - first)
            metric = min(
                _ellipse_segment_metric(first, crossing, forward, rear, lateral),
                _ellipse_segment_metric(crossing, second, forward, rear, lateral),
            )
        else:
            metric = _ellipse_segment_metric(first, second, forward, rear, lateral)
        minimum = min(minimum, metric)
    return float(minimum)


def _context_metric(
    path: FloatArray,
    context: Context,
    config: PlannerConfig,
) -> FloatArray:
    relative = path - context.position
    direction = np.asarray(context.direction, dtype=np.float64)
    forward, rear, lateral = _human_radii(context, config)
    if np.linalg.norm(direction) <= np.finfo(float).eps:
        radius = max(forward, rear, lateral)
        return np.sum(relative * relative, axis=1) / (radius * radius)
    direction = direction / np.linalg.norm(direction)
    normal = np.asarray((-direction[1], direction[0]))
    longitudinal = relative @ direction
    longitudinal_radius = np.where(longitudinal >= 0.0, forward, rear)
    return (longitudinal / longitudinal_radius) ** 2 + (relative @ normal / lateral) ** 2


def _human_radii(context: Context, config: PlannerConfig) -> tuple[float, float, float]:
    inflation = config.footprint_radius_m + config.safe_distance_m
    forward = (
        config.human_forward_radius_m
        + inflation
        + config.human_speed_horizon_s * context.speed
    )
    rear = config.human_rear_radius_m + inflation
    lateral = config.human_lateral_radius_m + inflation
    return forward, rear, lateral


def _ellipse_segment_metric(
    first: FloatArray,
    second: FloatArray,
    forward: float,
    rear: float,
    lateral: float,
) -> float:
    radius = forward if 0.5 * (first[0] + second[0]) >= 0.0 else rear
    scaled_first = np.asarray((first[0] / radius, first[1] / lateral))
    scaled_second = np.asarray((second[0] / radius, second[1] / lateral))
    delta = scaled_second - scaled_first
    denominator = float(delta @ delta)
    if denominator <= np.finfo(float).eps:
        return float(scaled_first @ scaled_first)
    ratio = float(np.clip(-(scaled_first @ delta) / denominator, 0.0, 1.0))
    closest = scaled_first + ratio * delta
    return float(closest @ closest)


def _polyline_point_distance(path: FloatArray, point: FloatArray) -> float:
    starts = path[:-1]
    delta = path[1:] - starts
    relative = point - starts
    denominator = np.sum(delta * delta, axis=1)
    ratio = np.zeros_like(denominator)
    active = denominator > np.finfo(float).eps
    ratio[active] = np.sum(relative[active] * delta[active], axis=1) / denominator[active]
    closest = starts + np.clip(ratio, 0.0, 1.0)[:, None] * delta
    return float(np.min(np.linalg.norm(closest - point, axis=1)))


def _remaining_polyline(path: FloatArray, point: FloatArray) -> FloatArray:
    starts = path[:-1]
    delta = path[1:] - starts
    denominator = np.sum(delta * delta, axis=1)
    ratio = np.zeros_like(denominator)
    active = denominator > np.finfo(float).eps
    relative = point - starts
    ratio[active] = np.sum(relative[active] * delta[active], axis=1) / denominator[active]
    ratio = np.clip(ratio, 0.0, 1.0)
    closest = starts + ratio[:, None] * delta
    index = int(np.argmin(np.linalg.norm(closest - point, axis=1)))
    suffix = np.vstack((closest[index], path[index + 1 :]))
    if len(suffix) < 2 or path_length(suffix) <= np.finfo(float).eps:
        return path[-2:].copy()
    return suffix


def _resample_polyline(path: FloatArray, count: int) -> FloatArray:
    distance = np.concatenate(
        ([0.0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1)))
    )
    keep = np.concatenate(([True], np.diff(distance) > np.finfo(float).eps))
    filtered = path[keep]
    distance = distance[keep]
    if len(filtered) < 2 or distance[-1] <= np.finfo(float).eps:
        return np.repeat(filtered[:1], count, axis=0)
    query = np.linspace(0.0, distance[-1], count)
    return np.column_stack(
        (
            np.interp(query, distance, filtered[:, 0]),
            np.interp(query, distance, filtered[:, 1]),
        )
    )


def _shifted_seed(
    memory: PlannerMemory,
    segment: _Segment,
    config: PlannerConfig,
) -> FloatArray:
    width = config.waypoint_count - 2
    accepted = np.asarray(memory.chromosome, dtype=np.float64).reshape(-1)
    if accepted.shape != (width,) or memory.rejoin_index != segment.rejoin_index:
        return np.zeros(width)
    if width == 1:
        return np.zeros(1)
    return _canonicalize(np.concatenate((accepted[1:], [0.0])), config)


def _initial_population(
    anchor: FloatArray,
    config: PlannerConfig,
    rng: np.random.Generator,
) -> FloatArray:
    width = config.waypoint_count - 2
    population = rng.uniform(
        -config.max_offset_m,
        config.max_offset_m,
        size=(config.population, width),
    )
    if config.initialization_mode == "shifted":
        population[0] = anchor
    return population


def _next_population(
    current: FloatArray,
    costs: FloatArray,
    evaluated: NDArray[np.bool_],
    config: PlannerConfig,
    rng: np.random.Generator,
) -> FloatArray:
    finite = np.flatnonzero(evaluated & np.isfinite(costs))
    if finite.size == 0:
        return rng.uniform(
            -config.max_offset_m,
            config.max_offset_m,
            size=current.shape,
        )
    order = finite[np.argsort(costs[finite])]
    elite_count = min(config.elite_count, order.size)
    elites = current[order[:elite_count]]
    population = np.empty_like(current)
    population[:elite_count] = elites
    for index in range(elite_count, config.population):
        parents = elites[rng.integers(0, elite_count, size=2)]
        mask = rng.random(current.shape[1]) > 0.5
        child = np.where(mask, parents[1], parents[0])
        child += config.mutation_sigma_m * rng.standard_normal(current.shape[1])
        population[index] = _canonicalize(child, config)
    return population


def _canonicalize(chromosome: FloatArray, config: PlannerConfig) -> FloatArray:
    return np.clip(
        np.asarray(chromosome, dtype=np.float64).reshape(-1),
        -config.max_offset_m,
        config.max_offset_m,
    )


def _failure_result(
    status: str,
    global_path: FloatArray,
    original_path: FloatArray,
    memory: PlannerMemory,
    started: float,
    segment: _Segment | None = None,
) -> PlanResult:
    previous = np.asarray(memory.path, dtype=np.float64)
    fallback_available = bool(
        previous.ndim == 2
        and previous.shape[1:] == (2,)
        and len(previous) >= 2
        and np.isfinite(previous).all()
    )
    return PlanResult(
        status=status,
        path=previous.copy() if fallback_available else np.empty((0, 2)),
        chromosome=np.empty(0),
        terms=np.full(5, np.inf),
        score=np.inf,
        feasible=False,
        fallback_available=fallback_available,
        path_source="previous_unvalidated" if fallback_available else "none",
        constraint_violation=np.inf,
        rejoin_error_m=np.inf,
        minimum_obstacle_clearance_m=np.nan,
        minimum_context_metric=np.nan,
        maximum_curvature_inv_m=np.nan,
        candidate_count=0,
        decode_count=0,
        pre_repair_feasible_count=0,
        post_repair_feasible_count=0,
        repaired_feasible_count=0,
        repair_level=-1,
        generations_completed=0,
        segment_start_index=-1 if segment is None else segment.start_index,
        segment_rejoin_index=-1 if segment is None else segment.rejoin_index,
        global_path_unchanged=np.array_equal(global_path, original_path),
        elapsed_ms=1000.0 * (perf_counter() - started),
    )


def _validate_context(context: Context) -> None:
    _vector(context.position, 2, "context position")
    _vector(context.direction, 2, "context direction")
    scalars = np.asarray(
        (context.speed, context.confidence, context.age_ms),
        dtype=np.float64,
    )
    if not np.isfinite(scalars).all() or context.speed < 0.0:
        raise ValueError("context scalars are invalid")
    if not 0.0 <= context.confidence <= 1.0 or context.age_ms < 0.0:
        raise ValueError("context confidence or age is invalid")


def _vector(value: FloatArray, width: int, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64).reshape(-1)
    if array.shape != (width,) or not np.isfinite(array).all():
        raise ValueError(f"{name} must contain {width} finite values")
    return array


def _path(value: FloatArray, name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != 2 or len(array) < 2:
        raise ValueError(f"{name} must have shape [N,2]")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must be finite")
    return array


def _obstacles(value: FloatArray) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.size == 0:
        return np.empty((0, 3))
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError("obstacles must have shape [N,3]")
    if not np.isfinite(array).all() or np.any(array[:, 2] < 0.0):
        raise ValueError("obstacles must contain finite nonnegative radii")
    return array


def _sigmoid(value: FloatArray) -> FloatArray:
    return 1.0 / (1.0 + np.exp(-np.clip(value, -60.0, 60.0)))


def _softmax(value: FloatArray) -> FloatArray:
    shifted = value - np.max(value)
    probability = np.exp(shifted)
    return probability / probability.sum()
