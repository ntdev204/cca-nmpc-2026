from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT

from repository import validate_repository


def repository_root() -> Path:
    return PROJECT_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate repository schemas, canonical JSON/YAML instances, file hashes, "
            "and Obsidian frontmatter/wikilinks without running research workloads."
        )
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=repository_root(),
        help="Repository root containing schemas/, configs/, registries, and research/obsidian/.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = validate_repository(
        args.workspace_root,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
