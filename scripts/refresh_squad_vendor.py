"""Refresh the vendored squad payload in lovarch_cli/squad/ from the monorepo.

Run this script from this repo root, on Pablo's machine, when
squads/architettura-progetto/ in /Users/pablo/Lovarch/ has been updated
and you want to propagate the change to the standalone lovarch-cli repo.

Usage:
    cd /Users/pablo/lovarch-cli
    python3 scripts/refresh_squad_vendor.py

Result: lovarch_cli/squad/ is replaced with a fresh copy from the monorepo
(skipping heavy sample-inputs — those go to GitHub Releases). After running,
review the diff with `git diff --stat lovarch_cli/squad/` and commit if it
looks correct.

Heavy sample-inputs (data/sample-input/, data/sample-input-villa-chianti/)
are NOT vendored — see docs/squad-vendoring.md for the lazy-download story.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

MONOREPO_SQUAD = Path("/Users/pablo/Lovarch/squads/architettura-progetto")
LOCAL_SQUAD_DST = Path(__file__).resolve().parent.parent / "lovarch_cli" / "squad"

COPY_DIRS = (
    "agents",
    "tasks",
    "workflows",
    "checklists",
    "templates",
    "scripts",
    "data",
)
COPY_FILES = ("README.md", "config.yaml")
EXCLUDE_RELATIVE = frozenset({
    "data/sample-input",
    "data/sample-input-villa-chianti",
})


def _ignore_excluded(squad_src: Path):
    def _ignore(_dir: str, names: list[str]) -> list[str]:
        base = Path(_dir).relative_to(squad_src)
        return [
            n for n in names
            if str((base / n).as_posix()) in EXCLUDE_RELATIVE
        ]
    return _ignore


def main() -> int:
    if not MONOREPO_SQUAD.exists():
        print(f"ERROR: monorepo squad not found at {MONOREPO_SQUAD}", file=sys.stderr)
        print("This script only works on Pablo's machine with the Lovarch monorepo cloned.", file=sys.stderr)
        return 1

    # Wipe the destination clean (avoids stale files from removed agents/tasks)
    if LOCAL_SQUAD_DST.exists():
        for child in LOCAL_SQUAD_DST.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    LOCAL_SQUAD_DST.mkdir(parents=True, exist_ok=True)

    # Copy directories (skipping heavy excludes)
    ignore = _ignore_excluded(MONOREPO_SQUAD)
    copied_dirs = 0
    for dirname in COPY_DIRS:
        src_dir = MONOREPO_SQUAD / dirname
        if src_dir.exists() and src_dir.is_dir():
            shutil.copytree(src_dir, LOCAL_SQUAD_DST / dirname, ignore=ignore)
            copied_dirs += 1

    # Copy top-level files
    copied_files = 0
    for filename in COPY_FILES:
        src_file = MONOREPO_SQUAD / filename
        if src_file.exists() and src_file.is_file():
            shutil.copy2(src_file, LOCAL_SQUAD_DST / filename)
            copied_files += 1

    total = sum(1 for _ in LOCAL_SQUAD_DST.rglob("*") if _.is_file())
    print(f"OK: vendored {copied_dirs} dirs + {copied_files} top-level files")
    print(f"    {total} files total at {LOCAL_SQUAD_DST}")
    print()
    print("Next: review with `git diff --stat lovarch_cli/squad/`")
    print("      then commit if the diff matches the monorepo change you intended.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
