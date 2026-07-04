"""`lovarch progetto` — composed, phased workflows that chain the agents.

    lovarch progetto interni "attico 90mq, stile caldo minimale, cliente ama il legno"
    lovarch progetto interni "..." --renders 2 --no-preventivo -o dossier.md

The interior workflow runs: interior-designer (concept) → optional render(s) →
optional preventivo → assembled mini-dossier. Text uses the platform models;
renders debit image credits. Everything after the concept is opt-in.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from lovarch_cli.upsell import insufficient_credits, not_authenticated

console = Console()
err_console = Console(stderr=True)

progetto_app = typer.Typer(
    help="Workflow composti (progetto interni: concept → render → preventivo → dossier).",
    no_args_is_help=True,
)


@progetto_app.command("interni")
def interni_command(
    brief: str = typer.Argument(..., help="Brief del progetto di interni."),
    renders: int = typer.Option(0, "--renders", help="Numero di render da generare (crediti)."),
    preventivo: bool = typer.Option(True, "--preventivo/--no-preventivo", help="Includere il preventivo."),
    lead: str = typer.Option(None, "--lead", help="ID cliente CRM da usare come contesto."),
    language: str = typer.Option(None, "--language", help="Lingua dell'output."),
    output: Path = typer.Option(None, "--output", "-o", help="Salva il dossier markdown su file."),
) -> None:
    """Progetto di interni composto: concept → render → preventivo → mini-dossier."""
    from lovarch_cli.ai import AiGatewayError, InsufficientCreditsError, LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession
    from lovarch_cli.i18n import current_lang
    from lovarch_cli.workflows.progetto import progetto_interni

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)

    def _on_phase(name: str) -> None:
        console.print(f"[dim]→ {name}…[/dim]")

    try:
        result = asyncio.run(progetto_interni(
            LovarchAiGateway(session), brief,
            language=language or current_lang(),
            want_render=renders > 0,
            want_preventivo=preventivo,
            lead_id=lead,
            render_count=max(renders, 1),
            on_phase=_on_phase,
        ))
    except InsufficientCreditsError as exc:
        insufficient_credits(exc.available, exc.needed)
        raise typer.Exit(1)
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)

    console.print(Markdown(result.dossier_md))
    for w in result.warnings:
        console.print(f"  [yellow]· {w}[/yellow]")
    console.print(f"\n[dim]Crediti addebitati: {result.credits_charged}[/dim]")
    if output:
        out = Path(output).expanduser()
        out.write_text(result.dossier_md, encoding="utf-8")
        # Save renders next to the dossier as render-1.png, … (referenced in the md).
        for i, img in enumerate(result.renders, 1):
            (out.parent / f"render-{i}.png").write_bytes(img)
        console.print(f"[green]✓[/green] dossier salvato: {output}"
                      + (f" (+{len(result.renders)} render)" if result.renders else ""))


@progetto_app.command("cantiere")
def cantiere_command(
    brief: str = typer.Argument(..., help="Brief del cantiere (opere, tempi, vincoli)."),
    sicurezza: bool = typer.Option(True, "--sicurezza/--no-sicurezza", help="Includere il pre-check sicurezza."),
    lead: str = typer.Option(None, "--lead", help="ID cliente CRM come contesto."),
    language: str = typer.Option(None, "--language", help="Lingua dell'output."),
    output: Path = typer.Option(None, "--output", "-o", help="Salva il dossier markdown."),
) -> None:
    """Check cantiere composto: cronoprogramma (direzione lavori) → pre-check sicurezza."""
    from lovarch_cli.ai import AiGatewayError, InsufficientCreditsError, LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession
    from lovarch_cli.i18n import current_lang
    from lovarch_cli.workflows.progetto import cantiere_check

    session = LovarchSession.load()
    if session is None:
        not_authenticated("Il check cantiere")
        raise typer.Exit(1)

    try:
        result = asyncio.run(cantiere_check(
            LovarchAiGateway(session), brief,
            language=language or current_lang(), want_sicurezza=sicurezza,
            lead_id=lead, on_phase=lambda n: console.print(f"[dim]→ {n}…[/dim]"),
        ))
    except InsufficientCreditsError as exc:
        insufficient_credits(exc.available, exc.needed); raise typer.Exit(1)
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]"); raise typer.Exit(1)

    console.print(Markdown(result.dossier_md))
    for w in result.warnings:
        console.print(f"  [yellow]· {w}[/yellow]")
    console.print(f"\n[dim]Crediti addebitati: {result.credits_charged}[/dim]")
    if output:
        Path(output).expanduser().write_text(result.dossier_md, encoding="utf-8")
        console.print(f"[green]✓[/green] dossier salvato: {output}")


@progetto_app.command("completo")
def completo_command(
    brief: str = typer.Argument(..., help="Brief del progetto."),
    esegui: int = typer.Option(0, "--esegui", help="Esegui fino a N specialisti raccomandati (0 = solo piano)."),
    lead: str = typer.Option(None, "--lead", help="ID cliente CRM come contesto."),
    language: str = typer.Option(None, "--language", help="Lingua dell'output."),
    output: Path = typer.Option(None, "--output", "-o", help="Salva il dossier markdown."),
) -> None:
    """Orchestratore: @progetto-chief pianifica gli specialisti e (--esegui) li lancia."""
    from lovarch_cli.ai import AiGatewayError, InsufficientCreditsError, LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession
    from lovarch_cli.i18n import current_lang
    from lovarch_cli.workflows.progetto import progetto_completo

    session = LovarchSession.load()
    if session is None:
        not_authenticated("L'orchestratore di progetto")
        raise typer.Exit(1)

    try:
        result = asyncio.run(progetto_completo(
            LovarchAiGateway(session), brief,
            language=language or current_lang(), esegui=esegui, lead_id=lead,
            on_phase=lambda n: console.print(f"[dim]→ {n}…[/dim]"),
        ))
    except InsufficientCreditsError as exc:
        insufficient_credits(exc.available, exc.needed); raise typer.Exit(1)
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]"); raise typer.Exit(1)

    console.print(Markdown(result.dossier_md))
    agenti = result.plan.get("agenti") or []
    if agenti and esegui == 0:
        console.print("\n[dim]Per eseguire gli specialisti: aggiungi [bold]--esegui N[/bold].[/dim]")
    for w in result.warnings:
        console.print(f"  [yellow]· {w}[/yellow]")
    console.print(f"\n[dim]Crediti addebitati: {result.credits_charged}[/dim]")
    if output:
        Path(output).expanduser().write_text(result.dossier_md, encoding="utf-8")
        console.print(f"[green]✓[/green] dossier salvato: {output}")
