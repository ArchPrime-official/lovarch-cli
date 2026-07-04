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
from lovarch_cli.upsell import not_authenticated

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


@verifica_app.command("computo")
def computo_command(
    computo: Path = typer.Argument(..., help="Computo metrico (.csv o .json: codice,quantita,prezzo_unitario)."),
    region: str = typer.Option("Lombardia", "--region", help="Regione del prezzario di riferimento."),
    version: str = typer.Option(None, "--version", help="Versione del prezzario (opzionale)."),
) -> None:
    """Confronta le voci del computo col prezzario regionale (gratis, deterministico).

    Funziona offline con il prezzario Lombardia integrato; con login usa i prezzari
    live del DB (tutte le regioni/versioni)."""
    from lovarch_cli.auth.session import LovarchSession
    from lovarch_cli.verify import verify_computo
    from lovarch_cli.verify.computo import ComputoError

    # Login is optional: without a session we use the bundled Lombardia prezzario.
    session = LovarchSession.load()
    if session is None and region.lower() != "lombardia":
        err_console.print(
            f"[yellow]Prezzario '{region}' richiede login (i prezzari live).[/yellow] "
            "Offline è disponibile solo Lombardia. `lovarch login --premium`.")

    try:
        report = asyncio.run(verify_computo(session, computo, region=region, version=version))
    except ComputoError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)

    table = Table(title=f"verifica computo — {computo.name}", header_style="bold gold1")
    table.add_column("Metrica", style="cyan")
    table.add_column("Valore", justify="right")
    table.add_row("Prezzario", str(report.stats.get("prezzario", "—")))
    table.add_row("Voci totali", str(report.stats.get("voci_totali", "—")))
    table.add_row("Voci verificate", str(report.stats.get("voci_verificate", "—")))
    table.add_row("Codici sconosciuti", str(report.stats.get("codici_sconosciuti", 0)))
    table.add_row("Prezzi fuori tolleranza", str(report.stats.get("prezzi_fuori_tolleranza", 0)))
    table.add_row("Unità incoerenti", str(report.stats.get("unita_incoerenti", 0)))
    table.add_row("Totale computo (€)", f"{report.stats.get('totale_computo_eur', 0):,.2f}")
    console.print(table)
    for f in report.findings:
        console.print(f"  [yellow]·[/yellow] {f}")
    _print_verdict(report.verdict)
    raise typer.Exit(0 if report.verdict == "PASS" else (2 if report.verdict == "CONCERNS" else 1))


@verifica_app.command("pratica")
def pratica_command(
    documento: Path = typer.Argument(..., help="Pratica edilizia (.pdf, .md, .txt)."),
    tipo: str = typer.Option(None, "--tipo", help="CILA | SCIA (se noto)."),
    language: str = typer.Option(None, "--language", help="Lingua del report."),
) -> None:
    """Verifica adversarial di una pratica CILA/SCIA (2 modelli · debita crediti)."""
    from lovarch_cli.ai import LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession
    from lovarch_cli.i18n import current_lang
    from lovarch_cli.verify import verify_pratica
    from lovarch_cli.verify.normativa import NormativaError

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)

    try:
        report = asyncio.run(verify_pratica(
            LovarchAiGateway(session), documento, tipo=tipo,
            language=language or current_lang(),
        ))
    except NormativaError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)

    console.print(f"[dim]Tipo pratica: {report.tipo}[/dim]")
    table = Table(title=f"verifica pratica — {documento.name}", header_style="bold gold1")
    table.add_column("Area", style="cyan")
    table.add_column("Severità", justify="center")
    table.add_column("Motivo")
    for f in report.findings:
        sev = str(f.get("severity", "")).lower()
        icon = {"critical": "[red]✗[/red]", "concern": "[yellow]?[/yellow]", "info": "[dim]·[/dim]"}.get(sev, "?")
        table.add_row(str(f.get("area", "—")), icon, str(f.get("reason", ""))[:100])
    console.print(table)
    console.print("[dim]Firma e responsabilità restano del tecnico abilitato (BOZZA).[/dim]")
    console.print(f"[dim]Crediti addebitati: {report.credits_charged}[/dim]")
    _print_verdict(report.verdict)
    raise typer.Exit(0 if report.verdict == "PASS" else (2 if report.verdict == "CONCERNS" else 1))


def _run_adversarial_verify(verify_fn, documento, tipo_label, language, tipo_value=None):
    """Shared runner for the adversarial verifiers (sicurezza/accessibilità)."""
    from lovarch_cli.ai import LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession
    from lovarch_cli.i18n import current_lang
    from lovarch_cli.verify.normativa import NormativaError

    session = LovarchSession.load()
    if session is None:
        not_authenticated(tipo_label)
        raise typer.Exit(1)
    try:
        report = asyncio.run(verify_fn(
            LovarchAiGateway(session), str(documento), language=language or current_lang(),
        ))
    except NormativaError as exc:
        err_console.print(f"[red]✗ {exc}[/red]"); raise typer.Exit(1)

    table = Table(title=f"{tipo_label} — {documento.name}", header_style="bold gold1")
    table.add_column("Area", style="cyan")
    table.add_column("Severità", justify="center")
    table.add_column("Motivo")
    for f in report.findings:
        sev = str(f.get("severity", "")).lower()
        icon = {"critical": "[red]✗[/red]", "concern": "[yellow]?[/yellow]", "info": "[dim]·[/dim]"}.get(sev, "?")
        table.add_row(str(f.get("area", "—")), icon, str(f.get("reason", ""))[:100])
    console.print(table)
    console.print("[dim]Firma e responsabilità restano del professionista abilitato (BOZZA).[/dim]")
    console.print(f"[dim]Crediti addebitati: {report.credits_charged}[/dim]")
    _print_verdict(report.verdict)
    raise typer.Exit(0 if report.verdict == "PASS" else (2 if report.verdict == "CONCERNS" else 1))


@verifica_app.command("sicurezza")
def sicurezza_command(
    documento: Path = typer.Argument(..., help="Piano di sicurezza (PSC/POS, .pdf/.md/.txt)."),
    language: str = typer.Option(None, "--language", help="Lingua del report."),
) -> None:
    """Verifica adversarial di un PSC/POS (D.Lgs 81/2008 · 2 modelli · crediti)."""
    from lovarch_cli.verify import verify_sicurezza
    _run_adversarial_verify(verify_sicurezza, documento, "verifica sicurezza", language)


@verifica_app.command("accessibilita")
def accessibilita_command(
    documento: Path = typer.Argument(..., help="Progetto/relazione accessibilità (.pdf/.md/.txt)."),
    language: str = typer.Option(None, "--language", help="Lingua del report."),
) -> None:
    """Verifica adversarial accessibilità (L.13/89 · DM 236/89 · 2 modelli · crediti)."""
    from lovarch_cli.verify import verify_accessibilita
    _run_adversarial_verify(verify_accessibilita, documento, "verifica accessibilità", language)


@verifica_app.command("strutturale")
def strutturale_command(
    documento: Path = typer.Argument(..., help="Relazione/progetto strutturale (.pdf/.md/.txt)."),
    language: str = typer.Option(None, "--language", help="Lingua del report."),
) -> None:
    """Verifica adversarial strutturale (NTC 2018 · advisory · 2 modelli · crediti)."""
    from lovarch_cli.verify import verify_strutturale
    _run_adversarial_verify(verify_strutturale, documento, "verifica strutturale", language)


@verifica_app.command("antincendio")
def antincendio_command(
    documento: Path = typer.Argument(..., help="Progetto antincendio (.pdf/.md/.txt)."),
    language: str = typer.Option(None, "--language", help="Lingua del report."),
) -> None:
    """Verifica adversarial antincendio (DM 03/08/2015 · 2 modelli · crediti)."""
    from lovarch_cli.verify import verify_antincendio
    _run_adversarial_verify(verify_antincendio, documento, "verifica antincendio", language)


@verifica_app.command("acustica")
def acustica_command(
    documento: Path = typer.Argument(..., help="Relazione acustica (.pdf/.md/.txt)."),
    language: str = typer.Option(None, "--language", help="Lingua del report."),
) -> None:
    """Verifica adversarial acustica (DPCM 5/12/1997 · 2 modelli · crediti)."""
    from lovarch_cli.verify import verify_acustica
    _run_adversarial_verify(verify_acustica, documento, "verifica acustica", language)


@verifica_app.command("energetica")
def energetica_command(
    documento: Path = typer.Argument(..., help="Relazione energetica / L.10 (.pdf/.md/.txt)."),
    language: str = typer.Option(None, "--language", help="Lingua del report."),
) -> None:
    """Verifica adversarial energetica (D.Lgs 192/2005 · DM 26/06/2015 · crediti)."""
    from lovarch_cli.verify import verify_energetica
    _run_adversarial_verify(verify_energetica, documento, "verifica energetica", language)


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
        not_authenticated()
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


@verifica_app.command("contratto")
def contratto_command(
    documento: Path = typer.Argument(..., help="Contratto da verificare (.pdf, .md, .txt)."),
    language: str = typer.Option(None, "--language", help="Lingua del report."),
) -> None:
    """Verifica adversarial de contrato CNAPPC (estrutura + compenso · debita créditos)."""
    from lovarch_cli.ai import LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession
    from lovarch_cli.i18n import current_lang
    from lovarch_cli.verify import verify_contratto
    from lovarch_cli.verify.normativa import NormativaError

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)
    try:
        report = asyncio.run(verify_contratto(
            LovarchAiGateway(session), str(documento), language=language or current_lang(),
        ))
    except NormativaError as exc:
        err_console.print(f"[red]\u2717 {exc}[/red]")
        raise typer.Exit(1)

    st = report.structure or {}
    if st.get("client_type"):
        compenso_amount = (st.get("compenso") or {}).get("amount") or "\u2014"
        console.print(f"[dim]Committente: {st['client_type']} \u00b7 Compenso: {compenso_amount}[/dim]")
    missing = st.get("sections_missing") or []
    if missing:
        console.print(f"  [yellow]\u00b7[/yellow] Sezioni mancanti: {', '.join(str(m) for m in missing[:6])}")
    for f in report.findings:
        sev = str(f.get("severity", "info")).lower()
        icon = {"critical": "[red]\u2717[/red]", "concern": "[yellow]?[/yellow]"}.get(sev, "[dim]\u00b7[/dim]")
        console.print(f"  {icon} [{f.get('area', '?')}] {str(f.get('reason', ''))[:110]}")
    console.print(f"[dim]Crediti addebitati: {report.credits_charged}[/dim]")
    _print_verdict(report.verdict)
    raise typer.Exit(0 if report.verdict == "PASS" else (2 if report.verdict == "CONCERNS" else 1))


@verifica_app.command("dossier")
def dossier_command(
    cartella: Path = typer.Argument(..., help="Cartella dei deliverable da verificare."),
    language: str = typer.Option(None, "--language", help="Lingua del report."),
    max_llm: int = typer.Option(8, "--max-llm", help="Massimo documenti verificati con AI (i DXF sono gratis)."),
) -> None:
    """QA completo standalone su una cartella (DXF gratis + documenti adversarial)."""
    from lovarch_cli.ai import LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession
    from lovarch_cli.i18n import current_lang
    from lovarch_cli.verify import verify_dossier
    from lovarch_cli.verify.normativa import NormativaError

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)
    try:
        report = asyncio.run(verify_dossier(
            LovarchAiGateway(session), cartella,
            language=language or current_lang(), max_llm_files=max_llm,
        ))
    except NormativaError as exc:
        err_console.print(f"[red]\u2717 {exc}[/red]")
        raise typer.Exit(1)

    table = Table(title=f"verifica dossier \u2014 {cartella.name}", header_style="bold gold1")
    table.add_column("File", style="cyan")
    table.add_column("Tipo")
    table.add_column("Verdetto", justify="center")
    table.add_column("Dettaglio")
    for f in report.files:
        style = _VERDICT_STYLE.get(f["verdict"], "white")
        table.add_row(f["name"], f["kind"], f"[{style}]{f['verdict']}[/{style}]", str(f["detail"])[:70])
    console.print(table)
    if report.skipped:
        console.print(f"  [yellow]\u00b7[/yellow] non verificati con AI (limite --max-llm): {', '.join(report.skipped)}")
    console.print(f"[dim]Crediti addebitati: {report.credits_charged}[/dim]")
    _print_verdict(report.verdict)
    raise typer.Exit(0 if report.verdict == "PASS" else (2 if report.verdict == "CONCERNS" else 1))
