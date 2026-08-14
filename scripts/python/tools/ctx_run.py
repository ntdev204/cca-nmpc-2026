from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import random
from typing import Any, Callable

import numpy as np
import torch
from jsonschema import Draft202012Validator, FormatChecker
from torch import Tensor
from torch.nn import functional as F
from torch.utils.data import DataLoader, TensorDataset

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT

from ai.ctx_lstm import DIRECTION_CLASSES, ContextDirectionConfig, ContextDirectionLstm
from shared import (
    CONTRACT_PATH,
    is_forbidden_context_field,
    load_contract,
    sha256_file,
    validate_capture_calibration,
)

CONTRACT = load_contract()
CONTEXT = CONTRACT["context"]
OBSERVED_STEPS = int(CONTEXT["observed_steps"])
FUTURE_STEPS = int(CONTEXT["future_steps"])
FRAME_STRIDE = int(CONTEXT["frame_stride"])
DT_S = float(CONTEXT["dt_s"])
MIN_SPEED_MPS = float(CONTEXT["min_speed_mps"])
MIN_WINDOWS = 30
MIN_TRAINING_SEEDS = 5
BOOTSTRAP_REPLICATES = 400
BOOTSTRAP_SEED = 20260812
SPLIT_SCHEMA = "cca-context-split-manifest-v1"
SPLIT_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "context-split-manifest.schema.json"
SPLIT_PURPOSES = ("train", "validation", "calibration", "test_id", "test_ood")
GROUP_COLUMNS = ("recording_id", "episode_id", "source_id", "scene_id")
CONFIRMATORY_CAPTURE_SOURCES = {"hardware", "hardware_in_loop", "real_offline"}
SIMULATION_CAPTURE_SOURCES = {"simulation"}
REQUIRED_COLUMNS = (
    "t_ns",
    "position_x_m",
    "position_y_m",
    "speed_mps",
    "direction",
    "confidence",
    "context_valid",
)


def parse_bool(value: str) -> bool:
    token = value.strip().lower()
    if token in {"1", "true", "yes", "valid"}:
        return True
    if token in {"0", "false", "no", "invalid"}:
        return False
    raise ValueError(f"unsupported boolean value: {value}")


def read_context(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = tuple(reader.fieldnames or ())
        forbidden = [field for field in fields if is_forbidden_context_field(field)]
        if forbidden:
            raise ValueError(f"{path.name}: human trajectory fields are forbidden: {', '.join(forbidden)}")
        missing = [name for name in REQUIRED_COLUMNS if name not in fields]
        if missing:
            raise ValueError(f"{path.name}: missing columns {', '.join(missing)}")
        rows: list[dict[str, Any]] = []
        previous: int | None = None
        for line, raw in enumerate(reader, start=2):
            try:
                timestamp = int(raw["t_ns"])
                position = np.asarray(
                    (float(raw["position_x_m"]), float(raw["position_y_m"])),
                    dtype=np.float64,
                )
                speed = float(raw["speed_mps"])
                confidence = float(raw["confidence"])
                valid = parse_bool(raw["context_valid"])
            except (TypeError, ValueError) as error:
                raise ValueError(f"{path.name}:{line}: invalid context row") from error
            if previous is not None and timestamp <= previous:
                raise ValueError(f"{path.name}:{line}: t_ns must be strictly increasing")
            if not np.isfinite(position).all() or not np.isfinite((speed, confidence)).all():
                raise ValueError(f"{path.name}:{line}: context values must be finite")
            if speed < 0.0 or not 0.0 <= confidence <= 1.0:
                raise ValueError(f"{path.name}:{line}: speed/confidence out of range")
            direction = raw["direction"].strip().lower()
            if direction not in {*DIRECTION_CLASSES, "unknown", "invalid"}:
                raise ValueError(f"{path.name}:{line}: unsupported direction")
            rows.append(
                {
                    "t_ns": timestamp,
                    "position": position,
                    "speed_mps": speed,
                    "direction": direction,
                    "confidence": confidence,
                    "valid": valid,
                    "groups": {
                        name: raw.get(name, "").strip()
                        for name in GROUP_COLUMNS
                    },
                    "declared_split": raw.get("split", "").strip(),
                }
            )
            previous = timestamp
    if not rows:
        raise ValueError(f"{path.name}: no data rows")
    return rows


def load_confirmatory_capture_manifest(
    input_path: Path,
    context_path: Path,
    *,
    allow_simulation: bool = False,
) -> dict[str, Any]:
    """Require a sealed direct-capture package before split training.

    A split manifest alone cannot prove that its rows came from a real capture.
    The final-run manifest is therefore checked for source, structural
    integrity, context-only semantics, and the exact context-file digest. An
    explicit simulation-only flag may admit a sealed simulator package, but it
    never changes the real-capture gate used for hardware evidence.
    """
    root = Path(input_path).resolve()
    if not root.is_dir():
        raise ValueError("confirmatory context input must be a sealed run directory")
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("confirmatory context input requires manifest.json")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("confirmatory capture manifest is not valid JSON") from error
    if not isinstance(payload, dict):
        raise ValueError("confirmatory capture manifest must be an object")
    if payload.get("status") != "verified" or payload.get("integrity_status") != "verified":
        raise ValueError("confirmatory capture manifest must have verified structural integrity")
    allowed_sources = CONFIRMATORY_CAPTURE_SOURCES | SIMULATION_CAPTURE_SOURCES if allow_simulation else CONFIRMATORY_CAPTURE_SOURCES
    if payload.get("capture_source") not in allowed_sources:
        raise ValueError("confirmatory context requires a declared real capture source")
    if allow_simulation and payload.get("capture_source") == "simulation" and payload.get("simulation_only") is not True:
        raise ValueError("simulation context package must declare simulation_only=true")
    if not allow_simulation and payload.get("capture_source") == "simulation":
        raise ValueError("confirmatory context requires a declared real capture source")
    if payload.get("context_only") is not True or payload.get("human_trajectory_generated") is not False:
        raise ValueError("confirmatory capture must be context-only and trajectory-free")
    files = payload.get("files")
    context_record = files.get("context.csv") if isinstance(files, dict) else None
    if not isinstance(context_record, dict) or not isinstance(context_record.get("sha256"), str):
        raise ValueError("confirmatory capture manifest lacks context.csv provenance")
    if context_record["sha256"] != sha256_file(context_path):
        raise ValueError("context.csv hash does not match the sealed capture manifest")
    calibration_record = payload.get("calibration")
    calibration_files = files if isinstance(files, dict) else {}
    if not isinstance(calibration_record, dict) or calibration_record.get("path") != "calibration.json":
        raise ValueError("confirmatory capture manifest lacks calibration.json provenance")
    calibration_path = root / "calibration.json"
    calibration_file_record = calibration_files.get("calibration.json")
    if not calibration_path.is_file() or not isinstance(calibration_file_record, dict):
        raise ValueError("confirmatory capture requires calibration.json")
    calibration_sha256 = str(calibration_file_record.get("sha256", ""))
    if calibration_sha256 != sha256_file(calibration_path) or calibration_sha256 != calibration_record.get("sha256"):
        raise ValueError("calibration.json hash does not match the sealed capture manifest")
    try:
        calibration_payload = json.loads(calibration_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("calibration.json is not valid JSON") from error
    sensors = payload.get("sensors")
    validate_capture_calibration(
        calibration_payload,
        camera=sensors.get("camera") if isinstance(sensors, dict) else None,
        lidar=sensors.get("lidar") if isinstance(sensors, dict) else None,
    )
    return {
        "path": manifest_path,
        "sha256": sha256_file(manifest_path),
        "capture_source": payload["capture_source"],
        "run_id": payload.get("run_id"),
        "context_sha256": context_record["sha256"],
        "calibration_sha256": calibration_sha256,
    }


def load_split_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(SPLIT_SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(payload),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise ValueError(f"invalid context split manifest: {errors[0].message}")
    if not isinstance(payload, dict) or payload.get("schema") != SPLIT_SCHEMA:
        raise ValueError(f"split manifest must use schema {SPLIT_SCHEMA}")
    if tuple(payload.get("purposes", ())) != SPLIT_PURPOSES:
        raise ValueError("split manifest purposes must be train, validation, calibration, test_id, test_ood")
    group_key = str(payload.get("group_key", ""))
    if group_key not in GROUP_COLUMNS:
        raise ValueError(f"split manifest group_key must be one of {GROUP_COLUMNS}")
    if payload.get("frozen_before_training") is not True:
        raise ValueError("split manifest must be frozen before training")
    if payload.get("group_intersections_empty") is not True:
        raise ValueError("split manifest must verify empty group intersections")
    assignments = payload.get("assignments")
    if not isinstance(assignments, list) or not assignments:
        raise ValueError("split manifest has no group assignments")
    indexed: dict[str, str] = {}
    for item in assignments:
        if not isinstance(item, dict):
            raise ValueError("split manifest assignments must be objects")
        group_id = str(item.get("group_id", "")).strip()
        split = str(item.get("split", "")).strip()
        if not group_id or split not in SPLIT_PURPOSES or group_id in indexed:
            raise ValueError("split manifest group assignments must be unique and valid")
        indexed[group_id] = split
    if set(indexed.values()) != set(SPLIT_PURPOSES):
        raise ValueError("split manifest must contain every split purpose")
    return {"path": path, "group_key": group_key, "assignments": indexed}


def build_split_windows(
    rows: list[dict[str, Any]],
    split_manifest: dict[str, Any],
) -> tuple[dict[str, tuple[np.ndarray, np.ndarray]], dict[str, Any]]:
    group_key = str(split_manifest["group_key"])
    assignments = split_manifest["assignments"]
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        group_id = str(row.get("groups", {}).get(group_key, "")).strip()
        if not group_id or group_id not in assignments:
            raise ValueError(f"context row has no split assignment for {group_key}: {group_id}")
        declared_split = str(row.get("declared_split", "")).strip()
        assigned_split = assignments[group_id]
        if declared_split and declared_split != assigned_split:
            raise ValueError(f"declared split disagrees with manifest for group {group_id}")
        grouped.setdefault((assigned_split, group_id), []).append(row)
    split_windows: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    audit: dict[str, Any] = {"group_key": group_key, "groups": {}, "window_count": 0, "dropped_window_count": 0}
    for split in SPLIT_PURPOSES:
        histories: list[np.ndarray] = []
        targets: list[np.ndarray] = []
        groups = sorted(group_id for assigned, group_id in grouped if assigned == split)
        if not groups:
            raise ValueError(f"split manifest has no context rows for {split}")
        for group_id in groups:
            group_rows = grouped[(split, group_id)]
            history, target, group_audit = build_windows(group_rows)
            histories.append(history)
            targets.append(target)
            audit["groups"][group_id] = {"split": split, **group_audit}
            audit["window_count"] += group_audit["window_count"]
            audit["dropped_window_count"] += group_audit["dropped_window_count"]
        split_windows[split] = (np.concatenate(histories), np.concatenate(targets))
    return split_windows, audit


def validate_context_group_metadata(rows: list[dict[str, Any]]) -> None:
    """Require all leakage keys before a confirmatory split is admitted."""
    missing = [
        name
        for name in GROUP_COLUMNS
        if any(not str(row.get("groups", {}).get(name, "")).strip() for row in rows)
    ]
    if missing:
        raise ValueError(
            "confirmatory context rows require nonempty leakage-group metadata: "
            + ", ".join(missing)
        )


def validate_confirmatory_split_support(
    split_windows: dict[str, tuple[np.ndarray, np.ndarray]],
    *,
    minimum_windows: int = MIN_WINDOWS,
) -> None:
    if minimum_windows < 1:
        raise ValueError("minimum confirmatory windows must be positive")
    required = ("calibration", "test_id", "test_ood")
    missing = [split for split in required if split not in split_windows]
    if missing:
        raise ValueError(f"confirmatory split is missing: {', '.join(missing)}")
    insufficient = {
        split: len(split_windows[split][0])
        for split in required
        if len(split_windows[split][0]) < minimum_windows
    }
    if insufficient:
        details = ", ".join(f"{split}={count}" for split, count in sorted(insufficient.items()))
        raise ValueError(
            f"confirmatory calibration/test splits require at least {minimum_windows} windows: {details}"
        )


def make_history(positions_xy: np.ndarray, valid_mask: np.ndarray | None = None) -> np.ndarray:
    positions = np.asarray(positions_xy, dtype=np.float32)
    if positions.shape != (OBSERVED_STEPS, 2):
        raise ValueError("context history must have shape [observed_steps, 2]")
    if valid_mask is None:
        valid = np.ones(OBSERVED_STEPS, dtype=np.float32)
    else:
        valid = np.asarray(valid_mask, dtype=np.float32)
        if valid.shape != (OBSERVED_STEPS,) or not np.isfinite(valid).all():
            raise ValueError("valid_mask must have shape [observed_steps]")
        if np.any((valid < 0.0) | (valid > 1.0)):
            raise ValueError("valid_mask must lie in [0, 1]")
    anchor = positions[-1]
    relative = positions - anchor
    velocities = np.zeros_like(relative)
    velocities[1:] = np.diff(positions, axis=0) / DT_S
    velocities[0] = velocities[1]
    return np.concatenate((relative, velocities, valid[:, None]), axis=1).astype(np.float32)


def contiguous_context_windows(
    selected: dict[int, np.ndarray | None],
    frame_indices: list[int],
    *,
    minimum_valid_fraction: float = 0.80,
) -> list[tuple[int, np.ndarray, np.ndarray]]:
    if not 0.0 < minimum_valid_fraction <= 1.0:
        raise ValueError("minimum_valid_fraction must lie in (0, 1]")
    minimum_valid = int(np.ceil(OBSERVED_STEPS * minimum_valid_fraction))
    windows: list[tuple[int, np.ndarray, np.ndarray]] = []
    for offset in range(0, len(frame_indices) - OBSERVED_STEPS + 1):
        raw = [selected[frame] for frame in frame_indices[offset : offset + OBSERVED_STEPS]]
        valid = np.asarray([item is not None for item in raw], dtype=bool)
        if int(valid.sum()) < minimum_valid or not valid[-1]:
            continue
        first = next((index for index, flag in enumerate(valid) if flag), None)
        if first is None:
            continue
        filled = np.zeros((OBSERVED_STEPS, 2), dtype=np.float64)
        last = np.asarray(raw[first], dtype=np.float64)
        filled[: first + 1] = last
        for index, item in enumerate(raw[first + 1 :], start=first + 1):
            if item is not None:
                last = np.asarray(item, dtype=np.float64)
            filled[index] = last
        windows.append((offset, filled.astype(np.float32), valid.astype(np.float32)))
    return windows


def build_windows(rows: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    span = (OBSERVED_STEPS + FUTURE_STEPS - 1) * FRAME_STRIDE + 1
    histories: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    dropped = 0
    for start in range(0, len(rows) - span + 1):
        indices = start + np.arange(OBSERVED_STEPS + FUTURE_STEPS) * FRAME_STRIDE
        selected = [rows[int(index)] for index in indices]
        observed = selected[:OBSERVED_STEPS]
        future = selected[OBSERVED_STEPS:]
        observed_positions = {offset: row["position"] if row["valid"] else None for offset, row in enumerate(observed)}
        history_windows = contiguous_context_windows(
            observed_positions,
            list(range(OBSERVED_STEPS)),
            minimum_valid_fraction=0.80,
        )
        if not history_windows or not all(row["valid"] for row in future):
            dropped += 1
            continue
        _, filled, valid = history_windows[0]
        elapsed = (future[-1]["t_ns"] - observed[-1]["t_ns"]) / 1.0e9
        if elapsed <= 0.0:
            dropped += 1
            continue
        target = (future[-1]["position"] - observed[-1]["position"]) / elapsed
        if not np.isfinite(target).all():
            dropped += 1
            continue
        histories.append(make_history(filled, valid))
        targets.append(target.astype(np.float32))
    if not histories:
        raise ValueError("context.csv has no valid self-supervised windows")
    return np.stack(histories), np.stack(targets), {"window_count": len(histories), "dropped_window_count": dropped}


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)


def score_components(predicted: Tensor, target: Tensor) -> tuple[Tensor, Tensor, Tensor]:
    predicted_speed = torch.linalg.vector_norm(predicted, dim=-1)
    target_speed = torch.linalg.vector_norm(target, dim=-1)
    cosine = F.cosine_similarity(predicted, target, dim=-1, eps=1.0e-8)
    moving = target_speed >= MIN_SPEED_MPS
    cosine = torch.where(moving, cosine, torch.ones_like(cosine))
    speed_score = torch.exp(-torch.abs(predicted_speed - target_speed) / (target_speed + 0.10))
    direction_score = torch.clamp((cosine + 1.0) * 0.5, 0.0, 1.0)
    return (speed_score * direction_score).mean(), speed_score.mean(), direction_score.mean()


def direction_index(vector: np.ndarray, speed: float) -> int | None:
    if speed < MIN_SPEED_MPS:
        return None
    if abs(float(vector[0])) >= abs(float(vector[1])):
        return DIRECTION_CLASSES.index("right" if vector[0] >= 0.0 else "left")
    return DIRECTION_CLASSES.index("forward" if vector[1] >= 0.0 else "backward")


def run_epoch(model: ContextDirectionLstm, loader: DataLoader, optimizer: torch.optim.Optimizer | None) -> dict[str, float]:
    training = optimizer is not None
    model.train(training)
    losses: list[float] = []
    scores: list[float] = []
    with torch.set_grad_enabled(training):
        for history, target in loader:
            if training:
                optimizer.zero_grad(set_to_none=True)
            prediction = model(history)
            vector_loss = F.smooth_l1_loss(prediction.context_velocity_xy, target)
            speed_loss = F.smooth_l1_loss(prediction.speed_mps, torch.linalg.vector_norm(target, dim=-1))
            cosine_loss = 1.0 - F.cosine_similarity(prediction.context_velocity_xy, target, dim=-1, eps=1.0e-8).mean()
            loss = vector_loss + 0.25 * speed_loss + 0.25 * cosine_loss
            if training:
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
                optimizer.step()
            score, _, _ = score_components(prediction.context_velocity_xy, target)
            losses.append(float(loss.item()))
            scores.append(float(score.item()))
    return {"loss": float(np.mean(losses)), "score": float(np.mean(scores))}


def train(
    history: np.ndarray,
    target: np.ndarray,
    *,
    epochs: int,
    score_target: float,
    seed: int,
) -> tuple[ContextDirectionLstm, dict[str, Any], list[dict[str, Any]], int, int]:
    if len(history) < MIN_WINDOWS:
        raise ValueError(f"at least {MIN_WINDOWS} valid windows are required")
    train_end = max(1, int(len(history) * 0.60))
    validation_end = max(train_end + 1, int(len(history) * 0.80))
    if validation_end >= len(history):
        validation_end = len(history) - 1
    mean = history[:train_end].reshape(-1, history.shape[-1]).mean(axis=0)
    std = np.maximum(history[:train_end].reshape(-1, history.shape[-1]).std(axis=0), 1.0e-6)
    config = ContextDirectionConfig(
        input_mean=tuple(float(value) for value in mean),
        input_std=tuple(float(value) for value in std),
    )
    model = ContextDirectionLstm(config)
    optimizer = torch.optim.Adam(model.parameters(), lr=1.0e-3, weight_decay=1.0e-5)
    train_loader = DataLoader(TensorDataset(torch.from_numpy(history[:train_end]), torch.from_numpy(target[:train_end])), batch_size=128, shuffle=True)
    validation_loader = DataLoader(TensorDataset(torch.from_numpy(history[train_end:validation_end]), torch.from_numpy(target[train_end:validation_end])), batch_size=256)
    best_state: dict[str, Tensor] | None = None
    best_score = -math.inf
    patience = 0
    log: list[dict[str, Any]] = []
    for epoch in range(1, epochs + 1):
        train_metrics = run_epoch(model, train_loader, optimizer)
        validation_metrics = run_epoch(model, validation_loader, None)
        log.append({"epoch": epoch, "train": train_metrics, "validation": validation_metrics})
        if validation_metrics["score"] > best_score + 1.0e-8:
            best_score = validation_metrics["score"]
            best_state = {key: value.detach().clone() for key, value in model.state_dict().items()}
            patience = 0
        else:
            patience += 1
        if best_score >= score_target or patience >= 8:
            break
    if best_state is None:
        raise RuntimeError("validation did not produce a checkpoint")
    model.load_state_dict(best_state)
    return model, {"config": config.__dict__, "best_validation_score": best_score, "epochs": log, "seed": seed}, log, train_end, validation_end


def train_with_fixed_splits(
    train_history: np.ndarray,
    train_target: np.ndarray,
    validation_history: np.ndarray,
    validation_target: np.ndarray,
    *,
    epochs: int,
    score_target: float,
    seed: int,
) -> tuple[ContextDirectionLstm, dict[str, Any], list[dict[str, Any]]]:
    if len(train_history) < MIN_WINDOWS:
        raise ValueError(f"at least {MIN_WINDOWS} train windows are required")
    if len(validation_history) < 1:
        raise ValueError("at least one validation window is required")
    mean = train_history.reshape(-1, train_history.shape[-1]).mean(axis=0)
    std = np.maximum(train_history.reshape(-1, train_history.shape[-1]).std(axis=0), 1.0e-6)
    config = ContextDirectionConfig(
        input_mean=tuple(float(value) for value in mean),
        input_std=tuple(float(value) for value in std),
    )
    model = ContextDirectionLstm(config)
    optimizer = torch.optim.Adam(model.parameters(), lr=1.0e-3, weight_decay=1.0e-5)
    train_loader = DataLoader(
        TensorDataset(torch.from_numpy(train_history), torch.from_numpy(train_target)),
        batch_size=128,
        shuffle=True,
    )
    validation_loader = DataLoader(
        TensorDataset(torch.from_numpy(validation_history), torch.from_numpy(validation_target)),
        batch_size=256,
    )
    best_state: dict[str, Tensor] | None = None
    best_score = -math.inf
    patience = 0
    log: list[dict[str, Any]] = []
    for epoch in range(1, epochs + 1):
        train_metrics = run_epoch(model, train_loader, optimizer)
        validation_metrics = run_epoch(model, validation_loader, None)
        log.append({"epoch": epoch, "train": train_metrics, "validation": validation_metrics})
        if validation_metrics["score"] > best_score + 1.0e-8:
            best_score = validation_metrics["score"]
            best_state = {key: value.detach().clone() for key, value in model.state_dict().items()}
            patience = 0
        else:
            patience += 1
        if best_score >= score_target or patience >= 8:
            break
    if best_state is None:
        raise RuntimeError("validation did not produce a checkpoint")
    model.load_state_dict(best_state)
    return model, {"config": config.__dict__, "best_validation_score": best_score, "seed": seed}, log


def select_training_seed(
    seeds: list[int] | tuple[int, ...],
    train_candidate: Callable[[int], tuple[ContextDirectionLstm, dict[str, Any], list[dict[str, Any]]]],
    *,
    minimum_completed_seeds: int = 1,
) -> tuple[ContextDirectionLstm, dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Select the highest validation-score candidate and retain every outcome."""

    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("training seeds must be a non-empty sequence of unique integers")
    if minimum_completed_seeds < 1:
        raise ValueError("minimum_completed_seeds must be positive")
    candidates: list[tuple[float, int, ContextDirectionLstm, dict[str, Any], list[dict[str, Any]]]] = []
    ledger: list[dict[str, Any]] = []
    for seed in seeds:
        set_seed(int(seed))
        try:
            model, training, epoch_log = train_candidate(int(seed))
            score = float(training["best_validation_score"])
            if not math.isfinite(score):
                raise ValueError("best validation score is not finite")
            ledger.append(
                {
                    "seed": int(seed),
                    "status": "completed",
                    "best_validation_score": score,
                    "epoch_count": len(epoch_log),
                }
            )
            candidates.append((score, int(seed), model, training, epoch_log))
        except Exception as error:
            ledger.append(
                {
                    "seed": int(seed),
                    "status": "failed",
                    "failure_reason": str(error),
                }
            )
    if not candidates:
        raise RuntimeError("all LSTM training seeds failed")
    if len(candidates) < minimum_completed_seeds:
        raise RuntimeError(
            f"only {len(candidates)} of {minimum_completed_seeds} required LSTM seeds completed"
        )
    score, seed, model, training, epoch_log = max(
        candidates,
        key=lambda item: (item[0], -item[1]),
    )
    selection = {
        "requested_seed_count": len(seeds),
        "completed_seed_count": len(candidates),
        "failed_seed_count": len(seeds) - len(candidates),
        "selected_seed": seed,
        "selected_validation_score": score,
        "selection_rule": "maximum_validation_self_supervised_score; lowest_seed_tiebreak",
        "ledger": ledger,
    }
    training = dict(training)
    training["seed_selection"] = selection
    return model, training, epoch_log, selection


_DIRECTION_AXES = np.asarray(((-1.0, 0.0), (1.0, 0.0), (0.0, 1.0), (0.0, -1.0)), dtype=np.float32)


def direction_logits(predicted: np.ndarray) -> np.ndarray:
    values = np.asarray(predicted, dtype=np.float32)
    if values.ndim != 2 or values.shape[1] != 2:
        raise ValueError("predicted must have shape [N, 2]")
    speed = np.linalg.norm(values, axis=1, keepdims=True)
    normalized = values / np.maximum(speed, 1.0e-8)
    return normalized @ _DIRECTION_AXES.T


def direction_probabilities(predicted: np.ndarray, *, temperature: float = 1.0) -> np.ndarray:
    if not np.isfinite(temperature) or temperature <= 0.0:
        raise ValueError("temperature must be finite and positive")
    logits = direction_logits(predicted).astype(np.float64) / float(temperature)
    logits -= np.max(logits, axis=1, keepdims=True)
    weights = np.exp(logits)
    return weights / np.maximum(np.sum(weights, axis=1, keepdims=True), 1.0e-12)


def _nll_from_logits(logits: np.ndarray, labels: np.ndarray, temperature: float) -> float:
    if len(labels) == 0:
        raise ValueError("at least one calibration label is required")
    scaled = np.asarray(logits, dtype=np.float64) / float(temperature)
    scaled -= np.max(scaled, axis=1, keepdims=True)
    log_normalizer = np.log(np.maximum(np.sum(np.exp(scaled), axis=1), 1.0e-300))
    rows = np.arange(len(labels))
    return float(np.mean(log_normalizer - scaled[rows, labels]))


def fit_temperature(
    predicted: np.ndarray,
    target: np.ndarray,
    *,
    minimum_samples: int = 2,
) -> dict[str, Any]:
    predicted = np.asarray(predicted, dtype=np.float32)
    target = np.asarray(target, dtype=np.float32)
    if predicted.shape != target.shape or predicted.ndim != 2 or predicted.shape[1] != 2:
        raise ValueError("predicted and target must have shape [N, 2]")
    if minimum_samples < 1:
        raise ValueError("minimum calibration samples must be positive")
    target_speed = np.linalg.norm(target, axis=1)
    predicted_speed = np.linalg.norm(predicted, axis=1)
    valid = (target_speed >= MIN_SPEED_MPS) & (predicted_speed >= MIN_SPEED_MPS)
    labels = np.asarray(
        [direction_index(vector, float(speed)) for vector, speed in zip(target, target_speed, strict=True)],
        dtype=object,
    )
    labels = labels[valid].astype(np.int64, copy=False)
    if len(labels) < minimum_samples:
        raise ValueError(
            f"calibration split has {len(labels)} valid direction samples; at least {minimum_samples} are required"
        )
    logits = direction_logits(predicted[valid]).astype(np.float64)
    temperatures = np.exp(np.linspace(np.log(0.05), np.log(20.0), 401))
    losses = np.asarray([_nll_from_logits(logits, labels, float(value)) for value in temperatures])
    best_index = int(np.argmin(losses))
    temperature = float(temperatures[best_index])
    return {
        "status": "fit",
        "method": "temperature_scaling_grid",
        "temperature": temperature,
        "source_split": "calibration",
        "valid_sample_count": int(len(labels)),
        "minimum_sample_count": int(minimum_samples),
        "nll_before": _nll_from_logits(logits, labels, 1.0),
        "nll_after": float(losses[best_index]),
        "valid_sample_definition": "moving_target_and_valid_predicted_direction",
        "independent_from_training_validation_and_test": True,
    }


def _point_metrics(predicted: np.ndarray, target: np.ndarray, *, temperature: float = 1.0) -> dict[str, float]:
    predicted = np.asarray(predicted, dtype=np.float32)
    target = np.asarray(target, dtype=np.float32)
    if predicted.shape != target.shape or predicted.ndim != 2 or predicted.shape[1] != 2:
        raise ValueError("predicted and target must have shape [N, 2]")
    predicted_speed = np.linalg.norm(predicted, axis=1)
    target_speed = np.linalg.norm(target, axis=1)
    truth_labels = [direction_index(vector, speed) for vector, speed in zip(target, target_speed, strict=True)]
    predicted_labels = [direction_index(vector, float(speed)) for vector, speed in zip(predicted, predicted_speed, strict=True)]
    matrix = np.zeros((len(DIRECTION_CLASSES), len(DIRECTION_CLASSES)), dtype=np.int64)
    pairs = [(truth, estimate) for truth, estimate in zip(truth_labels, predicted_labels, strict=True) if truth is not None and estimate is not None]
    for truth, estimate in pairs:
        matrix[truth, estimate] += 1
    f1: list[float] = []
    for index in range(len(DIRECTION_CLASSES)):
        tp = float(matrix[index, index])
        fp = float(matrix[:, index].sum() - tp)
        fn = float(matrix[index, :].sum() - tp)
        precision = tp / max(tp + fp, 1.0e-12)
        recall = tp / max(tp + fn, 1.0e-12)
        f1.append(2.0 * precision * recall / max(precision + recall, 1.0e-12))
    score, speed_score, direction_score = score_components(torch.from_numpy(predicted), torch.from_numpy(target))
    moving = target_speed >= MIN_SPEED_MPS
    valid_prediction = moving & (predicted_speed >= MIN_SPEED_MPS)
    correct = np.asarray(
        [truth == estimate for truth, estimate in zip(truth_labels, predicted_labels, strict=True)],
        dtype=bool,
    )
    direction_accuracy = float(np.mean(correct[valid_prediction])) if np.any(valid_prediction) else 0.0
    probabilities = direction_probabilities(predicted, temperature=temperature)
    one_hot = np.zeros_like(probabilities)
    for row, label in enumerate(truth_labels):
        if label is not None:
            one_hot[row, label] = 1.0
    brier = float(np.mean(np.sum((probabilities[moving] - one_hot[moving]) ** 2, axis=1))) if np.any(moving) else 0.0
    nll = float(
        np.mean(-np.log(np.maximum(probabilities[moving][np.arange(int(np.sum(moving))), np.asarray([label for label in truth_labels if label is not None])], 1.0e-12)))
    ) if np.any(moving) else 0.0
    return {
        "self_supervised_score": float(score.item()),
        "speed_score": float(speed_score.item()),
        "direction_score": float(direction_score.item()),
        "speed_mae_mps": float(np.mean(np.abs(predicted_speed - target_speed))),
        "direction_macro_f1": float(np.mean(f1)),
        "direction_accuracy": direction_accuracy,
        "direction_coverage": float(np.mean(valid_prediction[moving])) if np.any(moving) else 0.0,
        "direction_valid_count": float(np.sum(valid_prediction)),
        "direction_moving_count": float(np.sum(moving)),
        "brier_score": brier,
        "direction_nll": nll,
    }


def bootstrap_intervals(
    predicted: np.ndarray,
    target: np.ndarray,
    *,
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
    temperature: float = 1.0,
) -> dict[str, dict[str, float | int | None]]:
    if replicates < 1:
        raise ValueError("bootstrap replicates must be positive")
    n = len(target)
    if n < 2:
        return {
            name: {"lower": None, "upper": None, "replicates": 0}
            for name in _point_metrics(predicted, target, temperature=temperature)
        }
    rng = np.random.default_rng(seed)
    names = tuple(_point_metrics(predicted, target, temperature=temperature))
    samples = {name: np.empty(replicates, dtype=np.float64) for name in names}
    for replicate in range(replicates):
        indices = rng.integers(0, n, size=n)
        values = _point_metrics(predicted[indices], target[indices], temperature=temperature)
        for name in names:
            samples[name][replicate] = values[name]
    return {
        name: {
            "lower": float(np.percentile(values, 2.5)),
            "upper": float(np.percentile(values, 97.5)),
            "replicates": replicates,
        }
        for name, values in samples.items()
    }


def evaluate_predictions(
    predicted: np.ndarray,
    target: np.ndarray,
    *,
    temperature: float = 1.0,
    calibration_method: str = "none",
    calibration_source_split: str | None = None,
) -> dict[str, Any]:
    predicted = np.asarray(predicted, dtype=np.float32)
    target = np.asarray(target, dtype=np.float32)
    if len(target) == 0:
        raise ValueError("evaluation requires at least one target sample")
    point = _point_metrics(predicted, target, temperature=temperature)
    predicted_speed = np.linalg.norm(predicted, axis=1)
    target_speed = np.linalg.norm(target, axis=1)
    truth_labels = [direction_index(vector, speed) for vector, speed in zip(target, target_speed, strict=True)]
    predicted_labels = [direction_index(vector, float(speed)) for vector, speed in zip(predicted, predicted_speed, strict=True)]
    matrix = np.zeros((len(DIRECTION_CLASSES), len(DIRECTION_CLASSES)), dtype=np.int64)
    pairs = [(truth, estimate) for truth, estimate in zip(truth_labels, predicted_labels, strict=True) if truth is not None and estimate is not None]
    for truth, estimate in pairs:
        matrix[truth, estimate] += 1
    class_metrics: list[dict[str, float | int | str]] = []
    for index, name in enumerate(DIRECTION_CLASSES):
        true_positive = int(matrix[index, index])
        predicted_count = int(matrix[:, index].sum())
        support = int(matrix[index, :].sum())
        precision = true_positive / max(predicted_count, 1)
        recall = true_positive / max(support, 1)
        f1_value = 2.0 * precision * recall / max(precision + recall, 1.0e-12)
        class_metrics.append(
            {
                "class": name,
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1_value),
                "support": support,
            }
        )
    probabilities = direction_probabilities(predicted, temperature=temperature)
    moving = target_speed >= MIN_SPEED_MPS
    valid_prediction = moving & (predicted_speed >= MIN_SPEED_MPS)
    correct = np.asarray(
        [truth == estimate for truth, estimate in zip(truth_labels, predicted_labels, strict=True)],
        dtype=bool,
    )
    confidence = np.max(probabilities, axis=1)
    calibration_correct = correct[valid_prediction]
    calibration_confidence = confidence[valid_prediction]
    bins: list[dict[str, float | int]] = []
    ece = 0.0
    calibration_count = len(calibration_confidence)
    for index in range(10):
        lower = index / 10.0
        upper = (index + 1) / 10.0
        selected = (calibration_confidence >= lower) & (
            calibration_confidence <= upper if index == 9 else calibration_confidence < upper
        )
        count = int(np.sum(selected))
        bin_confidence = float(np.mean(calibration_confidence[selected])) if count else 0.0
        bin_accuracy = float(np.mean(calibration_correct[selected])) if count else 0.0
        ece += (count / calibration_count) * abs(bin_accuracy - bin_confidence) if calibration_count else 0.0
        bins.append({"lower": lower, "upper": upper, "count": count, "confidence": bin_confidence, "accuracy": bin_accuracy})
    return {
        "sample_count": int(len(target)),
        **point,
        "direction_confusion_matrix_rows_truth_columns_prediction": matrix.tolist(),
        "direction_diagnostic_samples": len(pairs),
        "direction_class_metrics": class_metrics,
        "direction_calibration": {
            "scope": "moving_targets_with_valid_direction_prediction",
            "ece_10_bin": float(ece),
            "brier_score_all_moving_targets": point["brier_score"],
            "nll_all_moving_targets": point["direction_nll"],
            "temperature": float(temperature),
            "method": calibration_method,
            "source_split": calibration_source_split,
            "valid_prediction_count": int(point["direction_valid_count"]),
            "moving_target_count": int(point["direction_moving_count"]),
            "reliability_bins": bins,
        },
        "bootstrap_95ci": bootstrap_intervals(predicted, target, temperature=temperature),
        "direction_labels_used_for_training": False,
    }


def predict_velocity(model: ContextDirectionLstm, history: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        prediction = model(torch.from_numpy(history))
    return prediction.context_velocity_xy.cpu().numpy()


def evaluate(
    model: ContextDirectionLstm,
    history: np.ndarray,
    target: np.ndarray,
    *,
    temperature: float = 1.0,
    calibration_method: str = "none",
    calibration_source_split: str | None = None,
) -> dict[str, Any]:
    return evaluate_predictions(
        predict_velocity(model, history),
        target,
        temperature=temperature,
        calibration_method=calibration_method,
        calibration_source_split=calibration_source_split,
    )


def constant_velocity_predictions(history: np.ndarray) -> np.ndarray:
    values = np.asarray(history, dtype=np.float32)
    if values.ndim != 3 or values.shape[-1] < 5:
        raise ValueError("history must have shape [N, steps, 5]")
    return values[:, -1, 2:4].copy()


def kalman_velocity_predictions(
    history: np.ndarray,
    *,
    process_variance: float = 0.01,
    measurement_variance: float = 0.04,
) -> np.ndarray:
    values = np.asarray(history, dtype=np.float32)
    if values.ndim != 3 or values.shape[-1] < 5:
        raise ValueError("history must have shape [N, steps, 5]")
    if process_variance <= 0.0 or measurement_variance <= 0.0:
        raise ValueError("Kalman variances must be positive")
    predictions = np.zeros((len(values), 2), dtype=np.float32)
    process = np.eye(2, dtype=np.float64) * process_variance
    measurement = np.eye(2, dtype=np.float64) * measurement_variance
    identity = np.eye(2, dtype=np.float64)
    for row_index, window in enumerate(values):
        estimate = np.zeros(2, dtype=np.float64)
        covariance = np.eye(2, dtype=np.float64)
        for observation, valid in zip(window[:, 2:4], window[:, 4], strict=True):
            covariance = covariance + process
            if float(valid) < 0.5:
                continue
            innovation_covariance = covariance + measurement
            gain = covariance @ np.linalg.inv(innovation_covariance)
            estimate = estimate + gain @ (observation.astype(np.float64) - estimate)
            covariance = (identity - gain) @ covariance
        predictions[row_index] = estimate.astype(np.float32)
    return predictions


def evaluate_baselines(history: np.ndarray, target: np.ndarray) -> dict[str, dict[str, Any]]:
    return {
        "constant_velocity": evaluate_predictions(constant_velocity_predictions(history), target),
        "kalman_velocity": evaluate_predictions(kalman_velocity_predictions(history), target),
    }


def evaluate_split_windows(
    model: ContextDirectionLstm,
    split_windows: dict[str, tuple[np.ndarray, np.ndarray]],
    *,
    temperature: float = 1.0,
    calibration_method: str = "none",
    calibration_source_split: str | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, dict[str, Any]]]]:
    model_metrics: dict[str, dict[str, Any]] = {}
    baseline_metrics: dict[str, dict[str, dict[str, Any]]] = {}
    for split, (history, target) in split_windows.items():
        model_metrics[split] = evaluate(
            model,
            history,
            target,
            temperature=temperature,
            calibration_method=calibration_method,
            calibration_source_split=calibration_source_split,
        )
        baseline_metrics[split] = evaluate_baselines(history, target)
    return model_metrics, baseline_metrics


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Train and evaluate the CCA context LSTM from real context.csv data")
    parser.add_argument("--input", type=Path, required=True, help="final-run directory or context.csv")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--score-target", type=float, default=float(CONTEXT["score_target"]))
    parser.add_argument("--seed", type=int, default=int(CONTEXT["seed"]))
    parser.add_argument(
        "--seed-count",
        type=int,
        default=1,
        help="independent score-loop seeds; confirmatory runs require at least five",
    )
    parser.add_argument(
        "--split-manifest",
        type=Path,
        help="frozen recording/episode split manifest for independent ID/OOD evaluation",
    )
    parser.add_argument(
        "--simulation-only",
        action="store_true",
        help="allow an explicitly sealed simulation package; never admits hardware evidence",
    )
    args = parser.parse_args()
    if args.epochs < 1 or not 0.0 < args.score_target <= 1.0 or args.seed_count < 1:
        parser.error("epochs/seed-count must be positive and score-target must lie in (0, 1]")
    input_path = args.input.resolve()
    context_path = input_path / "context.csv" if input_path.is_dir() else input_path
    if not context_path.is_file():
        parser.error(f"context.csv not found: {context_path}")
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error(f"output directory must be empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    set_seed(args.seed)
    rows = read_context(context_path)
    split_manifest = load_split_manifest(args.split_manifest.resolve()) if args.split_manifest else None
    if split_manifest is not None and args.seed_count < MIN_TRAINING_SEEDS:
        parser.error(
            f"confirmatory training requires at least {MIN_TRAINING_SEEDS} independent seeds"
        )
    training_seeds = tuple(args.seed + offset for offset in range(args.seed_count))
    input_package_metadata: dict[str, Any] | None = None
    if args.simulation_only and split_manifest is None:
        parser.error("--simulation-only requires --split-manifest")
    if split_manifest is not None:
        if not input_path.is_dir():
            parser.error("confirmatory context input must be a sealed run directory")
        input_package = input_path
        try:
            input_package_metadata = load_confirmatory_capture_manifest(
                input_package,
                context_path,
                allow_simulation=args.simulation_only,
            )
        except (OSError, ValueError) as error:
            parser.error(str(error))
    temperature = 1.0
    calibration_fit: dict[str, Any] = {
        "status": "not_fit",
        "method": "none",
        "temperature": temperature,
        "source_split": None,
        "reason": "a frozen calibration split was not supplied",
        "independent_from_training_validation_and_test": False,
    }
    if split_manifest is None:
        histories, targets, audit = build_windows(rows)
        def train_candidate(seed: int) -> tuple[ContextDirectionLstm, dict[str, Any], list[dict[str, Any]]]:
            model, training, epochs_log, _, _ = train(
                histories,
                targets,
                epochs=args.epochs,
                score_target=args.score_target,
                seed=seed,
            )
            return model, training, epochs_log

        model, training, epochs_log, seed_selection = select_training_seed(
            training_seeds,
            train_candidate,
        )
        train_end = max(1, int(len(histories) * 0.60))
        validation_end = max(train_end + 1, int(len(histories) * 0.80))
        if validation_end >= len(histories):
            validation_end = len(histories) - 1
        split_windows = {
            "validation": (histories[train_end:validation_end], targets[train_end:validation_end]),
            "test": (histories[validation_end:], targets[validation_end:]),
        }
        model_metrics, baseline_metrics = evaluate_split_windows(model, split_windows)
        split_metadata = {
            "train": train_end,
            "validation": validation_end - train_end,
            "test": len(histories) - validation_end,
            "chronological_single_run": True,
            "independent_id_ood_holdout": False,
        }
        split_manifest_metadata = None
    else:
        validate_context_group_metadata(rows)
        split_windows, audit = build_split_windows(rows, split_manifest)
        validate_confirmatory_split_support(split_windows)
        train_history, train_target = split_windows["train"]
        validation_history, validation_target = split_windows["validation"]
        def train_candidate(seed: int) -> tuple[ContextDirectionLstm, dict[str, Any], list[dict[str, Any]]]:
            return train_with_fixed_splits(
                train_history,
                train_target,
                validation_history,
                validation_target,
                epochs=args.epochs,
                score_target=args.score_target,
                seed=seed,
            )

        model, training, epochs_log, seed_selection = select_training_seed(
            training_seeds,
            train_candidate,
            minimum_completed_seeds=MIN_TRAINING_SEEDS,
        )
        calibration_history, calibration_target = split_windows["calibration"]
        calibration_fit = fit_temperature(
            predict_velocity(model, calibration_history),
            calibration_target,
            minimum_samples=MIN_WINDOWS,
        )
        temperature = float(calibration_fit["temperature"])
        model_metrics, baseline_metrics = evaluate_split_windows(
            model,
            split_windows,
            temperature=temperature,
            calibration_method=str(calibration_fit["method"]),
            calibration_source_split="calibration",
        )
        split_metadata = {
            "train_windows": len(train_history),
            "validation_windows": len(validation_history),
            "calibration_windows": len(split_windows["calibration"][0]),
            "test_id_windows": len(split_windows["test_id"][0]),
            "test_ood_windows": len(split_windows["test_ood"][0]),
            "minimum_calibration_test_windows": MIN_WINDOWS,
            "chronological_single_run": False,
            "independent_id_ood_holdout": True,
        }
        try:
            split_manifest_relative = split_manifest["path"].resolve().relative_to(PROJECT_ROOT).as_posix()
        except ValueError as error:
            raise ValueError("split manifest must be inside the project root") from error
        split_manifest_metadata = {
            "schema": SPLIT_SCHEMA,
            "path": split_manifest_relative,
            "sha256": sha256_file(split_manifest["path"]),
            "group_key": split_manifest["group_key"],
            "purposes": list(SPLIT_PURPOSES),
        }
    source_capture_manifest_path: str | None = None
    if input_package_metadata is not None:
        try:
            source_capture_manifest_path = (
                Path(input_package_metadata["path"])
                .resolve()
                .relative_to(PROJECT_ROOT)
                .as_posix()
            )
        except (KeyError, ValueError) as error:
            raise ValueError("confirmatory capture manifest must be inside the project root") from error
    checkpoint = output / "ctx_lstm.pt"
    torch.save(
        {
            "schema": "cca-context-direction-lstm-score-trained-checkpoint-v2",
            "source_context_sha256": sha256_file(context_path),
            "source_capture_manifest_sha256": (
                input_package_metadata["sha256"]
                if input_package_metadata is not None
                else None
            ),
            "source_capture_manifest_path": source_capture_manifest_path,
            "source_calibration_sha256": (
                input_package_metadata["calibration_sha256"]
                if input_package_metadata is not None
                else None
            ),
            "source_capture": (
                input_package_metadata["capture_source"]
                if input_package_metadata is not None
                else None
            ),
            "model_config": training["config"],
            "state_dict": model.state_dict(),
            "direction_classes": DIRECTION_CLASSES,
            "training_mode": "self_supervised_score_loop",
            "direction_labels_used_for_training": False,
            "calibration": calibration_fit,
            "seed_selection": seed_selection,
        },
        checkpoint,
    )
    metrics = {
        "schema": "cca-context-direction-lstm-csv-metrics-v1",
        "status": "candidate-not-evidence",
        "source_context": context_path.as_posix(),
        "source_context_sha256": sha256_file(context_path),
        "window_audit": audit,
        "split": split_metadata,
        "split_manifest": split_manifest_metadata,
        "input_package_manifest": (
            {
                **input_package_metadata,
                "path": input_package_metadata["path"].as_posix(),
            }
            if input_package_metadata is not None
            else None
        ),
        "validation": model_metrics["validation"],
        "test": model_metrics.get("test", model_metrics.get("test_id")),
        "calibration_metrics": model_metrics.get("calibration"),
        "test_id": model_metrics.get("test_id"),
        "test_ood": model_metrics.get("test_ood"),
        "calibration_fit": calibration_fit,
        "baselines": baseline_metrics,
        "seed_selection": seed_selection,
        "direction_labels_used_for_training": False,
        "human_trajectory_generated": False,
        "simulation_only": bool(args.simulation_only),
    }
    write_json(
        output / "training.json",
        {
            "training_mode": "self_supervised_score_loop",
            "score_target": args.score_target,
            "epochs": epochs_log,
            "best_validation_score": training["best_validation_score"],
            "seed": training["seed"],
            "seed_selection": seed_selection,
        },
    )
    write_json(output / "metrics.json", metrics)
    manifest = {
        "schema": "cca-context-direction-lstm-csv-run-manifest-v1",
        "status": "candidate-not-evidence",
        "input_context_csv": context_path.as_posix(),
        "input_context_sha256": sha256_file(context_path),
        "checkpoint_sha256": sha256_file(checkpoint),
        "code_sha256": {
            "scripts/python/tools/ctx_run.py": sha256_file(Path(__file__).resolve()),
            "src/ai/ctx_lstm.py": sha256_file(PROJECT_ROOT / "src/ai/ctx_lstm.py"),
            "configs/study_contract.json": sha256_file(CONTRACT_PATH),
            "schemas/context-split-manifest.schema.json": sha256_file(
                PROJECT_ROOT / "schemas/context-split-manifest.schema.json"
            ),
        },
        "training_mode": "self_supervised_score_loop",
        "simulation_only": bool(args.simulation_only),
        "training_seed_count": seed_selection["requested_seed_count"],
        "completed_seed_count": seed_selection["completed_seed_count"],
        "failed_seed_count": seed_selection["failed_seed_count"],
        "selected_seed": seed_selection["selected_seed"],
        "direction_labels_used_for_training": False,
        "human_trajectory_generated": False,
        "paper_edit": False,
        "hardware_validated": False,
        "split": split_metadata,
        "split_manifest": split_manifest_metadata,
        "input_package_manifest": (
            {
                **input_package_metadata,
                "path": input_package_metadata["path"].as_posix(),
            }
            if input_package_metadata is not None
            else None
        ),
        "metrics": {
            "path": "metrics.json",
            "sha256": sha256_file(output / "metrics.json"),
        },
        "training": {
            "path": "training.json",
            "sha256": sha256_file(output / "training.json"),
        },
        "uncertainty": {
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "confidence_calibration": "direction_probability_reliability_bins_ece_brier_nll",
            "temperature_scaling": calibration_fit,
        },
        "claim_scope": "candidate_context_prediction_only",
    }
    write_json(output / "manifest.json", manifest)
    print(json.dumps({"output": output.as_posix(), "status": manifest["status"], "window_count": audit["window_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
