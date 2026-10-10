"""`lovarch proposte` — le proposte dello studio dal terminale (stessa api del connettore MCP).

    lovarch proposte elenco
    lovarch proposte migliora presentazione.pdf --cliente "Famiglia Bianchi"
    lovarch proposte migliora deck.pptx --modello <id> --max-crediti 200 --no-attendi
    lovarch proposte pdf <id-proposta> --a4 -o proposta.pdf
    lovarch proposte stato <job-id>

`migliora` è «Migliora una presentazione» dell'app: la presentazione GIÀ FATTA (PDF o
PowerPoint .pptx) diventa una proposta Lovarch con lo stesso testo e le stesse foto. Il file
viene caricato nel workspace solo per la lettura e cancellato subito dopo.
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.table import Table

from lovarch_cli.upsell import not_authenticated

console = Console()
err_console = Console(stderr=True)

proposte_app = typer.Typer(
    help="Proposte: elenco, Migliora una presentazione (PDF/PPTX), PDF.",
    no_args_is_help=True,
)

DONE = {"done", "failed", "cancelled"}


def _gateway():
    from lovarch_cli.ai import LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)
    return LovarchAiGateway(session)


async def wait_job(gw, job_id: str, every: float = 5.0, timeout: float = 900.0) -> dict:
    """Interroga `proposals.status` finché il job non è finito (o scade il tempo)."""
    deadline = time.monotonic() + timeout
    last: dict = {"status": "processing", "job_id": job_id}
    while time.monotonic() < deadline:
        await asyncio.sleep(every)
        last = await gw.api("proposals.status", {"job_id": job_id})
        if str(last.get("status", "")).lower() in DONE:
            return last
    return last


def _run(coro):
    from lovarch_cli.ai import AiGatewayError

    try:
        return asyncio.run(coro)
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)


@proposte_app.command("elenco")
def list_command(
    stato: str = typer.Option(None, "--stato", help="draft, sent, accepted…"),
    cerca: str = typer.Option(None, "--cerca", help="Cerca nel titolo."),
    limite: int = typer.Option(20, "--limite"),
) -> None:
    """Le proposte del workspace (con il link del cliente, se già inviata)."""
    gw = _gateway()
    params: dict = {"limit": limite}
    if stato:
        params["status"] = stato
    if cerca:
        params["q"] = cerca
    out = _run(gw.api("proposals.list", params))
    table = Table("id", "titolo", "cliente", "stato", "totale", "link cliente")
    for p in out.get("proposals", []):
        table.add_row(str(p.get("id", ""))[:8], str(p.get("title") or ""), str(p.get("client_name") or ""),
                      str(p.get("status") or ""), str(p.get("total") or ""), str(p.get("client_url") or "—"))
    console.print(table)


@proposte_app.command("migliora")
def restyle_command(
    file: Path = typer.Argument(..., help="La presentazione: PDF o PowerPoint .pptx"),
    cliente: str = typer.Option(None, "--cliente", help="Nome del cliente sulla copertina."),
    lead: str = typer.Option(None, "--lead", help="ID cliente del CRM."),
    modello: str = typer.Option(None, "--modello", help="ID di un modello salvato (template)."),
    lingua: str = typer.Option("it", "--lingua", help="it | en | pt | es"),
    termini: bool = typer.Option(False, "--termini/--no-termini", help="Aggiunge termini e firma."),
    copertina: bool = typer.Option(True, "--copertina/--no-copertina"),
    max_crediti: int = typer.Option(None, "--max-crediti", help="Non parte se la stima supera il tetto."),
    attendi: bool = typer.Option(True, "--attendi/--no-attendi", help="Aspetta la proposta pronta."),
) -> None:
    """«Migliora una presentazione»: PDF/PPTX → proposta Lovarch (stesso testo, stesse foto)."""
    gw = _gateway()

    async def run() -> dict:
        ref = await gw.upload_file(str(file), "proposals")
        body: dict = {
            "storage_path": ref.get("storage_path"), "language": lingua,
            "include_terms_sign": termini, "include_cover": copertina,
        }
        for k, v in (("client_name", cliente), ("lead_id", lead), ("template_id", modello), ("max_credits", max_crediti)):
            if v is not None:
                body[k] = v
        started = await gw.api("proposals.restyle", body)
        console.print(f"[dim]… {started.get('pages', '?')} pagine, {started.get('photos', 0)} foto — job {started.get('job_id')}[/dim]")
        return await wait_job(gw, str(started["job_id"])) if attendi else started

    out = _run(run())
    if out.get("status") == "done":
        console.print(f"[green]✓[/green] proposta «{out.get('title')}» pronta ({out.get('slides')} slide, "
                      f"{out.get('credits_cost', 0)} crediti) — id {out.get('proposal_id')}")
        console.print(f"  Apri l'app → Clienti → Proposte · PDF: lovarch proposte pdf {out.get('proposal_id')}")
    elif out.get("status") in ("failed", "cancelled"):
        err_console.print(f"[red]✗ {out.get('error') or out.get('status')}[/red]")
        raise typer.Exit(1)
    else:
        console.print(f"Job avviato: {out.get('job_id')} — lovarch proposte stato {out.get('job_id')}")


@proposte_app.command("pdf")
def pdf_command(
    proposal_id: str = typer.Argument(..., help="ID della proposta (lovarch proposte elenco)."),
    a4: bool = typer.Option(False, "--a4", help="A4 verticale (stampa) invece di 16:9."),
    output: Path = typer.Option(None, "--output", "-o", help="Salva il PDF su file."),
) -> None:
    """Esporta la proposta in PDF (16:9 o A4) e, con -o, lo scarica."""
    gw = _gateway()

    async def run() -> dict:
        started = await gw.api("proposals.export_pdf", {"proposal_id": proposal_id, "format": "a4" if a4 else "16x9"})
        return await wait_job(gw, str(started["job_id"]), every=3.0, timeout=420.0)

    out = _run(run())
    url = out.get("url")
    if out.get("status") != "done" or not url:
        err_console.print(f"[red]✗ PDF non pronto: {out.get('error') or out.get('status')}[/red]")
        raise typer.Exit(1)
    if output:
        r = httpx.get(str(url), timeout=120.0)
        r.raise_for_status()
        output.write_bytes(r.content)
        console.print(f"[green]✓[/green] {output} ({len(r.content) // 1024} KB)")
    else:
        console.print(f"[green]✓[/green] PDF pronto (link valido 1 ora): {url}")


@proposte_app.command("stato")
def status_command(job_id: str = typer.Argument(...)) -> None:
    """Stato di un job di proposta (migliora / pdf)."""
    out = _run(_gateway().api("proposals.status", {"job_id": job_id}))
    console.print_json(data=out)
