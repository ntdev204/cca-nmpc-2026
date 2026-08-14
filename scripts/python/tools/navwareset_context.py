from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT


ROOT = PROJECT_ROOT


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_rows(path: Path, track_index: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if track_index not in range(1, 6):
        raise ValueError("track-index must be in [1,5]")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"timestamp", "robot_x", "robot_y", "robot_yaw_rad"}
        required.update({f"x{track_index}", f"y{track_index}"})
        missing = sorted(required - set(reader.fieldnames or ()))
        if missing:
            raise ValueError(f"input CSV is missing columns: {', '.join(missing)}")
        timestamps: list[int] = []
        robot: list[tuple[float, float, float]] = []
        person: list[tuple[float, float]] = []
        for line, row in enumerate(reader, start=2):
            try:
                timestamp = int(row["timestamp"])
                values = tuple(
                    float(row[name])
                    for name in ("robot_x", "robot_y", "robot_yaw_rad", f"x{track_index}", f"y{track_index}")
                )
            except (TypeError, ValueError) as error:
                raise ValueError(f"input CSV row {line} contains invalid numeric data") from error
            if timestamps and timestamp <= timestamps[-1]:
                raise ValueError(f"input CSV timestamps are not strictly increasing at row {line}")
            if not np.isfinite(values).all():
                raise ValueError(f"input CSV row {line} contains non-finite values")
            timestamps.append(timestamp)
            robot.append(values[:3])
            person.append(values[3:])
    if len(timestamps) < 64:
        raise ValueError("input CSV is too short for a context sequence")
    return (
        np.asarray(timestamps, dtype=np.int64),
        np.asarray(robot, dtype=np.float64),
        np.asarray(person, dtype=np.float64),
        np.arange(len(timestamps), dtype=np.int64),
    )


def to_robot_frame(robot: np.ndarray, person: np.ndarray) -> np.ndarray:
    delta = person - robot[:, :2]
    cosine = np.cos(robot[:, 2])
    sine = np.sin(robot[:, 2])
    return np.column_stack((cosine * delta[:, 0] + sine * delta[:, 1], -sine * delta[:, 0] + cosine * delta[:, 1]))


def direction(vector: np.ndarray, speed: float) -> str:
    if speed < 0.02:
        return "unknown"
    if abs(float(vector[0])) >= abs(float(vector[1])):
        return "right" if vector[0] >= 0.0 else "left"
    return "forward" if vector[1] >= 0.0 else "backward"


def write_context(
    output: Path,
    timestamps: np.ndarray,
    local_position: np.ndarray,
    track_index: int,
    source_id: str,
    recording_id: str,
    scene_id: str,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    seconds = (timestamps - timestamps[0]).astype(np.float64) * 1.0e-9
    velocity = np.column_stack(
        (
            np.gradient(local_position[:, 0], seconds, edge_order=1),
            np.gradient(local_position[:, 1], seconds, edge_order=1),
        )
    )
    speed = np.linalg.norm(velocity, axis=1)
    with output.open("w", encoding="utf-8", newline="") as stream:
        fields = (
            "t_ns",
            "position_x_m",
            "position_y_m",
            "speed_mps",
            "direction",
            "confidence",
            "context_valid",
            "recording_id",
            "episode_id",
            "source_id",
            "scene_id",
            "track_id",
            "frame_id",
            "split",
            "real_media",
            "image_to_local_transform_verified",
        )
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for index, (timestamp, position, vector, magnitude) in enumerate(
            zip(timestamps, local_position, velocity, speed, strict=True)
        ):
            writer.writerow(
                {
                    "t_ns": int(timestamp),
                    "position_x_m": f"{position[0]:.9f}",
                    "position_y_m": f"{position[1]:.9f}",
                    "speed_mps": f"{magnitude:.9f}",
                    "direction": direction(vector, float(magnitude)),
                    "confidence": "1.0",
                    "context_valid": "true",
                    "recording_id": recording_id,
                    "episode_id": f"{recording_id}-track-{track_index}",
                    "source_id": source_id,
                    "scene_id": scene_id,
                    "track_id": f"participant-{track_index}",
                    "frame_id": int(index),
                    "split": "",
                    "real_media": "false",
                    "image_to_local_transform_verified": "false",
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert one real NavWareSet participant track to CCA context CSV")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--track-index", type=int, default=1)
    parser.add_argument("--source-id", default="navwareset-tutorial-scene-13")
    parser.add_argument("--recording-id", default="navwareset-scene-13")
    parser.add_argument("--scene-id", default="scene-13")
    args = parser.parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    if not input_path.is_file():
        parser.error(f"input CSV not found: {input_path}")
    if output_path.exists():
        parser.error(f"output already exists: {output_path}")
    timestamps, robot, person, _ = read_rows(input_path, args.track_index)
    local_position = to_robot_frame(robot, person)
    write_context(
        output_path,
        timestamps,
        local_position,
        args.track_index,
        args.source_id,
        args.recording_id,
        args.scene_id,
    )
    sidecar = output_path.with_suffix(".provenance.json")
    payload = {
        "schema": "cca-context-derived-candidate-v1",
        "status": "candidate-not-evidence",
        "source_dataset": "NavWareSet",
        "source_url": "https://anr-navware.github.io/navwareset/",
        "source_repository": "https://github.com/anr-navware/NavWareSet-Tutorials",
        "source_license": "CC BY-SA 4.0",
        "source_file": input_path.as_posix(),
        "source_file_sha256": sha256_file(input_path),
        "derived_context_csv": output_path.as_posix(),
        "derived_context_sha256": sha256_file(output_path),
        "conversion_code": "scripts/python/tools/navwareset_context.py",
        "conversion_code_sha256": sha256_file(Path(__file__).resolve()),
        "track_index": args.track_index,
        "row_count": int(len(timestamps)),
        "coordinate_frame": "robot_local_xy_from_published_robot_pose",
        "real_media": False,
        "image_to_local_transform_verified": False,
        "target_platform_match": False,
        "human_trajectory_generated": False,
        "future_human_path_exported": False,
        "paper_edit": False,
    }
    sidecar.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": output_path.as_posix(), "rows": len(timestamps), "status": payload["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
