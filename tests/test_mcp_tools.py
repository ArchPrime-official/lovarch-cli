"""Unit tests for the Lovarch MCP tool implementations."""
from __future__ import annotations

import httpx

from lovarch_cli.ai import AiImageResult, InsufficientCreditsError
from lovarch_cli.mcp import tools


class _FakeSession:
    def __init__(self, response: httpx.Response, user_id="u1", email="a@b.co"):
        self._response = response
        self._uid = user_id
        self._email = email

    @property
    def user_id(self):
        return self._uid

    @property
    def email(self):
        return self._email

    async def request(self, method, path, *, json=None, timeout=None, **kwargs):
        return self._response


def _resp(status, payload):
    return httpx.Response(status, json=payload, request=httpx.Request("POST", "http://x"))


async def test_whoami_unauthenticated():
    out = await tools.tool_whoami(None)
    assert out["authenticated"] is False
    assert out["mode"] == "none"


async def test_whoami_premium():
    out = await tools.tool_whoami(_FakeSession(_resp(200, {}), user_id="abc", email="x@y.z"))
    assert out == {"authenticated": True, "mode": "premium", "user_id": "abc", "email": "x@y.z"}


async def test_credits_reports_balance():
    session = _FakeSession(_resp(200, {
        "ok": True, "balance": 994, "monthly_used": 6,
        "credits_remaining": 988, "is_admin": False,
    }))
    out = await tools.tool_credits(session)
    assert out == {"balance": 994, "monthly_used": 6, "credits_remaining": 988, "is_admin": False}


async def test_credits_unauthenticated():
    out = await tools.tool_credits(None)
    assert out["error"] == "not_authenticated"


class _FakeGateway:
    def __init__(self, result=None, exc=None):
        self._result = result
        self._exc = exc
        self.last_kwargs = None

    async def generate_image(self, prompt, **kwargs):
        self.last_kwargs = {"prompt": prompt, **kwargs}
        if self._exc:
            raise self._exc
        return self._result


async def test_generate_image_saves_and_reports_debit(tmp_path):
    gw = _FakeGateway(result=AiImageResult(
        image_bytes=b"PNGDATA", content_type="image/png", revised_prompt="rp",
        credits_charged=6, balance=994, is_admin=False,
    ))
    out_file = tmp_path / "sub" / "img.png"
    out = await tools.tool_generate_image(gw, prompt="grey square",
                                          output_path=str(out_file), quality="low")
    assert out["ok"] is True
    assert out["credits_charged"] == 6
    assert out_file.read_bytes() == b"PNGDATA"
    # operation_type is tagged so cost attribution shows the MCP origin
    assert gw.last_kwargs["operation_type"] == "mcp:generate_image"


async def test_generate_image_insufficient_credits(tmp_path):
    gw = _FakeGateway(exc=InsufficientCreditsError(available=2, needed=6))
    out = await tools.tool_generate_image(gw, prompt="x", output_path=str(tmp_path / "x.png"))
    assert out["error"] == "insufficient_credits"
    assert out["credits_available"] == 2 and out["credits_needed"] == 6
    assert not (tmp_path / "x.png").exists()


async def test_generate_image_unauthenticated(tmp_path):
    out = await tools.tool_generate_image(None, prompt="x", output_path=str(tmp_path / "x.png"))
    assert out["error"] == "not_authenticated"




