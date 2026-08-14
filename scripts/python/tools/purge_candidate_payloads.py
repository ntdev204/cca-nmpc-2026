from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TARGETS = (
    "data/raw/web-cohort-20260814",
    "experiments/runs",
    "experiments/commands",
    "models/candidates",
)


def main() -> int:
    root = ROOT.resolve()
    paths = []
    for relative in TARGETS:
        path = (root / relative).resolve()
        if root not in path.parents:
            raise RuntimeError(f"unsafe purge target: {path}")
        if not path.exists():
            continue
        paths.append(path)
    if not paths:
        print("no candidate payloads found")
        return 0
    deleted_files = 0
    deleted_bytes = 0
    for path in paths:
        if path.is_dir():
            for child in sorted(path.rglob("*"), reverse=True):
                if child.is_file() or child.is_symlink():
                    deleted_files += 1
                    deleted_bytes += child.stat().st_size if child.is_file() else 0
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
            path.rmdir()
        else:
            deleted_files += 1
            deleted_bytes += path.stat().st_size
            path.unlink()
    print(
        f"purged {len(paths)} candidate/development targets; "
        f"files={deleted_files}; bytes={deleted_bytes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
