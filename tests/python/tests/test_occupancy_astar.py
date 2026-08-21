from __future__ import annotations

import numpy as np
import pytest

from simulation.occupancy_astar import occupancy_obstacles, plan_occupancy_map


def _map_payload() -> dict[str, object]:
    width, height = 30, 20
    occupancy = [0] * (width * height)
    # A wall in world x=0, with a free opening only near the top of the map.
    for cell_y in range(2, 17):
        occupancy[cell_y * width + 15] = 100
    return {
        "width": width,
        "height": height,
        "resolution_m": 0.2,
        "origin": [-3.0, -2.0, 0.0],
        "occupancy": occupancy,
    }


def test_occupancy_astar_keeps_world_coordinates_and_routes_around_wall() -> None:
    result = plan_occupancy_map(
        _map_payload(),
        (-2.0, 0.0),
        (1.0, 0.0),
        inflation_m=0.10,
    )
    assert result.planner.status == "ASTAR_SUCCESS"
    np.testing.assert_allclose(result.path_xy[0], [-2.0, 0.0])
    np.testing.assert_allclose(result.path_xy[-1], [1.0, 0.0])
    assert result.expanded_nodes > 0
    assert float(np.max(np.abs(result.path_xy[:, 1]))) > 1.0
    assert result.occupied_cells == 15


def test_unknown_space_is_fail_closed_by_default() -> None:
    payload = _map_payload()
    payload["occupancy"] = [0] * (30 * 20)
    payload["occupancy"][10 * 30 + 15] = -1
    # The start is the centre of the unknown cell; fail-closed planning must
    # reject it before attempting to drive through unobserved space.
    with pytest.raises(ValueError, match="start or goal is occupied"):
        plan_occupancy_map(payload, (0.1, 0.1), (0.4, 0.1), inflation_m=0.05)


def test_unknown_space_can_be_excluded_explicitly() -> None:
    payload = _map_payload()
    payload["occupancy"] = [0] * (30 * 20)
    payload["occupancy"][10 * 30 + 15] = -1
    obstacles, occupied, unknown = occupancy_obstacles(payload, unknown_is_occupied=False)
    assert obstacles.shape == (0, 4)
    assert occupied == 0
    assert unknown == 1
    result = plan_occupancy_map(
        payload,
        (-2.0, 0.0),
        (1.0, 0.0),
        inflation_m=0.0,
        unknown_is_occupied=False,
    )
    assert result.planner.status == "ASTAR_SUCCESS"
