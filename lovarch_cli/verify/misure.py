"""verifica misure — deterministic DXF checks (UNI ISO 5457 / CNAPPC).

Ported from the squad's Tier-2 @quality-misure verifier (pipeline_runner Q1) so
any professional can check a drawing standalone, without running the dossier.
Pure code — no credits are consumed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ISO_LAYERS = {
    "CAD-A-WALL", "CAD-A-WALL-EXT", "CAD-A-DOOR", "CAD-A-WIND", "CAD-A-DIM",
    "CAD-A-TEXT", "CAD-A-SYMB", "CAD-A-FURN", "CAD-A-CART",
}
ROOM_LABELS = {"INGRESSO", "SOGGIORNO", "CUCINA", "STUDIO", "CAMERA", "BAGNO", "LAVANDERIA"}
CARTIGLIO_REQUIRED = ["PROGETTO", "CLIENTE", "ARCHITETTO", "SCALA", "DATA"]


@dataclass
class MisureReport:
    verdict: str                 # PASS | CONCERNS | REJECT
    findings: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def verify_misure(dxf_path: str | Path) -> MisureReport:
    """Check a DXF for ISO layer compliance, room labels and CNAPPC cartiglio."""
    path = Path(dxf_path).expanduser()
    findings: list[str] = []
    stats: dict = {}

    if not path.is_file():
        return MisureReport(verdict="REJECT", findings=[f"file non trovato: {path}"])

    try:
        import ezdxf
        doc = ezdxf.readfile(str(path))
    except Exception as exc:  # noqa: BLE001 — parse errors are the finding
        return MisureReport(verdict="REJECT", findings=[f"DXF non leggibile: {str(exc)[:120]}"])

    msp = doc.modelspace()
    layers = {e.dxf.layer for e in msp}
    stats["entities"] = len(msp)
    stats["layers"] = sorted(layers)

    # 1. ISO layer compliance (UNI ISO 5457 naming convention)
    iso_ok = ISO_LAYERS & layers
    stats["iso_layers_present"] = len(iso_ok)
    if len(iso_ok) < 6:
        findings.append(
            f"conformità layer ISO: solo {len(iso_ok)}/9 layer standard presenti "
            f"(attesi: {', '.join(sorted(ISO_LAYERS - layers))} mancanti)"
        )

    # 2. Room labels
    texts = [e for e in msp if e.dxftype() in ("TEXT", "MTEXT")]
    rooms: set[str] = set()
    for e in texts:
        try:
            t = (e.dxf.text if e.dxftype() == "TEXT" else e.text).upper()
        except Exception:  # noqa: BLE001
            continue
        for room in ROOM_LABELS:
            if room in t:
                rooms.add(room)
    stats["room_labels_found"] = sorted(rooms)
    missing_rooms = ROOM_LABELS - rooms
    if len(missing_rooms) > 1:
        findings.append(f"etichette ambienti mancanti: {', '.join(sorted(missing_rooms))}")

    # 3. Cartiglio CNAPPC
    cart_text = " ".join(
        (e.dxf.text if e.dxftype() == "TEXT" else e.text).upper()
        for e in texts
        if "CART" in str(e.dxf.layer).upper()
    )
    cart_missing = [k for k in CARTIGLIO_REQUIRED if k not in cart_text]
    if cart_missing:
        findings.append(f"cartiglio CNAPPC incompleto: mancano {', '.join(cart_missing)}")

    verdict = "PASS" if not findings else ("CONCERNS" if len(findings) == 1 else "REJECT")
    return MisureReport(verdict=verdict, findings=findings, stats=stats)
