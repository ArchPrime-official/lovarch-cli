"""verifica dossier — run the full standalone QA over a deliverables folder.

Composes the individual verifiers by file type:
  *.dxf                → misure (deterministic, free)
  contratto*.{pdf,md}  → contratto (adversarial, credits)
  other *.{pdf,md,txt} → normativa (adversarial, credits)

Verdict aggregation mirrors the squad's Tier-2 rule: any REJECT → REJECT;
any CONCERNS → CONCERNS; else PASS.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lovarch_cli.verify.contratto import verify_contratto
from lovarch_cli.verify.misure import verify_misure
from lovarch_cli.verify.normativa import NormativaError, verify_normativa

_TEXT_SUFFIXES = {".pdf", ".md", ".txt"}


@dataclass
class DossierReport:
    verdict: str
    files: list[dict] = field(default_factory=list)   # per-file {name, kind, verdict, detail}
    credits_charged: int = 0
    skipped: list[str] = field(default_factory=list)


async def verify_dossier(
    gateway: Any,
    directory: str | Path,
    *,
    language: str = "it",
    max_llm_files: int = 8,
) -> DossierReport:
    """Verify every recognized deliverable in a folder.

    ``max_llm_files`` caps how many documents go through the paid adversarial
    checks in one run (DXF checks are free and uncapped) — the cap and any
    skipped files are reported explicitly, never silently.
    """
    root = Path(directory).expanduser()
    if not root.is_dir():
        raise NormativaError(f"cartella non trovata: {root}")

    files: list[dict] = []
    skipped: list[str] = []
    credits = 0
    llm_used = 0

    entries = sorted(p for p in root.rglob("*") if p.is_file())
    for path in entries:
        suffix = path.suffix.lower()
        rel = str(path.relative_to(root))
        if suffix == ".dxf":
            report = verify_misure(path)
            files.append({
                "name": rel, "kind": "misure", "verdict": report.verdict,
                "detail": "; ".join(report.findings) or "ok",
            })
        elif suffix in _TEXT_SUFFIXES:
            if llm_used >= max_llm_files:
                skipped.append(rel)
                continue
            llm_used += 1
            is_contract = "contratto" in path.name.lower() or "contract" in path.name.lower()
            try:
                if is_contract:
                    rep = await verify_contratto(gateway, str(path), language=language)
                    detail = "; ".join(
                        f"[{f.get('severity')}] {f.get('area')}" for f in rep.findings[:4]
                    ) or "ok"
                else:
                    rep = await verify_normativa(gateway, str(path), language=language)
                    detail = "; ".join(
                        f"{v.get('reference')}: {v.get('status')}" for v in rep.verdicts[:4]
                    ) or "; ".join(rep.notes) or "ok"
                credits += rep.credits_charged
                files.append({
                    "name": rel, "kind": "contratto" if is_contract else "normativa",
                    "verdict": rep.verdict, "detail": detail,
                })
            except NormativaError as exc:
                files.append({"name": rel, "kind": "errore", "verdict": "CONCERNS",
                              "detail": str(exc)[:120]})

    if not files:
        raise NormativaError("nessun file verificabile trovato (.dxf/.pdf/.md/.txt).")

    verdicts = [f["verdict"] for f in files]
    overall = ("REJECT" if "REJECT" in verdicts
               else ("CONCERNS" if "CONCERNS" in verdicts or skipped else "PASS"))
    return DossierReport(verdict=overall, files=files,
                         credits_charged=credits, skipped=skipped)
