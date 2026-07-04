"""`lovarch media` — la tua galleria Lovarch dal terminale.

    lovarch media list                    (immagini/video generati, app+CLI+MCP)
    lovarch media list --type video
    lovarch media download <id>           (scarica l'asset originale)
    lovarch media worlds                  (mondi 3D WorldLabs)
    lovarch media cad                     (modelli CAD/BIM caricati)

Tutto ciò che generi dal terminale appare nell'app, e tutto ciò che hai
generato nell'app si scarica da qui. Sola lettura: nessun credito addebitato.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.table import Table

from lovarch_cli.upsell import not_authenticated

console = Console()
err_console = Console(stderr=True)

media_app = typer.Typer(
    help="Galleria Lovarch: immagini, video, mondi 3D e CAD (premium, gratis).",
    no_args_is_help=True,
)


def _gateway():
    from lovarch_cli.ai import LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)
    return LovarchAiGateway(session)


@media_app.command("list")
def list_command(
    asset_type: str = typer.Option(None, "--type", help="image | video"),
    limit: int = typer.Option(20, "--limit", "-n", help="Quanti elementi mostrare."),
) -> None:
    """Elenca le tue creazioni (le stesse della galleria dell'app)."""
    from lovarch_cli.ai import AiGatewayError

    gw = _gateway()
    params: dict = {"limit": limit}
    if asset_type in ("image", "video"):
        params["asset_type"] = asset_type
    try:
        data = asyncio.run(gw.data("media_list", **params))
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)

    items = data.get("items", [])
    if not items:
        console.print("[dim]Nessuna creazione ancora. Prova `lovarch do render` o genera nell'app.[/dim]")
        return
    table = Table(title=f"Le tue creazioni ({data.get('total', len(items))} totali)", header_style="bold gold1")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Tipo")
    table.add_column("Modalità")
    table.add_column("Fonte")
    table.add_column("Creato")
    for it in items:
        source = (it.get("metadata") or {}).get("source", "app")
        table.add_row(
            str(it["id"])[:8], it.get("asset_type", "?"), it.get("render_mode") or "—",
            source, str(it.get("created_at", ""))[:16].replace("T", " "),
        )
    console.print(table)
    console.print("[dim]Scarica con: lovarch media download <id>[/dim]")


@media_app.command("download")
def download_command(
    asset_id: str = typer.Argument(..., help="ID (anche solo le prime 8 cifre) dell'asset."),
    output: str = typer.Option(None, "--output", "-o", help="File di destinazione."),
) -> None:
    """Scarica un asset della galleria sul disco."""
    from lovarch_cli.ai import AiGatewayError

    gw = _gateway()
    try:
        # Short-id convenience: resolve via list when not a full UUID.
        target_id = asset_id
        if len(asset_id) < 36:
            listing = asyncio.run(gw.data("media_list", limit=100))
            matches = [i for i in listing.get("items", []) if str(i["id"]).startswith(asset_id)]
            if len(matches) != 1:
                err_console.print(f"[red]✗ ID ambiguo o non trovato: {asset_id} ({len(matches)} corrispondenze)[/red]")
                raise typer.Exit(2)
            target_id = matches[0]["id"]
        data = asyncio.run(gw.data("media_get", id=target_id))
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)

    item = data["item"]
    url = item.get("asset_url", "")
    if not url.startswith("http"):
        err_console.print("[red]✗ Asset senza URL scaricabile.[/red]")
        raise typer.Exit(1)

    ext = url.split("?")[0].rsplit(".", 1)[-1] if "." in url.split("?")[0].rsplit("/", 1)[-1] else (
        "mp4" if item.get("asset_type") == "video" else "png")
    dest = Path(output).expanduser() if output else Path(f"lovarch-{str(item['id'])[:8]}.{ext}")
    with httpx.stream("GET", url, timeout=300.0, follow_redirects=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    console.print(f"[green]✓[/green] scaricato: {dest} ({dest.stat().st_size // 1024} KB)")


@media_app.command("worlds")
def worlds_command(
    limit: int = typer.Option(20, "--limit", "-n"),
) -> None:
    """Elenca i tuoi mondi 3D (WorldLabs Marble)."""
    from lovarch_cli.ai import AiGatewayError

    gw = _gateway()
    try:
        data = asyncio.run(gw.data("worlds_list", limit=limit))
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)
    items = data.get("items", [])
    if not items:
        console.print("[dim]Nessun mondo 3D. Genera con: lovarch do world \"<prompt o immagine>\"[/dim]")
        return
    table = Table(title="I tuoi mondi 3D", header_style="bold gold1")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Nome")
    table.add_column("Stato")
    table.add_column("Naviga")
    for w in items:
        table.add_row(
            str(w["id"])[:8], w.get("display_name") or "—", w.get("status", "?"),
            w.get("marble_url") or "—",
        )
    console.print(table)


@media_app.command("cad")
def cad_command(
    limit: int = typer.Option(20, "--limit", "-n"),
) -> None:
    """Elenca i tuoi modelli CAD/BIM (Autodesk viewer)."""
    from lovarch_cli.ai import AiGatewayError

    gw = _gateway()
    try:
        data = asyncio.run(gw.data("cad_list", limit=limit))
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)
    items = data.get("items", [])
    if not items:
        console.print("[dim]Nessun modello CAD. Carica con: lovarch cad view <file.dwg|rvt|ifc>[/dim]")
        return
    table = Table(title="I tuoi modelli CAD/BIM", header_style="bold gold1")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("File")
    table.add_column("Stato")
    table.add_column("Viewer")
    for m in items:
        viewer = (f"https://app.lovarch.com/cad/{m['id']}" if m.get("status") == "ready" else "—")
        table.add_row(str(m["id"])[:8], m.get("file_name", "?"), m.get("status", "?"), viewer)
    console.print(table)
