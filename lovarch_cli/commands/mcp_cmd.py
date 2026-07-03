"""`lovarch mcp` — run the Lovarch MCP server.

The heavy ``mcp`` SDK import is lazy (inside the command) so that
``lovarch --help`` and every other command keep working even when the optional
``[mcp]`` extra is not installed.
"""
from __future__ import annotations

import typer

mcp_app = typer.Typer(
    help="Server MCP di Lovarch (per Claude Code / IDE). Richiede l'extra [mcp].",
    no_args_is_help=True,
)


@mcp_app.command("serve")
def serve_command() -> None:
    """Avvia il server MCP su stdio.

    Registra in Claude Code con:
        claude mcp add lovarch -- lovarch mcp serve
    """
    from lovarch_cli.mcp.server import serve

    serve()


@mcp_app.command("key")
def key_command(
    label: str = typer.Option(None, "--label", "-l", help="Etichetta della chiave (es. 'claude-code macbook')."),
    revoke: str = typer.Option(None, "--revoke", help="ID di una chiave da revocare."),
    list_keys: bool = typer.Option(False, "--list", help="Elenca le chiavi esistenti."),
) -> None:
    """Crea (o gestisce) una chiave di connessione per il MCP REMOTO
    (https://mcp.lovarch.com/mcp). La chiave è mostrata UNA sola volta."""
    import asyncio

    from rich.console import Console

    from lovarch_cli.auth.session import LovarchSession

    console = Console()
    err_console = Console(stderr=True)

    session = LovarchSession.load()
    if session is None:
        err_console.print("[red]✗ Non autenticato. Esegui `lovarch login --premium`.[/red]")
        raise typer.Exit(1)

    async def _call(body: dict) -> dict:
        resp = await session.request("POST", "/functions/v1/mcp-key-create", json=body)
        try:
            return resp.json()
        except ValueError:
            return {"ok": False, "error": f"HTTP {resp.status_code}"}

    if list_keys:
        data = asyncio.run(_call({"action": "list"}))
        for k in data.get("keys", []):
            state = "revocata" if k.get("revoked_at") else "attiva"
            console.print(f"  {k['id'][:8]} · {k.get('label') or '—'} · {state} · creata {str(k.get('created_at'))[:10]}")
        if not data.get("keys"):
            console.print("[dim]Nessuna chiave.[/dim]")
        return

    if revoke:
        data = asyncio.run(_call({"action": "revoke", "key_id": revoke}))
        if data.get("ok"):
            console.print(f"[green]✓[/green] chiave revocata: {revoke}")
        else:
            err_console.print(f"[red]✗ {data.get('error')}[/red]")
            raise typer.Exit(1)
        return

    data = asyncio.run(_call({"action": "create", "label": label}))
    if not data.get("ok"):
        err_console.print(f"[red]✗ {data.get('error')}[/red]")
        raise typer.Exit(1)
    console.print("\n[bold gold1]Chiave MCP creata[/bold gold1] [dim](mostrata solo ORA — salvala)[/dim]\n")
    console.print(f"  [bold]{data['key']}[/bold]\n")
    console.print("Collega a Claude Code:\n")
    console.print(f"  [cyan]claude mcp add lovarch --transport http {data.get('mcp_url', 'https://mcp.lovarch.com/mcp')} --header \"Authorization: Bearer {data['key']}\"[/cyan]\n")
