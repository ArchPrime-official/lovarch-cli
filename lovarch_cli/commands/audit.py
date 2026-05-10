"""lovarch audit — 18-point input validation checklist.

Inspects ~/.lovarch/projects/<name>/input/ and runs an 18-check audit that
mirrors the @auditor-input Tier-0 gate inside the squad pipeline. Output:

  - Rich table with one row per check (#, name, status, detail)
  - Summary verdict (PASS / CONCERNS / FAIL)
  - Exit code 0 for PASS/CONCERNS, 1 for FAIL
  - --json flag for machine-readable output (CI pipelines)

The checklist is divided into three tiers:
  REQUIRED (10): missing → FAIL the whole audit
  RECOMMENDED (4): missing → CONCERNS verdict, not blocking
  BRIEFING (4): keyword checks inside briefing-cliente.md

This is intentionally permissive on RECOMMENDED so a user can still drive a
run with a partial input set (e.g. only 4 photos instead of 6), but the
required core (briefing, DXF, photos≥4, pinterest≥4, visura, architetto JSON)
is hard-gated.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from enum import Enum
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

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".webp"}


class CheckStatus(str, Enum):
    PASS = "PASS"
    CONCERNS = "CONCERNS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class CheckResult:
    """One row in the audit table."""

    index: int
    key: str  # i18n key suffix (e.g. "briefing_present")
    status: CheckStatus
    detail: str  # short human-readable explanation
    required: bool  # True = FAIL blocks audit; False = downgrades to CONCERNS


# ──────────────────────────────────────────────────────────────────────────
# Individual checkers
# ──────────────────────────────────────────────────────────────────────────


def _check_file(
    input_dir: Path,
    filename: str,
    min_size_bytes: int = 0,
    required: bool = True,
) -> tuple[CheckStatus, str]:
    path = input_dir / filename
    if not path.exists():
        return (CheckStatus.FAIL if required else CheckStatus.CONCERNS,
                f"missing: {filename}")
    size = path.stat().st_size
    if size < min_size_bytes:
        return (CheckStatus.FAIL if required else CheckStatus.CONCERNS,
                f"{size}B < {min_size_bytes}B min")
    return CheckStatus.PASS, f"{size:,}B"


def _check_image_dir(
    input_dir: Path,
    dirname: str,
    min_count: int,
    recommended_count: int,
) -> tuple[CheckStatus, str]:
    path = input_dir / dirname
    if not path.is_dir():
        return CheckStatus.FAIL, f"missing dir: {dirname}/"
    images = [
        p for p in path.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ]
    n = len(images)
    if n < min_count:
        return CheckStatus.FAIL, f"{n} images, need ≥{min_count}"
    if n < recommended_count:
        return CheckStatus.CONCERNS, f"{n} images (recommended ≥{recommended_count})"
    return CheckStatus.PASS, f"{n} images"


def _check_json_keys(
    input_dir: Path, filename: str, required_keys: list[str]
) -> tuple[CheckStatus, str]:
    path = input_dir / filename
    if not path.exists():
        return CheckStatus.FAIL, f"missing: {filename}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return CheckStatus.FAIL, f"invalid JSON: {exc}"
    missing = [k for k in required_keys if k not in data]
    if missing:
        return CheckStatus.FAIL, f"missing keys: {', '.join(missing)}"
    return CheckStatus.PASS, f"{len(required_keys)} required keys present"


def _check_briefing_keyword(
    input_dir: Path, keyword: str, min_occurrences: int = 1
) -> tuple[CheckStatus, str]:
    path = input_dir / "briefing-cliente.md"
    if not path.exists():
        return CheckStatus.FAIL, "briefing not found"
    text = path.read_text(encoding="utf-8").lower()
    n = text.count(keyword.lower())
    if n < min_occurrences:
        return CheckStatus.CONCERNS, f"'{keyword}' not mentioned"
    return CheckStatus.PASS, f"'{keyword}' x{n}"


def _check_briefing_size(input_dir: Path, min_lines: int = 50) -> tuple[CheckStatus, str]:
    path = input_dir / "briefing-cliente.md"
    if not path.exists():
        return CheckStatus.FAIL, "missing: briefing-cliente.md"
    lines = path.read_text(encoding="utf-8").count("\n")
    if lines < min_lines:
        return CheckStatus.CONCERNS, f"{lines} lines < {min_lines} recommended"
    return CheckStatus.PASS, f"{lines} lines"


# ──────────────────────────────────────────────────────────────────────────
# Full 18-point checklist
# ──────────────────────────────────────────────────────────────────────────


def _run_checks(input_dir: Path) -> list[CheckResult]:
    """Execute all 18 checks and return ordered results."""
    results: list[CheckResult] = []

    # Required (10) — FAIL here breaks the audit
    s, d = _check_briefing_size(input_dir, min_lines=50)
    results.append(CheckResult(1, "briefing_present", s, d, required=True))

    s, d = _check_briefing_keyword(input_dir, "cliente")
    results.append(CheckResult(2, "briefing_cliente", s, d, required=True))

    s, d = _check_briefing_keyword(input_dir, "programma")
    results.append(CheckResult(3, "briefing_programma", s, d, required=True))

    s, d = _check_file(input_dir, "stato-attuale.dxf", min_size_bytes=5_000, required=True)
    results.append(CheckResult(4, "dxf_present", s, d, required=True))

    s, d = _check_file(input_dir, "stato-attuale.png", min_size_bytes=1_000, required=True)
    results.append(CheckResult(5, "preview_png", s, d, required=True))

    s, d = _check_file(input_dir, "visura-catastale.pdf", min_size_bytes=1_000, required=True)
    results.append(CheckResult(6, "visura_present", s, d, required=True))

    s, d = _check_json_keys(
        input_dir,
        "architetto-info.json",
        ["nome", "iscrizione_ordine", "codice_fiscale"],
    )
    results.append(CheckResult(7, "architetto_json", s, d, required=True))

    s, d = _check_image_dir(input_dir, "foto", min_count=4, recommended_count=6)
    results.append(CheckResult(8, "foto_dir", s, d, required=True))

    s, d = _check_image_dir(
        input_dir, "pinterest-references", min_count=4, recommended_count=6
    )
    results.append(CheckResult(9, "pinterest_dir", s, d, required=True))

    s, d = _check_briefing_keyword(input_dir, "budget")
    results.append(CheckResult(10, "briefing_budget", s, d, required=True))

    # Recommended (4) — CONCERNS only, not blocking
    s, d = _check_briefing_keyword(input_dir, "tempi")
    results.append(CheckResult(11, "briefing_tempi", s, d, required=False))

    s, d = _check_briefing_keyword(input_dir, "vincoli")
    results.append(CheckResult(12, "briefing_vincoli", s, d, required=False))

    s, d = _check_briefing_keyword(input_dir, "stile")
    results.append(CheckResult(13, "briefing_stile", s, d, required=False))

    s, d = _check_briefing_keyword(input_dir, "spazi")
    results.append(CheckResult(14, "briefing_spazi", s, d, required=False))

    # Briefing depth checks (4) — CONCERNS only
    s, d = _check_briefing_keyword(input_dir, "famiglia")
    results.append(CheckResult(15, "briefing_famiglia", s, d, required=False))

    s, d = _check_briefing_keyword(input_dir, "abitudini")
    results.append(CheckResult(16, "briefing_abitudini", s, d, required=False))

    s, d = _check_briefing_keyword(input_dir, "materiali")
    results.append(CheckResult(17, "briefing_materiali", s, d, required=False))

    s, d = _check_briefing_keyword(input_dir, "sostenibilità", min_occurrences=1)
    if s != CheckStatus.PASS:
        # fall back to plain ascii 'sostenibilita'
        s, d = _check_briefing_keyword(input_dir, "sostenibilita")
    results.append(CheckResult(18, "briefing_sostenibilita", s, d, required=False))

    return results


def _overall_verdict(results: list[CheckResult]) -> CheckStatus:
    """PASS only if everything green; FAIL if any required FAIL; else CONCERNS."""
    any_required_fail = any(
        r.required and r.status == CheckStatus.FAIL for r in results
    )
    if any_required_fail:
        return CheckStatus.FAIL
    any_concerns = any(r.status != CheckStatus.PASS for r in results)
    return CheckStatus.CONCERNS if any_concerns else CheckStatus.PASS


# ──────────────────────────────────────────────────────────────────────────
# Render helpers
# ──────────────────────────────────────────────────────────────────────────


_STATUS_STYLE = {
    CheckStatus.PASS: "[bold green]✓ PASS[/bold green]",
    CheckStatus.CONCERNS: "[bold yellow]⚠ CONCERNS[/bold yellow]",
    CheckStatus.FAIL: "[bold red]✗ FAIL[/bold red]",
}


def _render_table(results: list[CheckResult], lang: str) -> Table:
    table = Table(
        title=t("audit.checklist_title", lang=lang),
        show_lines=False,
        title_style="bold gold1",
        header_style="bold",
    )
    table.add_column("#", justify="right", style="dim", width=3)
    table.add_column(t("audit.col_check", lang=lang), no_wrap=True)
    table.add_column(t("audit.col_status", lang=lang), no_wrap=True)
    table.add_column(t("audit.col_detail", lang=lang), overflow="fold")

    for r in results:
        check_label = t(f"audit.checks.{r.key}", lang=lang)
        table.add_row(
            str(r.index),
            check_label,
            _STATUS_STYLE[r.status],
            r.detail,
        )
    return table


# ──────────────────────────────────────────────────────────────────────────
# Typer command
# ──────────────────────────────────────────────────────────────────────────


def audit_command(
    project: Annotated[
        str, typer.Argument(help="Project name to audit.")
    ],
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print machine-readable JSON instead of Rich table.",
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
    """Validate project input against the 18-point checklist."""
    if lang_flag is not None:
        set_current_lang(lang_flag)
    lang = current_lang()

    home = home_override or DEFAULT_HOME
    proj_dir = home / "projects" / project
    if not proj_dir.is_dir():
        err_console.print(
            f"\n[red]✗ {t('audit.no_project', lang=lang, name=project)}[/red]\n"
        )
        sys.exit(2)

    input_dir = proj_dir / "input"
    if not input_dir.is_dir():
        err_console.print(
            f"\n[red]✗ {t('audit.no_input', lang=lang, path=str(input_dir))}[/red]\n"
        )
        sys.exit(2)

    # ─── Run checks ──────────────────────────────────────────────────────
    results = _run_checks(input_dir)
    verdict = _overall_verdict(results)

    # ─── Persist verdict in project.yaml ────────────────────────────────
    yaml_path = proj_dir / "project.yaml"
    if yaml_path.exists():
        try:
            meta = yaml.safe_load(yaml_path.read_text()) or {}
        except yaml.YAMLError:
            meta = {}
        meta["last_audit"] = {
            "verdict": verdict.value,
            "pass_count": sum(1 for r in results if r.status == CheckStatus.PASS),
            "concerns_count": sum(
                1 for r in results if r.status == CheckStatus.CONCERNS
            ),
            "fail_count": sum(1 for r in results if r.status == CheckStatus.FAIL),
        }
        yaml_path.write_text(
            yaml.safe_dump(meta, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    # ─── JSON output (for CI) ─────────────────────────────────────────────
    if json_output:
        payload = {
            "project": project,
            "verdict": verdict.value,
            "checks": [
                {
                    "index": r.index,
                    "key": r.key,
                    "status": r.status.value,
                    "detail": r.detail,
                    "required": r.required,
                }
                for r in results
            ],
        }
        console.print(json.dumps(payload, indent=2, ensure_ascii=False))
        sys.exit(0 if verdict != CheckStatus.FAIL else 1)

    # ─── Rich output ─────────────────────────────────────────────────────
    console.print()
    console.print(_render_table(results, lang))

    summary_key = {
        CheckStatus.PASS: "audit.summary_pass",
        CheckStatus.CONCERNS: "audit.summary_concerns",
        CheckStatus.FAIL: "audit.summary_fail",
    }[verdict]
    next_key = (
        "audit.next_steps_fail" if verdict == CheckStatus.FAIL else "audit.next_steps_pass"
    )

    summary_text = Text.from_markup(
        f"{_STATUS_STYLE[verdict]} — "
        f"{t(summary_key, lang=lang, name=project)}\n\n"
        f"{t(next_key, lang=lang, name=project)}"
    )
    border = {
        CheckStatus.PASS: "green",
        CheckStatus.CONCERNS: "yellow",
        CheckStatus.FAIL: "red",
    }[verdict]
    console.print()
    console.print(
        Panel(
            summary_text,
            title=f"[bold {border}]{t('audit.summary_title', lang=lang)}[/bold {border}]",
            border_style=border,
            padding=(1, 2),
        )
    )
    console.print()

    sys.exit(0 if verdict != CheckStatus.FAIL else 1)
