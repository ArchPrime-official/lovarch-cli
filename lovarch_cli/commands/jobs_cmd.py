"""`lovarch jobs` — async platform jobs (video, Shotstack export, upscale).

    lovarch jobs list
    lovarch jobs status <id>

Reads content_video_jobs via the user's own session (owner RLS). Costs are
shown only as the user's credits.
"""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table
from lovarch_cli.upsell import not_authenticated

console = Console()
err_console = Console(stderr=True)

jobs_app = typer.Typer(
    help="Job asincroni della piattaforma (video, export, upscale).",
    no_args_is_help=True,
)

_STATUS_ICON = {"done": "✅", "completed": "✅", "failed": "❌", "error": "❌",
                "running": "⏳", "pending": "⏳", "queued": "⏳"}


def _workflows():
    from lovarch_cli.auth.session import LovarchSession
    from lovarch_cli.workflows import PlatformWorkflows

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)
    return PlatformWorkflows(session)


@jobs_app.command("list")
def list_command(
    limit: int = typer.Option(10, "--limit", "-n", help="Quanti job mostrare."),
) -> None:
    """Ultimi job asincroni dell'account."""
    from lovarch_cli.workflows import WorkflowError

    try:
        jobs = asyncio.run(_workflows().jobs_list(limit=limit))
    except WorkflowError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)
    if not jobs:
        console.print("[dim]Nessun job trovato.[/dim]")
        return
    table = Table(title="Job asincroni", header_style="bold gold1")
    for col in ("Stato", "Engine", "Modello", "Crediti", "Creato", "ID"):
        table.add_column(col)
    for j in jobs:
        status = str(j.get("status", "?"))
        table.add_row(
            f"{_STATUS_ICON.get(status, '·')} {status}",
            str(j.get("engine", "—")), str(j.get("model", "—")),
            str(j.get("credits_charged", "—")),
            str(j.get("created_at", ""))[:16], str(j.get("id", ""))[:8],
        )
    console.print(table)


@jobs_app.command("status")
def status_command(
    job_id: str = typer.Argument(..., help="ID del job."),
) -> None:
    """Stato dettagliato di un job."""
    from lovarch_cli.workflows import WorkflowError

    try:
        j = asyncio.run(_workflows().job_status(job_id))
    except WorkflowError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)
    status = str(j.get("status", "?"))
    console.print(f"{_STATUS_ICON.get(status, '·')} [bold]{status}[/bold] · {j.get('engine')} · {j.get('model')}")
    if j.get("prompt"):
        console.print(f"[dim]{str(j['prompt'])[:120]}[/dim]")
    if j.get("output_url"):
        console.print(f"[green]Output:[/green] {j['output_url']}")
    if j.get("error_message"):
        console.print(f"[red]Errore:[/red] {j['error_message']}")
    charged = j.get("credits_charged")
    refunded = j.get("credits_refunded")
    if charged is not None:
        line = f"Crediti: {charged}"
        if refunded:
            line += f" (rimborsati: {refunded})"
        console.print(f"[dim]{line}[/dim]")
