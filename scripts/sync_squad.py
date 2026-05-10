"""Hatchling build hook — sync architettura-progetto squad into the package.

This hook runs at build time (uv build, pip install -e .) and refreshes the
vendored squad payload in lovarch_cli/squad/ from a sibling source repo.

Two-mode behavior:

1. Standalone (default — public ArchPrime-official/lovarch-cli):
   No sibling squad/. Squad is committed inside lovarch_cli/squad/ as a
   light vendor (~830KB without sample-inputs). Hook detects missing source
   and exits NO-OP — preserves the committed payload. Sample-input villa-
   chianti (49MB) lives in GitHub Releases, downloaded by `lovarch init
   --sample` on demand.

2. Monorepo dev (Pablo's Lovarch repo with cli/):
   Hook finds sibling squads/architettura-progetto/, refreshes the vendored
   payload from it (skipping EXCLUDE_RELATIVE — heavy sample-inputs).
   Used to keep the standalone repo's vendor in sync via
   scripts/refresh_squad_vendor.py.

WITHOUT a populated squad, `arch run` and `arch init --sample` cannot
function — agents/tasks/workflows/templates and the pipeline_runner.py
must be present in lovarch_cli/squad/.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

SQUAD_NAME = "architettura-progetto"
COPY_DIRS: tuple[str, ...] = (
    "agents",
    "tasks",
    "workflows",
    "checklists",
    "templates",
    "scripts",
    "data",
)
SQUAD_FILES: tuple[str, ...] = ("README.md", "config.yaml")
# Excluded from vendor: heavy sample-inputs (~49MB of jpgs/pdfs/dxfs).
# These are shipped via GitHub Releases and downloaded lazily by
# `lovarch init --sample`. See docs/squad-vendoring.md.
EXCLUDE_RELATIVE: frozenset[str] = frozenset({
    "data/sample-input",
    "data/sample-input-villa-chianti",
})


class SyncSquadBuildHook(BuildHookInterface):
    """Sync architettura-progetto squad files into lovarch_cli/squad/."""

    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """Copy squad files into the package before build artifacts are produced."""
        cli_root = Path(self.root).resolve()
        repo_root = cli_root.parent
        squad_src = repo_root / "squads" / SQUAD_NAME
        squad_dst = cli_root / "lovarch_cli" / "squad"

        squad_dst.mkdir(parents=True, exist_ok=True)

        if not squad_src.exists():
            # Sdist build or external repo without sibling squad
            # Skip silently — squad/ may already be populated by previous sync.
            self.app.display_info(
                f"sync_squad: source not found at {squad_src} — skipping"
            )
            return

        # Clean target preserving .gitkeep marker for empty-dir signaling
        for child in squad_dst.iterdir():
            if child.name == ".gitkeep":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

        # Copy directories (skipping heavy excludes).
        def _ignore(_dir: str, names: list[str]) -> list[str]:
            base = Path(_dir).relative_to(squad_src)
            return [
                n for n in names
                if str((base / n).as_posix()) in EXCLUDE_RELATIVE
            ]

        copied_dirs = 0
        for dirname in COPY_DIRS:
            src_dir = squad_src / dirname
            if src_dir.exists() and src_dir.is_dir():
                shutil.copytree(src_dir, squad_dst / dirname, ignore=_ignore)
                copied_dirs += 1

        # Copy top-level files
        copied_files = 0
        for filename in SQUAD_FILES:
            src_file = squad_src / filename
            if src_file.exists() and src_file.is_file():
                shutil.copy2(src_file, squad_dst / filename)
                copied_files += 1

        self.app.display_info(
            f"sync_squad: synced {copied_dirs} dirs, {copied_files} files "
            f"from {squad_src} → {squad_dst}"
        )
