"""verifica contratto — adversarial check of an architect's contract.

Same two-model pattern as normativa: Sonnet 5 (executor) extracts the
contract's structure, Opus 4.8 (verifier) adversarially checks it against the
CNAPPC standard (12 articles) and the compenso rules — including the QN_007
nuance: for a PRIVATE consumer client the DM 17/06/2016 parameters are
ORIENTATIVE (an unexplained gap is a CONCERN, never an illegality; L.49/2023
binds only strong counterparties such as PA/banks/large companies).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from lovarch_cli.verify.normativa import NormativaError, _parse_json, extract_text

CNAPPC_ARTICLES = [
    "oggetto dell'incarico", "prestazioni professionali", "compenso",
    "modalità di pagamento", "spese e oneri", "tempi di esecuzione",
    "recesso", "inadempimento", "proprietà intellettuale",
    "privacy/GDPR", "controversie/foro", "firma delle parti",
]

_EXTRACT_SYSTEM = (
    "Sei un assistente per contratti di prestazione professionale di "
    "architettura (standard CNAPPC). Estrai dal contratto la struttura: quali "
    "delle 12 sezioni tipiche sono presenti, il tipo di committente "
    "(privato consumatore | PA | impresa | banca/assicurazione), il compenso "
    "pattuito e come è giustificato. Rispondi SOLO con JSON valido: "
    '{"sections_present": ["..."], "sections_missing": ["..."], '
    '"client_type": "privato|pa|impresa|banca|sconosciuto", '
    '"compenso": {"amount": "...", "justification": "... o null"}, '
    '"notes": ["..."]}'
)

_REFUTE_SYSTEM = (
    "Sei un verificatore ADVERSARIALE di contratti CNAPPC. Controlla: "
    "(1) completezza delle 12 sezioni tipiche; (2) coerenza del compenso. "
    "REGOLA COMPENSO (QN_007): per un committente PRIVATO CONSUMATORE i "
    "parametri DM 17/06/2016 sono ORIENTATIVI — uno scostamento non motivato è "
    "un CONCERN (mai una violazione di legge, la L.49/2023 vincola solo "
    "contraenti forti: PA, banche, assicurazioni, grandi imprese); per un "
    "contraente FORTE lo scostamento sotto i parametri è invece violazione. "
    "Rispondi SOLO con JSON valido: "
    '{"findings": [{"area": "...", "severity": "critical" | "concern" | "info", '
    '"reason": "..."}], "overall": "PASS" | "CONCERNS" | "REJECT"}'
)


@dataclass
class ContrattoReport:
    verdict: str
    structure: dict = field(default_factory=dict)
    findings: list[dict] = field(default_factory=list)
    credits_charged: int = 0


async def verify_contratto(
    gateway: Any,
    document_path: str,
    *,
    language: str = "it",
    max_chars: int = 60_000,
) -> ContrattoReport:
    """Adversarial CNAPPC contract check. Debits credits (2 calls)."""
    text = extract_text(document_path)
    if not text.strip():
        raise NormativaError("documento vuoto o testo non estraibile.")
    if len(text) > max_chars:
        text = text[:max_chars]

    credits = 0
    extraction = await gateway.generate_text(
        f"CONTRATTO:\n\n{text}",
        role="executor",
        system=_EXTRACT_SYSTEM,
        max_tokens=1500,
        language=language,
        operation_type="verify:contratto:extract",
    )
    credits += extraction.credits_charged
    structure = _parse_json(extraction.text)

    refutation = await gateway.generate_text(
        "STRUTTURA ESTRATTA DAL CONTRATTO:\n\n"
        + json.dumps(structure, ensure_ascii=False)
        + "\n\nSezioni CNAPPC attese: " + ", ".join(CNAPPC_ARTICLES),
        role="verifier",
        system=_REFUTE_SYSTEM,
        max_tokens=2000,
        language=language,
        operation_type="verify:contratto:refute",
    )
    credits += refutation.credits_charged
    judged = _parse_json(refutation.text)
    findings = judged.get("findings") or []

    overall = str(judged.get("overall", "")).upper()
    if overall not in ("PASS", "CONCERNS", "REJECT"):
        severities = [str(f.get("severity", "")).lower() for f in findings]
        overall = ("REJECT" if "critical" in severities
                   else ("CONCERNS" if "concern" in severities else "PASS"))

    return ContrattoReport(
        verdict=overall,
        structure=structure,
        findings=findings,
        credits_charged=credits,
    )
