"""`lovarch credits` — saldo crediti dell'account.

Mancava un modo di vedere il saldo dal terminale: l'unico segnale erano i 402
a operazione già fallita. La logica esisteva (LovarchCreditsClient →
cli-credits-check), mancava il comando.
"""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from lovarch_cli.upsell import insufficient_credits, not_authenticated

console = Console()
err_console = Console(stderr=True)


def credits_command(
    required: int = typer.Option(
        None,
        "--required",
        "-r",
        help="Verifica se il saldo copre N crediti (exit 1 se non basta).",
    ),
) -> None:
    """Mostra il saldo crediti del tuo account Lovarch."""
    from lovarch_cli.auth.session import LovarchSession
    from lovarch_cli.credits.lovarch import LovarchCreditsClient

    session = LovarchSession.load()
    if session is None:
        not_authenticated("Vedere il saldo crediti")
        raise typer.Exit(1)

    # LovarchSession non ha un close(): apre il client per request (come dati_cmd).
    try:
        balance = asyncio.run(LovarchCreditsClient(session).check(required))
    except Exception as exc:  # noqa: BLE001 — messaggio amichevole, non traceback
        err_console.print(f"[red]✗ Impossibile leggere il saldo:[/red] {exc}")
        raise typer.Exit(1) from exc

    if balance.is_admin:
        console.print(
            "[bold gold1]∞ Crediti illimitati[/bold gold1] [dim](account admin)[/dim]"
        )
        return

    table = Table(title="Crediti Lovarch", header_style="bold gold1", show_header=False)
    table.add_column("", style="dim")
    table.add_column("", justify="right")
    table.add_row("Saldo", f"[bold]{balance.balance:,}[/bold] crediti")
    table.add_row("Usati questo mese", f"{balance.monthly_used:,}")
    if required is not None:
        table.add_row(
            f"Copre {required:,} crediti?",
            "[green]sì[/green]" if balance.sufficient else "[red]no[/red]",
        )
    console.print(table)
    console.print(
        "[dim]I crediti coprono immagini, render, dati e verifiche di piattaforma. "
        "Il testo generato dal tuo modello (skill) è gratis.[/dim]\n"
        "[dim]Ricarica: [bold]lovarch upgrade[/bold][/dim]"
    )

    if required is not None and not balance.sufficient:
        insufficient_credits(balance.balance, required)
        raise typer.Exit(1)
