from __future__ import annotations

import heapq
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class PlannerResult:
    path_xy: NDArray[np.float64]
    expanded_nodes: int
    fallback_used: bool
    status: str


def _free(point: NDArray[np.float64], bounds_xy: tuple[float, float], obstacles: NDArray[np.float64], inflation_m: float) -> bool:
    if np.any(point < inflation_m) or point[0] > bounds_xy[0] - inflation_m or point[1] > bounds_xy[1] - inflation_m:
        return False
    if obstacles.size == 0:
        return True
    delta = np.abs(point[None] - obstacles[:, :2])
    return not bool(np.any((delta[:, 0] <= obstacles[:, 2] + inflation_m) & (delta[:, 1] <= obstacles[:, 3] + inflation_m)))


def _segment_free(start: NDArray[np.float64], end: NDArray[np.float64], bounds_xy: tuple[float, float], obstacles: NDArray[np.float64], inflation_m: float) -> bool:
    count = max(2, int(np.ceil(float(np.linalg.norm(end - start)) / 0.08)) + 1)
    return all(_free(start + fraction * (end - start), bounds_xy, obstacles, inflation_m) for fraction in np.linspace(0.0, 1.0, count))


def _densify(points: NDArray[np.float64], spacing_m: float = 0.08) -> NDArray[np.float64]:
    output = [points[0]]
    for start, end in zip(points[:-1], points[1:], strict=True):
        count = max(1, int(np.ceil(float(np.linalg.norm(end - start)) / spacing_m)))
        output.extend(start + fraction * (end - start) for fraction in np.linspace(0.0, 1.0, count + 1)[1:])
    return np.asarray(output, dtype=np.float64)


def _shortcut(points: NDArray[np.float64], bounds_xy: tuple[float, float], obstacles: NDArray[np.float64], inflation_m: float) -> NDArray[np.float64]:
    if len(points) <= 2:
        return points
    output = [points[0]]
    anchor = 0
    while anchor < len(points) - 1:
        candidate = len(points) - 1
        while candidate > anchor + 1 and not _segment_free(points[anchor], points[candidate], bounds_xy, obstacles, inflation_m):
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

    def node(point: NDArray[np.float64]) -> tuple[int, int]:
        value = np.rint(point / resolution_m).astype(int)
        return int(np.clip(value[0], 0, width - 1)), int(np.clip(value[1], 0, height - 1))

    def point(index: tuple[int, int]) -> NDArray[np.float64]:
        return resolution_m * np.asarray(index, dtype=np.float64)

    start = node(start_point)
    goal = node(goal_point)
    if not _free(point(start), bounds_xy, obstacles, inflation_m) or not _free(point(goal), bounds_xy, obstacles, inflation_m):
        raise ValueError("A* start or goal is occupied after obstacle inflation")
    queue: list[tuple[float, float, tuple[int, int]]] = [(0.0, 0.0, start)]
    costs = {start: 0.0}
    parents: dict[tuple[int, int], tuple[int, int]] = {}
    expanded = 0
    neighbors = tuple((dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0))
    while queue:
        _, current_cost, current = heapq.heappop(queue)
        if current_cost > costs[current] + 1.0e-12:
            continue
        expanded += 1
        if current == goal:
            break
        for dx, dy in neighbors:
            neighbor = (current[0] + dx, current[1] + dy)
            if not (0 <= neighbor[0] < width and 0 <= neighbor[1] < height) or not _free(point(neighbor), bounds_xy, obstacles, inflation_m):
                continue
            tentative = current_cost + resolution_m * float(np.hypot(dx, dy))
            if tentative + 1.0e-12 >= costs.get(neighbor, np.inf):
                continue
            costs[neighbor] = tentative
            parents[neighbor] = current
            heapq.heappush(queue, (tentative + float(np.linalg.norm(point(neighbor) - point(goal))), tentative, neighbor))
    if goal not in costs:
        raise RuntimeError("A* failed to find an inflated-obstacle path")
    nodes = [goal]
    while nodes[-1] != start:
        nodes.append(parents[nodes[-1]])
    nodes.reverse()
    path = np.asarray([point(item) for item in nodes], dtype=np.float64)
    path[0] = start_point
    path[-1] = goal_point
    return PlannerResult(_shortcut(path, bounds_xy, obstacles, inflation_m), expanded, False, "ASTAR_SUCCESS")
