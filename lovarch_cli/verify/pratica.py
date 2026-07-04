"""verifica pratica — adversarial check of a building permit filing (CILA/SCIA).

Same two-model pattern as contratto/normativa: Sonnet 5 (executor) extracts the
filing's structure and declared data, Opus 4.8 (verifier) adversarially checks
completeness and coherence against the required elements of a CILA (Comunicazione
Inizio Lavori Asseverata) or SCIA (Segnalazione Certificata di Inizio Attività):
identificativi catastali, titolo di legittimità, asseverazione del tecnico,
elaborati allegati, e coerenza dell'intervento col titolo scelto (una CILA non
copre interventi che richiedono SCIA/permesso di costruire).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from lovarch_cli.verify.normativa import NormativaError, _parse_json, extract_text

# Required elements per filing type (used to prompt the verifier, not as a
# rigid checklist — the LLM judges presence/coherence adversarially).
CILA_REQUIRED = [
    "dati anagrafici del committente", "identificativi catastali (foglio/mappale/sub)",
    "titolo di legittimità dell'immobile", "descrizione dell'intervento",
    "asseverazione del tecnico abilitato", "elaborati grafici allegati",
    "dichiarazione di conformità urbanistica",
]
SCIA_REQUIRED = CILA_REQUIRED + [
    "relazione tecnica di asseverazione", "eventuali pareri/nulla osta (paesaggistico, ecc.)",
]

_EXTRACT_SYSTEM = (
    "Sei un assistente per pratiche edilizie italiane (CILA/SCIA). Estrai dalla "
    "pratica la struttura e i dati dichiarati. Rispondi SOLO con JSON valido: "
    '{"tipo": "CILA|SCIA|sconosciuto", "sezioni_presenti": ["..."], '
    '"sezioni_mancanti": ["..."], "identificativi_catastali": "... o null", '
    '"titolo_legittimita": "... o null", "asseverazione_presente": true|false, '
    '"intervento": "descrizione sintetica", "note": ["..."]}'
)

_REFUTE_SYSTEM = (
    "Sei un verificatore ADVERSARIALE di pratiche edilizie (CILA/SCIA). "
    "Controlla: (1) completezza degli elementi obbligatori per il tipo dichiarato; "
    "(2) presenza di identificativi catastali e titolo di legittimità; "
    "(3) presenza dell'asseverazione del tecnico abilitato; (4) COERENZA tra "
    "l'intervento descritto e il titolo scelto — una CILA NON copre interventi "
    "strutturali o che incidono su prospetti/volumi (quelli richiedono SCIA o "
    "permesso di costruire); segnala il possibile sottodimensionamento del titolo. "
    "Nel dubbio sii scettico. La firma e la responsabilità restano del tecnico "
    "abilitato. Rispondi SOLO con JSON valido: "
    '{"findings": [{"area": "...", "severity": "critical" | "concern" | "info", '
    '"reason": "..."}], "overall": "PASS" | "CONCERNS" | "REJECT"}'
)


@dataclass
class PraticaReport:
    verdict: str
    tipo: str = "sconosciuto"
    structure: dict = field(default_factory=dict)
    findings: list[dict] = field(default_factory=list)
    credits_charged: int = 0


async def verify_pratica(
    gateway: Any,
    document_path: str,
    *,
    tipo: str | None = None,
    language: str = "it",
    max_chars: int = 60_000,
) -> PraticaReport:
    """Adversarial CILA/SCIA filing check. Debits credits (2 calls)."""
    text = extract_text(document_path)
    if not text.strip():
        raise NormativaError("documento vuoto o testo non estraibile.")
    if len(text) > max_chars:
        text = text[:max_chars]

    credits = 0
    hint = f" (tipo dichiarato dall'utente: {tipo.upper()})" if tipo else ""
    extraction = await gateway.generate_text(
        f"PRATICA EDILIZIA{hint}:\n\n{text}",
        role="executor",
        system=_EXTRACT_SYSTEM,
        max_tokens=1500,
        language=language,
        operation_type="verify:pratica:extract",
    )
    credits += extraction.credits_charged
    structure = _parse_json(extraction.text)

    resolved_tipo = (tipo or str(structure.get("tipo") or "sconosciuto")).upper()
    required = SCIA_REQUIRED if resolved_tipo == "SCIA" else CILA_REQUIRED

    refutation = await gateway.generate_text(
        "STRUTTURA ESTRATTA DALLA PRATICA:\n\n"
        + json.dumps(structure, ensure_ascii=False)
        + f"\n\nTipo: {resolved_tipo}. Elementi obbligatori attesi: "
        + ", ".join(required),
        role="verifier",
        system=_REFUTE_SYSTEM,
        max_tokens=2000,
        language=language,
        operation_type="verify:pratica:refute",
    )
    credits += refutation.credits_charged
    judged = _parse_json(refutation.text)
    findings = judged.get("findings") or []

    overall = str(judged.get("overall", "")).upper()
    if overall not in ("PASS", "CONCERNS", "REJECT"):
        severities = [str(f.get("severity", "")).lower() for f in findings]
        overall = ("REJECT" if "critical" in severities
                   else ("CONCERNS" if "concern" in severities else "PASS"))

    return PraticaReport(
        verdict=overall,
        tipo=resolved_tipo,
        structure=structure,
        findings=findings,
        credits_charged=credits,
    )
