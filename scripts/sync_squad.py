"""Hatchling build hook — sync architettura-progetto squad into the package.

This hook runs at build time (uv build, pip install -e .) and copies relevant
files from sibling squads/architettura-progetto/ into archprime_cli/squad/ so
the published wheel ships with the squad as bundled package data.

WITHOUT this sync, the CLI ships empty — `arch run` would have no agents to
orchestrate, no tasks to execute, no workflow YAML to follow. This is a
CRITICAL build step.

Behavior:
- Looks for squads/architettura-progetto/ as sibling of cli/ (monorepo dev)
- Falls back to NO-OP if running inside an isolated CI sdist (squad already
  bundled by previous sync). The .gitkeep marker in archprime_cli/squad/
  ensures the directory exists even before first sync.

Repository layout (monorepo dev):
    Lovarch/
    ├── cli/                        ← this package
    │   ├── pyproject.toml          ← references scripts/sync_squad.py
    │   ├── archprime_cli/squad/    ← target (gitignored, populated here)
    │   └── scripts/sync_squad.py   ← this file
    └── squads/architettura-progetto/   ← source (sibling)
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
    "data",
)
SQUAD_FILES: tuple[str, ...] = ("README.md", "config.yaml")


class SyncSquadBuildHook(BuildHookInterface):
    """Sync architettura-progetto squad files into archprime_cli/squad/."""

    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """Copy squad files into the package before build artifacts are produced."""
        cli_root = Path(self.root).resolve()
        repo_root = cli_root.parent
        squad_src = repo_root / "squads" / SQUAD_NAME
        squad_dst = cli_root / "archprime_cli" / "squad"

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

        # Copy directories
        copied_dirs = 0
        for dirname in COPY_DIRS:
            src_dir = squad_src / dirname
            if src_dir.exists() and src_dir.is_dir():
                shutil.copytree(src_dir, squad_dst / dirname)
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
