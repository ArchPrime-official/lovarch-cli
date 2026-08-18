"""`lovarch workspace` — scegli in quale studio stai lavorando.

Chi collabora con più studi ha più workspace: il proprio, e quello di ognuno che
lo ha invitato. Il workspace attivo decide **di chi sono i dati** che leggi e
scrivi e **da chi escono i crediti** — quindi sapere dove sei non è un dettaglio.

Fino al 18/08/2026 il terminale ereditava in silenzio il contesto scelto
nell'app: cambiarlo lì cambiava quello che il CLI faceva alla chiamata dopo, e
non c'era modo di vederlo né di sceglierlo da qui.
"""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from lovarch_cli.upsell import not_authenticated

console = Console()
err_console = Console(stderr=True)

workspace_app = typer.Typer(
    help="Workspace attivo: il tuo studio o quelli che ti hanno invitato.",
    no_args_is_help=False,
    invoke_without_command=True,
)


def _gateway():
    """Sessione premium + gateway, o esce con il messaggio di login."""
    from lovarch_cli.ai import LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)
    return LovarchAiGateway(session)


def _print_current(payload: dict) -> None:
    cur = payload.get("current") or {}
    name = "Personale" if cur.get("is_personal") else (cur.get("owner_name") or "—")
    console.print(f"[bold gold1]Workspace attivo:[/bold gold1] {name}")


@workspace_app.callback()
def _default(ctx: typer.Context) -> None:
    """Senza sottocomando mostra la lista (il caso d'uso più frequente)."""
    if ctx.invoked_subcommand is None:
        list_command()


@workspace_app.command("list")
def list_command() -> None:
    """Elenca i workspace disponibili e segna quello attivo."""
    from lovarch_cli.ai import AiGatewayError

    gw = _gateway()
    try:
        payload = asyncio.run(gw.workspace("list"))
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)

    table = Table(show_header=True, header_style="bold gold1")
    table.add_column("", width=2)
    table.add_column("Workspace", style="cyan")
    table.add_column("Piano")
    table.add_column("Ruolo")
    for w in payload.get("workspaces", []):
        table.add_row(
            "●" if w.get("is_current") else "",
            w.get("name") or "—",
            (w.get("plan") or "—"),
            (w.get("role") or "—"),
        )
    console.print(table)

    pending = payload.get("pending_invites") or []
    if pending:
        names = ", ".join(p.get("name") or "—" for p in pending)
        console.print(f"[yellow]Inviti da accettare:[/yellow] {names} [dim](accettali nell'app)[/dim]")

    console.print("[dim]lovarch workspace use \"<nome>\" per cambiare · 'personal' per il tuo.[/dim]")


@workspace_app.command("use")
def use_command(
    owner: str = typer.Argument(..., help="Nome, email o uuid dello studio — oppure 'personal'."),
) -> None:
    """Passa a un altro workspace."""
    from lovarch_cli.ai import AiGatewayError

    gw = _gateway()
    try:
        payload = asyncio.run(gw.workspace("use", owner=owner))
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)

    dest = payload.get("switched_to") or {}
    console.print(f"[green]✓[/green] Ora stai lavorando in [bold]{dest.get('name')}[/bold]")
    if payload.get("note"):
        console.print(f"[dim]{payload['note']}[/dim]")


@workspace_app.command("status")
def status_command() -> None:
    """Mostra solo il workspace attivo (utile negli script)."""
    from lovarch_cli.ai import AiGatewayError

    gw = _gateway()
    try:
        payload = asyncio.run(gw.workspace("status"))
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)
    _print_current(payload)
