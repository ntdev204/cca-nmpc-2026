from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT

from tools.final_pack import (
    CAPTURE_SOURCES,
    CONTROL_INTERFACES,
    REQUIRED,
    OPTIONAL,
    read_context,
    read_control,
    read_csv,
    read_events,
    read_lidar,
    read_map,
    sha256_file,
    validate_capture_calibration,
    validate_control_interface,
)

ROOT = PROJECT_ROOT


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "valid"}:
        return True
    if normalized in {"0", "false", "no", "invalid"}:
        return False
    raise ValueError(f"invalid boolean value: {value}")


def quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    weight = position - lower
    return float(ordered[lower] + weight * (ordered[upper] - ordered[lower]))


def stats(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None, "p50": None, "p95": None}
    return {
        "count": len(values),
        "min": float(min(values)),
        "max": float(max(values)),
        "mean": float(sum(values) / len(values)),
        "p50": quantile(values, 0.50),
        "p95": quantile(values, 0.95),
    }


def summarize_controller_events(
    rows: list[dict[str, str]],
) -> tuple[dict[str, object], int]:
    status_counts: dict[str, int] = {}
    solve_times: list[float] = []
    risk_bounds: list[float] = []
    constraint_violations: list[float] = []
    local_generation_counts: list[int] = []
    local_replans = 0
    deadline_misses = 0
    detail_parse_failures = 0
    cca_step_count = 0
    for row in rows:
        if row.get("event_type", "").strip().lower() != "cca_nmpc_step":
            continue
        cca_step_count += 1
        raw_detail = row.get("detail", "").strip()
        if not raw_detail:
            detail_parse_failures += 1
            continue
        try:
            detail = json.loads(raw_detail)
        except json.JSONDecodeError:
            detail_parse_failures += 1
            continue
        if not isinstance(detail, dict):
            detail_parse_failures += 1
            continue
        status = str(detail.get("status", "unknown"))
        status_counts[status] = status_counts.get(status, 0) + 1
        if detail.get("local_replanned") is True:
            local_replans += 1
        if detail.get("deadline_missed") is True:
            deadline_misses += 1
        for field, destination in (
            ("solve_ms", solve_times),
            ("risk_bound", risk_bounds),
            ("constraint_violation", constraint_violations),
        ):
            value = detail.get(field)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
                destination.append(float(value))
        generation = detail.get("local_generation_count")
        if isinstance(generation, int) and not isinstance(generation, bool) and generation >= 0:
            local_generation_counts.append(generation)
    return (
        {
            "cca_nmpc_step_count": cca_step_count,
            "status_counts": status_counts,
            "local_replan_count": local_replans,
            "local_generation_count": stats([float(value) for value in local_generation_counts]),
            "deadline_miss_count": deadline_misses,
            "solve_ms": stats(solve_times),
            "risk_bound": stats(risk_bounds),
            "constraint_violation": stats(constraint_violations),
            "detail_parse_failures": detail_parse_failures,
            "future_human_path_exported": False,
        },
        detail_parse_failures,
    )


def duration(rows: list[dict[str, str]]) -> float:
    timestamps = [int(row["t_ns"]) for row in rows]
    return float(timestamps[-1] - timestamps[0]) / 1.0e9


def verify_checksums(root: Path) -> dict[str, str]:
    checksum_path = root / "checksums.sha256"
    if not checksum_path.is_file():
        raise ValueError("checksums.sha256 is required")
    records: dict[str, str] = {}
    for line_number, line in enumerate(checksum_path.read_text(encoding="utf-8").splitlines(), start=1):
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise ValueError(f"checksums.sha256:{line_number}: invalid record")
        name = parts[1].strip()
        if name in records:
            raise ValueError(f"checksums.sha256:{line_number}: duplicate record for {name}")
        candidate = (root / name).resolve()
        if (
            not candidate.is_file()
            or not candidate.is_relative_to(root.resolve())
            or candidate.parent != root.resolve()
        ):
            raise ValueError(f"checksums.sha256:{line_number}: file is outside package")
        digest = sha256_file(candidate)
        if digest.lower() != parts[0].lower():
            raise ValueError(f"checksums.sha256:{line_number}: hash mismatch for {name}")
        records[name] = digest
    expected = {
        name
        for name in (*REQUIRED, "map.json", *OPTIONAL, "manifest.json")
        if (root / name).is_file()
    }
    if set(records) != expected:
        missing = sorted(expected - set(records))
        extra = sorted(set(records) - expected)
        detail = []
        if missing:
            detail.append(f"missing {', '.join(missing)}")
        if extra:
            detail.append(f"unexpected {', '.join(extra)}")
        raise ValueError("checksums.sha256: " + "; ".join(detail))
    return records


def validate_manifest(manifest: dict[str, object], checksums: dict[str, str], root: Path) -> None:
    if manifest.get("integrity_status") != "verified":
        raise ValueError("input package must have integrity_status=verified")
    if not isinstance(manifest.get("run_id"), str) or not str(manifest["run_id"]).strip():
        raise ValueError("manifest.run_id is required")
    if manifest.get("capture_source") not in CAPTURE_SOURCES:
        raise ValueError("manifest.capture_source is unsupported")
    if manifest.get("control_interface") not in CONTROL_INTERFACES:
        raise ValueError("manifest.control_interface is unsupported")
    if manifest.get("clock") not in {"robot_time", "system_time"}:
        raise ValueError("manifest.clock is unsupported")
    if manifest.get("units") != "si":
        raise ValueError("manifest.units must be si")
    if manifest.get("context_only") is not True or manifest.get("human_trajectory_generated") is not False:
        raise ValueError("input package must declare context_only and no human trajectory")
    if manifest.get("replay_file_included") is not False:
        raise ValueError("input package must not include a replay file")
    sensors = manifest.get("sensors")
    if (
        not isinstance(sensors, dict)
        or not isinstance(sensors.get("camera"), str)
        or not isinstance(sensors.get("lidar"), str)
        or not isinstance(manifest.get("firmware"), str)
    ):
        raise ValueError("manifest must declare camera, lidar and firmware identity")
    if manifest.get("map_sha256") != checksums.get("map.json"):
        raise ValueError("manifest.map_sha256 does not match map.json")
    manifest_files = manifest.get("files")
    expected_files = {
        name
        for name in (*REQUIRED, "map.json", *OPTIONAL)
        if (root / name).is_file()
    }
    if not isinstance(manifest_files, dict) or set(manifest_files) != expected_files:
        raise ValueError("manifest.files must enumerate exactly the package payload files")
    for name in expected_files:
        record = manifest_files.get(name)
        if not isinstance(record, dict) or record.get("sha256") != checksums.get(name):
            raise ValueError(f"manifest.files hash mismatch for {name}")
    calibration_path = root / "calibration.json"
    calibration_record = manifest.get("calibration")
    if manifest.get("capture_source") != "unknown" and not calibration_path.is_file():
        raise ValueError("non-unknown capture requires calibration.json")
    if calibration_path.is_file():
        if not isinstance(calibration_record, dict) or calibration_record.get("path") != "calibration.json" or calibration_record.get("sha256") != checksums.get("calibration.json"):
            raise ValueError("manifest.calibration must bind calibration.json")
        try:
            calibration_payload = json.loads(calibration_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("calibration.json is not valid JSON") from error
        validate_capture_calibration(
            calibration_payload,
            camera=sensors["camera"],
            lidar=sensors["lidar"],
        )
    elif calibration_record is not None:
        raise ValueError("manifest.calibration references an absent file")


def read_package(root: Path) -> tuple[dict[str, object], dict[str, str], dict[str, object]]:
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("manifest.json is required")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest.json must contain an object")
    if manifest.get("status") != "verified":
        raise ValueError("input package must have status=verified")
    allowed = set((*REQUIRED, "map.json", *OPTIONAL, "manifest.json", "checksums.sha256"))
    unexpected = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_dir() or path.name not in allowed
    )
    if unexpected:
        raise ValueError(f"input package contains unrelated files: {', '.join(unexpected)}")
    checksums = verify_checksums(root)
    validate_manifest(manifest, checksums, root)
    robot_rows, _ = read_csv(
        root / "robot_state.csv",
        REQUIRED["robot_state.csv"],
        tuple(field for field in REQUIRED["robot_state.csv"] if field != "t_ns"),
    )
    control_rows, control_fields = read_control(root / "control.csv")
    validate_control_interface(control_fields, str(manifest["control_interface"]))
    context_rows, _ = read_context(root / "context.csv")
    events_rows, events_fields = read_events(root / "events.csv")
    lidar_rows = []
    if (root / "lidar.csv").is_file():
        lidar_rows, _ = read_lidar(root / "lidar.csv")
    map_payload = read_map(root / "map.json")
    return (
        manifest,
        checksums,
        {
            "robot": robot_rows,
            "control": control_rows,
            "control_fields": control_fields,
            "context": context_rows,
            "events": events_rows,
            "events_fields": events_fields,
            "lidar": lidar_rows,
            "map": map_payload,
        },
    )


def analyze(root: Path, output: Path) -> Path:
    root = root.resolve()
    output = output.resolve()
    if output == root or output.is_relative_to(root):
        raise ValueError("analysis output must be separate from the raw package")
    if not root.is_dir():
        raise ValueError(f"input package does not exist: {root}")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"analysis output must be empty: {output}")
    manifest, checksums, payload = read_package(root)
    output.mkdir(parents=True, exist_ok=True)
    robot_rows = payload["robot"]
    control_rows = payload["control"]
    context_rows = payload["context"]
    events_rows = payload["events"]
    lidar_rows = payload["lidar"]
    map_payload = payload["map"]
    robot_speed = [
        math.hypot(float(row["vx_mps"]), float(row["vy_mps"])) for row in robot_rows
    ]
    path_length = sum(
        math.hypot(
            float(current["x_m"]) - float(previous["x_m"]),
            float(current["y_m"]) - float(previous["y_m"]),
        )
        for previous, current in zip(robot_rows, robot_rows[1:], strict=False)
    )
    controls: dict[str, dict[str, float | int | None]] = {}
    for field in payload["control_fields"]:
        if field == "t_ns":
            continue
        values: list[float] = []
        for row in control_rows:
            try:
                value = float(row[field])
            except (TypeError, ValueError):
                continue
            if math.isfinite(value):
                values.append(value)
        controls[field] = stats(values)
    valid_rows = [row for row in context_rows if parse_bool(row["context_valid"])]
    direction_counts: dict[str, int] = {}
    for row in context_rows:
        direction = row["direction"].strip().lower()
        direction_counts[direction] = direction_counts.get(direction, 0) + 1
    direction_transitions = sum(
        first["direction"].strip().lower() != second["direction"].strip().lower()
        for first, second in zip(valid_rows, valid_rows[1:], strict=False)
    )
    event_counts: dict[str, int] = {}
    solve_times: list[float] = []
    clearances: list[float] = []
    for row in events_rows:
        event_type = row["event_type"].strip().lower()
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
        if row.get("solve_ms", "").strip():
            solve_times.append(float(row["solve_ms"]))
        if row.get("minimum_clearance_m", "").strip():
            clearances.append(float(row["minimum_clearance_m"]))
    controller_summary, _ = summarize_controller_events(events_rows)
    analysis = {
        "schema": "cca-final-run-analysis-v1",
        "schema_version": "1.0.0",
        "status": "candidate-analysis",
        "created_at": utc_now(),
        "paper_edit": False,
        "raw_data_scope": "external-only",
        "source": {
            "run_id": manifest["run_id"],
            "package_name": root.name,
            "manifest_sha256": checksums["manifest.json"],
            "file_sha256": checksums,
            "capture_source": manifest.get("capture_source", "unknown"),
            "control_interface": manifest.get("control_interface", "unknown"),
            "evidence_status": manifest.get("evidence_status", "source-unverified"),
            "clock": manifest.get("clock"),
            "controller": manifest.get("controller"),
            "robot": manifest.get("robot"),
        },
        "analysis_script_sha256": sha256_file(Path(__file__).resolve()),
        "robot_state": {
            "sample_count": len(robot_rows),
            "duration_s": duration(robot_rows),
            "path_length_m": float(path_length),
            "displacement_m": math.hypot(
                float(robot_rows[-1]["x_m"]) - float(robot_rows[0]["x_m"]),
                float(robot_rows[-1]["y_m"]) - float(robot_rows[0]["y_m"]),
            ),
            "speed_mps": stats(robot_speed),
        },
        "control": {"sample_count": len(control_rows), "signals": controls},
        "context": {
            "sample_count": len(context_rows),
            "valid_rate": float(len(valid_rows) / len(context_rows)),
            "confidence": stats([float(row["confidence"]) for row in context_rows]),
            "speed_mps": stats([float(row["speed_mps"]) for row in context_rows]),
            "direction_counts": direction_counts,
            "direction_transitions_valid_context": direction_transitions,
            "confusion_matrix": "not_available_without_independent_direction_labels",
        },
        "lidar": {
            "scan_count": len(lidar_rows),
            "total_point_count": int(sum(int(row["point_count"]) for row in lidar_rows)),
            "scan_timestamps_strictly_increasing": True,
        },
        "events": {
            "sample_count": len(events_rows),
            "event_counts": event_counts,
            "solve_ms": stats(solve_times),
            "minimum_clearance_m": stats(clearances),
            "controller": controller_summary,
        },
        "map": {
            "frame_id": map_payload["frame_id"],
            "resolution_m": map_payload["resolution_m"],
            "width": map_payload["width"],
            "height": map_payload["height"],
            "sha256": checksums["map.json"],
        },
        "limitations": [
            "No independent pose ground truth is present in the package.",
            "Tracking error and direction confusion matrix are not estimated without labels.",
            "This analysis does not establish real-time, safety, or generalization claims.",
            "CCA event-detail parse failures are reported and are not imputed.",
        ],
    }
    analysis_path = output / "analysis.json"
    analysis_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "checksums.sha256").write_text(
        f"{sha256_file(analysis_path)}  analysis.json\n",
        encoding="utf-8",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a sealed direct CSV/JSON robot package")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        result = analyze(arguments.input, arguments.output)
    except (OSError, ValueError, json.JSONDecodeError, csv.Error) as error:
        parser.error(str(error))
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
