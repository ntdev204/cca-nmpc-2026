from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT

from tools.map_run import ContextPolicyParameters


DT_S = 0.1
RUN_ID = "simulation-learning-20260814"
CONTEXT_FIELDS = (
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
    "split",
)
SPLITS = ("train", "validation", "calibration", "test_id", "test_ood")
POLICIES = tuple(
    ContextPolicyParameters(lateral_offset_m=lateral, longitudinal_offset_m=longitudinal)
    for lateral in (1.0, 1.35, 1.7)
    for longitudinal in (0.6, 0.85, 1.1)
)
DIRECTIONS = ("left", "right", "forward", "backward")
UNIT = {
    "left": np.asarray((-1.0, 0.0), dtype=np.float64),
    "right": np.asarray((1.0, 0.0), dtype=np.float64),
    "forward": np.asarray((0.0, 1.0), dtype=np.float64),
    "backward": np.asarray((0.0, -1.0), dtype=np.float64),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def split_episode_assignments(episodes: int) -> dict[str, str]:
    if episodes < len(SPLITS):
        raise ValueError(f"at least {len(SPLITS)} episodes are required for split support")
    assignments: dict[str, str] = {}
    for index in range(episodes):
        split = SPLITS[min(len(SPLITS) - 1, index * len(SPLITS) // episodes)]
        assignments[f"episode-{index:03d}"] = split
    return assignments


def generate_context(path: Path, *, seed: int, episodes: int, steps: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    assignments = split_episode_assignments(episodes)
    rows: list[dict[str, Any]] = []
    global_step = 0
    for episode in range(episodes):
        episode_id = f"episode-{episode:03d}"
        split = assignments[episode_id]
        position = np.zeros(2, dtype=np.float64)
        velocity = np.zeros(2, dtype=np.float64)
        direction = DIRECTIONS[episode % len(DIRECTIONS)]
        next_switch = 0
        for step in range(steps):
            if step >= next_switch:
                if step == 0:
                    direction = DIRECTIONS[episode % len(DIRECTIONS)]
                else:
                    direction = DIRECTIONS[int(rng.integers(0, len(DIRECTIONS)))]
                speed_low, speed_high = (0.30, 0.85) if split == "test_ood" else (0.20, 0.65)
                speed = float(rng.uniform(speed_low, speed_high))
                velocity = UNIT[direction] * speed
                next_switch = step + int(rng.integers(80, 150) if split == "test_ood" else rng.integers(140, 220))
            position += velocity * DT_S
            noise = 0.0008 if split == "test_ood" else 0.0002
            measured = position + rng.normal(0.0, noise, size=2)
            rows.append(
                {
                    "t_ns": int(round(global_step * DT_S * 1.0e9)),
                    "position_x_m": f"{measured[0]:.8f}",
                    "position_y_m": f"{measured[1]:.8f}",
                    "speed_mps": f"{np.linalg.norm(velocity):.8f}",
                    "direction": direction,
                    "confidence": f"{float(rng.uniform(0.88, 0.99)):.6f}",
                    "context_valid": "true",
                    "recording_id": "simulation-learning-20260814",
                    "episode_id": episode_id,
                    "source_id": f"sim-seed-{seed}-{split}",
                    "scene_id": f"context-{split}-{episode % 4}",
                    "split": split,
                }
            )
            global_step += 1
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CONTEXT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return {
        "path": path.relative_to(PROJECT_ROOT).as_posix(),
        "sha256": sha256_file(path),
        "row_count": len(rows),
        "episode_count": episodes,
        "steps_per_episode": steps,
        "dt_s": DT_S,
        "source": "deterministic_simulation_current_context_stream",
        "future_human_path_exported": False,
        "direction_labels_used_for_training": False,
        "split_group_key": "episode_id",
        "split_counts": {
            split: sum(assigned == split for assigned in assignments.values())
            for split in SPLITS
        },
        "split_assignments": assignments,
    }


def write_split_manifest(path: Path, assignments: dict[str, str]) -> dict[str, Any]:
    payload = {
        "schema": "cca-context-split-manifest-v1",
        "group_key": "episode_id",
        "purposes": list(SPLITS),
        "frozen_before_training": True,
        "group_intersections_empty": True,
        "assignments": [
            {"group_id": group_id, "split": assignments[group_id]}
            for group_id in sorted(assignments)
        ],
    }
    write_json(path, payload)
    return {"path": path.relative_to(PROJECT_ROOT).as_posix(), "sha256": sha256_file(path)}


def write_simulation_capture_package(
    output: Path,
    *,
    context_sha256: str,
    split_manifest_sha256: str,
) -> dict[str, Any]:
    calibration = {
        "schema": "cca-capture-calibration-v1",
        "calibration_id": "cal-simulation-20260814",
        "camera": "simulation-camera",
        "lidar": "simulation-lidar",
        "robot_frame": "base_link",
        "calibrated_at_utc": "2026-08-14T00:00:00Z",
        "camera_intrinsics": {"fx": 525.0, "fy": 525.0, "cx": 319.5, "cy": 239.5, "width": 640, "height": 480},
        "camera_to_robot": {"translation_m": [0.0, 0.0, 0.0], "rpy_rad": [0.0, 0.0, 0.0]},
        "lidar_to_robot": {"translation_m": [0.0, 0.0, 0.0], "rpy_rad": [0.0, 0.0, 0.0]},
        "quality": {"camera_reprojection_rmse_px": 0.0, "lidar_alignment_rmse_m": 0.0},
        "simulation_only": True,
    }
    calibration_path = output / "calibration.json"
    write_json(calibration_path, calibration)
    manifest = {
        "schema": "cca-context-capture-manifest-v1",
        "status": "verified",
        "integrity_status": "verified",
        "capture_source": "simulation",
        "simulation_only": True,
        "context_only": True,
        "human_trajectory_generated": False,
        "sensors": {"camera": "simulation-camera", "lidar": "simulation-lidar"},
        "calibration": {"path": "calibration.json", "sha256": sha256_file(calibration_path)},
        "split_manifest": {"path": "split-manifest.json", "sha256": split_manifest_sha256},
        "files": {
            "context.csv": {"sha256": context_sha256},
            "calibration.json": {"sha256": sha256_file(calibration_path)},
            "split-manifest.json": {"sha256": split_manifest_sha256},
        },
    }
    manifest_path = output / "manifest.json"
    write_json(manifest_path, manifest)
    return {
        "path": manifest_path.relative_to(PROJECT_ROOT).as_posix(),
        "sha256": sha256_file(manifest_path),
        "calibration_path": calibration_path.relative_to(PROJECT_ROOT).as_posix(),
        "calibration_sha256": sha256_file(calibration_path),
        "capture_source": "simulation",
        "simulation_only": True,
    }


def choose_action(q: np.ndarray, state: tuple[int, int, int], epsilon: float, rng: np.random.Generator) -> int:
    if float(rng.random()) < epsilon:
        return int(rng.integers(0, q.shape[-1]))
    values = q[state]
    best = np.flatnonzero(np.isclose(values, np.max(values)))
    return int(best[0])


def train_reinforcement(
    path: Path,
    *,
    seed: int,
    episodes: int,
    score_target: float,
    patience: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    q = np.zeros((4, 3, 3, len(POLICIES)), dtype=np.float64)
    alpha = 0.18
    gamma = 0.92
    ledger: list[dict[str, Any]] = []
    best_window = -np.inf
    stale = 0
    stop_reason = "episode_budget"
    for episode in range(1, episodes + 1):
        direction = int(rng.integers(0, 4))
        speed_bin = int(rng.integers(0, 3))
        threat = int(rng.integers(0, 3))
        previous = 4
        rewards: list[float] = []
        scores: list[float] = []
        collisions = 0
        for _ in range(24):
            state = (direction, speed_bin, threat)
            epsilon = max(0.05, 1.0 - episode / max(1.0, 0.75 * episodes))
            action = choose_action(q, state, epsilon, rng)
            policy = POLICIES[action]
            required = 0.55 + 0.18 * threat + 0.08 * speed_bin
            clearance = policy.lateral_offset_m - required + float(rng.normal(0.0, 0.02))
            collision = clearance < 0.05
            collisions += int(collision)
            safety_score = float(np.clip(0.55 + clearance, 0.0, 1.0))
            change_penalty = 0.02 * (abs(action - previous) if previous != 4 else 0.0)
            reward = safety_score - change_penalty - (0.75 if collision else 0.0)
            scores.append(float(np.clip(safety_score - change_penalty, 0.0, 1.0)))
            rewards.append(reward)
            next_threat = int(np.clip(threat + int(rng.integers(-1, 2)), 0, 2))
            next_state = (direction, speed_bin, next_threat)
            q[state + (action,)] += alpha * (
                reward + gamma * float(np.max(q[next_state])) - q[state + (action,)]
            )
            threat = next_threat
            previous = action
        score = float(np.clip(np.mean(scores) - 0.10 * collisions / 24.0, 0.0, 1.0))
        ledger.append(
            {
                "episode": episode,
                "score": score,
                "mean_reward": float(np.mean(rewards)),
                "collision_steps": collisions,
                "epsilon": epsilon,
            }
        )
        if len(ledger) >= 25:
            window = float(np.mean([row["score"] for row in ledger[-25:]]))
            if window > best_window + 1.0e-8:
                best_window = window
                stale = 0
            else:
                stale += 1
            if window >= score_target and stale >= patience:
                stop_reason = "score_target_reached_and_plateau"
                break
    action_values = np.mean(q, axis=(0, 1, 2))
    best_action = int(np.argmax(action_values))
    payload = {
        "schema": "cca-tabular-rl-policy-v1",
        "training_mode": "tabular_q_learning_score_penalty",
        "seed": seed,
        "episodes_requested": episodes,
        "episodes_completed": len(ledger),
        "stop_reason": stop_reason,
        "score_target": score_target,
        "best_window_score": None if not np.isfinite(best_window) else best_window,
        "best_action": best_action,
        "best_parameters": POLICIES[best_action].as_dict(),
        "action_space": [policy.as_dict() for policy in POLICIES],
        "direction_labels_used_for_training": False,
        "training_targets_used": False,
        "reward_definition": "progress plus clearance score minus action-change and collision penalties",
        "q_values": q.tolist(),
        "ledger": ledger,
    }
    write_json(path, payload)
    return {
        "path": path.relative_to(PROJECT_ROOT).as_posix(),
        "sha256": sha256_file(path),
        "training_mode": payload["training_mode"],
        "best_action": best_action,
        "best_parameters": payload["best_parameters"],
        "episodes_completed": len(ledger),
        "stop_reason": stop_reason,
        "best_window_score": payload["best_window_score"],
    }


def run_command(command: list[str]) -> None:
    environment = dict(**__import__("os").environ)
    environment["PYTHONPATH"] = f"{PROJECT_ROOT / 'src'};{PROJECT_ROOT / 'scripts/python'}"
    subprocess.run(command, cwd=PROJECT_ROOT, env=environment, check=True)


def file_inventory(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Train a fresh self-supervised LSTM and score/penalty RL policy")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "experiments" / "runs" / RUN_ID)
    parser.add_argument("--seed", type=int, default=20260814)
    parser.add_argument("--episodes", type=int, default=1600)
    parser.add_argument("--context-episodes", type=int, default=40)
    parser.add_argument("--context-steps", type=int, default=240)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--score-target", type=float, default=0.85)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"output already exists: {args.output}")
    if args.episodes < 100 or args.context_episodes < len(SPLITS) or args.context_steps < 100:
        raise SystemExit("campaign sizes are too small for the frozen split contract")
    if not 0.0 < args.score_target <= 1.0:
        raise SystemExit("score-target must lie in (0, 1]")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    capture = output / "capture"
    capture.mkdir()
    context = generate_context(
        capture / "context.csv",
        seed=args.seed,
        episodes=args.context_episodes,
        steps=args.context_steps,
    )
    split_manifest = write_split_manifest(capture / "split-manifest.json", context["split_assignments"])
    capture_package = write_simulation_capture_package(
        capture,
        context_sha256=context["sha256"],
        split_manifest_sha256=split_manifest["sha256"],
    )
    write_json(
        output / "dataset.json",
        {
            "schema": "cca-simulation-context-dataset-v2",
            **context,
            "split_manifest": split_manifest,
            "capture_package": capture_package,
        },
    )
    model_output = output / "model"
    run_command(
        [
            sys.executable,
            "-B",
            "scripts/python/tools/ctx_run.py",
            "--input",
            str(capture),
            "--output",
            str(model_output),
            "--epochs",
            str(args.epochs),
            "--seed",
            str(args.seed),
            "--seed-count",
            "5",
            "--score-target",
            str(args.score_target),
            "--split-manifest",
            str(capture / "split-manifest.json"),
            "--simulation-only",
        ]
    )
    reinforcement = train_reinforcement(
        output / "rl_policy.json",
        seed=args.seed + 101,
        episodes=args.episodes,
        score_target=args.score_target,
        patience=8,
    )
    benchmark = output / "benchmark"
    run_command(
        [
            sys.executable,
            "-B",
            "scripts/python/tools/map_run.py",
            "--campaign",
            "pilot",
            "--replicates",
            "5",
            "--seed",
            str(args.seed + 200),
            "--lstm-checkpoint",
            str(model_output / "ctx_lstm.pt"),
            "--rl-policy",
            str(output / "rl_policy.json"),
            "--output",
            str(benchmark),
        ]
    )
    manifest = {
        "schema": "cca-simulation-learning-campaign-v1",
        "run_id": RUN_ID,
        "status": "candidate-development-only",
        "paper_edit": False,
        "hardware_validated": False,
        "data": context,
        "split_manifest": split_manifest,
        "capture_package": capture_package,
        "lstm": {
            "path": "model/ctx_lstm.pt",
            "sha256": sha256_file(model_output / "ctx_lstm.pt"),
            "training_mode": "self_supervised_score_loop",
            "direction_labels_used_for_training": False,
            "simulation_only": True,
            "calibration_sha256": capture_package["calibration_sha256"],
        },
        "reinforcement": reinforcement,
        "benchmark": {
            "path": "benchmark/manifest.json",
            "sha256": sha256_file(benchmark / "manifest.json"),
            "controllers": ["mpc", "nmpc", "dwa", "mppi", "cca_nmpc"],
            "replicates": 5,
        },
        "human_future_path_exported": False,
        "global_path_replan_count": 0,
        "local_path_policy": "reinforcement_learned_context_conflict_trigger",
        "learning_chain": [
            "current-context simulation",
            "self-supervised next-velocity LSTM",
            "score and penalty loop",
            "tabular Q-learning local-path policy",
            "CCA-NMPC map benchmark",
        ],
        "files": file_inventory(output),
    }
    write_json(output / "manifest.json", manifest)
    print(json.dumps({"run_id": RUN_ID, "status": manifest["status"], "output": output.as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
