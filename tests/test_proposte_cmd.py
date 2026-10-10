"""`lovarch proposte` — elenco, migliora (upload + restyle + attesa), pdf e stato."""
from __future__ import annotations

from typer.testing import CliRunner

from lovarch_cli.commands import proposte_cmd

runner = CliRunner()


class _FakeGw:
    def __init__(self, responses: dict[str, list[dict]]) -> None:
        self.responses = {k: list(v) for k, v in responses.items()}
        self.calls: list[tuple[str, dict]] = []
        self.uploads: list[tuple[str, str]] = []

    async def api(self, action, params=None):
        self.calls.append((action, params or {}))
        queue = self.responses[action]
        return queue.pop(0) if len(queue) > 1 else queue[0]

    async def upload_file(self, path, purpose):
        self.uploads.append((path, purpose))
        return {"storage_path": "connector-uploads/u/proposal/x-deck.pdf", "purpose": "proposal"}


def _patch(monkeypatch, gw):
    monkeypatch.setattr(proposte_cmd, "_gateway", lambda: gw)

    async def no_sleep(_):
        return None
    monkeypatch.setattr(proposte_cmd.asyncio, "sleep", no_sleep)


def test_elenco_mostra_link_do_cliente(monkeypatch):
    gw = _FakeGw({"proposals.list": [{"ok": True, "proposals": [
        {"id": "p1234567-x", "title": "Casa Rossi", "client_name": "Rossi", "status": "sent", "total": 1000,
         "client_url": "https://app.lovarch.com/proposta/t"}]}]})
    _patch(monkeypatch, gw)
    r = runner.invoke(proposte_cmd.proposte_app, ["elenco", "--stato", "sent", "--cerca", "Rossi"])
    assert r.exit_code == 0, r.output
    assert "Casa Rossi" in r.output and "p1234567" in r.output
    assert gw.calls[0] == ("proposals.list", {"limit": 20, "status": "sent", "q": "Rossi"})


def test_migliora_carica_restyle_e_attende(monkeypatch, tmp_path):
    f = tmp_path / "deck.pdf"
    f.write_bytes(b"%PDF")
    gw = _FakeGw({
        "proposals.restyle": [{"ok": True, "job_id": "j1", "pages": 4, "photos": 3}],
        "proposals.status": [{"status": "processing"}, {"status": "done", "proposal_id": "p1", "title": "Villa", "slides": 4, "credits_cost": 7}],
    })
    _patch(monkeypatch, gw)
    r = runner.invoke(proposte_cmd.proposte_app, ["migliora", str(f), "--cliente", "Bianchi", "--termini", "--max-crediti", "200"])
    assert r.exit_code == 0, r.output
    assert "Villa" in r.output and "p1" in r.output
    assert gw.uploads == [(str(f), "proposals")]
    action, body = gw.calls[0]
    assert action == "proposals.restyle"
    assert body == {"storage_path": "connector-uploads/u/proposal/x-deck.pdf", "language": "it", "include_terms_sign": True,
                    "include_cover": True, "client_name": "Bianchi", "max_credits": 200}


def test_migliora_falha_e_sem_attesa(monkeypatch, tmp_path):
    f = tmp_path / "deck.pptx"
    f.write_bytes(b"PK")
    gw = _FakeGw({"proposals.restyle": [{"ok": True, "job_id": "j2"}], "proposals.status": [{"status": "failed", "error": "not_a_presentation"}]})
    _patch(monkeypatch, gw)
    r = runner.invoke(proposte_cmd.proposte_app, ["migliora", str(f)])
    assert r.exit_code == 1 and "not_a_presentation" in r.output
    r = runner.invoke(proposte_cmd.proposte_app, ["migliora", str(f), "--no-attendi"])
    assert r.exit_code == 0 and "lovarch proposte stato j2" in r.output


def test_pdf_scarica_e_stato(monkeypatch, tmp_path):
    gw = _FakeGw({
        "proposals.export_pdf": [{"ok": True, "job_id": "j3"}],
        "proposals.status": [{"status": "done", "url": "https://storage/x.pdf"}],
    })
    _patch(monkeypatch, gw)

    class _R:
        content = b"%PDF-1.7" * 200
        def raise_for_status(self): return None
    monkeypatch.setattr(proposte_cmd.httpx, "get", lambda url, timeout=None: _R())
    out = tmp_path / "p.pdf"
    r = runner.invoke(proposte_cmd.proposte_app, ["pdf", "p1", "--a4", "-o", str(out)])
    assert r.exit_code == 0, r.output
    assert out.read_bytes().startswith(b"%PDF")
    assert gw.calls[0] == ("proposals.export_pdf", {"proposal_id": "p1", "format": "a4"})
    r = runner.invoke(proposte_cmd.proposte_app, ["pdf", "p1"])
    assert "https://storage/x.pdf" in r.output
    r = runner.invoke(proposte_cmd.proposte_app, ["stato", "j3"])
    assert r.exit_code == 0 and "done" in r.output


def test_pdf_nao_pronto_e_erro_da_api(monkeypatch):
    from lovarch_cli.ai import AiGatewayError

    gw = _FakeGw({"proposals.export_pdf": [{"ok": True, "job_id": "j4"}], "proposals.status": [{"status": "failed", "error": "render_failed"}]})
    _patch(monkeypatch, gw)
    r = runner.invoke(proposte_cmd.proposte_app, ["pdf", "p1"])
    assert r.exit_code == 1 and "render_failed" in r.output

    class _Boom(_FakeGw):
        async def api(self, action, params=None):
            raise AiGatewayError("proposal_not_found")
    _patch(monkeypatch, _Boom({}))
    r = runner.invoke(proposte_cmd.proposte_app, ["pdf", "nada"])
    assert r.exit_code == 1 and "proposal_not_found" in r.output
