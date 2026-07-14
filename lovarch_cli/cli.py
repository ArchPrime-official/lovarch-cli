"""lovarch-cli — Typer app entry point.

Subcommand structure:
    lovarch login      → Free or Premium authentication
    lovarch signup     → Free mode registration (name, email, phone)
    lovarch config     → API keys, language, storage path
    lovarch agent      → Real LLM agents (interior-designer, sicurezza-advisor…)
    lovarch progetto   → Composed workflows (interni, cantiere)
    lovarch do         → Render/logo/site/colors/copy/script (platform)
    lovarch verifica   → misure/computo/normativa/contratto/pratica/sicurezza/…
    lovarch cad        → Generate a real DXF floor plan
    lovarch archchat   → Read your studio's ArchChat conversations
    lovarch skills     → Install skills (text with YOUR model, zero credits)
    lovarch mcp        → Remote/local MCP connection
    lovarch status     → Inspect executions
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
        "Agenti LLM reali per architetti, interior designer, geometri e "
        "ingegneri: progetto, computo, capitolato, verifiche adversarial "
        "(NTC, antincendio, acustica, energetica, contratto CNAPPC), CAD 2D "
        "DXF, render e workflow orchestrati dal @progetto-chief."
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

    # Keep the Claude Code skills (/lovarch-*) in lockstep with the installed
    # CLI: install on first run, refresh on upgrade. Cheap + best-effort — see
    # ensure_skills_synced. Skipped for --version/--help (eager, exit before
    # this body runs). Opt out with LOVARCH_NO_SKILLS_SYNC=1.
    from lovarch_cli.commands.skills_cmd import ensure_skills_synced

    ensure_skills_synced()

    # Avviso di versione nuova (1×/24h, timeout 2s, silenzioso se fallisce).
    # Senza questo, chi installa una volta resta fermo per sempre.
    # Opt out: LOVARCH_NO_UPDATE_CHECK=1.
    try:
        from lovarch_cli.update_check import check_for_update

        msg = check_for_update()
        if msg:
            from rich.console import Console

            Console(stderr=True).print(f"[dim]↑ {msg}[/dim]")
    except Exception:
        pass


def _agents_count() -> int:
    from lovarch_cli.agents import AGENTS

    return len(AGENTS)


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
        ("Agenti:  ", "dim"),
        (f"{_agents_count()} agenti LLM + 12 verifiche (vedi `lovarch agent list`)\n", "bold"),
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

from lovarch_cli.commands.credits_cmd import credits_command  # noqa: E402

app.command(name="credits", help="Saldo crediti del tuo account Lovarch.")(
    credits_command
)

# The hard-coded squad demo pipeline (init/audit/run/consolidate/dev) was a test
# scaffold and has been removed. Real project work is done with the LLM agents and
# composed workflows — no hard-coded content:
#   lovarch agent <persona> · lovarch progetto interni|cantiere · lovarch do ...
#   lovarch verifica ... · lovarch cad genera · lovarch skills (col tuo modello).

# Inspect project state and recent CLI executions
from lovarch_cli.commands.status import status_command  # noqa: E402

app.command(name="status", help="Stato dei progetti e ultime esecuzioni.")(
    status_command
)

from lovarch_cli.commands.mcp_cmd import mcp_app  # noqa: E402

app.add_typer(
    mcp_app,
    name="mcp",
    help="Server MCP (Claude Code / IDE). Richiede l'extra [mcp].",
)

from lovarch_cli.commands.context_cmd import context_app  # noqa: E402

app.add_typer(
    context_app,
    name="context",
    help="Contesto di personalizzazione usato dagli agenti AI (premium).",
)

from lovarch_cli.commands.do_cmd import do_app  # noqa: E402

app.add_typer(
    do_app,
    name="do",
    help="Workflow della piattaforma: render, colors, copy (premium).",
)

from lovarch_cli.commands.verifica_cmd import verifica_app  # noqa: E402

app.add_typer(
    verifica_app,
    name="verifica",
    help="Verifica dati: misure DXF (gratis) · normativa adversarial (premium).",
)

from lovarch_cli.commands.jobs_cmd import jobs_app  # noqa: E402

app.add_typer(
    jobs_app,
    name="jobs",
    help="Job asincroni (video, export, upscale) — stato e output.",
)

from lovarch_cli.commands.agent_cmd import agent_app  # noqa: E402

app.add_typer(
    agent_app,
    name="agent",
    help="Agenti architetto/interior/cantiere (interior-designer, direzione-lavori...).",
)

from lovarch_cli.commands.progetto_cmd import progetto_app  # noqa: E402

app.add_typer(
    progetto_app,
    name="progetto",
    help="Workflow composti (progetto interni: concept → render → preventivo → dossier).",
)

from lovarch_cli.commands.archchat_cmd import archchat_app  # noqa: E402

app.add_typer(
    archchat_app,
    name="archchat",
    help="Leggi le tue conversazioni ArchChat dello studio (sola lettura, nessun credito).",
)

from lovarch_cli.commands.cad_cmd import cad_app  # noqa: E402

app.add_typer(
    cad_app,
    name="cad",
    help="CAD: genera DXF 2D (gratis) e viewer BIM Autodesk (`cad view`, premium).",
)

from lovarch_cli.commands.media_cmd import media_app  # noqa: E402

app.add_typer(
    media_app,
    name="media",
    help="La tua galleria Lovarch: immagini, video, mondi 3D, CAD — list e download.",
)

from lovarch_cli.commands.dati_cmd import dati_app  # noqa: E402

app.add_typer(
    dati_app,
    name="dati",
    help="I tuoi dati Lovarch: progetti, finanze, prezzari, CRM (sola lettura).",
)

from lovarch_cli.commands.skills_cmd import skills_app  # noqa: E402

app.add_typer(
    skills_app,
    name="skills",
    help="Skills per il tuo agente (Claude Code): testo col TUO modello, zero crediti.",
)

from lovarch_cli.commands.config_cmd import config_app  # noqa: E402

app.add_typer(
    config_app,
    name="config",
    help="Configurazione utente (lingua, storage, API keys Free mode).",
)


if __name__ == "__main__":
    app()
