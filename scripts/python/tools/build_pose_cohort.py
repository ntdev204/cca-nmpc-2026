from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone

UTC = timezone.utc
from pathlib import Path

import cv2

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT


SOURCE_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/coco8-pose.zip"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_boxes(label_path: Path, width: int, height: int) -> list[dict[str, list[float]]]:
    persons = []
    for line in label_path.read_text(encoding="utf-8").splitlines():
        values = [float(item) for item in line.split()]
        if len(values) < 5 or int(values[0]) != 0:
            continue
        _, cx, cy, box_width, box_height = values[:5]
        x1 = max(0.0, (cx - box_width / 2.0) * width)
        y1 = max(0.0, (cy - box_height / 2.0) * height)
        x2 = min(float(width), (cx + box_width / 2.0) * width)
        y2 = min(float(height), (cy + box_height / 2.0) * height)
        if x1 >= x2 or y1 >= y2:
            raise ValueError(f"degenerate box in {label_path}")
        persons.append({"bbox_xyxy": [x1, y1, x2, y2]})
    return persons


def build(root: Path, dataset_root: Path, manifest_path: Path, annotation_path: Path) -> None:
    image_root = dataset_root / "coco8-pose" / "images" / "val"
    label_root = dataset_root / "coco8-pose" / "labels" / "val"
    images = sorted(image_root.glob("*.jpg"))
    if not images:
        raise ValueError(f"no validation images found under {image_root}")
    retrieved_at = utc_now()
    records = []
    annotations = []
    for image_path in images:
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"cannot decode {image_path}")
        height, width = image.shape[:2]
        stem = image_path.stem
        image_id = int(stem)
        asset_id = f"asset-coco8-pose-{stem}"
        source_id = f"source-coco2017-{image_id}"
        local_path = image_path.relative_to(root).as_posix()
        records.append(
            {
                "asset_id": asset_id,
                "source_id": source_id,
                "landing_url": f"https://cocodataset.org/#explore?id={image_id}",
                "download_url": SOURCE_URL,
                "retrieved_at_utc": retrieved_at,
                "http_etag": None,
                "sha256": sha256_file(image_path),
                "byte_size": image_path.stat().st_size,
                "mime": "image/jpeg",
                "width": width,
                "height": height,
                "fps": None,
                "local_relative_path": local_path,
                "license": {
                    "name": "COCO image terms; local candidate processing",
                    "url": "https://cocodataset.org/#termsofuse",
                    "checked_at_utc": retrieved_at,
                    "download_allowed": True,
                    "processing_allowed": True,
                    "derivative_annotation_allowed": True,
                    "notes": "The subset is distributed by Ultralytics; per-image rights and privacy release remain under review.",
                },
                "creator": "COCO Consortium; Ultralytics COCO8-pose subset",
                "required_attribution": "COCO Consortium and Ultralytics; local evaluation only",
                "source_split_group": "coco2017-val",
                "real_media": True,
                "ai_generated": False,
                "redistribution_allowed": False,
                "annotation_status": "annotated",
                "reviewer_id": "coco8-pose-provider",
                "privacy_review": {
                    "contains_people": True,
                    "face_handling": "retained_with_basis",
                    "reviewed_at_utc": retrieved_at,
                    "ethics_or_legal_basis": "Public COCO subset; local identity-free evaluation only; release decision pending.",
                    "notes": "Candidate public ground truth; no identity or biometric labels.",
                },
                "split_eligibility": {"split": "test_id", "held_out": True, "approved": False},
                "scene_tags": ["public_ground_truth", "person_present", "pose", "test_id"],
            }
        )
        annotations.append(
            {
                "asset_id": asset_id,
                "image_width": width,
                "image_height": height,
                "persons": parse_boxes(label_root / f"{stem}.txt", width, height),
            }
        )
    write_json(
        manifest_path,
        {
            "schema_version": "2.0.0",
            "dataset_id": "ds-coco8-pose-ground-truth-20260814",
            "created_at_utc": retrieved_at,
            "records": records,
        },
    )
    source_hash = sha256_file(manifest_path)
    write_json(
        annotation_path,
        {
            "schema": "cca-person-bbox-annotations-v1",
            "schema_version": "1.0.0",
            "annotation_id": "ann-coco8-pose-provider-20260814",
            "source_manifest": {"path": manifest_path.relative_to(root).as_posix(), "sha256": source_hash},
            "guideline_version": "coco8-pose-official-boxes-v1",
            "blinded_to_predictions": True,
            "annotator_id": "coco8-pose-provider",
            "records": annotations,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    args = parser.parse_args()
    root = args.workspace_root.resolve()
    build(root, (root / args.dataset_root).resolve(), (root / args.manifest).resolve(), (root / args.annotations).resolve())
    print((root / args.manifest).resolve())
    print((root / args.annotations).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
