"""lovarch dev — developer tooling for working on the squad payload.

Subcommands:

  lovarch dev show-squad-root
      Print which squad payload would be used by `lovarch run` right now,
      and where the resolution chain landed (override flag / env var /
      bundled).

  lovarch dev refresh-squad [--source PATH] [--target PATH] [--dry-run]
      Copy the squad source-of-truth (default: $LOVARCH_SQUAD_SRC or
      `~/Lovarch/squads/architettura-progetto/`) into the standalone
      repo's vendored copy at `lovarch_cli/squad/`. Excludes the heavy
      sample-input directories — those ship via GitHub Releases. This is
      the "promote dev edits to staged" step before cutting a release.

These commands are intended for Pablo / future contributors maintaining
the squad. Brew-installed users never need them.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from lovarch_cli.squad_loader import (
    ENV_VAR,
    SquadNotFoundError,
    bundled_squad_dir,
    resolve_squad_root,
    squad_source_label,
)


console = Console()
err_console = Console(stderr=True)

dev_app = typer.Typer(
    help="Developer tooling for the squad payload (Pablo / contributors only).",
    no_args_is_help=True,
)


# What the build hook + refresh script copy. Mirror of scripts/sync_squad.py.
COPY_DIRS: tuple[str, ...] = (
    "agents",
    "tasks",
    "workflows",
    "checklists",
    "templates",
    "scripts",
    "data",
)
COPY_FILES: tuple[str, ...] = ("README.md", "config.yaml")
# Heavy sample-inputs that ship via GitHub Releases instead.
EXCLUDE_RELATIVE: frozenset[str] = frozenset({
    "data/sample-input",
    "data/sample-input-villa-chianti",
})
DEFAULT_SOURCE = Path.home() / "Lovarch" / "squads" / "architettura-progetto"


@dev_app.command("show-squad-root")
def show_squad_root_command(
    squad_src: Annotated[
        Path | None,
        typer.Option(
            "--squad-src",
            help="Mirror the --squad-src flag passed to `lovarch run`.",
        ),
    ] = None,
) -> None:
    """Show which squad payload `lovarch run` would currently use."""
    try:
        root = resolve_squad_root(override=squad_src)
    except SquadNotFoundError as exc:
        err_console.print(f"\n[red]✗ {exc}[/red]\n")
        sys.exit(2)

    label = squad_source_label(root)
    env_val = os.environ.get(ENV_VAR) or "(unset)"

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()
    table.add_row("Resolved path:", str(root))
    table.add_row("Source:", label)
    table.add_row(f"${ENV_VAR}:", env_val)
    table.add_row("Bundled vendor:", str(bundled_squad_dir()))

    console.print()
    console.print(
        Panel(
            table,
            title="[bold gold1]🔍 Squad resolution[/bold gold1]",
            border_style="gold1",
            padding=(1, 2),
        )
    )
    console.print()


def _ignore_excluded(squad_src: Path):
    """shutil.copytree ignore-callback that skips EXCLUDE_RELATIVE dirs."""

    def _ignore(_dir: str, names: list[str]) -> list[str]:
        base = Path(_dir).relative_to(squad_src)
        return [
            n for n in names
            if str((base / n).as_posix()) in EXCLUDE_RELATIVE
        ]

    return _ignore


def _locate_target_default() -> Path | None:
    """Try to auto-detect the `lovarch_cli/squad/` dir in the dev install.

    Works when this file is imported from an editable install (i.e. the
    user's clone of `lovarch-cli`). Returns None when imported from a
    site-packages install (brew / pipx) — caller must require --target.
    """
    bundled = bundled_squad_dir()
    # Heuristic: if the bundled dir is writable AND lives inside a path
    # that does NOT contain "site-packages" or "/Cellar/", treat it as
    # the dev-install target.
    try:
        path_str = str(bundled)
        if "site-packages" in path_str or "/Cellar/" in path_str:
            return None
        # Touch-test writability
        if not os.access(bundled, os.W_OK):
            return None
        return bundled
    except (OSError, PermissionError):
        return None


@dev_app.command("refresh-squad")
def refresh_squad_command(
    source: Annotated[
        Path | None,
        typer.Option(
            "--source",
            "-s",
            help=(
                "Source squad-architettura-progetto path. Defaults to "
                f"${ENV_VAR} or ~/Lovarch/squads/architettura-progetto."
            ),
        ),
    ] = None,
    target: Annotated[
        Path | None,
        typer.Option(
            "--target",
            "-t",
            help=(
                "Destination lovarch_cli/squad/ path. Auto-detected if "
                "running from a dev install (pip install -e), else required."
            ),
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Show what would change, no write.",
        ),
    ] = False,
) -> None:
    """Promote the dev squad source into the vendored snapshot."""
    # ── Resolve SOURCE ──────────────────────────────────────────────────
    if source is None:
        env_src = os.environ.get(ENV_VAR)
        if env_src:
            source = Path(env_src).expanduser().resolve()
        else:
            source = DEFAULT_SOURCE
    source = source.expanduser().resolve()

    if not source.is_dir():
        err_console.print(
            f"\n[red]✗ Source not found: {source}[/red]\n"
            f"[dim]Set ${ENV_VAR}, pass --source, or check that the path "
            f"exists.[/dim]\n"
        )
        sys.exit(2)
    if not (source / "scripts" / "pipeline_runner.py").exists():
        err_console.print(
            f"\n[red]✗ Source does not look like a squad payload: "
            f"missing scripts/pipeline_runner.py at {source}[/red]\n"
        )
        sys.exit(2)

    # ── Resolve TARGET ──────────────────────────────────────────────────
    if target is None:
        target = _locate_target_default()
    if target is None:
        err_console.print(
            "\n[red]✗ Cannot auto-detect target — you're not running from "
            "a dev install (pip install -e). Pass --target explicitly to "
            "the lovarch_cli/squad/ dir of your lovarch-cli clone.[/red]\n"
        )
        sys.exit(2)
    target = target.expanduser().resolve()

    # ── Plan ────────────────────────────────────────────────────────────
    summary = Table(show_header=False, box=None, padding=(0, 2))
    summary.add_column(style="bold")
    summary.add_column()
    summary.add_row("Source:", str(source))
    summary.add_row("Target:", str(target))
    summary.add_row("Dry-run:", "yes" if dry_run else "no")
    summary.add_row(
        "Excluded:",
        ", ".join(sorted(EXCLUDE_RELATIVE)),
    )
    console.print()
    console.print(
        Panel(
            summary,
            title="[bold gold1]🔄 Refresh squad vendor[/bold gold1]",
            border_style="gold1",
            padding=(1, 2),
        )
    )

    if dry_run:
        console.print(
            "[dim]Dry-run: no files modified. Re-run without --dry-run "
            "to apply.[/dim]\n"
        )
        return

    # ── Execute ─────────────────────────────────────────────────────────
    # Wipe target preserving the dir itself (so file ownership / git
    # status of the parent stays sane).
    target.mkdir(parents=True, exist_ok=True)
    for child in target.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    ignore = _ignore_excluded(source)
    copied_dirs = 0
    copied_files = 0
    for dirname in COPY_DIRS:
        src_dir = source / dirname
        if src_dir.exists() and src_dir.is_dir():
            shutil.copytree(src_dir, target / dirname, ignore=ignore)
            copied_dirs += 1
    for filename in COPY_FILES:
        src_file = source / filename
        if src_file.exists() and src_file.is_file():
            shutil.copy2(src_file, target / filename)
            copied_files += 1

    total_files = sum(1 for _ in target.rglob("*") if _.is_file())

    done = Text.from_markup(
        f"[green]✓[/green] Refreshed [bold]{copied_dirs}[/bold] dirs + "
        f"[bold]{copied_files}[/bold] top-level files\n"
        f"  [dim]{total_files} files total at {target}[/dim]\n\n"
        f"Next steps:\n"
        f"  1. [cyan]cd {target.parent.parent}[/cyan]\n"
        f"  2. [cyan]git diff --stat lovarch_cli/squad/[/cyan] — review the diff\n"
        f"  3. [cyan]git add lovarch_cli/squad/[/cyan] + commit\n"
        f"  4. Cut a release with [cyan]git tag v0.1.X && git push[/cyan]"
    )
    console.print(
        Panel(
            done,
            title="[bold green]✓ Refresh complete[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print()
