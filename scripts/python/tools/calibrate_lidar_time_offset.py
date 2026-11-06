"""Estimate the N10P receive-time offset against a stationary scan reference."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from app.backend.robot_console import load_robot_geometry
from app.backend.slam import OccupancyMap
from hardware import LidarPoint, LidarScan


def load_run(root: Path):
    with (root / "robot_state.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    rows = sorted({int(row["t_ns"]): row for row in rows}.values(), key=lambda row: int(row["t_ns"]))
    poses = tuple((int(row["t_ns"]), float(row["x_m"]), float(row["y_m"]), float(row["yaw_rad"])) for row in rows)
    twist = [(math.hypot(float(row["vx_mps"]), float(row["vy_mps"])),
              abs(float(row["wz_radps"]))) for row in rows]
    history = {}
    with (root / "map_history.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            entry = json.loads(line)
            history[entry["t_ns"]] = entry
    scans = []
    with (root / "lidar.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            ts = int(row["t_ns"])
            entry = history.get(ts, {})
            points = json.loads(row["points_json"])
            offsets = entry.get("lidar_point_offsets_ns")
            if offsets is not None and len(points) == len(offsets):
                scans.append(LidarScan(ts, tuple(LidarPoint(ts + dt, *point) for dt, point in zip(offsets, points)),
                                       entry.get("lidar_period_ns")))
    if len(poses) < 10 or len(scans) < 10:
        raise ValueError(f"{root}: need a capture with point timing and at least 10 scans and odometry samples")
    return poses, twist, scans


def evaluate(root: Path, offsets_ms: list[float]) -> list[dict[str, float | int]]:
    poses, twist, scans = load_run(root)
    origin = poses[0][0]
    times = np.asarray([row[0] - origin for row in poses], dtype=float)
    xy_yaw = np.asarray([row[1:] for row in poses])
    xy_yaw[:, 2] = np.unwrap(xy_yaw[:, 2])
    geometry = load_robot_geometry()
    mapper = OccupancyMap(0.025, lidar_x_m=geometry["lidar_position_x_m"], lidar_y_m=0,
                          lidar_yaw_rad=0, min_range_m=0.05, max_range_m=8, padding_cells=5)

    def world_points(scan: LidarScan) -> np.ndarray | None:
        stamp = mapper.scan_reference_ns(scan) - origin
        start = max(0, int(np.searchsorted(times, stamp - 200_000_000)) - 1)
        end = int(np.searchsorted(times, stamp, side="right")) + 1
        points = mapper._scan_points(scan)
        rays = mapper._deskew_rays(scan, points, poses[start:end])
        if rays is None:
            return None
        x, y, yaw = (np.interp(stamp, times, xy_yaw[:, k]) for k in range(3))
        ex, ey = np.asarray(rays)[:, 2:].T
        c, s = math.cos(yaw), math.sin(yaw)
        return np.column_stack((x + c*ex - s*ey, y + s*ex + c*ey))

    first_turn = next((i for i, (_, yaw) in enumerate(twist) if yaw >= 0.2), None)
    if first_turn is None:
        raise ValueError(f"{root}: no turn above 0.2 rad/s")
    rotation_start = poses[first_turn][0]
    stationary = []
    rotating = []
    span = max(abs(value) for value in offsets_ms) * 1e6
    for scan in scans:
        if scan.t_ns - (scan.period_ns or 100_000_000) - span < origin or scan.t_ns + span > poses[-1][0]:
            continue
        idx = min(len(poses)-1, int(np.searchsorted(times, scan.t_ns-origin)))
        speed, yaw = twist[idx]
        if scan.t_ns < rotation_start - 200_000_000 and speed <= 0.04 and yaw < 0.05:
            points = world_points(scan)
            if points is not None:
                stationary.append(points)
        elif speed <= 0.08 and yaw >= 0.2:
            rotating.append(scan)
    if len(stationary) < 3 or len(rotating) < 8:
        raise ValueError(f"{root}: record at least 3 stationary scans before at least 8 turning scans")
    tree = cKDTree(np.concatenate(stationary[-8:]))
    selected = rotating[::max(1, math.ceil(len(rotating) / 80))]
    result = []
    for offset in offsets_ms:
        mapper.lidar_time_offset_ns = round(offset * 1e6)
        errors = []
        for scan in selected:
            points = world_points(scan)
            if points is None:
                raise ValueError(f"{root}: odometry or scan coverage is insufficient for offset {offset} ms")
            distances, _ = tree.query(points)
            errors.append(float(np.minimum(distances, 0.30).mean()))
        result.append({"offset_ms": offset, "mean_clipped_distance_m": float(np.mean(errors)), "scans": len(errors)})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--validation", type=Path, required=True, help="Independent stationary-then-turn run")
    parser.add_argument("--max-offset-ms", type=int, default=80)
    parser.add_argument("--step-ms", type=int, default=5)
    args = parser.parse_args()
    if not (1 <= args.step_ms <= args.max_offset_ms <= 200):
        parser.error("require 1 <= step-ms <= max-offset-ms <= 200")
    if args.run.resolve() == args.validation.resolve():
        parser.error("validation must use an independent run")
    offsets = sorted({0, *range(-args.max_offset_ms, args.max_offset_ms+1, args.step_ms)})
    try:
        calibration = evaluate(args.run, offsets)
        best = min(calibration, key=lambda row: (row["mean_clipped_distance_m"], abs(row["offset_ms"])))
        validation = evaluate(args.validation, sorted({0, best["offset_ms"]}))
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    print(json.dumps({"best": best, "calibration": calibration, "validation": validation}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
