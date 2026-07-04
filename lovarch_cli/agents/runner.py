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
    except AiGatewayError:
        pass  # personalization is optional; the agent still runs
    return system, language


async def run_agent(
    gateway: LovarchAiGateway,
    agent_id: str,
    brief: str,
    *,
    language: str = "it",
    lead_id: str | None = None,
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
