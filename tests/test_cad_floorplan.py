"""Unit tests for the DXF floor-plan generator (round-trips through verify)."""
from __future__ import annotations

from lovarch_cli.cad import generate_floorplan
from lovarch_cli.verify import verify_misure


def test_standard_plan_passes_verify(tmp_path):
    out = tmp_path / "p.dxf"
    r = generate_floorplan(None, out_path=out, progetto="P", cliente="C", architetto="A")
    assert out.is_file()
    assert r.layers == 9
    assert len(r.rooms) == 7
    assert r.total_area_m2 > 0
    rep = verify_misure(str(out))
    assert rep.verdict == "PASS"
    assert rep.stats["iso_layers_present"] == 9


def test_custom_rooms(tmp_path):
    out = tmp_path / "c.dxf"
    rooms = [{"name": "soggiorno", "width_m": 6, "height_m": 5},
             {"name": "cucina", "width_m": 3, "height_m": 3}]
    r = generate_floorplan(rooms, out_path=out)
    assert len(r.rooms) == 2
    assert r.rooms[0]["label"] == "SOGGIORNO"  # alias normalized
    assert abs(r.total_area_m2 - 39.0) < 0.1


def test_label_aliases(tmp_path):
    out = tmp_path / "a.dxf"
    r = generate_floorplan([{"name": "living", "width_m": 4, "height_m": 4}], out_path=out)
    assert r.rooms[0]["label"] == "SOGGIORNO"
