"""`lovarch context` — show the personalization bundle the AI agents use.

Displays which profile pieces the platform will inject into every generation
(brand, style, DISC, fiscal, professional signature, language) — the CLI
equivalent of the web app's "IA usa il tuo: …" chips.
"""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

console = Console()
err_console = Console(stderr=True)

context_app = typer.Typer(
    help="Contesto di personalizzazione usato dagli agenti AI.",
    no_args_is_help=True,
)

_CHIP_LABELS = {
    "hasBrand": "Brand",
    "hasStyle": "Stile visivo",
    "hasDisc": "DISC",
    "hasSwot": "SWOT",
    "hasAvatar": "Avatar cliente",
    "hasFiscal": "Dati fiscali",
    "hasCredentials": "Credenziali professionali",
    "hasClient": "Cliente CRM",
}


@context_app.command("show")
def show_command(
    lead_id: str = typer.Option(None, "--lead", help="ID di un lead CRM da includere."),
) -> None:
    """Mostra il bundle di personalizzazione (richiede login premium)."""
    from lovarch_cli.ai import AiGatewayError, LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession

    session = LovarchSession.load()
    if session is None:
        err_console.print("[red]✗ Non autenticato. Esegui `lovarch login --premium`.[/red]")
        raise typer.Exit(1)

    try:
        bundle = asyncio.run(LovarchAiGateway(session).get_user_context(lead_id=lead_id))
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)

    summary = bundle.get("context_summary", {})
    table = Table(title="Contesto AI — cosa viene usato per personalizzare",
                  show_header=True, header_style="bold gold1")
    table.add_column("Elemento", style="cyan")
    table.add_column("Attivo", justify="center")
    for key, label in _CHIP_LABELS.items():
        table.add_row(label, "✅" if summary.get(key) else "—")
    console.print(table)

    if bundle.get("signature_line"):
        console.print(f"\n[bold]Firma documenti:[/bold] {bundle['signature_line']}")
    prefs = bundle.get("preferences", {})
    console.print(
        f"[dim]Lingua output: {prefs.get('preferred_language', 'it')} · "
        f"Valuta: {prefs.get('currency', 'EUR')} · "
        f"Unità: {prefs.get('measurement_unit', 'metric')}[/dim]"
    )
    client = bundle.get("client")
    if client and client.get("lead"):
        console.print(f"[bold]Cliente CRM:[/bold] {client['lead'].get('name')}")
