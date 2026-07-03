"""Unit tests for the Lovarch AI gateway client (cli-ai-generate)."""
from __future__ import annotations

import base64

import httpx
import pytest

from lovarch_cli.ai import (
    AiGatewayError,
    InsufficientCreditsError,
    LovarchAiGateway,
)

# 1x1 transparent PNG
_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg=="
)
_DATA_URL = "data:image/png;base64," + base64.b64encode(_PNG).decode()


class _FakeSession:
    """Records the last request and returns a canned httpx.Response."""

    def __init__(self, response: httpx.Response) -> None:
        self._response = response
        self.last_call: dict | None = None

    async def request(self, method, path, *, json=None, timeout=None, **kwargs):
        self.last_call = {"method": method, "path": path, "json": json, "timeout": timeout}
        return self._response


def _resp(status: int, payload: dict) -> httpx.Response:
    return httpx.Response(status, json=payload, request=httpx.Request("POST", "http://x"))


async def test_generate_image_success_decodes_and_reports_debit():
    session = _FakeSession(_resp(200, {
        "ok": True,
        "image_base64": _DATA_URL,
        "revised_prompt": "a grey square",
        "credits_charged": 6,
        "balance": 994,
        "cost_usd": 0.006,
        "is_admin": False,
    }))
    gw = LovarchAiGateway(session)  # type: ignore[arg-type]

    result = await gw.generate_image("grey square", quality="low")

    assert result.image_bytes == _PNG
    assert result.content_type == "image/png"
    assert result.credits_charged == 6
    assert result.balance == 994
    assert result.cost_usd == 0.006
    assert result.is_admin is False
    # request went to the gateway EF with the expected body
    assert session.last_call["path"] == "/functions/v1/cli-ai-generate"
    assert session.last_call["json"]["quality"] == "low"
    assert session.last_call["json"]["mode"] == "generate"


async def test_insufficient_credits_raises_typed_error():
    session = _FakeSession(_resp(402, {
        "ok": False,
        "error": "insufficient_credits",
        "credits_available": 2,
        "credits_needed": 6,
    }))
    gw = LovarchAiGateway(session)  # type: ignore[arg-type]

    with pytest.raises(InsufficientCreditsError) as exc:
        await gw.generate_image("x", quality="low")
    assert exc.value.available == 2
    assert exc.value.needed == 6


async def test_generation_failure_raises_gateway_error():
    session = _FakeSession(_resp(500, {"ok": False, "error": "generation_failed"}))
    gw = LovarchAiGateway(session)  # type: ignore[arg-type]

    with pytest.raises(AiGatewayError) as exc:
        await gw.generate_image("x")
    assert "generation_failed" in str(exc.value)


async def test_edit_mode_sends_image_urls():
    session = _FakeSession(_resp(200, {
        "ok": True, "image_base64": _DATA_URL, "credits_charged": 6,
        "balance": 100, "cost_usd": 0.006, "is_admin": False,
    }))
    gw = LovarchAiGateway(session)  # type: ignore[arg-type]

    await gw.generate_image(
        "combine", mode="edit", image_urls=["https://ex/a.png", "https://ex/b.png"],
        operation_type="cli:render",
    )
    assert session.last_call["json"]["mode"] == "edit"
    assert session.last_call["json"]["image_urls"] == ["https://ex/a.png", "https://ex/b.png"]
    assert session.last_call["json"]["operation_type"] == "cli:render"


def test_bad_data_url_raises():
    from lovarch_cli.ai.gateway import _decode_data_url

    with pytest.raises(AiGatewayError):
        _decode_data_url("not-a-data-url")
