"""Unit tests for the engineer-ICP adversarial verifiers."""
from __future__ import annotations

import json

import pytest

from lovarch_cli.ai import AiTextResult
from lovarch_cli.verify import (
    verify_strutturale, verify_antincendio, verify_acustica, verify_energetica,
)
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


def _doc(tmp_path, txt="Relazione tecnica."):
    p = tmp_path / "doc.txt"; p.write_text(txt, encoding="utf-8"); return str(p)


async def test_strutturale_reject_missing_seismic(tmp_path):
    gw = _FakeGateway(
        {"inquadramento": {"zona_sismica": None}, "interventi": ["apertura su muro portante"]},
        {"findings": [{"area": "sismica", "severity": "critical", "reason": "inquadramento sismico assente"}], "overall": "REJECT"},
    )
    r = await verify_strutturale(gw, _doc(tmp_path))
    assert r.verdict == "REJECT"
    assert r.credits_charged == 5
    assert gw.roles == ["executor", "verifier"]


async def test_antincendio_concern(tmp_path):
    gw = _FakeGateway({"soggetta": True, "categoria": "B"},
                      {"findings": [{"area": "esodo", "severity": "concern", "reason": "vie di esodo non quotate"}]})
    r = await verify_antincendio(gw, _doc(tmp_path))
    assert r.verdict == "CONCERNS"


async def test_acustica_pass(tmp_path):
    gw = _FakeGateway({"categoria": "A", "R_w": "52"}, {"findings": [], "overall": "PASS"})
    r = await verify_acustica(gw, _doc(tmp_path))
    assert r.verdict == "PASS"


async def test_energetica_reject(tmp_path):
    gw = _FakeGateway({"zona_climatica": "E", "FER": None},
                      {"findings": [{"area": "FER", "severity": "critical", "reason": "quota rinnovabili non rispettata"}], "overall": "REJECT"})
    r = await verify_energetica(gw, _doc(tmp_path))
    assert r.verdict == "REJECT"


async def test_empty_doc_raises(tmp_path):
    p = tmp_path / "e.txt"; p.write_text("  ", encoding="utf-8")
    with pytest.raises(NormativaError):
        await verify_strutturale(_FakeGateway({}, {}), str(p))
