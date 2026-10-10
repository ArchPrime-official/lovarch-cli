"""`lovarch api` — tutta la piattaforma dal terminale, la stessa del connettore MCP.

    lovarch api azioni
    lovarch api call progetta.list
    lovarch api call projects.ask project_id=… question="È in ritardo?"
    lovarch api call progetta.create message="bilocale 60 mq" --file files=pianta.pdf --wait
    lovarch api call render.create renderStyle=minimale aspectRatio=16:9 image_model=blackforestlabs/flux-3

Ogni operazione `modulo.azione` della api-v1 è raggiungibile qui: è la STESSA superficie
che Claude e ChatGPT usano via MCP (stessi gate, stessi crediti, stesso workspace).
`chiave=valore` prova a leggere il valore come JSON (numeri, true/false, liste, oggetti) e
altrimenti lo passa come testo. `--file campo=percorso` carica il file locale nel workspace
(URL firmato) e passa il riferimento nel campo indicato (sempre come lista).
"""
from __future__ import annotations

import asyncio
import json
import time

import typer
from rich.console import Console

from lovarch_cli.upsell import not_authenticated

console = Console()
err_console = Console(stderr=True)

api_app = typer.Typer(
    help="Qualsiasi operazione della piattaforma (api-v1) — la stessa del connettore MCP.",
    no_args_is_help=True,
)

TERMINAL = {"done", "completed", "succeeded", "failed", "error", "cancelled", "canceled", "refunded", "expired"}


def _gateway():
    from lovarch_cli.ai import LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)
    return LovarchAiGateway(session)


def parse_value(raw: str) -> object:
    """`true`→True, `12`→12, `[1,2]`→lista, `{"a":1}`→oggetto; il resto resta testo."""
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def parse_params(pairs: list[str], json_body: str | None) -> dict:
    params: dict = {}
    if json_body:
        loaded = json.loads(json_body)
        if not isinstance(loaded, dict):
            raise typer.BadParameter("--json deve essere un oggetto JSON")
        params.update(loaded)
    for pair in pairs:
        if "=" not in pair:
            raise typer.BadParameter(f"Parametro senza '=': {pair} (usa chiave=valore)")
        key, value = pair.split("=", 1)
        params[key.strip()] = parse_value(value)
    return params


def status_action(action: str) -> str:
    """Operazione di stato del modulo: `progetta.render` → `progetta.status`."""
    module = action.split(".", 1)[0]
    return f"{module}.status"


async def _wait(gw, action: str, result: dict, every: float, timeout: float) -> dict:
    job_id = result.get("job_id")
    if not job_id:
        return result
    params: dict = {"job_id": job_id}
    if result.get("engine"):
        params["engine"] = result["engine"]
    deadline = time.monotonic() + timeout
    last = result
    while time.monotonic() < deadline:
        await asyncio.sleep(every)
        last = await gw.api(status_action(action), params)
        status = str(last.get("status") or (last.get("job") or {}).get("status") or "").lower()
        err_console.print(f"[dim]… {status_action(action)} {job_id}: {status or '?'}[/dim]")
        if status in TERMINAL:
            return last
    return last


@api_app.command("azioni")
def actions_command() -> None:
    """Elenca le operazioni disponibili (`modulo.azione`)."""
    gw = _gateway()
    actions = asyncio.run(gw.api_actions())
    if not actions:
        err_console.print("[yellow]Nessuna operazione restituita dal server.[/yellow]")
        raise typer.Exit(1)
    for a in actions:
        console.print(a)


@api_app.command("call")
def call_command(
    action: str = typer.Argument(..., help="Operazione, es. progetta.list o projects.ask"),
    params: list[str] = typer.Argument(None, help="Parametri chiave=valore"),
    json_body: str = typer.Option(None, "--json", help="Parametri come oggetto JSON"),
    files: list[str] = typer.Option(None, "--file", help="campo=percorso — carica un file locale"),
    wait: bool = typer.Option(False, "--wait", help="Se torna un job_id, attende la fine"),
    every: float = typer.Option(5.0, "--ogni", help="Secondi tra un controllo e l'altro (--wait)"),
    timeout: float = typer.Option(1800.0, "--timeout", help="Attesa massima in secondi (--wait)"),
    raw: bool = typer.Option(False, "--raw", help="JSON compatto (per script)"),
) -> None:
    """Esegue un'operazione della piattaforma e stampa la risposta JSON."""
    from lovarch_cli.ai import AiGatewayError

    body = parse_params(params or [], json_body)
    gw = _gateway()

    async def run() -> dict:
        for spec in files or []:
            if "=" not in spec:
                raise typer.BadParameter(f"--file senza '=': {spec} (usa campo=percorso)")
            field, path = spec.split("=", 1)
            ref = await gw.upload_file(path, purpose=action.split(".", 1)[0])
            existing = body.get(field)
            body[field] = [*existing, ref] if isinstance(existing, list) else [ref]
        result = await gw.api(action, body)
        return await _wait(gw, action, result, every, timeout) if wait else result

    try:
        result = asyncio.run(run())
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)
    if raw:
        print(json.dumps(result, ensure_ascii=False))
    else:
        console.print_json(json.dumps(result, ensure_ascii=False))
