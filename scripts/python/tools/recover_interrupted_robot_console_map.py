"""Recover map artifacts from an interrupted robot-console capture.

The console writes raw lidar and state rows incrementally.  If the process is
terminated before its normal shutdown path, those rows can still be replayed
through the existing occupancy mapper to produce the missing map package.
This utility never opens hardware and never sends a velocity command.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from bisect import bisect_right
from pathlib import Path
from typing import Any

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT

from hardware import LidarPoint, LidarScan
from manual_map import EVENT_FIELDS, OccupancyMap, Pose


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_states(path: Path) -> list[tuple[int, float, float, float, str]]:
    states: list[tuple[int, float, float, float, str]] = []
    with path.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            try:
                states.append(
                    (
                        int(row["t_ns"]),
                        float(row["x_m"]),
                        float(row["y_m"]),
                        float(row["yaw_rad"]),
                        str(row.get("transport") or "unknown"),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
    states.sort(key=lambda item: item[0])
    return states


def read_scans(path: Path):
    with path.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            try:
                t_ns = int(row["t_ns"])
                raw_points = json.loads(row["points_json"])
                points = tuple(
                    LidarPoint(t_ns, float(item[0]), float(item[1]), int(item[2]), int(item[3]))
                    for item in raw_points
                    if isinstance(item, list) and len(item) >= 4
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
            yield LidarScan(t_ns, points)


def write_manifest(root: Path, mapper: OccupancyMap, states: list[tuple[int, float, float, float, str]], scan_count: int) -> None:
    files = {
        path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in root.iterdir()
        if path.is_file() and path.name != "manifest.json"
    }
    payload: dict[str, Any] = {
        "schema": "cca-robot-console-capture-v1",
        "run_id": root.name,
        "capture_source": "hardware",
        "status": "recovered",
        "paper_edit": False,
        "devices": {"stm": "STM32", "lidar": "N10P", "camera": "Astra-S"},
        "transport": states[0][4] if states else "unknown",
        "control_interface": "body_velocity",
        "state_definition": ["x_m", "y_m", "theta_rad", "vx_mps", "vy_mps", "omega_radps"],
        "map": {
            "resolution_m": mapper.resolution_m,
            "lidar_mount_m": [mapper.lidar_x_m, mapper.lidar_y_m],
            "scans": mapper.scans,
            "points": mapper.points,
            "scan_matching": mapper.scan_matching_enabled,
            "scan_match_attempts": mapper.scan_match_attempts,
            "scan_match_accepted": mapper.scan_match_accepted,
        },
        "recovery": {"source_scan_rows": scan_count, "source_state_rows": len(states)},
        "files": files,
    }
    (root / "manifest.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def recover(root: Path) -> dict[str, Any]:
    if not root.is_dir():
        raise FileNotFoundError(root)
    required = (root / "lidar.csv", root / "robot_state.csv")
    if any(not path.is_file() for path in required):
        raise FileNotFoundError("recovery requires lidar.csv and robot_state.csv")
    if any((root / name).exists() for name in ("map.json", "map.pgm", "map.yaml", "manifest.json")):
        raise FileExistsError("map artifacts already exist; recovery is limited to incomplete runs")

    states = read_states(root / "robot_state.csv")
    if not states:
        raise ValueError("robot_state.csv contains no valid pose rows")
    state_times = [item[0] for item in states]
    mapper = OccupancyMap(
        0.05,
        lidar_x_m=0.10,
        lidar_y_m=0.0,
        lidar_yaw_rad=0.0,
        min_range_m=0.05,
        max_range_m=8.0,
        padding_cells=5,
    )
    scan_count = 0
    for scan in read_scans(root / "lidar.csv"):
        index = min(max(bisect_right(state_times, scan.t_ns) - 1, 0), len(states) - 1)
        _, x_m, y_m, yaw_rad, _ = states[index]
        mapper.update(scan, Pose(x_m=x_m, y_m=y_m, yaw_rad=yaw_rad))
        scan_count += 1
    if scan_count == 0:
        raise ValueError("lidar.csv contains no valid scan rows")

    summary = mapper.save(root)
    events = root / "events.csv"
    if not events.exists() or events.stat().st_size == 0:
        with events.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=EVENT_FIELDS)
            writer.writeheader()
            writer.writerow(
                {
                    "t_ns": states[-1][0],
                    "event_type": "console_scan_recovered",
                    "solve_ms": "",
                    "status_code": 0,
                    "sequence": 0,
                    "detail": f"scans={mapper.scans}; points={mapper.points}",
                }
            )
    write_manifest(root, mapper, states, scan_count)
    return {**summary, "scan_rows": scan_count, "state_rows": len(states)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        type=Path,
        default=PROJECT_ROOT / "experiments" / "runs" / "console-map-20260820-112602",
        help="incomplete console run directory",
    )
    args = parser.parse_args()
    summary = recover(args.run.resolve())
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
