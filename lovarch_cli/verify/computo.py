"""verifica computo — deterministic check of a computo metrico against the
regional prezzario (table `prezzari`). No LLM, no credits: it compares each
voce's unit price and unit of measure to the official reference and flags
codes that don't exist, prices out of tolerance, and unit mismatches.

Input file: CSV (header: codice,descrizione,quantita,prezzo_unitario[,unita])
or JSON (list of {codice, quantita, prezzo_unitario, unita?}).
"""
from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# A unit price this far from the prezzario reference is flagged (±%).
PRICE_TOLERANCE = 0.20


class ComputoError(Exception):
    pass


@dataclass
class ComputoReport:
    verdict: str                       # PASS | CONCERNS | REJECT
    findings: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def _parse_computo(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if not isinstance(data, list):
            raise ComputoError("il JSON del computo deve essere una lista di voci")
        return data
    # CSV
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def _num(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", ".").replace("€", "").strip())
    except ValueError:
        return None


def _bundled_prezzario(region: str) -> list[dict]:
    """Offline fallback prezzario shipped with the CLI (free, no login).
    Only Lombardia is bundled; other regions need a premium session (live DB)."""
    if region.lower() != "lombardia":
        return []
    data_path = Path(__file__).resolve().parent.parent / "data" / "prezzario-lombardia.json"
    try:
        return json.loads(data_path.read_text(encoding="utf-8")).get("voci", [])
    except (OSError, json.JSONDecodeError):
        return []


async def verify_computo(
    session: Any,
    computo_path: str | Path,
    *,
    region: str = "Lombardia",
    version: str | None = None,
) -> ComputoReport:
    """Compare a computo file's voci against the prezzari reference for a region.

    With a session, reads the live `prezzari` table (all regions/versions). Without
    a session (free/offline), falls back to the bundled Lombardia prezzario."""
    path = Path(computo_path).expanduser()
    if not path.is_file():
        return ComputoReport(verdict="REJECT", findings=[f"file non trovato: {path}"])

    try:
        voci = _parse_computo(path)
    except Exception as exc:  # noqa: BLE001 — parse errors are the finding
        return ComputoReport(verdict="REJECT", findings=[f"computo non leggibile: {str(exc)[:150]}"])

    if not voci:
        return ComputoReport(verdict="REJECT", findings=["nessuna voce nel computo"])

    ref_rows: list[dict] = []
    used_bundled = False
    if session is not None:
        # Live prezzario (RLS: authenticated read) — all regions/versions.
        params = {"region": f"eq.{region}", "select": "codice,prezzo,unita,descrizione"}
        if version:
            params["version"] = f"eq.{version}"
        resp = await session.request("GET", "/rest/v1/prezzari", params=params)
        if resp.status_code != 200:
            raise ComputoError(f"prezzari non disponibili: HTTP {resp.status_code}")
        ref_rows = resp.json()
    if not ref_rows:
        # Free/offline fallback (or region missing in DB): bundled Lombardia.
        ref_rows = _bundled_prezzario(region)
        used_bundled = bool(ref_rows)

    ref = {r["codice"]: r for r in ref_rows if isinstance(r, dict) and r.get("codice")}
    if not ref:
        raise ComputoError(
            f"nessun prezzario per regione '{region}'"
            + (f" versione '{version}'" if version else "")
            + (" — accedi con `lovarch login --premium` per i prezzari live di altre regioni."
               if region.lower() != "lombardia" else ""))

    findings: list[str] = []
    unknown = 0
    out_of_range = 0
    unit_mismatch = 0
    total_computo = 0.0
    checked = 0

    for i, voce in enumerate(voci, 1):
        codice = str(voce.get("codice") or "").strip()
        if not codice:
            findings.append(f"voce {i}: codice mancante")
            continue
        qta = _num(voce.get("quantita") or voce.get("quantità"))
        prezzo = _num(voce.get("prezzo_unitario") or voce.get("prezzo"))
        unita = str(voce.get("unita") or voce.get("unità") or "").strip()

        if qta is not None and prezzo is not None:
            total_computo += qta * prezzo

        r = ref.get(codice)
        if not r:
            unknown += 1
            findings.append(f"voce {i} [{codice}]: codice non presente nel prezzario {region}")
            continue
        checked += 1

        ref_price = float(r["prezzo"])
        if prezzo is not None and ref_price > 0:
            delta = (prezzo - ref_price) / ref_price
            if abs(delta) > PRICE_TOLERANCE:
                out_of_range += 1
                findings.append(
                    f"voce {i} [{codice}]: prezzo {prezzo:.2f} vs riferimento "
                    f"{ref_price:.2f} ({delta:+.0%}) — fuori tolleranza ±{PRICE_TOLERANCE:.0%}"
                )
        if unita and r.get("unita") and unita.lower() != str(r["unita"]).lower():
            unit_mismatch += 1
            findings.append(
                f"voce {i} [{codice}]: unità '{unita}' ≠ prezzario '{r['unita']}'"
            )

    stats = {
        "voci_totali": len(voci),
        "voci_verificate": checked,
        "codici_sconosciuti": unknown,
        "prezzi_fuori_tolleranza": out_of_range,
        "unita_incoerenti": unit_mismatch,
        "totale_computo_eur": round(total_computo, 2),
        "prezzario": f"{region}"
        + (f" {version}" if version else "")
        + f" ({len(ref)} voci)"
        + (" · offline/gratis" if used_bundled else ""),
    }

    if unknown or out_of_range:
        verdict = "CONCERNS"
    else:
        verdict = "PASS"
    # A computo where nothing could be matched is not trustworthy.
    if checked == 0:
        verdict = "REJECT"
        findings.insert(0, "nessuna voce del computo trovata nel prezzario")

    return ComputoReport(verdict=verdict, findings=findings, stats=stats)
