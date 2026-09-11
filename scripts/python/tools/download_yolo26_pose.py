#!/usr/bin/env python3
"""Fetch the declared YOLO26s-pose checkpoint and optionally export TensorRT.

The weight file is intentionally ignored by Git.  This tool leaves a small
JSON sidecar with the source URL and SHA-256 so a Jetson deployment can be
verified without committing the binary model to the repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path


MODEL_NAME = "yolo26s-pose"
MODEL_URL = "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26s-pose.pt"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        print(f"Downloading {url}")
        with urllib.request.urlopen(url, timeout=60) as response, temporary.open("wb") as stream:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                stream.write(block)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("models/yolo26s-pose.pt"),
        help="checkpoint path (default: models/yolo26s-pose.pt)",
    )
    parser.add_argument("--url", default=MODEL_URL)
    parser.add_argument(
        "--export-engine",
        action="store_true",
        help="export a TensorRT engine after loading the checkpoint",
    )
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="0")
    args = parser.parse_args()

    if not args.output.is_file():
        download(args.url, args.output)
    digest = sha256(args.output)
    manifest = {
        "schema": "cca-yolo26s-pose-runtime-v1",
        "model_name": MODEL_NAME,
        "task": "pose",
        "format": "pt",
        "path": str(args.output),
        "source_url": args.url,
        "sha256": digest,
        "keypoint_count": 17,
        "pretrained_checkpoint_only": True,
    }

    if args.export_engine:
        try:
            from ultralytics import YOLO
        except Exception as error:
            print(f"Ultralytics is required for TensorRT export: {error}", file=sys.stderr)
            return 2
        model = YOLO(str(args.output))
        exported = model.export(format="engine", imgsz=args.imgsz, device=args.device, nms=False)
        engine = Path(str(exported))
        manifest["engine_path"] = str(engine)
        manifest["engine_sha256"] = sha256(engine)
        manifest["format"] = "tensorrt_engine"

    manifest_path = args.output.with_suffix(args.output.suffix + ".json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
