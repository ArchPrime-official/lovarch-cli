"""Unit tests for the architect/interior/construction agents."""
from __future__ import annotations

import httpx
import pytest

from lovarch_cli.agents import AGENTS, run_agent
from lovarch_cli.ai import AiGatewayError


class _FakeSession:
    def __init__(self, ctx_resp, text_resp):
        self._ctx = ctx_resp
        self._text = text_resp
        self.calls = []

    async def request(self, method, path, *, json=None, timeout=None, **kwargs):
        self.calls.append(path)
        return self._ctx if "cli-user-context" in path else self._text


def _resp(status, payload):
    return httpx.Response(status, json=payload, request=httpx.Request("POST", "http://x"))


def test_agents_catalog_has_roles():
    assert "interior-designer" in AGENTS
    assert AGENTS["geometra-catasto"].role == "verifier"  # → Opus
    assert AGENTS["interior-designer"].role == "executor"  # → Sonnet


async def test_run_agent_personalizes_and_debits():
    from lovarch_cli.ai import LovarchAiGateway

    ctx = _resp(200, {"ok": True, "prompt_block": "## Brand\nStudio X",
                      "preferences": {"preferred_language": "it"}})
    txt = _resp(200, {"ok": True, "text": "## Progetto di interni\n...",
                      "model": "anthropic/claude-sonnet-5",
                      "usage": {"input_tokens": 200, "output_tokens": 800},
                      "credits_charged": 13, "balance": 987, "is_admin": False})
    session = _FakeSession(ctx, txt)
    gw = LovarchAiGateway(session)  # type: ignore[arg-type]
    r = await run_agent(gw, "interior-designer", "attico 90mq legno")
    assert r.agent_id == "interior-designer"
    assert r.credits_charged == 13
    # both the context fetch and the text generation happened
    assert any("cli-user-context" in c for c in session.calls)
    assert any("cli-ai-text" in c for c in session.calls)


async def test_run_agent_unknown_raises():
    from lovarch_cli.ai import LovarchAiGateway

    session = _FakeSession(_resp(200, {"ok": True}), _resp(200, {"ok": True}))
    gw = LovarchAiGateway(session)  # type: ignore[arg-type]
    with pytest.raises(AiGatewayError):
        await run_agent(gw, "nonexistent", "x")


async def test_run_agent_survives_context_failure():
    from lovarch_cli.ai import LovarchAiGateway

    ctx = _resp(500, {"ok": False, "error": "boom"})  # context fails
    txt = _resp(200, {"ok": True, "text": "output", "model": "anthropic/claude-sonnet-5",
                      "usage": {}, "credits_charged": 5, "balance": 5, "is_admin": False})
    session = _FakeSession(ctx, txt)
    gw = LovarchAiGateway(session)  # type: ignore[arg-type]
    r = await run_agent(gw, "preventivi", "brief")  # personalization optional
    assert r.text == "output"
