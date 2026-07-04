"""`lovarch cad` — generate real 2D CAD (DXF) from room specs.

    lovarch cad genera -o pianta.dxf                       # standard 7-room flat
    lovarch cad genera --rooms rooms.json -o pianta.dxf    # your rooms
    lovarch cad genera --brief "attico 90mq, 2 camere" -o pianta.dxf   # AI layout (crediti)

Deterministic geometry (ezdxf) laid out on the 9 ISO layers with a CNAPPC
cartiglio — no credits for the geometry. `--brief` uses the platform AI only to
turn a description into a room list (that step debits credits). The output passes
`lovarch verifica misure`.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from lovarch_cli.upsell import not_authenticated

console = Console()
err_console = Console(stderr=True)

cad_app = typer.Typer(
    help="Genera CAD 2D (DXF) da specifiche di ambienti (deterministico, gratis).",
    no_args_is_help=True,
)

_LAYOUT_SYSTEM = (
    "Sei un assistente di progettazione. Data una descrizione, restituisci SOLO "
    "JSON valido con la lista degli ambienti e le dimensioni in metri: "
    '{"rooms": [{"name": "soggiorno", "width_m": 5.0, "height_m": 4.0}, ...]}. '
    "Usa nomi italiani standard (ingresso, soggiorno, cucina, studio, camera, "
    "bagno, lavanderia). Dimensioni realistiche e coerenti con la superficie."
)


@cad_app.command("genera")
def genera_command(
    output: Path = typer.Option(Path("pianta.dxf"), "--output", "-o", help="File DXF di output."),
    rooms_file: Path = typer.Option(None, "--rooms", help="JSON con la lista ambienti."),
    brief: str = typer.Option(None, "--brief", help="Descrizione → layout via IA (crediti)."),
    progetto: str = typer.Option("Progetto", "--progetto"),
    cliente: str = typer.Option("Cliente", "--cliente"),
    architetto: str = typer.Option("Arch.", "--architetto"),
    scala: str = typer.Option("1:100", "--scala"),
    data: str = typer.Option("", "--data"),
    verifica: bool = typer.Option(True, "--verifica/--no-verifica", help="Verifica il DXF generato."),
    language: str = typer.Option(None, "--language"),
) -> None:
    """Genera una pianta DXF (9 layer ISO + cartiglio CNAPPC)."""
    from lovarch_cli.cad import generate_floorplan

    rooms = None
    credits_charged = 0

    if brief:
        # AI layout: turn the description into a room list (debits credits).
        from lovarch_cli.ai import AiGatewayError, LovarchAiGateway
        from lovarch_cli.auth.session import LovarchSession
        from lovarch_cli.i18n import current_lang

        session = LovarchSession.load()
        if session is None:
            not_authenticated("Il layout via IA (--brief)")
            raise typer.Exit(1)
        try:
            res = asyncio.run(LovarchAiGateway(session).generate_text(
                brief, role="executor", system=_LAYOUT_SYSTEM, max_tokens=800,
                language=language or current_lang(), operation_type="cad:layout",
            ))
            credits_charged = res.credits_charged
            parsed = json.loads(res.text[res.text.find("{"):res.text.rfind("}") + 1])
            rooms = parsed.get("rooms")
        except (AiGatewayError, ValueError) as exc:
            err_console.print(f"[red]✗ layout IA non riuscito: {exc}[/red]")
            raise typer.Exit(1)
    elif rooms_file:
        try:
            data_in = json.loads(Path(rooms_file).expanduser().read_text(encoding="utf-8"))
            rooms = data_in.get("rooms") if isinstance(data_in, dict) else data_in
        except (json.JSONDecodeError, OSError) as exc:
            err_console.print(f"[red]✗ rooms non leggibile: {exc}[/red]")
            raise typer.Exit(1)

    result = generate_floorplan(
        rooms, out_path=output, progetto=progetto, cliente=cliente,
        architetto=architetto, scala=scala, data=data,
    )

    table = Table(title=f"CAD generato — {result.path}", header_style="bold gold1")
    table.add_column("Ambiente", style="cyan")
    table.add_column("L (m)", justify="right")
    table.add_column("H (m)", justify="right")
    for r in result.rooms:
        table.add_row(str(r["label"]), f"{r['width_m']:.2f}", f"{r['height_m']:.2f}")
    console.print(table)
    console.print(f"[green]✓[/green] {result.path} · {result.total_area_m2} mq · {result.layers} layer ISO"
                  + (f" · crediti: {credits_charged}" if credits_charged else " · gratis"))

    if verifica:
        from lovarch_cli.verify import verify_misure
        report = verify_misure(result.path)
        style = {"PASS": "green", "CONCERNS": "yellow", "REJECT": "red"}.get(report.verdict, "white")
        console.print(f"[dim]verifica misure:[/dim] [bold {style}]{report.verdict}[/bold {style}]"
                      + (f" — {report.findings[0]}" if report.findings else ""))


@cad_app.command("view")
def view_command(
    file: str = typer.Argument(..., help="File CAD/BIM: .dwg .dxf .rvt .ifc .skp .obj …"),
    wait: bool = typer.Option(True, "--wait/--no-wait", help="Attendi la traduzione."),
) -> None:
    """Carica un file CAD/BIM e rendilo navigabile nel viewer Autodesk dell'app.

    Traduzione addebitata in crediti (RVT/IFC/NWD 1500 · DWG/DXF e altri 300),
    rimborso automatico se fallisce. Il modello appare in `lovarch media cad`
    e su app.lovarch.com/cad/<id>.
    """
    import asyncio
    from pathlib import Path

    import httpx

    from lovarch_cli.ai import AiGatewayError, InsufficientCreditsError, LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession
    from lovarch_cli.upsell import insufficient_credits, not_authenticated

    path = Path(file).expanduser()
    if not path.is_file():
        err_console.print(f"[red]✗ File non trovato: {file}[/red]")
        raise typer.Exit(2)
    size = path.stat().st_size

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)
    gw = LovarchAiGateway(session)

    try:
        begin = asyncio.run(gw.platform("aps-cad", {
            "operation": "upload_begin", "file_name": path.name,
            "size_bytes": size, "source": "cli",
        }))
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]"); raise typer.Exit(1)

    cad_id = begin["cad_id"]
    urls = begin["upload_urls"]
    part_size = (size // len(urls)) + (1 if size % len(urls) else 0) if len(urls) > 1 else size

    with console.status(f"[gold1]Caricando {path.name} ({size // 1024} KB)…[/gold1]"):
        with open(path, "rb") as f, httpx.Client(timeout=600.0) as client:
            for url in urls:
                chunk = f.read(part_size)
                r = client.put(url, content=chunk)
                r.raise_for_status()

    try:
        asyncio.run(gw.platform("aps-cad", {
            "operation": "upload_complete", "cad_id": cad_id,
            "upload_key": begin["upload_key"],
        }))
        console.print("[green]✓[/green] caricato — urn pronto")
        tr = asyncio.run(gw.platform("aps-cad", {"operation": "translate", "cad_id": cad_id}))
        console.print(f"[green]✓[/green] traduzione avviata (crediti: {tr.get('credits_charged', 0)})")
    except InsufficientCreditsError as exc:
        insufficient_credits(exc.available, exc.needed); raise typer.Exit(1)
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]"); raise typer.Exit(1)

    if not wait:
        console.print(f"Controlla con: lovarch media cad  (id {str(cad_id)[:8]})")
        return

    import time as _time
    with console.status("[gold1]Traducendo il modello (Autodesk)…[/gold1]"):
        for _ in range(60):  # up to ~10 min
            _time.sleep(10)
            try:
                st = asyncio.run(gw.platform("aps-cad", {"operation": "status", "cad_id": cad_id}))
            except AiGatewayError:
                continue
            if st.get("status") == "ready":
                console.print("\n[green]✓ Modello pronto[/green]")
                console.print(f"  Viewer: https://app.lovarch.com/cad/{cad_id}")
                console.print("[dim]Elenco: lovarch media cad[/dim]")
                return
            if st.get("status") == "failed":
                err_console.print("[red]✗ Traduzione fallita — crediti rimborsati.[/red]")
                raise typer.Exit(1)
    console.print("[yellow]⚠ Traduzione ancora in corso — `lovarch media cad` per lo stato.[/yellow]")
