"""signup: il token esce solo dopo il codice ricevuto via email (falla F16 lato server).

Il server (cli-signup) ora risponde ``verification_required`` senza token; il CLI chiede
il codice e lo conferma su cli-signup-verify. Nessuna chiamata di rete reale.
"""
from __future__ import annotations

from typing import Any

import pytest
from typer.testing import CliRunner

from lovarch_cli.api import ApiClient, LovarchApiError
from lovarch_cli.commands import signup as signup_mod
from lovarch_cli.commands.signup import normalize_code, verify_email_code

TOKEN_RESPONSE = {
    "ok": True,
    "lead_id": "lead-1",
    "user_id": "user-1",
    "free_token": "11111111-2222-3333-4444-555555555555",
    "language": "it",
    "upgrade_url": "https://app.lovarch.com/settings/credits",
}


class FakeApi:
    """invoke_ef falso: accetta solo ``good_code`` su cli-signup-verify."""

    def __init__(self, good_code: str = "123456", signup_response: dict[str, Any] | None = None):
        self.good_code = good_code
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.signup_response = signup_response or {
            "ok": True,
            "verification_required": True,
            "expires_in_seconds": 900,
        }

    async def invoke_ef(self, name: str, body: dict[str, Any], bearer_token: str | None = None):
        self.calls.append((name, body))
        if name == "cli-signup":
            return self.signup_response
        if name == "cli-signup-verify":
            if body["code"] == self.good_code:
                return TOKEN_RESPONSE
            raise LovarchApiError("Codice non valido", status_code=400, error_code="invalid_code")
        raise AssertionError(f"unexpected EF {name}")


def answers(*values: str):
    it = iter(values)
    return lambda _lang: next(it)


def test_normalize_code_accepts_spaces_and_dashes_only_six_digits():
    assert normalize_code("123456") == "123456"
    assert normalize_code(" 123 456 ") == "123456"
    assert normalize_code("123-456") == "123456"
    assert normalize_code("12345") is None
    assert normalize_code("1234567") is None
    assert normalize_code("12a456") is None
    assert normalize_code("") is None


def test_verify_returns_token_on_right_code():
    api = FakeApi()
    out = verify_email_code(api, "a@b.it", "it", ask_code=answers("123456"))  # type: ignore[arg-type]
    assert out["free_token"] == TOKEN_RESPONSE["free_token"]
    assert api.calls == [("cli-signup-verify", {"email": "a@b.it", "code": "123456", "language": "it"})]


def test_bad_format_does_not_reach_server_nor_spend_attempts():
    api = FakeApi()
    out = verify_email_code(api, "a@b.it", "pt", ask_code=answers("abc", "12", "123 456"))  # type: ignore[arg-type]
    assert out["ok"] is True
    assert len(api.calls) == 1


def test_wrong_code_retries_then_succeeds():
    api = FakeApi()
    out = verify_email_code(api, "a@b.it", "en", ask_code=answers("000000", "111111", "123456"))  # type: ignore[arg-type]
    assert out["lead_id"] == "lead-1"
    assert len(api.calls) == 3


def test_five_wrong_codes_stop_with_invalid_code():
    api = FakeApi()
    with pytest.raises(LovarchApiError) as exc:
        verify_email_code(api, "a@b.it", "es", ask_code=answers(*["000000"] * 10))  # type: ignore[arg-type]
    assert exc.value.error_code == "invalid_code"
    assert len(api.calls) == 5  # stesso limite del server


def test_other_server_errors_are_not_retried():
    class Boom(FakeApi):
        async def invoke_ef(self, name, body, bearer_token=None):
            self.calls.append((name, body))
            raise LovarchApiError("Hai già un account", status_code=400, error_code="existing_premium_account")

    api = Boom()
    with pytest.raises(LovarchApiError) as exc:
        verify_email_code(api, "a@b.it", "it", ask_code=answers("123456", "123456"))  # type: ignore[arg-type]
    assert exc.value.error_code == "existing_premium_account"
    assert len(api.calls) == 1


def _run_signup(monkeypatch, fake: FakeApi, stdin: str):
    saved: list[Any] = []
    monkeypatch.setattr(ApiClient, "invoke_ef", lambda self, name, body, bearer_token=None: fake.invoke_ef(name, body))
    monkeypatch.setattr(signup_mod, "save_credentials", lambda creds: saved.append(creds) or "/tmp/creds.json")
    app = __import__("typer").Typer()
    app.command()(signup_mod.signup_command)
    result = CliRunner().invoke(app, ["--yes", "--lang", "it"], input=stdin)
    return result, saved


SIGNUP_INPUT = "it\nMario Rossi\nmario@studio.it\n+390000000000\nIT\n"


def test_signup_command_sends_verification_flag_and_saves_token_after_code(monkeypatch):
    fake = FakeApi()
    result, saved = _run_signup(monkeypatch, fake, SIGNUP_INPUT + "123456\n")
    assert result.exit_code == 0, result.output
    name, body = fake.calls[0]
    assert name == "cli-signup"
    assert body["verification"] == "email_code"
    assert fake.calls[1][0] == "cli-signup-verify"
    assert saved and saved[0].free_token == TOKEN_RESPONSE["free_token"]


def test_signup_command_saves_nothing_when_code_never_confirmed(monkeypatch):
    fake = FakeApi()
    result, saved = _run_signup(monkeypatch, fake, SIGNUP_INPUT + "000000\n" * 5)
    assert result.exit_code == 1
    assert saved == []


def test_signup_command_still_accepts_server_that_returns_token_directly(monkeypatch):
    fake = FakeApi(signup_response=TOKEN_RESPONSE)
    result, saved = _run_signup(monkeypatch, fake, SIGNUP_INPUT)
    assert result.exit_code == 0, result.output
    assert [c[0] for c in fake.calls] == ["cli-signup"]
    assert saved[0].free_token == TOKEN_RESPONSE["free_token"]
