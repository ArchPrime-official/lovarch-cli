"""`lovarch api` — passthrough genérico para a api-v1 (mesma superfície do MCP)."""
from __future__ import annotations

import httpx
import pytest
import typer

from lovarch_cli.ai import ApiCallError, LovarchAiGateway
from lovarch_cli.commands import api_cmd


class _FakeSession:
    def __init__(self, responses: list[httpx.Response]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    async def request(self, method, path, *, json=None, timeout=None, **kwargs):
        self.calls.append({"method": method, "path": path, "json": json})
        return self._responses.pop(0)


def _resp(status: int, payload) -> httpx.Response:
    return httpx.Response(status, json=payload, request=httpx.Request("POST", "http://x"))


async def test_api_sends_action_and_params_to_api_v1():
    s = _FakeSession([_resp(200, {"ok": True, "projects": []})])
    out = await LovarchAiGateway(s).api("progetta.list", {"limit": 5})
    assert out["projects"] == []
    assert s.calls[0]["path"] == "/functions/v1/api-v1"
    assert s.calls[0]["json"] == {"limit": 5, "action": "progetta.list"}


async def test_api_error_carries_hint_status_and_payload():
    s = _FakeSession([_resp(403, {"ok": False, "error": "progetta_not_available", "hint": "Progetta non disponibile"})])
    with pytest.raises(ApiCallError) as exc:
        await LovarchAiGateway(s).api("progetta.list")
    assert "Progetta non disponibile" in str(exc.value)
    assert exc.value.status_code == 403
    assert exc.value.payload["error"] == "progetta_not_available"


async def test_api_error_without_hint_shows_field():
    s = _FakeSession([_resp(400, {"ok": False, "error": "missing_field", "field": "name"})])
    with pytest.raises(ApiCallError) as exc:
        await LovarchAiGateway(s).api("write.create_lead")
    assert "missing_field" in str(exc.value) and "campo: name" in str(exc.value)


async def test_api_actions_reads_list_from_get():
    s = _FakeSession([_resp(405, {"ok": False, "actions": ["whoami", "progetta.<action>", 3]})])
    assert await LovarchAiGateway(s).api_actions() == ["whoami", "progetta.<action>"]
    assert s.calls[0]["method"] == "GET"


def test_parse_params_reads_json_values_and_merges_json_body():
    out = api_cmd.parse_params(["limit=5", "force=true", "ids=[\"W3\"]", "title=Casa Rossi", "x=a=b"], '{"lang":"it"}')
    assert out == {"lang": "it", "limit": 5, "force": True, "ids": ["W3"], "title": "Casa Rossi", "x": "a=b"}
    with pytest.raises(typer.BadParameter):
        api_cmd.parse_params(["senza-uguale"], None)
    with pytest.raises(typer.BadParameter):
        api_cmd.parse_params([], "[1,2]")


def test_status_action_uses_module():
    assert api_cmd.status_action("progetta.render") == "progetta.status"
    assert api_cmd.status_action("video.create") == "video.status"


async def test_wait_polls_status_until_terminal(monkeypatch):
    async def no_sleep(_):
        return None
    monkeypatch.setattr(api_cmd.asyncio, "sleep", no_sleep)
    s = _FakeSession([
        _resp(200, {"ok": True, "status": "running"}),
        _resp(200, {"ok": True, "status": "done", "result": {"revision_number": 2}}),
    ])
    gw = LovarchAiGateway(s)
    out = await api_cmd._wait(gw, "progetta.edit", {"ok": True, "job_id": "j1"}, every=0, timeout=60)
    assert out["status"] == "done"
    assert [c["json"] for c in s.calls] == [{"job_id": "j1", "action": "progetta.status"}] * 2


async def test_wait_without_job_id_returns_result():
    gw = LovarchAiGateway(_FakeSession([]))
    assert await api_cmd._wait(gw, "progetta.list", {"ok": True}, every=0, timeout=1) == {"ok": True}


class _PutClient:
    puts: list[dict] = []

    def __init__(self, *a, **k): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    async def put(self, url, content=None, headers=None):
        _PutClient.puts.append({"url": url, "len": len(content), "ct": headers["Content-Type"]})
        return httpx.Response(200, request=httpx.Request("PUT", url))


@pytest.mark.parametrize("module,action,purpose", [
    ("progetta", "progetta.upload_url", None),
    ("proposals", "files.upload", "proposal"),
    ("render", "files.upload", "media"),
])
async def test_upload_file_routes_by_module_and_puts_bytes(tmp_path, monkeypatch, module, action, purpose):
    f = tmp_path / "pianta.pdf"
    f.write_bytes(b"%PDF-1.4 test")
    s = _FakeSession([_resp(200, {
        "ok": True, "upload_url": "https://storage.test/upload?token=t", "upload_page_url": "https://app/upload#t=x",
        "storage_path": "connector-uploads/u/x.pdf", "method": "PUT", "headers": {}, "accepted": ["pdf"],
    })])
    _PutClient.puts = []
    monkeypatch.setattr("lovarch_cli.ai.gateway.httpx.AsyncClient", _PutClient)
    ref = await LovarchAiGateway(s).upload_file(str(f), module)
    assert ref == {"storage_path": "connector-uploads/u/x.pdf"}
    sent = s.calls[0]["json"]
    assert sent["action"] == action and sent["size"] == 13 and sent["file_name"] == "pianta.pdf"
    assert sent.get("purpose") == purpose
    assert _PutClient.puts == [{"url": "https://storage.test/upload?token=t", "len": 13, "ct": "application/pdf"}]


async def test_upload_file_errors(tmp_path, monkeypatch):
    from lovarch_cli.ai import AiGatewayError
    with pytest.raises(AiGatewayError):
        await LovarchAiGateway(_FakeSession([])).upload_file(str(tmp_path / "nada.pdf"), "proposals")
    f = tmp_path / "a.pdf"
    f.write_bytes(b"%PDF")
    with pytest.raises(AiGatewayError):
        await LovarchAiGateway(_FakeSession([_resp(200, {"ok": True})])).upload_file(str(f), "proposals")
