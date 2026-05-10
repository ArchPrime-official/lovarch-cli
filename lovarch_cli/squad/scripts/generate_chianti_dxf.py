"""
Generate sample DXF for Casa Colonica Belvedere · Chianti demo.

Creates a realistic farmhouse plan in DXF format with:
- Layer ISO standard (CAD-A-WALL, CAD-A-DIM, CAD-A-DOOR, CAD-A-WIND, CAD-A-TEXT)
- Two buildings: corpo principale (220 m² ground floor) + annesso ex-stalla (60 m²)
- Stone perimeter walls 50cm thick, internal partitions 15cm
- Cartiglio CNAPPC for Pablo Ruan · Ordine Firenze
- Specific to Italian rural restoration project

Output: data/sample-input-villa-chianti/stato-attuale.dxf

Usage:
    python3 generate_chianti_dxf.py [output_path]
"""
import sys
from pathlib import Path

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
except ImportError:
    sys.stderr.write("ERROR: ezdxf not installed. Run: pip install ezdxf\n")
    sys.exit(1)


LAYERS = [
    ("CAD-A-WALL", 7, "Continuous"),
    ("CAD-A-WALL-EXT", 1, "Continuous"),
    ("CAD-A-DOOR", 4, "Continuous"),
    ("CAD-A-WIND", 5, "Continuous"),
    ("CAD-A-DIM", 3, "Continuous"),
    ("CAD-A-TEXT", 2, "Continuous"),
    ("CAD-A-SYMB", 6, "Continuous"),
    ("CAD-A-FURN", 8, "Continuous"),
    ("CAD-A-CART", 7, "Continuous"),
]


def setup_layers(doc):
    for name, color, linetype in LAYERS:
        if name not in doc.layers:
            doc.layers.add(name=name, color=color, linetype=linetype)


def setup_dim_style(doc):
    if "UNI_DIM" not in doc.dimstyles:
        ds = doc.dimstyles.new("UNI_DIM")
        ds.dxf.dimtxt = 25
        ds.dxf.dimasz = 25
        ds.dxf.dimexe = 12
        ds.dxf.dimexo = 12
        ds.dxf.dimdec = 0
        ds.dxf.dimlfac = 0.1


def add_wall(msp, p1, p2, *, layer="CAD-A-WALL", thickness=150):
    import math
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return
    nx = -dy / length
    ny = dx / length
    half = thickness / 2
    p1a = (p1[0] + nx * half, p1[1] + ny * half)
    p1b = (p1[0] - nx * half, p1[1] - ny * half)
    p2a = (p2[0] + nx * half, p2[1] + ny * half)
    p2b = (p2[0] - nx * half, p2[1] - ny * half)
    msp.add_line(p1a, p2a, dxfattribs={"layer": layer})
    msp.add_line(p1b, p2b, dxfattribs={"layer": layer})
    msp.add_line(p1a, p1b, dxfattribs={"layer": layer})
    msp.add_line(p2a, p2b, dxfattribs={"layer": layer})


def add_door(msp, center, width=900):
    half = width / 2
    msp.add_line((center[0] - half, center[1]),
                 (center[0] + half, center[1]),
                 dxfattribs={"layer": "CAD-A-DOOR"})
    msp.add_arc(center=(center[0] - half, center[1]), radius=width,
                start_angle=0, end_angle=90,
                dxfattribs={"layer": "CAD-A-DOOR"})


def add_window(msp, p1, p2):
    import math
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return
    nx = -dy / length
    ny = dx / length
    offset = 30
    p1a = (p1[0] + nx * offset, p1[1] + ny * offset)
    p1b = (p1[0] - nx * offset, p1[1] - ny * offset)
    p2a = (p2[0] + nx * offset, p2[1] + ny * offset)
    p2b = (p2[0] - nx * offset, p2[1] - ny * offset)
    msp.add_line(p1a, p2a, dxfattribs={"layer": "CAD-A-WIND"})
    msp.add_line(p1b, p2b, dxfattribs={"layer": "CAD-A-WIND"})
    msp.add_line(p1a, p1b, dxfattribs={"layer": "CAD-A-WIND"})
    msp.add_line(p2a, p2b, dxfattribs={"layer": "CAD-A-WIND"})


def add_room_label(msp, center, name, area):
    msp.add_text(name, dxfattribs={"layer": "CAD-A-TEXT", "height": 200}) \
        .set_placement(center, align=TextEntityAlignment.MIDDLE_CENTER)
    msp.add_text(f"{area:.1f} m²", dxfattribs={"layer": "CAD-A-TEXT", "height": 150}) \
        .set_placement((center[0], center[1] - 250),
                       align=TextEntityAlignment.MIDDLE_CENTER)


def add_camino(msp, center, w=1800, d=1200):
    """Draw a fireplace symbol · stone monumental on a wall."""
    x, y = center
    pts = [(x - w/2, y), (x + w/2, y), (x + w/2, y + d),
           (x + w/2 - 200, y + d), (x + w/2 - 200, y + 200),
           (x - w/2 + 200, y + 200), (x - w/2 + 200, y + d),
           (x - w/2, y + d), (x - w/2, y)]
    msp.add_lwpolyline(pts, dxfattribs={"layer": "CAD-A-SYMB"}, close=False)
    msp.add_text("CAMINO", dxfattribs={"layer": "CAD-A-SYMB", "height": 120}) \
        .set_placement((x, y + d/2), align=TextEntityAlignment.MIDDLE_CENTER)


def add_cartiglio(msp, origin):
    w, h = 18000, 5000
    x0, y0 = origin
    msp.add_lwpolyline(
        [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h), (x0, y0)],
        dxfattribs={"layer": "CAD-A-CART"}, close=True,
    )
    msp.add_line((x0 + 6000, y0), (x0 + 6000, y0 + h), dxfattribs={"layer": "CAD-A-CART"})
    msp.add_line((x0 + 12000, y0), (x0 + 12000, y0 + h), dxfattribs={"layer": "CAD-A-CART"})
    msp.add_line((x0, y0 + 2500), (x0 + 18000, y0 + 2500), dxfattribs={"layer": "CAD-A-CART"})

    fields = [
        ("Progetto:", x0 + 200, y0 + 4500, 200),
        ("Casa Colonica Belvedere · Recupero rurale", x0 + 200, y0 + 4200, 250),
        ("Cliente: Lorenzo Ferri & Alessandra Conti", x0 + 200, y0 + 3700, 200),
        ("Indirizzo: Loc. Belvedere 12, Greve in Chianti (FI)", x0 + 200, y0 + 3400, 200),
        ("Architetto:", x0 + 6200, y0 + 4500, 200),
        ("Pablo Ruan · Ord. Arch. Firenze", x0 + 6200, y0 + 4200, 200),
        ("Tavola:", x0 + 12200, y0 + 4500, 200),
        ("01 · Pianta Stato Attuale · Piano Terra", x0 + 12200, y0 + 4200, 250),
        ("Scala 1:50  ·  Data 25/04/2026  ·  Rev. 0", x0 + 12200, y0 + 3700, 200),
        ("Formato A1 (UNI ISO 5457)", x0 + 200, y0 + 1500, 200),
        ("Fase: progetto preliminare", x0 + 6200, y0 + 1500, 200),
        ("File: stato-attuale.dxf", x0 + 12200, y0 + 1500, 200),
    ]
    for txt, x, y, h_text in fields:
        msp.add_text(txt, dxfattribs={"layer": "CAD-A-CART", "height": h_text}) \
            .set_placement((x, y), align=TextEntityAlignment.LEFT)


def build_chianti_dxf(output_path: Path) -> dict:
    """
    Build Casa Colonica Chianti DXF · piano terra.

    Layout (mm, origin bottom-left):
      - Corpo principale: 16000 × 14000 mm = 224 m² lordi (ground floor)
      - Annesso ex-stalla: 10000 × 6000 mm = 60 m² (offset right by 21000)
      - Perimeter walls 500mm (stone), internal 150mm
    """
    doc = ezdxf.new(dxfversion="R2018", setup=True)
    setup_layers(doc)
    setup_dim_style(doc)
    msp = doc.modelspace()

    # ----------------------------------------------------------------
    # CORPO PRINCIPALE · perimeter walls 50cm thick
    # ----------------------------------------------------------------
    P = 500
    add_wall(msp, (0, 0), (16000, 0), layer="CAD-A-WALL-EXT", thickness=P)
    add_wall(msp, (16000, 0), (16000, 14000), layer="CAD-A-WALL-EXT", thickness=P)
    add_wall(msp, (16000, 14000), (0, 14000), layer="CAD-A-WALL-EXT", thickness=P)
    add_wall(msp, (0, 14000), (0, 0), layer="CAD-A-WALL-EXT", thickness=P)

    # ----------------------------------------------------------------
    # Internal partitions (15cm)
    # ----------------------------------------------------------------
    T = 150

    # Horizontal mid-divider (at y=7500): south = bagno+disimp+cantina, north = cucina+sala+sogg
    add_wall(msp, (0, 7500), (16000, 7500), thickness=T)

    # Vertical dividers south side
    add_wall(msp, (5500, 0), (5500, 7500), thickness=T)
    add_wall(msp, (10500, 0), (10500, 7500), thickness=T)

    # Vertical dividers north side
    add_wall(msp, (5500, 7500), (5500, 14000), thickness=T)
    add_wall(msp, (10500, 7500), (10500, 14000), thickness=T)

    # Bagno separation inside south-west room
    add_wall(msp, (0, 3500), (3000, 3500), thickness=T)
    add_wall(msp, (3000, 0), (3000, 3500), thickness=T)

    # ----------------------------------------------------------------
    # Doors (centroid + width)
    # ----------------------------------------------------------------
    add_door(msp, (2750, 0), width=1100)        # ingresso principale (sud)
    add_door(msp, (5500, 5000), width=900)      # ingresso → disimpegno
    add_door(msp, (8000, 7500), width=900)      # disimpegno → sala pranzo
    add_door(msp, (3500, 7500), width=900)      # disimpegno → cucina (NS)
    add_door(msp, (13500, 7500), width=900)     # cantina → soggiorno
    add_door(msp, (10500, 11000), width=900)    # sala pranzo → soggiorno
    add_door(msp, (5500, 10500), width=900)     # cucina → sala pranzo
    add_door(msp, (1500, 3500), width=800)      # disimp → bagno
    add_door(msp, (3000, 1500), width=800)      # ingresso → bagno

    # ----------------------------------------------------------------
    # Windows (perimeter)
    # ----------------------------------------------------------------
    # Cucina (nord)
    add_window(msp, (1000, 14000), (3000, 14000))
    # Sala pranzo (nord)
    add_window(msp, (6500, 14000), (8000, 14000))
    add_window(msp, (8500, 14000), (10000, 14000))
    # Soggiorno (nord)
    add_window(msp, (12000, 14000), (14000, 14000))
    # Soggiorno (est)
    add_window(msp, (16000, 9500), (16000, 12000))
    # Cantina (est)
    add_window(msp, (16000, 2500), (16000, 5000))
    # Cantina (sud)
    add_window(msp, (12000, 0), (14000, 0))
    # Cucina (ovest)
    add_window(msp, (0, 11000), (0, 13000))
    # Bagno (ovest)
    add_window(msp, (0, 2000), (0, 3000))

    # ----------------------------------------------------------------
    # Camino monumentale · centrale parete nord cucina
    # ----------------------------------------------------------------
    add_camino(msp, center=(2750, 13800), w=1800, d=1200)

    # Camino piccolo · soggiorno (parete est)
    add_camino(msp, center=(15800, 11500), w=1200, d=900)

    # ----------------------------------------------------------------
    # Room labels · CORPO PRINCIPALE
    # ----------------------------------------------------------------
    rooms_main = [
        ("INGRESSO + BAGNO", (4250, 1800), 22.0),
        ("DISIMPEGNO", (8000, 3700), 28.0),
        ("CANTINA VINIFIC.", (13250, 3700), 32.0),
        ("CUCINA", (2750, 10500), 28.0),
        ("SALA DA PRANZO", (8000, 10500), 32.0),
        ("SOGGIORNO", (13250, 10500), 30.0),
    ]
    for name, center, area in rooms_main:
        add_room_label(msp, center, name, area)

    # ----------------------------------------------------------------
    # ANNESSO EX-STALLA · offset 5000mm a destra
    # ----------------------------------------------------------------
    OX, OY = 21000, 4000
    PA = 500   # stone perimeter
    add_wall(msp, (OX, OY), (OX + 10000, OY), layer="CAD-A-WALL-EXT", thickness=PA)
    add_wall(msp, (OX + 10000, OY), (OX + 10000, OY + 6000), layer="CAD-A-WALL-EXT", thickness=PA)
    add_wall(msp, (OX + 10000, OY + 6000), (OX, OY + 6000), layer="CAD-A-WALL-EXT", thickness=PA)
    add_wall(msp, (OX, OY + 6000), (OX, OY), layer="CAD-A-WALL-EXT", thickness=PA)

    # 1 simple partition · ex-stalla aperta
    add_wall(msp, (OX + 6500, OY), (OX + 6500, OY + 6000), thickness=T)

    # 1 main door (sud)
    add_door(msp, (OX + 3000, OY), width=1500)
    # piccolo wc con porta
    add_door(msp, (OX + 6500, OY + 3000), width=800)

    # finestre annesso
    add_window(msp, (OX + 1000, OY + 6000), (OX + 2500, OY + 6000))     # nord
    add_window(msp, (OX + 5000, OY + 6000), (OX + 6000, OY + 6000))     # nord
    add_window(msp, (OX, OY + 2500), (OX, OY + 4000))                    # ovest
    add_window(msp, (OX + 10000, OY + 4500), (OX + 10000, OY + 5500))    # est

    rooms_annex = [
        ("ANNESSO · EX-STALLA", (OX + 3250, OY + 3000), 39.0),
        ("WC SERVIZIO", (OX + 8250, OY + 3000), 21.0),
    ]
    for name, center, area in rooms_annex:
        add_room_label(msp, center, name, area)

    # Mangiatoie originali in pietra (ovest del annesso)
    msp.add_lwpolyline(
        [(OX + 200, OY + 1000), (OX + 5500, OY + 1000),
         (OX + 5500, OY + 1700), (OX + 200, OY + 1700),
         (OX + 200, OY + 1000)],
        dxfattribs={"layer": "CAD-A-FURN"}, close=True,
    )
    msp.add_text("MANGIATOIE ORIGINALI · pietra serena · da preservare",
                 dxfattribs={"layer": "CAD-A-TEXT", "height": 100}) \
        .set_placement((OX + 2850, OY + 1350),
                       align=TextEntityAlignment.MIDDLE_CENTER)

    # ----------------------------------------------------------------
    # Dimensions principali (perimeter corpo principale)
    # ----------------------------------------------------------------
    msp.add_linear_dim(base=(0, -800), p1=(0, 0), p2=(16000, 0),
                       dimstyle="UNI_DIM", text="1600").render()
    msp.add_linear_dim(base=(0, 14800), p1=(0, 14000), p2=(16000, 14000),
                       dimstyle="UNI_DIM", text="1600").render()
    msp.add_linear_dim(base=(-800, 0), p1=(0, 0), p2=(0, 14000),
                       angle=90, dimstyle="UNI_DIM", text="1400").render()

    # Annesso dim
    msp.add_linear_dim(base=(OX, OY - 800), p1=(OX, OY), p2=(OX + 10000, OY),
                       dimstyle="UNI_DIM", text="1000").render()
    msp.add_linear_dim(base=(OX - 800, OY), p1=(OX, OY), p2=(OX, OY + 6000),
                       angle=90, dimstyle="UNI_DIM", text="600").render()

    # ----------------------------------------------------------------
    # Cartiglio
    # ----------------------------------------------------------------
    add_cartiglio(msp, (-1000, -8000))

    # ----------------------------------------------------------------
    # Title text above plan
    # ----------------------------------------------------------------
    msp.add_text("CASA COLONICA BELVEDERE · PIANTA STATO ATTUALE PIANO TERRA",
                 dxfattribs={"layer": "CAD-A-TEXT", "height": 350}) \
        .set_placement((8000, 15500), align=TextEntityAlignment.MIDDLE_CENTER)
    msp.add_text("ANNESSO · EX-STALLA",
                 dxfattribs={"layer": "CAD-A-TEXT", "height": 250}) \
        .set_placement((26000, 11000), align=TextEntityAlignment.MIDDLE_CENTER)

    # ----------------------------------------------------------------
    # Save
    # ----------------------------------------------------------------
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(output_path))

    total_lordo_main = 16000 * 14000 / 1_000_000
    total_lordo_annex = 10000 * 6000 / 1_000_000
    rooms_all = rooms_main + rooms_annex
    total_utile = sum(area for _, _, area in rooms_all)

    return {
        "output_path": str(output_path),
        "corpo_principale_lordo_m2": total_lordo_main,
        "annesso_lordo_m2": total_lordo_annex,
        "total_lordo_m2": total_lordo_main + total_lordo_annex,
        "total_utile_m2": total_utile,
        "muratura_m2": (total_lordo_main + total_lordo_annex) - total_utile,
        "rooms_count": len(rooms_all),
        "rooms": [{"name": n, "area_m2": a, "center_mm": c} for n, c, a in rooms_all],
        "layers": [name for name, _, _ in LAYERS],
        "dxf_version": "R2018",
    }


def main():
    if len(sys.argv) > 1:
        output = sys.argv[1]
    else:
        output = str(Path(__file__).resolve().parents[1]
                     / "data" / "sample-input-villa-chianti" / "stato-attuale.dxf")
    summary = build_chianti_dxf(Path(output))
    import json
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
