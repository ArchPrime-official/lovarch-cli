"""`lovarch crea` — scrivi nel TUO account Lovarch dal terminale.

    lovarch crea lead "Mario Rossi" --email m@rossi.it --telefono 333...
    lovarch crea spesa 240 "Ferramenta — cantiere Rossi"
    lovarch crea entrata 3500 "Acconto progetto Bianchi"
    lovarch crea progetto "Appartamento Rossi" --cliente "Mario Rossi" --mq 80
    lovarch crea task "Preparare rilievo" --scadenza 2026-08-01
    lovarch crea proposta "Ristrutturazione Rossi" --cliente "Mario Rossi" --totale 12000
    lovarch crea contratto "Incarico Rossi" --cliente "Mario Rossi"
    lovarch crea fornitore "Idraulica SRL" --progetto "Appartamento Rossi"
    lovarch crea audience "Proprietari 35-55 Milano"
    lovarch crea campagna "Lancio autunno" --piattaforma instagram --budget 500
    lovarch crea categoria "Trasferte" --tipo expense

E per aggiornare lo stato di un lead:

    lovarch aggiorna lead-stato "Mario Rossi" closed_won

Sono i TUOI dati: nessun credito addebitato. La scrittura è owner-scoped lato
server (un membro del team scrive nell'account del titolare).
"""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console

from lovarch_cli.upsell import not_authenticated

console = Console()
err_console = Console(stderr=True)

crea_app = typer.Typer(
    help="Crea nel tuo account Lovarch: lead, progetti, spese, task… (gratis).",
    no_args_is_help=True,
)
aggiorna_app = typer.Typer(
    help="Aggiorna dati esistenti nel tuo account Lovarch (gratis).",
    no_args_is_help=True,
)


def _clean(params: dict) -> dict:
    """Toglie i campi non valorizzati.

    Il registry lato server tratta il campo ASSENTE diversamente da una stringa
    vuota (`''` passerebbe la validazione e finirebbe nel DB come valore vuoto).
    """
    return {k: v for k, v in params.items() if v is not None and v != ""}


def _write(action: str, **params) -> dict:
    """Chiama cli-write e stampa l'errore in modo leggibile."""
    from lovarch_cli.ai import AiGatewayError, LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)
    clean = _clean(params)
    try:
        return asyncio.run(LovarchAiGateway(session).write(action, **clean))
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)


def _ok(label: str, payload: dict, hint: str) -> None:
    data = payload.get("data") or {}
    new_id = data.get("id") if isinstance(data, dict) else None
    suffix = f" [dim]({str(new_id)[:8]})[/dim]" if new_id else ""
    console.print(f"[green]✓[/green] {label}{suffix}")
    _print_workspace_if_shared()
    console.print(f"[dim]{hint}[/dim]")


def _print_workspace_if_shared() -> None:
    """Dice DOVE è finito il dato, quando l'utente collabora con più studi.

    Chi ha un solo workspace non vede niente: sarebbe rumore su ogni comando.
    Chi ne ha più di uno ha bisogno di saperlo — creare un lead nello studio
    sbagliato è silenzioso e si scopre giorni dopo.

    Best-effort: se la chiamata fallisce non si dice niente e il comando resta
    riuscito. Non è una conferma, è un promemoria.
    """
    try:
        from lovarch_cli.ai import LovarchAiGateway
        from lovarch_cli.auth.session import LovarchSession

        session = LovarchSession.load()
        if session is None:
            return
        payload = asyncio.run(LovarchAiGateway(session).workspace("status"))
        spaces = payload.get("workspaces") or []
        if len(spaces) <= 1:
            return
        cur = payload.get("current") or {}
        name = "Personale" if cur.get("is_personal") else (cur.get("owner_name") or "—")
        console.print(f"[dim]workspace: {name}[/dim]")
    except Exception:
        return


# ── CRM ────────────────────────────────────────────────────────────────────────

@crea_app.command("lead")
def lead_command(
    nome: str = typer.Argument(..., help="Nome del contatto."),
    email: str = typer.Option(None, "--email"),
    telefono: str = typer.Option(None, "--telefono", "--phone"),
    tipo: str = typer.Option(None, "--tipo", help="Tipo di progetto (es. ristrutturazione)."),
    note: str = typer.Option(None, "--note"),
) -> None:
    """Aggiunge un contatto al CRM."""
    p = _write("create_lead", name=nome, email=email, phone=telefono,
               project_type=tipo, notes=note)
    _ok(f"Lead creato: [bold]{nome}[/bold]", p, "Vedi: lovarch dati clienti")


@aggiorna_app.command("lead-stato")
def lead_status_command(
    nome: str = typer.Argument(..., help="Nome (anche parziale) del lead."),
    stato: str = typer.Argument(..., help="new · contacted · qualified · proposal · closed_won · closed_lost"),
) -> None:
    """Aggiorna lo stato di un lead del CRM."""
    p = _write("update_lead_status", lead_name=nome, status=stato)
    _ok(f"Lead aggiornato: [bold]{nome}[/bold] → {stato}", p, "Vedi: lovarch dati clienti")


@crea_app.command("task")
def task_command(
    titolo: str = typer.Argument(..., help="Cosa c'è da fare."),
    descrizione: str = typer.Option(None, "--descrizione", "-d"),
    scadenza: str = typer.Option(None, "--scadenza", help="AAAA-MM-GG"),
    priorita: str = typer.Option(None, "--priorita", help="low · medium · high"),
    progetto_id: str = typer.Option(None, "--progetto-id"),
) -> None:
    """Crea un'attività."""
    p = _write("create_task", title=titolo, description=descrizione,
               due_date=scadenza, priority=priorita, project_id=progetto_id)
    _ok(f"Task creato: [bold]{titolo}[/bold]", p, "Lo trovi nei task della piattaforma.")


@crea_app.command("proposta")
def proposal_command(
    titolo: str = typer.Argument(..., help="Titolo della proposta."),
    cliente: str = typer.Option(None, "--cliente"),
    totale: float = typer.Option(None, "--totale", help="Importo in EUR."),
) -> None:
    """Crea una proposta commerciale."""
    p = _write("create_proposal", title=titolo, client_name=cliente, total=totale)
    _ok(f"Proposta creata: [bold]{titolo}[/bold]", p, "La trovi in Proposte.")


@crea_app.command("contratto")
def contract_command(
    titolo: str = typer.Argument(..., help="Titolo del contratto."),
    cliente: str = typer.Option(None, "--cliente"),
    scadenza: str = typer.Option(None, "--scadenza", help="AAAA-MM-GG"),
) -> None:
    """Crea un contratto."""
    p = _write("create_contract", title=titolo, client_name=cliente, expires_at=scadenza)
    _ok(f"Contratto creato: [bold]{titolo}[/bold]", p, "Vedi: lovarch dati contratti")


# ── PROGETTI ───────────────────────────────────────────────────────────────────

@crea_app.command("progetto")
def project_command(
    nome: str = typer.Argument(..., help="Nome del progetto/cantiere."),
    cliente: str = typer.Option(None, "--cliente"),
    tipologia: str = typer.Option(None, "--tipologia"),
    mq: float = typer.Option(None, "--mq", help="Superficie in m²."),
    inizio: str = typer.Option(None, "--inizio", help="AAAA-MM-GG"),
) -> None:
    """Crea un progetto/cantiere."""
    p = _write("create_project", name=nome, client_name=cliente, typology=tipologia,
               square_meters=mq, start_date=inizio)
    _ok(f"Progetto creato: [bold]{nome}[/bold]", p, "Vedi: lovarch dati progetti")


@crea_app.command("fornitore")
def supplier_command(
    nome: str = typer.Argument(..., help="Nome del fornitore."),
    progetto: str = typer.Option(..., "--progetto", help="Nome del progetto a cui collegarlo."),
    ruolo: str = typer.Option(None, "--ruolo", help="Es. idraulico, elettricista."),
    telefono: str = typer.Option(None, "--telefono"),
) -> None:
    """Aggiunge un fornitore a un progetto."""
    p = _write("create_supplier", name=nome, project_name=progetto, role=ruolo, phone=telefono)
    _ok(f"Fornitore creato: [bold]{nome}[/bold]", p, f"Collegato al progetto «{progetto}».")


# ── SOLDI ──────────────────────────────────────────────────────────────────────

@crea_app.command("spesa")
def expense_command(
    importo: float = typer.Argument(..., help="Importo in EUR."),
    descrizione: str = typer.Argument(..., help="Cosa hai pagato."),
    data: str = typer.Option(None, "--data", help="AAAA-MM-GG (default: oggi)."),
    stato: str = typer.Option(None, "--stato", help="paid (default) · pending"),
) -> None:
    """Registra un'uscita."""
    p = _write("create_financial_transaction", type="expense", value=importo,
               description=descrizione, date=data, status=stato)
    _ok(f"Uscita registrata: [bold]€ {importo:,.2f}[/bold] — {descrizione}", p,
        "Vedi: lovarch dati finanze")


@crea_app.command("entrata")
def income_command(
    importo: float = typer.Argument(..., help="Importo in EUR."),
    descrizione: str = typer.Argument(..., help="Da cosa arriva."),
    data: str = typer.Option(None, "--data", help="AAAA-MM-GG (default: oggi)."),
    stato: str = typer.Option(None, "--stato", help="paid (default) · pending"),
) -> None:
    """Registra un'entrata."""
    p = _write("create_financial_transaction", type="income", value=importo,
               description=descrizione, date=data, status=stato)
    _ok(f"Entrata registrata: [bold]€ {importo:,.2f}[/bold] — {descrizione}", p,
        "Vedi: lovarch dati finanze")


@crea_app.command("categoria")
def category_command(
    nome: str = typer.Argument(..., help="Nome della categoria."),
    tipo: str = typer.Option("expense", "--tipo", help="expense (default) · income"),
) -> None:
    """Crea una categoria finanziaria."""
    p = _write("create_financial_category", name=nome, type=tipo)
    _ok(f"Categoria creata: [bold]{nome}[/bold] ({tipo})", p, "La usi nel modulo Finanze.")


# ── MARKETING ──────────────────────────────────────────────────────────────────

@crea_app.command("audience")
def audience_command(
    nome: str = typer.Argument(..., help="Nome del pubblico."),
    descrizione: str = typer.Option(None, "--descrizione", "-d"),
) -> None:
    """Crea un'audience marketing."""
    p = _write("create_audience", name=nome, description=descrizione)
    _ok(f"Audience creata: [bold]{nome}[/bold]", p, "La trovi in Audiences.")


@crea_app.command("campagna")
def campaign_command(
    nome: str = typer.Argument(..., help="Nome della campagna."),
    obiettivo: str = typer.Option(None, "--obiettivo"),
    piattaforma: str = typer.Option(None, "--piattaforma", help="Es. instagram, meta, google."),
    budget: float = typer.Option(None, "--budget", help="Budget totale in EUR."),
) -> None:
    """Crea una campagna marketing."""
    p = _write("create_campaign", name=nome, objective=obiettivo,
               platform=piattaforma, budget_total=budget)
    _ok(f"Campagna creata: [bold]{nome}[/bold]", p, "La trovi in Campagne.")
