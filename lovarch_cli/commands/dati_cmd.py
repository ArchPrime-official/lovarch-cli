"""`lovarch dati` — i dati del tuo account Lovarch dal terminale (sola lettura).

    lovarch dati progetti
    lovarch dati progetto <id>
    lovarch dati finanze [--mesi 12]
    lovarch dati prezzario "massetto" --region Lombardia
    lovarch dati clienti
    lovarch dati contratti

Gli agenti usano gli stessi dati per lavorare sul TUO studio, non su ipotesi.
Nessun credito addebitato.
"""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from lovarch_cli.upsell import not_authenticated

console = Console()
err_console = Console(stderr=True)

dati_app = typer.Typer(
    help="I tuoi dati Lovarch: progetti, finanze, prezzari, CRM (premium, gratis).",
    no_args_is_help=True,
)


def _fetch(resource: str, **params):
    from lovarch_cli.ai import AiGatewayError, LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)
    try:
        return asyncio.run(LovarchAiGateway(session).data(resource, **params))
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)


@dati_app.command("progetti")
def progetti_command(limit: int = typer.Option(20, "--limit", "-n")) -> None:
    """Elenca i tuoi progetti/cantieri."""
    data = _fetch("projects_list", limit=limit)
    items = data.get("items", [])
    if not items:
        console.print("[dim]Nessun progetto.[/dim]")
        return
    table = Table(title="I tuoi progetti", header_style="bold gold1")
    for col in ("ID", "Nome", "Stato", "Tipologia", "Cliente", "Budget"):
        table.add_column(col, style="cyan" if col == "ID" else None, no_wrap=(col == "ID"))
    for p in items:
        budget = "—"
        if p.get("budget_min") or p.get("budget_max"):
            budget = f"{p.get('budget_min') or '?'}–{p.get('budget_max') or '?'} EUR"
        table.add_row(str(p["id"])[:8], p.get("name", "?"), p.get("status", "?"),
                      p.get("typology") or "—", p.get("client_name") or "—", budget)
    console.print(table)
    console.print("[dim]Dettaglio: lovarch dati progetto <id>[/dim]")


@dati_app.command("progetto")
def progetto_command(project_id: str = typer.Argument(..., help="ID del progetto (anche 8 cifre).")) -> None:
    """Dettaglio di un progetto: fasi, task, budget, documenti."""
    target = project_id
    if len(project_id) < 36:
        listing = _fetch("projects_list", limit=100)
        matches = [p for p in listing.get("items", []) if str(p["id"]).startswith(project_id)]
        if len(matches) != 1:
            err_console.print(f"[red]✗ ID ambiguo o non trovato ({len(matches)} corrispondenze)[/red]")
            raise typer.Exit(2)
        target = matches[0]["id"]
    data = _fetch("project_get", id=target)
    p = data["project"]
    console.print(f"[bold gold1]{p.get('name')}[/bold gold1] — {p.get('status')} · "
                  f"{p.get('typology') or ''} {p.get('square_meters') or ''}mq · cliente {p.get('client_name') or '—'}")
    if data.get("phases"):
        t = Table(title="Fasi", header_style="bold")
        for c in ("Fase", "Stato", "Inizio", "Fine"):
            t.add_column(c)
        for f in data["phases"]:
            t.add_row(f.get("name", "?"), f.get("status", "?"),
                      str(f.get("actual_start") or f.get("planned_start") or "—"),
                      str(f.get("actual_end") or f.get("planned_end") or "—"))
        console.print(t)
    if data.get("tasks"):
        open_tasks = [x for x in data["tasks"] if x.get("status") != "done"]
        console.print(f"Task aperti: [bold]{len(open_tasks)}[/bold] / {len(data['tasks'])}")
    if data.get("budget_items"):
        tot_est = sum(float(b.get("estimated_amount") or 0) for b in data["budget_items"])
        tot_act = sum(float(b.get("actual_amount") or 0) for b in data["budget_items"])
        console.print(f"Budget: stimato [bold]{tot_est:,.0f}[/bold] EUR · consuntivo [bold]{tot_act:,.0f}[/bold] EUR")
    if data.get("documents"):
        console.print(f"Documenti: {len(data['documents'])} (ultimi: "
                      + ", ".join(d.get("name", "?") for d in data["documents"][:3]) + ")")


@dati_app.command("finanze")
def finanze_command(mesi: int = typer.Option(12, "--mesi", help="Quanti mesi indietro.")) -> None:
    """Sintesi finanziaria: entrate/uscite per mese e spese per categoria."""
    data = _fetch("financial_summary", months=mesi)
    by_month = data.get("by_month", {})
    if not by_month:
        console.print("[dim]Nessuna transazione nel periodo.[/dim]")
        return
    table = Table(title=f"Finanze — ultimi {mesi} mesi", header_style="bold gold1")
    for c in ("Mese", "Entrate", "Uscite", "Saldo"):
        table.add_column(c, justify="right" if c != "Mese" else "left")
    for month in sorted(by_month):
        m = by_month[month]
        saldo = m["income"] - m["expense"]
        color = "green" if saldo >= 0 else "red"
        table.add_row(month, f"{m['income']:,.0f}", f"{m['expense']:,.0f}",
                      f"[{color}]{saldo:,.0f}[/{color}]")
    console.print(table)
    cats = data.get("expense_by_category", {})
    if cats:
        top = sorted(cats.items(), key=lambda kv: -kv[1])[:5]
        console.print("Top spese: " + " · ".join(f"{k} {v:,.0f}" for k, v in top))


@dati_app.command("prezzario")
def prezzario_command(
    search: str = typer.Argument(None, help="Testo da cercare nelle descrizioni."),
    region: str = typer.Option("Lombardia", "--region"),
    limit: int = typer.Option(20, "--limit", "-n"),
) -> None:
    """Consulta il prezzario regionale live."""
    params: dict = {"region": region, "limit": limit}
    if search:
        params["search"] = search
    data = _fetch("prezzario", **params)
    items = data.get("items", [])
    if not items:
        console.print(f"[dim]Nessuna voce per '{search or '*'}' in {region}.[/dim]")
        return
    table = Table(title=f"Prezzario {region}", header_style="bold gold1")
    for c in ("Codice", "Descrizione", "UM", "Prezzo"):
        table.add_column(c, justify="right" if c == "Prezzo" else "left")
    for v in items:
        desc = v.get("descrizione", "")
        table.add_row(v.get("codice", "?"), desc[:70] + ("…" if len(desc) > 70 else ""),
                      v.get("unita", "?"), f"{float(v.get('prezzo') or 0):,.2f}")
    console.print(table)


@dati_app.command("clienti")
def clienti_command(limit: int = typer.Option(20, "--limit", "-n")) -> None:
    """Elenca i tuoi clienti/lead CRM."""
    data = _fetch("leads_list", limit=limit)
    items = data.get("items", [])
    if not items:
        console.print("[dim]Nessun cliente nel CRM.[/dim]")
        return
    table = Table(title="Clienti / lead", header_style="bold gold1")
    for c in ("ID", "Nome", "Azienda", "Stato", "Budget"):
        table.add_column(c, style="cyan" if c == "ID" else None, no_wrap=(c == "ID"))
    for x in items:
        table.add_row(str(x["id"])[:8], x.get("name", "?"), x.get("company") or "—",
                      x.get("status") or "—", str(x.get("budget") or "—"))
    console.print(table)
    console.print("[dim]Usa un cliente come contesto: lovarch agent preventivi \"...\" --lead <id>[/dim]")


@dati_app.command("contratti")
def contratti_command(limit: int = typer.Option(20, "--limit", "-n")) -> None:
    """Elenca i tuoi contratti."""
    data = _fetch("contracts_list", limit=limit)
    items = data.get("items", [])
    if not items:
        console.print("[dim]Nessun contratto.[/dim]")
        return
    table = Table(title="Contratti", header_style="bold gold1")
    for c in ("ID", "Titolo", "Cliente", "Stato", "Firmato"):
        table.add_column(c, style="cyan" if c == "ID" else None, no_wrap=(c == "ID"))
    for x in items:
        table.add_row(str(x["id"])[:8], x.get("title", "?"), x.get("client_name") or "—",
                      x.get("status") or "—", str(x.get("signed_at") or "—")[:10])
    console.print(table)
