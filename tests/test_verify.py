"""Unit tests for lovarch verifica (misure DXF + normativa adversarial)."""
from __future__ import annotations

import json

import pytest

from lovarch_cli.ai import AiTextResult
from lovarch_cli.verify import verify_misure, verify_normativa
from lovarch_cli.verify.normativa import NormativaError, _parse_json, scan_canonical


# ── misure (deterministic, free) ──────────────────────────────────────────

def _make_dxf(path, *, good: bool):
    import ezdxf

    doc = ezdxf.new()
    msp = doc.modelspace()
    if good:
        layers = ["CAD-A-WALL", "CAD-A-WALL-EXT", "CAD-A-DOOR", "CAD-A-WIND",
                  "CAD-A-DIM", "CAD-A-TEXT", "CAD-A-SYMB", "CAD-A-FURN", "CAD-A-CART"]
        for name in layers:
            doc.layers.add(name)
            msp.add_line((0, 0), (1, 1), dxfattribs={"layer": name})
        for i, room in enumerate(["INGRESSO", "SOGGIORNO", "CUCINA", "STUDIO",
                                  "CAMERA", "BAGNO", "LAVANDERIA"]):
            msp.add_text(f"{room} 12.5 m2", dxfattribs={"layer": "CAD-A-TEXT"}).set_placement((i, 0))
        cart = "PROGETTO Villa X · CLIENTE Rossi · ARCHITETTO Verdi · SCALA 1:100 · DATA 03/07/2026"
        msp.add_text(cart, dxfattribs={"layer": "CAD-A-CART"}).set_placement((0, 5))
    else:
        doc.layers.add("Layer1")
        msp.add_line((0, 0), (1, 1), dxfattribs={"layer": "Layer1"})
        msp.add_text("STANZA", dxfattribs={"layer": "Layer1"}).set_placement((0, 0))
    doc.saveas(str(path))


def test_misure_good_dxf_passes(tmp_path):
    p = tmp_path / "good.dxf"
    _make_dxf(p, good=True)
    report = verify_misure(p)
    assert report.verdict == "PASS", report.findings
    assert report.stats["iso_layers_present"] == 9


def test_misure_bad_dxf_rejected(tmp_path):
    p = tmp_path / "bad.dxf"
    _make_dxf(p, good=False)
    report = verify_misure(p)
    assert report.verdict == "REJECT"
    assert len(report.findings) >= 2  # layers + rooms + cartiglio


def test_misure_missing_file():
    report = verify_misure("/nonexistent/x.dxf")
    assert report.verdict == "REJECT"


# ── normativa (adversarial two-model) ──────────────────────────────────────

def test_scan_canonical():
    text = "Ai sensi del DPR 380/2001 e della UNI 11337, nel rispetto del GDPR (2016/679)."
    found = scan_canonical(text)
    assert "DPR 380/2001" in found and "UNI 11337" in found and "GDPR" in found


def test_parse_json_with_fences():
    assert _parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert _parse_json('Ecco il JSON: {"b": 2} fine.') == {"b": 2}
    with pytest.raises(NormativaError):
        _parse_json("niente json qui")


class _FakeGateway:
    """Returns extraction then refutation, recording roles used."""

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


async def test_normativa_refuted_citation_rejects(tmp_path):
    doc = tmp_path / "capitolato.md"
    doc.write_text("La CILA è regolata dal DPR 380/2001 art. 99. Si applica la UNI 11337.")
    gw = _FakeGateway(
        {"citations": [
            {"reference": "DPR 380/2001", "article": "99", "claim": "regola le CILA"},
            {"reference": "UNI 11337", "article": None, "claim": "gestione digitale"},
        ]},
        {"verdicts": [
            {"reference": "DPR 380/2001 art. 99", "status": "refuted",
             "reason": "l'art. 99 riguarda il cemento armato, non le CILA"},
            {"reference": "UNI 11337", "status": "ok", "reason": "corretto"},
        ]},
    )
    report = await verify_normativa(gw, doc)
    assert report.verdict == "REJECT"
    assert gw.roles == ["executor", "verifier"]  # adversarial split
    assert report.credits_charged == 5
    assert "DPR 380/2001" in report.canonical_found


async def test_normativa_all_ok_passes(tmp_path):
    doc = tmp_path / "doc.md"
    doc.write_text("Riferimento: NTC 2018 (DM 17/01/2018) per le strutture.")
    gw = _FakeGateway(
        {"citations": [{"reference": "NTC 2018", "article": None, "claim": "strutture"}]},
        {"verdicts": [{"reference": "NTC 2018", "status": "ok", "reason": "corretto"}]},
    )
    report = await verify_normativa(gw, doc)
    assert report.verdict == "PASS"


async def test_normativa_no_citations_concerns(tmp_path):
    doc = tmp_path / "doc.md"
    doc.write_text("Un documento senza alcun riferimento.")
    gw = _FakeGateway({"citations": []}, {"verdicts": []})
    report = await verify_normativa(gw, doc)
    assert report.verdict == "CONCERNS"
    assert report.credits_charged == 2  # only the extract call ran


async def test_normativa_missing_file():
    with pytest.raises(NormativaError):
        await verify_normativa(_FakeGateway({}, {}), "/nope/x.pdf")


# ── contratto (adversarial) ────────────────────────────────────────────────

async def test_contratto_private_client_concern_not_reject(tmp_path):
    from lovarch_cli.verify import verify_contratto

    doc = tmp_path / "contratto.md"
    doc.write_text("Committente privato. Compenso EUR 11.000 (parametri: 19.700).")
    gw = _FakeGateway(
        {"sections_present": ["oggetto", "compenso"], "sections_missing": ["privacy/GDPR"],
         "client_type": "privato", "compenso": {"amount": "11000", "justification": None}},
        {"findings": [
            {"area": "compenso", "severity": "concern",
             "reason": "privato: parametri orientativi (QN_007), scostamento non motivato"},
            {"area": "completezza", "severity": "concern", "reason": "manca GDPR"},
        ], "overall": "CONCERNS"},
    )
    report = await verify_contratto(gw, str(doc))
    assert report.verdict == "CONCERNS"
    assert gw.roles == ["executor", "verifier"]
    assert report.credits_charged == 5
    assert all(f["severity"] != "critical" for f in report.findings)


async def test_contratto_strong_counterparty_reject(tmp_path):
    from lovarch_cli.verify import verify_contratto

    doc = tmp_path / "contratto-pa.md"
    doc.write_text("Committente: Comune di Milano. Compenso sotto parametri.")
    gw = _FakeGateway(
        {"sections_present": [], "sections_missing": [], "client_type": "pa",
         "compenso": {"amount": "11000", "justification": None}},
        {"findings": [{"area": "compenso", "severity": "critical",
                       "reason": "contraente forte: L.49/2023 applicabile"}],
         "overall": "REJECT"},
    )
    report = await verify_contratto(gw, str(doc))
    assert report.verdict == "REJECT"
