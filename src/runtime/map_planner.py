"""Plan a fixed global path from an occupancy grid.

The project already defines the A* search and its post-processing in
The continuous A* search and occupancy adapter share this module. It translates
payload produced by ``manual_map.OccupancyMap`` into that planner's obstacle
rectangle contract.  No search, cost, neighbour, shortcut, or controller
formula is duplicated here.
"""

from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
from typing import Any, Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

@dataclass(frozen=True)
class PlannerResult:
    path_xy: NDArray[np.float64]
    expanded_nodes: int
    fallback_used: bool
    status: str


def _free(
    point: NDArray[np.float64],
    bounds_xy: tuple[float, float],
    obstacles: NDArray[np.float64],
    inflation_m: float,
) -> bool:
    if np.any(point < inflation_m):
        return False
    if point[0] > bounds_xy[0] - inflation_m:
        return False
    if point[1] > bounds_xy[1] - inflation_m:
        return False
    if obstacles.size == 0:
        return True
    delta = np.abs(point[None] - obstacles[:, :2])
    occupied = (delta[:, 0] <= obstacles[:, 2] + inflation_m) & (
        delta[:, 1] <= obstacles[:, 3] + inflation_m
    )
    return not bool(np.any(occupied))


def _segment_free(
    start: NDArray[np.float64],
    end: NDArray[np.float64],
    bounds_xy: tuple[float, float],
    obstacles: NDArray[np.float64],
    inflation_m: float,
) -> bool:
    count = max(2, int(np.ceil(float(np.linalg.norm(end - start)) / 0.08)) + 1)
    return all(
        _free(start + fraction * (end - start), bounds_xy, obstacles, inflation_m)
        for fraction in np.linspace(0.0, 1.0, count)
    )


def _densify(points: NDArray[np.float64], spacing_m: float = 0.08) -> NDArray[np.float64]:
    output = [points[0]]
    for start, end in zip(points[:-1], points[1:], strict=True):
        count = max(1, int(np.ceil(float(np.linalg.norm(end - start)) / spacing_m)))
        fractions = np.linspace(0.0, 1.0, count + 1)[1:]
        output.extend(start + fraction * (end - start) for fraction in fractions)
    return np.asarray(output, dtype=np.float64)


def _shortcut(
    points: NDArray[np.float64],
    bounds_xy: tuple[float, float],
    obstacles: NDArray[np.float64],
    inflation_m: float,
) -> NDArray[np.float64]:
    if len(points) <= 2:
        return points
    output = [points[0]]
    anchor = 0
    while anchor < len(points) - 1:
        candidate = len(points) - 1
        while candidate > anchor + 1 and not _segment_free(
            points[anchor], points[candidate], bounds_xy, obstacles, inflation_m
        ):
            candidate -= 1
        output.append(points[candidate])
        anchor = candidate
    return _densify(np.asarray(output, dtype=np.float64))


def astar_plan(
    start_xy: NDArray[np.float64],
    goal_xy: NDArray[np.float64],
    bounds_xy: tuple[float, float],
    obstacles: NDArray[np.float64],
    inflation_m: float = 0.42,
    resolution_m: float = 0.20,
) -> PlannerResult:
    obstacles = np.asarray(obstacles, dtype=np.float64).reshape(-1, 4)
    start_point = np.asarray(start_xy, dtype=np.float64)
    goal_point = np.asarray(goal_xy, dtype=np.float64)
    width = int(np.floor(bounds_xy[0] / resolution_m)) + 1
    height = int(np.floor(bounds_xy[1] / resolution_m)) + 1

    def node(point_xy: NDArray[np.float64]) -> tuple[int, int]:
        value = np.rint(point_xy / resolution_m).astype(int)
        return int(np.clip(value[0], 0, width - 1)), int(
            np.clip(value[1], 0, height - 1)
        )

    def point(index: tuple[int, int]) -> NDArray[np.float64]:
        return resolution_m * np.asarray(index, dtype=np.float64)

    start = node(start_point)
    goal = node(goal_point)
    start_free = _free(point(start), bounds_xy, obstacles, inflation_m)
    goal_free = _free(point(goal), bounds_xy, obstacles, inflation_m)
    if not start_free or not goal_free:
        raise ValueError("A* start or goal is occupied after obstacle inflation")
    queue: list[tuple[float, float, tuple[int, int]]] = [(0.0, 0.0, start)]
    costs = {start: 0.0}
    parents: dict[tuple[int, int], tuple[int, int]] = {}
    expanded = 0
    neighbors = tuple(
        (dx, dy)
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        if (dx, dy) != (0, 0)
    )
    while queue:
        _, current_cost, current = heapq.heappop(queue)
        if current_cost > costs[current] + 1.0e-12:
            continue
        expanded += 1
        if current == goal:
            break
        for dx, dy in neighbors:
            neighbor = (current[0] + dx, current[1] + dy)
            if not (0 <= neighbor[0] < width and 0 <= neighbor[1] < height):
                continue
            if not _free(point(neighbor), bounds_xy, obstacles, inflation_m):
                continue
            tentative = current_cost + resolution_m * float(np.hypot(dx, dy))
            if tentative + 1.0e-12 >= costs.get(neighbor, np.inf):
                continue
            costs[neighbor] = tentative
            parents[neighbor] = current
            heuristic = float(np.linalg.norm(point(neighbor) - point(goal)))
            heapq.heappush(queue, (tentative + heuristic, tentative, neighbor))
    if goal not in costs:
        raise RuntimeError("A* failed to find an inflated-obstacle path")
    nodes = [goal]
    while nodes[-1] != start:
        nodes.append(parents[nodes[-1]])
    nodes.reverse()
    path = np.asarray([point(item) for item in nodes], dtype=np.float64)
    path[0] = start_point
    path[-1] = goal_point
    path = _shortcut(path, bounds_xy, obstacles, inflation_m)
    return PlannerResult(path, expanded, False, "ASTAR_SUCCESS")


@dataclass(frozen=True)
class OccupancyPlanResult:
    """A* result plus map-coordinate metadata used by the app/controller."""

    planner: PlannerResult
    start_xy: NDArray[np.float64]
    goal_xy: NDArray[np.float64]
    bounds_xy: tuple[float, float]
    resolution_m: float
    inflation_m: float
    occupied_cells: int
    unknown_cells: int

    @property
    def path_xy(self) -> NDArray[np.float64]:
        """Return the world-frame path generated by the existing A* planner."""

        return self.planner.path_xy

    @property
    def expanded_nodes(self) -> int:
        return int(self.planner.expanded_nodes)

    @property
    def status(self) -> str:
        return self.planner.status

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable navigation-plan payload."""

        return {
            "status": self.planner.status,
            "fallback_used": bool(self.planner.fallback_used),
            "expanded_nodes": int(self.planner.expanded_nodes),
            "path_xy": self.path_xy.tolist(),
            "start_xy": self.start_xy.tolist(),
            "goal_xy": self.goal_xy.tolist(),
            "bounds_xy": [float(value) for value in self.bounds_xy],
            "resolution_m": float(self.resolution_m),
            "inflation_m": float(self.inflation_m),
            "occupied_cells": int(self.occupied_cells),
            "unknown_cells": int(self.unknown_cells),
        }


def _finite_pair(value: Sequence[Any], name: str) -> NDArray[np.float64]:
    try:
        length = len(value)
    except TypeError as error:
        raise ValueError(f"{name} must contain two finite coordinates") from error
    if isinstance(value, (str, bytes)) or length < 2:
        raise ValueError(f"{name} must contain two finite coordinates")
    try:
        result = np.asarray((float(value[0]), float(value[1])), dtype=np.float64)
    except (TypeError, ValueError, IndexError) as error:
        raise ValueError(f"{name} must contain two finite coordinates") from error
    if result.shape != (2,) or not np.isfinite(result).all():
        raise ValueError(f"{name} must contain two finite coordinates")
    return result


def _map_geometry(
    payload: Mapping[str, Any],
) -> tuple[int, int, float, NDArray[np.float64], list[Any]]:
    try:
        width = int(payload["width"])
        height = int(payload["height"])
        resolution = float(payload["resolution_m"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("occupancy map requires integer width/height and resolution_m") from error
    if width < 2 or height < 2 or not math.isfinite(resolution) or resolution <= 0.0:
        raise ValueError("occupancy map dimensions and resolution_m must be positive")
    origin = _finite_pair(payload.get("origin", (0.0, 0.0)), "map origin")
    occupancy = payload.get("occupancy")
    if not isinstance(occupancy, list) or len(occupancy) < width * height:
        raise ValueError("occupancy map must contain width*height cells")
    return width, height, resolution, origin, occupancy


def occupancy_obstacles(
    payload: Mapping[str, Any],
    *,
    unknown_is_occupied: bool = True,
) -> tuple[NDArray[np.float64], int, int]:
    """Convert a map payload to the existing planner's rectangle contract.

    Each occupied/unknown cell is represented by its centre and half-cell
    extents.  Unknown space is treated as occupied by default so a route is
    never inferred through an unobserved area.
    """

    width, height, resolution, origin, occupancy = _map_geometry(payload)
    obstacles: list[tuple[float, float, float, float]] = []
    occupied_cells = 0
    unknown_cells = 0
    half = 0.5 * resolution
    for index, value in enumerate(occupancy[: width * height]):
        try:
            cell_value = int(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"occupancy cell {index} is not numeric") from error
        if cell_value == 100 or (cell_value == -1 and unknown_is_occupied):
            cell_x = index % width
            cell_y = index // width
            obstacles.append(
                (
                    float(origin[0] + (cell_x + 0.5) * resolution),
                    float(origin[1] + (cell_y + 0.5) * resolution),
                    half,
                    half,
                )
            )
            if cell_value == 100:
                occupied_cells += 1
            else:
                unknown_cells += 1
        elif cell_value == -1:
            unknown_cells += 1
        elif cell_value != 0:
            raise ValueError(f"occupancy cell {index} must be -1, 0, or 100")
    return np.asarray(obstacles, dtype=np.float64).reshape(-1, 4), occupied_cells, unknown_cells


def plan_occupancy_map(
    payload: Mapping[str, Any],
    start_xy: Sequence[Any],
    goal_xy: Sequence[Any],
    *,
    inflation_m: float,
    resolution_m: float | None = None,
    unknown_is_occupied: bool = True,
) -> OccupancyPlanResult:
    """Plan a world-frame route from an occupancy-map payload with A*.

    The existing ``astar_plan`` works in a local frame whose lower corner is
    ``(0, 0)``.  We subtract the map origin before calling it and add the
    origin back to the returned path.  This keeps its implementation and all
    controller-side path semantics unchanged.
    """

    width, height, map_resolution, origin, _ = _map_geometry(payload)
    if resolution_m is None:
        search_resolution = map_resolution
    else:
        search_resolution = float(resolution_m)
        if not math.isfinite(search_resolution) or search_resolution <= 0.0:
            raise ValueError("resolution_m must be positive and finite")
    inflation = float(inflation_m)
    if not math.isfinite(inflation) or inflation < 0.0:
        raise ValueError("inflation_m must be finite and nonnegative")
    start = _finite_pair(start_xy, "start_xy")
    goal = _finite_pair(goal_xy, "goal_xy")
    if float(np.linalg.norm(goal - start)) <= 1.0e-12:
        raise ValueError("start_xy and goal_xy must be distinct")
    obstacles, occupied_cells, unknown_cells = occupancy_obstacles(
        payload,
        unknown_is_occupied=unknown_is_occupied,
    )
    bounds = (float(width * map_resolution), float(height * map_resolution))
    local_start = start - origin
    local_goal = goal - origin
    local_result = astar_plan(
        local_start,
        local_goal,
        bounds,
        obstacles - np.asarray((origin[0], origin[1], 0.0, 0.0), dtype=np.float64)
        if obstacles.size
        else obstacles,
        inflation_m=inflation,
        resolution_m=search_resolution,
    )
    path = np.asarray(local_result.path_xy, dtype=np.float64) + origin[None, :]
    planner = PlannerResult(
        path_xy=path,
        expanded_nodes=local_result.expanded_nodes,
        fallback_used=local_result.fallback_used,
        status=local_result.status,
    )
    return OccupancyPlanResult(
        planner=planner,
        start_xy=start.copy(),
        goal_xy=goal.copy(),
        bounds_xy=bounds,
        resolution_m=search_resolution,
        inflation_m=inflation,
        occupied_cells=occupied_cells,
        unknown_cells=unknown_cells,
    )
