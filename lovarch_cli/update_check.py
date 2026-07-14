"""Avviso non invasivo quando esiste una versione più nuova del CLI.

Il CLI non aveva NESSUN meccanismo di update-check: chi installava una volta
restava fermo per sempre (un utente è rimasto su una versione col login rotto
finché non ha chiesto aiuto). Con la cadenza di release reale, "aggiorna quando
te ne accorgi" non funziona.

Principi:
  - best-effort: qualsiasi errore (rete, rate limit, JSON strano) = silenzio;
  - 1 sola richiesta ogni 24h (cache in ~/.lovarch/.update-check);
  - timeout corto: non deve rallentare un comando;
  - opt-out: LOVARCH_NO_UPDATE_CHECK=1.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

from .version import __version__

RELEASES_API = "https://api.github.com/repos/ArchPrime-official/lovarch-cli/releases/latest"
CACHE_FILE = Path.home() / ".lovarch" / ".update-check"
CACHE_TTL_S = 24 * 60 * 60
TIMEOUT_S = 2.0


def _parse(v: str) -> tuple[int, ...]:
    """'v0.5.1' -> (0, 5, 1). Parti non numeriche (rc, beta) → ignorate."""
    core = v.lstrip("vV").split("-")[0].split("+")[0]
    out: list[int] = []
    for part in core.split("."):
        try:
            out.append(int(part))
        except ValueError:
            break
    return tuple(out) or (0,)


def _cached_latest() -> str | None:
    try:
        data = json.loads(CACHE_FILE.read_text())
        if time.time() - float(data["checked_at"]) < CACHE_TTL_S:
            return str(data.get("latest") or "")
    except Exception:
        pass
    return None


def _store(latest: str) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({"checked_at": time.time(), "latest": latest}))
    except Exception:
        pass


def latest_version() -> str | None:
    """Ultima release pubblicata, o None se non determinabile (silenzioso)."""
    cached = _cached_latest()
    if cached is not None:
        return cached or None
    try:
        req = urllib.request.Request(
            RELEASES_API,
            headers={"Accept": "application/vnd.github+json", "User-Agent": f"lovarch-cli/{__version__}"},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            tag = str(json.load(resp).get("tag_name") or "")
        _store(tag)
        return tag or None
    except Exception:
        _store("")  # non riprovare per 24h anche in caso di errore
        return None


def check_for_update() -> str | None:
    """Ritorna il messaggio di upgrade se c'è una versione più nuova, altrimenti None."""
    if os.environ.get("LOVARCH_NO_UPDATE_CHECK") == "1":
        return None
    latest = latest_version()
    if not latest:
        return None
    if _parse(latest) <= _parse(__version__):
        return None
    return (
        f"Nuova versione disponibile: {latest} (hai {__version__}). "
        "Aggiorna con [bold]brew upgrade lovarch-cli[/bold] o "
        "[bold]pipx upgrade lovarch-cli[/bold]."
    )
