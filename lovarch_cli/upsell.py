"""Consistent free→premium upsell messages for 401 (not authenticated) and 402
(insufficient credits). Cost is never shown in dollars — only credits — and every
message routes the user to the same in-terminal upgrade funnel (`lovarch upgrade`).
"""
from __future__ import annotations

from rich.console import Console

_err = Console(stderr=True)


def not_authenticated(action: str = "questa operazione") -> None:
    """Print a 401 message with an upgrade/login CTA."""
    _err.print(
        f"[red]✗ Non autenticato.[/red] {action} richiede un account Lovarch.\n"
        "  → Accedi con [bold]lovarch login --premium[/bold] "
        "(o attiva un piano con [bold]lovarch upgrade[/bold]).\n"
        "  [dim]Senza account puoi comunque usare le skill (testo col tuo modello), "
        "`lovarch verifica misure` e `lovarch cad genera`.[/dim]"
    )


def insufficient_credits(available: int | None = None, needed: int | None = None) -> None:
    """Print a 402 message with a recharge CTA (credits only, never USD)."""
    detail = ""
    if available is not None and needed is not None:
        detail = f" Disponibili {available} crediti, richiesti {needed}."
    _err.print(
        f"[red]✗ Crediti insufficienti.[/red]{detail}\n"
        "  → Ricarica o attiva un piano con [bold]lovarch upgrade[/bold].\n"
        "  [dim]I crediti coprono immagini, render, dati e verifiche di piattaforma. "
        "Il testo col tuo modello (skill) resta gratis.[/dim]"
    )
