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

from lovarch_cli.agents import run_agent
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
