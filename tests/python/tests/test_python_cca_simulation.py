from __future__ import annotations

from dataclasses import replace

import numpy as np

from simulations.python.planner import (
    Context,
    LstmState,
    Observation,
    PlannerConfig,
    PlannerMemory,
    context_from_velocity,
    observe_context,
    plan_local_path,
)
from simulations.python.study import (
    _observed_human_clearance,
    smoke_config,
    smoke_lstm_weights,
    smoke_package,
    run_sequence,
)


def test_context_update_holds_state_when_observation_is_stale() -> None:
    config = smoke_config()
    weights = smoke_lstm_weights()
    previous = LstmState.zeros(2)
    observation = Observation(np.asarray((0.4, 0.3)), np.asarray((0.2, -0.1)))
    context, updated = observe_context(observation, previous, weights, config)
    assert context.valid
    assert np.linalg.norm(updated.hidden) > 0.0
    stale = replace(observation, age_ms=config.max_context_age_ms + 1.0)
    invalid, held = observe_context(stale, updated, weights, config)
    assert not invalid.valid
    np.testing.assert_array_equal(held.hidden, updated.hidden)
    np.testing.assert_array_equal(held.cell, updated.cell)


def test_planner_is_deterministic_and_preserves_the_global_path() -> None:
    global_path = np.column_stack((np.linspace(0.0, 1.0, 51), np.zeros(51)))
    original = global_path.copy()
    state = np.zeros(6)
    context = Context.invalid(np.asarray((0.5, 0.8)), 0.0)
    config = PlannerConfig(
        population=4,
        generations=2,
        candidate_budget=8,
        decode_budget=8,
        waypoint_count=5,
        path_samples=21,
        elite_count=2,
        repair_steps=1,
        context_enabled=False,
    )
    first = plan_local_path(
        global_path,
        state,
        context,
        np.empty((0, 3)),
        config,
        seed=31,
    )
    second = plan_local_path(
        global_path,
        state,
        context,
        np.empty((0, 3)),
        config,
        seed=31,
    )
    assert first.feasible and second.feasible
    assert first.global_path_unchanged and second.global_path_unchanged
    np.testing.assert_array_equal(global_path, original)
    np.testing.assert_allclose(first.path, second.path, atol=0.0, rtol=0.0)
    np.testing.assert_allclose(first.chromosome, second.chromosome, atol=0.0, rtol=0.0)
    assert np.linalg.norm(first.path[0] - state[:2]) <= 1.0e-12
    assert np.linalg.norm(first.path[-1] - global_path[-1]) <= 1.0e-12


def test_human_footprint_constraint_can_reject_the_only_path() -> None:
    global_path = np.column_stack((np.linspace(0.0, 0.8, 41), np.zeros(41)))
    state = np.zeros(6)
    config = PlannerConfig(
        population=1,
        generations=1,
        candidate_budget=1,
        decode_budget=1,
        waypoint_count=3,
        path_samples=9,
        elite_count=1,
        max_offset_m=0.0,
        repair_steps=0,
        repair_mode="decoder_only",
        temperature=0.1,
    )
    context = context_from_velocity(
        np.asarray((0.4, 0.0)),
        np.asarray((0.0, 0.2)),
        0.0,
        config,
    )
    result = plan_local_path(
        global_path,
        state,
        context,
        np.empty((0, 3)),
        config,
        seed=7,
    )
    assert result.status == "no_feasible_candidate"
    assert not result.feasible
    assert result.candidate_count == 1
    assert result.decode_count == 1


def test_sequence_baselines_are_paired_and_continuous_updates_more_often() -> None:
    result = run_sequence(
        smoke_package(),
        smoke_config(),
        algorithm_seed=101,
        lstm_weights=smoke_lstm_weights(),
    )
    summary = result.summary
    assert summary["paired_attempts"]
    assert not summary["evidence_admissible"]
    assert not summary["nmpc_backend_included"]
    assert not summary["human_trajectory_generated"]
    assert len(summary["package_sha256"]) == 64
    assert len(summary["lstm_weights_sha256"]) == 64
    assert summary["matched_contract"]["same_ga_seed_per_event"]
    methods = summary["methods"]
    assert {methods[name]["attempts"] for name in methods} == {4}
    assert methods["P"]["context_update_count"] > methods["GLT"][
        "context_update_count"
    ]
    assert methods["GCV"]["context_update_count"] == methods["P"][
        "context_update_count"
    ]
    contrasts = summary["paired_contrasts"]
    assert set(contrasts) == {"P−GLT", "P−GCV", "P−G0"}
    assert all(item["event_keys_match"] for item in contrasts.values())


def test_invalid_observation_is_rejected_by_lstm_and_cv_contexts() -> None:
    package = smoke_package()
    observations = list(package.observations)
    observations[3] = replace(observations[3], valid=False)
    result = run_sequence(
        replace(package, observations=tuple(observations)),
        smoke_config(),
        algorithm_seed=101,
        lstm_weights=smoke_lstm_weights(),
    )
    methods = result.summary["methods"]
    assert methods["P"]["context_update_count"] == 9
    assert methods["GCV"]["context_update_count"] == 9
    assert methods["P"]["failure_counts"]["invalid_context"] == 1
    assert methods["GCV"]["failure_counts"]["invalid_context"] == 1


def test_failure_exposes_previous_path_without_claiming_current_feasibility() -> None:
    path = np.column_stack((np.linspace(0.0, 1.0, 21), np.zeros(21)))
    memory = PlannerMemory(np.zeros(3), path.copy(), 20)
    result = plan_local_path(
        path,
        np.zeros(6),
        Context.invalid(np.asarray((0.5, 0.2)), 0.0),
        np.empty((0, 3)),
        PlannerConfig(
            population=1,
            generations=1,
            candidate_budget=1,
            decode_budget=1,
            waypoint_count=5,
            path_samples=21,
            elite_count=1,
            repair_steps=0,
        ),
        seed=5,
        memory=memory,
    )
    assert result.status == "invalid_context"
    assert not result.feasible
    assert result.fallback_available
    assert result.path_source == "previous_unvalidated"
    np.testing.assert_array_equal(result.path, path)


def test_registered_metric_lookahead_and_aligned_continuity() -> None:
    global_path = np.column_stack((np.linspace(0.0, 5.0, 51), np.zeros(51)))
    previous = np.column_stack((np.linspace(0.0, 1.8, 19), np.zeros(19)))
    config = PlannerConfig(
        population=1,
        generations=1,
        candidate_budget=1,
        decode_budget=1,
        waypoint_count=5,
        path_samples=19,
        elite_count=1,
        max_offset_m=0.0,
        repair_steps=0,
        context_enabled=False,
        lookahead_distance_m=0.8,
    )
    state = np.zeros(6)
    state[0] = 1.0
    result = plan_local_path(
        global_path,
        state,
        Context.invalid(np.asarray((0.0, 0.0)), 0.0),
        np.empty((0, 3)),
        config,
        seed=9,
        memory=PlannerMemory(np.zeros(3), previous, 18),
    )
    assert result.feasible
    assert result.segment_start_index == 10
    assert result.segment_rejoin_index == 18
    np.testing.assert_allclose(result.path[-1], global_path[18], atol=1.0e-12)
    assert result.terms[4] <= 1.0e-12


def test_common_human_clearance_is_context_independent() -> None:
    path = np.column_stack((np.linspace(0.0, 1.0, 11), np.ones(11)))
    config = PlannerConfig(
        half_length_m=0.12,
        half_width_m=0.16,
        human_forward_radius_m=0.25,
        human_rear_radius_m=0.25,
        human_lateral_radius_m=0.25,
        safe_distance_m=0.05,
    )
    clearance = _observed_human_clearance(path, np.asarray((0.5, 0.0)), config)
    assert abs(clearance - 0.5) <= 1.0e-12


def test_direction_confidence_threshold_is_bounded() -> None:
    with np.testing.assert_raises(ValueError):
        replace(smoke_config(), minimum_direction_confidence=1.1).validate()
