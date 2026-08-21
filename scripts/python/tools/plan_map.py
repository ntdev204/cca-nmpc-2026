"""Create a controller-ready map by planning an A* global path.

The command only plans and writes JSON.  It never opens a sensor or sends a
motion command.  The resulting ``global_path_xy`` is accepted by the existing
``record_hardware.py --controller cca_nmpc`` path, whose safety and actuation
gates remain unchanged.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT

from runtime.navigation import plan_navigation_path
from shared import load_contract


def _pair(values: list[str], name: str) -> tuple[float, float]:
    if len(values) != 2:
        raise ValueError(f"{name} requires two numbers")
    try:
        pair = (float(values[0]), float(values[1]))
    except ValueError as error:
        raise ValueError(f"{name} requires two numbers") from error
    if not all(math.isfinite(value) for value in pair):
        raise ValueError(f"{name} requires two finite numbers")
    return pair


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object required: {path}")
    return payload


def _controller_settings(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = _load_json(path)
    settings = payload.get("cca_nmpc", payload)
    if not isinstance(settings, dict):
        raise ValueError("CCA settings JSON must be an object")
    return settings


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Plan an A* global path on a saved occupancy map")
    result.add_argument("--map", dest="map_path", type=Path, required=True, help="saved map.json")
    result.add_argument("--start", nargs=2, metavar=("X", "Y"), required=True)
    result.add_argument("--goal", nargs=2, metavar=("X", "Y"), required=True)
    result.add_argument(
        "--output", type=Path, required=True, help="controller-ready navigation map JSON"
    )
    result.add_argument("--inflation-m", type=float)
    result.add_argument("--resolution-m", type=float)
    result.add_argument(
        "--cca-settings", type=Path, help="JSON object for existing cca_nmpc settings"
    )
    result.add_argument(
        "--unknown-free",
        action="store_true",
        help="allow A* to traverse unknown cells (default is fail-closed)",
    )
    return result


def main() -> int:
    args = parser().parse_args()
    contract = load_contract()
    default_inflation = float(contract["map"]["robot_radius_m"])
    inflation = default_inflation if args.inflation_m is None else float(args.inflation_m)
    source = _load_json(args.map_path.resolve())
    start = _pair(args.start, "--start")
    goal = _pair(args.goal, "--goal")
    planned = plan_navigation_path(
        source,
        start,
        goal,
        inflation_m=inflation,
        resolution_m=args.resolution_m,
        unknown_is_occupied=not args.unknown_free,
    )
    settings = _controller_settings(args.cca_settings.resolve() if args.cca_settings else None)
    if settings is None and isinstance(source.get("cca_nmpc"), dict):
        settings = source["cca_nmpc"]
    output = planned.controller_map_payload(source, cca_nmpc=settings)
    resolved_map = args.map_path.resolve()
    output["navigation"]["source_map"] = (
        resolved_map.relative_to(PROJECT_ROOT).as_posix()
        if resolved_map.is_relative_to(PROJECT_ROOT)
        else resolved_map.as_posix()
    )
    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(
        f"A* plan written: {output_path} "
        f"({len(planned.global_path_xy)} points, "
        f"expanded {planned.occupancy_result.expanded_nodes})"
    )
    if settings is None:
        print(
            "Note: add --cca-settings before using this JSON with "
            "record_hardware.py --controller cca_nmpc"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
