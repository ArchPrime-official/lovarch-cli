"""
Generate sample DWG for Attico Brera demo.

Creates a realistic 120 m² floor plan in DXF format with:
- Layer ISO standard (CAD-A-WALL, CAD-A-DIM, CAD-A-DOOR, CAD-A-WIND, CAD-A-TEXT)
- Walls (perimeter + internal)
- Doors and windows as blocks
- Dimensions
- Room labels
- A1 sheet with cartiglio CNAPPC

Output: stato-attuale.dxf

Usage:
    python3 generate_attico_brera_dwg.py [output_path]

Default output: ./stato-attuale.dxf
"""
import sys
from pathlib import Path

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
except ImportError:
    sys.stderr.write(
        "ERROR: ezdxf not installed. Run: pip install ezdxf\n"
    )
    sys.exit(1)


# Layer specifications (UNI ISO standard)
LAYERS = [
    ("CAD-A-WALL", 7, "Continuous"),       # 7 = white
    ("CAD-A-WALL-EXT", 1, "Continuous"),   # 1 = red (perimeter)
    ("CAD-A-DOOR", 4, "Continuous"),       # 4 = cyan
    ("CAD-A-WIND", 5, "Continuous"),       # 5 = blue
    ("CAD-A-DIM", 3, "Continuous"),        # 3 = green
    ("CAD-A-TEXT", 2, "Continuous"),       # 2 = yellow
    ("CAD-A-SYMB", 6, "Continuous"),       # 6 = magenta
    ("CAD-A-FURN", 8, "Continuous"),       # 8 = grey
    ("CAD-A-CART", 7, "Continuous"),       # cartiglio
]


def setup_layers(doc):
    """Create all required layers."""
    for name, color, linetype in LAYERS:
        if name not in doc.layers:
            doc.layers.add(name=name, color=color, linetype=linetype)


def setup_dim_style(doc):
    """Create UNI dimension style with mm precision."""
    if "UNI_DIM" not in doc.dimstyles:
        dim_style = doc.dimstyles.new("UNI_DIM")
        dim_style.dxf.dimtxt = 25      # text height (mm in plot 1:50 = 2.5mm real)
        dim_style.dxf.dimasz = 25      # arrow size
        dim_style.dxf.dimexe = 12      # extension line beyond dim
        dim_style.dxf.dimexo = 12      # extension line offset
        dim_style.dxf.dimdec = 0       # 0 decimals (cm)
        dim_style.dxf.dimlfac = 0.1    # scale factor: mm → cm display


def add_wall(msp, p1, p2, *, layer="CAD-A-WALL", thickness=80):
    """
    Add a wall as 2 parallel lines (thickness mm).
    p1, p2 are wall axis (in mm).
    Wall thickness perpendicular to axis.
    """
    import math
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return
    # perpendicular unit vector
    nx = -dy / length
    ny = dx / length
    half = thickness / 2

    p1a = (p1[0] + nx * half, p1[1] + ny * half)
    p1b = (p1[0] - nx * half, p1[1] - ny * half)
    p2a = (p2[0] + nx * half, p2[1] + ny * half)
    p2b = (p2[0] - nx * half, p2[1] - ny * half)

    # 4 lines forming a closed thick wall
    msp.add_line(p1a, p2a, dxfattribs={"layer": layer})
    msp.add_line(p1b, p2b, dxfattribs={"layer": layer})
    msp.add_line(p1a, p1b, dxfattribs={"layer": layer})
    msp.add_line(p2a, p2b, dxfattribs={"layer": layer})


def add_door(msp, center, width=900, swing="right"):
    """Add a simple door symbol."""
    half = width / 2
    msp.add_line(
        (center[0] - half, center[1]),
        (center[0] + half, center[1]),
        dxfattribs={"layer": "CAD-A-DOOR"},
    )
    # arc representing swing
    msp.add_arc(
        center=(center[0] - half, center[1]),
        radius=width,
        start_angle=0,
        end_angle=90,
        dxfattribs={"layer": "CAD-A-DOOR"},
    )


def add_window(msp, p1, p2):
    """Add a window symbol (double line)."""
    import math
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return
    nx = -dy / length
    ny = dx / length
    offset = 30  # mm

    p1a = (p1[0] + nx * offset, p1[1] + ny * offset)
    p1b = (p1[0] - nx * offset, p1[1] - ny * offset)
    p2a = (p2[0] + nx * offset, p2[1] + ny * offset)
    p2b = (p2[0] - nx * offset, p2[1] - ny * offset)

    msp.add_line(p1a, p2a, dxfattribs={"layer": "CAD-A-WIND"})
    msp.add_line(p1b, p2b, dxfattribs={"layer": "CAD-A-WIND"})
    msp.add_line(p1a, p1b, dxfattribs={"layer": "CAD-A-WIND"})
    msp.add_line(p2a, p2b, dxfattribs={"layer": "CAD-A-WIND"})


def add_room_label(msp, center, name, area):
    """Add room label with name and area."""
    msp.add_text(
        name,
        dxfattribs={"layer": "CAD-A-TEXT", "height": 200},
    ).set_placement(center, align=TextEntityAlignment.MIDDLE_CENTER)
    msp.add_text(
        f"{area:.1f} m²",
        dxfattribs={"layer": "CAD-A-TEXT", "height": 150},
    ).set_placement(
        (center[0], center[1] - 250),
        align=TextEntityAlignment.MIDDLE_CENTER,
    )


def add_dimension_h(msp, p1, p2, offset_y, text_override=None):
    """Add horizontal linear dimension."""
    dim = msp.add_linear_dim(
        base=(p1[0], p1[1] + offset_y),
        p1=p1,
        p2=p2,
        dimstyle="UNI_DIM",
        text=text_override,
    )
    dim.render()


def add_cartiglio(msp, origin):
    """Add CNAPPC-style cartiglio (title block) at given origin."""
    # Outer frame: 180 × 50 mm in plot scale
    w, h = 18000, 5000  # in mm at scale 1:1
    x0, y0 = origin

    # Frame
    msp.add_lwpolyline(
        [
            (x0, y0),
            (x0 + w, y0),
            (x0 + w, y0 + h),
            (x0, y0 + h),
            (x0, y0),
        ],
        dxfattribs={"layer": "CAD-A-CART"},
        close=True,
    )
    # Internal divisions
    msp.add_line((x0 + 6000, y0), (x0 + 6000, y0 + h), dxfattribs={"layer": "CAD-A-CART"})
    msp.add_line((x0 + 12000, y0), (x0 + 12000, y0 + h), dxfattribs={"layer": "CAD-A-CART"})
    msp.add_line((x0, y0 + 2500), (x0 + 18000, y0 + 2500), dxfattribs={"layer": "CAD-A-CART"})

    # Texts
    fields = [
        ("Progetto:", x0 + 200, y0 + 4500, 200),
        ("Attico Brera · Ristrutturazione interna", x0 + 200, y0 + 4200, 250),
        ("Cliente: Marco Rossini & Giulia Bianchi", x0 + 200, y0 + 3700, 200),
        ("Indirizzo: Via Fiori Chiari 17, Milano", x0 + 200, y0 + 3400, 200),
        ("Architetto:", x0 + 6200, y0 + 4500, 200),
        ("Pablo Ruan · Ord. Arch. Milano", x0 + 6200, y0 + 4200, 200),
        ("Tavola:", x0 + 12200, y0 + 4500, 200),
        ("01 · Pianta Stato Attuale", x0 + 12200, y0 + 4200, 250),
        ("Scala 1:50  ·  Data 25/04/2026  ·  Rev. 0", x0 + 12200, y0 + 3700, 200),
        ("Formato A1 (UNI ISO 5457)", x0 + 200, y0 + 1500, 200),
        ("Fase: progetto definitivo", x0 + 6200, y0 + 1500, 200),
        ("File: stato-attuale.dxf", x0 + 12200, y0 + 1500, 200),
    ]
    for txt, x, y, h_text in fields:
        msp.add_text(
            txt,
            dxfattribs={"layer": "CAD-A-CART", "height": h_text},
        ).set_placement((x, y), align=TextEntityAlignment.LEFT)


def build_attico_brera(output_path: Path) -> dict:
    """
    Build the Attico Brera 120 m² DWG.

    Layout (origin at bottom-left, +X right, +Y up, mm):
      - Total: 12000 × 10000 mm = 120 m²
      - Walls 12cm (perimeter) and 8cm (internal partitions)

    Returns:
        dict with summary (rooms, areas, etc.)
    """
    doc = ezdxf.new(dxfversion="R2018", setup=True)
    setup_layers(doc)
    setup_dim_style(doc)
    msp = doc.modelspace()

    # ----------------------------------------------------------------------
    # Perimeter walls (12 cm thick) · outer rectangle 12000 × 10000 mm
    # ----------------------------------------------------------------------
    P = 120  # perimeter wall thickness (mm)
    add_wall(msp, (0, 0), (12000, 0), layer="CAD-A-WALL-EXT", thickness=P)
    add_wall(msp, (12000, 0), (12000, 10000), layer="CAD-A-WALL-EXT", thickness=P)
    add_wall(msp, (12000, 10000), (0, 10000), layer="CAD-A-WALL-EXT", thickness=P)
    add_wall(msp, (0, 10000), (0, 0), layer="CAD-A-WALL-EXT", thickness=P)

    # ----------------------------------------------------------------------
    # Internal partitions (8 cm)
    # Layout (state attuale, before redesign):
    #   - Ingresso (left bottom): 0-2500, 0-3000
    #   - Cucina (left top): 0-3500, 6000-10000
    #   - Soggiorno (center): 2500-7500, 0-6000
    #   - Camera 1: 7500-12000, 0-4000
    #   - Camera 2: 0-4000, 3000-6000
    #   - Camera 3: 7500-12000, 4000-7000
    #   - Bagno: 7500-10000, 7000-10000
    #   - Ripostiglio: 10000-12000, 7000-10000
    # ----------------------------------------------------------------------
    T = 80  # internal wall thickness

    # Ingresso / Soggiorno divider
    add_wall(msp, (2500, 0), (2500, 3000), thickness=T)
    # Ingresso / Camera 2 divider
    add_wall(msp, (0, 3000), (4000, 3000), thickness=T)
    # Camera 2 / Cucina divider
    add_wall(msp, (0, 6000), (3500, 6000), thickness=T)
    add_wall(msp, (3500, 6000), (3500, 10000), thickness=T)
    # Camera 2 / Soggiorno
    add_wall(msp, (4000, 3000), (4000, 6000), thickness=T)
    # Soggiorno / Camera 1 divider
    add_wall(msp, (7500, 0), (7500, 4000), thickness=T)
    add_wall(msp, (7500, 4000), (12000, 4000), thickness=T)
    # Camera 3 sopra
    add_wall(msp, (7500, 7000), (12000, 7000), thickness=T)
    add_wall(msp, (7500, 4000), (7500, 7000), thickness=T)
    # Bagno / Ripostiglio
    add_wall(msp, (10000, 7000), (10000, 10000), thickness=T)
    # Soggiorno / cucina (parete tramezzo anni 80)
    add_wall(msp, (3500, 6000), (7500, 6000), thickness=T)

    # ----------------------------------------------------------------------
    # Doors (centroid + width)
    # ----------------------------------------------------------------------
    add_door(msp, (1250, 3000), width=800)   # ingresso → camera 2
    add_door(msp, (2500, 1500), width=900)   # ingresso → soggiorno
    add_door(msp, (5500, 6000), width=800)   # soggiorno → cucina
    add_door(msp, (7500, 2000), width=800)   # soggiorno → camera 1
    add_door(msp, (7500, 5500), width=800)   # corridoio → camera 3
    add_door(msp, (8750, 7000), width=800)   # corridoio → bagno
    add_door(msp, (10500, 7000), width=700)  # corridoio → ripostiglio

    # ----------------------------------------------------------------------
    # Windows (perimeter)
    # ----------------------------------------------------------------------
    # Cucina (north)
    add_window(msp, (1000, 10000), (2500, 10000))
    # Cucina (north, second)
    add_window(msp, (3000, 10000), (3500, 10000))
    # Bagno (north)
    add_window(msp, (8500, 10000), (9500, 10000))
    # Camera 3 (east)
    add_window(msp, (12000, 5000), (12000, 6500))
    # Camera 1 (east)
    add_window(msp, (12000, 1000), (12000, 3000))
    # Soggiorno (south, terrace door)
    add_window(msp, (3500, 0), (6500, 0))
    # Camera 2 (west)
    add_window(msp, (0, 4000), (0, 5500))
    # Ingresso (south)
    add_window(msp, (500, 0), (1500, 0))

    # ----------------------------------------------------------------------
    # Room labels with areas
    # ----------------------------------------------------------------------
    rooms = [
        # (name, center, area_m2)
        ("INGRESSO", (1250, 1500), 7.5),
        ("CUCINA", (1750, 8000), 14.0),
        ("SOGGIORNO", (5000, 3000), 30.0),
        ("CAMERA 2", (2000, 4500), 12.0),
        ("CAMERA 1", (9750, 2000), 18.0),
        ("CAMERA 3", (9750, 5500), 13.5),
        ("BAGNO", (8750, 8500), 7.5),
        ("RIPOSTIGLIO", (11000, 8500), 6.0),
    ]
    for name, center, area in rooms:
        add_room_label(msp, center, name, area)

    # ----------------------------------------------------------------------
    # Main dimensions (perimeter)
    # ----------------------------------------------------------------------
    add_dimension_h(msp, (0, 0), (12000, 0), -800, text_override="1200")
    add_dimension_h(msp, (0, 10000), (12000, 10000), 800, text_override="1200")

    # vertical dim left
    dim_v = msp.add_linear_dim(
        base=(-800, 0),
        p1=(0, 0),
        p2=(0, 10000),
        angle=90,
        dimstyle="UNI_DIM",
        text="1000",
    )
    dim_v.render()

    # ----------------------------------------------------------------------
    # Cartiglio (title block)
    # ----------------------------------------------------------------------
    add_cartiglio(msp, (-1000, -8000))

    # ----------------------------------------------------------------------
    # Save
    # ----------------------------------------------------------------------
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(output_path))

    # Summary
    total_lordo = 12000 * 10000 / 1_000_000  # m²
    total_utile = sum(area for _, _, area in rooms)
    return {
        "output_path": str(output_path),
        "total_lordo_m2": total_lordo,
        "total_utile_m2": total_utile,
        "muratura_m2": total_lordo - total_utile,
        "rooms_count": len(rooms),
        "rooms": [
            {"name": n, "area_m2": a, "center_mm": c}
            for n, c, a in rooms
        ],
        "layers": [name for name, _, _ in LAYERS],
        "dxf_version": "R2018",
    }


def main():
    output = sys.argv[1] if len(sys.argv) > 1 else "stato-attuale.dxf"
    summary = build_attico_brera(Path(output))
    import json
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
