"""verifica accessibilità — adversarial check of accessibility compliance
(L.13/1989 + DM 236/1989, and DPR 503/1996 for public buildings).

Two-model pattern (Sonnet extract → Opus refute). Flags where a project's
described dimensions/solutions fail the three levels — accessibilità,
visitabilità, adattabilità — and the mandatory prescriptive parameters (porte,
corridoi, rampe, servizi igienici, dislivelli). ADVISORY: the sworn accessibility
declaration (relazione L.13) is signed by the tecnico abilitato (BOZZA).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from lovarch_cli.verify.normativa import NormativaError, _parse_json, extract_text

# Prescriptive parameters DM 236/89 (used to prompt the verifier).
DM236_PARAMS = [
    "porte: luce netta ≥ 0,80 m (≥ 0,90 m ingresso principale)",
    "corridoi/percorsi: larghezza ≥ 1,00 m con allargamenti/rotazione Ø 1,50 m",
    "rampe: pendenza ≤ 8% (deroghe fino 12% per brevi tratti), pianerottoli",
    "servizio igienico accessibile: spazio rotazione Ø 1,50 m, maniglioni",
    "dislivelli/soglie: ≤ 2,5 cm; ascensore dove necessario (DM 236 §8.1.13)",
    "livelli: accessibilità | visitabilità | adattabilità secondo destinazione",
]

_EXTRACT_SYSTEM = (
    "Sei un assistente per la conformità all'accessibilità (L.13/1989, DM "
    "236/1989, DPR 503/1996). Estrai dal documento: livello richiesto "
    "(accessibilità | visitabilità | adattabilità), destinazione d'uso, e i "
    "parametri dimensionali dichiarati (porte, corridoi, rampe, servizi, "
    "dislivelli, ascensore). Rispondi SOLO con JSON valido: "
    '{"livello": "accessibilità|visitabilità|adattabilità|sconosciuto", '
    '"destinazione": "...", "parametri": {"porte_cm": "...|null", '
    '"corridoi_cm": "...|null", "rampe_pendenza": "...|null", '
    '"servizio_accessibile": true|false|null, "ascensore": true|false|null}, '
    '"note": ["..."]}'
)

_REFUTE_SYSTEM = (
    "Sei un verificatore ADVERSARIALE di accessibilità (DM 236/1989). Controlla "
    "i parametri dichiarati contro i minimi prescrittivi: porte luce netta ≥ 0,80 "
    "m; percorsi ≥ 1,00 m con rotazione Ø 1,50 m; rampe pendenza ≤ 8%; servizio "
    "igienico con rotazione Ø 1,50 m; dislivelli ≤ 2,5 cm; ascensore dove dovuto. "
    "Verifica anche che il LIVELLO dichiarato sia adeguato alla destinazione d'uso "
    "(es.: pubblico esercizio → visitabilità obbligatoria; residenza → "
    "adattabilità minima). Nel dubbio sii scettico. La relazione L.13 è firmata "
    "dal tecnico abilitato. Rispondi SOLO con JSON valido: {\"findings\": "
    '[{"area": "...", "severity": "critical" | "concern" | "info", "reason": '
    '"..."}], "overall": "PASS" | "CONCERNS" | "REJECT"}'
)


@dataclass
class AccessibilitaReport:
    verdict: str
    livello: str = "sconosciuto"
    structure: dict = field(default_factory=dict)
    findings: list[dict] = field(default_factory=list)
    credits_charged: int = 0


async def verify_accessibilita(
    gateway: Any,
    document_path: str,
    *,
    language: str = "it",
    max_chars: int = 60_000,
) -> AccessibilitaReport:
    """Adversarial accessibility check (L.13/89 · DM 236/89). Debits credits."""
    text = extract_text(document_path)
    if not text.strip():
        raise NormativaError("documento vuoto o testo non estraibile.")
    if len(text) > max_chars:
        text = text[:max_chars]

    credits = 0
    extraction = await gateway.generate_text(
        f"DOCUMENTO (progetto/relazione accessibilità):\n\n{text}",
        role="executor", system=_EXTRACT_SYSTEM, max_tokens=1500,
        language=language, operation_type="verify:accessibilita:extract",
    )
    credits += extraction.credits_charged
    structure = _parse_json(extraction.text)
    livello = str(structure.get("livello") or "sconosciuto")

    refutation = await gateway.generate_text(
        "STRUTTURA ESTRATTA:\n\n" + json.dumps(structure, ensure_ascii=False)
        + "\n\nParametri prescrittivi DM 236/89: " + ", ".join(DM236_PARAMS),
        role="verifier", system=_REFUTE_SYSTEM, max_tokens=2000,
        language=language, operation_type="verify:accessibilita:refute",
    )
    credits += refutation.credits_charged
    judged = _parse_json(refutation.text)
    findings = judged.get("findings") or []

    overall = str(judged.get("overall", "")).upper()
    if overall not in ("PASS", "CONCERNS", "REJECT"):
        severities = [str(f.get("severity", "")).lower() for f in findings]
        overall = ("REJECT" if "critical" in severities
                   else ("CONCERNS" if "concern" in severities else "PASS"))

    return AccessibilitaReport(
        verdict=overall, livello=livello, structure=structure,
        findings=findings, credits_charged=credits,
    )
