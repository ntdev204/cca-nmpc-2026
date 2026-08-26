from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

try:
    from .planner import (
        Context,
        LstmState,
        LstmWeights,
        Observation,
        PlanResult,
        PlannerConfig,
        PlannerMemory,
        context_from_velocity,
        observe_context,
        path_curvature,
        path_length,
        plan_local_path,
    )
except ImportError:
    from planner import (
        Context,
        LstmState,
        LstmWeights,
        Observation,
        PlanResult,
        PlannerConfig,
        PlannerMemory,
        context_from_velocity,
        observe_context,
        path_curvature,
        path_length,
        plan_local_path,
    )


FloatArray = NDArray[np.float64]
BASELINES = ("G0", "GCV", "GLT", "P")
SCENARIOS = (
    "corridor", "crossing", "head_on", "passing", "overtaking",
    "stop_go", "dropout", "narrow", "lateral",
)


@dataclass(slots=True)
class SequencePackage:
    package_id: str
    global_path: FloatArray
    robot_states: FloatArray
    observations: tuple[Observation, ...]
    obstacles: FloatArray
    replan_trigger: NDArray[np.bool_]
    segment_start_index: NDArray[np.int64]
    segment_rejoin_index: NDArray[np.int64]

    def validate(self) -> None:
        steps = len(self.observations)
        if self.global_path.ndim != 2 or self.global_path.shape[1] != 2:
            raise ValueError("global path must have shape [N,2]")
        if self.robot_states.shape != (steps, 6):
            raise ValueError("robot states must have shape [T,6]")
        if self.replan_trigger.shape != (steps,):
            raise ValueError("replan trigger must have shape [T]")
        if self.segment_start_index.shape != (steps,):
            raise ValueError("segment start index must have shape [T]")
        if self.segment_rejoin_index.shape != (steps,):
            raise ValueError("segment rejoin index must have shape [T]")
        if self.obstacles.size and self.obstacles.shape[1] != 3:
            raise ValueError("obstacles must have shape [N,3]")
        arrays = (self.global_path, self.robot_states, self.obstacles)
        if any(not np.isfinite(array).all() for array in arrays):
            raise ValueError("sequence arrays must be finite")
        if not self.replan_trigger.any():
            raise ValueError("sequence requires at least one planning event")
        if np.any(self.segment_start_index < 0):
            raise ValueError("segment start indices must be nonnegative")
        if np.any(self.segment_rejoin_index <= self.segment_start_index):
            raise ValueError("segment rejoin indices must follow their starts")
        if np.any(self.segment_rejoin_index >= len(self.global_path)):
            raise ValueError("segment rejoin indices exceed the global path")


@dataclass(slots=True)
class StudyRun:
    summary: dict[str, Any]
    paths: dict[str, list[FloatArray]]
    event_steps: list[int]
    traces: dict[str, list[dict[str, Any]]] | None = None


def scenario_package(name: str = "corridor") -> SequencePackage:
    """Build one deterministic, fixed-global-path CCA scenario."""
    if name not in SCENARIOS:
        raise ValueError(f"unknown scenario: {name}")
    steps = 24
    progress = np.linspace(0.0, 1.0, steps)
    if name == "lateral":
        global_path = np.column_stack((np.zeros(101), np.linspace(0.0, 2.0, 101)))
        robot_xy = np.column_stack((np.zeros(steps), 0.72 * progress))
        human_xy = np.column_stack((0.42 * np.sin(2.0 * np.pi * progress),
                                    1.10 * np.ones(steps)))
    else:
        global_path = np.column_stack((np.linspace(0.0, 2.4, 121), np.zeros(121)))
        robot_xy = np.column_stack((0.72 * progress, np.zeros(steps)))
        if name == "crossing":
            human_xy = np.column_stack((0.95 * np.ones(steps), 0.95 - 1.6 * progress))
        elif name == "head_on":
            human_xy = np.column_stack((1.85 - 1.20 * progress, 0.12 * np.ones(steps)))
        elif name in {"passing", "overtaking"}:
            human_xy = np.column_stack((0.50 + 0.70 * progress, 0.48 * np.ones(steps)))
        elif name == "stop_go":
            stop = np.clip((progress - 0.35) / 0.25, 0.0, 1.0)
            human_xy = np.column_stack((0.60 + 0.75 * stop, -0.42 * np.ones(steps)))
        else:
            human_xy = np.column_stack((0.88 * np.ones(steps), 0.58 * np.ones(steps)))
    robot_states = np.zeros((steps, 6), dtype=np.float64)
    robot_states[:, :2] = robot_xy
    robot_states[1:, 3:5] = np.diff(robot_xy, axis=0) / 0.10
    observations_xy = human_xy.copy()
    features = np.zeros_like(observations_xy)
    features[1:] = np.diff(observations_xy, axis=0) / 0.10
    valid = np.ones(steps, dtype=bool)
    if name == "dropout":
        valid[[5, 6, 14]] = False
    observations = tuple(
        Observation(
            observations_xy[index],
            features[index],
            0.0 if valid[index] else 250.0,
            bool(valid[index]),
        )
        for index in range(steps)
    )
    trigger = np.zeros(steps, dtype=bool)
    trigger[::3] = True
    if name == "narrow":
        obstacles = np.asarray(((1.10, 0.27, 0.10), (1.55, -0.27, 0.10)))
    else:
        obstacles = np.asarray(((1.32, -0.72, 0.08),), dtype=np.float64)
    starts, rejoins = _register_segments(global_path, robot_states, 1.5)
    package = SequencePackage(
        f"scenario-{name}",
        global_path,
        robot_states,
        observations,
        obstacles,
        trigger,
        starts,
        rejoins,
    )
    package.validate()
    return package


def smoke_package() -> SequencePackage:
    steps = 10
    global_path = np.column_stack((np.linspace(0.0, 1.8, 91), np.zeros(91)))
    robot_states = np.zeros((steps, 6))
    robot_states[:, 0] = np.linspace(0.0, 0.27, steps)
    positions = np.column_stack(
        (
            np.full(steps, 0.90),
            np.asarray((0.60, 0.54, 0.47, 0.39, 0.31, 0.25, 0.29, 0.37, 0.48, 0.60)),
        )
    )
    features = np.zeros_like(positions)
    features[1:] = (positions[1:] - positions[:-1]) / 0.10
    observations = tuple(
        Observation(positions[index], features[index], 0.0, True)
        for index in range(steps)
    )
    trigger = np.zeros(steps, dtype=bool)
    trigger[[0, 3, 6, 9]] = True
    obstacles = np.asarray(((1.25, -0.72, 0.08),), dtype=np.float64)
    starts, rejoins = _register_segments(global_path, robot_states, 1.5)
    return SequencePackage(
        "deterministic-smoke",
        global_path,
        robot_states,
        observations,
        obstacles,
        trigger,
        starts,
        rejoins,
    )


def _register_segments(
    global_path: FloatArray,
    robot_states: FloatArray,
    lookahead_distance_m: float,
) -> tuple[NDArray[np.int64], NDArray[np.int64]]:
    starts = np.empty(len(robot_states), dtype=np.int64)
    rejoins = np.empty(len(robot_states), dtype=np.int64)
    for index, state in enumerate(robot_states):
        start = int(np.argmin(np.linalg.norm(global_path[:-1] - state[:2], axis=1)))
        remaining = global_path[start:]
        distance = np.concatenate(
            ([0.0], np.cumsum(np.linalg.norm(np.diff(remaining, axis=0), axis=1)))
        )
        offset = int(np.searchsorted(distance, lookahead_distance_m))
        starts[index] = start
        rejoins[index] = min(start + max(offset, 1), len(global_path) - 1)
    return starts, rejoins


def smoke_lstm_weights() -> LstmWeights:
    width = 2
    gates = np.zeros((4 * width, 2 + width))
    gates[3 * width :, :2] = 0.85 * np.eye(width)
    gates[3 * width :, 2:] = 0.15 * np.eye(width)
    bias = np.concatenate(
        (
            np.full(width, _logit(0.70)),
            np.full(width, _logit(0.80)),
            np.full(width, _logit(0.90)),
            np.zeros(width),
        )
    )
    return LstmWeights(gates, bias, np.eye(2), np.zeros(2))


def smoke_config() -> PlannerConfig:
    return PlannerConfig(
        population=6,
        generations=2,
        candidate_budget=12,
        decode_budget=12,
        waypoint_count=5,
        path_samples=21,
        elite_count=2,
        repair_steps=1,
        temperature=0.10,
    )


def run_sequence(
    package: SequencePackage,
    config: PlannerConfig,
    *,
    algorithm_seed: int,
    lstm_weights: LstmWeights,
) -> StudyRun:
    package.validate()
    traces: dict[str, list[dict[str, Any]]] = {name: [] for name in BASELINES}
    paths: dict[str, list[FloatArray]] = {name: [] for name in BASELINES}
    memory = {name: PlannerMemory() for name in BASELINES}
    state = {
        "GLT": LstmState.zeros(2),
        "P": LstmState.zeros(2),
    }
    context = {
        name: Context.invalid(package.observations[0].position, 0.0)
        for name in BASELINES
    }
    context_updates = {name: 0 for name in BASELINES}
    event_steps: list[int] = []
    event_index = 0
    for step_index, observation in enumerate(package.observations):
        current, next_state = observe_context(
            observation,
            state["P"],
            lstm_weights,
            config,
        )
        context["P"] = current
        if current.valid:
            state["P"] = next_state
            context_updates["P"] += 1
        if observation.valid:
            cv_context = context_from_velocity(
                observation.position,
                observation.feature,
                observation.age_ms,
                config,
            )
        else:
            cv_context = Context.invalid(observation.position, observation.age_ms)
        context["GCV"] = cv_context
        if cv_context.valid:
            context_updates["GCV"] += 1
        if not package.replan_trigger[step_index]:
            continue
        event_steps.append(step_index)
        event_config = replace(
            config,
            start_index=int(package.segment_start_index[step_index]),
            rejoin_index=int(package.segment_rejoin_index[step_index]),
        )
        triggered, next_state = observe_context(
            observation,
            state["GLT"],
            lstm_weights,
            config,
        )
        context["GLT"] = triggered
        if triggered.valid:
            state["GLT"] = next_state
            context_updates["GLT"] += 1
        context["G0"] = Context.invalid(observation.position, observation.age_ms)
        paired_seed = algorithm_seed + 1009 * event_index
        for name in BASELINES:
            method_config = _method_config(event_config, name)
            result = plan_local_path(
                package.global_path,
                package.robot_states[step_index],
                context[name],
                package.obstacles,
                method_config,
                seed=paired_seed,
                memory=memory[name],
            )
            traces[name].append(
                _trace_row(
                    result,
                    package.global_path,
                    observation,
                    method_config,
                    step_index,
                    event_index,
                    paired_seed,
                )
            )
            paths[name].append(
                result.path.copy() if result.feasible else np.empty((0, 2))
            )
            if result.feasible:
                memory[name] = PlannerMemory(
                    result.chromosome.copy(),
                    result.path.copy(),
                    result.segment_rejoin_index,
                )
        event_index += 1
    methods = {
        name: _aggregate(traces[name], context_updates[name])
        for name in BASELINES
    }
    event_keys = {
        name: {
            (row["event_index"], row["algorithm_seed"])
            for row in traces[name]
        }
        for name in BASELINES
    }
    paired = (
        len({frozenset(keys) for keys in event_keys.values()}) == 1
        and len(event_keys["P"]) == int(package.replan_trigger.sum())
    )
    summary = {
        "schema": "cca-python-sequence-study-v1",
        "status": "development-smoke-only",
        "evidence_admissible": False,
        "package_id": package.package_id,
        "package_sha256": _package_digest(package),
        "planner_config_sha256": _config_digest(config),
        "lstm_weights_sha256": _weights_digest(lstm_weights),
        "baselines": list(BASELINES),
        "paired_attempts": paired,
        "algorithm_seed": algorithm_seed,
        "context_model": "deterministic-untrained-lstm-fixture",
        "context_update_schedule": {
            "G0": "none",
            "GCV": "every-valid-observation",
            "GLT": "replan-trigger-only",
            "P": "every-valid-observation",
        },
        "metric_scope": "CCA-geometric-local-path-only",
        "nmpc_backend_included": False,
        "realtime_claim": False,
        "latency_interpretation": "desktop-telemetry-only",
        "human_trajectory_generated": False,
        "matched_contract": {
            "same_sequence_package": True,
            "same_fixed_global_path": True,
            "same_robot_states": True,
            "same_observation_stream": True,
            "same_obstacles": True,
            "same_registered_local_segment": True,
            "same_ga_seed_per_event": True,
            "candidate_budget": config.candidate_budget,
            "decode_budget": config.decode_budget,
        },
        "paired_contrasts": _paired_contrasts(traces),
        "methods": methods,
    }
    return StudyRun(summary, paths, event_steps, traces)


def render_study(
    package: SequencePackage,
    result: StudyRun,
    config: PlannerConfig,
    output: Path,
) -> None:
    import matplotlib.pyplot as plt

    joint_events = [
        index
        for index in range(len(result.event_steps))
        if all(result.paths[name][index].size for name in BASELINES)
    ]
    if not joint_events:
        raise ValueError("no same-event feasible paths are available for rendering")
    selected_event = joint_events[-1]
    selected_step = result.event_steps[selected_event]
    figure, axis = plt.subplots(figsize=(9.0, 5.0), constrained_layout=True)
    axis.plot(
        package.global_path[:, 0],
        package.global_path[:, 1],
        "--",
        color="#475569",
        linewidth=1.8,
        label="fixed global path",
    )
    colors = {
        "G0": "#64748b",
        "GCV": "#0891b2",
        "GLT": "#7c3aed",
        "P": "#2563eb",
    }
    for name in BASELINES:
        path = result.paths[name][selected_event]
        axis.plot(path[:, 0], path[:, 1], color=colors[name], label=name)
    for obstacle in package.obstacles:
        axis.add_patch(
            plt.Circle(
                obstacle[:2],
                obstacle[2]
                + config.footprint_radius_m
                + config.safe_distance_m,
                facecolor="#fca5a5",
                edgecolor="#dc2626",
                alpha=0.65,
            )
        )
    current_human = package.observations[selected_step].position
    axis.scatter(*current_human, marker="o", color="#dc2626", label="current human")
    axis.set_title(f"CCA event {selected_event}, observation step {selected_step}")
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("x (m)")
    axis.set_ylabel("y (m)")
    axis.grid(True, alpha=0.25)
    axis.legend(ncol=2)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180)
    plt.close(figure)


def _resample_path(path: FloatArray, count: int) -> FloatArray:
    distance = np.concatenate(
        ([0.0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1)))
    )
    keep = np.concatenate(([True], np.diff(distance) > np.finfo(float).eps))
    path = path[keep]
    distance = distance[keep]
    if len(path) < 2 or distance[-1] <= np.finfo(float).eps:
        return np.repeat(path[:1], count, axis=0)
    query = np.linspace(0.0, distance[-1], count)
    return np.column_stack(
        (
            np.interp(query, distance, path[:, 0]),
            np.interp(query, distance, path[:, 1]),
        )
    )


def _reference_from_path(
    path: FloatArray,
    horizon: int,
    dt_s: float,
    velocity_time_constant_s: float = 0.20,
) -> FloatArray:
    points = _resample_path(path, horizon + 1)
    points[-1] = points[-2]
    delta = np.diff(points, axis=0)
    yaw = np.zeros(horizon + 1, dtype=np.float64)
    yaw[:-1] = np.arctan2(delta[:, 1], delta[:, 0])
    yaw[-1] = yaw[-2]
    yaw = np.unwrap(yaw)
    velocity = np.zeros((horizon + 1, 3), dtype=np.float64)
    for index in range(horizon):
        cosine = np.cos(yaw[index])
        sine = np.sin(yaw[index])
        world = delta[index] / dt_s
        velocity[index + 1, :2] = (
            cosine * world[0] + sine * world[1],
            -sine * world[0] + cosine * world[1],
        )
        velocity[index + 1, 2] = (yaw[index + 1] - yaw[index]) / dt_s
    velocity[-1] = 0.0
    return np.column_stack(
        (
            np.arange(horizon + 1, dtype=np.float64) * dt_s,
            points,
            yaw,
            velocity,
        )
    )


def export_cca_contract(
    package: SequencePackage,
    result: StudyRun,
    config: PlannerConfig,
    output: Path,
    *,
    horizon: int = 20,
    dt_s: float = 0.10,
    lstm_weights: LstmWeights | None = None,
) -> dict[str, Any]:
    """Export one CCA path and its NMPC-ready state reference."""
    feasible = [
        (event_index, path)
        for event_index, path in enumerate(result.paths["P"])
        if path.ndim == 2 and path.shape[0] >= 2
    ]
    event_index, path = feasible[0] if feasible else (-1, np.empty((0, 2)))
    output.mkdir(parents=True, exist_ok=True)
    local_file = output / "cca_local_path.csv"
    reference_file = output / "cca_reference.csv"
    events_file = output / "cca_events.csv"
    manifest_file = output / "cca_run.json"
    with local_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("point_index", "x_m", "y_m"))
        if feasible:
            writer.writerows(
                (index, float(point[0]), float(point[1]))
                for index, point in enumerate(path)
            )
    reference = _reference_from_path(path, horizon, dt_s) if feasible else np.empty((0, 7))
    with reference_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("time_s", "x_m", "y_m", "theta_rad", "vx_mps", "vy_mps", "omega_radps"))
        if reference.size:
            writer.writerows(reference.tolist())
    with events_file.open("w", newline="", encoding="utf-8") as handle:
        fields = (
            "event_index", "step_index", "feasible", "status", "path_source",
            "segment_start_index", "segment_rejoin_index", "candidate_count",
            "decode_count", "elapsed_ms",
        )
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        traces = result.traces["P"] if result.traces is not None else []
        for index, step in enumerate(result.event_steps):
            trace = next(
                (row for row in traces if row.get("event_index") == index),
                None,
            )
            if trace is None:
                trace = {"event_index": index, "step_index": step}
            writer.writerow({field: trace.get(field, "") for field in fields})
    weights = smoke_lstm_weights() if lstm_weights is None else lstm_weights
    manifest = {
        "schema": "cca-nmpc-cca-contract-v1",
        "status": "development-simulation" if feasible else "no-feasible-proposal",
        "evidence_admissible": False,
        "package_id": package.package_id,
        "selected_method": "P",
        "selected_event_index": event_index if feasible else None,
        "global_path_unchanged": True,
        "nmpc_input": "cca_reference.csv" if feasible else None,
        "state_order": ["x", "y", "theta", "vx", "vy", "omega"],
        "command_order": ["vx_cmd", "vy_cmd", "omega_cmd"],
        "dt_s": dt_s,
        "horizon": horizon,
        "planner_config_sha256": _config_digest(config),
        "lstm_weights_sha256": _weights_digest(weights),
        "sequence_package_sha256": _package_digest(package),
        "human_trajectory_generated": False,
        "nmpc_backend_included": False,
        "hardware_run": False,
        "files": {
            "local_path": local_file.name,
            "reference": reference_file.name,
            "events": events_file.name,
        },
    }
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _method_config(config: PlannerConfig, name: str) -> PlannerConfig:
    return replace(config, context_enabled=name != "G0")


def _trace_row(
    result: PlanResult,
    global_path: FloatArray,
    observation: Observation,
    config: PlannerConfig,
    step_index: int,
    event_index: int,
    algorithm_seed: int,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "step_index": step_index,
        "event_index": event_index,
        "algorithm_seed": algorithm_seed,
        "feasible": result.feasible,
        "status": result.status,
        "fallback_available": result.fallback_available,
        "path_source": result.path_source,
        "segment_start_index": result.segment_start_index,
        "segment_rejoin_index": result.segment_rejoin_index,
        "candidate_count": result.candidate_count,
        "decode_count": result.decode_count,
        "pre_repair_feasible_count": result.pre_repair_feasible_count,
        "post_repair_feasible_count": result.post_repair_feasible_count,
        "repaired_feasible_count": result.repaired_feasible_count,
        "repair_level": result.repair_level,
        "elapsed_ms": result.elapsed_ms,
    }
    if not result.feasible:
        return row
    curvature = path_curvature(result.path)
    distance = np.linalg.norm(np.diff(result.path, axis=0), axis=1)
    integrated_curvature = float(
        np.sum(0.5 * (curvature[:-1] ** 2 + curvature[1:] ** 2) * distance)
    )
    row.update(
        {
            "path_length_m": path_length(result.path),
            "integrated_squared_curvature_inv_m": integrated_curvature,
            "global_deviation_m": _mean_polyline_distance(result.path, global_path),
            "continuity_m": float(result.terms[4]),
            "rejoin_error_m": result.rejoin_error_m,
            "minimum_obstacle_clearance_m": result.minimum_obstacle_clearance_m,
            "minimum_context_metric": result.minimum_context_metric,
            "observed_human_clearance_m": _observed_human_clearance(
                result.path,
                observation.position,
                config,
            ),
        }
    )
    return row


def _aggregate(rows: list[dict[str, Any]], context_updates: int) -> dict[str, Any]:
    attempts = len(rows)
    successes = sum(int(row["feasible"]) for row in rows)
    output: dict[str, Any] = {
        "attempts": attempts,
        "valid_paths": successes,
        "valid_path_yield": successes / attempts if attempts else 0.0,
        "context_update_count": context_updates,
        "candidate_count": int(sum(row["candidate_count"] for row in rows)),
        "decode_count": int(sum(row["decode_count"] for row in rows)),
        "pre_repair_feasible_count": int(
            sum(row["pre_repair_feasible_count"] for row in rows)
        ),
        "post_repair_feasible_count": int(
            sum(row["post_repair_feasible_count"] for row in rows)
        ),
        "repaired_feasible_count": int(
            sum(row["repaired_feasible_count"] for row in rows)
        ),
        "failure_counts": _failure_counts(rows),
        "path_metrics_scope": "descriptive-success-only",
    }
    latency = np.asarray([row["elapsed_ms"] for row in rows], dtype=np.float64)
    output["latency_ms_telemetry"] = {
        "p50": float(np.percentile(latency, 50)) if latency.size else None,
        "p95": float(np.percentile(latency, 95)) if latency.size else None,
        "p99": float(np.percentile(latency, 99)) if latency.size else None,
    }
    metrics = (
        "path_length_m",
        "integrated_squared_curvature_inv_m",
        "global_deviation_m",
        "continuity_m",
        "rejoin_error_m",
        "minimum_obstacle_clearance_m",
        "minimum_context_metric",
        "observed_human_clearance_m",
    )
    for metric in metrics:
        values = np.asarray(
            [row[metric] for row in rows if metric in row and np.isfinite(row[metric])],
            dtype=np.float64,
        )
        output[metric] = {
            "median": float(np.median(values)) if values.size else None,
            "mean": float(np.mean(values)) if values.size else None,
        }
    return output


def _paired_contrasts(
    traces: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    metrics = (
        "path_length_m",
        "integrated_squared_curvature_inv_m",
        "global_deviation_m",
        "continuity_m",
        "rejoin_error_m",
        "minimum_obstacle_clearance_m",
        "observed_human_clearance_m",
    )
    proposed = {row["event_index"]: row for row in traces["P"]}
    output: dict[str, Any] = {}
    for baseline in ("GLT", "GCV", "G0"):
        comparator = {row["event_index"]: row for row in traces[baseline]}
        keys_match = proposed.keys() == comparator.keys()
        event_ids = sorted(proposed.keys() & comparator.keys())
        paired_rows = [(proposed[index], comparator[index]) for index in event_ids]
        valid_delta = np.asarray(
            [int(first["feasible"]) - int(second["feasible"]) for first, second in paired_rows],
            dtype=np.float64,
        )
        item: dict[str, Any] = {
            "sign": "P-minus-baseline",
            "event_keys_match": keys_match,
            "event_count": len(event_ids),
            "valid_path_yield_difference": (
                float(np.mean(valid_delta)) if valid_delta.size else None
            ),
            "joint_valid_count": sum(
                int(first["feasible"] and second["feasible"])
                for first, second in paired_rows
            ),
            "p_only_valid_count": sum(
                int(first["feasible"] and not second["feasible"])
                for first, second in paired_rows
            ),
            "baseline_only_valid_count": sum(
                int(not first["feasible"] and second["feasible"])
                for first, second in paired_rows
            ),
            "both_invalid_count": sum(
                int(not first["feasible"] and not second["feasible"])
                for first, second in paired_rows
            ),
            "joint-valid-metric-differences": {},
        }
        for metric in metrics:
            differences = np.asarray(
                [
                    first[metric] - second[metric]
                    for first, second in paired_rows
                    if metric in first
                    and metric in second
                    and np.isfinite(first[metric])
                    and np.isfinite(second[metric])
                ],
                dtype=np.float64,
            )
            item["joint-valid-metric-differences"][metric] = {
                "count": int(differences.size),
                "mean": float(np.mean(differences)) if differences.size else None,
                "median": float(np.median(differences)) if differences.size else None,
            }
        output[f"P−{baseline}"] = item
    return output


def _failure_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        if row["feasible"]:
            continue
        status = str(row["status"])
        counts[status] = counts.get(status, 0) + 1
    return counts


def _observed_human_clearance(
    path: FloatArray,
    human_position: FloatArray,
    config: PlannerConfig,
) -> float:
    common_radius = (
        max(
            config.human_forward_radius_m,
            config.human_rear_radius_m,
            config.human_lateral_radius_m,
        )
        + config.footprint_radius_m
        + config.safe_distance_m
    )
    return _polyline_distance(human_position, path) - common_radius


def _mean_polyline_distance(path: FloatArray, reference: FloatArray) -> float:
    distances = [_polyline_distance(point, reference) for point in path]
    return float(np.mean(distances))


def _polyline_distance(point: FloatArray, path: FloatArray) -> float:
    starts = path[:-1]
    delta = path[1:] - starts
    denominator = np.sum(delta * delta, axis=1)
    ratio = np.zeros_like(denominator)
    active = denominator > np.finfo(float).eps
    relative = point - starts
    ratio[active] = np.sum(relative[active] * delta[active], axis=1) / denominator[active]
    closest = starts + np.clip(ratio, 0.0, 1.0)[:, None] * delta
    return float(np.min(np.linalg.norm(closest - point, axis=1)))


def _logit(probability: float) -> float:
    return float(np.log(probability / (1.0 - probability)))


def _package_digest(package: SequencePackage) -> str:
    digest = hashlib.sha256(package.package_id.encode("utf-8"))
    for array in (
        package.global_path,
        package.robot_states,
        package.obstacles,
        package.segment_start_index,
        package.segment_rejoin_index,
    ):
        value = np.ascontiguousarray(array, dtype=np.float64)
        digest.update(value.shape.__repr__().encode("ascii"))
        digest.update(value.tobytes())
    digest.update(np.ascontiguousarray(package.replan_trigger).tobytes())
    for observation in package.observations:
        digest.update(np.ascontiguousarray(observation.position).tobytes())
        digest.update(np.ascontiguousarray(observation.feature).tobytes())
        digest.update(np.float64(observation.age_ms).tobytes())
        digest.update(bytes((int(observation.valid),)))
    return digest.hexdigest()


def _config_digest(config: PlannerConfig) -> str:
    payload = json.dumps(asdict(config), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _weights_digest(weights: LstmWeights) -> str:
    digest = hashlib.sha256()
    for array in (
        weights.gates,
        weights.bias,
        weights.velocity,
        weights.velocity_bias,
    ):
        value = np.ascontiguousarray(array, dtype=np.float64)
        digest.update(value.shape.__repr__().encode("ascii"))
        digest.update(value.tobytes())
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument(
        "--scenario",
        choices=SCENARIOS,
        default="corridor",
    )
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--plot", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if args.all and (args.smoke or args.plot is not None):
        parser.error("--all cannot be combined with --smoke or --plot")
    if args.all:
        if args.output is None:
            parser.error("--all requires --output")
        campaign: dict[str, Any] = {
            "schema": "cca-python-campaign-v1",
            "status": "development-simulation",
            "evidence_admissible": False,
            "scenarios": {},
        }
        for index, scenario in enumerate(SCENARIOS):
            package = scenario_package(scenario)
            result = run_sequence(
                package,
                config=smoke_config(),
                algorithm_seed=args.seed + index,
                lstm_weights=smoke_lstm_weights(),
            )
            scenario_output = args.output / scenario
            scenario_output.mkdir(parents=True, exist_ok=True)
            (scenario_output / "cca_summary.json").write_text(
                json.dumps(result.summary, indent=2), encoding="utf-8"
            )
            contract = export_cca_contract(
                package,
                result,
                smoke_config(),
                scenario_output,
                lstm_weights=smoke_lstm_weights(),
            )
            campaign["scenarios"][scenario] = {
                "package_id": package.package_id,
                "contract_status": contract["status"],
                "methods": result.summary["methods"],
            }
        (args.output / "campaign.json").write_text(
            json.dumps(campaign, indent=2), encoding="utf-8"
        )
        print(json.dumps(campaign, sort_keys=True, separators=(",", ":")))
        return 0
    package = smoke_package() if args.smoke else scenario_package(args.scenario)
    config = smoke_config()
    result = run_sequence(
        package,
        config,
        algorithm_seed=args.seed,
        lstm_weights=smoke_lstm_weights(),
    )
    if args.plot is not None:
        render_study(package, result, config, args.plot)
    output = result.summary
    if args.output is not None:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "cca_summary.json").write_text(
            json.dumps(result.summary, indent=2), encoding="utf-8"
        )
        output = dict(result.summary)
        output["contract"] = export_cca_contract(
            package,
            result,
            config,
            args.output,
            lstm_weights=smoke_lstm_weights(),
        )
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
