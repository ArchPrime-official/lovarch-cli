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
            err_console.print("[red]✗ Non autenticato (--brief richiede login). `lovarch login --premium`.[/red]")
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
