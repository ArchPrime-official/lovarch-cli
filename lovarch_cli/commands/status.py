"""lovarch status — Inspect project state and recent runs.

Two modes:
  - lovarch status            → list all projects + their last_audit / last_dossier
  - lovarch status <project>  → drill into one project: full last_audit detail,
                                  last_dossier, output/ file listing

Reads project.yaml metadata (no Lovarch backend required), so this works
identically in Free and Premium modes. For executions persisted via the
DataPersistenceClient (Story 1.3), a future revision will fetch step-level
status from the persistence layer; today we surface what the file system
+ project.yaml reveal.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from lovarch_cli.config import DEFAULT_HOME
from lovarch_cli.i18n import current_lang, set_current_lang, t

console = Console()
err_console = Console(stderr=True)


def _load_project_meta(proj_dir: Path) -> dict:
    yaml_path = proj_dir / "project.yaml"
    if not yaml_path.exists():
        return {}
    try:
        return yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}


def _format_relative_age(iso_ts: str | None) -> str:
    """Convert ISO 8601 → 'Xm ago' / 'Xh ago' / 'Xd ago'."""
    if not iso_ts:
        return "-"
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    except ValueError:
        return iso_ts
    delta = datetime.now(timezone.utc) - dt
    seconds = int(delta.total_seconds())
    if seconds < 0:
        return "just now"
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86_400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86_400}d ago"


_VERDICT_STYLE = {
    "PASS": "[bold green]PASS[/bold green]",
    "CONCERNS": "[bold yellow]CONCERNS[/bold yellow]",
    "FAIL": "[bold red]FAIL[/bold red]",
    None: "[dim]—[/dim]",
}


def _render_project_list(projects_root: Path, lang: str) -> Table:
    """Table view: all projects with their audit+dossier state."""
    table = Table(
        title=t("status.list_title", lang=lang),
        title_style="bold gold1",
        header_style="bold",
    )
    table.add_column(t("status.col_project", lang=lang), no_wrap=True)
    table.add_column(t("status.col_workflow", lang=lang))
    table.add_column(t("status.col_audit", lang=lang), no_wrap=True)
    table.add_column(t("status.col_dossier", lang=lang), no_wrap=True)
    table.add_column(t("status.col_age", lang=lang), no_wrap=True)

    for proj_dir in sorted(projects_root.iterdir()):
        if not proj_dir.is_dir():
            continue
        meta = _load_project_meta(proj_dir)
        last_audit = meta.get("last_audit") or {}
        last_dossier = meta.get("last_dossier") or {}
        verdict_label = _VERDICT_STYLE.get(
            last_audit.get("verdict"), _VERDICT_STYLE[None]
        )
        dossier_label = (
            f"[green]✓[/green] {last_dossier.get('files', 0)} files"
            if last_dossier
            else "[dim]—[/dim]"
        )
        # Age is the freshest of created_at / last_audit / last_dossier
        most_recent = max(
            (
                ts for ts in [
                    meta.get("created_at"),
                    last_dossier.get("created_at"),
                ]
                if ts
            ),
            default=None,
        )
        table.add_row(
            proj_dir.name,
            meta.get("workflow", "-"),
            verdict_label,
            dossier_label,
            _format_relative_age(most_recent),
        )
    return table


def _render_project_detail(proj_dir: Path, lang: str) -> None:
    """Drill-down view for a single project."""
    meta = _load_project_meta(proj_dir)
    name = proj_dir.name

    body_lines = [
        f"[dim]{t('status.label_workflow', lang=lang)}:[/dim] [bold]{meta.get('workflow', '-')}[/bold]",
        f"[dim]{t('status.label_created', lang=lang)}:[/dim] {meta.get('created_at', '-')}",
        f"[dim]{t('status.label_sample', lang=lang)}:[/dim] {meta.get('sample', False)}",
    ]

    # Audit section
    last_audit = meta.get("last_audit")
    if last_audit:
        verdict = last_audit.get("verdict")
        body_lines.append("")
        body_lines.append(
            f"[bold]{t('status.section_audit', lang=lang)}:[/bold] "
            f"{_VERDICT_STYLE.get(verdict, _VERDICT_STYLE[None])} — "
            f"PASS={last_audit.get('pass_count', 0)} · "
            f"CONCERNS={last_audit.get('concerns_count', 0)} · "
            f"FAIL={last_audit.get('fail_count', 0)}"
        )
    else:
        body_lines.append("")
        body_lines.append(
            f"[bold]{t('status.section_audit', lang=lang)}:[/bold] "
            f"[dim]{t('status.no_audit_yet', lang=lang)}[/dim]"
        )

    # Dossier section
    last_dossier = meta.get("last_dossier")
    if last_dossier:
        size_kb = (last_dossier.get("size_bytes", 0)) // 1024
        body_lines.append(
            f"[bold]{t('status.section_dossier', lang=lang)}:[/bold] "
            f"[green]{last_dossier.get('files', 0)} files · {size_kb} KB[/green] "
            f"[dim]({_format_relative_age(last_dossier.get('created_at'))})[/dim]"
        )
        body_lines.append(f"  [dim]{last_dossier.get('path')}[/dim]")
    else:
        body_lines.append(
            f"[bold]{t('status.section_dossier', lang=lang)}:[/bold] "
            f"[dim]{t('status.no_dossier_yet', lang=lang)}[/dim]"
        )

    # Output dir glance: count files
    output_dir = proj_dir / "output"
    if output_dir.is_dir():
        n_output = sum(1 for _ in output_dir.rglob("*") if _.is_file())
        body_lines.append("")
        body_lines.append(
            f"[bold]{t('status.section_output', lang=lang)}:[/bold] "
            f"{n_output} files in [dim]{output_dir}[/dim]"
        )

    console.print()
    console.print(
        Panel(
            Text.from_markup("\n".join(body_lines)),
            title=f"[bold gold1]📋 {t('status.detail_title', lang=lang, name=name)}[/bold gold1]",
            border_style="gold1",
            padding=(1, 2),
        )
    )
    console.print()


def status_command(
    project: Annotated[
        str | None,
        typer.Argument(
            help="Project name to inspect (omit to list all projects).",
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
    """Inspect project state and recent runs."""
    if lang_flag is not None:
        set_current_lang(lang_flag)
    lang = current_lang()

    home = home_override or DEFAULT_HOME
    projects_root = home / "projects"
    if not projects_root.is_dir():
        err_console.print(
            f"\n[yellow]{t('status.no_projects', lang=lang)}[/yellow]\n"
        )
        sys.exit(0)

    if project is None:
        # List all projects in a table
        table = _render_project_list(projects_root, lang)
        console.print()
        console.print(table)
        # Empty-state hint
        if projects_root.exists() and not any(projects_root.iterdir()):
            console.print(
                f"\n[dim]{t('status.no_projects_hint', lang=lang)}[/dim]\n"
            )
        else:
            console.print()
        return

    proj_dir = projects_root / project
    if not proj_dir.is_dir():
        err_console.print(
            f"\n[red]✗ {t('status.project_not_found', lang=lang, name=project)}[/red]\n"
        )
        sys.exit(2)
    _render_project_detail(proj_dir, lang)
