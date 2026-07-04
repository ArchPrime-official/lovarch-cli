"""verifica dati-modello — deterministic cross-check of a computo metrico
against the REAL quantities extracted from a CAD/BIM model (aps-cad-data).

No LLM, no credits. It flags area-based voci whose declared quantity is
impossible given the model's surface (e.g. more flooring than the whole
apartment), and reports the declared vs modelled total surface. Catches
inflated/typo quantities that a prezzario check alone can't.

Input: computo CSV/JSON (codice,descrizione,quantita,prezzo_unitario[,unita])
+ cad_id (the model whose extracted_data is the ground truth).
"""
from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lovarch_cli.ai import AiGatewayError, LovarchAiGateway

# A declared area this far above the model's total surface is impossible.
SURFACE_TOLERANCE = 1.20
# Voci whose unit/description implies an area quantity (m²).
AREA_HINTS = ("paviment", "rivestiment", "intonac", "tinteggiat", "massett",
              "controsoffitt", "isolament", "mq", "m²", "m2")


class DatiModelloError(Exception):
    pass


@dataclass
class DatiModelloReport:
    verdict: str                       # PASS | CONCERNS | REJECT
    findings: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def _parse_computo(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if not isinstance(data, list):
            raise DatiModelloError("il JSON del computo deve essere una lista di voci")
        return data
    return [dict(row) for row in csv.DictReader(io.StringIO(text))]


def _num(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", ".").replace("€", "").strip())
    except ValueError:
        return None


def _is_area_voce(row: dict) -> bool:
    blob = " ".join(str(row.get(k, "")) for k in ("descrizione", "unita", "um")).lower()
    return any(h in blob for h in AREA_HINTS)


async def verify_dati_modello(
    gateway: LovarchAiGateway, computo_path: str, cad_id: str,
) -> DatiModelloReport:
    """Compare a computo's area quantities against the model's real surface."""
    voci = _parse_computo(Path(computo_path))

    try:
        resp = await gateway.data("model_data", cad_id=cad_id)
    except AiGatewayError as exc:
        raise DatiModelloError(f"dati del modello non disponibili: {exc}") from exc
    model = (resp or {}).get("data") if isinstance(resp, dict) else None
    if not isinstance(model, dict):
        raise DatiModelloError("il modello non ha dati estratti (usa 'Dati modello' prima).")

    surface = model.get("superficie_totale_mq")
    findings: list[str] = []

    if not surface:
        findings.append("Il modello non riporta una superficie totale: "
                        "verifica le quantità manualmente.")
    else:
        limit = surface * SURFACE_TOLERANCE
        declared_area = 0.0
        for row in voci:
            q = _num(row.get("quantita") or row.get("quantità"))
            if q is None or not _is_area_voce(row):
                continue
            declared_area += q
            desc = str(row.get("descrizione") or row.get("codice") or "voce")
            if q > limit:
                findings.append(
                    f"'{desc}': {q} mq dichiarati > superficie del modello "
                    f"({surface} mq) — quantità impossibile, verifica.")
        if declared_area and declared_area > surface * 3:
            findings.append(
                f"Superficie a base d'area totale dichiarata ({round(declared_area, 1)} "
                f"mq) molto oltre la superficie del modello ({surface} mq): "
                "controlla ripetizioni o unità sbagliate.")

    verdict = "REJECT" if any("impossibile" in f for f in findings) \
        else ("CONCERNS" if findings else "PASS")
    return DatiModelloReport(
        verdict=verdict,
        findings=findings,
        stats={
            "superficie_modello_mq": surface,
            "ambienti_modello": model.get("contagem_ambienti"),
            "voci_computo": len(voci),
        },
    )
