"""lovarch-cli — Typer app entry point.

Subcommand structure (loaded lazily as commands are implemented):
    lovarch login      → Free or Premium authentication
    lovarch signup     → Free mode registration (name, email, phone)
    lovarch config     → API keys, language, storage path
    lovarch init       → Create new project with sample-input
    lovarch audit      → Run input audit (18-point checklist)
    lovarch run        → Execute full workflow
    lovarch consolidate → Generate DOSSIER.zip
    lovarch status     → Inspect execution
    lovarch upgrade    → CTA from Free to Premium
    lovarch account    → GDPR right-to-erasure

Global flags:
    --lang {it,pt,en,es}  → override detected language
    --version             → print version and exit
    --verbose             → verbose logging
"""
from __future__ import annotations

import sys
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from lovarch_cli.i18n import current_lang, set_current_lang, t
from lovarch_cli.version import __version__

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    name="lovarch",
    help=(
        "lovarch-cli — AI-powered architectural project execution.\n\n"
        "Squad di 17 agenti specializzati che genera audit, CAD, BIM/IFC, "
        "computo, capitolato, pratiche IT, contratto CNAPPC, energy/LCA "
        "in 14 minuti vs 3 settimane di lavoro tradizionale."
    ),
    no_args_is_help=True,
    add_completion=True,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _version_callback(value: bool) -> None:
    """Print version and exit (used by --version global flag)."""
    if value:
        console.print(f"lovarch-cli [bold]{__version__}[/bold]")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Mostra la versione e esce.",
        ),
    ] = None,
    lang: Annotated[
        Optional[str],
        typer.Option(
            "--lang",
            "-l",
            help="Lingua: it, pt, en, es (default: rilevata automaticamente).",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Output dettagliato per debug.",
        ),
    ] = False,
) -> None:
    """lovarch-cli — global flags handler."""
    # Resolve --lang precedence: explicit flag > $LOVARCH_LANG > $LANG > 'it'.
    # set_current_lang() validates against VALID_LANGUAGES and falls back to
    # env detection if the override is invalid.
    if lang is not None:
        set_current_lang(lang)
    ctx.ensure_object(dict)
    ctx.obj["lang"] = lang
    ctx.obj["verbose"] = verbose


@app.command(name="info")
def info_cmd() -> None:
    """Mostra informazioni sulla installazione corrente."""
    lang = current_lang()
    title = Text("lovarch-cli", style="bold gold1")
    body = Text.assemble(
        ("Version: ", "dim"),
        (f"{__version__}\n", "bold"),
        ("Python:  ", "dim"),
        (f"{sys.version.split()[0]}\n", "bold"),
        ("Platform:", "dim"),
        (f" {sys.platform}\n", "bold"),
        ("Squad:   ", "dim"),
        ("architettura-progetto (17 agents, 6 tasks, 1 workflow)\n", "bold"),
        ("Mode:    ", "dim"),
        (t("info.mode_not_configured", lang=lang), "italic yellow"),
    )
    console.print(
        Panel(
            Text.assemble(title, "\n\n", body),
            title=f"[bold]{t('info.title', lang=lang)}[/bold]",
            border_style="gold1",
            padding=(1, 2),
        )
    )
    console.print(
        f"\n[dim]{t('info.powered_by', lang=lang)}[/dim]\n"
        f"[dim]{t('info.course_promo', lang=lang)}[/dim]\n"
    )


# ════════════════════════════════════════════════════════════════════════════
# Subcommands registration
#
# Each subcommand is either:
# - a single-action command via app.command()(fn)
# - a multi-subcommand group via app.add_typer(sub.app, name=...)
# ════════════════════════════════════════════════════════════════════════════

# Story 2.2 — Free mode signup with lead capture
from lovarch_cli.commands.signup import signup_command  # noqa: E402

app.command(name="signup", help="Cadastro Free interattivo (lead capture).")(
    signup_command
)

# Story 2.3 — GDPR right-to-erasure + account info
from lovarch_cli.commands import account as account_cmd  # noqa: E402

app.add_typer(
    account_cmd.app,
    name="account",
    help="Gestione account (info, delete GDPR).",
)

# Story 3.3 — premium PKCE login + free redirect
from lovarch_cli.commands.login import login_command  # noqa: E402

app.command(name="login", help="Login al CLI (--free o --premium).")(
    login_command
)

# Story 3.4 — CTA Free → Premium upgrade flow (opens browser)
from lovarch_cli.commands.upgrade import upgrade_command  # noqa: E402

app.command(name="upgrade", help="Passa da Free a Premium (apre il browser).")(
    upgrade_command
)

# Fase A.1 — Create a new project directory (+ optional sample-input)
from lovarch_cli.commands.init import init_command  # noqa: E402

app.command(name="init", help="Inizializza un nuovo progetto (con --sample copia villa-chianti).")(
    init_command
)

# Fase A.2 — 18-point input validation checklist
from lovarch_cli.commands.audit import audit_command  # noqa: E402

app.command(name="audit", help="Audit dei 18 input prima del run (verdict PASS/CONCERNS/FAIL).")(
    audit_command
)

# Fase A.3 — Execute the squad pipeline (subprocess wrapper, premium = real)
from lovarch_cli.commands.run import run_command  # noqa: E402

app.command(name="run", help="Esegui il pipeline (Free=dry-run, Premium=reale).")(
    run_command
)

# Fase A.4 — Bundle run output into DOSSIER.zip
from lovarch_cli.commands.consolidate import consolidate_command  # noqa: E402

app.command(name="consolidate", help="Genera DOSSIER.zip dall'output di un run.")(
    consolidate_command
)

# Fase A.5 — Inspect project state and recent runs
from lovarch_cli.commands.status import status_command  # noqa: E402

app.command(name="status", help="Stato dei progetti e ultime esecuzioni.")(
    status_command
)

# Squad-dev-loop — developer tooling (squad path resolution, vendor refresh)
from lovarch_cli.commands.dev import dev_app  # noqa: E402

app.add_typer(
    dev_app,
    name="dev",
    help="Developer tooling for the squad payload (contributors only).",
)

from lovarch_cli.commands.config_cmd import config_app  # noqa: E402

app.add_typer(
    config_app,
    name="config",
    help="Configurazione utente (lingua, storage, API keys Free mode).",
)


if __name__ == "__main__":
    app()
