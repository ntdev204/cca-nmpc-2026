from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from PIL import Image

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT

from repository import validate_web_image_payload


ROOT = PROJECT_ROOT
RESET_HISTORICAL_MANIFEST = Path("research/metadata/web_images/person_context_manifest.json")
RESET_HISTORICAL_ANNOTATIONS = Path("research/metadata/web_images/person_bbox_annotations_20260812.json")
MANIFEST_SCHEMA = Path("schemas/web-image-manifest.schema.json")
ANNOTATION_SCHEMA = Path("schemas/person-bbox-annotation.schema.json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_errors(instance: Any, schema: dict[str, Any], label: str) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [f"{label}:{error.json_path}: {error.message}" for error in sorted(validator.iter_errors(instance), key=lambda item: item.json_path)]


def report_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def validate_annotation_records(
    records: Any,
    source_index: dict[str, dict[str, Any]],
    label: str,
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    errors: list[str] = []
    if not isinstance(records, list):
        return [f"{label}:records must be an array"], {}
    index: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or not record.get("asset_id"):
            continue
        asset_id = str(record["asset_id"])
        if asset_id in index:
            errors.append(f"{label}: duplicate asset_id {asset_id}")
        index[asset_id] = record
    if set(index) != set(source_index):
        errors.append(f"{label}: annotation asset IDs must match web-image manifest exactly")
    for asset_id, record in index.items():
        source = source_index.get(asset_id)
        if source is None:
            continue
        if record.get("image_width") != source.get("width") or record.get("image_height") != source.get("height"):
            errors.append(f"{label}[{asset_id}]: annotation dimensions do not match source media")
        persons = record.get("persons", [])
        if not isinstance(persons, list):
            continue
        for person_index, person in enumerate(persons):
            if not isinstance(person, dict) or not isinstance(person.get("bbox_xyxy"), list):
                continue
            box = person["bbox_xyxy"]
            if len(box) != 4:
                continue
            try:
                x1, y1, x2, y2 = (float(value) for value in box)
            except (TypeError, ValueError):
                continue
            width = float(source["width"])
            height = float(source["height"])
            if not (0.0 <= x1 < x2 <= width and 0.0 <= y1 < y2 <= height):
                errors.append(
                    f"{label}[{asset_id}].persons[{person_index}]: bounding box lies outside source media"
                )
    return errors, index


def manifest_binding_error(
    root: Path,
    source_ref: Any,
    label: str,
    manifest_relative_path: str,
) -> str | None:
    expected_manifest_path = manifest_relative_path
    if not isinstance(source_ref, dict) or source_ref.get("path") != expected_manifest_path:
        return f"{label}.path: annotation is bound to a different web-image manifest"
    if str(source_ref.get("sha256", "")).lower() != sha256_file(root / expected_manifest_path).lower():
        return f"{label}.sha256: annotation source-manifest hash does not match"
    return None


def independent_annotation_gate(
    root: Path,
    annotations: dict[str, Any],
    source_index: dict[str, dict[str, Any]],
    primary_index: dict[str, dict[str, Any]],
    manifest_relative_path: str,
) -> tuple[bool, list[str], dict[str, Any]]:
    errors: list[str] = []
    independent = annotations.get("independent_annotation")
    adjudication = annotations.get("adjudication")
    result: dict[str, Any] = {
        "independent_annotation_present": isinstance(independent, dict),
        "adjudication_present": isinstance(adjudication, dict),
        "independent_annotation_valid": False,
        "adjudication_valid": False,
    }
    independent_index: dict[str, dict[str, Any]] = {}
    if isinstance(independent, dict):
        binding_error = manifest_binding_error(
            root,
            independent.get("source_manifest"),
            "person-bbox-annotation:$.independent_annotation.source_manifest",
            manifest_relative_path,
        )
        if binding_error:
            errors.append(binding_error)
        if independent.get("annotation_id") == annotations.get("annotation_id"):
            errors.append("person-bbox-annotation: independent annotation_id must differ from primary annotation_id")
        if independent.get("annotator_id") == annotations.get("annotator_id"):
            errors.append("person-bbox-annotation: independent annotator_id must differ from primary annotator_id")
        if independent.get("guideline_version") != annotations.get("guideline_version"):
            errors.append("person-bbox-annotation: independent guideline_version must match primary guideline_version")
        record_errors, independent_index = validate_annotation_records(
            independent.get("records"), source_index, "person-bbox-annotation:$.independent_annotation.records"
        )
        errors.extend(record_errors)
        result["independent_record_count"] = len(independent_index)
        result["independent_annotation_valid"] = not binding_error and not record_errors and independent.get("blinded_to_predictions") is True and independent.get("annotation_id") != annotations.get("annotation_id") and independent.get("annotator_id") != annotations.get("annotator_id") and independent.get("guideline_version") == annotations.get("guideline_version")
    if isinstance(adjudication, dict):
        expected_primary_id = annotations.get("annotation_id")
        expected_independent_id = independent.get("annotation_id") if isinstance(independent, dict) else None
        if adjudication.get("primary_annotation_id") != expected_primary_id:
            errors.append("person-bbox-annotation: adjudication primary_annotation_id is not bound to the primary annotation")
        if adjudication.get("independent_annotation_id") != expected_independent_id:
            errors.append("person-bbox-annotation: adjudication independent_annotation_id is not bound to the independent annotation")
        if adjudication.get("adjudicator_id") in {annotations.get("annotator_id"), independent.get("annotator_id") if isinstance(independent, dict) else None}:
            errors.append("person-bbox-annotation: adjudicator_id must be independent of both annotators")
        agreement = adjudication.get("agreement")
        if isinstance(agreement, dict) and agreement.get("asset_count") != len(source_index):
            errors.append("person-bbox-annotation: adjudication agreement.asset_count must cover the complete cohort")
        changed = adjudication.get("changed_asset_ids", [])
        changed_ids = set(changed) if isinstance(changed, list) else set()
        if isinstance(changed, list) and not changed_ids.issubset(source_index):
            errors.append("person-bbox-annotation: adjudication changed_asset_ids contain unknown assets")
        result["adjudication_valid"] = (
            result["independent_annotation_valid"]
            and adjudication.get("status") == "complete"
            and adjudication.get("blinded_to_predictions") is True
            and adjudication.get("primary_annotation_id") == expected_primary_id
            and adjudication.get("independent_annotation_id") == expected_independent_id
            and adjudication.get("adjudicator_id") not in {annotations.get("annotator_id"), independent.get("annotator_id") if isinstance(independent, dict) else None}
            and isinstance(agreement, dict)
            and agreement.get("asset_count") == len(source_index)
            and isinstance(changed, list)
            and changed_ids.issubset(source_index)
        )
    gate = bool(result["independent_annotation_valid"] and result["adjudication_valid"])
    result["gate"] = gate
    result["primary_record_count"] = len(primary_index)
    return gate, errors, result


def run_preflight(root: Path, manifest_path: Path, annotation_path: Path) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    annotations = load_json(annotation_path)
    try:
        manifest_relative_path = manifest_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        manifest_relative_path = manifest_path.resolve().as_posix()
    errors = schema_errors(manifest, load_json(root / MANIFEST_SCHEMA), "manifest")
    errors.extend(schema_errors(annotations, load_json(root / ANNOTATION_SCHEMA), "annotations"))
    errors.extend(
        issue.message
        for issue in validate_web_image_payload(
            root,
            manifest,
            annotation=annotations,
            manifest_relative_path=manifest_relative_path,
        )
    )
    records = manifest.get("records", []) if isinstance(manifest, dict) else []
    asset_ids = [str(record.get("asset_id")) for record in records if isinstance(record, dict)]
    hashes = [str(record.get("sha256")).lower() for record in records if isinstance(record, dict)]
    group_splits: dict[str, set[str]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        group = str(record.get("source_split_group"))
        split = str(record.get("split_eligibility", {}).get("split"))
        group_splits.setdefault(group, set()).add(split)
    if len(asset_ids) != len(set(asset_ids)):
        errors.append("asset_id values are not unique")
    if len(hashes) != len(set(hashes)):
        errors.append("exact duplicate media SHA-256 values are present")
    if any(len(splits) != 1 for splits in group_splits.values()):
        errors.append("a source_split_group spans more than one split")
    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("real_media") is not True or record.get("ai_generated") is not False:
            errors.append(f"media type flags are invalid for {record.get('asset_id')}")
        rights = record.get("license", {})
        if not all(rights.get(field) is True for field in ("download_allowed", "processing_allowed", "derivative_annotation_allowed")):
            errors.append(f"license rights are incomplete for {record.get('asset_id')}")
        privacy = record.get("privacy_review", {})
        if privacy.get("contains_people") is True and not str(privacy.get("ethics_or_legal_basis", "")).strip():
            errors.append(f"privacy/legal basis is missing for {record.get('asset_id')}")
        split = record.get("split_eligibility", {}).get("split")
        if split in {"calibration", "test_id", "test_ood"} and record.get("split_eligibility", {}).get("held_out") is not True:
            errors.append(f"held_out is false for {record.get('asset_id')}")
        local_path = root / str(record.get("local_relative_path", ""))
        if local_path.is_file():
            try:
                with Image.open(local_path) as image:
                    image.verify()
            except (OSError, ValueError) as error:
                errors.append(f"decode failed for {record.get('asset_id')}: {error}")
    source_index = {
        str(record.get("asset_id")): record
        for record in records
        if isinstance(record, dict) and record.get("asset_id")
    }
    approved_count = sum(
        bool(record.get("split_eligibility", {}).get("approved"))
        for record in records
        if isinstance(record, dict)
    )
    annotation_records = annotations.get("records", []) if isinstance(annotations, dict) else []
    annotation_record_errors, annotation_index = validate_annotation_records(
        annotation_records,
        source_index,
        "person-bbox-annotation:$.records",
    )
    errors.extend(annotation_record_errors)
    independent_gate, independent_errors, annotation_gate = independent_annotation_gate(
        root,
        annotations,
        source_index,
        annotation_index,
        manifest_relative_path,
    )
    errors.extend(independent_errors)
    admission_reasons = []
    if approved_count != len(records):
        admission_reasons.append("all calibration/test records remain approved=false")
    if not independent_gate:
        admission_reasons.append("independent second annotator and blinded adjudication record are absent or incomplete")
    admission_reasons.append("pretraining-overlap review is not recorded for the detector")
    admission_reasons.append("cohort expansion and held-out OOD audit remain open")
    return {
        "schema": "cca-pr10-web-cohort-preflight-v1",
        "checked_at_utc": utc_now(),
        "paper_edit": False,
        "status": "PASS" if not errors else "FAIL",
        "admission_status": "BLOCKED" if admission_reasons else "READY_FOR_REVIEW",
        "tool": {
            "path": Path(__file__).resolve().relative_to(root).as_posix(),
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "manifest": {
            "path": report_path(manifest_path, root),
            "sha256": sha256_file(manifest_path),
            "asset_count": len(records),
            "approved_count": approved_count,
            "split_counts": {
                split: sum(1 for record in records if record.get("split_eligibility", {}).get("split") == split)
                for split in ("calibration", "test_id", "test_ood")
            },
        },
        "annotations": {
            "path": report_path(annotation_path, root),
            "sha256": sha256_file(annotation_path),
            "record_count": len(annotation_records),
            "blinded_to_predictions": annotations.get("blinded_to_predictions") is True,
            "annotator_id": annotations.get("annotator_id"),
            "independent_annotation": annotation_gate,
        },
        "checks": {
            "json_schema": not any(item.startswith(("manifest:", "annotations:")) for item in errors),
            "media_hash_size_decode_dimensions": not any("media" in item or "decode" in item for item in errors),
            "annotation_binding_and_bbox_bounds": not any("annotation" in item or "bounding box" in item for item in errors),
            "independent_annotation_and_adjudication": independent_gate,
            "unique_asset_and_sha256": len(asset_ids) == len(set(asset_ids)) and len(hashes) == len(set(hashes)),
            "source_group_split_disjoint": all(len(splits) == 1 for splits in group_splits.values()),
            "real_non_ai_media": all(record.get("real_media") is True and record.get("ai_generated") is False for record in records),
            "rights_and_privacy_fields": all(
                all(record.get("license", {}).get(field) is True for field in ("download_allowed", "processing_allowed", "derivative_annotation_allowed"))
                and (record.get("privacy_review", {}).get("contains_people") is not True or bool(str(record.get("privacy_review", {}).get("ethics_or_legal_basis", "")).strip()))
                for record in records
            ),
        },
        "errors": errors,
        "admission_reasons": admission_reasons,
        "next_actions": ([
            "obtain an independent bbox annotation and blinded adjudication record",
        ] if not independent_gate else []) + [
            "record detector pretraining-overlap review",
            "expand and lock calibration/test_id/test_ood cohort before model selection",
        ],
    }


def run_manifest_only(root: Path, manifest_path: Path) -> dict[str, Any]:
    """Validate a newly acquired manifest without manufacturing annotations."""
    manifest = load_json(manifest_path)
    manifest_relative_path = report_path(manifest_path, root)
    errors = schema_errors(manifest, load_json(root / MANIFEST_SCHEMA), "manifest")
    errors.extend(
        issue.message
        for issue in validate_web_image_payload(
            root,
            manifest,
            manifest_relative_path=manifest_relative_path,
        )
    )
    records = manifest.get("records", []) if isinstance(manifest, dict) else []
    asset_ids = [str(record.get("asset_id")) for record in records if isinstance(record, dict)]
    hashes = [str(record.get("sha256")).lower() for record in records if isinstance(record, dict)]
    group_splits: dict[str, set[str]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        group = str(record.get("source_split_group"))
        split = str(record.get("split_eligibility", {}).get("split"))
        group_splits.setdefault(group, set()).add(split)
    if len(asset_ids) != len(set(asset_ids)):
        errors.append("asset_id values are not unique")
    if len(hashes) != len(set(hashes)):
        errors.append("exact duplicate media SHA-256 values are present")
    if any(len(splits) != 1 for splits in group_splits.values()):
        errors.append("a source_split_group spans more than one split")
    rights_ok = True
    real_media_ok = True
    for record in records:
        if not isinstance(record, dict):
            continue
        real_media_ok = real_media_ok and record.get("real_media") is True and record.get("ai_generated") is False
        rights = record.get("license", {})
        privacy = record.get("privacy_review", {})
        rights_ok = rights_ok and all(
            rights.get(field) is True
            for field in ("download_allowed", "processing_allowed", "derivative_annotation_allowed")
        )
        rights_ok = rights_ok and (
            privacy.get("contains_people") is not True
            or bool(str(privacy.get("ethics_or_legal_basis", "")).strip())
        )
    return {
        "schema": "cca-pr10-web-manifest-acquisition-validation-v1",
        "checked_at_utc": utc_now(),
        "paper_edit": False,
        "status": "PASS" if not errors else "FAIL",
        "admission_status": "BLOCKED",
        "manifest": {
            "path": manifest_relative_path,
            "sha256": sha256_file(manifest_path),
            "asset_count": len(records),
            "approved_count": sum(
                bool(record.get("split_eligibility", {}).get("approved"))
                for record in records
                if isinstance(record, dict)
            ),
        },
        "checks": {
            "json_schema": not any(item.startswith("manifest:") for item in errors),
            "media_hash_size_decode_dimensions": not any(
                item.startswith("web-image-manifest:") for item in errors
            ),
            "unique_asset_and_sha256": len(asset_ids) == len(set(asset_ids)) and len(hashes) == len(set(hashes)),
            "source_group_split_disjoint": all(len(splits) == 1 for splits in group_splits.values()),
            "real_non_ai_media": real_media_ok,
            "rights_and_privacy_fields": rights_ok,
            "annotation_gate": False,
        },
        "errors": errors,
        "admission_reasons": [
            "independent blinded annotation and adjudication are not present",
            "detector pretraining-overlap review is not recorded",
            "cohort expansion and held-out OOD audit remain open",
        ],
        "next_actions": [
            "perform independent blinded person bounding-box annotation",
            "record detector pretraining-overlap review",
            "expand and lock calibration/test_id/test_ood cohort before model selection",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", type=Path, default=ROOT)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--annotations", type=Path)
    parser.add_argument("--manifest-only", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.workspace_root.resolve()
    manifest = (root / args.manifest).resolve()
    if args.manifest_only:
        report = run_manifest_only(root, manifest)
    else:
        if args.annotations is None:
            parser.error("--annotations is required unless --manifest-only is set")
        annotations = (root / args.annotations).resolve()
        report = run_preflight(root, manifest, annotations)
    output = (root / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
