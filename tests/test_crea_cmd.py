"""Unit tests for `lovarch crea` / `lovarch aggiorna` (cli-write)."""
from __future__ import annotations

import httpx
import pytest

from lovarch_cli.ai import AiGatewayError, LovarchAiGateway


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


async def test_write_posts_action_and_params_to_cli_write():
    session = _FakeSession(_resp(200, {"ok": True, "action": "create_lead", "data": {"id": "abc-123"}}))
    gateway = LovarchAiGateway(session)

    result = await gateway.write("create_lead", name="Mario Verdi", email="m@verdi.it")

    assert result["data"]["id"] == "abc-123"
    assert session.last_call["path"] == "/functions/v1/cli-write"
    assert session.last_call["json"] == {
        "action": "create_lead", "name": "Mario Verdi", "email": "m@verdi.it",
    }


async def test_write_surfaces_missing_field_hint():
    """O server devolve QUAL campo falta — o utente tem de vê-lo."""
    session = _FakeSession(_resp(400, {
        "ok": False, "error": "missing_field", "field": "value",
        "hint": "Campo obbligatorio mancante: value.",
    }))
    gateway = LovarchAiGateway(session)

    with pytest.raises(AiGatewayError) as exc:
        await gateway.write("create_financial_transaction", description="x")

    assert "value" in str(exc.value)


async def test_write_surfaces_error_without_hint_with_field():
    session = _FakeSession(_resp(400, {"ok": False, "error": "missing_field", "field": "name"}))
    gateway = LovarchAiGateway(session)

    with pytest.raises(AiGatewayError) as exc:
        await gateway.write("create_lead")

    assert "campo: name" in str(exc.value)


async def test_write_rate_limited_is_reported():
    session = _FakeSession(_resp(429, {
        "ok": False, "error": "rate_limited", "retry_after_seconds": 60,
        "hint": "Limite di 120 scritture/ora raggiunto. Riprova tra 60s.",
    }))
    gateway = LovarchAiGateway(session)

    with pytest.raises(AiGatewayError) as exc:
        await gateway.write("create_lead", name="X")

    assert "120 scritture/ora" in str(exc.value)


def test_crea_app_exposes_every_write_action():
    """Os 11 comandos do registry têm de existir na CLI (senão a ação fica órfã)."""
    from lovarch_cli.commands.crea_cmd import aggiorna_app, crea_app

    crea = {c.name for c in crea_app.registered_commands}
    assert crea == {
        "lead", "task", "proposta", "contratto", "progetto", "fornitore",
        "spesa", "entrata", "categoria", "audience", "campagna",
    }
    assert {c.name for c in aggiorna_app.registered_commands} == {"lead-stato"}


def test_empty_options_are_not_sent():
    """Campo não informado != string vazia: o registry trata os dois diferente.

    `''` passaria a validação `!p.name` do lado errado e gravaria vazio no DB.
    """
    from lovarch_cli.commands.crea_cmd import _clean

    assert _clean({
        "name": "Mario", "email": None, "phone": "",
        "project_type": "ristrutturazione", "notes": None,
    }) == {"name": "Mario", "project_type": "ristrutturazione"}

    # zero é valor legítimo (importo 0 tem de chegar ao server e ser rifiutato lá,
    # não sumir silenciosamente no cliente)
    assert _clean({"value": 0}) == {"value": 0}
