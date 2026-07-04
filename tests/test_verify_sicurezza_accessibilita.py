"""Unit tests for verify_sicurezza and verify_accessibilita (adversarial)."""
from __future__ import annotations

import json

import pytest

from lovarch_cli.ai import AiTextResult
from lovarch_cli.verify import verify_sicurezza, verify_accessibilita
from lovarch_cli.verify.normativa import NormativaError


class _FakeGateway:
    def __init__(self, extract, refute):
        self._r = [
            AiTextResult(text=json.dumps(extract), model="anthropic/claude-sonnet-5",
                         input_tokens=10, output_tokens=20, credits_charged=2, balance=98, is_admin=False),
            AiTextResult(text=json.dumps(refute), model="anthropic/claude-opus-4.8",
                         input_tokens=8, output_tokens=15, credits_charged=3, balance=95, is_admin=False),
        ]
        self.roles = []

    async def generate_text(self, prompt, *, role="executor", **kw):
        self.roles.append(role)
        return self._r[len(self.roles) - 1]


def _doc(tmp_path, txt="Piano di sicurezza cantiere."):
    p = tmp_path / "doc.txt"; p.write_text(txt, encoding="utf-8"); return str(p)


async def test_sicurezza_reject_missing_csp(tmp_path):
    gw = _FakeGateway(
        {"tipo": "PSC", "soggetti": {"CSP": None, "CSE": None, "imprese": ["A", "B"]}, "rischi_per_fase": False},
        {"findings": [{"area": "coordinamento", "severity": "critical", "reason": "CSP/CSE non nominati con più imprese"}], "overall": "REJECT"},
    )
    r = await verify_sicurezza(gw, _doc(tmp_path))
    assert r.verdict == "REJECT"
    assert r.tipo == "PSC"
    assert r.credits_charged == 5
    assert gw.roles == ["executor", "verifier"]


async def test_accessibilita_concern_door_too_narrow(tmp_path):
    gw = _FakeGateway(
        {"livello": "visitabilità", "parametri": {"porte_cm": "75", "servizio_accessibile": False}},
        {"findings": [{"area": "porte", "severity": "concern", "reason": "luce netta 75<80 cm"}]},
    )
    r = await verify_accessibilita(gw, _doc(tmp_path))
    assert r.verdict == "CONCERNS"
    assert r.livello == "visitabilità"


async def test_sicurezza_empty_raises(tmp_path):
    p = tmp_path / "e.txt"; p.write_text("  ", encoding="utf-8")
    with pytest.raises(NormativaError):
        await verify_sicurezza(_FakeGateway({}, {}), str(p))
