"""Shared engine for the adversarial verifiers (two-model: Sonnet extract → Opus
refute). Used by strutturale/antincendio/acustica/energetica so each verifier is
just a config (systems + required elements), not repeated orchestration.

Cost is always in credits; the signed document/responsibility stays with the
licensed professional (callers add the BOZZA banner in the CLI output).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from lovarch_cli.verify.normativa import NormativaError, _parse_json, extract_text


@dataclass
class AdversarialReport:
    verdict: str                       # PASS | CONCERNS | REJECT
    structure: dict = field(default_factory=dict)
    findings: list[dict] = field(default_factory=list)
    credits_charged: int = 0


async def run_adversarial(
    gateway: Any,
    document_path: str,
    *,
    extract_system: str,
    refute_system: str,
    required: list[str],
    op_prefix: str,
    doc_label: str = "DOCUMENTO",
    language: str = "it",
    max_chars: int = 60_000,
) -> AdversarialReport:
    """Extract structure (executor) → adversarially refute (verifier)."""
    text = extract_text(document_path)
    if not text.strip():
        raise NormativaError("documento vuoto o testo non estraibile.")
    if len(text) > max_chars:
        text = text[:max_chars]

    credits = 0
    extraction = await gateway.generate_text(
        f"{doc_label}:\n\n{text}",
        role="executor", system=extract_system, max_tokens=1500,
        language=language, operation_type=f"{op_prefix}:extract",
    )
    credits += extraction.credits_charged
    structure = _parse_json(extraction.text)

    refutation = await gateway.generate_text(
        "STRUTTURA ESTRATTA:\n\n" + json.dumps(structure, ensure_ascii=False)
        + "\n\nElementi/parametri attesi: " + ", ".join(required),
        role="verifier", system=refute_system, max_tokens=2000,
        language=language, operation_type=f"{op_prefix}:refute",
    )
    credits += refutation.credits_charged
    judged = _parse_json(refutation.text)
    findings = judged.get("findings") or []

    overall = str(judged.get("overall", "")).upper()
    if overall not in ("PASS", "CONCERNS", "REJECT"):
        severities = [str(f.get("severity", "")).lower() for f in findings]
        overall = ("REJECT" if "critical" in severities
                   else ("CONCERNS" if "concern" in severities else "PASS"))

    return AdversarialReport(
        verdict=overall, structure=structure, findings=findings, credits_charged=credits,
    )


_REFUTE_TAIL = (
    ' Nel dubbio sii scettico. La firma e la responsabilità restano del tecnico '
    'abilitato. Rispondi SOLO con JSON valido: {"findings": [{"area": "...", '
    '"severity": "critical" | "concern" | "info", "reason": "..."}], "overall": '
    '"PASS" | "CONCERNS" | "REJECT"}'
)
