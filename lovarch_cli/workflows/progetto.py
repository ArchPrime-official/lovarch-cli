"""Composed workflow `progetto interni` — chains the standalone agents into a
single phased run: interior-designer (concept) → optional render(s) → optional
preventivo → assembled mini-dossier (markdown).

This is what turns the F11 agents from standalone tools into a real workflow.
Everything is opt-in (the user chooses what to generate); text runs on the
platform text models (Sonnet/Opus by role) and renders debit image credits.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from lovarch_cli.agents import AGENTS, personalize_system, run_agent
from lovarch_cli.ai import AiGatewayError, LovarchAiGateway


@dataclass
class ProgettoInterniResult:
    dossier_md: str
    sections: dict = field(default_factory=dict)   # concept / preventivo
    renders: list[bytes] = field(default_factory=list)  # generated render image bytes
    credits_charged: int = 0
    warnings: list[str] = field(default_factory=list)


async def progetto_interni(
    gateway: LovarchAiGateway,
    brief: str,
    *,
    language: str = "it",
    want_render: bool = False,
    want_preventivo: bool = True,
    lead_id: str | None = None,
    render_count: int = 1,
    on_phase: Any = None,   # optional callback(phase_name) for progress UI
) -> ProgettoInterniResult:
    """Run the composed interior-design workflow. Each phase is opt-in."""
    def _phase(name: str) -> None:
        if callable(on_phase):
            on_phase(name)

    credits = 0
    sections: dict = {}
    renders: list[bytes] = []
    warnings: list[str] = []

    # Phase 1 — Concept (interior-designer, always).
    _phase("interior-designer")
    concept = await run_agent(
        gateway, "interior-designer", brief, language=language, lead_id=lead_id,
    )
    credits += concept.credits_charged
    sections["concept"] = concept.text

    # Phase 2 — Render(s) (opt-in; debits image credits).
    if want_render:
        _phase("render")
        # Derive a render prompt from the brief; keep it grounded in the concept.
        render_prompt = (
            f"Interior design render, fotorealistico. {brief}. "
            "Illuminazione naturale, materiali coerenti col concept, "
            "composizione elegante da presentazione."
        )
        for _ in range(max(1, render_count)):
            try:
                r = await gateway.generate_image(
                    render_prompt, quality="medium", aspect="16:9",
                    operation_type="progetto-interni:render",
                )
                credits += r.credits_charged
                if r.image_bytes:
                    renders.append(r.image_bytes)
            except AiGatewayError as exc:
                warnings.append(f"render non riuscito: {exc}")
                break

    # Phase 3 — Preventivo (opt-in; the preventivi agent uses the fiscal context).
    if want_preventivo:
        _phase("preventivi")
        try:
            prev = await run_agent(
                gateway, "preventivi",
                f"Progetto di interni. Brief: {brief}\n\nConcept sintetico:\n{concept.text[:2000]}",
                language=language, lead_id=lead_id,
            )
            credits += prev.credits_charged
            sections["preventivo"] = prev.text
        except AiGatewayError as exc:
            warnings.append(f"preventivo non generato: {exc}")

    # Phase 4 — Assemble the mini-dossier. Renders are referenced by the file
    # names the command will save them under (render-1.png, …).
    _phase("dossier")
    dossier = _assemble_dossier(brief, sections, len(renders), language)

    return ProgettoInterniResult(
        dossier_md=dossier,
        sections=sections,
        renders=renders,
        credits_charged=credits,
        warnings=warnings,
    )


def _assemble_dossier(
    brief: str, sections: dict, render_count: int, language: str,
) -> str:
    banner = {
        "it": "> **BOZZA** — elaborato generato con IA. Firma e responsabilità "
              "restano del professionista abilitato.",
        "en": "> **DRAFT** — AI-generated. Sign-off and liability remain with the "
              "licensed professional.",
        "pt": "> **RASCUNHO** — gerado por IA. Assinatura e responsabilidade "
              "permanecem do profissional habilitado.",
        "es": "> **BORRADOR** — generado con IA. Firma y responsabilidad del "
              "profesional habilitado.",
    }.get(language, "")

    parts = [f"# Progetto di interni\n\n{banner}\n", f"**Brief:** {brief}\n"]
    if sections.get("concept"):
        parts.append("## Concept e progetto\n\n" + sections["concept"])
    if render_count:
        parts.append("## Render\n\n" + "\n".join(
            f"![render {i}](render-{i}.png)" for i in range(1, render_count + 1)
        ))
    if sections.get("preventivo"):
        parts.append("## Preventivo / Proposta\n\n" + sections["preventivo"])
    return "\n\n".join(parts) + "\n"


@dataclass
class CantiereResult:
    dossier_md: str
    sections: dict = field(default_factory=dict)   # cronoprogramma / sicurezza
    credits_charged: int = 0
    warnings: list = field(default_factory=list)


async def cantiere_check(
    gateway: LovarchAiGateway,
    brief: str,
    *,
    language: str = "it",
    want_sicurezza: bool = True,
    lead_id: str | None = None,
    on_phase: Any = None,
) -> CantiereResult:
    """Composed site-check: direzione-lavori (cronoprogramma) → sicurezza pre-check
    → assembled cantiere dossier. Text via platform models (debits)."""
    def _phase(name: str) -> None:
        if callable(on_phase):
            on_phase(name)

    credits = 0
    sections: dict = {}
    warnings: list = []

    _phase("direzione-lavori")
    dl = await run_agent(gateway, "direzione-lavori", brief, language=language, lead_id=lead_id)
    credits += dl.credits_charged
    sections["cronoprogramma"] = dl.text

    if want_sicurezza:
        _phase("sicurezza-advisor")
        try:
            sic = await run_agent(
                gateway, "sicurezza-advisor",
                f"Cantiere. Brief: {brief}\n\nCronoprogramma sintetico:\n{dl.text[:2000]}",
                language=language, lead_id=lead_id,
            )
            credits += sic.credits_charged
            sections["sicurezza"] = sic.text
        except AiGatewayError as exc:
            warnings.append(f"pre-check sicurezza non generato: {exc}")

    _phase("dossier")
    banner = {
        "it": "> **BOZZA** — pre-check generato con IA. PSC/POS e responsabilità "
              "restano del coordinatore abilitato (CSP/CSE).",
        "en": "> **DRAFT** — AI pre-check. The signed safety plan remains the "
              "licensed coordinator's responsibility.",
        "pt": "> **RASCUNHO** — pré-verificação por IA. O PSC/POS assinado é do "
              "coordenador habilitado.",
        "es": "> **BORRADOR** — pre-check por IA. El plan firmado es del "
              "coordinador habilitado.",
    }.get(language, "")
    parts = [f"# Cantiere — check\n\n{banner}\n", f"**Brief:** {brief}\n"]
    if sections.get("cronoprogramma"):
        parts.append("## Direzione lavori · cronoprogramma\n\n" + sections["cronoprogramma"])
    if sections.get("sicurezza"):
        parts.append("## Pre-check sicurezza (advisory)\n\n" + sections["sicurezza"])
    dossier = "\n\n".join(parts) + "\n"

    return CantiereResult(dossier_md=dossier, sections=sections,
                          credits_charged=credits, warnings=warnings)


# Every runnable specialist except the chief itself — derived from AGENTS so
# the plan prompt and the dispatch set can never drift apart (that drift is
# exactly the bug that hid moodboard-curator/fornitori-scout from the chief).
_DISPATCHABLE = {aid for aid in AGENTS if aid != "progetto-chief"}


def _chief_plan_system() -> str:
    roster = "; ".join(
        f"{p.id} ({p.label})" for aid, p in sorted(AGENTS.items())
        if aid != "progetto-chief"
    )
    return (
        "Sei @progetto-chief, direttore di studio. Dato un brief, decidi quali "
        "specialisti coinvolgere — SOLO quelli pertinenti. Rispondi SOLO con JSON "
        'valido: {"inquadramento": "...", "agenti": [{"id": "<id>", "focus": "cosa '
        'deve produrre per questo progetto"}], "note": ["..."]}. '
        f"Gli id ammessi: {roster}. Sii selettivo (di norma 2-4 agenti); ordina "
        "gli agenti nella sequenza di lavoro corretta (chi produce input per gli "
        "altri va prima)."
    )


_CHIEF_SYNTH_SYSTEM = (
    "Sei @progetto-chief, direttore di studio. Hai ricevuto il brief e gli "
    "elaborati prodotti dagli specialisti che hai coinvolto. Produci in markdown "
    "la SINTESI DI DIREZIONE: (1) valutazione di coerenza tra gli elaborati — "
    "contraddizioni, sovrapposizioni, buchi (cita lo specialista e il punto "
    "esatto); (2) '## Dati mancanti' — le domande da fare al cliente prima di "
    "procedere; (3) prossimi passi concreti in ordine, indicando quale agente "
    "rilanciare con quale focus se un elaborato è debole; (4) cosa richiede la "
    "firma di un tecnico abilitato. Sii critico e concreto: se un elaborato non "
    "regge, dillo."
)


@dataclass
class CompletoResult:
    dossier_md: str
    plan: dict = field(default_factory=dict)
    sections: dict = field(default_factory=dict)   # agent_id → text
    credits_charged: int = 0
    warnings: list = field(default_factory=list)


async def progetto_completo(
    gateway: LovarchAiGateway,
    brief: str,
    *,
    language: str = "it",
    esegui: int = 0,           # run up to N recommended agents (0 = plan only)
    lead_id: str | None = None,
    on_phase: Any = None,
) -> CompletoResult:
    """The real hub: @progetto-chief plans (which specialists), optionally runs
    the recommended agents and consolidates them into a dossier."""
    import json as _json

    def _phase(name: str) -> None:
        if callable(on_phase):
            on_phase(name)

    credits = 0
    warnings: list = []
    sections: dict = {}

    # Phase 1 — chief plans (structured), personalized with the user's context
    # (brand/studio/fiscal/CRM lead) like every other agent.
    _phase("progetto-chief")
    plan_system, language = await personalize_system(
        gateway, _chief_plan_system(), lead_id=lead_id, language=language,
    )
    planned = await gateway.generate_text(
        brief, role="chief", system=plan_system, max_tokens=1200,
        language=language, operation_type="progetto:chief-plan",
    )
    credits += planned.credits_charged
    try:
        txt = planned.text
        plan = _json.loads(txt[txt.find("{"):txt.rfind("}") + 1])
    except (ValueError, TypeError):
        plan = {"inquadramento": planned.text[:500], "agenti": [], "note": ["piano non strutturato"]}

    agenti = [a for a in (plan.get("agenti") or []) if a.get("id") in _DISPATCHABLE]

    # Phase 2 — optionally run the recommended agents, chaining context: each
    # specialist sees a digest of what the previous ones produced (coherence).
    prior_digest = ""
    if esegui > 0 and agenti:
        for a in agenti[:esegui]:
            aid = a["id"]
            focus = a.get("focus", "")
            _phase(aid)
            payload = f"{brief}\n\nFocus richiesto: {focus}"
            if prior_digest:
                payload += (
                    "\n\nELABORATI GIÀ PRODOTTI dagli altri specialisti "
                    "(mantieni coerenza, non ripeterli):\n" + prior_digest[-6000:]
                )
            try:
                r = await run_agent(gateway, aid, payload,
                                    language=language, lead_id=lead_id)
                credits += r.credits_charged
                # Guard against transient provider early-stops: a specialist
                # deliverable under ~400 chars is truncation, not work — retry once.
                if len(r.text.strip()) < 400:
                    warnings.append(f"{aid}: output troncato ({len(r.text)} char), retry")
                    r = await run_agent(gateway, aid, payload,
                                        language=language, lead_id=lead_id)
                    credits += r.credits_charged
                sections[aid] = r.text
                prior_digest += f"\n### {aid}\n{r.text[:1500]}\n"
            except AiGatewayError as exc:
                warnings.append(f"{aid} non eseguito: {exc}")

    # Phase 3 — back to the chief: it REVIEWS the specialists' output and writes
    # the executive synthesis (coherence check, missing data, next steps).
    synthesis = ""
    if sections:
        _phase("progetto-chief:sintesi")
        review_payload = f"BRIEF:\n{brief}\n\n" + "\n\n".join(
            f"## Elaborato di {aid}\n{text[:4000]}" for aid, text in sections.items()
        )
        try:
            synth = await gateway.generate_text(
                review_payload, role="chief", system=_CHIEF_SYNTH_SYSTEM,
                max_tokens=2000, language=language,
                operation_type="progetto:chief-sintesi",
            )
            credits += synth.credits_charged
            synthesis = synth.text
        except AiGatewayError as exc:
            warnings.append(f"sintesi del chief non generata: {exc}")

    # Phase 4 — assemble.
    _phase("dossier")
    banner = {
        "it": "> **BOZZA** — piano e elaborati generati con IA. Firme e "
              "responsabilità restano dei professionisti abilitati.",
        "en": "> **DRAFT** — AI-generated plan and documents. Sign-off stays with "
              "the licensed professionals.",
        "pt": "> **RASCUNHO** — plano e documentos por IA. Assinaturas dos "
              "profissionais habilitados.",
        "es": "> **BORRADOR** — plan y documentos por IA.",
    }.get(language, "")
    parts = [f"# Dossier di progetto\n\n{banner}\n", f"**Brief:** {brief}\n"]
    if plan.get("inquadramento"):
        parts.append("## Inquadramento (progetto-chief)\n\n" + str(plan["inquadramento"]))
    if agenti:
        parts.append("## Piano — specialisti coinvolti\n\n" + "\n".join(
            f"- **{a['id']}** — {a.get('focus','')}" for a in agenti))
    for aid, text in sections.items():
        parts.append(f"## {aid}\n\n{text}")
    if synthesis:
        parts.append("## Sintesi di direzione (progetto-chief)\n\n" + synthesis)
    dossier = "\n\n".join(parts) + "\n"

    return CompletoResult(dossier_md=dossier, plan=plan, sections=sections,
                          credits_charged=credits, warnings=warnings)
