"""Deterministic 2D CAD floor-plan generator (DXF via ezdxf).

Produces a real .dxf an architect can open in AutoCAD/BricsCAD, laid out on the
9 ISO layers the platform expects (CAD-A-WALL, -WALL-EXT, -DOOR, -WIND, -DIM,
-TEXT, -SYMB, -FURN, -CART) with room labels and a CNAPPC cartiglio. No AI, no
credits — the geometry is computed. It round-trips: a plan generated here passes
`lovarch verifica misure`.

Quality (2026-07-05): real linear DIMENSION entities (extension lines + arrows,
not just text), double-line walls with thickness, door swing arcs, double-line
windows with sill, an overall dimension chain, a scale bar and a bordered
cartiglio grid — captures the "editable professional DWG" value without the paid
Design Automation round-trip.

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

WALL_T = 0.10  # interior wall half-thickness (m) → double-line walls read as real
DIM_TXT = 0.18  # dimension text height (m)

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

    # A dimension style scaled for a plan drawn in metres (small text + arrows).
    dimstyle = doc.dimstyles.get("Standard")
    dimstyle.dxf.dimtxt = DIM_TXT
    dimstyle.dxf.dimasz = 0.12
    dimstyle.dxf.dimexe = 0.06
    dimstyle.dxf.dimexo = 0.05
    dimstyle.dxf.dimdec = 2

    def rect(x0, y0, x1, y1, layer):
        msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True,
                           dxfattribs={"layer": layer})

    def hdim(x0, x1, y, text_gap):
        """Horizontal linear dimension between x0..x1 placed below at y-text_gap."""
        d = msp.add_linear_dim(base=(x0, y - text_gap), p1=(x0, y), p2=(x1, y),
                               dxfattribs={"layer": "CAD-A-DIM"})
        d.render()

    def vdim(x, y0, y1, text_gap):
        """Vertical linear dimension between y0..y1 placed left at x-text_gap."""
        d = msp.add_linear_dim(base=(x - text_gap, y0), p1=(x, y0), p2=(x, y1),
                               angle=90, dxfattribs={"layer": "CAD-A-DIM"})
        d.render()

    x = 0.0
    gap = 2 * WALL_T  # shared double-line wall between rooms
    max_h = 0.0
    placed = []
    total_area = 0.0
    for spec in specs:
        label = _norm_label(str(spec.get("name", "")))
        w = float(spec.get("width_m", 3.0))
        h = float(spec.get("height_m", 3.0))
        # Double-line interior walls: inner room boundary + thickness offset.
        rect(x, 0, x + w, h, "CAD-A-WALL")
        rect(x - WALL_T, -WALL_T, x + w + WALL_T, h + WALL_T, "CAD-A-WALL")
        # Door: opening in the bottom wall + swing arc (quarter circle) + leaf.
        dx = x + w / 2
        msp.add_line((dx - 0.4, 0), (dx - 0.4, 0.02), dxfattribs={"layer": "CAD-A-DOOR"})
        msp.add_arc(center=(dx - 0.4, 0), radius=0.8, start_angle=0, end_angle=90,
                    dxfattribs={"layer": "CAD-A-DOOR"})
        msp.add_line((dx - 0.4, 0), (dx - 0.4, 0.8), dxfattribs={"layer": "CAD-A-DOOR"})
        # Window: double line on the top wall with a sill tick.
        msp.add_line((dx - 0.6, h - 0.03), (dx + 0.6, h - 0.03), dxfattribs={"layer": "CAD-A-WIND"})
        msp.add_line((dx - 0.6, h + 0.03), (dx + 0.6, h + 0.03), dxfattribs={"layer": "CAD-A-WIND"})
        # Furniture placeholder (centered box).
        rect(x + w * 0.35, h * 0.35, x + w * 0.65, h * 0.65, "CAD-A-FURN")
        # Room label + area.
        area = w * h
        total_area += area
        msp.add_text(f"{label} {area:.1f} mq",
                     dxfattribs={"layer": "CAD-A-TEXT", "height": 0.25}
                     ).set_placement((x + 0.2, h / 2))
        # Real per-room dimensions: width below, height on the left of the first room.
        hdim(x, x + w, 0, 0.9)
        placed.append((label, w, h, x))
        x += w + gap
        max_h = max(max_h, h)

    total_w = x - gap
    # Height dimension on the tallest room (left side) + overall width chain.
    if placed:
        first_x = placed[0][3]
        vdim(first_x, 0, max_h, 0.9)
    hdim(0, total_w, 0, 1.8)  # overall width chain below the per-room dims
    # Exterior boundary (thick double line).
    rect(-WALL_T, -WALL_T, total_w + WALL_T, max_h + WALL_T, "CAD-A-WALL-EXT")
    rect(-2 * WALL_T, -2 * WALL_T, total_w + 2 * WALL_T, max_h + 2 * WALL_T, "CAD-A-WALL-EXT")

    # North arrow symbol.
    nax = total_w + 1.2
    msp.add_line((nax, 0), (nax, 1.2), dxfattribs={"layer": "CAD-A-SYMB"})
    msp.add_line((nax, 1.2), (nax - 0.15, 0.9), dxfattribs={"layer": "CAD-A-SYMB"})
    msp.add_line((nax, 1.2), (nax + 0.15, 0.9), dxfattribs={"layer": "CAD-A-SYMB"})
    msp.add_text("N", dxfattribs={"layer": "CAD-A-SYMB", "height": 0.3}).set_placement((nax - 0.15, 1.3))

    # Scale bar (0..5 m, 1 m ticks) on the SYMB layer.
    sbx, sby = 0.0, max_h + 1.0
    msp.add_line((sbx, sby), (sbx + 5, sby), dxfattribs={"layer": "CAD-A-SYMB"})
    for i in range(6):
        msp.add_line((sbx + i, sby), (sbx + i, sby + 0.15), dxfattribs={"layer": "CAD-A-SYMB"})
    msp.add_text("0        5 m", dxfattribs={"layer": "CAD-A-SYMB", "height": 0.2}
                 ).set_placement((sbx, sby + 0.25))

    # Cartiglio CNAPPC (title block) — bordered grid, all required fields on CAD-A-CART.
    # Placed well below the dimension chains; two comfortably-spaced columns + divider.
    cw, ch = 11.0, 2.6
    col2 = 5.9
    cy = -(1.8 + 0.9 + ch)  # below the overall dimension chain (y ≈ -1.8) with margin
    rect(0, cy, cw, cy + ch, "CAD-A-CART")          # outer frame
    rect(0.08, cy + 0.08, cw - 0.08, cy + ch - 0.08, "CAD-A-CART")  # inner frame
    msp.add_line((0, cy + ch - 0.55), (cw, cy + ch - 0.55), dxfattribs={"layer": "CAD-A-CART"})  # header rule
    msp.add_line((col2 - 0.3, cy), (col2 - 0.3, cy + ch - 0.55), dxfattribs={"layer": "CAD-A-CART"})  # column divider
    msp.add_text("LOVARCH - TAVOLA DI PROGETTO",
                 dxfattribs={"layer": "CAD-A-CART", "height": 0.28}
                 ).set_placement((0.25, cy + ch - 0.42))
    col1_lines = [f"PROGETTO: {progetto}", f"CLIENTE: {cliente}", f"ARCHITETTO: {architetto}"]
    col2_lines = [f"SCALA: {scala}", f"DATA: {data or 'in redazione'}", f"SUPERFICIE: {total_area:.1f} mq"]
    for i, line in enumerate(col1_lines):
        msp.add_text(line, dxfattribs={"layer": "CAD-A-CART", "height": 0.2}
                     ).set_placement((0.25, cy + ch - 1.05 - i * 0.45))
    for i, line in enumerate(col2_lines):
        msp.add_text(line, dxfattribs={"layer": "CAD-A-CART", "height": 0.2}
                     ).set_placement((col2, cy + ch - 1.05 - i * 0.45))

    out = Path(out_path).expanduser()
    doc.saveas(str(out))
    return FloorplanResult(
        path=str(out),
        rooms=[{"label": l, "width_m": w, "height_m": h} for l, w, h, _ in placed],
        total_area_m2=round(total_area, 1),
        layers=len(ISO_LAYERS),
    )
