"""lovarch consolidate — Generate DOSSIER.zip from a completed run.

Walks ~/.lovarch/projects/<name>/output/ and produces a structured ZIP
that mirrors the dossier format expected by Lovarch's downstream consumers
(architects sharing with clients, builders importing into BIM, etc.).

Folder convention inside the ZIP (matches the squad's deliverable layout):

    DOSSIER-<project>-<YYYY-MM-DD>.zip
    ├── 00-validation/    audit + input-validation JSONs
    ├── 01-bootstrap/     project metadata, project.yaml snapshot
    ├── 02-concept/       moodboard + render images
    ├── 03-tier1/         CAD/IFC/PDF/XLSX from tier-1 agents
    ├── 04-tier2/         QA reports
    └── 05-dossier/       briefing-architect, regolatorio, energy

Files in output/ that don't match a known prefix go into 99-other/ so we
never silently drop content. The user can inspect what landed there to
catch missing routing rules.

Free mode (no real run): we still zip whatever is in output/, even if
empty — useful for users who want to package their own deliverables and
hand them off without going through Premium.
"""
from __future__ import annotations

import sys
import zipfile
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


# Routing prefixes → DOSSIER folder.
# The squad pipeline writes filenames with these prefixes; if a new
# convention shows up, add the mapping here rather than scattering it.
_ROUTING: list[tuple[str, str]] = [
    ("input-validation", "00-validation"),
    ("audit-", "00-validation"),
    ("project-", "01-bootstrap"),
    ("bootstrap-", "01-bootstrap"),
    ("moodboard-", "02-concept"),
    ("render-", "02-concept"),
    ("brief-", "02-concept"),
    ("dxf-", "03-tier1"),
    ("ifc-", "03-tier1"),
    ("pianta-", "03-tier1"),
    ("sezione-", "03-tier1"),
    ("computo-", "03-tier1"),
    ("capitolato-", "03-tier1"),
    ("contratto-", "03-tier1"),
    ("qa-", "04-tier2"),
    ("verifica-", "04-tier2"),
    ("briefing-architect", "05-dossier"),
    ("regolatorio-", "05-dossier"),
    ("energy-", "05-dossier"),
    ("dossier-", "05-dossier"),
]


def _route_filename(name: str) -> str:
    """Map a filename prefix to its DOSSIER folder, or '99-other/' fallback."""
    lower = name.lower()
    for prefix, folder in _ROUTING:
        if lower.startswith(prefix):
            return folder
    return "99-other"


def _gather_files(output_dir: Path) -> list[tuple[Path, str]]:
    """Return (abs_path, arcname) tuples for every file under output_dir."""
    items: list[tuple[Path, str]] = []
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file():
            continue
        # Use the file's name relative to output_dir for routing,
        # but preserve any subdir structure inside the routed folder.
        rel = path.relative_to(output_dir)
        first_component = rel.parts[0]
        # If the user already organized into 0X-foo/, preserve it.
        if "-" in first_component and first_component[:2].isdigit():
            arcname = str(rel)
        else:
            folder = _route_filename(rel.name)
            arcname = f"{folder}/{rel.name}"
        items.append((path, arcname))
    return items


def consolidate_command(
    project: Annotated[
        str, typer.Argument(help="Project name to consolidate.")
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Where to write the ZIP (default: project's output/ dir).",
        ),
    ] = None,
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
) -> None:
    """Bundle the run output into a DOSSIER.zip."""
    if lang_flag is not None:
        set_current_lang(lang_flag)
    lang = current_lang()

    home = home_override or DEFAULT_HOME
    proj_dir = home / "projects" / project
    if not proj_dir.is_dir():
        err_console.print(
            f"\n[red]✗ {t('consolidate.no_project', lang=lang, name=project)}[/red]\n"
        )
        sys.exit(2)

    output_dir = proj_dir / "output"
    if not output_dir.is_dir():
        err_console.print(
            f"\n[red]✗ {t('consolidate.no_output', lang=lang, path=str(output_dir))}[/red]\n"
        )
        sys.exit(2)

    items = _gather_files(output_dir)
    if not items:
        err_console.print(
            f"\n[yellow]⚠ {t('consolidate.empty_output', lang=lang, name=project)}[/yellow]\n"
        )
        sys.exit(1)

    # ─── Choose ZIP path ─────────────────────────────────────────────────
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    zip_name = f"DOSSIER-{project}-{today}.zip"
    zip_path = output / zip_name if output else proj_dir / zip_name

    # ─── Write ZIP ───────────────────────────────────────────────────────
    console.print(
        f"\n[gold1]→[/gold1] {t('consolidate.zipping', lang=lang, count=len(items))}"
    )
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for src, arcname in items:
                zf.write(src, arcname=arcname)
            # Drop a small README inside the ZIP describing the layout.
            zf.writestr(
                "README.md",
                t(
                    "consolidate.zip_readme",
                    lang=lang,
                    project=project,
                    date=today,
                    count=len(items),
                ),
            )
    except OSError as exc:
        err_console.print(
            f"\n[red]✗ {t('consolidate.write_failed', lang=lang, message=str(exc))}[/red]\n"
        )
        sys.exit(2)

    # ─── Persist last_dossier in project.yaml ────────────────────────────
    yaml_path = proj_dir / "project.yaml"
    if yaml_path.exists():
        try:
            meta = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            meta = {}
        meta["last_dossier"] = {
            "path": str(zip_path),
            "files": len(items),
            "size_bytes": zip_path.stat().st_size,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        yaml_path.write_text(
            yaml.safe_dump(meta, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    # ─── Success panel ───────────────────────────────────────────────────
    size_kb = zip_path.stat().st_size // 1024
    body = Text.from_markup(
        f"{t('consolidate.created', lang=lang, path=str(zip_path), size_kb=size_kb, count=len(items))}\n\n"
        f"{t('consolidate.next_steps', lang=lang, project=project)}"
    )
    console.print()
    console.print(
        Panel(
            body,
            title=f"[bold green]📦 {t('consolidate.title', lang=lang)}[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print()
