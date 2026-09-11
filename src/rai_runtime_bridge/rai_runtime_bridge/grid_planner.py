"""Small, deterministic A* planner for the runtime occupancy-grid contract.

The bridge receives maps as the same base64-encoded occupancy grid that the
dashboard displays.  Keeping the planner here means a navigation goal uses the
selected saved map or the live SLAM map, rather than an unrelated planner
process with a different map lifecycle.
"""

from __future__ import annotations

import base64
import heapq
import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GridPath:
    """A world-coordinate path and the cells used for its endpoints."""

    points: tuple[tuple[float, float], ...]
    length_m: float
    start_cell: tuple[int, int]
    goal_cell: tuple[int, int]


_NEIGHBOURS: tuple[tuple[int, int, float], ...] = (
    (-1, -1, math.sqrt(2.0)),
    (-1, 0, 1.0),
    (-1, 1, math.sqrt(2.0)),
    (0, -1, 1.0),
    (0, 1, 1.0),
    (1, -1, math.sqrt(2.0)),
    (1, 0, 1.0),
    (1, 1, math.sqrt(2.0)),
)


def _grid_data(snapshot: dict[str, Any]) -> tuple[int, int, float, float, float, float, list[int]]:
    width = int(snapshot.get("width", 0))
    height = int(snapshot.get("height", 0))
    resolution = float(snapshot.get("resolution", 0.0))
    origin_x = float(snapshot.get("origin_x", 0.0))
    origin_y = float(snapshot.get("origin_y", 0.0))
    origin_yaw = float(snapshot.get("origin_yaw", 0.0))
    if width <= 0 or height <= 0 or not math.isfinite(resolution) or resolution <= 0.0:
        raise ValueError("occupancy map dimensions or resolution are invalid")

    encoded = snapshot.get("grid_data", "")
    try:
        raw = base64.b64decode(str(encoded), validate=True)
    except Exception as error:
        raise ValueError("occupancy map payload is not valid base64") from error
    expected = width * height
    if len(raw) < expected:
        raise ValueError("occupancy map payload is truncated")
    return width, height, resolution, origin_x, origin_y, origin_yaw, list(raw[:expected])


def _world_to_cell(
    x: float,
    y: float,
    resolution: float,
    origin_x: float,
    origin_y: float,
    origin_yaw: float,
) -> tuple[int, int]:
    dx = x - origin_x
    dy = y - origin_y
    c = math.cos(origin_yaw)
    s = math.sin(origin_yaw)
    local_x = c * dx + s * dy
    local_y = -s * dx + c * dy
    return math.floor(local_x / resolution), math.floor(local_y / resolution)


def _cell_to_world(
    cell: tuple[int, int],
    resolution: float,
    origin_x: float,
    origin_y: float,
    origin_yaw: float,
) -> tuple[float, float]:
    local_x = (cell[0] + 0.5) * resolution
    local_y = (cell[1] + 0.5) * resolution
    c = math.cos(origin_yaw)
    s = math.sin(origin_yaw)
    return origin_x + c * local_x - s * local_y, origin_y + s * local_x + c * local_y


def _in_bounds(cell: tuple[int, int], width: int, height: int) -> bool:
    return 0 <= cell[0] < width and 0 <= cell[1] < height


def _index(cell: tuple[int, int], width: int) -> int:
    return cell[1] * width + cell[0]


def _inflated_blocked(
    values: list[int],
    width: int,
    height: int,
    radius_cells: int,
) -> set[int]:
    # Unknown cells are treated as occupied: a goal must never be sent through
    # map space that SLAM has not observed yet.
    blocked = {
        index for index, value in enumerate(values) if value < 0 or value >= 65
    }
    if radius_cells <= 0:
        return blocked

    # Keep unknown cells fail-closed, but do not dilate every unknown cell.
    # Live SLAM maps are mostly unknown outside the explored room; expanding
    # that whole region would turn a small goal request into an O(N*r^2)
    # operation without changing which cells are traversable.
    occupied = {
        index for index, value in enumerate(values) if 65 <= value < 255
    }
    if not occupied:
        return blocked

    offsets = [
        (dx, dy)
        for dy in range(-radius_cells, radius_cells + 1)
        for dx in range(-radius_cells, radius_cells + 1)
        if dx * dx + dy * dy <= radius_cells * radius_cells
    ]
    inflated = set(blocked)
    for obstacle in occupied:
        ox = obstacle % width
        oy = obstacle // width
        for dx, dy in offsets:
            cell = (ox + dx, oy + dy)
            if _in_bounds(cell, width, height):
                inflated.add(_index(cell, width))
    return inflated


def _nearest_free(
    requested: tuple[int, int],
    blocked: set[int],
    width: int,
    height: int,
    max_radius_cells: int,
) -> tuple[int, int]:
    if _in_bounds(requested, width, height) and _index(requested, width) not in blocked:
        return requested
    queue: list[tuple[int, int, int]] = [(0, requested[0], requested[1])]
    visited = {requested}
    while queue:
        distance, x, y = heapq.heappop(queue)
        if distance > max_radius_cells:
            continue
        cell = (x, y)
        if _in_bounds(cell, width, height) and _index(cell, width) not in blocked:
            return cell
        if distance == max_radius_cells:
            continue
        for dx, dy, _ in _NEIGHBOURS:
            neighbour = (x + dx, y + dy)
            if neighbour in visited:
                continue
            visited.add(neighbour)
            heapq.heappush(queue, (distance + 1, neighbour[0], neighbour[1]))
    raise ValueError("start or goal is occupied/outside the known free map")


def _heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _astar(
    start: tuple[int, int],
    goal: tuple[int, int],
    blocked: set[int],
    width: int,
    height: int,
) -> list[tuple[int, int]]:
    if start == goal:
        return [start]
    open_set: list[tuple[float, float, int, int]] = [
        (_heuristic(start, goal), 0.0, start[0], start[1])
    ]
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    cost_so_far = {start: 0.0}
    while open_set:
        _, cost, x, y = heapq.heappop(open_set)
        current = (x, y)
        if cost > cost_so_far.get(current, math.inf) + 1.0e-9:
            continue
        if current == goal:
            path = [current]
            while path[-1] != start:
                path.append(came_from[path[-1]])
            path.reverse()
            return path
        for dx, dy, step_cost in _NEIGHBOURS:
            neighbour = (x + dx, y + dy)
            if not _in_bounds(neighbour, width, height):
                continue
            if _index(neighbour, width) in blocked:
                continue
            # Do not cut diagonally through two inflated obstacle corners.
            if dx and dy:
                if (
                    _index((x + dx, y), width) in blocked
                    or _index((x, y + dy), width) in blocked
                ):
                    continue
            new_cost = cost + step_cost
            if new_cost >= cost_so_far.get(neighbour, math.inf):
                continue
            came_from[neighbour] = current
            cost_so_far[neighbour] = new_cost
            heapq.heappush(
                open_set,
                (
                    new_cost + _heuristic(neighbour, goal),
                    new_cost,
                    neighbour[0],
                    neighbour[1],
                ),
            )
    raise ValueError("A* could not find a collision-free path")


def _simplify(path: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if len(path) < 3:
        return path
    simplified = [path[0]]
    previous_dx = path[1][0] - path[0][0]
    previous_dy = path[1][1] - path[0][1]
    for index in range(1, len(path) - 1):
        dx = path[index + 1][0] - path[index][0]
        dy = path[index + 1][1] - path[index][1]
        if (dx, dy) != (previous_dx, previous_dy):
            simplified.append(path[index])
            previous_dx, previous_dy = dx, dy
    simplified.append(path[-1])
    return simplified


def plan_occupancy_path(
    snapshot: dict[str, Any],
    start: tuple[float, float],
    goal: tuple[float, float],
    *,
    inflation_m: float,
    max_snap_m: float,
) -> GridPath:
    """Plan the shortest safe 8-connected path in a ROS occupancy grid."""
    if not all(math.isfinite(value) for value in (*start, *goal)):
        raise ValueError("start and goal must be finite")
    if inflation_m < 0.0 or max_snap_m < 0.0:
        raise ValueError("planner distances must be non-negative")

    width, height, resolution, origin_x, origin_y, origin_yaw, values = _grid_data(snapshot)
    blocked = _inflated_blocked(
        values,
        width,
        height,
        int(math.ceil(inflation_m / resolution)),
    )
    start_cell = _world_to_cell(start[0], start[1], resolution, origin_x, origin_y, origin_yaw)
    goal_cell = _world_to_cell(goal[0], goal[1], resolution, origin_x, origin_y, origin_yaw)
    snap_cells = max(0, int(math.ceil(max_snap_m / resolution)))
    start_cell = _nearest_free(start_cell, blocked, width, height, snap_cells)
    goal_cell = _nearest_free(goal_cell, blocked, width, height, snap_cells)
    cells = _simplify(_astar(start_cell, goal_cell, blocked, width, height))
    points = tuple(
        _cell_to_world(cell, resolution, origin_x, origin_y, origin_yaw) for cell in cells
    )
    length_m = sum(
        math.hypot(points[index + 1][0] - points[index][0], points[index + 1][1] - points[index][1])
        for index in range(len(points) - 1)
    )
    return GridPath(points, length_m, start_cell, goal_cell)
