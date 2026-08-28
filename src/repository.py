from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from PIL import Image


JSON_INSTANCE_SCHEMAS = {
    "data/registry.json": "dataset-registry.schema.json",
    "models/registry.json": "model-registry.schema.json",
    "experiments/registry.json": "experiment-registry.schema.json",
    "artifacts/registry.json": "artifact-registry.schema.json",
    "configs/physical_robot.json": "physical-robot.schema.json",
    # Historical PR01 records remain hash- and schema-checked for provenance.
    # Retired focused-audit and claim-matrix records are not active instances.
    "research/metadata/pr01_gap_decision.json": "pr01-gap-decision.schema.json",
    "research/metadata/pr01_search_manifest.json": "pr01-search-manifest.schema.json",
    "research/metadata/pr01_raw_search_export_manifest.json": "pr01-raw-search-export-manifest.schema.json",
    "references/zotero/import_queue/source_manifest.json": "zotero-source-manifest.schema.json",
    "references/zotero/export/receipt.json": "zotero-export-receipt.schema.json",
}

YAML_INSTANCE_SCHEMAS = {
    "configs/dataset.template.yaml": "dataset-config.schema.json",
    "configs/simulation.template.yaml": "simulation-config.schema.json",
    "configs/evaluation.template.yaml": "evaluation-config.schema.json",
    "configs/physical_experiment.template.yaml": "physical-experiment-config.schema.json",
}

WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")
SHA256_PATTERN = re.compile(r"^[A-Fa-f0-9]{64}$")
BIBTEX_ENTRY_PATTERN = re.compile(
    r"(?m)^@(?!(?:comment|preamble|string)\b)[A-Za-z][A-Za-z0-9_-]*\s*[({]",
    re.IGNORECASE,
)
BIBTEX_LOCAL_FILE_FIELD_PATTERN = re.compile(r"(?im)^\s*(?:file|attachment)\s*=")
BIBTEX_DOI_FIELD_PATTERN = re.compile(
    r'(?im)^\s*doi\s*=\s*(?:\{([^}]*)\}|"([^"]*)"|([^,\r\n]+))\s*,?\s*$'
)
ZOTERO_SOURCE_MANIFEST_PATH = "references/zotero/import_queue/source_manifest.json"
ZOTERO_RECEIPT_PATH = "references/zotero/export/receipt.json"
ZOTERO_BIBTEX_PATH = "references/zotero/export/library.bib"
ZOTERO_BIBTEX_TRANSFORMATION = (
    "Exported by the Zotero local API; machine-local file fields removed."
)
PR01_SEARCH_MANIFEST_PATH = "research/metadata/pr01_search_manifest.json"
PR01_RAW_SEARCH_EXPORT_MANIFEST_PATH = (
    "research/metadata/pr01_raw_search_export_manifest.json"
)
PR01_REQUIRED_DATABASE_IDS = {
    "crossref",
    "ieee-xplore",
    "scopus",
    "semantic-scholar",
    "web-of-science",
}
PR01_MINIMUM_EXECUTION_DATABASE_IDS = {
    "crossref",
    "ieee-xplore",
    "semantic-scholar",
}
PR01_REQUIRED_CONCEPT_BLOCKS = {
    "adaptive-risk",
    "chance-risk-human",
    "context-human-nmpc",
    "elastic-chance",
    "lstm-trajectory",
    "mecanum-dynamics",
}
PR01_FORBIDDEN_PLACEHOLDERS = ("[START_YEAR]", "[FREEZE_DATE]", "TBD", "TODO")


class DuplicateJsonKeyError(ValueError):
    """Raised when JSON input contains an ambiguous duplicate object key."""


@dataclass(frozen=True)
class ValidationIssue:
    location: str
    message: str


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateJsonKeyError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def load_json_strict(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)


def _json_path(parts: Any) -> str:
    rendered = "$"
    for part in parts:
        rendered += f"[{part}]" if isinstance(part, int) else f".{part}"
    return rendered


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalize_doi(value: str) -> str:
    normalized = value.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if normalized.startswith(prefix):
            normalized = normalized.removeprefix(prefix).strip()
    return normalized.rstrip(".")


def _bibtex_dois(text: str) -> list[str]:
    values: list[str] = []
    for match in BIBTEX_DOI_FIELD_PATTERN.finditer(text):
        raw = next(group for group in match.groups() if group is not None)
        values.append(_normalize_doi(raw))
    return values


def _schema_issues(instance: Any, schema: dict[str, Any], label: str) -> list[ValidationIssue]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        ValidationIssue(f"{label}:{_json_path(error.absolute_path)}", error.message)
        for error in sorted(
            validator.iter_errors(instance),
            key=lambda item: _json_path(item.absolute_path),
        )
    ]


def _walk_file_references(value: Any, location: str = "$") -> list[tuple[str, dict[str, str]]]:
    references: list[tuple[str, dict[str, str]]] = []
    if isinstance(value, dict):
        if set(value) == {"path", "sha256"} and isinstance(value.get("path"), str):
            references.append((location, value))
        for key, nested in value.items():
            references.extend(_walk_file_references(nested, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            references.extend(_walk_file_references(nested, f"{location}[{index}]"))
    return references


def _file_reference_issues(
    repository_root: Path,
    instance: Any,
    label: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    root = repository_root.resolve()
    for location, reference in _walk_file_references(instance):
        relative = Path(reference["path"])
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            issues.append(
                ValidationIssue(f"{label}:{location}", "file reference escapes repository")
            )
            continue
        if not candidate.is_file():
            issues.append(
                ValidationIssue(f"{label}:{location}", f"referenced file is absent: {relative}")
            )
            continue
        expected = reference.get("sha256")
        if not isinstance(expected, str) or not SHA256_PATTERN.fullmatch(expected):
            issues.append(ValidationIssue(f"{label}:{location}", "invalid SHA-256 value"))
        elif _sha256_file(candidate).lower() != expected.lower():
            issues.append(ValidationIssue(f"{label}:{location}", f"SHA-256 mismatch: {relative}"))
    return issues


def validate_web_image_payload(
    repository_root: Path,
    manifest: dict[str, Any],
    *,
    annotation: dict[str, Any] | None = None,
    manifest_relative_path: str = "research/metadata/web_images/person_context_manifest.json",
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    root = repository_root.resolve()
    records = manifest.get("records") if isinstance(manifest, dict) else None
    if not isinstance(records, list):
        return issues
    indexed: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        asset_id = str(record.get("asset_id", ""))
        if not asset_id:
            continue
        indexed[asset_id] = record
        relative = record.get("local_relative_path")
        if not isinstance(relative, str):
            continue
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            issues.append(ValidationIssue(
                f"web-image-manifest:$.records[{index}].local_relative_path",
                "media path escapes repository",
            ))
            continue
        if not candidate.is_file():
            issues.append(ValidationIssue(
                f"web-image-manifest:$.records[{index}].local_relative_path",
                f"media file is absent: {relative}",
            ))
            continue
        actual_bytes = candidate.stat().st_size
        if actual_bytes != record.get("byte_size"):
            issues.append(ValidationIssue(
                f"web-image-manifest:$.records[{index}].byte_size",
                f"media byte size mismatch: {relative}",
            ))
        expected_hash = str(record.get("sha256", "")).lower()
        if expected_hash and _sha256_file(candidate).lower() != expected_hash:
            issues.append(ValidationIssue(
                f"web-image-manifest:$.records[{index}].sha256",
                f"media SHA-256 mismatch: {relative}",
            ))
        try:
            with Image.open(candidate) as image:
                width, height = image.size
                image.verify()
        except (OSError, ValueError) as error:
            issues.append(ValidationIssue(
                f"web-image-manifest:$.records[{index}].local_relative_path",
                f"media cannot be decoded: {error}",
            ))
            continue
        if width != record.get("width") or height != record.get("height"):
            issues.append(ValidationIssue(
                f"web-image-manifest:$.records[{index}]",
                f"media dimensions mismatch: {relative}",
            ))
    if annotation is None:
        return issues
    source_ref = annotation.get("source_manifest")
    expected_manifest_path = manifest_relative_path
    if not isinstance(source_ref, dict) or source_ref.get("path") != expected_manifest_path:
        issues.append(ValidationIssue(
            "person-bbox-annotation:$.source_manifest.path",
            "annotation is bound to a different web-image manifest",
        ))
    elif str(source_ref.get("sha256", "")).lower() != _sha256_file(
        root / expected_manifest_path
    ).lower():
        issues.append(ValidationIssue(
            "person-bbox-annotation:$.source_manifest.sha256",
            "annotation source-manifest hash does not match",
        ))
    annotation_records = annotation.get("records")
    annotation_index = {
        str(record.get("asset_id")): record
        for record in annotation_records
        if isinstance(record, dict) and record.get("asset_id")
    } if isinstance(annotation_records, list) else {}
    if set(annotation_index) != set(indexed):
        issues.append(ValidationIssue(
            "person-bbox-annotation:$.records",
            "annotation asset IDs must match web-image manifest exactly",
        ))
    for asset_id, record in annotation_index.items():
        source = indexed.get(asset_id)
        if source is None:
            continue
        if record.get("image_width") != source.get("width") or record.get("image_height") != source.get("height"):
            issues.append(ValidationIssue(
                f"person-bbox-annotation:$.records[{asset_id}]",
                "annotation dimensions do not match source media",
            ))
        for person_index, person in enumerate(record.get("persons", [])):
            if not isinstance(person, dict) or not isinstance(person.get("bbox_xyxy"), list):
                continue
            box = person["bbox_xyxy"]
            if len(box) != 4:
                continue
            x1, y1, x2, y2 = (float(value) for value in box)
            width = float(source["width"])
            height = float(source["height"])
            if not (0.0 <= x1 < x2 <= width and 0.0 <= y1 < y2 <= height):
                issues.append(ValidationIssue(
                    f"person-bbox-annotation:$.records[{asset_id}].persons[{person_index}]",
                    "bounding box lies outside source media",
                ))
    return issues


def validate_zotero_source_manifest(
    manifest_path: Path,
    instance: Any,
    *,
    label: str | None = None,
) -> list[ValidationIssue]:
    """Check that every source PDF exists beside the manifest and matches its record hash."""
    issues: list[ValidationIssue] = []
    rendered_label = label or str(manifest_path)
    manifest_root = manifest_path.resolve().parent
    if not isinstance(instance, list):
        return issues

    seen_keys: set[str] = set()
    seen_citation_numbers: set[int] = set()
    seen_dois: set[str] = set()

    for record_index, record in enumerate(instance):
        if not isinstance(record, dict):
            continue
        for field, normalized_value, seen in (
            ("key", record.get("key"), seen_keys),
            ("citation_number", record.get("citation_number"), seen_citation_numbers),
            (
                "doi",
                _normalize_doi(record["doi"]) if isinstance(record.get("doi"), str) else None,
                seen_dois,
            ),
        ):
            if normalized_value is None:
                continue
            if normalized_value in seen:
                issues.append(
                    ValidationIssue(
                        f"{rendered_label}:$[{record_index}].{field}",
                        f"duplicate source-manifest {field}: {normalized_value}",
                    )
                )
            seen.add(normalized_value)
        source_files = record.get("source_files")
        expected = record.get("sha256")
        if not isinstance(source_files, list) or not isinstance(expected, str):
            continue
        if not SHA256_PATTERN.fullmatch(expected):
            issues.append(
                ValidationIssue(
                    f"{rendered_label}:$[{record_index}].sha256",
                    "invalid source PDF SHA-256 value",
                )
            )
            continue

        for source_index, source_file in enumerate(source_files):
            if not isinstance(source_file, str):
                continue
            location = f"{rendered_label}:$[{record_index}].source_files[{source_index}]"
            candidate = (manifest_root / Path(source_file)).resolve()
            try:
                candidate.relative_to(manifest_root)
            except ValueError:
                issues.append(
                    ValidationIssue(location, "source PDF reference escapes manifest directory")
                )
                continue
            if not candidate.is_file():
                issues.append(
                    ValidationIssue(location, f"source PDF is absent: {source_file}")
                )
                continue
            if _sha256_file(candidate).lower() != expected.lower():
                issues.append(
                    ValidationIssue(location, f"source PDF SHA-256 mismatch: {source_file}")
                )

    expected_citation_numbers = set(range(1, len(instance) + 1))
    if seen_citation_numbers != expected_citation_numbers:
        issues.append(
            ValidationIssue(
                rendered_label,
                "citation_number values must be contiguous from 1 through manifest length",
            )
        )

    return issues


def validate_zotero_receipt(
    repository_root: Path,
    receipt: Any,
    source_manifest: Any,
    *,
    label: str = ZOTERO_RECEIPT_PATH,
) -> list[ValidationIssue]:
    """Cross-check the Zotero receipt against its source manifest and portable BibTeX."""
    issues: list[ValidationIssue] = []
    root = repository_root.resolve()
    source_manifest_path = (root / ZOTERO_SOURCE_MANIFEST_PATH).resolve()
    expected_bibtex_path = (root / ZOTERO_BIBTEX_PATH).resolve()
    if not isinstance(receipt, dict):
        return [ValidationIssue(label, "receipt must be a JSON object")]
    if not isinstance(source_manifest, list):
        return [ValidationIssue(label, "source manifest must be a JSON array")]

    import_source = receipt.get("import_source")
    portable_bibtex = receipt.get("portable_bibtex")
    verification = receipt.get("verification")
    for name, value in (
        ("import_source", import_source),
        ("portable_bibtex", portable_bibtex),
        ("verification", verification),
    ):
        if not isinstance(value, dict):
            issues.append(ValidationIssue(f"{label}:$.{name}", "receipt section must be an object"))
    if not all(isinstance(value, dict) for value in (import_source, portable_bibtex, verification)):
        return issues

    parsed_timestamps: dict[str, datetime] = {}
    for field in ("exported_at_utc", "verified_at_utc"):
        raw_timestamp = receipt.get(field)
        location = f"{label}:$.{field}"
        if not isinstance(raw_timestamp, str) or not raw_timestamp.endswith("Z"):
            issues.append(ValidationIssue(location, "receipt timestamp must be UTC and end in Z"))
            continue
        try:
            parsed_timestamps[field] = datetime.fromisoformat(
                raw_timestamp.removesuffix("Z") + "+00:00"
            )
        except ValueError:
            issues.append(ValidationIssue(location, "invalid receipt timestamp"))
    if (
        "exported_at_utc" in parsed_timestamps
        and "verified_at_utc" in parsed_timestamps
        and parsed_timestamps["verified_at_utc"] < parsed_timestamps["exported_at_utc"]
    ):
        issues.append(
            ValidationIssue(
                f"{label}:$.verified_at_utc",
                "verification timestamp precedes export timestamp",
            )
        )

    exported_at = parsed_timestamps.get("exported_at_utc")
    if exported_at is not None:
        for record_index, record in enumerate(source_manifest):
            if not isinstance(record, dict) or record.get("provenance_status") != "verified-download":
                continue
            raw_retrieved_at = record.get("retrieved_at")
            try:
                retrieved_at = datetime.fromisoformat(str(raw_retrieved_at).replace("Z", "+00:00"))
            except ValueError:
                continue
            if retrieved_at > exported_at:
                issues.append(
                    ValidationIssue(
                        f"{label}:$.import_source.manifest_path[{record_index}].retrieved_at",
                        "source retrieval timestamp follows Zotero export timestamp",
                    )
                )

    def checked_repository_file(
        section: dict[str, Any],
        *,
        section_name: str,
        path_key: str,
        hash_key: str,
        required_path: Path,
    ) -> Path | None:
        raw_path = section.get(path_key)
        expected_hash = section.get(hash_key)
        location = f"{label}:$.{section_name}.{path_key}"
        if not isinstance(raw_path, str):
            issues.append(ValidationIssue(location, "receipt path must be a string"))
            return None
        candidate = (root / Path(raw_path)).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            issues.append(ValidationIssue(location, "receipt path escapes repository"))
            return None
        if candidate != required_path:
            issues.append(
                ValidationIssue(location, f"receipt path does not identify {required_path.relative_to(root)}")
            )
            return None
        if not candidate.is_file():
            issues.append(ValidationIssue(location, f"referenced file is absent: {raw_path}"))
            return None
        hash_location = f"{label}:$.{section_name}.{hash_key}"
        if not isinstance(expected_hash, str) or not SHA256_PATTERN.fullmatch(expected_hash):
            issues.append(ValidationIssue(hash_location, "invalid SHA-256 value"))
        elif _sha256_file(candidate).lower() != expected_hash.lower():
            issues.append(ValidationIssue(hash_location, f"SHA-256 mismatch: {raw_path}"))
        return candidate

    checked_repository_file(
        import_source,
        section_name="import_source",
        path_key="manifest_path",
        hash_key="manifest_sha256",
        required_path=source_manifest_path,
    )
    bibtex_path = checked_repository_file(
        portable_bibtex,
        section_name="portable_bibtex",
        path_key="path",
        hash_key="sha256",
        required_path=expected_bibtex_path,
    )

    item_count = len(source_manifest)
    pdf_count = 0
    pdf_sha256_count = 0
    pdf_hash_match_count = 0
    verified_download_count = 0
    legacy_unresolved_count = 0
    manifest_root = source_manifest_path.parent
    for record in source_manifest:
        if not isinstance(record, dict):
            continue
        sources = record.get("source_files")
        expected_hash = record.get("sha256")
        if isinstance(sources, list):
            pdf_count += len(sources)
        else:
            sources = []
        if isinstance(expected_hash, str) and SHA256_PATTERN.fullmatch(expected_hash):
            pdf_sha256_count += len(sources)
            for source in sources:
                if not isinstance(source, str):
                    continue
                candidate = (manifest_root / Path(source)).resolve()
                try:
                    candidate.relative_to(manifest_root)
                except ValueError:
                    continue
                if candidate.is_file() and _sha256_file(candidate).lower() == expected_hash.lower():
                    pdf_hash_match_count += 1
        if record.get("provenance_status") == "verified-download":
            verified_download_count += 1
        elif record.get("provenance_status") == "legacy-origin-unresolved":
            legacy_unresolved_count += 1

    expected_counts = {
        ("import_source", "declared_item_count"): item_count,
        ("import_source", "pdf_count"): pdf_count,
        ("import_source", "pdf_sha256_count"): pdf_sha256_count,
        ("import_source", "verified_download_origin_count"): verified_download_count,
        ("import_source", "legacy_origin_unresolved_count"): legacy_unresolved_count,
        ("verification", "top_level_item_count"): item_count,
        ("verification", "pdf_attachment_count"): pdf_count,
        ("verification", "total_item_count"): item_count + pdf_count,
        ("verification", "manifest_pdf_hash_match_count"): pdf_hash_match_count,
        ("verification", "items_without_exactly_one_child"): 0,
        ("verification", "duplicate_normalized_doi_groups"): 0,
        ("verification", "items_missing_title_doi_creator_or_date"): 0,
    }
    sections = {"import_source": import_source, "verification": verification}
    for (section_name, field), expected_value in expected_counts.items():
        actual_value = sections[section_name].get(field)
        if actual_value != expected_value:
            issues.append(
                ValidationIssue(
                    f"{label}:$.{section_name}.{field}",
                    f"receipt count mismatch: expected {expected_value}, found {actual_value}",
                )
            )

    if bibtex_path is not None:
        try:
            bibtex_text = bibtex_path.read_text(encoding="utf-8")
            entry_count = len(BIBTEX_ENTRY_PATTERN.findall(bibtex_text))
        except (OSError, UnicodeError) as error:
            issues.append(ValidationIssue(f"{label}:$.portable_bibtex.path", str(error)))
        else:
            declared_entry_count = portable_bibtex.get("entry_count")
            if declared_entry_count != entry_count:
                issues.append(
                    ValidationIssue(
                        f"{label}:$.portable_bibtex.entry_count",
                        f"BibTeX entry count mismatch: expected {entry_count}, "
                        f"found {declared_entry_count}",
                    )
                )
            if entry_count != item_count:
                issues.append(
                    ValidationIssue(
                        f"{label}:$.portable_bibtex.entry_count",
                        f"BibTeX/source-manifest item mismatch: expected {item_count}, "
                        f"found {entry_count}",
                    )
                )
            bibtex_dois = _bibtex_dois(bibtex_text)
            manifest_dois = [
                _normalize_doi(record["doi"])
                for record in source_manifest
                if isinstance(record, dict) and isinstance(record.get("doi"), str)
            ]
            if len(bibtex_dois) != entry_count:
                issues.append(
                    ValidationIssue(
                        f"{label}:$.portable_bibtex.path",
                        "every portable BibTeX entry must contain exactly one DOI field",
                    )
                )
            if len(set(bibtex_dois)) != len(bibtex_dois):
                issues.append(
                    ValidationIssue(
                        f"{label}:$.portable_bibtex.path",
                        "portable BibTeX contains duplicate normalized DOI values",
                    )
                )
            if set(bibtex_dois) != set(manifest_dois):
                issues.append(
                    ValidationIssue(
                        f"{label}:$.portable_bibtex.path",
                        "portable BibTeX DOI set does not match source manifest",
                    )
                )
            if BIBTEX_LOCAL_FILE_FIELD_PATTERN.search(bibtex_text):
                issues.append(
                    ValidationIssue(
                        f"{label}:$.portable_bibtex.path",
                        "portable BibTeX contains a machine-local file or attachment field",
                    )
                )

    if portable_bibtex.get("transformation") != ZOTERO_BIBTEX_TRANSFORMATION:
        issues.append(
            ValidationIssue(
                f"{label}:$.portable_bibtex.transformation",
                "unexpected portable BibTeX transformation declaration",
            )
        )

    return issues


def validate_pr01_search_manifest(
    repository_root: Path,
    manifest: Any,
    *,
    label: str = PR01_SEARCH_MANIFEST_PATH,
) -> list[ValidationIssue]:
    """Validate frozen PR01 database/query coverage beyond JSON Schema shape."""
    issues: list[ValidationIssue] = []
    if not isinstance(manifest, dict):
        return [ValidationIssue(label, "PR01 search manifest must be a JSON object")]

    serialized = json.dumps(manifest, ensure_ascii=False)
    for placeholder in PR01_FORBIDDEN_PLACEHOLDERS:
        if placeholder in serialized:
            issues.append(ValidationIssue(label, f"unresolved search placeholder: {placeholder}"))

    databases = manifest.get("databases")
    queries = manifest.get("queries")
    filter_profiles = manifest.get("filter_profiles")
    if not isinstance(databases, list) or not isinstance(queries, list):
        return issues
    if not isinstance(filter_profiles, list):
        filter_profiles = []

    database_ids: list[str] = [
        record.get("database_id")
        for record in databases
        if isinstance(record, dict) and isinstance(record.get("database_id"), str)
    ]
    if len(database_ids) != len(set(database_ids)):
        issues.append(ValidationIssue(label, "duplicate PR01 database_id"))
    missing_databases = PR01_REQUIRED_DATABASE_IDS - set(database_ids)
    if missing_databases:
        issues.append(
            ValidationIssue(
                label,
                f"missing required PR01 databases: {sorted(missing_databases)}",
            )
        )
    if "google-scholar" in database_ids:
        issues.append(ValidationIssue(label, "Google Scholar is snowballing-only"))
    required_execution_database_ids = {
        record.get("database_id")
        for record in databases
        if isinstance(record, dict) and record.get("required_for_completion") is True
    }
    missing_execution_databases = (
        PR01_MINIMUM_EXECUTION_DATABASE_IDS - required_execution_database_ids
    )
    if missing_execution_databases:
        issues.append(
            ValidationIssue(
                label,
                "missing required executable PR01 databases: "
                f"{sorted(missing_execution_databases)}",
            )
        )
    for database_index, record in enumerate(databases):
        if not isinstance(record, dict):
            continue
        if (
            record.get("required_for_completion") is True
            and record.get("access_state_at_freeze") == "access-blocked"
        ):
            issues.append(
                ValidationIssue(
                    f"{label}:$.databases[{database_index}]",
                    "access-blocked database cannot be required for completion",
                )
            )
        database_id = record.get("database_id")
        retrieval_policy = record.get("retrieval_policy")
        if not isinstance(retrieval_policy, dict):
            continue
        if database_id == "crossref":
            expected_crossref_policy = {
                "mode": "ranked-cap",
                "cap_records_per_query": 1000,
                "page_size": 1000,
                "ordering": "score:desc",
                "pagination_method": "none",
                "reported_total_semantics": "source-reported-unverified",
                "completion_rule": "cap-reached-or-source-exhausted",
            }
            for key, expected_value in expected_crossref_policy.items():
                if retrieval_policy.get(key) != expected_value:
                    issues.append(
                        ValidationIssue(
                            f"{label}:$.databases[{database_index}].retrieval_policy.{key}",
                            "Crossref retrieval policy differs from the frozen ranked-cap plan",
                        )
                    )
        if database_id == "semantic-scholar":
            expected_semantic_scholar_policy = {
                "mode": "all-results-pagination",
                "page_size": 1000,
                "ordering": "paperId:asc",
                "pagination_method": "continuation-token",
                "reported_total_semantics": "estimated",
                "completion_rule": "terminal-pagination-state",
                "platform_record_limit": 10_000_000,
                "overflow_action": "fail-and-amend",
            }
            for key, expected_value in expected_semantic_scholar_policy.items():
                if retrieval_policy.get(key) != expected_value:
                    issues.append(
                        ValidationIssue(
                            f"{label}:$.databases[{database_index}].retrieval_policy.{key}",
                            "Semantic Scholar retrieval policy differs from the frozen token plan",
                        )
                    )
    if not any(
        isinstance(record, dict) and record.get("coverage_role") == "broad-robotics-control"
        for record in databases
    ):
        issues.append(ValidationIssue(label, "broad robotics/control source is absent"))

    filter_profile_ids = [
        record.get("filter_profile_id")
        for record in filter_profiles
        if isinstance(record, dict) and isinstance(record.get("filter_profile_id"), str)
    ]
    if len(filter_profile_ids) != len(set(filter_profile_ids)):
        issues.append(ValidationIssue(label, "duplicate PR01 filter_profile_id"))

    query_ids: list[str] = []
    database_concepts: dict[str, list[str]] = {database_id: [] for database_id in database_ids}
    for query_index, query in enumerate(queries):
        if not isinstance(query, dict):
            continue
        query_id = query.get("query_id")
        database_id = query.get("database_id")
        concept_block = query.get("concept_block")
        filter_profile_id = query.get("filter_profile_id")
        if isinstance(query_id, str):
            query_ids.append(query_id)
        if database_id not in database_ids:
            issues.append(
                ValidationIssue(
                    f"{label}:$.queries[{query_index}].database_id",
                    f"unresolved database_id: {database_id}",
                )
            )
        elif isinstance(concept_block, str):
            database_concepts[database_id].append(concept_block)
        if filter_profile_id not in filter_profile_ids:
            issues.append(
                ValidationIssue(
                    f"{label}:$.queries[{query_index}].filter_profile_id",
                    f"unresolved filter_profile_id: {filter_profile_id}",
                )
            )
        if database_id == "crossref":
            exact_query = query.get("exact_query")
            query_parameters = (
                parse_qs(exact_query, keep_blank_values=True)
                if isinstance(exact_query, str)
                else {}
            )
            if "cursor" in query_parameters:
                issues.append(
                    ValidationIssue(
                        f"{label}:$.queries[{query_index}].exact_query",
                        "Crossref ranked-cap query must not use cursor pagination",
                    )
                )
            if not isinstance(exact_query, str) or any(
                query_parameters.get(key) != [value]
                for key, value in (
                    ("rows", "1000"),
                    ("sort", "score"),
                    ("order", "desc"),
                )
            ):
                issues.append(
                    ValidationIssue(
                        f"{label}:$.queries[{query_index}].exact_query",
                        "Crossref query must freeze rows=1000 and descending relevance score",
                    )
                )
        if database_id == "semantic-scholar":
            exact_query = query.get("exact_query")
            query_parameters = (
                parse_qs(exact_query, keep_blank_values=True)
                if isinstance(exact_query, str)
                else {}
            )
            expected_fields = (
                "paperId,title,abstract,authors,year,publicationDate,venue,externalIds,"
                "publicationTypes,url,openAccessPdf"
            )
            if (
                query_parameters.get("sort") != ["paperId:asc"]
                or "token" in query_parameters
                or query_parameters.get("fields") != [expected_fields]
            ):
                issues.append(
                    ValidationIssue(
                        f"{label}:$.queries[{query_index}].exact_query",
                        "Semantic Scholar query must freeze screening fields and paperId ordering "
                        "without a token",
                    )
                )
    if len(query_ids) != len(set(query_ids)):
        issues.append(ValidationIssue(label, "duplicate PR01 query_id"))

    for database_id in PR01_REQUIRED_DATABASE_IDS & set(database_ids):
        concepts = database_concepts.get(database_id, [])
        if len(concepts) != len(set(concepts)):
            issues.append(
                ValidationIssue(label, f"duplicate concept query for database: {database_id}")
            )
        missing_concepts = PR01_REQUIRED_CONCEPT_BLOCKS - set(concepts)
        if missing_concepts:
            issues.append(
                ValidationIssue(
                    label,
                    f"database {database_id} misses concept blocks: {sorted(missing_concepts)}",
                )
            )

    return issues


def validate_pr01_raw_search_manifest(
    repository_root: Path,
    raw_manifest: Any,
    search_manifest: Any,
    *,
    label: str = PR01_RAW_SEARCH_EXPORT_MANIFEST_PATH,
) -> list[ValidationIssue]:
    """Bind raw search executions and payload accounting to the frozen PR01 plan."""
    issues: list[ValidationIssue] = []
    root = repository_root.resolve()
    if not isinstance(raw_manifest, dict):
        return [ValidationIssue(label, "PR01 raw-search manifest must be a JSON object")]
    if not isinstance(search_manifest, dict):
        return [ValidationIssue(label, "frozen PR01 search manifest is unavailable")]

    expected_search_path = (root / PR01_SEARCH_MANIFEST_PATH).resolve()
    search_reference = raw_manifest.get("search_manifest")
    if isinstance(search_reference, dict):
        raw_path = search_reference.get("path")
        if isinstance(raw_path, str) and (root / raw_path).resolve() != expected_search_path:
            issues.append(
                ValidationIssue(
                    f"{label}:$.search_manifest.path",
                    "raw-search manifest does not identify the canonical frozen search plan",
                )
            )

    try:
        frozen_at = datetime.fromisoformat(
            str(search_manifest.get("frozen_at_utc")).replace("Z", "+00:00")
        )
        created_at = datetime.fromisoformat(
            str(raw_manifest.get("created_at_utc")).replace("Z", "+00:00")
        )
    except ValueError:
        frozen_at = None
        created_at = None
    if frozen_at is not None and created_at is not None and created_at < frozen_at:
        issues.append(ValidationIssue(label, "raw-search manifest predates the frozen search plan"))

    planned_queries = {
        query.get("query_id"): query
        for query in search_manifest.get("queries", [])
        if isinstance(query, dict) and isinstance(query.get("query_id"), str)
    }
    planned_databases = {
        record.get("database_id"): record
        for record in search_manifest.get("databases", [])
        if isinstance(record, dict) and isinstance(record.get("database_id"), str)
    }
    required_database_ids = {
        database_id
        for database_id, record in planned_databases.items()
        if record.get("required_for_completion") is True
    }
    required_planned_query_ids = {
        query_id
        for query_id, query in planned_queries.items()
        if query.get("database_id") in required_database_ids
    }
    executions = raw_manifest.get("executions")
    if not isinstance(executions, list):
        return issues

    seen_execution_ids: set[str] = set()
    seen_execution_keys: set[tuple[Any, Any, Any]] = set()
    seen_raw_payload_paths: set[str] = set()
    satisfied_initial_query_ids: set[str] = set()
    latest_execution_at: datetime | None = None
    for execution_index, execution in enumerate(executions):
        if not isinstance(execution, dict):
            continue
        execution_label = f"{label}:$.executions[{execution_index}]"
        issue_count_before_execution = len(issues)
        execution_id = execution.get("execution_id")
        execution_key = (
            execution.get("round_id"),
            execution.get("database_id"),
            execution.get("query_id"),
        )
        if isinstance(execution_id, str):
            if execution_id in seen_execution_ids:
                issues.append(ValidationIssue(label, f"duplicate execution_id: {execution_id}"))
            seen_execution_ids.add(execution_id)
        if execution_key in seen_execution_keys:
            issues.append(ValidationIssue(label, f"duplicate search execution: {execution_key}"))
        seen_execution_keys.add(execution_key)

        query_id = execution.get("query_id")
        database_id = execution.get("database_id")
        planned_query = planned_queries.get(query_id)
        planned_database = planned_databases.get(database_id)
        if planned_query is None:
            issues.append(
                ValidationIssue(
                    f"{execution_label}.query_id",
                    f"unresolved frozen query_id: {query_id}",
                )
            )
        else:
            if database_id != planned_query.get("database_id"):
                issues.append(
                    ValidationIssue(
                        f"{execution_label}.database_id",
                        "execution database differs from frozen query",
                    )
                )
            expected_snapshot = {
                key: planned_query.get(key)
                for key in (
                    "exact_query",
                    "search_fields",
                    "filter_profile_id",
                    "platform_filters",
                    "export_format",
                )
            }
            expected_snapshot["retrieval_policy"] = (
                planned_database.get("retrieval_policy")
                if isinstance(planned_database, dict)
                else None
            )
            if execution.get("query_snapshot") != expected_snapshot:
                issues.append(
                    ValidationIssue(
                        f"{execution_label}.query_snapshot",
                        "execution query snapshot differs from frozen plan",
                    )
                )

        try:
            executed_at = datetime.fromisoformat(
                str(execution.get("executed_at_utc")).replace("Z", "+00:00")
            )
        except ValueError:
            executed_at = None
        if executed_at is not None:
            if frozen_at is not None and executed_at < frozen_at:
                issues.append(
                    ValidationIssue(
                        f"{execution_label}.executed_at_utc",
                        "search execution predates frozen plan",
                    )
                )
            latest_execution_at = (
                executed_at
                if latest_execution_at is None
                else max(latest_execution_at, executed_at)
            )

        parts = execution.get("parts")
        if not isinstance(parts, list):
            continue
        part_indices: list[int] = []
        part_record_count = 0
        part_payloads: list[Any | None] = []
        for part_index, part in enumerate(parts):
            payload: Any | None = None
            if not isinstance(part, dict):
                part_payloads.append(payload)
                continue
            index_value = part.get("part_index")
            if isinstance(index_value, int):
                part_indices.append(index_value)
            record_count = part.get("record_count")
            if isinstance(record_count, int):
                part_record_count += record_count
            file_reference = part.get("file")
            if not isinstance(file_reference, dict):
                part_payloads.append(payload)
                continue
            relative_path = file_reference.get("path")
            if not isinstance(relative_path, str):
                part_payloads.append(payload)
                continue
            normalized_path = relative_path.replace("\\", "/")
            if normalized_path in seen_raw_payload_paths:
                issues.append(
                    ValidationIssue(
                        f"{execution_label}.parts[{part_index}].file.path",
                        "raw search payload path is reused",
                    )
                )
            seen_raw_payload_paths.add(normalized_path)
            if not normalized_path.startswith("references/literature/raw/"):
                issues.append(
                    ValidationIssue(
                        f"{execution_label}.parts[{part_index}].file.path",
                        "raw search payload must be under references/literature/raw/",
                    )
                )
            candidate = (root / relative_path).resolve()
            if candidate.is_file():
                if part.get("byte_size") != candidate.stat().st_size:
                    issues.append(
                        ValidationIssue(
                            f"{execution_label}.parts[{part_index}].byte_size",
                            "raw search payload byte_size mismatch",
                        )
                    )
                if part.get("format") == "json":
                    try:
                        payload = load_json_strict(candidate)
                    except (DuplicateJsonKeyError, OSError, json.JSONDecodeError) as error:
                        issues.append(
                            ValidationIssue(
                                f"{execution_label}.parts[{part_index}].file",
                                f"cannot parse raw JSON payload: {error}",
                            )
                        )
            part_payloads.append(payload)

        if part_indices != list(range(1, len(parts) + 1)):
            issues.append(
                ValidationIssue(
                    f"{execution_label}.parts",
                    "part_index values must be contiguous and ordered from 1",
                )
            )
        if part_record_count != execution.get("retrieved_record_count"):
            issues.append(
                ValidationIssue(
                    f"{execution_label}.retrieved_record_count",
                    "retrieved record count does not equal the sum of part counts",
                )
            )

        outcome = execution.get("retrieval_outcome")
        policy = (
            planned_database.get("retrieval_policy")
            if isinstance(planned_database, dict)
            else None
        )
        if not isinstance(outcome, dict) or not isinstance(policy, dict):
            continue
        outcome_status = outcome.get("status")
        retrieved_count = execution.get("retrieved_record_count")
        source_count = outcome.get("source_reported_hit_count")
        termination_reason = outcome.get("termination_reason")

        if database_id == "crossref" and policy.get("mode") == "ranked-cap":
            if outcome_status == "FAILED":
                if retrieved_count != 0 or termination_reason != "request-failed":
                    issues.append(
                        ValidationIssue(
                            execution_label,
                            "failed Crossref request must record zero retrieved records",
                        )
                    )
                continue
            if len(parts) != 1:
                issues.append(
                    ValidationIssue(
                        f"{execution_label}.parts",
                        "Crossref ranked-cap execution must retain exactly one raw response",
                    )
                )
            if parts and isinstance(parts[0], dict) and parts[0].get("pagination") is not None:
                issues.append(
                    ValidationIssue(
                        f"{execution_label}.parts[0].pagination",
                        "Crossref ranked-cap response must not claim pagination",
                    )
                )
            payload = part_payloads[0] if part_payloads else None
            message = payload.get("message") if isinstance(payload, dict) else None
            items = message.get("items") if isinstance(message, dict) else None
            payload_total = message.get("total-results") if isinstance(message, dict) else None
            if not isinstance(items, list):
                issues.append(
                    ValidationIssue(execution_label, "Crossref raw response lacks message.items")
                )
            elif parts and isinstance(parts[0], dict) and len(items) != parts[0].get("record_count"):
                issues.append(
                    ValidationIssue(
                        f"{execution_label}.parts[0].record_count",
                        "Crossref message.items count differs from the manifest part",
                    )
                )
            if not isinstance(payload_total, int) or payload_total != source_count:
                issues.append(
                    ValidationIssue(
                        f"{execution_label}.retrieval_outcome.source_reported_hit_count",
                        "Crossref total-results differs from the recorded source count",
                    )
                )
            cap = policy.get("cap_records_per_query")
            if (
                isinstance(retrieved_count, int)
                and isinstance(cap, int)
                and retrieved_count > cap
            ):
                issues.append(
                    ValidationIssue(
                        f"{execution_label}.retrieved_record_count",
                        "Crossref retrieved count exceeds the frozen ranked cap",
                    )
                )
            if outcome_status == "POLICY-SATISFIED" and isinstance(retrieved_count, int):
                if retrieved_count == cap and isinstance(source_count, int) and source_count >= cap:
                    if termination_reason != "ranked-cap-reached":
                        issues.append(
                            ValidationIssue(
                                execution_label,
                                "Crossref cap completion must use ranked-cap-reached",
                            )
                        )
                elif (
                    isinstance(cap, int)
                    and retrieved_count < cap
                    and source_count == retrieved_count
                ):
                    if termination_reason != "source-exhausted-before-cap":
                        issues.append(
                            ValidationIssue(
                                execution_label,
                                "Crossref short result set must use source-exhausted-before-cap",
                            )
                        )
                else:
                    issues.append(
                        ValidationIssue(
                            execution_label,
                            "Crossref outcome does not satisfy the frozen ranked-cap policy",
                        )
                    )

        elif database_id == "semantic-scholar":
            if outcome_status == "FAILED":
                if retrieved_count != 0 or termination_reason != "request-failed":
                    issues.append(
                        ValidationIssue(
                            execution_label,
                            "failed Semantic Scholar request must record zero retrieved records",
                        )
                    )
                continue
            if outcome_status == "POLICY-SATISFIED" and not parts:
                issues.append(
                    ValidationIssue(
                        f"{execution_label}.parts",
                        "Semantic Scholar completion must retain its raw response",
                    )
                )
            expected_request_token: str | None = None
            seen_paper_ids: set[str] = set()
            first_total: int | None = None
            for part_index, (part, payload) in enumerate(zip(parts, part_payloads, strict=True)):
                if not isinstance(part, dict):
                    continue
                pagination = part.get("pagination")
                if not isinstance(pagination, dict):
                    issues.append(
                        ValidationIssue(
                            f"{execution_label}.parts[{part_index}].pagination",
                            "Semantic Scholar part requires token provenance",
                        )
                    )
                    continue
                request_token = pagination.get("request_token")
                response_next_token = pagination.get("response_next_token")
                if request_token != expected_request_token:
                    issues.append(
                        ValidationIssue(
                            f"{execution_label}.parts[{part_index}].pagination.request_token",
                            "Semantic Scholar continuation-token chain is broken",
                        )
                    )
                if not isinstance(payload, dict):
                    expected_request_token = (
                        response_next_token if isinstance(response_next_token, str) else None
                    )
                    continue
                data = payload.get("data")
                payload_next_token = payload.get("token")
                if not isinstance(data, list):
                    issues.append(
                        ValidationIssue(
                            f"{execution_label}.parts[{part_index}]",
                            "Semantic Scholar raw response lacks data",
                        )
                    )
                else:
                    if len(data) != part.get("record_count"):
                        issues.append(
                            ValidationIssue(
                                f"{execution_label}.parts[{part_index}].record_count",
                                "Semantic Scholar data count differs from the manifest part",
                            )
                        )
                    page_size = policy.get("page_size")
                    if isinstance(page_size, int) and len(data) > page_size:
                        issues.append(
                            ValidationIssue(
                                f"{execution_label}.parts[{part_index}].record_count",
                                "Semantic Scholar page exceeds the frozen page size",
                            )
                        )
                    for paper in data:
                        paper_id = paper.get("paperId") if isinstance(paper, dict) else None
                        if not isinstance(paper_id, str) or paper_id in seen_paper_ids:
                            issues.append(
                                ValidationIssue(
                                    f"{execution_label}.parts[{part_index}]",
                                    "Semantic Scholar paperId is missing or duplicated",
                                )
                            )
                        else:
                            seen_paper_ids.add(paper_id)
                normalized_payload_token = (
                    payload_next_token if isinstance(payload_next_token, str) else None
                )
                if response_next_token != normalized_payload_token:
                    issues.append(
                        ValidationIssue(
                            f"{execution_label}.parts[{part_index}].pagination.response_next_token",
                            "Semantic Scholar response token differs from the raw payload",
                        )
                    )
                if part_index == 0:
                    payload_total = payload.get("total")
                    first_total = payload_total if isinstance(payload_total, int) else None
                expected_request_token = normalized_payload_token

            if not isinstance(first_total, int):
                issues.append(
                    ValidationIssue(
                        f"{execution_label}.retrieval_outcome.source_reported_hit_count",
                        "Semantic Scholar first raw response lacks an estimated total",
                    )
                )
            elif first_total != source_count:
                issues.append(
                    ValidationIssue(
                        f"{execution_label}.retrieval_outcome.source_reported_hit_count",
                        "Semantic Scholar estimated total differs from the first raw response",
                    )
                )
            platform_limit = policy.get("platform_record_limit")
            if (
                outcome_status == "POLICY-SATISFIED"
                and isinstance(first_total, int)
                and isinstance(platform_limit, int)
                and first_total > platform_limit
            ):
                issues.append(
                    ValidationIssue(
                        execution_label,
                        "Semantic Scholar estimate exceeds the frozen platform limit",
                    )
                )
            if outcome_status == "POLICY-SATISFIED":
                if expected_request_token is not None:
                    issues.append(
                        ValidationIssue(
                            execution_label,
                            "Semantic Scholar completion retains a continuation token",
                        )
                    )
                if termination_reason != "pagination-exhausted":
                    issues.append(
                        ValidationIssue(
                            execution_label,
                            "Semantic Scholar completion must use pagination-exhausted",
                        )
                    )

        elif outcome_status == "POLICY-SATISFIED":
            if policy.get("pagination_method") == "ui-batch":
                if termination_reason != "platform-export-complete":
                    issues.append(
                        ValidationIssue(
                            execution_label,
                            "UI export completion must use platform-export-complete",
                        )
                    )
                if isinstance(source_count, int) and source_count != retrieved_count:
                    issues.append(
                        ValidationIssue(
                            execution_label,
                            "complete UI export must match the source-reported result count",
                        )
                    )

        if (
            outcome_status == "POLICY-SATISFIED"
            and execution.get("round_id") == "initial"
            and isinstance(query_id, str)
            and len(issues) == issue_count_before_execution
        ):
            satisfied_initial_query_ids.add(query_id)

    if raw_manifest.get("status") == "POLICY-COMPLETE":
        missing_queries = required_planned_query_ids - satisfied_initial_query_ids
        if missing_queries:
            issues.append(
                ValidationIssue(
                    label,
                    "POLICY-COMPLETE raw manifest misses satisfied initial queries: "
                    f"{sorted(missing_queries)}",
                )
            )
        try:
            completed_at = datetime.fromisoformat(
                str(raw_manifest.get("completed_at_utc")).replace("Z", "+00:00")
            )
        except ValueError:
            completed_at = None
        if (
            completed_at is not None
            and latest_execution_at is not None
            and completed_at < latest_execution_at
        ):
            issues.append(ValidationIssue(label, "raw manifest completion predates an execution"))

    return issues


def _frontmatter(note: Path) -> dict[str, Any]:
    text = note.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError("missing YAML frontmatter")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise ValueError("unterminated YAML frontmatter")
    metadata = yaml.safe_load(parts[1])
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a mapping")
    return metadata


def _wikilink_target(vault_root: Path, raw_link: str) -> Path | None:
    note_part = raw_link.split("|", 1)[0].split("#", 1)[0].strip()
    if not note_part:
        return None
    relative = Path(*note_part.split("/"))
    if relative.suffix.lower() != ".md":
        relative = relative.with_suffix(".md")
    return (vault_root / relative).resolve()


def validate_obsidian_vault(vault_root: Path) -> tuple[list[ValidationIssue], int, int]:
    issues: list[ValidationIssue] = []
    notes = sorted(vault_root.rglob("*.md"))
    link_count = 0
    resolved_root = vault_root.resolve()
    for note in notes:
        label = str(note.relative_to(vault_root)).replace("\\", "/")
        try:
            metadata = _frontmatter(note)
        except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
            issues.append(ValidationIssue(label, str(error)))
            continue
        for key in ("type", "status"):
            if key not in metadata or not str(metadata[key]).strip():
                issues.append(ValidationIssue(label, f"frontmatter.{key} is required"))
        text = note.read_text(encoding="utf-8")
        for raw_link in WIKILINK_PATTERN.findall(text):
            link_count += 1
            target = _wikilink_target(resolved_root, raw_link)
            if target is None:
                continue
            try:
                target.relative_to(resolved_root)
            except ValueError:
                issues.append(ValidationIssue(label, f"wikilink escapes vault: [[{raw_link}]]"))
                continue
            if not target.is_file():
                issues.append(ValidationIssue(label, f"unresolved wikilink: [[{raw_link}]]"))
    return issues, len(notes), link_count


def _pr01_gate_state(
    repository_root: Path,
    record: dict[str, Any],
    search_manifest: Any,
    raw_search_manifest: Any,
) -> str:
    if record.get("status") != "VERIFIED":
        return "CLOSED_IN_PROGRESS"
    if not isinstance(search_manifest, dict) or search_manifest.get("status") != "FROZEN":
        return "CLOSED_EVIDENCE_INCOMPLETE"
    if (
        not isinstance(raw_search_manifest, dict)
        or raw_search_manifest.get("status") != "POLICY-COMPLETE"
    ):
        return "CLOSED_EVIDENCE_INCOMPLETE"
    evidence = record.get("evidence")
    if not isinstance(evidence, dict):
        return "CLOSED_EVIDENCE_INCOMPLETE"
    for evidence_key, expected_path in (
        ("search_manifest", PR01_SEARCH_MANIFEST_PATH),
        ("raw_search_export_manifest", PR01_RAW_SEARCH_EXPORT_MANIFEST_PATH),
    ):
        reference = evidence.get(evidence_key)
        expected_file = repository_root / expected_path
        if (
            not isinstance(reference, dict)
            or reference.get("path") != expected_path
            or not expected_file.is_file()
            or str(reference.get("sha256", "")).lower() != _sha256_file(expected_file).lower()
        ):
            return "CLOSED_EVIDENCE_INCOMPLETE"
    if record.get("decision") == "STOP":
        return "CLOSED_STOP"
    if record.get("decision") in {"GO-ALGORITHM", "PIVOT-EMPIRICAL"}:
        return "OPEN"
    return "CLOSED_INVALID"


def validate_repository(
    repository_root: Path,
) -> dict[str, Any]:
    root = repository_root.resolve()
    issues: list[ValidationIssue] = []
    schemas: dict[str, dict[str, Any]] = {}

    for path in sorted((root / "schemas").glob("*.schema.json")):
        label = str(path.relative_to(root)).replace("\\", "/")
        try:
            schema = load_json_strict(path)
            Draft202012Validator.check_schema(schema)
            schemas[path.name] = schema
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            DuplicateJsonKeyError,
            SchemaError,
        ) as error:
            issues.append(ValidationIssue(label, str(error)))

    validated_instances: list[tuple[str, Any]] = []
    for relative_path, schema_name in JSON_INSTANCE_SCHEMAS.items():
        path = root / relative_path
        try:
            instance = load_json_strict(path)
        except (OSError, UnicodeError, json.JSONDecodeError, DuplicateJsonKeyError) as error:
            issues.append(ValidationIssue(relative_path, str(error)))
            continue
        schema = schemas.get(schema_name)
        if schema is None:
            issues.append(ValidationIssue(relative_path, f"schema unavailable: {schema_name}"))
            continue
        issues.extend(_schema_issues(instance, schema, relative_path))
        issues.extend(_file_reference_issues(root, instance, relative_path))
        if relative_path == ZOTERO_SOURCE_MANIFEST_PATH:
            issues.extend(validate_zotero_source_manifest(path, instance, label=relative_path))
        validated_instances.append((relative_path, instance))

    source_manifest = next(
        (
            instance
            for relative_path, instance in validated_instances
            if relative_path == ZOTERO_SOURCE_MANIFEST_PATH
        ),
        None,
    )
    receipt = next(
        (
            instance
            for relative_path, instance in validated_instances
            if relative_path == ZOTERO_RECEIPT_PATH
        ),
        None,
    )
    if receipt is not None:
        issues.extend(validate_zotero_receipt(root, receipt, source_manifest))

    web_manifest = next(
        (
            instance
            for relative_path, instance in validated_instances
            if relative_path == "research/metadata/web_images/person_context_manifest.json"
        ),
        None,
    )
    bbox_annotation = next(
        (
            instance
            for relative_path, instance in validated_instances
            if relative_path == "research/metadata/web_images/person_bbox_annotations_20260812.json"
        ),
        None,
    )
    if web_manifest is not None:
        issues.extend(
            validate_web_image_payload(
                root,
                web_manifest,
                annotation=bbox_annotation,
                manifest_relative_path="research/metadata/web_images/person_context_manifest.json",
            )
        )

    for relative_path, schema_name in YAML_INSTANCE_SCHEMAS.items():
        path = root / relative_path
        try:
            instance = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as error:
            issues.append(ValidationIssue(relative_path, str(error)))
            continue
        schema = schemas.get(schema_name)
        if schema is None:
            issues.append(ValidationIssue(relative_path, f"schema unavailable: {schema_name}"))
            continue
        issues.extend(_schema_issues(instance, schema, relative_path))
        issues.extend(_file_reference_issues(root, instance, relative_path))
        validated_instances.append((relative_path, instance))

    vault_issues, note_count, wikilink_count = validate_obsidian_vault(root / "research/obsidian")
    issues.extend(vault_issues)

    return {
        "schema": "cca-nmpc-repository-contract-validation-report",
        "schema_version": "1.0.0",
        "status": "PASS" if not issues else "FAIL",
        "schema_count": len(schemas),
        "instance_count": len(validated_instances),
        "obsidian_note_count": note_count,
        "wikilink_count": wikilink_count,
        "active_confirmatory_gate": "NOT_APPLICABLE",
        "issues": [asdict(issue) for issue in issues],
    }
