"""verifica sicurezza — adversarial check of a construction-site safety plan
(PSC — Piano di Sicurezza e Coordinamento, or POS) against D.Lgs 81/2008.

Same two-model pattern as pratica/contratto (Sonnet extract → Opus refute). This
is an ADVISORY pre-check for the impresa / direttore lavori / CSE — it flags
missing mandatory elements and coherence gaps. It NEVER replaces the sworn plan:
the CSP/CSE (coordinatore abilitato) signs and is responsible (BOZZA).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from lovarch_cli.verify.normativa import NormativaError, _parse_json, extract_text

# Mandatory PSC elements per D.Lgs 81/2008 Allegato XV (used to prompt the
# verifier, not as a rigid checklist — the LLM judges presence/coherence).
PSC_REQUIRED = [
    "identificazione soggetti (committente, RL, CSP, CSE, imprese)",
    "descrizione dell'opera e area di cantiere",
    "analisi dei rischi per fase lavorativa",
    "misure preventive e DPI per rischio",
    "cronoprogramma dei lavori con sovrapposizioni",
    "coordinamento imprese e lavoratori autonomi",
    "costi della sicurezza (non soggetti a ribasso)",
    "notifica preliminare (art. 99) se prevista",
    "gestione emergenze e primo soccorso",
]

_EXTRACT_SYSTEM = (
    "Sei un assistente per piani di sicurezza di cantiere italiani (PSC/POS, "
    "D.Lgs 81/2008 Allegato XV). Estrai la struttura del documento: quali "
    "elementi obbligatori sono presenti, il tipo (PSC | POS | PSS | sconosciuto), "
    "i soggetti individuati (committente/RL/CSP/CSE/imprese), se ci sono analisi "
    "rischi per fase e i costi della sicurezza. Rispondi SOLO con JSON valido: "
    '{"tipo": "PSC|POS|PSS|sconosciuto", "elementi_presenti": ["..."], '
    '"elementi_mancanti": ["..."], "soggetti": {"CSP": "...|null", "CSE": '
    '"...|null", "imprese": ["..."]}, "rischi_per_fase": true|false, '
    '"costi_sicurezza": "...|null", "note": ["..."]}'
)

_REFUTE_SYSTEM = (
    "Sei un verificatore ADVERSARIALE di piani di sicurezza (D.Lgs 81/2008). "
    "Controlla: (1) completezza degli elementi obbligatori dell'Allegato XV per "
    "il tipo dichiarato; (2) presenza e nomina di CSP/CSE dove obbligatori "
    "(cantieri con più imprese); (3) analisi rischi PER FASE (non generica); "
    "(4) costi della sicurezza esplicitati e non soggetti a ribasso; (5) notifica "
    "preliminare art. 99 se dovuta. Nel dubbio sii scettico. La firma e la "
    "responsabilità restano del coordinatore abilitato (CSP/CSE). Rispondi SOLO "
    "con JSON valido: {\"findings\": [{\"area\": \"...\", \"severity\": "
    '"critical" | "concern" | "info", "reason": "..."}], "overall": "PASS" | '
    '"CONCERNS" | "REJECT"}'
)


@dataclass
class SicurezzaReport:
    verdict: str
    tipo: str = "sconosciuto"
    structure: dict = field(default_factory=dict)
    findings: list[dict] = field(default_factory=list)
    credits_charged: int = 0


async def verify_sicurezza(
    gateway: Any,
    document_path: str,
    *,
    language: str = "it",
    max_chars: int = 60_000,
) -> SicurezzaReport:
    """Adversarial PSC/POS safety-plan check. Debits credits (2 calls)."""
    text = extract_text(document_path)
    if not text.strip():
        raise NormativaError("documento vuoto o testo non estraibile.")
    if len(text) > max_chars:
        text = text[:max_chars]

    credits = 0
    extraction = await gateway.generate_text(
        f"PIANO DI SICUREZZA:\n\n{text}",
        role="executor", system=_EXTRACT_SYSTEM, max_tokens=1500,
        language=language, operation_type="verify:sicurezza:extract",
    )
    credits += extraction.credits_charged
    structure = _parse_json(extraction.text)
    resolved_tipo = str(structure.get("tipo") or "sconosciuto").upper()

    refutation = await gateway.generate_text(
        "STRUTTURA ESTRATTA DAL PIANO:\n\n"
        + json.dumps(structure, ensure_ascii=False)
        + "\n\nElementi obbligatori attesi (Allegato XV): " + ", ".join(PSC_REQUIRED),
        role="verifier", system=_REFUTE_SYSTEM, max_tokens=2000,
        language=language, operation_type="verify:sicurezza:refute",
    )
    credits += refutation.credits_charged
    judged = _parse_json(refutation.text)
    findings = judged.get("findings") or []

    overall = str(judged.get("overall", "")).upper()
    if overall not in ("PASS", "CONCERNS", "REJECT"):
        severities = [str(f.get("severity", "")).lower() for f in findings]
        overall = ("REJECT" if "critical" in severities
                   else ("CONCERNS" if "concern" in severities else "PASS"))

    return SicurezzaReport(
        verdict=overall, tipo=resolved_tipo, structure=structure,
        findings=findings, credits_charged=credits,
    )
