"""Unit tests for generate_text / get_user_context + MCP text/context tools."""
from __future__ import annotations

import httpx
import pytest

from lovarch_cli.ai import AiGatewayError, InsufficientCreditsError, LovarchAiGateway
from lovarch_cli.mcp import tools


class _FakeSession:
    def __init__(self, response: httpx.Response) -> None:
        self._response = response
        self.last_call: dict | None = None

    async def request(self, method, path, *, json=None, timeout=None, **kwargs):
        self.last_call = {"method": method, "path": path, "json": json}
        return self._response


def _resp(status, payload):
    return httpx.Response(status, json=payload, request=httpx.Request("POST", "http://x"))


async def test_generate_text_role_and_debit():
    session = _FakeSession(_resp(200, {
        "ok": True, "text": "Ecco 3 vantaggi...", "model": "anthropic/claude-sonnet-5",
        "usage": {"input_tokens": 120, "output_tokens": 300},
        "credits_charged": 5, "balance": 995, "is_admin": False,
    }))
    gw = LovarchAiGateway(session)  # type: ignore[arg-type]
    r = await gw.generate_text("vantaggi BIM", role="executor", language="it", max_tokens=300)
    assert r.text.startswith("Ecco")
    assert r.model == "anthropic/claude-sonnet-5"
    assert r.credits_charged == 5 and r.balance == 995
    assert r.input_tokens == 120 and r.output_tokens == 300
    body = session.last_call["json"]
    assert body["role"] == "executor" and body["language"] == "it"
    assert "model" not in body
    assert session.last_call["path"] == "/functions/v1/cli-ai-text"


async def test_generate_text_explicit_model_wins_over_role():
    session = _FakeSession(_resp(200, {
        "ok": True, "text": "OK", "model": "google/gemini-3.5-flash",
        "usage": {}, "credits_charged": 1, "balance": 99, "is_admin": False,
    }))
    gw = LovarchAiGateway(session)  # type: ignore[arg-type]
    await gw.generate_text("x", model="google/gemini-3.5-flash")
    body = session.last_call["json"]
    assert body["model"] == "google/gemini-3.5-flash"
    assert "role" not in body


async def test_generate_text_402():
    session = _FakeSession(_resp(402, {
        "ok": False, "error": "insufficient_credits",
        "credits_available": 3, "credits_needed": 70,
    }))
    gw = LovarchAiGateway(session)  # type: ignore[arg-type]
    with pytest.raises(InsufficientCreditsError) as exc:
        await gw.generate_text("x")
    assert exc.value.available == 3 and exc.value.needed == 70


async def test_get_user_context_bundle():
    session = _FakeSession(_resp(200, {
        "ok": True, "signature_line": "Giulia Verdi · architetto",
        "preferences": {"preferred_language": "it"},
        "context_summary": {"hasBrand": True},
        "prompt_block": "## Contesto...",
    }))
    gw = LovarchAiGateway(session)  # type: ignore[arg-type]
    bundle = await gw.get_user_context(lead_id="abc")
    assert bundle["signature_line"] == "Giulia Verdi · architetto"
    assert session.last_call["json"] == {"lead_id": "abc"}


async def test_get_user_context_error():
    session = _FakeSession(_resp(500, {"ok": False, "error": "boom"}))
    gw = LovarchAiGateway(session)  # type: ignore[arg-type]
    with pytest.raises(AiGatewayError):
        await gw.get_user_context()


class _FakeGateway:
    def __init__(self, text_result=None, ctx=None, exc=None):
        self._text = text_result
        self._ctx = ctx
        self._exc = exc

    async def generate_text(self, prompt, **kwargs):
        if self._exc:
            raise self._exc
        return self._text

    async def get_user_context(self, lead_id=None):
        if self._exc:
            raise self._exc
        return self._ctx


async def test_tool_ai_text_reports_credits_only():
    from lovarch_cli.ai import AiTextResult
    gw = _FakeGateway(text_result=AiTextResult(
        text="ciao", model="anthropic/claude-sonnet-5", input_tokens=10,
        output_tokens=5, credits_charged=1, balance=99, is_admin=False))
    out = await tools.tool_ai_text(gw, prompt="x")
    assert out["ok"] is True and out["credits_charged"] == 1
    # never expose provider cost fields
    assert "cost_usd" not in out


async def test_tool_ai_text_unauthenticated():
    out = await tools.tool_ai_text(None, prompt="x")
    assert out["error"] == "not_authenticated"


async def test_tool_user_context_passthrough():
    gw = _FakeGateway(ctx={"ok": True, "signature_line": "X"})
    out = await tools.tool_user_context(gw)
    assert out["signature_line"] == "X"
