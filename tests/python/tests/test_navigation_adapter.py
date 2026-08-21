from __future__ import annotations

import numpy as np

from runtime.navigation import plan_navigation_path


def test_astar_navigation_initialises_fixed_global_path_for_controller() -> None:
    payload = {
        "frame_id": "map",
        "width": 16,
        "height": 16,
        "resolution_m": 0.25,
        "origin": [-2.0, -2.0, 0.0],
        "occupancy": [0] * (16 * 16),
        "metadata": {"scans": 1, "points": 1},
    }
    navigation = plan_navigation_path(
        payload,
        (-1.5, -1.5),
        (1.0, 1.0),
        inflation_m=0.10,
    )
    assert navigation.path_state.local_generation_count == 0
    np.testing.assert_array_equal(navigation.global_path_xy, navigation.local_path_xy)
    controller_map = navigation.controller_map_payload(
        payload,
        cca_nmpc={"horizon": 6, "cruise_speed_mps": 0.2},
    )
    assert controller_map["global_path_xy"] == navigation.global_path_xy.tolist()
    assert controller_map["navigation"]["global_path_held_fixed"] is True
    assert controller_map["cca_nmpc"]["horizon"] == 6
    assert "global_path_xy" not in payload

