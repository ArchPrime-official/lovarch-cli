"""`lovarch archchat` — read your ArchChat (office) conversations from the terminal.

    lovarch archchat list
    lovarch archchat read <conversation_id>

READ-ONLY. This does NOT run the ArchChat AI and costs NO credits — since you're
already working in your own agent (Claude Code), the point is to pull information
that already exists in your ArchChat history, not to spend credits per message.
Reads go through your session with RLS (you only see your own conversations).
"""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table
from lovarch_cli.upsell import not_authenticated

console = Console()
err_console = Console(stderr=True)

archchat_app = typer.Typer(
    help="Leggi le tue conversazioni ArchChat (sola lettura, nessun credito).",
    no_args_is_help=True,
)


async def _get(session, path: str, params: dict) -> list:
    resp = await session.request("GET", path, params=params)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}")
    data = resp.json()
    return data if isinstance(data, list) else []


@archchat_app.command("list")
def list_command(
    limit: int = typer.Option(20, "--limit", help="Numero di conversazioni."),
) -> None:
    """Elenca le tue conversazioni ArchChat (titolo, agente, messaggi, data)."""
    from lovarch_cli.auth.session import LovarchSession

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)

    try:
        convs = asyncio.run(_get(session, "/rest/v1/archchat_conversations", {
            "select": "id,title,current_agent,message_count,last_message_at",
            "order": "last_message_at.desc",
            "limit": str(max(1, min(limit, 100))),
        }))
    except RuntimeError as exc:
        err_console.print(f"[red]✗ {exc}[/red]"); raise typer.Exit(1)

    if not convs:
        console.print("[dim]Nessuna conversazione ArchChat.[/dim]")
        return
    table = Table(title="ArchChat — conversazioni", header_style="bold gold1")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Titolo")
    table.add_column("Agente")
    table.add_column("Msg", justify="right")
    table.add_column("Ultimo")
    for c in convs:
        last = str(c.get("last_message_at") or "")[:10]
        table.add_row(str(c.get("id", ""))[:8], str(c.get("title") or "—")[:44],
                      str(c.get("current_agent") or "—"), str(c.get("message_count") or 0), last)
    console.print(table)
    console.print("[dim]Leggi una conversazione: lovarch archchat read <id>[/dim]")


@archchat_app.command("read")
def read_command(
    conversation_id: str = typer.Argument(..., help="ID della conversazione (vedi `archchat list`)."),
    limit: int = typer.Option(200, "--limit", help="Numero massimo di messaggi."),
) -> None:
    """Leggi i messaggi di una conversazione ArchChat."""
    from lovarch_cli.auth.session import LovarchSession
    from rich.markdown import Markdown

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)

    async def _run():
        convs = await _get(session, "/rest/v1/archchat_conversations", {
            "select": "id,title", "id": f"eq.{conversation_id}", "limit": "1",
        })
        if not convs:
            raise RuntimeError("conversazione non trovata (o non tua).")
        msgs = await _get(session, "/rest/v1/archchat_messages", {
            "select": "role,content,agent_type,created_at",
            "conversation_id": f"eq.{conversation_id}",
            "order": "created_at.asc",
            "limit": str(max(1, min(limit, 500))),
        })
        return convs[0], msgs

    try:
        conv, msgs = asyncio.run(_run())
    except RuntimeError as exc:
        err_console.print(f"[red]✗ {exc}[/red]"); raise typer.Exit(1)

    console.print(f"\n[bold gold1]{conv.get('title') or 'ArchChat'}[/bold gold1]\n")
    role_style = {"user": "cyan", "assistant": "green", "system": "dim"}
    for m in msgs:
        role = str(m.get("role") or "?")
        who = m.get("agent_type") or role
        console.print(f"[{role_style.get(role, 'white')}]● {who}[/]")
        console.print(Markdown(str(m.get("content") or "")))
        console.print("")
    console.print(f"[dim]{len(msgs)} messaggi · sola lettura, nessun credito.[/dim]")
