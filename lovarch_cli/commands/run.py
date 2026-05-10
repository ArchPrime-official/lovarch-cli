"""lovarch run — Execute the squad pipeline against a project.

Pragmatic shell-out: invokes the existing `pipeline_runner.py` (1821 lines,
proven in production) as a subprocess instead of pulling its logic into the
CLI's modular phases architecture (that's Story 1.3 — deferred to Q3 2026).

Flow:
    1. Resolve project dir (~/.lovarch/projects/<name>/)
    2. Verify audit was run and passed (last_audit.verdict in project.yaml)
    3. Load credentials → detect mode (free/premium)
    4. Premium: pre-flight credits.check_or_raise(required=3500)
       Free:    skip credits gate
    5. Persistence: create_execution() → exec_id
    6. Locate bundled pipeline_runner.py inside lovarch_cli/squad/
    7. subprocess.Popen with --input-dir <project_input> + mode flag
       Free → --dry-run (simulation, no API calls)
       Premium → --real (production, hits Lovarch Supabase + AI providers)
    8. Stream stdout/stderr to user in real time (preserve ANSI colors)
    9. Wait for exit code → persistence.update_execution(status)
   10. Show summary panel with `lovarch status` hint

Free mode dry-run is intentionally limited: the existing pipeline_runner
hardcodes LovarchClient() which connects to Supabase. A "true" Free run
that uses LocalSqliteClient + LocalFilesystemStorage requires the Story 1.3
refactor (replace LovarchClient calls with persistence ABC). For the curso
delivery, Free → dry-run is sufficient (shows the orchestration flow,
useful for teaching), Premium → real run delivers actual artifacts.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from lovarch_cli.clients.persistence import ExecutionMode
from lovarch_cli.config import DEFAULT_HOME, load_credentials
from lovarch_cli.credits import (
    InsufficientCreditsError,
    get_credits_client,
)
from lovarch_cli.i18n import current_lang, set_current_lang, t

console = Console()
err_console = Console(stderr=True)

# Typical workflow cost (mirrors what the squad bills for a full run).
# This is the threshold that gates premium runs at pre-flight.
DEFAULT_REQUIRED_CREDITS = 3_500

# Default workflow until we expose more squads via `lovarch run --workflow X`.
DEFAULT_WORKFLOW = "dal-brief-al-cantiere"


def _pipeline_runner_path() -> Path:
    """Locate the bundled pipeline_runner.py inside the synced squad payload."""
    pkg_root = Path(__file__).resolve().parent.parent
    return pkg_root / "squad" / "scripts" / "pipeline_runner.py"


def _resolve_mode_from_creds() -> ExecutionMode:
    """Map persisted credentials.mode → ExecutionMode enum."""
    creds = load_credentials()
    if creds.mode == "premium":
        return ExecutionMode.PREMIUM
    # 'free' or 'none' → Free mode dry-run (no real calls)
    return ExecutionMode.FREE


def _read_audit_verdict(project_dir: Path) -> str | None:
    """Return the last_audit.verdict from project.yaml, or None if absent."""
    yaml_path = project_dir / "project.yaml"
    if not yaml_path.exists():
        return None
    try:
        meta = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return None
    last = meta.get("last_audit") or {}
    return last.get("verdict")


def run_command(
    project: Annotated[
        str,
        typer.Argument(help="Project name (created via `lovarch init`)."),
    ],
    workflow: Annotated[
        str,
        typer.Option(
            "--workflow",
            "-w",
            help="Workflow to execute.",
        ),
    ] = DEFAULT_WORKFLOW,
    skip_audit: Annotated[
        bool,
        typer.Option(
            "--skip-audit",
            help="Skip the audit-verdict check (dangerous).",
        ),
    ] = False,
    skip_credits: Annotated[
        bool,
        typer.Option(
            "--skip-credits",
            help="Skip the credits pre-flight (Premium only — for testing).",
        ),
    ] = False,
    force_dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Force dry-run mode regardless of free/premium auth.",
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
) -> None:
    """Run the squad pipeline against a project."""
    if lang_flag is not None:
        set_current_lang(lang_flag)
    lang = current_lang()

    home = home_override or DEFAULT_HOME
    proj_dir = home / "projects" / project
    if not proj_dir.is_dir():
        err_console.print(
            f"\n[red]✗ {t('run.no_project', lang=lang, name=project)}[/red]\n"
        )
        sys.exit(2)

    input_dir = proj_dir / "input"
    if not input_dir.is_dir():
        err_console.print(
            f"\n[red]✗ {t('run.no_input', lang=lang, path=str(input_dir))}[/red]\n"
        )
        sys.exit(2)

    # ─── Pre-flight: audit verdict gate ──────────────────────────────────
    if not skip_audit:
        verdict = _read_audit_verdict(proj_dir)
        if verdict is None:
            err_console.print(
                f"\n[yellow]{t('run.no_audit', lang=lang, name=project)}[/yellow]\n"
            )
            sys.exit(1)
        if verdict == "FAIL":
            err_console.print(
                f"\n[red]{t('run.audit_failed', lang=lang, name=project)}[/red]\n"
            )
            sys.exit(1)

    # ─── Mode resolution ─────────────────────────────────────────────────
    mode = ExecutionMode.FREE if force_dry_run else _resolve_mode_from_creds()
    is_dry_run = (mode == ExecutionMode.FREE) or force_dry_run

    # ─── Pre-flight: credits check (Premium only) ────────────────────────
    if mode == ExecutionMode.PREMIUM and not skip_credits:
        try:
            credits_client = get_credits_client(mode)
            asyncio.run(
                credits_client.check_or_raise(required=DEFAULT_REQUIRED_CREDITS)
            )
        except InsufficientCreditsError as exc:
            bal = exc.balance
            err_console.print(
                "\n[red]"
                + t(
                    "errors.credits_insufficient",
                    lang=lang,
                    remaining=bal.credits_remaining,
                    required=bal.required,
                    deficit=bal.deficit,
                )
                + "[/red]\n"
            )
            sys.exit(1)
        except RuntimeError as exc:
            # Premium client unavailable (no keyring session). Programmer-facing.
            err_console.print(
                f"\n[red]{t('errors.credits_check_failed', lang=lang, message=str(exc))}[/red]\n"
            )
            sys.exit(1)

    # ─── Locate pipeline_runner.py ───────────────────────────────────────
    runner = _pipeline_runner_path()
    if not runner.exists():
        err_console.print(
            f"\n[red]✗ {t('run.no_runner', lang=lang, path=str(runner))}[/red]\n"
        )
        sys.exit(2)

    # ─── Header panel ────────────────────────────────────────────────────
    mode_label = t(
        "run.mode_free" if is_dry_run else "run.mode_premium",
        lang=lang,
    )
    body_lines = [
        t("run.starting", lang=lang, project=project, workflow=workflow),
        t("run.mode_label", lang=lang, mode=mode_label),
    ]
    if is_dry_run:
        body_lines.append(t("run.dry_run_note", lang=lang))
    console.print()
    console.print(
        Panel(
            Text.from_markup("\n".join(body_lines)),
            title=f"[bold gold1]🚀 {t('run.title', lang=lang)}[/bold gold1]",
            border_style="gold1",
            padding=(1, 2),
        )
    )
    console.print()

    # ─── Build subprocess command ────────────────────────────────────────
    cmd = [
        sys.executable,
        str(runner),
        "--input-dir",
        str(input_dir),
    ]
    cmd.append("--dry-run" if is_dry_run else "--real")

    # Env vars passed through. The pipeline_runner reads OPENAI_API_KEY,
    # MAPBOX_TOKEN, etc. directly from os.environ — so any keys the user
    # has exported in their shell are inherited.
    env = dict(os.environ)
    env.setdefault("LOVARCH_PROJECT_NAME", project)
    env.setdefault("LOVARCH_WORKFLOW", workflow)

    # ─── Run subprocess + stream output ──────────────────────────────────
    try:
        result = subprocess.run(cmd, env=env, check=False)
    except FileNotFoundError as exc:
        err_console.print(
            f"\n[red]✗ {t('run.subprocess_failed', lang=lang, message=str(exc))}[/red]\n"
        )
        sys.exit(2)
    except KeyboardInterrupt:
        err_console.print(
            f"\n[yellow]⚠ {t('run.interrupted', lang=lang)}[/yellow]\n"
        )
        sys.exit(130)

    # ─── Result panel ────────────────────────────────────────────────────
    success = result.returncode == 0
    summary_key = "run.completed" if success else "run.failed"
    border = "green" if success else "red"
    console.print()
    console.print(
        Panel(
            Text.from_markup(
                f"{t(summary_key, lang=lang, project=project)}\n\n"
                f"{t('run.next_steps', lang=lang, project=project)}"
            ),
            title=f"[bold {border}]{t('run.summary_title', lang=lang)}[/bold {border}]",
            border_style=border,
            padding=(1, 2),
        )
    )
    console.print()
    sys.exit(result.returncode)
