"""Unit tests for PlatformWorkflows (render/colors/copy wrappers)."""
from __future__ import annotations

import base64

import httpx
import pytest

from lovarch_cli.workflows import PlatformWorkflows, WorkflowError

_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+P+/HgAFhAJ/wlseKgAAAABJRU5ErkJggg=="
)


class _FakeSession:
    def __init__(self, response: httpx.Response) -> None:
        self._response = response
        self.last_call: dict | None = None

    async def request(self, method, path, *, json=None, timeout=None, **kwargs):
        self.last_call = {"method": method, "path": path, "json": json, "timeout": timeout}
        return self._response


def _resp(status, payload):
    return httpx.Response(status, json=payload, request=httpx.Request("POST", "http://x"))


async def test_render_data_url_decoded():
    data_url = "data:image/png;base64," + base64.b64encode(_PNG).decode()
    session = _FakeSession(_resp(200, {"image": data_url, "message": "ok"}))
    wf = PlatformWorkflows(session)  # type: ignore[arg-type]
    r = await wf.render("soggiorno minimal", render_style="wabi-sabi", language="it")
    assert r.image_bytes == _PNG and r.image_url is None
    body = session.last_call["json"]
    assert body["renderStyle"] == "wabi-sabi" and body["language"] == "it"
    assert "mode" not in body  # legacy 2D path
    assert session.last_call["path"] == "/functions/v1/render-ai-generate"


async def test_render_hosted_url_passthrough():
    session = _FakeSession(_resp(200, {"image": "https://cdn/render.png"}))
    wf = PlatformWorkflows(session)  # type: ignore[arg-type]
    r = await wf.render("x", mode="room_render")
    assert r.image_url == "https://cdn/render.png" and r.image_bytes is None
    assert session.last_call["json"]["mode"] == "room_render"


async def test_render_invalid_mode():
    wf = PlatformWorkflows(_FakeSession(_resp(200, {})))  # type: ignore[arg-type]
    with pytest.raises(WorkflowError):
        await wf.render("x", mode="teleport")


async def test_render_reference_image_inlined(tmp_path):
    ref = tmp_path / "sketch.png"
    ref.write_bytes(_PNG)
    data_url = "data:image/png;base64," + base64.b64encode(_PNG).decode()
    session = _FakeSession(_resp(200, {"image": data_url}))
    wf = PlatformWorkflows(session)  # type: ignore[arg-type]
    await wf.render("x", reference_image_path=ref)
    assert session.last_call["json"]["referenceImage"].startswith("data:image/png;base64,")


async def test_insufficient_credits_message_user_safe():
    session = _FakeSession(_resp(402, {"error": "insufficient_credits",
                                       "credits_available": 10, "credits_needed": 134}))
    wf = PlatformWorkflows(session)  # type: ignore[arg-type]
    with pytest.raises(WorkflowError) as exc:
        await wf.render("x", mode="plan_to_3d")
    msg = str(exc.value)
    assert "Crediti insufficienti" in msg and "134" in msg
    assert "usd" not in msg.lower() and "$" not in msg


async def test_colors_extract_from_image():
    session = _FakeSession(_resp(200, {"palette": ["#A16207"]}))
    wf = PlatformWorkflows(session)  # type: ignore[arg-type]
    out = await wf.colors(image_url="https://x/i.png", language="pt")
    assert out["palette"] == ["#A16207"]
    body = session.last_call["json"]
    assert body["extractFromImage"] is True and body["language"] == "pt"


async def test_colors_invalid_style():
    wf = PlatformWorkflows(_FakeSession(_resp(200, {})))  # type: ignore[arg-type]
    with pytest.raises(WorkflowError):
        await wf.colors(style="brutalist")


async def test_copy_unwraps_copy_field():
    session = _FakeSession(_resp(200, {"ok": True, "copy": {"caption": "Bella casa", "hashtags": ["#casa"]}}))
    wf = PlatformWorkflows(session)  # type: ignore[arg-type]
    out = await wf.copy("nuovo progetto attico", mode="post", language="it")
    assert out["caption"] == "Bella casa"
    assert session.last_call["json"]["slideCount"] == 5


async def test_copy_invalid_mode():
    wf = PlatformWorkflows(_FakeSession(_resp(200, {})))  # type: ignore[arg-type]
    with pytest.raises(WorkflowError):
        await wf.copy("x", mode="reel")


async def test_logo_returns_url():
    session = _FakeSession(_resp(200, {"success": True, "logoUrl": "https://cdn/logo.png", "message": "ok"}))
    wf = PlatformWorkflows(session)  # type: ignore[arg-type]
    r = await wf.logo("studio minimal", language="it")
    assert r.image_url == "https://cdn/logo.png"
    assert session.last_call["path"] == "/functions/v1/logo-generate"


async def test_site_returns_html():
    session = _FakeSession(_resp(200, {"code": "<html>ciao</html>"}))
    wf = PlatformWorkflows(session)  # type: ignore[arg-type]
    html = await wf.site("portfolio architetto", language="pt")
    assert "<html>" in html
    assert session.last_call["json"]["language"] == "pt"



async def test_script_returns_persisted_content():
    session = _FakeSession(_resp(200, {
        "success": True, "persisted": True,
        "script": {"id": "abc", "title": "Reel luce", "content": "<p>Hook</p>",
                   "keywords": ["#luce"]},
    }))
    wf = PlatformWorkflows(session)  # type: ignore[arg-type]
    out = await wf.script("illuminazione", type="reel", language="it")
    assert out["content"] == "<p>Hook</p>"
    assert out["persisted"] is True
    assert session.last_call["json"]["topic"] == "illuminazione"
    assert session.last_call["json"]["language"] == "it"


async def test_script_resilient_not_persisted():
    session = _FakeSession(_resp(200, {
        "success": True, "persisted": False, "refunded": True,
        "script": {"id": None, "title": "T", "full_script": "<p>x</p>"},
    }))
    wf = PlatformWorkflows(session)  # type: ignore[arg-type]
    out = await wf.script("tema", language="it")
    # content is normalized from full_script when not persisted
    assert out["content"] == "<p>x</p>"
    assert out["persisted"] is False


async def test_script_error_raises():
    session = _FakeSession(_resp(200, {"success": False, "error": "boom"}))
    wf = PlatformWorkflows(session)  # type: ignore[arg-type]
    with pytest.raises(WorkflowError):
        await wf.script("tema", language="it")
