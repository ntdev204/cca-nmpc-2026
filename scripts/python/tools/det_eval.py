from __future__ import annotations

import argparse
import csv
import hashlib
import json
import string
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from ultralytics import YOLO

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT

from shared import is_forbidden_context_field


ROOT = PROJECT_ROOT
CONTEXT_SCHEMA = "cca-context-overlay-v1"
ANNOTATION_SCHEMA = "cca-person-bbox-annotations-v1"
PRESENCE_SCHEMA = "cca-person-presence-annotations-v1"
CONTEXT_DIRECTIONS = {"left", "right", "forward", "backward", "unknown"}
CONTEXT_FIELDS = {
    "asset_id",
    "position_xy",
    "heading_unit",
    "speed_mps",
    "direction",
    "confidence",
    "context_valid",
    "timestamp_ns",
    "frame_id",
    "track_id",
    "coordinate_units",
    "source_sha256",
    "model_sha256",
}
POSE_KEYPOINT_COUNT = 17
BOOTSTRAP_REPLICATES = 400
BOOTSTRAP_SEED = 20260812


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def present(record: dict[str, Any]) -> bool:
    tags = {str(value) for value in record.get("scene_tags", [])}
    if tags & {"person_present", "person_absent"} == {"person_present", "person_absent"}:
        raise ValueError(f"ambiguous presence annotation: {record['asset_id']}")
    if "person_present" in tags:
        return True
    if "person_absent" in tags:
        return False
    raise ValueError(f"missing image-level presence annotation: {record['asset_id']}")


def load_presence_annotations(
    path: Path,
    source_manifest_path: Path,
    source_manifest_relative: str,
    source_records: list[dict[str, Any]],
) -> dict[str, bool]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != PRESENCE_SCHEMA:
        raise ValueError(f"presence annotations must use schema {PRESENCE_SCHEMA}")
    if payload.get("blinded_to_predictions") is not True:
        raise ValueError("presence annotations must be blinded to predictions")
    if not str(payload.get("annotation_status", "")).strip():
        raise ValueError("presence annotations require an annotation_status")
    source_ref = payload.get("source_manifest")
    if not isinstance(source_ref, dict) or source_ref.get("path") != source_manifest_relative:
        raise ValueError("presence annotations are bound to a different source manifest")
    if str(source_ref.get("sha256", "")).lower() != sha256_file(source_manifest_path).lower():
        raise ValueError("presence annotations source-manifest hash does not match")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("presence annotations have no records")
    indexed: dict[str, bool] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("presence annotation records must be objects")
        asset_id = str(record.get("asset_id", ""))
        if not asset_id or asset_id in indexed:
            raise ValueError("presence annotation asset_id must be unique and nonempty")
        value = record.get("person_present")
        if not isinstance(value, bool):
            raise ValueError(f"person_present must be boolean for {asset_id}")
        indexed[asset_id] = value
    expected_ids = {str(record["asset_id"]) for record in source_records}
    if set(indexed) != expected_ids:
        raise ValueError("presence annotations must contain exactly one record per image")
    return indexed


def detector_predictions(result: Any) -> list[dict[str, Any]]:
    if result.boxes is None:
        return []
    if result.keypoints is None:
        raise RuntimeError("YOLO pose output is missing keypoints")
    boxes = result.boxes.xyxy.detach().cpu().numpy()
    confidence = result.boxes.conf.detach().cpu().numpy()
    classes = result.boxes.cls.detach().cpu().numpy()
    keypoint_xy = result.keypoints.xy.detach().cpu().numpy()
    keypoint_confidence_tensor = getattr(result.keypoints, "conf", None)
    if keypoint_confidence_tensor is None:
        keypoint_data = result.keypoints.data.detach().cpu().numpy()
        keypoint_confidence = keypoint_data[..., 2]
    else:
        keypoint_confidence = keypoint_confidence_tensor.detach().cpu().numpy()
    if (
        keypoint_xy.ndim != 3
        or keypoint_xy.shape[1:] != (POSE_KEYPOINT_COUNT, 2)
        or keypoint_confidence.shape != keypoint_xy.shape[:2]
        or len(boxes) != len(keypoint_xy)
    ):
        raise RuntimeError("YOLO pose output does not match the 17-keypoint contract")
    rows = []
    for box, score, class_id, xy, kp_score in zip(
        boxes, confidence, classes, keypoint_xy, keypoint_confidence, strict=True
    ):
        if int(class_id) == 0:
            xy = np.asarray(xy, dtype=np.float64)
            kp_score = np.asarray(kp_score, dtype=np.float64)
            if not np.isfinite(xy).all() or not np.isfinite(kp_score).all():
                raise RuntimeError("YOLO pose output contains non-finite keypoints")
            rows.append(
                {
                    "class": "person",
                    "confidence": float(score),
                    "xyxy": [float(value) for value in box],
                    "keypoints_xy": xy.tolist(),
                    "keypoint_confidence": np.clip(kp_score, 0.0, 1.0).tolist(),
                    "keypoint_valid": (kp_score >= 0.25).tolist(),
                }
            )
    return rows


def _validate_bbox(box: Any, width: int, height: int, label: str) -> list[float]:
    if not isinstance(box, list) or len(box) != 4:
        raise ValueError(f"{label} must be [x1,y1,x2,y2]")
    values = [float(item) for item in box]
    if not np.isfinite(values).all():
        raise ValueError(f"{label} must be finite")
    x1, y1, x2, y2 = values
    if not (0.0 <= x1 < x2 <= width and 0.0 <= y1 < y2 <= height):
        raise ValueError(f"{label} lies outside the image or is degenerate")
    return values


def load_bbox_annotations(
    path: Path,
    source_manifest_path: Path,
    source_manifest_relative: str,
    source_records: list[dict[str, Any]],
) -> dict[str, list[list[float]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != ANNOTATION_SCHEMA:
        raise ValueError(f"bbox annotations must use schema {ANNOTATION_SCHEMA}")
    if payload.get("blinded_to_predictions") is not True:
        raise ValueError("bbox annotations must be blinded to predictions")
    source_ref = payload.get("source_manifest")
    expected_path = source_manifest_relative
    if not isinstance(source_ref, dict) or source_ref.get("path") != expected_path:
        raise ValueError("bbox annotations are bound to a different source manifest")
    if str(source_ref.get("sha256", "")).lower() != sha256_file(source_manifest_path).lower():
        raise ValueError("bbox annotations source-manifest hash does not match")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("bbox annotations have no records")
    indexed: dict[str, list[list[float]]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("bbox annotation records must be objects")
        asset_id = str(record.get("asset_id", ""))
        if not asset_id or asset_id in indexed:
            raise ValueError("bbox annotation asset_id must be unique and nonempty")
        width = int(record.get("image_width", 0))
        height = int(record.get("image_height", 0))
        persons = record.get("persons")
        if width < 1 or height < 1 or not isinstance(persons, list):
            raise ValueError(f"invalid bbox annotation dimensions/persons for {asset_id}")
        indexed[asset_id] = [
            _validate_bbox(item.get("bbox_xyxy"), width, height, f"{asset_id}.bbox")
            for item in persons
            if isinstance(item, dict)
        ]
        if len(indexed[asset_id]) != len(persons):
            raise ValueError(f"bbox annotation persons must be objects for {asset_id}")
    expected_ids = {str(record["asset_id"]) for record in source_records}
    if set(indexed) != expected_ids:
        raise ValueError("bbox annotations must contain exactly one record per image")
    return indexed


def bbox_iou(left: list[float], right: list[float]) -> float:
    x1 = max(left[0], right[0])
    y1 = max(left[1], right[1])
    x2 = min(left[2], right[2])
    y2 = min(left[3], right[3])
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    left_area = max(0.0, left[2] - left[0]) * max(0.0, left[3] - left[1])
    right_area = max(0.0, right[2] - right[0]) * max(0.0, right[3] - right[1])
    union = left_area + right_area - intersection
    return intersection / union if union > 0.0 else 0.0


def aggregate_bbox_metrics(
    evaluated: list[dict[str, Any]],
    annotations: dict[str, list[list[float]]],
    iou_threshold: float,
    minimum_confidence: float = 0.0,
) -> dict[str, Any]:
    if not 0.0 < iou_threshold <= 1.0:
        raise ValueError("IoU threshold must lie in (0, 1]")
    if not 0.0 <= minimum_confidence < 1.0:
        raise ValueError("minimum confidence must lie in [0, 1)")
    ranked: list[tuple[float, str, list[float]]] = []
    total_truth = 0
    matched_ious: list[float] = []
    image_rows: list[dict[str, Any]] = []
    for item in evaluated:
        asset_id = str(item["asset_id"])
        truth = annotations[asset_id]
        predictions = sorted(
            (
                row
                for row in item["predictions"]
                if float(row["confidence"]) >= minimum_confidence
            ),
            key=lambda row: float(row["confidence"]),
            reverse=True,
        )
        total_truth += len(truth)
        used: set[int] = set()
        true_positive = 0
        false_positive = 0
        for prediction in predictions:
            box = [float(value) for value in prediction["xyxy"]]
            ranked.append((float(prediction["confidence"]), asset_id, box))
            candidates = [(bbox_iou(box, target), index) for index, target in enumerate(truth) if index not in used]
            best_iou, best_index = max(candidates, default=(0.0, -1))
            if best_iou >= iou_threshold:
                used.add(best_index)
                true_positive += 1
                matched_ious.append(best_iou)
            else:
                false_positive += 1
        image_rows.append({"asset_id": asset_id, "tp": true_positive, "fp": false_positive, "fn": len(truth) - true_positive})
    ranked.sort(key=lambda row: row[0], reverse=True)
    matched: set[tuple[str, int]] = set()
    tp_curve: list[int] = []
    fp_curve: list[int] = []
    cumulative_tp = 0
    cumulative_fp = 0
    for _, asset_id, box in ranked:
        candidates = [
            (bbox_iou(box, target), index)
            for index, target in enumerate(annotations[asset_id])
            if (asset_id, index) not in matched
        ]
        best_iou, best_index = max(candidates, default=(0.0, -1))
        if best_iou >= iou_threshold:
            matched.add((asset_id, best_index))
            cumulative_tp += 1
        else:
            cumulative_fp += 1
        tp_curve.append(cumulative_tp)
        fp_curve.append(cumulative_fp)
    if total_truth:
        precision_curve = np.asarray(tp_curve, dtype=np.float64) / np.maximum(
            np.asarray(tp_curve) + np.asarray(fp_curve), 1
        )
        recall_curve = np.asarray(tp_curve, dtype=np.float64) / total_truth
        previous_recall = np.concatenate(([0.0], recall_curve[:-1]))
        average_precision = float(np.sum((recall_curve - previous_recall) * precision_curve))
    else:
        average_precision = None
    tp = sum(int(row["tp"]) for row in image_rows)
    fp = sum(int(row["fp"]) for row in image_rows)
    fn = sum(int(row["fn"]) for row in image_rows)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "status": "candidate-not-evidence",
        "iou_threshold": iou_threshold,
        "confidence_threshold": minimum_confidence,
        "image_count": len(evaluated),
        "ground_truth_person_count": total_truth,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "average_precision": average_precision,
        "average_precision_definition": "all_point_recall_precision_area_over_predictions_retained_at_confidence_threshold",
        "mean_matched_iou": float(np.mean(matched_ious)) if matched_ious else None,
        "per_image": image_rows,
    }


def _sha256(value: Any, field: str) -> str:
    digest = str(value)
    if len(digest) != 64 or any(character not in string.hexdigits for character in digest):
        raise ValueError(f"{field} must be a SHA-256 hex digest")
    return digest


def _direction(heading: list[float], valid: bool) -> str:
    if not valid:
        return "unknown"
    x, y = heading
    if abs(x) >= abs(y):
        return "right" if x >= 0.0 else "left"
    return "forward" if y >= 0.0 else "backward"


def _finite_pair(value: Any, field: str, asset_id: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{field} must have two values for {asset_id}")
    try:
        pair = [float(item) for item in value]
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be numeric for {asset_id}") from error
    if not np.isfinite(pair).all():
        raise ValueError(f"invalid {field} for {asset_id}")
    return pair


def load_context_overlay(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != CONTEXT_SCHEMA:
        raise ValueError(f"context overlay must use schema {CONTEXT_SCHEMA}")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("context overlay has no records")
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("context overlay records must be objects")
        asset_id = str(record.get("asset_id", ""))
        if not asset_id or asset_id in indexed:
            raise ValueError("context overlay asset_id must be unique and nonempty")
        forbidden = [key for key in record if is_forbidden_context_field(key)]
        if forbidden:
            raise ValueError("context overlay must contain a current snapshot only")
        unknown = sorted(set(record).difference(CONTEXT_FIELDS))
        if unknown:
            raise ValueError(f"unsupported context overlay fields: {', '.join(unknown)}")
        position = _finite_pair(record.get("position_xy"), "position_xy", asset_id)
        heading = _finite_pair(record.get("heading_unit"), "heading_unit", asset_id)
        valid = record.get("context_valid")
        if not isinstance(valid, bool):
            raise ValueError(f"context_valid must be boolean for {asset_id}")
        speed = float(record.get("speed_mps", -1.0))
        confidence = float(record.get("confidence", -1.0))
        if not np.isfinite(speed) or speed < 0.0 or not np.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise ValueError(f"invalid speed or confidence for {asset_id}")
        heading_norm = float(np.linalg.norm(heading))
        if valid and (speed <= 0.0 or not np.isclose(heading_norm, 1.0, atol=1.0e-6)):
            raise ValueError(f"valid context requires positive speed and unit heading for {asset_id}")
        if not valid and (speed > 1.0e-9 or heading_norm > 1.0e-9):
            raise ValueError(f"invalid context must not carry speed or heading for {asset_id}")
        direction = _direction([float(value) for value in heading], valid)
        declared_direction = str(record.get("direction", direction))
        if declared_direction not in CONTEXT_DIRECTIONS or declared_direction != direction:
            raise ValueError(f"direction does not match heading_unit for {asset_id}")
        frame_id = str(record.get("frame_id", ""))
        units = str(record.get("coordinate_units", ""))
        if not frame_id or not units:
            raise ValueError(f"frame_id and coordinate_units are required for {asset_id}")
        timestamp_ns = int(record.get("timestamp_ns", -1))
        track_id = int(record.get("track_id", -1))
        if timestamp_ns < 0 or track_id < 0:
            raise ValueError(f"invalid timestamp_ns or track_id for {asset_id}")
        indexed[asset_id] = {
            "position_xy": position,
            "heading_unit": heading,
            "speed_mps": speed,
            "direction": direction,
            "confidence": confidence,
            "context_valid": valid,
            "timestamp_ns": timestamp_ns,
            "frame_id": frame_id,
            "track_id": track_id,
            "coordinate_units": units,
            "source_sha256": _sha256(record.get("source_sha256"), "source_sha256"),
            "model_sha256": _sha256(record.get("model_sha256"), "model_sha256"),
        }
    return indexed


def draw_context_overlay(
    image: np.ndarray,
    context: dict[str, Any],
    lstm_path: str | None = None,
) -> np.ndarray:
    x, y = context["position_xy"]
    path_text = str(lstm_path or "<not-provided>")
    path_lines = [path_text[index : index + 84] for index in range(0, len(path_text), 84)] or [path_text]
    lines = [
        f"context={'valid' if context['context_valid'] else 'invalid'} track={context['track_id']}",
        f"pos=({x:.3f},{y:.3f}) {context['coordinate_units']}",
        f"speed={context['speed_mps']:.3f} m/s dir={context['direction']}",
        f"confidence={context['confidence']:.3f} frame={context['frame_id']}",
        f"lstm={context['model_sha256'][:12]} source={context['source_sha256'][:12]}",
    ]
    lines.extend(
        f"LSTM_PATH={path_line}" if index == 0 else f"           {path_line}"
        for index, path_line in enumerate(path_lines)
    )
    result = image.copy()
    for line_index, line in enumerate(lines):
        cv2.putText(result, line, (18, 48 + 22 * line_index), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 220, 0), 2, cv2.LINE_AA)
    return result


def draw_lstm_provenance_overlay(image: np.ndarray, lstm_path: str) -> np.ndarray:
    path_text = str(lstm_path)
    path_lines = [path_text[index : index + 84] for index in range(0, len(path_text), 84)] or [path_text]
    lines = ["context=not-provided (static image)"]
    lines.extend(
        f"LSTM_PATH={path_line}" if index == 0 else f"           {path_line}"
        for index, path_line in enumerate(path_lines)
    )
    result = image.copy()
    for line_index, line in enumerate(lines):
        cv2.putText(result, line, (18, 48 + 22 * line_index), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 220, 0), 2, cv2.LINE_AA)
    return result


def aggregate_presence_metrics(
    evaluated: list[dict[str, Any]],
    confidence: float,
) -> dict[str, Any]:
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie in (0, 1)")
    tp = sum(
        bool(item["ground_truth_person_present"])
        and any(float(row["confidence"]) >= confidence for row in item["predictions"])
        for item in evaluated
    )
    tn = sum(
        not bool(item["ground_truth_person_present"])
        and not any(float(row["confidence"]) >= confidence for row in item["predictions"])
        for item in evaluated
    )
    fp = sum(
        not bool(item["ground_truth_person_present"])
        and any(float(row["confidence"]) >= confidence for row in item["predictions"])
        for item in evaluated
    )
    fn = sum(
        bool(item["ground_truth_person_present"])
        and not any(float(row["confidence"]) >= confidence for row in item["predictions"])
        for item in evaluated
    )
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "confidence_threshold": confidence,
        "image_count": len(evaluated),
        "positive_count": sum(bool(item["ground_truth_person_present"]) for item in evaluated),
        "negative_count": sum(not bool(item["ground_truth_person_present"]) for item in evaluated),
        "confusion_matrix": {
            "labels": ["negative", "positive"],
            "rows_ground_truth_columns_prediction": [[tn, fp], [fn, tp]],
        },
        "accuracy": (tp + tn) / len(evaluated) if evaluated else 0.0,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1,
    }


def bootstrap_presence_intervals(
    evaluated: list[dict[str, Any]],
    confidence: float,
    *,
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, dict[str, float | int]]:
    if not evaluated or replicates < 1:
        raise ValueError("presence bootstrap requires images and positive replicates")
    rng = np.random.default_rng(seed)
    names = ("accuracy", "precision", "recall", "specificity", "f1")
    samples = {name: np.empty(replicates, dtype=np.float64) for name in names}
    for index in range(replicates):
        indices = rng.integers(0, len(evaluated), size=len(evaluated))
        metrics = aggregate_presence_metrics([evaluated[item] for item in indices], confidence)
        for name in names:
            samples[name][index] = float(metrics[name])
    return {
        name: {
            "lower": float(np.percentile(values, 2.5)),
            "upper": float(np.percentile(values, 97.5)),
            "replicates": int(replicates),
            "image_count": int(len(evaluated)),
            "confidence_level": 0.95,
        }
        for name, values in samples.items()
    }


def bootstrap_bbox_intervals(
    evaluated: list[dict[str, Any]],
    annotations: dict[str, list[list[float]]],
    iou_threshold: float,
    minimum_confidence: float = 0.0,
    *,
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, dict[str, float | int]]:
    if not evaluated or replicates < 1:
        raise ValueError("bbox bootstrap requires images and positive replicates")
    base = aggregate_bbox_metrics(evaluated, annotations, iou_threshold, minimum_confidence)
    image_rows = list(base["per_image"])
    rng = np.random.default_rng(seed)
    names = ("precision", "recall", "f1")
    samples = {name: np.empty(replicates, dtype=np.float64) for name in names}
    for index in range(replicates):
        selected = [image_rows[item] for item in rng.integers(0, len(image_rows), size=len(image_rows))]
        tp = sum(int(row["tp"]) for row in selected)
        fp = sum(int(row["fp"]) for row in selected)
        fn = sum(int(row["fn"]) for row in selected)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        samples["precision"][index] = precision
        samples["recall"][index] = recall
        samples["f1"][index] = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        name: {
            "lower": float(np.percentile(values, 2.5)),
            "upper": float(np.percentile(values, 97.5)),
            "replicates": int(replicates),
            "image_count": int(len(evaluated)),
            "confidence_level": 0.95,
        }
        for name, values in samples.items()
    }


def evaluate(
    root: Path,
    manifest_path: Path,
    weights_path: Path,
    output: Path,
    confidence: float,
    device: str,
    context_path: Path | None = None,
    lstm_path: Path | None = None,
    annotations_path: Path | None = None,
    presence_path: Path | None = None,
    iou_threshold: float = 0.5,
) -> None:
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie in (0, 1)")
    if not 0.0 < iou_threshold <= 1.0:
        raise ValueError("IoU threshold must lie in (0, 1]")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = manifest.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("web manifest has no records")
    context_records = load_context_overlay(context_path) if context_path is not None else {}
    lstm_checkpoint = lstm_path.resolve() if lstm_path is not None else None
    lstm_checkpoint_sha256 = None
    if lstm_checkpoint is not None:
        if not lstm_checkpoint.is_file():
            raise FileNotFoundError(lstm_checkpoint)
        lstm_checkpoint_sha256 = sha256_file(lstm_checkpoint)
        mismatched_assets = [
            asset_id
            for asset_id, context in context_records.items()
            if str(context["model_sha256"]).lower() != lstm_checkpoint_sha256.lower()
        ]
        if mismatched_assets:
            raise ValueError(
                "LSTM checkpoint hash does not match context overlay for: "
                + ", ".join(sorted(mismatched_assets))
            )
    annotations = (
        load_bbox_annotations(
            annotations_path,
            manifest_path,
            manifest_path.relative_to(root).as_posix(),
            records,
        )
        if annotations_path is not None
        else None
    )
    presence_records = (
        load_presence_annotations(
            presence_path,
            manifest_path,
            manifest_path.relative_to(root).as_posix(),
            records,
        )
        if presence_path is not None
        else None
    )
    manifest_asset_ids = {str(record["asset_id"]) for record in records}
    if context_records and set(context_records) != manifest_asset_ids:
        raise ValueError("context overlay must contain exactly one record per image asset")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"output is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    for record in records:
        path = root / str(record["local_relative_path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        if sha256_file(path).lower() != str(record["sha256"]).lower():
            raise ValueError(f"media hash mismatch: {path}")
    if not weights_path.is_file():
        raise FileNotFoundError(weights_path)
    model_hash = sha256_file(weights_path)
    detector = YOLO(str(weights_path), task="pose")
    evaluated: list[dict[str, Any]] = []
    latency: list[float] = []
    gallery = output / "gallery"
    gallery.mkdir()
    for index, record in enumerate(records):
        path = root / str(record["local_relative_path"])
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"cannot decode image: {path}")
        started = time.perf_counter_ns()
        result = detector.predict(image, conf=0.01, device=device, verbose=False)[0]
        elapsed_ms = (time.perf_counter_ns() - started) / 1.0e6
        predictions = detector_predictions(result)
        truth = (
            presence_records[str(record["asset_id"])]
            if presence_records is not None
            else present(record)
        )
        prediction = any(item["confidence"] >= confidence for item in predictions)
        evaluated.append(
            {
                "asset_id": record["asset_id"],
                "source_id": record["source_id"],
                "split": record["split_eligibility"]["split"],
                "ground_truth_person_present": truth,
                "predicted_person_present": prediction,
                "predictions": predictions,
                "latency_ms": float(elapsed_ms),
                "source_sha256": record["sha256"],
                "context": context_records.get(record["asset_id"]),
            }
        )
        latency.append(float(elapsed_ms))
        overlay = result.plot()
        label = f"gt={'person' if truth else 'empty'} pred={'person' if prediction else 'empty'}"
        cv2.putText(overlay, label, (18, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
        if record["asset_id"] in context_records:
            overlay = draw_context_overlay(
                overlay,
                context_records[record["asset_id"]],
                lstm_checkpoint.as_posix() if lstm_checkpoint is not None else None,
            )
        elif lstm_checkpoint is not None:
            overlay = draw_lstm_provenance_overlay(overlay, lstm_checkpoint.as_posix())
        if not cv2.imwrite(str(gallery / f"{index:02d}-{record['asset_id']}.jpg"), overlay):
            raise OSError(f"cannot write overlay for {record['asset_id']}")
    metrics = aggregate_presence_metrics(evaluated, confidence)
    metrics.update({
        "status": "candidate-not-evidence",
        "confidence_sweep": [aggregate_presence_metrics(evaluated, threshold) for threshold in (0.10, 0.25, 0.50, 0.75)],
        "latency_ms": {
            "p50": float(np.percentile(latency, 50)),
            "p95": float(np.percentile(latency, 95)),
            "max": float(np.max(latency)),
        },
        "box_metrics": (
            aggregate_bbox_metrics(evaluated, annotations, iou_threshold, confidence)
            if annotations is not None
            else "not_available_without_blind_bbox_annotations"
        ),
        "presence_annotation_status": (
            json.loads(presence_path.read_text(encoding="utf-8")).get("annotation_status")
            if presence_path is not None
            else "manifest_scene_tags"
        ),
        "statistics": {
            "unit": "image",
            "method": "nonparametric_bootstrap",
            "confidence_level": 0.95,
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "descriptive_only": True,
        },
        "presence_bootstrap_95ci": bootstrap_presence_intervals(
            evaluated,
            confidence,
        ),
    })
    if annotations is not None:
        metrics["box_confidence_sweep"] = [
            aggregate_bbox_metrics(evaluated, annotations, iou_threshold, threshold)
            for threshold in (0.10, 0.25, 0.50, 0.75)
        ]
        metrics["box_bootstrap_95ci"] = bootstrap_bbox_intervals(
            evaluated,
            annotations,
            iou_threshold,
            confidence,
        )
    write_json(output / "predictions.json", {"status": metrics["status"], "records": evaluated})
    write_json(output / "metrics.json", metrics)
    confusion = metrics["confusion_matrix"]["rows_ground_truth_columns_prediction"]
    with (output / "confusion_matrix.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["ground_truth\\prediction", "negative", "positive"])
        writer.writerow(["negative", confusion[0][0], confusion[0][1]])
        writer.writerow(["positive", confusion[1][0], confusion[1][1]])
    with (output / "latency.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["asset_id", "latency_ms"])
        writer.writerows((item["asset_id"], item["latency_ms"]) for item in evaluated)
    write_json(
        output / "manifest.json",
        {
            "schema": "cca-yolo26s-pose-web-image-evaluation-v1",
            "status": metrics["status"],
            "created_at_utc": utc_now(),
            "paper_edit": False,
            "real_media_hashes_verified": True,
            "manifest_source": {"path": manifest_path.relative_to(root).as_posix(), "sha256": sha256_file(manifest_path)},
            "tool": {"path": Path(__file__).resolve().relative_to(root).as_posix(), "sha256": sha256_file(Path(__file__).resolve())},
            "model": {
                "name": "yolo26s-pose",
                "task": "pose",
                "person_class_id": 0,
                "keypoint_count": POSE_KEYPOINT_COUNT,
                "path": weights_path.relative_to(root).as_posix(),
                "sha256": model_hash,
            },
            "device": device,
            "context_overlay": (
                {
                    "schema": CONTEXT_SCHEMA,
                    "path": context_path.relative_to(root).as_posix(),
                    "sha256": sha256_file(context_path),
                    "current_snapshot_only": True,
                    "human_trajectory_overlay": False,
                    "robot_local_path_overlay": False,
                    "lstm_checkpoint": (
                        {
                            "path": lstm_checkpoint.relative_to(root).as_posix()
                            if lstm_checkpoint.is_relative_to(root)
                            else lstm_checkpoint.as_posix(),
                            "sha256": lstm_checkpoint_sha256,
                        }
                        if lstm_checkpoint is not None
                        else {"status": "not-provided"}
                    ),
                }
                if context_path is not None
                else {
                    "status": "not-provided",
                    "human_trajectory_overlay": False,
                    "robot_local_path_overlay": False,
                    "lstm_checkpoint": (
                        {
                            "path": lstm_checkpoint.relative_to(root).as_posix()
                            if lstm_checkpoint.is_relative_to(root)
                            else lstm_checkpoint.as_posix(),
                            "sha256": lstm_checkpoint_sha256,
                        }
                        if lstm_checkpoint is not None
                        else {"status": "not-provided"}
                    ),
                }
            ),
            "bbox_annotations": (
                {
                    "schema": ANNOTATION_SCHEMA,
                    "path": annotations_path.relative_to(root).as_posix(),
                    "sha256": sha256_file(annotations_path),
                    "blinded_to_predictions": True,
                    "confidence_threshold": confidence,
                    "iou_threshold": iou_threshold,
                    "metrics_available": True,
                }
                if annotations_path is not None
                else {
                    "status": "not-provided",
                    "blinded_to_predictions": False,
                    "metrics_available": False,
                }
            ),
            "presence_annotations": (
                {
                    "schema": PRESENCE_SCHEMA,
                    "path": presence_path.relative_to(root).as_posix(),
                    "sha256": sha256_file(presence_path),
                    "blinded_to_predictions": True,
                    "annotation_status": json.loads(presence_path.read_text(encoding="utf-8")).get("annotation_status"),
                }
                if presence_path is not None
                else {"status": "not-provided"}
            ),
            "statistics": metrics["statistics"],
            "metrics": {"path": "metrics.json", "sha256": sha256_file(output / "metrics.json")},
            "predictions": {"path": "predictions.json", "sha256": sha256_file(output / "predictions.json")},
            "confusion_matrix": {"path": "confusion_matrix.csv", "sha256": sha256_file(output / "confusion_matrix.csv")},
            "latency": {"path": "latency.csv", "sha256": sha256_file(output / "latency.csv")},
            "claim_scope": (
                "real_internet_images_image_level_presence_blind_bbox_diagnostics_and_context_overlay"
                if context_path is not None and annotations_path is not None
                else "real_internet_images_image_level_presence_annotation_candidate_and_context_overlay"
                if context_path is not None and presence_path is not None
                else "real_internet_images_image_level_presence_and_blind_bbox_diagnostics"
                if annotations_path is not None
                else "real_internet_images_image_level_presence_annotation_candidate"
                if presence_path is not None
                else "real_internet_images_image_level_presence_and_context_overlay"
                if context_path is not None
                else "real_internet_images_image_level_presence_and_lstm_provenance_overlay"
                if lstm_checkpoint is not None
                else "real_internet_images_image_level_presence_only"
            ),
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", type=Path, default=ROOT)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--context", type=Path, default=None)
    parser.add_argument("--lstm-checkpoint", type=Path, default=None)
    parser.add_argument("--annotations", type=Path, default=None)
    parser.add_argument("--presence-annotations", type=Path, default=None)
    parser.add_argument("--iou-threshold", type=float, default=0.5)
    arguments = parser.parse_args()
    root = arguments.workspace_root.resolve()
    manifest = (root / arguments.manifest).resolve()
    weights = (root / arguments.weights).resolve()
    output = (root / arguments.output).resolve()
    context = (root / arguments.context).resolve() if arguments.context is not None else None
    lstm_checkpoint = (root / arguments.lstm_checkpoint).resolve() if arguments.lstm_checkpoint is not None else None
    annotations = (root / arguments.annotations).resolve() if arguments.annotations is not None else None
    presence = (root / arguments.presence_annotations).resolve() if arguments.presence_annotations is not None else None
    evaluate(
        root,
        manifest,
        weights,
        output,
        arguments.confidence,
        arguments.device,
        context,
        lstm_checkpoint,
        annotations,
        presence,
        arguments.iou_threshold,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
