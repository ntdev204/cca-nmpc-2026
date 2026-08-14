import json

import pytest

from tools.validate_web_cohort import (
    RESET_HISTORICAL_ANNOTATIONS,
    RESET_HISTORICAL_MANIFEST,
    ROOT,
    manifest_binding_error,
    run_preflight,
)

from shared import sha256_file


def test_pr10_old_cohort_is_absent_after_reset() -> None:
    assert not (ROOT / RESET_HISTORICAL_MANIFEST).exists()
    assert not (ROOT / RESET_HISTORICAL_ANNOTATIONS).exists()


def test_pr10_preflight_fails_closed_until_new_acquisition() -> None:
    with pytest.raises(FileNotFoundError):
        run_preflight(ROOT, ROOT / RESET_HISTORICAL_MANIFEST, ROOT / RESET_HISTORICAL_ANNOTATIONS)


def test_pr10_independent_annotation_binding_uses_new_manifest_path(tmp_path) -> None:
    manifest = tmp_path / "data" / "manifest.json"
    manifest.parent.mkdir()
    manifest.write_text("{}\n", encoding="utf-8")
    source_ref = {"path": "data/manifest.json", "sha256": sha256_file(manifest)}
    assert manifest_binding_error(
        tmp_path,
        source_ref,
        "annotation",
        "data/manifest.json",
    ) is None


def test_clean_reset_has_no_retained_candidate_payloads() -> None:
    audit_path = ROOT / "research" / "metadata" / "development-purge-20260814.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["total_removed_files"] == 55
    assert audit["total_removed_bytes"] == 59260346
    for item in audit["removed"]:
        assert not (ROOT / item["path"]).exists(), item["path"]
    for relative, expected in (
        ("data/registry.json", []),
        ("models/registry.json", []),
        ("experiments/registry.json", []),
        ("artifacts/registry.json", []),
    ):
        payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        collection = next(value for key, value in payload.items() if key.endswith("s") and isinstance(value, list))
        assert collection == expected
