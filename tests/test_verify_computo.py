"""Unit tests for verify_computo (deterministic, no LLM)."""
from __future__ import annotations

import json

import httpx
import pytest

from lovarch_cli.verify.computo import verify_computo, ComputoError

_PREZZARI = [
    {"codice": "1.A.01.01.001", "prezzo": 18.5, "unita": "m²", "descrizione": "Demolizione"},
    {"codice": "3.A.02.01.001", "prezzo": 95.0, "unita": "m²", "descrizione": "Parquet"},
]


class _FakeSession:
    def __init__(self, rows):
        self._rows = rows

    async def request(self, method, path, *, params=None, **kwargs):
        return httpx.Response(200, json=self._rows, request=httpx.Request(method, "http://x" + path))


def _write(tmp_path, name, content):
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


async def test_computo_pass_within_tolerance(tmp_path):
    f = _write(tmp_path, "c.json", json.dumps([
        {"codice": "1.A.01.01.001", "quantita": 10, "prezzo_unitario": 19.0, "unita": "m²"},
        {"codice": "3.A.02.01.001", "quantita": 20, "prezzo_unitario": 98.0, "unita": "m²"},
    ]))
    r = await verify_computo(_FakeSession(_PREZZARI), f, region="Lombardia")
    assert r.verdict == "PASS"
    assert r.stats["voci_verificate"] == 2
    assert r.stats["prezzi_fuori_tolleranza"] == 0


async def test_computo_flags_out_of_range_and_unknown(tmp_path):
    f = _write(tmp_path, "c.json", json.dumps([
        {"codice": "1.A.01.01.001", "quantita": 10, "prezzo_unitario": 40.0, "unita": "m²"},  # +116%
        {"codice": "9.Z.99", "quantita": 1, "prezzo_unitario": 10.0},                          # unknown
    ]))
    r = await verify_computo(_FakeSession(_PREZZARI), f, region="Lombardia")
    assert r.verdict == "CONCERNS"
    assert r.stats["prezzi_fuori_tolleranza"] == 1
    assert r.stats["codici_sconosciuti"] == 1


async def test_computo_unit_mismatch(tmp_path):
    f = _write(tmp_path, "c.csv", "codice,quantita,prezzo_unitario,unita\n1.A.01.01.001,5,18.5,cad\n")
    r = await verify_computo(_FakeSession(_PREZZARI), f, region="Lombardia")
    assert r.stats["unita_incoerenti"] == 1


async def test_computo_no_prezzario_raises(tmp_path):
    f = _write(tmp_path, "c.json", json.dumps([{"codice": "x", "quantita": 1, "prezzo_unitario": 1}]))
    with pytest.raises(ComputoError):
        await verify_computo(_FakeSession([]), f, region="Sicilia")


async def test_computo_missing_file(tmp_path):
    r = await verify_computo(_FakeSession(_PREZZARI), tmp_path / "nope.json")
    assert r.verdict == "REJECT"


async def test_computo_offline_bundled_lombardia(tmp_path):
    """Without a session, verify_computo uses the bundled Lombardia prezzario."""
    import json as _json
    f = tmp_path / "c.json"
    # usa um codice real do prezzario bundled (1.A.01.01.001 = demolizione)
    f.write_text(_json.dumps([
        {"codice": "1.A.01.01.001", "quantita": 10, "prezzo_unitario": 19.0, "unita": "m²"},
    ]), encoding="utf-8")
    r = await verify_computo(None, f, region="Lombardia")   # session=None → offline
    assert r.stats["voci_verificate"] == 1
    assert "offline" in r.stats["prezzario"]
    assert r.verdict in ("PASS", "CONCERNS")


async def test_computo_offline_unknown_region_raises(tmp_path):
    import json as _json
    f = tmp_path / "c.json"
    f.write_text(_json.dumps([{"codice": "x", "quantita": 1, "prezzo_unitario": 1}]), encoding="utf-8")
    with pytest.raises(ComputoError):
        await verify_computo(None, f, region="Sicilia")   # não bundled, sem sessão
