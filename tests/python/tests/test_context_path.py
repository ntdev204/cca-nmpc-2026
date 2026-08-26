from __future__ import annotations

import numpy as np
import pytest

from ai.ctx_lstm import direction_context_to_heading_observation
from ai.heading import HumanHeadingObservation, estimate_heading_observation
from runtime.map_planner import astar_plan
from runtime.local_path import (
    FixedGlobalLocalPath,
    context_footprint_points,
    evaluate_context_replan,
    generate_context_local_detour,
)


def _context_observation(direction: str = "forward"):
    return direction_context_to_heading_observation(
        direction,
        position_xy=np.asarray((5.0, 0.0)),
        speed_mps=0.3,
        direction_confidence=0.9,
        timestamp_ns=0,
        frame_id="map-frame",
        track_id=0,
        source_sha256="b" * 64,
        coordinate_units="map_m",
    )


def _heading_observation() -> HumanHeadingObservation:
    return estimate_heading_observation(
        np.asarray([[1.0, 0.0], [1.1, 0.0], [1.2, 0.0], [1.3, 0.0]]),
        np.asarray([0, 100_000_000, 200_000_000, 300_000_000]),
        track_id=2,
        frame_id="robot_local",
        source_sha256="a" * 64,
        detector_confidence=0.9,
        coordinate_units="m",
    )


def test_context_footprint_contains_current_context_position() -> None:
    footprint = context_footprint_points(_context_observation())
    assert footprint.shape[1] == 2
    assert np.any(
        np.linalg.norm(footprint - np.asarray((5.0, 0.0)), axis=1) < 1.0e-12
    )


def test_context_conflict_replaces_local_path_without_global_replan() -> None:
    global_path = np.asarray(((0.0, 0.0), (10.0, 0.0)))
    state = FixedGlobalLocalPath.from_global(global_path)
    observation = _context_observation()
    decision = evaluate_context_replan(state.local_path_xy, observation, now_ns=0)
    assert decision.replan
    local = generate_context_local_detour(
        np.asarray((0.0, 0.0)), global_path[-1], observation, side=1
    )
    replaced = FixedGlobalLocalPath(global_path, local, 1)
    np.testing.assert_array_equal(replaced.global_path_xy, global_path)
    assert replaced.local_generation_count == 1
    assert not np.array_equal(replaced.local_path_xy, global_path)


def test_global_path_is_unchanged_when_local_detour_is_generated() -> None:
    global_path = np.asarray([[0.0, 0.0], [10.0, 0.0]])
    planner = FixedGlobalLocalPath.from_global(global_path)
    updated = planner.generate_local_detour(
        np.asarray([3.0, 0.0]), _heading_observation(), side=1, lateral_offset=1.2
    )
    np.testing.assert_array_equal(updated.global_path_xy, global_path)
    assert updated.local_generation_count == 1
    assert len(updated.local_path_xy) == 4
    assert not np.array_equal(updated.local_path_xy, global_path)


def test_direction_change_triggers_local_replan_without_global_replan() -> None:
    global_path = np.asarray([[0.0, 5.0], [10.0, 5.0]])
    observation = _context_observation("forward")
    decision = evaluate_context_replan(
        global_path,
        observation,
        now_ns=0,
        previous_heading_unit=np.asarray((0.0, -1.0)),
        safe_distance_m=0.20,
        heading_change_threshold_rad=0.60,
    )
    assert decision.replan
    assert "direction_change" in decision.reasons
    assert "context_conflict" not in decision.reasons
    planner = FixedGlobalLocalPath.from_global(global_path)
    updated = planner.generate_local_detour(
        np.asarray([0.0, 5.0]), observation, side=1
    )
    np.testing.assert_array_equal(updated.global_path_xy, global_path)
    assert updated.local_generation_count == 1


def test_second_generation_still_reconnects_to_same_global_goal() -> None:
    planner = FixedGlobalLocalPath.from_global(
        np.asarray([[0.0, 0.0], [10.0, 0.0]])
    )
    first = planner.generate_local_detour(
        np.asarray([3.0, 0.0]), _heading_observation(), side=-1
    )
    second = first.generate_local_detour(
        np.asarray([4.0, -0.5]), _heading_observation(), side=1
    )
    np.testing.assert_array_equal(second.global_path_xy[-1], [10.0, 0.0])
    np.testing.assert_array_equal(second.global_path_xy, planner.global_path_xy)
    assert second.local_generation_count == 2


def test_heading_is_causal_and_unit_length() -> None:
    observation = _heading_observation()
    np.testing.assert_allclose(observation.heading_unit, [1.0, 0.0])
    assert observation.heading_valid
    assert observation.speed_per_s == pytest.approx(1.0)


def test_stationary_history_is_explicitly_invalid() -> None:
    observation = estimate_heading_observation(
        np.asarray([[1.0, 1.0], [1.0, 1.0]]),
        np.asarray([0, 100_000_000]),
        track_id=0,
        frame_id="image",
        source_sha256="a" * 64,
        detector_confidence=1.0,
    )
    assert not observation.heading_valid
    np.testing.assert_allclose(observation.heading_unit, [0.0, 0.0])


def test_stale_history_is_invalid() -> None:
    observation = estimate_heading_observation(
        np.asarray([[0.0, 0.0], [1.0, 0.0]]),
        np.asarray([0, 2_000_000_000]),
        track_id=0,
        frame_id="image",
        source_sha256="a" * 64,
        detector_confidence=1.0,
        max_gap_ns=500_000_000,
    )
    assert not observation.heading_valid


def test_astar_reaches_goal_around_obstacle() -> None:
    plan = astar_plan(
        np.asarray((0.5, 0.5)),
        np.asarray((4.0, 0.5)),
        (5.0, 5.0),
        np.asarray(((2.5, 0.5, 0.45, 0.45),)),
        inflation_m=0.20,
        resolution_m=0.25,
    )
    assert plan.status == "ASTAR_SUCCESS"
    assert not plan.fallback_used
    np.testing.assert_allclose(plan.path_xy[0], [0.5, 0.5])
    np.testing.assert_allclose(plan.path_xy[-1], [4.0, 0.5])
    assert float(np.max(np.abs(plan.path_xy[:, 1]))) > 0.6
