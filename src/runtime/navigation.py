"""Navigation adapter that feeds an A* global path to the existing controller.

This module intentionally contains no controller equations.  It binds the
occupancy-map A* result to the already-frozen ``FixedGlobalLocalPath``
contract, which is what ``OnlineCcaNmpc`` and the simulation runner consume.
The global path is created once; context handling may replace only the local
path through the existing replanner.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from simulation.context_replanner import FixedGlobalLocalPath
from simulation.occupancy_astar import OccupancyPlanResult, plan_occupancy_map


@dataclass(frozen=True)
class AStarNavigationPlan:
    """A planned global path and its fixed/local controller path state."""

    occupancy_result: OccupancyPlanResult
    path_state: FixedGlobalLocalPath

    @property
    def global_path_xy(self) -> np.ndarray:
        return self.path_state.global_path_xy

    @property
    def local_path_xy(self) -> np.ndarray:
        return self.path_state.local_path_xy

    def controller_map_payload(
        self,
        map_payload: Mapping[str, Any],
        *,
        cca_nmpc: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add the fixed A* path to a map for existing CCA-NMPC entrypoints."""

        payload = deepcopy(dict(map_payload))
        payload["global_path_xy"] = self.global_path_xy.tolist()
        if cca_nmpc is not None:
            payload["cca_nmpc"] = deepcopy(dict(cca_nmpc))
        payload["navigation"] = {
            "planner": "astar",
            "planner_status": self.occupancy_result.status,
            "expanded_nodes": self.occupancy_result.expanded_nodes,
            "inflation_m": self.occupancy_result.inflation_m,
            "resolution_m": self.occupancy_result.resolution_m,
            "global_path_held_fixed": True,
            "local_path_controller": "FixedGlobalLocalPath",
        }
        return payload


def plan_navigation_path(
    map_payload: Mapping[str, Any],
    start_xy: Sequence[Any],
    goal_xy: Sequence[Any],
    *,
    inflation_m: float,
    resolution_m: float | None = None,
    unknown_is_occupied: bool = True,
) -> AStarNavigationPlan:
    """Plan A* once and initialise the existing immutable path structure."""

    result = plan_occupancy_map(
        map_payload,
        start_xy,
        goal_xy,
        inflation_m=inflation_m,
        resolution_m=resolution_m,
        unknown_is_occupied=unknown_is_occupied,
    )
    path_state = FixedGlobalLocalPath.from_global(result.path_xy)
    return AStarNavigationPlan(result, path_state)

