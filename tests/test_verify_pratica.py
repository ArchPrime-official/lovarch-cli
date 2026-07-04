"""Unit tests for verify_pratica (adversarial CILA/SCIA, two-model)."""
from __future__ import annotations

import json

import pytest

from lovarch_cli.ai import AiTextResult
from lovarch_cli.verify import verify_pratica
from lovarch_cli.verify.normativa import NormativaError


class _FakeGateway:
    def __init__(self, extract_payload, refute_payload):
        self._responses = [
            AiTextResult(text=json.dumps(extract_payload), model="anthropic/claude-sonnet-5",
                         input_tokens=100, output_tokens=50, credits_charged=2,
                         balance=98, is_admin=False),
            AiTextResult(text=json.dumps(refute_payload), model="anthropic/claude-opus-4.8",
                         input_tokens=80, output_tokens=60, credits_charged=3,
                         balance=95, is_admin=False),
        ]
        self.roles: list[str] = []

    async def generate_text(self, prompt, *, role="executor", **kwargs):
        self.roles.append(role)
        return self._responses[len(self.roles) - 1]


def _doc(tmp_path, txt="Pratica CILA per ristrutturazione interna."):
    p = tmp_path / "pratica.txt"
    p.write_text(txt, encoding="utf-8")
    return str(p)


async def test_pratica_reject_understated_title(tmp_path):
    gw = _FakeGateway(
        {"tipo": "CILA", "sezioni_presenti": ["intervento"], "asseverazione_presente": False,
         "intervento": "demolizione parete portante"},
        {"findings": [{"area": "titolo", "severity": "critical",
                       "reason": "intervento strutturale non copribile da CILA"}],
         "overall": "REJECT"},
    )
    r = await verify_pratica(gw, _doc(tmp_path), tipo="CILA")
    assert r.verdict == "REJECT"
    assert r.tipo == "CILA"
    assert r.credits_charged == 5
    assert gw.roles == ["executor", "verifier"]


async def test_pratica_pass(tmp_path):
    gw = _FakeGateway(
        {"tipo": "SCIA", "sezioni_presenti": ["tutto"], "asseverazione_presente": True,
         "intervento": "manutenzione straordinaria"},
        {"findings": [], "overall": "PASS"},
    )
    r = await verify_pratica(gw, _doc(tmp_path))
    assert r.verdict == "PASS"
    assert r.tipo == "SCIA"


async def test_pratica_overall_derived_from_severity(tmp_path):
    gw = _FakeGateway(
        {"tipo": "CILA", "asseverazione_presente": True},
        {"findings": [{"area": "catasto", "severity": "concern", "reason": "sub mancante"}]},
    )
    r = await verify_pratica(gw, _doc(tmp_path))
    assert r.verdict == "CONCERNS"


async def test_pratica_empty_doc_raises(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("   ", encoding="utf-8")
    gw = _FakeGateway({}, {})
    with pytest.raises(NormativaError):
        await verify_pratica(gw, str(p))
