from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker

from repository import (
    DuplicateJsonKeyError,
    _pr01_gate_state,
    load_json_strict,
    validate_obsidian_vault,
    validate_pr01_raw_search_manifest,
    validate_pr01_search_manifest,
    validate_repository,
    validate_zotero_receipt,
    validate_zotero_source_manifest,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _pr01_query_snapshot(
    search_manifest: dict[str, object],
    database_id: str,
    concept_block: str = "context-human-nmpc",
) -> tuple[dict[str, object], dict[str, object]]:
    planned_query = next(
        query
        for query in search_manifest["queries"]
        if query["database_id"] == database_id and query["concept_block"] == concept_block
    )
    planned_database = next(
        database
        for database in search_manifest["databases"]
        if database["database_id"] == database_id
    )
    snapshot_fields = (
        "exact_query",
        "search_fields",
        "filter_profile_id",
        "platform_filters",
        "export_format",
    )
    snapshot = {field: deepcopy(planned_query[field]) for field in snapshot_fields}
    snapshot["retrieval_policy"] = deepcopy(planned_database["retrieval_policy"])
    return planned_query, snapshot


def _write_pr01_json_part(
    repository_root: Path,
    relative_path: str,
    payload: dict[str, object],
    *,
    part_index: int,
    record_count: int,
    pagination: dict[str, str | None] | None,
) -> dict[str, object]:
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode()
    destination = repository_root / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(encoded)
    return {
        "part_index": part_index,
        "record_count": record_count,
        "byte_size": len(encoded),
        "format": "json",
        "file": {
            "path": relative_path,
            "sha256": hashlib.sha256(encoded).hexdigest().upper(),
        },
        "pagination": pagination,
    }


def _pr01_execution(
    planned_query: dict[str, object],
    snapshot: dict[str, object],
    *,
    parts: list[dict[str, object]],
    retrieved_record_count: int,
    source_reported_hit_count: int | None,
    termination_reason: str,
    outcome_status: str = "POLICY-SATISFIED",
    incompleteness_reason: str | None = None,
) -> dict[str, object]:
    database_id = str(planned_query["database_id"])
    return {
        "execution_id": f"search-{database_id}-context-human-nmpc-initial",
        "round_id": "initial",
        "database_id": database_id,
        "query_id": planned_query["query_id"],
        "executed_at_utc": "2026-08-01T17:00:00Z",
        "executed_by": "nguyen-ngoc-thien",
        "query_snapshot": deepcopy(snapshot),
        "retrieved_record_count": retrieved_record_count,
        "retrieval_outcome": {
            "status": outcome_status,
            "source_reported_hit_count": source_reported_hit_count,
            "termination_reason": termination_reason,
            "incompleteness_reason": incompleteness_reason,
        },
        "parts": parts,
    }


def test_repository_contracts_are_valid_for_active_code() -> None:
    report = validate_repository(REPOSITORY_ROOT)

    assert report["status"] == "PASS"
    assert report["schema_count"] >= 16
    assert report["instance_count"] >= 14
    assert report["obsidian_note_count"] >= 1
    assert report["wikilink_count"] >= 1
    assert report["active_confirmatory_gate"] == "NOT_APPLICABLE"
    assert report["issues"] == []


def test_old_web_image_dataset_is_absent_after_reset() -> None:
    assert not (
        REPOSITORY_ROOT / "research/metadata/web_images/person_context_manifest.json"
    ).exists()
    assert not (
        REPOSITORY_ROOT
        / "research/metadata/web_images/person_bbox_annotations_20260812.json"
    ).exists()


def test_active_pipeline_has_no_ros_runtime_dependency() -> None:
    forbidden = ("ros2", "rosbag", "rclpy", "rospy", "ros::")
    roots = (
        REPOSITORY_ROOT / "src",
        REPOSITORY_ROOT / "simulations",
        REPOSITORY_ROOT / "src/stm",
        REPOSITORY_ROOT / "scripts/python/tools",
        REPOSITORY_ROOT / "configs",
    )
    extensions = {".py", ".m", ".c", ".h", ".ps1", ".yaml", ".yml", ".json", ".toml"}
    violations: list[str] = []
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in extensions:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            if any(token in text for token in forbidden):
                violations.append(path.relative_to(REPOSITORY_ROOT).as_posix())
    assert violations == []


def test_protocol_freeze_schema_requires_completed_focused_audit() -> None:
    schema = load_json_strict(
        REPOSITORY_ROOT / "schemas/protocol-freeze-manifest.schema.json"
    )

    assert schema["properties"]["schema_version"]["const"] == "1.3.0"
    assert (
        schema["$defs"]["research_gap_gate"]["properties"]["status"]["const"]
        == "COMPLETE"
    )


def test_simulation_schema_freezes_position_state_interface() -> None:
    schema = load_json_strict(REPOSITORY_ROOT / "schemas/simulation-config.schema.json")
    controller = schema["$defs"]["controller_contract"]
    assert controller["properties"]["actuation"]["enum"] == ["body_velocity", None]
    assert controller["properties"]["state_definition"]["enum"] == [
        "[x,y,theta,vx,vy,omega]",
        None,
    ]
    assert controller["required"][:3] == ["family", "actuation", "state_definition"]
    confirmatory = schema["allOf"][0]["then"]["properties"]["controller_contract"]["properties"]
    assert confirmatory["actuation"]["const"] == "body_velocity"
    assert confirmatory["state_definition"]["const"] == "[x,y,theta,vx,vy,omega]"


def test_evaluation_schema_requires_lstm_direction_confusion_contract() -> None:
    schema = load_json_strict(REPOSITORY_ROOT / "schemas/evaluation-config.schema.json")
    config = yaml.safe_load(
        (REPOSITORY_ROOT / "configs/evaluation.template.yaml").read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    config["lstm_context"]["enabled"] = True
    assert list(validator.iter_errors(config))

    direction = config["lstm_context"]["direction_classification"]
    config["lstm_context"]["representative_case_selection_rule"] = "predeclared-stratified"
    config["lstm_context"]["failure_case_selection_rule"] = "predeclared-failure-taxonomy"
    direction.update(
        {
            "enabled": True,
            "confusion_matrix_required": True,
            "contract": {
                "task_id": "direction-v1",
                "task_kind": "multiclass_classification",
                "ontology": {"path": "research/ontology/direction.json", "sha256": "a" * 64},
                "class_order": ["left", "right", "forward", "backward", "unknown"],
                "decision_rule": {"path": "research/rules/direction.json", "sha256": "b" * 64},
                "ground_truth": {"path": "data/labels/direction.json", "sha256": "c" * 64},
                "genuine_negative_examples": True,
                "counts_rates_and_support_required": True,
            },
        }
    )
    assert list(validator.iter_errors(config)) == []


def test_pr01_gate_requires_policy_complete_raw_search() -> None:
    decision = load_json_strict(
        REPOSITORY_ROOT / "research/metadata/pr01_gap_decision.json"
    )
    search_manifest = load_json_strict(
        REPOSITORY_ROOT / "research/metadata/pr01_search_manifest.json"
    )
    raw_manifest = load_json_strict(
        REPOSITORY_ROOT / "research/metadata/pr01_raw_search_export_manifest.json"
    )
    verified_decision = deepcopy(decision)
    verified_decision["status"] = "VERIFIED"
    verified_decision["decision"] = "PIVOT-EMPIRICAL"

    assert (
        _pr01_gate_state(
            REPOSITORY_ROOT,
            verified_decision,
            search_manifest,
            raw_manifest,
        )
        == "CLOSED_EVIDENCE_INCOMPLETE"
    )


def test_zotero_source_manifest_provenance_status_fails_closed() -> None:
    schema = load_json_strict(REPOSITORY_ROOT / "schemas/zotero-source-manifest.schema.json")
    manifest = load_json_strict(
        REPOSITORY_ROOT / "references/zotero/import_queue/source_manifest.json"
    )
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    assert list(validator.iter_errors(manifest)) == []

    invalid_variants = []
    verified_without_url = deepcopy(manifest)
    verified_row = next(
        row for row in verified_without_url if row["provenance_status"] == "verified-download"
    )
    verified_row["source_url"] = None
    invalid_variants.append(verified_without_url)

    verified_without_timestamp = deepcopy(manifest)
    verified_row = next(
        row for row in verified_without_timestamp if row["provenance_status"] == "verified-download"
    )
    verified_row["retrieved_at"] = None
    invalid_variants.append(verified_without_timestamp)

    unresolved_with_origin = deepcopy(manifest)
    unresolved_row = next(
        row
        for row in unresolved_with_origin
        if row["provenance_status"] == "legacy-origin-unresolved"
    )
    unresolved_row["source_url"] = "https://example.org/paper.pdf"
    invalid_variants.append(unresolved_with_origin)

    unresolved_without_error = deepcopy(manifest)
    unresolved_row = next(
        row
        for row in unresolved_without_error
        if row["provenance_status"] == "legacy-origin-unresolved"
    )
    unresolved_row["errors"] = []
    invalid_variants.append(unresolved_without_error)

    assert all(list(validator.iter_errors(candidate)) for candidate in invalid_variants)


def test_zotero_source_manifest_checks_pdf_existence_and_hash(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "import_queue"
    citations = manifest_dir / "citations"
    citations.mkdir(parents=True)
    source_pdf = citations / "paper.pdf"
    source_pdf.write_bytes(b"frozen source PDF bytes")
    expected = hashlib.sha256(source_pdf.read_bytes()).hexdigest()
    record = {
        "key": "paper",
        "citation_number": 1,
        "doi": "10.0000/test-paper",
        "source_files": ["citations/paper.pdf"],
        "sha256": expected,
    }
    manifest_path = manifest_dir / "source_manifest.json"

    assert validate_zotero_source_manifest(manifest_path, [record], label="manifest") == []

    bad_hash = deepcopy(record)
    bad_hash["sha256"] = "0" * 64
    mismatch = validate_zotero_source_manifest(manifest_path, [bad_hash], label="manifest")
    assert any("SHA-256 mismatch" in issue.message for issue in mismatch)

    missing = deepcopy(record)
    missing["source_files"] = ["citations/missing.pdf"]
    absent = validate_zotero_source_manifest(manifest_path, [missing], label="manifest")
    assert any("source PDF is absent" in issue.message for issue in absent)

    escaped = deepcopy(record)
    escaped["source_files"] = ["../outside.pdf"]
    escape = validate_zotero_source_manifest(manifest_path, [escaped], label="manifest")
    assert any("escapes manifest directory" in issue.message for issue in escape)


def test_zotero_source_manifest_rejects_duplicate_identity_and_number_gaps() -> None:
    manifest = load_json_strict(
        REPOSITORY_ROOT / "references/zotero/import_queue/source_manifest.json"
    )

    duplicate_doi = deepcopy(manifest)
    duplicate_doi[1]["doi"] = duplicate_doi[0]["doi"].upper()
    issues = validate_zotero_source_manifest(
        REPOSITORY_ROOT / "references/zotero/import_queue/source_manifest.json",
        duplicate_doi,
        label="manifest",
    )
    assert any("duplicate source-manifest doi" in issue.message for issue in issues)

    citation_gap = deepcopy(manifest)
    citation_gap[-1]["citation_number"] = len(citation_gap) + 1
    issues = validate_zotero_source_manifest(
        REPOSITORY_ROOT / "references/zotero/import_queue/source_manifest.json",
        citation_gap,
        label="manifest",
    )
    assert any("citation_number values must be contiguous" in issue.message for issue in issues)


def test_zotero_receipt_binds_manifest_bibtex_and_counts() -> None:
    manifest = load_json_strict(
        REPOSITORY_ROOT / "references/zotero/import_queue/source_manifest.json"
    )
    receipt = load_json_strict(REPOSITORY_ROOT / "references/zotero/export/receipt.json")

    assert validate_zotero_receipt(REPOSITORY_ROOT, receipt, manifest) == []

    bad_manifest_hash = deepcopy(receipt)
    bad_manifest_hash["import_source"]["manifest_sha256"] = "0" * 64
    assert any(
        "SHA-256 mismatch" in issue.message
        for issue in validate_zotero_receipt(REPOSITORY_ROOT, bad_manifest_hash, manifest)
    )

    bad_hash_count = deepcopy(receipt)
    bad_hash_count["verification"]["manifest_pdf_hash_match_count"] -= 1
    assert any(
        "receipt count mismatch" in issue.message
        for issue in validate_zotero_receipt(REPOSITORY_ROOT, bad_hash_count, manifest)
    )

    bad_bibtex_count = deepcopy(receipt)
    bad_bibtex_count["portable_bibtex"]["entry_count"] -= 1
    assert any(
        "BibTeX entry count mismatch" in issue.message
        for issue in validate_zotero_receipt(REPOSITORY_ROOT, bad_bibtex_count, manifest)
    )

    verified_before_export = deepcopy(receipt)
    verified_before_export["verified_at_utc"] = "2026-08-01T14:00:00Z"
    assert any(
        "precedes export" in issue.message
        for issue in validate_zotero_receipt(REPOSITORY_ROOT, verified_before_export, manifest)
    )

    for field in (
        "items_without_exactly_one_child",
        "duplicate_normalized_doi_groups",
        "items_missing_title_doi_creator_or_date",
    ):
        bad_quality_count = deepcopy(receipt)
        bad_quality_count["verification"][field] = 1
        assert any(
            "receipt count mismatch" in issue.message
            for issue in validate_zotero_receipt(REPOSITORY_ROOT, bad_quality_count, manifest)
        )

    wrong_transformation = deepcopy(receipt)
    wrong_transformation["portable_bibtex"]["transformation"] = "No removal performed."
    assert any(
        "unexpected portable BibTeX transformation" in issue.message
        for issue in validate_zotero_receipt(REPOSITORY_ROOT, wrong_transformation, manifest)
    )

    retrieved_after_export = deepcopy(manifest)
    verified_record = next(
        record
        for record in retrieved_after_export
        if record["provenance_status"] == "verified-download"
    )
    verified_record["retrieved_at"] = "2026-08-01T14:53:13Z"
    assert any(
        "retrieval timestamp follows" in issue.message
        for issue in validate_zotero_receipt(REPOSITORY_ROOT, receipt, retrieved_after_export)
    )


def test_zotero_receipt_schema_rejects_shape_drift() -> None:
    schema = load_json_strict(REPOSITORY_ROOT / "schemas/zotero-export-receipt.schema.json")
    receipt = load_json_strict(REPOSITORY_ROOT / "references/zotero/export/receipt.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    assert list(validator.iter_errors(receipt)) == []

    invalid_variants = []
    wrong_version = deepcopy(receipt)
    wrong_version["schema_version"] = "1.0.0"
    invalid_variants.append(wrong_version)

    absolute_manifest_path = deepcopy(receipt)
    absolute_manifest_path["import_source"]["manifest_path"] = "D:/manifest.json"
    invalid_variants.append(absolute_manifest_path)

    negative_count = deepcopy(receipt)
    negative_count["verification"]["pdf_attachment_count"] = -1
    invalid_variants.append(negative_count)

    nonzero_quality_gate = deepcopy(receipt)
    nonzero_quality_gate["verification"]["duplicate_normalized_doi_groups"] = 1
    invalid_variants.append(nonzero_quality_gate)

    non_utc_timestamp = deepcopy(receipt)
    non_utc_timestamp["verified_at_utc"] = "2026-08-01T15:15:28+07:00"
    invalid_variants.append(non_utc_timestamp)

    wrong_transformation = deepcopy(receipt)
    wrong_transformation["portable_bibtex"]["transformation"] = "No removal performed."
    invalid_variants.append(wrong_transformation)

    unexpected_field = deepcopy(receipt)
    unexpected_field["verification"]["unchecked_items"] = 1
    invalid_variants.append(unexpected_field)

    manifest = load_json_strict(
        REPOSITORY_ROOT / "references/zotero/import_queue/source_manifest.json"
    )
    verified_with_file_uri = deepcopy(manifest)
    verified_record = next(
        record
        for record in verified_with_file_uri
        if record["provenance_status"] == "verified-download"
    )
    verified_record["source_url"] = "file:///C:/paper.pdf"
    assert list(
        Draft202012Validator(
            load_json_strict(REPOSITORY_ROOT / "schemas/zotero-source-manifest.schema.json"),
            format_checker=FormatChecker(),
        ).iter_errors(verified_with_file_uri)
    )

    assert all(list(validator.iter_errors(candidate)) for candidate in invalid_variants)


def test_pr01_search_manifest_freezes_database_and_concept_coverage() -> None:
    manifest = load_json_strict(
        REPOSITORY_ROOT / "research/metadata/pr01_search_manifest.json"
    )
    assert validate_pr01_search_manifest(REPOSITORY_ROOT, manifest) == []

    missing_database = deepcopy(manifest)
    missing_database["databases"] = [
        record
        for record in missing_database["databases"]
        if record["database_id"] != "semantic-scholar"
    ]
    assert any(
        "missing required PR01 databases" in issue.message
        for issue in validate_pr01_search_manifest(REPOSITORY_ROOT, missing_database)
    )

    missing_executable = deepcopy(manifest)
    next(
        record
        for record in missing_executable["databases"]
        if record["database_id"] == "ieee-xplore"
    )["required_for_completion"] = False
    assert any(
        "missing required executable PR01 databases" in issue.message
        for issue in validate_pr01_search_manifest(REPOSITORY_ROOT, missing_executable)
    )

    duplicate_query = deepcopy(manifest)
    duplicate_query["queries"][1]["query_id"] = duplicate_query["queries"][0]["query_id"]
    assert any(
        "duplicate PR01 query_id" in issue.message
        for issue in validate_pr01_search_manifest(REPOSITORY_ROOT, duplicate_query)
    )

    missing_concept = deepcopy(manifest)
    missing_concept["queries"] = [
        query
        for query in missing_concept["queries"]
        if not (
            query["database_id"] == "crossref"
            and query["concept_block"] == "mecanum-dynamics"
        )
    ]
    assert any(
        "misses concept blocks" in issue.message
        for issue in validate_pr01_search_manifest(REPOSITORY_ROOT, missing_concept)
    )

    schema = load_json_strict(REPOSITORY_ROOT / "schemas/pr01-search-manifest.schema.json")
    schema_validator = Draft202012Validator(schema, format_checker=FormatChecker())
    wrong_crossref_policy = deepcopy(manifest)
    crossref = next(
        database
        for database in wrong_crossref_policy["databases"]
        if database["database_id"] == "crossref"
    )
    semantic_scholar = next(
        database
        for database in wrong_crossref_policy["databases"]
        if database["database_id"] == "semantic-scholar"
    )
    crossref["retrieval_policy"] = deepcopy(semantic_scholar["retrieval_policy"])
    assert list(schema_validator.iter_errors(wrong_crossref_policy))

    crossref_cursor = deepcopy(manifest)
    next(
        query
        for query in crossref_cursor["queries"]
        if query["database_id"] == "crossref"
    )["exact_query"] += "&cursor=*"
    assert any(
        "must not use cursor pagination" in issue.message
        for issue in validate_pr01_search_manifest(REPOSITORY_ROOT, crossref_cursor)
    )

    crossref_substring = deepcopy(manifest)
    substring_query = next(
        query
        for query in crossref_substring["queries"]
        if query["database_id"] == "crossref"
    )
    substring_query["exact_query"] = substring_query["exact_query"].replace(
        "rows=1000",
        "notrows=1000x",
    )
    assert any(
        "must freeze rows=1000" in issue.message
        for issue in validate_pr01_search_manifest(REPOSITORY_ROOT, crossref_substring)
    )

    semantic_scholar_without_fields = deepcopy(manifest)
    semantic_query = next(
        query
        for query in semantic_scholar_without_fields["queries"]
        if query["database_id"] == "semantic-scholar"
    )
    semantic_query["exact_query"] = semantic_query["exact_query"].split("&fields=", 1)[0]
    assert any(
        "must freeze screening fields" in issue.message
        for issue in validate_pr01_search_manifest(
            REPOSITORY_ROOT,
            semantic_scholar_without_fields,
        )
    )


def test_pr01_raw_search_manifest_binds_execution_to_frozen_query(tmp_path: Path) -> None:
    search_manifest = load_json_strict(
        REPOSITORY_ROOT / "research/metadata/pr01_search_manifest.json"
    )
    raw_manifest = load_json_strict(
        REPOSITORY_ROOT / "research/metadata/pr01_raw_search_export_manifest.json"
    )
    assert validate_pr01_raw_search_manifest(
        REPOSITORY_ROOT,
        raw_manifest,
        search_manifest,
    ) == []

    planned_query, snapshot = _pr01_query_snapshot(search_manifest, "crossref")
    part = _write_pr01_json_part(
        tmp_path,
        "references/literature/raw/crossref-zero.json",
        {"status": "ok", "message": {"total-results": 0, "items": []}},
        part_index=1,
        record_count=0,
        pagination=None,
    )
    execution = _pr01_execution(
        planned_query,
        snapshot,
        parts=[part],
        retrieved_record_count=0,
        source_reported_hit_count=0,
        termination_reason="source-exhausted-before-cap",
    )
    one_execution = deepcopy(raw_manifest)
    one_execution["executions"] = [execution]
    assert validate_pr01_raw_search_manifest(
        tmp_path,
        one_execution,
        search_manifest,
    ) == []

    changed_query = deepcopy(one_execution)
    changed_query["executions"][0]["query_snapshot"]["exact_query"] += " changed"
    assert any(
        "differs from frozen plan" in issue.message
        for issue in validate_pr01_raw_search_manifest(
            tmp_path,
            changed_query,
            search_manifest,
        )
    )

    early_execution = deepcopy(one_execution)
    early_execution["executions"][0]["executed_at_utc"] = "2026-08-01T15:00:00Z"
    assert any(
        "predates frozen plan" in issue.message
        for issue in validate_pr01_raw_search_manifest(
            tmp_path,
            early_execution,
            search_manifest,
        )
    )

    duplicate_execution = deepcopy(one_execution)
    duplicate_execution["executions"].append(deepcopy(execution))
    duplicate_messages = [
        issue.message
        for issue in validate_pr01_raw_search_manifest(
            tmp_path,
            duplicate_execution,
            search_manifest,
        )
    ]
    assert any("duplicate execution_id" in message for message in duplicate_messages)
    assert any("duplicate search execution" in message for message in duplicate_messages)

    premature_complete = deepcopy(one_execution)
    premature_complete["status"] = "POLICY-COMPLETE"
    premature_complete["completed_at_utc"] = "2026-08-01T17:00:01Z"
    assert any(
        "POLICY-COMPLETE raw manifest misses satisfied initial queries" in issue.message
        for issue in validate_pr01_raw_search_manifest(
            tmp_path,
            premature_complete,
            search_manifest,
        )
    )


@pytest.mark.parametrize(
    ("retrieved_count", "source_count", "termination_reason", "should_pass"),
    [
        (1000, 5000, "ranked-cap-reached", True),
        (999, 5000, "ranked-cap-reached", False),
        (600, 600, "source-exhausted-before-cap", True),
    ],
)
def test_pr01_crossref_ranked_cap_policy(
    tmp_path: Path,
    retrieved_count: int,
    source_count: int,
    termination_reason: str,
    should_pass: bool,
) -> None:
    search_manifest = load_json_strict(
        REPOSITORY_ROOT / "research/metadata/pr01_search_manifest.json"
    )
    raw_manifest = load_json_strict(
        REPOSITORY_ROOT / "research/metadata/pr01_raw_search_export_manifest.json"
    )
    planned_query, snapshot = _pr01_query_snapshot(search_manifest, "crossref")
    items = [{"DOI": f"10.0000/{index}"} for index in range(retrieved_count)]
    part = _write_pr01_json_part(
        tmp_path,
        "references/literature/raw/crossref-ranked.json",
        {"status": "ok", "message": {"total-results": source_count, "items": items}},
        part_index=1,
        record_count=retrieved_count,
        pagination=None,
    )
    execution = _pr01_execution(
        planned_query,
        snapshot,
        parts=[part],
        retrieved_record_count=retrieved_count,
        source_reported_hit_count=source_count,
        termination_reason=termination_reason,
    )
    candidate = deepcopy(raw_manifest)
    candidate["executions"] = [execution]

    issues = validate_pr01_raw_search_manifest(tmp_path, candidate, search_manifest)
    assert (issues == []) is should_pass
    if not should_pass:
        assert any("ranked-cap policy" in issue.message for issue in issues)


def test_pr01_crossref_failed_request_is_recordable(tmp_path: Path) -> None:
    search_manifest = load_json_strict(
        REPOSITORY_ROOT / "research/metadata/pr01_search_manifest.json"
    )
    raw_manifest = load_json_strict(
        REPOSITORY_ROOT / "research/metadata/pr01_raw_search_export_manifest.json"
    )
    planned_query, snapshot = _pr01_query_snapshot(search_manifest, "crossref")
    failed_execution = _pr01_execution(
        planned_query,
        snapshot,
        parts=[],
        retrieved_record_count=0,
        source_reported_hit_count=None,
        termination_reason="request-failed",
        outcome_status="FAILED",
        incompleteness_reason="HTTP request failed before a response was retained.",
    )
    candidate = deepcopy(raw_manifest)
    candidate["executions"] = [failed_execution]
    assert validate_pr01_raw_search_manifest(tmp_path, candidate, search_manifest) == []

    raw_schema = load_json_strict(
        REPOSITORY_ROOT / "schemas/pr01-raw-search-export-manifest.schema.json"
    )
    schema_validator = Draft202012Validator(raw_schema, format_checker=FormatChecker())
    assert list(schema_validator.iter_errors(candidate)) == []

    contradictory = deepcopy(candidate)
    contradictory["executions"][0]["retrieval_outcome"][
        "termination_reason"
    ] = "ranked-cap-reached"
    assert list(schema_validator.iter_errors(contradictory))


def test_pr01_semantic_scholar_token_policy_and_estimated_total(tmp_path: Path) -> None:
    search_manifest = load_json_strict(
        REPOSITORY_ROOT / "research/metadata/pr01_search_manifest.json"
    )
    raw_manifest = load_json_strict(
        REPOSITORY_ROOT / "research/metadata/pr01_raw_search_export_manifest.json"
    )
    planned_query, snapshot = _pr01_query_snapshot(search_manifest, "semantic-scholar")
    part_one = _write_pr01_json_part(
        tmp_path,
        "references/literature/raw/semantic-scholar-page-1.json",
        {"total": 3000, "token": "next-1", "data": [{"paperId": "p1"}]},
        part_index=1,
        record_count=1,
        pagination={"request_token": None, "response_next_token": "next-1"},
    )
    part_two = _write_pr01_json_part(
        tmp_path,
        "references/literature/raw/semantic-scholar-page-2.json",
        {"total": 3000, "data": [{"paperId": "p2"}]},
        part_index=2,
        record_count=1,
        pagination={"request_token": "next-1", "response_next_token": None},
    )
    execution = _pr01_execution(
        planned_query,
        snapshot,
        parts=[part_one, part_two],
        retrieved_record_count=2,
        source_reported_hit_count=3000,
        termination_reason="pagination-exhausted",
    )
    candidate = deepcopy(raw_manifest)
    candidate["executions"] = [execution]
    assert validate_pr01_raw_search_manifest(tmp_path, candidate, search_manifest) == []

    zero_part = _write_pr01_json_part(
        tmp_path,
        "references/literature/raw/semantic-scholar-zero.json",
        {"total": 0, "data": []},
        part_index=1,
        record_count=0,
        pagination={"request_token": None, "response_next_token": None},
    )
    zero_result = deepcopy(raw_manifest)
    zero_result["executions"] = [
        _pr01_execution(
            planned_query,
            snapshot,
            parts=[zero_part],
            retrieved_record_count=0,
            source_reported_hit_count=0,
            termination_reason="pagination-exhausted",
        )
    ]
    assert validate_pr01_raw_search_manifest(tmp_path, zero_result, search_manifest) == []

    broken_chain = deepcopy(candidate)
    broken_chain["executions"][0]["parts"][1]["pagination"]["request_token"] = "wrong"
    assert any(
        "continuation-token chain is broken" in issue.message
        for issue in validate_pr01_raw_search_manifest(
            tmp_path,
            broken_chain,
            search_manifest,
        )
    )

    duplicate_paper = deepcopy(candidate)
    duplicate_payload = {
        "total": 3000,
        "data": [{"paperId": "p1"}],
    }
    duplicate_paper["executions"][0]["parts"][1] = _write_pr01_json_part(
        tmp_path,
        "references/literature/raw/semantic-scholar-page-2-duplicate.json",
        duplicate_payload,
        part_index=2,
        record_count=1,
        pagination={"request_token": "next-1", "response_next_token": None},
    )
    assert any(
        "paperId is missing or duplicated" in issue.message
        for issue in validate_pr01_raw_search_manifest(
            tmp_path,
            duplicate_paper,
            search_manifest,
        )
    )


def test_pr01_semantic_scholar_rejects_terminal_continuation_token(tmp_path: Path) -> None:
    search_manifest = load_json_strict(
        REPOSITORY_ROOT / "research/metadata/pr01_search_manifest.json"
    )
    raw_manifest = load_json_strict(
        REPOSITORY_ROOT / "research/metadata/pr01_raw_search_export_manifest.json"
    )
    planned_query, snapshot = _pr01_query_snapshot(search_manifest, "semantic-scholar")
    part = _write_pr01_json_part(
        tmp_path,
        "references/literature/raw/semantic-scholar-not-terminal.json",
        {"total": 2, "token": "still-more", "data": [{"paperId": "p1"}]},
        part_index=1,
        record_count=1,
        pagination={"request_token": None, "response_next_token": "still-more"},
    )
    execution = _pr01_execution(
        planned_query,
        snapshot,
        parts=[part],
        retrieved_record_count=1,
        source_reported_hit_count=2,
        termination_reason="pagination-exhausted",
    )
    candidate = deepcopy(raw_manifest)
    candidate["executions"] = [execution]
    assert any(
        "retains a continuation token" in issue.message
        for issue in validate_pr01_raw_search_manifest(tmp_path, candidate, search_manifest)
    )


def test_duplicate_json_keys_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text('{"schema_version":"1.0.0","schema_version":"2.0.0"}', encoding="utf-8")

    with pytest.raises(DuplicateJsonKeyError, match="duplicate JSON key"):
        load_json_strict(path)


def test_obsidian_broken_link_and_frontmatter_are_reported(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "valid.md").write_text(
        "---\ntype: note\nstatus: active\n---\n\n[[missing/note]]\n",
        encoding="utf-8",
    )
    (vault / "invalid.md").write_text("no frontmatter", encoding="utf-8")

    issues, note_count, link_count = validate_obsidian_vault(vault)

    assert note_count == 2
    assert link_count == 1
    messages = json.dumps([issue.message for issue in issues])
    assert "unresolved wikilink" in messages
    assert "missing YAML frontmatter" in messages
