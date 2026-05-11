"""lovarch init — Create a new project directory.

Creates ~/.lovarch/projects/<project>/ with input/ and output/ subdirs and
a project.yaml metadata file. With --sample copies the bundled villa-chianti
sample-input as a starter pack the user can run end-to-end with no extra work.

Project layout after `lovarch init my-villa --sample`:

    ~/.lovarch/projects/my-villa/
    ├── project.yaml          # name, created_at, workflow, mode
    ├── input/                # 18 input files (briefing, photos, DXF, etc.)
    │   ├── architetto-info.json
    │   ├── briefing-cliente.md
    │   ├── foto/
    │   ├── pinterest-references/
    │   ├── README.md
    │   ├── stato-attuale.dxf
    │   ├── stato-attuale.png
    │   └── visura-catastale.pdf
    └── output/               # populated by `lovarch run`

The sample comes from the bundled squad payload (lovarch_cli/squad/), so it
ships with the pip package — no separate download needed.
"""
from __future__ import annotations

import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from lovarch_cli.config import DEFAULT_HOME
from lovarch_cli.i18n import current_lang, set_current_lang, t

console = Console()
err_console = Console(stderr=True)

# Valid project name pattern: lowercase letters, digits, hyphens.
# Forbids path-traversal characters and shell-unfriendly chars.
PROJECT_NAME_RX = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")

# Sample-input villa-chianti is NOT bundled in the wheel (49MB of photos/DXF/
# PDF — too heavy). It ships as a GitHub Releases asset and lovarch_cli.
# sample_downloader.resolve_sample_source() handles bundled→cache→download
# resolution transparently.


def _project_dir(home: Path, name: str) -> Path:
    return home / "projects" / name


def init_command(
    project: Annotated[
        str,
        typer.Argument(
            help="Project name (lowercase letters/digits/hyphens, 2-63 chars).",
        ),
    ],
    sample: Annotated[
        bool,
        typer.Option(
            "--sample",
            help="Copy the bundled villa-chianti sample-input as a starter.",
        ),
    ] = False,
    workflow: Annotated[
        str,
        typer.Option(
            "--workflow",
            help="Target workflow this project will run against.",
        ),
    ] = "dal-brief-al-cantiere",
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Overwrite an existing project directory (dangerous).",
        ),
    ] = False,
    lang_flag: Annotated[
        str | None,
        typer.Option("--lang", "-l", help="Override language (it/pt/en/es)."),
    ] = None,
    home_override: Annotated[
        Path | None,
        typer.Option(
            "--home",
            help="Override $HOME/.lovarch root (mainly for tests).",
            hidden=True,
        ),
    ] = None,
    squad_src: Annotated[
        Path | None,
        typer.Option(
            "--squad-src",
            help=(
                "Path to a squad-architettura-progetto source dir. Also reads "
                "$LOVARCH_SQUAD_SRC. When set, --sample reads the villa-"
                "chianti sample from this path instead of downloading."
            ),
        ),
    ] = None,
) -> None:
    """Initialize a new project directory."""
    if lang_flag is not None:
        set_current_lang(lang_flag)
    lang = current_lang()

    # ─── Validate project name ───────────────────────────────────────────
    if not PROJECT_NAME_RX.match(project):
        err_console.print(
            f"\n[red]✗ {t('init.invalid_name', lang=lang, name=project)}[/red]\n"
        )
        sys.exit(2)

    home = home_override or DEFAULT_HOME
    proj_dir = _project_dir(home, project)

    # ─── Handle existing project ─────────────────────────────────────────
    if proj_dir.exists():
        if not force:
            err_console.print(
                f"\n[yellow]{t('init.already_exists', lang=lang, name=project, path=str(proj_dir))}[/yellow]\n"
            )
            sys.exit(1)
        shutil.rmtree(proj_dir)

    # ─── Create dir tree ─────────────────────────────────────────────────
    input_dir = proj_dir / "input"
    output_dir = proj_dir / "output"
    input_dir.mkdir(parents=True)
    output_dir.mkdir()

    # ─── Optional: resolve + copy sample-input (lazy download if needed) ─
    sample_copied_count = 0
    sample_origin: str | None = None
    if sample:
        from lovarch_cli.sample_downloader import (
            SampleDownloadError,
            resolve_sample_source,
        )

        try:
            resolved = resolve_sample_source(
                console=console,
                lang=lang,
                home=home,
                squad_src=squad_src,
            )
            src = resolved.path
            sample_origin = resolved.origin
        except SampleDownloadError as exc:
            err_console.print(f"\n[red]✗ {exc}[/red]")
            err_console.print(
                f"[dim]{t('init.sample_hint', lang=lang)}[/dim]\n"
            )
            # Don't bail: project dir exists, user can still add own input.
        else:
            for item in src.iterdir():
                if item.is_dir():
                    shutil.copytree(item, input_dir / item.name)
                else:
                    shutil.copy2(item, input_dir / item.name)
            sample_copied_count = sum(1 for _ in input_dir.rglob("*") if _.is_file())

    # ─── Write project.yaml metadata ─────────────────────────────────────
    metadata = {
        "name": project,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "workflow": workflow,
        "sample": sample,
        "cli_version": _cli_version(),
    }
    (proj_dir / "project.yaml").write_text(
        yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    # ─── Success panel ───────────────────────────────────────────────────
    body_lines: list[str] = [
        t("init.created", lang=lang, path=str(proj_dir)),
    ]
    if sample and sample_copied_count > 0:
        body_lines.append(
            t("init.sample_copied", lang=lang, count=sample_copied_count)
        )
        if sample_origin in {"cache", "download"}:
            body_lines.append(
                f"[dim]{t(f'init.sample_origin_{sample_origin}', lang=lang)}[/dim]"
            )
    body_lines.append("")
    body_lines.append(t("init.next_steps", lang=lang, name=project))

    console.print()
    console.print(
        Panel(
            Text.from_markup("\n".join(body_lines)),
            title=f"[bold gold1]🌱 {t('init.title', lang=lang, name=project)}[/bold gold1]",
            border_style="gold1",
            padding=(1, 2),
        )
    )
    console.print()


def _cli_version() -> str:
    """Read version lazily — avoids circular import at module load."""
    from lovarch_cli.version import __version__

    return __version__
