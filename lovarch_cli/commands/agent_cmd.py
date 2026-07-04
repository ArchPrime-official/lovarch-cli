"""`lovarch agent` — run architecture/interior/construction agents.

    lovarch agent list
    lovarch agent interior-designer "attico 90mq, stile caldo minimale, cliente ama il legno"
    lovarch agent direzione-lavori "ristrutturazione 120mq, consegna 90 giorni"

Each agent runs via the platform (debits credits), personalized with your brand
and language.
"""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.markdown import Markdown

from lovarch_cli.agents import AGENTS
from lovarch_cli.upsell import insufficient_credits, not_authenticated

console = Console()
err_console = Console(stderr=True)

agent_app = typer.Typer(
    help="Agenti per architetti, interior designer e cantiere (premium).",
    no_args_is_help=True,
)


@agent_app.command("list")
def list_command() -> None:
    """Elenca gli agenti disponibili."""
    for a in AGENTS.values():
        model = "Opus 4.8" if a.role in ("verifier", "chief") else "Sonnet 5"
        console.print(f"  [cyan]{a.id}[/cyan] — {a.label} [dim]({model})[/dim]")


@agent_app.command("run")
def run_command(
    agent_id: str = typer.Argument(..., help="ID agente (vedi `lovarch agent list`)."),
    brief: str = typer.Argument(..., help="Brief / richiesta per l'agente."),
    lead: str = typer.Option(None, "--lead", help="ID di un cliente CRM da usare come contesto."),
    language: str = typer.Option(None, "--language", help="Lingua dell'output."),
    output: str = typer.Option(None, "--output", "-o", help="Salva il markdown su file."),
) -> None:
    """Esegui un agente su un brief (personalizzato + addebita crediti)."""
    from lovarch_cli.agents import run_agent
    from lovarch_cli.ai import AiGatewayError, InsufficientCreditsError, LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession
    from lovarch_cli.i18n import current_lang

    if agent_id not in AGENTS:
        err_console.print(
            f"[red]✗ Agente sconosciuto: {agent_id}. Disponibili: {', '.join(AGENTS)}[/red]"
        )
        raise typer.Exit(2)

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)

    try:
        result = asyncio.run(run_agent(
            LovarchAiGateway(session), agent_id, brief,
            language=language or current_lang(), lead_id=lead,
        ))
    except InsufficientCreditsError as exc:
        insufficient_credits(exc.available, exc.needed)
        raise typer.Exit(1)
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)

    # BOZZA banner is printed deterministically (not left to the model).
    banner = ("**BOZZA** — elaborato generato con IA. Firma e responsabilità "
              "restano del professionista abilitato.")
    console.print(Markdown(f"> {banner}"))
    console.print(Markdown(result.text))
    console.print(f"\n[dim]— @{result.agent_id} · crediti addebitati: {result.credits_charged}[/dim]")
    if output:
        from pathlib import Path

        text = result.text
        if "BOZZA" not in text[:400]:
            text = f"> {banner}\n\n{text}"
        Path(output).expanduser().write_text(text, encoding="utf-8")
        console.print(f"[green]✓[/green] salvato: {output}")
