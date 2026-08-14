from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[3]
ACTIVE_SOURCE_ROOTS = (
    REPOSITORY / "src",
    REPOSITORY / "matlab",
)
TEX_SUFFIX = "." + "t" + "ex"
FORBIDDEN_TOKENS = (
    "docs" + "/" + "paper",
    "docs" + "\\" + "paper",
    "main" + TEX_SUFFIX,
    "generated_results" + TEX_SUFFIX,
    "generate_" + "paper_" + "results",
    "tec" + "tonic",
    "pdf" + "la" + "tex",
    "xe" + "la" + "tex",
    "lua" + "la" + "tex",
    "la" + "texmk",
)


def test_active_source_has_no_local_manuscript_writer_or_builder() -> None:
    violations: list[str] = []
    for root in ACTIVE_SOURCE_ROOTS:
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            if path.suffix.lower() not in {".py", ".m"}:
                continue
            if path.resolve() == Path(__file__).resolve():
                continue
            content = path.read_text(encoding="utf-8").lower()
            for token in FORBIDDEN_TOKENS:
                if token in content:
                    relative = path.relative_to(REPOSITORY).as_posix()
                    violations.append(f"{relative}: {token}")
    assert not violations, "local-paper firewall violations:\n" + "\n".join(violations)


def test_obsolete_manuscript_macro_tools_are_absent() -> None:
    tool_name = "generate_" + "paper_" + "results.py"
    test_name = "test_" + "paper_" + "results.py"
    assert not (REPOSITORY / "src/tools" / tool_name).exists()
    assert not (REPOSITORY / "tests/python/tests" / test_name).exists()
