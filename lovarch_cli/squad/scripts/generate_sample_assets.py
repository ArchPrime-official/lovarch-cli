"""
Generate sample placeholder assets for Attico Brera demo input.

Outputs (all in data/sample-input/):
- foto/ · 6 JPG placeholders (facciata, ingresso, soggiorno, cucina, camera, bagno)
- visura-catastale.pdf · 2-page PDF mock with cadastral data
- pinterest-references/ · 6 JPG style references

These are PLACEHOLDERS for testing. Real demo would use actual photos +
real catastral PDF from Agenzia Entrate.

Usage:
    python3 generate_sample_assets.py
"""
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.stderr.write("ERROR: pillow not installed. Run: pip3 install --user pillow\n")
    sys.exit(1)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.lib.colors import HexColor, black, grey
    from reportlab.pdfgen import canvas
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
except ImportError:
    sys.stderr.write("ERROR: reportlab not installed. Run: pip3 install --user reportlab\n")
    sys.exit(1)


SAMPLE_DIR = Path(__file__).parent.parent / "data" / "sample-input"
FOTO_DIR = SAMPLE_DIR / "foto"
PINTEREST_DIR = SAMPLE_DIR / "pinterest-references"


# ============================================================================
# 1. FOTO placeholders · 6 JPG (1280x960 · ~150KB each)
# ============================================================================

PHOTOS = [
    {
        "filename": "01-facciata.jpg",
        "title": "Facciata",
        "subtitle": "Via Fiori Chiari 17, Milano · Brera",
        "color": "#7B6F5C",  # warm beige
        "description": "Edificio 1910 · facciata vincolata\nZona A1 PGT · NAF Brera",
    },
    {
        "filename": "02-ingresso.jpg",
        "title": "Ingresso",
        "subtitle": "Stato attuale",
        "color": "#9B8A7A",
        "description": "~6 m² · pavimento marmette anni '80\nCorridoio lungo a sostituire",
    },
    {
        "filename": "03-soggiorno.jpg",
        "title": "Soggiorno",
        "subtitle": "Stato attuale",
        "color": "#A99580",
        "description": "~30 m² · seminato veneziano originale\nSoffitti decorati da preservare",
    },
    {
        "filename": "04-cucina.jpg",
        "title": "Cucina",
        "subtitle": "Stato attuale",
        "color": "#C8B69E",
        "description": "~14 m² · separata dal soggiorno\nDa unificare in open-space",
    },
    {
        "filename": "05-camera-padronale.jpg",
        "title": "Camera padronale",
        "subtitle": "Stato attuale",
        "color": "#8B7B6E",
        "description": "~18 m² · soffitti alti 290 cm\nDa rifare con cabina armadio",
    },
    {
        "filename": "06-bagno.jpg",
        "title": "Bagno principale",
        "subtitle": "Stato attuale",
        "color": "#A89887",
        "description": "~6 m² · cieco · piastrelle anni '80\nDa rifare con doccia walk-in",
    },
]


def generate_photo_placeholder(filepath: Path, photo: dict) -> None:
    """Create a 1280x960 JPG with title + description · architectural placeholder style."""
    width, height = 1280, 960
    bg_color = photo["color"]
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Add gradient overlay (simulating ambient lighting)
    for y in range(height):
        alpha = int(80 * (y / height))
        overlay = Image.new("RGBA", (width, 1), (0, 0, 0, alpha))
        img.paste(overlay, (0, y), overlay if overlay.mode == "RGBA" else None)

    # Try load custom font, fall back to default
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Times New Roman.ttf", 80)
        sub_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Helvetica.ttc", 38)
        body_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Helvetica.ttc", 32)
        meta_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Helvetica.ttc", 20)
    except (OSError, IOError):
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        meta_font = ImageFont.load_default()

    # Title (centered top)
    draw.text((width // 2, 280), photo["title"], font=title_font, fill="white", anchor="mm")
    draw.text((width // 2, 360), photo["subtitle"], font=sub_font, fill="#E8DDD0", anchor="mm")

    # Description (centered middle)
    y = 500
    for line in photo["description"].split("\n"):
        draw.text((width // 2, y), line, font=body_font, fill="white", anchor="mm")
        y += 50

    # Meta footer
    draw.text(
        (width // 2, height - 40),
        "[ PLACEHOLDER · sample-input squad architettura-progetto ]",
        font=meta_font,
        fill="#D0C5B5",
        anchor="mm",
    )

    # Save as JPEG quality 85 (~120-180KB)
    img.save(filepath, "JPEG", quality=85, optimize=True)


# ============================================================================
# 2. PINTEREST REFERENCES · 6 style placeholders
# ============================================================================

PINTEREST = [
    {"filename": "pin-01-de-cotiis.jpg", "title": "Vincenzo De Cotiis", "subtitle": "Studio Milano", "color": "#A89880"},
    {"filename": "pin-02-studiopepe.jpg", "title": "Studiopepe", "subtitle": "Tonalità terra", "color": "#B8A38C"},
    {"filename": "pin-03-marcante-testa.jpg", "title": "Marcante & Testa", "subtitle": "Decori restaurati", "color": "#967D62"},
    {"filename": "pin-04-vilon.jpg", "title": "Hotel Vilòn Roma", "subtitle": "Seminato + contemporaneo", "color": "#C5A98A"},
    {"filename": "pin-05-cassina.jpg", "title": "Cassina Living", "subtitle": "Sofa Maralunga", "color": "#8E7B65"},
    {"filename": "pin-06-devon-devon.jpg", "title": "Devon&Devon", "subtitle": "Cucina rovere chiaro", "color": "#D4BC9C"},
]


# ============================================================================
# 3. VISURA CATASTALE · 2-page PDF mock
# ============================================================================

def generate_visura_pdf(filepath: Path) -> None:
    """Generate 2-page mock visura catastale (Agenzia Entrate format)."""
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=14,
        spaceAfter=12,
        textColor=HexColor("#003566"),
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=11,
        spaceAfter=6,
        textColor=HexColor("#1a1a1a"),
    )
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9, leading=12)
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=7, leading=9, textColor=grey)

    story = []

    # Header
    story.append(Paragraph("AGENZIA DELLE ENTRATE", title_style))
    story.append(Paragraph("Direzione Provinciale di Milano · Ufficio Provinciale Territorio", body))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>VISURA CATASTALE</b>", h2))
    story.append(Paragraph("Visura per immobile · Catasto Fabbricati", body))
    story.append(Spacer(1, 12))

    # Identificazione
    story.append(Paragraph("<b>IDENTIFICATIVO IMMOBILE</b>", h2))
    data = [
        ["Comune", "MILANO (cod. F205)"],
        ["Sezione", "—"],
        ["Foglio", "356"],
        ["Particella", "127"],
        ["Subalterno", "12"],
        ["Categoria", "A/2 (Abitazione di tipo civile)"],
        ["Classe", "5"],
        ["Consistenza", "5,5 vani"],
        ["Superficie catastale", "120 m² (totale lordo)"],
        ["Rendita catastale", "€ 1.456,32"],
        ["Zona censuaria", "01 (centro storico)"],
    ]
    t = Table(data, colWidths=[5 * cm, 12 * cm])
    t.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
                ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 12))

    # Ubicazione
    story.append(Paragraph("<b>UBICAZIONE</b>", h2))
    data = [
        ["Indirizzo", "Via Fiori Chiari 17"],
        ["CAP", "20121"],
        ["Comune", "Milano (MI)"],
        ["Piano", "3"],
        ["Scala", "A"],
        ["Interno", "5"],
        ["Civico", "17"],
    ]
    t = Table(data, colWidths=[5 * cm, 12 * cm])
    t.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
                ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 12))

    # Intestatari
    story.append(Paragraph("<b>INTESTATARI</b>", h2))
    data = [
        ["Cognome / Nome", "Codice Fiscale", "Quota", "Diritto"],
        ["ROSSINI MARCO", "RSSMRC83A15F205X", "1/2", "Proprietà"],
        ["BIANCHI GIULIA", "BNCGLI88D52F205Y", "1/2", "Proprietà"],
    ]
    t = Table(data, colWidths=[6 * cm, 5 * cm, 2.5 * cm, 3.5 * cm])
    t.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#E8E8E8")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 12))

    # Vincoli
    story.append(Paragraph("<b>VINCOLI E DENUNCE</b>", h2))
    data = [
        ["Tipo", "Riferimento", "Descrizione"],
        ["Vincolo paesaggistico", "D.Lgs 42/2004 art. 142", "Zona A1 PGT Milano · NAF Brera"],
        ["Vincolo monumentale indiretto", "art. 45 D.Lgs 42/2004", "Edificio in zona di rispetto"],
    ]
    t = Table(data, colWidths=[5 * cm, 5 * cm, 7 * cm])
    t.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), "Helvetica", 8),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#E8E8E8")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 12))

    # Storico
    story.append(Paragraph("<b>STORICO VARIAZIONI CATASTALI</b>", h2))
    data = [
        ["Data", "Tipo", "Riferimento"],
        ["1910-XX-XX", "Costruzione originaria", "Licenza edilizia n. 1234/1910"],
        ["1985-XX-XX", "Ristrutturazione", "Concessione edilizia n. 5678/1985"],
        ["2018-06-15", "Aggiornamento dati", "Variazione catastale (no oneri)"],
    ]
    t = Table(data, colWidths=[3 * cm, 5 * cm, 9 * cm])
    t.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), "Helvetica", 8),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#E8E8E8")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 24))

    # Footer · disclaimer
    story.append(
        Paragraph(
            "<b>NOTA</b> · La presente visura ha valore informativo e non costituisce certificazione giuridica.<br/>"
            "Per atti notarili o azioni legali è necessario richiedere visura ipo-catastale per soggetto.<br/>"
            "Questo documento è un MOCK · sample-input squad architettura-progetto · "
            "in produzione il dato proviene da Catasto via OpenAPI.com · NON valido per uso reale.",
            small,
        )
    )

    doc.build(story)


# ============================================================================
# RUN
# ============================================================================

def main():
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    FOTO_DIR.mkdir(parents=True, exist_ok=True)
    PINTEREST_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Generating sample assets ===\n")

    # Foto
    print("[1/3] Foto placeholders...")
    for photo in PHOTOS:
        path = FOTO_DIR / photo["filename"]
        generate_photo_placeholder(path, photo)
        size_kb = path.stat().st_size / 1024
        print(f"  ✓ {photo['filename']} · {size_kb:.0f} KB")

    # Pinterest
    print("\n[2/3] Pinterest references...")
    for ref in PINTEREST:
        path = PINTEREST_DIR / ref["filename"]
        generate_photo_placeholder(path, {**ref, "description": ref["subtitle"]})
        size_kb = path.stat().st_size / 1024
        print(f"  ✓ {ref['filename']} · {size_kb:.0f} KB")

    # Visura
    print("\n[3/3] Visura catastale PDF...")
    visura_path = SAMPLE_DIR / "visura-catastale.pdf"
    generate_visura_pdf(visura_path)
    size_kb = visura_path.stat().st_size / 1024
    print(f"  ✓ visura-catastale.pdf · {size_kb:.0f} KB")

    # Summary
    print("\n=== Done ===")
    print(f"  · sample-input/foto/ · {len(PHOTOS)} JPG (architectural placeholders)")
    print(f"  · sample-input/pinterest-references/ · {len(PINTEREST)} JPG")
    print(f"  · sample-input/visura-catastale.pdf · 2 pages")
    print(f"  · sample-input/briefing-cliente.md (already exists)")
    print(f"  · sample-input/stato-attuale.dxf (already generated)")


if __name__ == "__main__":
    main()
