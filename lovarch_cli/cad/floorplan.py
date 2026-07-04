"""Deterministic 2D CAD floor-plan generator (DXF via ezdxf).

Produces a real .dxf an architect can open in AutoCAD/BricsCAD, laid out on the
9 ISO layers the platform expects (CAD-A-WALL, -WALL-EXT, -DOOR, -WIND, -DIM,
-TEXT, -SYMB, -FURN, -CART) with room labels and a CNAPPC cartiglio. No AI, no
credits — the geometry is computed. It round-trips: a plan generated here passes
`lovarch verifica misure`.

Input: a list of rooms {name, width_m, height_m}. Rooms are packed left-to-right
in a single band (simple, predictable). Names are matched to the standard Italian
room labels for the cartiglio/verify.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ISO_LAYERS = {
    "CAD-A-WALL": 7, "CAD-A-WALL-EXT": 7, "CAD-A-DOOR": 3, "CAD-A-WIND": 4,
    "CAD-A-DIM": 2, "CAD-A-TEXT": 7, "CAD-A-SYMB": 1, "CAD-A-FURN": 8,
    "CAD-A-CART": 7,
}

STANDARD_ROOMS = [
    ("INGRESSO", 2.0, 3.0), ("SOGGIORNO", 5.0, 4.0), ("CUCINA", 3.0, 3.0),
    ("STUDIO", 3.0, 3.0), ("CAMERA", 4.0, 3.5), ("BAGNO", 2.0, 2.5),
    ("LAVANDERIA", 2.0, 2.0),
]

_LABEL_ALIASES = {
    "ingresso": "INGRESSO", "entrata": "INGRESSO", "soggiorno": "SOGGIORNO",
    "living": "SOGGIORNO", "salotto": "SOGGIORNO", "cucina": "CUCINA",
    "studio": "STUDIO", "ufficio": "STUDIO", "camera": "CAMERA",
    "camera da letto": "CAMERA", "bagno": "BAGNO", "wc": "BAGNO",
    "lavanderia": "LAVANDERIA",
}


@dataclass
class FloorplanResult:
    path: str
    rooms: list = field(default_factory=list)
    total_area_m2: float = 0.0
    layers: int = 0


def _norm_label(name: str) -> str:
    n = (name or "").strip().lower()
    return _LABEL_ALIASES.get(n, name.strip().upper())


def generate_floorplan(
    rooms: list[dict] | None,
    *,
    out_path: str | Path,
    progetto: str = "Progetto",
    cliente: str = "Cliente",
    architetto: str = "Arch.",
    scala: str = "1:100",
    data: str = "",
) -> FloorplanResult:
    """Generate a DXF floor plan and write it to out_path."""
    import ezdxf

    specs = rooms if rooms else [{"name": n, "width_m": w, "height_m": h} for n, w, h in STANDARD_ROOMS]

    doc = ezdxf.new(setup=True)
    msp = doc.modelspace()
    for name, color in ISO_LAYERS.items():
        if name not in doc.layers:
            doc.layers.add(name, color=color)

    def rect(x0, y0, x1, y1, layer):
        msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True,
                           dxfattribs={"layer": layer})

    x = 0.0
    gap = 0.15  # wall thickness between rooms
    max_h = 0.0
    placed = []
    total_area = 0.0
    for spec in specs:
        label = _norm_label(str(spec.get("name", "")))
        w = float(spec.get("width_m", 3.0))
        h = float(spec.get("height_m", 3.0))
        # interior walls
        rect(x, 0, x + w, h, "CAD-A-WALL")
        # a door opening on the bottom wall
        dx = x + w / 2
        msp.add_line((dx - 0.4, 0), (dx + 0.4, 0), dxfattribs={"layer": "CAD-A-DOOR"})
        # a window on the top wall
        msp.add_line((dx - 0.6, h), (dx + 0.6, h), dxfattribs={"layer": "CAD-A-WIND"})
        # furniture placeholder (centered box)
        rect(x + w * 0.35, h * 0.35, x + w * 0.65, h * 0.65, "CAD-A-FURN")
        # room label + area
        area = w * h
        total_area += area
        msp.add_text(f"{label} {area:.1f} mq",
                     dxfattribs={"layer": "CAD-A-TEXT", "height": 0.25}
                     ).set_placement((x + 0.2, h / 2))
        # dimension text (simple, on DIM layer)
        msp.add_text(f"{w:.2f}", dxfattribs={"layer": "CAD-A-DIM", "height": 0.18}
                     ).set_placement((x + w / 2 - 0.3, -0.4))
        placed.append((label, w, h))
        x += w + gap
        max_h = max(max_h, h)

    total_w = x
    # exterior boundary
    rect(-0.1, -0.1, total_w, max_h + 0.1, "CAD-A-WALL-EXT")
    # north arrow symbol
    msp.add_line((total_w + 1, 0), (total_w + 1, 1.2), dxfattribs={"layer": "CAD-A-SYMB"})
    msp.add_text("N", dxfattribs={"layer": "CAD-A-SYMB", "height": 0.3}).set_placement((total_w + 0.85, 1.3))

    # Cartiglio CNAPPC (title block) — all required fields on CAD-A-CART.
    cy = -1.2
    rect(0, cy - 2.2, 8, cy, "CAD-A-CART")
    lines = [
        f"PROGETTO: {progetto}", f"CLIENTE: {cliente}", f"ARCHITETTO: {architetto}",
        f"SCALA: {scala}", f"DATA: {data or 'in redazione'}",
        f"SUPERFICIE: {total_area:.1f} mq",
    ]
    for i, line in enumerate(lines):
        msp.add_text(line, dxfattribs={"layer": "CAD-A-CART", "height": 0.22}
                     ).set_placement((0.2, cy - 0.4 - i * 0.34))

    out = Path(out_path).expanduser()
    doc.saveas(str(out))
    return FloorplanResult(
        path=str(out),
        rooms=[{"label": l, "width_m": w, "height_m": h} for l, w, h in placed],
        total_area_m2=round(total_area, 1),
        layers=len(ISO_LAYERS),
    )
