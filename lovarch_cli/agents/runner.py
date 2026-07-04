"""Run a curated agent persona via the platform text gateway.

Prepends the user's personalization bundle (brand, style, signature, language)
to the agent's system prompt, so every agent speaks in the user's brand and
language, and debits the user's credits by real tokens.
"""
from __future__ import annotations

from dataclasses import dataclass

from lovarch_cli.agents.prompts import AGENTS
from lovarch_cli.ai import AiGatewayError, LovarchAiGateway


@dataclass
class AgentResult:
    agent_id: str
    text: str
    model: str
    credits_charged: int
    balance: int | None


# Appended to EVERY agent system prompt: when the brief lacks essentials the
# agent must ASK (Dati mancanti section) and declare its assumptions — never
# silently invent measures/prices/local rules.
AGENT_TAIL = (
    "\n\nSe nel brief mancano dati essenziali per un lavoro professionale, apri "
    "la risposta con una sezione '## Dati mancanti' elencando le domande precise "
    "da fare al cliente; poi procedi dichiarando esplicitamente le ipotesi "
    "assunte. Non inventare mai dati specifici (misure, prezzi, riferimenti "
    "locali) senza dichiararli come ipotesi."
)


async def personalize_system(
    gateway: LovarchAiGateway,
    system: str,
    *,
    lead_id: str | None = None,
    language: str = "it",
) -> tuple[str, str]:
    """Best-effort personalization: prepend the user's context prompt_block and
    honor the mandatory preferred_language. Returns (system, language)."""
    try:
        bundle = await gateway.get_user_context(lead_id=lead_id)
        block = bundle.get("prompt_block") if isinstance(bundle, dict) else None
        if block:
            system = f"{block}\n\n{system}"
        lang = ((bundle or {}).get("preferences") or {}).get("preferred_language") if isinstance(bundle, dict) else None
        if lang:
            language = lang
    except (AiGatewayError, AttributeError):
        pass  # personalization is optional; the agent still runs
    return system, language


async def fetch_account_digest(gateway: LovarchAiGateway) -> str:
    """Compact digest of the user's REAL account data (cli-data) for agents
    with ``wants_account_data`` — finance by month, projects, CRM pipeline.
    Best-effort: returns '' when the data surface is unavailable."""
    import json as _json

    parts: list[str] = []
    try:
        fin = await gateway.data("financial_summary", months=12)
        if fin.get("by_month"):
            parts.append("SINTESI FINANZIARIA (12 mesi, EUR):\n"
                         + _json.dumps(fin.get("by_month"), ensure_ascii=False))
            if fin.get("expense_by_category"):
                parts.append("SPESE PER CATEGORIA:\n"
                             + _json.dumps(fin["expense_by_category"], ensure_ascii=False))
    except (AiGatewayError, AttributeError):
        pass
    try:
        proj = await gateway.data("projects_list", limit=20)
        items = proj.get("items") or []
        if items:
            parts.append("PROGETTI:\n" + "\n".join(
                f"- {p.get('name')} · {p.get('status')} · {p.get('typology') or ''} "
                f"· budget {p.get('budget_min') or '?'}–{p.get('budget_max') or '?'}"
                for p in items[:20]))
    except (AiGatewayError, AttributeError):
        pass
    try:
        leads = await gateway.data("leads_list", limit=30)
        items = leads.get("items") or []
        if items:
            stages: dict[str, int] = {}
            for l in items:
                stages[l.get("status") or "?"] = stages.get(l.get("status") or "?", 0) + 1
            parts.append("PIPELINE CRM (clienti per fase): "
                         + ", ".join(f"{k}: {v}" for k, v in stages.items()))
    except (AiGatewayError, AttributeError):
        pass
    return "\n\n".join(parts)


async def fetch_model_digest(gateway: LovarchAiGateway, cad_id: str) -> str:
    """Digest of a CAD/BIM model's extracted data (rooms/areas/materials) for
    agents with ``wants_model_data`` — real quantities instead of estimates."""
    try:
        r = await gateway.data("model_data", cad_id=cad_id)
    except (AiGatewayError, AttributeError):
        return ""
    d = (r or {}).get("data") if isinstance(r, dict) else None
    if not isinstance(d, dict):
        return ""
    parts = []
    if d.get("superficie_totale_mq"):
        parts.append(f"Superficie totale: {d['superficie_totale_mq']} mq · "
                     f"{d.get('contagem_ambienti', 0)} ambienti")
    amb = d.get("ambienti") or []
    if amb:
        parts.append("AMBIENTI (dal modello CAD/BIM):\n" + "\n".join(
            f"- {a.get('nome')}: {a.get('area')} mq" for a in amb[:60]))
    cat = d.get("contagem_per_categoria") or {}
    if cat:
        parts.append("Oggetti per categoria: "
                     + ", ".join(f"{k}={v}" for k, v in list(cat.items())[:20]))
    mat = d.get("materiali") or []
    if mat:
        parts.append("Materiali: " + ", ".join(mat[:30]))
    return "\n\n".join(parts)


async def run_agent(
    gateway: LovarchAiGateway,
    agent_id: str,
    brief: str,
    *,
    language: str = "it",
    lead_id: str | None = None,
    cad_id: str | None = None,
) -> AgentResult:
    """Run the agent on a brief, personalized with the user's context bundle."""
    persona = AGENTS.get(agent_id)
    if persona is None:
        raise AiGatewayError(
            f"Agente sconosciuto: {agent_id}. Disponibili: {', '.join(AGENTS)}"
        )

    system, language = await personalize_system(
        gateway, persona.system + AGENT_TAIL, lead_id=lead_id, language=language,
    )

    # Data-driven agents (studio-advisor): work on the user's REAL numbers.
    if persona.wants_account_data:
        digest = await fetch_account_digest(gateway)
        if digest:
            brief = f"{brief}\n\n=== DATI REALI DELLO STUDIO (Lovarch) ===\n{digest}"
        else:
            brief = (f"{brief}\n\n(Nessun dato finanziario/CRM disponibile "
                     "nell'account — segnalalo in '## Dati mancanti'.)")

    # Model-driven agents (computo/capitolato): use REAL quantities from a CAD
    # model when the caller passed --cad <id>.
    if persona.wants_model_data and cad_id:
        model = await fetch_model_digest(gateway, cad_id)
        if model:
            brief = f"{brief}\n\n=== DATI DAL MODELLO CAD/BIM ===\n{model}"

    result = await gateway.generate_text(
        brief,
        role=persona.role,  # type: ignore[arg-type]
        system=system,
        max_tokens=persona.default_max_tokens,
        language=language,
        operation_type=f"agent:{agent_id}",
    )
    return AgentResult(
        agent_id=agent_id,
        text=result.text,
        model=result.model,
        credits_charged=result.credits_charged,
        balance=result.balance,
    )
