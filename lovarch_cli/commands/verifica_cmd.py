"""`lovarch verifica` — conferência de dados para profissionais.

    lovarch verifica misure pianta.dxf          (determinístico, grátis)
    lovarch verifica normativa capitolato.pdf   (adversarial 2 modelos, débito)
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()
err_console = Console(stderr=True)

verifica_app = typer.Typer(
    help="Verifica dati e documenti (misure DXF gratis · normativa adversarial).",
    no_args_is_help=True,
)

_VERDICT_STYLE = {"PASS": "green", "CONCERNS": "yellow", "REJECT": "red"}


def _print_verdict(verdict: str) -> None:
    style = _VERDICT_STYLE.get(verdict, "white")
    console.print(f"\n[bold {style}]VERDETTO: {verdict}[/bold {style}]")


@verifica_app.command("misure")
def misure_command(
    dxf: Path = typer.Argument(..., help="File DXF da verificare."),
) -> None:
    """Verifica layer ISO, etichette ambienti e cartiglio CNAPPC (gratis)."""
    from lovarch_cli.verify import verify_misure

    report = verify_misure(dxf)
    table = Table(title=f"verifica misure — {dxf.name}", header_style="bold gold1")
    table.add_column("Controllo", style="cyan")
    table.add_column("Esito")
    table.add_row("Entità DXF", str(report.stats.get("entities", "—")))
    table.add_row("Layer ISO presenti", f"{report.stats.get('iso_layers_present', 0)}/9")
    table.add_row("Ambienti etichettati", ", ".join(report.stats.get("room_labels_found", [])) or "—")
    console.print(table)
    for f in report.findings:
        console.print(f"  [yellow]·[/yellow] {f}")
    _print_verdict(report.verdict)
    raise typer.Exit(0 if report.verdict == "PASS" else (2 if report.verdict == "CONCERNS" else 1))


@verifica_app.command("normativa")
def normativa_command(
    documento: Path = typer.Argument(..., help="Documento da verificare (.pdf, .md, .txt)."),
    language: str = typer.Option(None, "--language", help="Lingua del report."),
) -> None:
    """Verifica adversarial das citações normativas (2 modelos · debita créditos)."""
    from lovarch_cli.ai import LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession
    from lovarch_cli.i18n import current_lang
    from lovarch_cli.verify import verify_normativa
    from lovarch_cli.verify.normativa import NormativaError

    session = LovarchSession.load()
    if session is None:
        err_console.print("[red]✗ Non autenticato. Esegui `lovarch login --premium`.[/red]")
        raise typer.Exit(1)

    try:
        report = asyncio.run(verify_normativa(
            LovarchAiGateway(session), documento, language=language or current_lang(),
        ))
    except NormativaError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)

    if report.canonical_found:
        console.print(f"[dim]Riferimenti canonici rilevati: {', '.join(report.canonical_found)}[/dim]")
    table = Table(title=f"verifica normativa — {documento.name}", header_style="bold gold1")
    table.add_column("Riferimento", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Motivo")
    for v in report.verdicts:
        status = str(v.get("status", "?")).lower()
        icon = {"ok": "[green]✓[/green]", "refuted": "[red]✗[/red]", "doubt": "[yellow]?[/yellow]"}.get(status, "?")
        table.add_row(str(v.get("reference", "—")), icon, str(v.get("reason", ""))[:100])
    console.print(table)
    for n in report.notes:
        console.print(f"  [yellow]·[/yellow] {n}")
    console.print(f"[dim]Crediti addebitati: {report.credits_charged}[/dim]")
    _print_verdict(report.verdict)
    raise typer.Exit(0 if report.verdict == "PASS" else (2 if report.verdict == "CONCERNS" else 1))
