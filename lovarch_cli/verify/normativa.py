"""verifica normativa — adversarial two-model check of normative citations.

Pipeline:
  0. Extract document text (pypdf for .pdf; plain read for .md/.txt).
  1. Deterministic pre-pass: regex of canonical Italian building references
     (same table the squad's Q2 verifier uses) — free.
  2. EXTRACT (Sonnet 5 · executor): list every normative citation with its
     claimed subject, as strict JSON.
  3. REFUTE (Opus 4.8 · verifier): adversarially challenge each citation —
     does the article exist? does it regulate what the document claims?
     Defaults to skeptical; returns per-citation verdicts as strict JSON.
  4. Merge: any refuted citation → REJECT; doubts → CONCERNS.

Credits: debited per real tokens via cli-ai-text (executor + verifier calls).
Report language follows the user's configured language.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CANONICAL_REFS: dict[str, list[str]] = {
    "DPR 380/2001": [r"dpr\s*380", r"d\.p\.r\.\s*380", r"testo unico edilizia"],
    "UNI 11337": [r"uni\s*11337"],
    "CAM 2025": [r"cam\s*edilizia", r"dm\s*23/06/2022", r"criteri ambientali"],
    "NTC 2018": [r"ntc\s*2018", r"dm\s*17/01/2018"],
    "D.Lgs 81/2008": [r"d\.?lgs\.?\s*81"],
    "D.Lgs 42/2004": [r"d\.?lgs\.?\s*42", r"codice beni culturali"],
    "L. 49/2023": [r"49/2023", r"equo compenso"],
    "GDPR": [r"gdpr", r"2016/679"],
}

_EXTRACT_SYSTEM = (
    "Sei un assistente tecnico-normativo per l'edilizia italiana. Estrai dal "
    "documento OGNI citazione normativa (leggi, decreti, norme UNI, articoli) "
    "insieme a ciò che il documento AFFERMA che quella norma regoli. Rispondi "
    "SOLO con JSON valido, nessun altro testo: "
    '{"citations": [{"reference": "...", "article": "... o null", '
    '"claim": "cosa il documento afferma che questa norma regola"}]}'
)

_REFUTE_SYSTEM = (
    "Sei un verificatore normativo ADVERSARIALE per l'edilizia italiana. Per "
    "ogni citazione, cerca attivamente di CONFUTARLA: l'articolo esiste? La "
    "norma regola davvero ciò che viene affermato? Nel dubbio, sii scettico e "
    "segnala. Esempi noti: DPR 380/2001 art. 99 riguarda il conglomerato "
    "cementizio armato (NON le CILA); la L.49/2023 (equo compenso) vincola solo "
    "verso contraenti forti (PA/banche/grandi imprese), NON i clienti privati. "
    "Rispondi SOLO con JSON valido: "
    '{"verdicts": [{"reference": "...", "status": "ok" | "refuted" | "doubt", '
    '"reason": "spiegazione breve"}]}'
)


@dataclass
class NormativaReport:
    verdict: str                        # PASS | CONCERNS | REJECT
    citations: list[dict] = field(default_factory=list)
    verdicts: list[dict] = field(default_factory=list)
    canonical_found: list[str] = field(default_factory=list)
    credits_charged: int = 0
    notes: list[str] = field(default_factory=list)


class NormativaError(Exception):
    pass


def extract_text(path: str | Path) -> str:
    """Read document text — pypdf for PDFs, plain read otherwise."""
    p = Path(path).expanduser()
    if not p.is_file():
        raise NormativaError(f"file non trovato: {p}")
    if p.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise NormativaError(
                "pypdf non installato — necessario per i PDF (pip install pypdf)."
            ) from exc
        try:
            reader = PdfReader(str(p))
            return " ".join((page.extract_text() or "") for page in reader.pages)
        except Exception as exc:  # noqa: BLE001
            raise NormativaError(f"PDF non leggibile: {str(exc)[:120]}") from exc
    return p.read_text(encoding="utf-8", errors="ignore")


def scan_canonical(text: str) -> list[str]:
    """Deterministic pre-pass: which canonical references appear in the text."""
    low = text.lower()
    return [name for name, patterns in CANONICAL_REFS.items()
            if any(re.search(pat, low) for pat in patterns)]


def _parse_json(raw: str) -> dict:
    """Robust JSON extraction from an LLM answer (tolerates fences/preamble)."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.S)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    raise NormativaError("il modello non ha restituito JSON valido.")


async def verify_normativa(
    gateway: Any,
    document_path: str | Path,
    *,
    language: str = "it",
    max_chars: int = 60_000,
) -> NormativaReport:
    """Adversarial normative check of one document. Debits credits (2 calls)."""
    text = extract_text(document_path)
    if not text.strip():
        raise NormativaError("documento vuoto o testo non estraibile.")
    if len(text) > max_chars:
        text = text[:max_chars]

    canonical = scan_canonical(text)
    credits = 0

    # 1 · EXTRACT (executor → Sonnet 5)
    extraction = await gateway.generate_text(
        f"DOCUMENTO:\n\n{text}",
        role="executor",
        system=_EXTRACT_SYSTEM,
        max_tokens=2000,
        language=language,
        operation_type="verify:normativa:extract",
    )
    credits += extraction.credits_charged
    citations = _parse_json(extraction.text).get("citations") or []
    if not citations:
        return NormativaReport(
            verdict="CONCERNS",
            canonical_found=canonical,
            credits_charged=credits,
            notes=["nessuna citazione normativa trovata nel documento"],
        )

    # 2 · REFUTE (verifier → Opus 4.8) — independent adversarial pass
    refutation = await gateway.generate_text(
        "CITAZIONI DA CONFUTARE:\n\n" + json.dumps(citations, ensure_ascii=False),
        role="verifier",
        system=_REFUTE_SYSTEM,
        max_tokens=2500,
        language=language,
        operation_type="verify:normativa:refute",
    )
    credits += refutation.credits_charged
    verdicts = _parse_json(refutation.text).get("verdicts") or []

    statuses = [str(v.get("status", "doubt")).lower() for v in verdicts]
    if any(s == "refuted" for s in statuses):
        overall = "REJECT"
    elif any(s == "doubt" for s in statuses) or not verdicts:
        overall = "CONCERNS"
    else:
        overall = "PASS"

    return NormativaReport(
        verdict=overall,
        citations=citations,
        verdicts=verdicts,
        canonical_found=canonical,
        credits_charged=credits,
    )
