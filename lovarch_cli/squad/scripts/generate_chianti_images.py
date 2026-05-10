#!/usr/bin/env python3
"""Generate photorealistic sample images for Casa Colonica Chianti demo.

Same pattern as generate_real_sample_images.py but with rural Tuscan prompts:
- 6 stato attuale (1850 colonica, neglected/dated, recovery candidate)
- 6 reference style photos (tuscan country-modern · contemporary rural · Adario/Reschio/Miani)

Uses OpenAI gpt-image-2 via direct API.
"""

import os
import sys
import base64
from pathlib import Path
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
FOTO_DIR = ROOT / "data" / "sample-input-villa-chianti" / "foto"
PIN_DIR = ROOT / "data" / "sample-input-villa-chianti" / "pinterest-references"

client = OpenAI()

STATO_ATTUALE_PROMPTS = {
    "01-facciata.jpg": (
        "Photorealistic exterior photo of an 1850 Tuscan rural farmhouse (casa colonica) in the "
        "Chianti Classico countryside near Greve in Chianti. Two-story stone masonry building with "
        "sasso del Chianti rough-cut local stone walls, weathered terracotta tile roof with marsigliesi "
        "tiles, original wooden shutters in faded green-grey, ground floor with stone arched portico "
        "supported by pietra serena columns and chestnut wooden beam. A small rusted metal gate, "
        "overgrown grass, an old fig tree on the right. Cypress trees and rolling hills with vineyards "
        "in the background. Late afternoon golden hour Tuscan light, slight haze. Documentary "
        "architectural photography, 35mm full-frame, f/8, eye-level, no people, no cars. "
        "Building shows neglect: dirt streaks, missing tiles in places, weathered walls."
    ),
    "02-portico-ingresso.jpg": (
        "Photorealistic interior photo of a Tuscan farmhouse entrance under a stone arched portico, "
        "looking inward toward the front door. Original cotto antico terracotta tile floor faded "
        "by 170 years of use, two stone columns in pietra serena flanking the view, chestnut wooden "
        "beam overhead with small spider webs and dust. Pale lime-washed plaster walls with patches "
        "of damp staining and original ochre pigment showing through. Old wooden door painted faded "
        "green-grey with iron hardware, terracotta planters with dead plants. A simple iron lantern "
        "on the wall, dated electrical conduit running along the wall (clearly 1980s), faded straw "
        "broom leaning. Documentary photography, soft afternoon light filtering through the arch, "
        "24mm wide angle, f/5.6. Lived-in but neglected, awaiting restoration."
    ),
    "03-cucina-rustica.jpg": (
        "Photorealistic interior of a 1850 Tuscan farmhouse kitchen, original but dated. Massive "
        "stone fireplace (camino monumentale) on the back wall measuring about 180 by 120 cm with "
        "blackened stone hearth, original cotto antico terracotta floor tiles uneven and worn, "
        "exposed chestnut wooden ceiling beams stained dark with age and smoke, lime-washed walls "
        "in faded ochre with cracks and damp patches. Terrible 1980s additions: a cheap white "
        "melamine kitchen unit with brown laminate doors against the right wall, a yellowed "
        "Smeg-style fridge from the 90s, a generic stainless steel sink on a brick base, an old "
        "rusty wood stove (stufa a legna) connected to the chimney, dated rectangular fluorescent "
        "ceiling light tube. Hanging copper pots covered in dust. Single small window with green "
        "shutters partially open. Real-estate photography, neutral indoor light, 24mm wide, dated "
        "and cluttered, documentary."
    ),
    "04-sala-pranzo.jpg": (
        "Photorealistic interior of an 1850 Tuscan farmhouse dining room, large rectangular space. "
        "Original wide-plank cotto antico terracotta floor uneven and faded with patches of "
        "darker tiles where furniture sat, exposed chestnut wood ceiling beams (5 main visible "
        "running parallel) with smaller joists, original lime-washed walls with peeling paint "
        "showing previous ochre layers. A simple long pine farmhouse table for 8 with mismatched "
        "wooden chairs, dated 1980s pendant light with pleated fabric shade, faded blue-and-white "
        "ceramic plates on a tall walnut sideboard from grandmother era. A small old fireplace on "
        "the side wall, terracotta tile fireplace surround. Two tall double-shutter windows on the "
        "left wall with original wooden internal shutters, looking out toward the vineyard. "
        "Real-estate photography, soft afternoon light filtering through, 35mm, f/4. Lived-in, "
        "outdated, mediocre 1985 partial intervention visible."
    ),
    "05-camera-piano-primo.jpg": (
        "Photorealistic Italian Tuscan farmhouse bedroom on the upper floor (piano primo), about "
        "14 sqm with a sloped ceiling exposing original chestnut wood beams and the underside of "
        "tiled roof (correntini visible). Faded cream lime-washed walls with damp stain patches "
        "near the corner, original cotto antico floor with some tiles cracked and replaced with "
        "darker non-matching pieces. A simple iron-frame double bed from grandmother's era with "
        "white linens, an old wooden wardrobe with mirror, plain wooden chair, a bedside table "
        "with a 1980s lamp. Single small window with green shutters open showing distant Tuscan "
        "hills. No insulation visible, no heating present. Real estate photography, soft natural "
        "light, 24mm wide, simple and modest, dated, documentary."
    ),
    "06-stalla-annesso.jpg": (
        "Photorealistic interior of a Tuscan farmhouse annex that was originally a stable (ex-"
        "stalla) from 1930s, currently disused. Stone walls (sasso del Chianti) partially covered "
        "in old whitewash that's flaking off, exposed wooden ceiling beams much rougher than the "
        "main house, dirt-stained terracotta floor with spots of straw and dust, original stone "
        "feeding troughs (mangiatoie) along the right wall about 1.2m high, an iron tie ring still "
        "embedded in the wall. The space is open and rectangular about 10 by 6 meters with one "
        "main door at the front and a small high window letting in dusty afternoon light. Cobwebs, "
        "an old pitchfork leaning, scattered tools and broken terracotta pots, traces of past "
        "agricultural use. Documentary photography, 24mm wide angle, mixed natural and dim "
        "ambient light, abandoned but restorable, raw and authentic Tuscan rural heritage."
    ),
}

PINTEREST_REFS_PROMPTS = {
    "pin-01-adario-tuscan.jpg": (
        "Photorealistic interior of a contemporary Tuscan farmhouse renovation in Massimo Adario "
        "style, rural country-modern aesthetic. Original cotto antico terracotta floor restored "
        "and gently polished, lime-washed walls in pale ocra siena warm tone, exposed chestnut "
        "ceiling beams treated naturally with linseed oil, large open living area with low-profile "
        "linen cream sofa, sculptural ceramic side table in unglazed terracotta, vintage Persian "
        "kilim runner in earthy reds and ochres, cast iron wood-burning stove (modern but classic "
        "shape) in the corner. Floor-to-ceiling tall window with simple linen curtains showing "
        "olive trees outside. Material honesty, refined rural sophistication, no kitsch. Editorial "
        "interior photography, 35mm f/4, warm afternoon light."
    ),
    "pin-02-pierattelli-recupero.jpg": (
        "Photorealistic Tuscan farmhouse kitchen interior, contemporary recovery in Pierattelli "
        "Architetture style. Massive original stone fireplace preserved as central architectural "
        "feature, restored cotto antico floor in warm orange-brown tones, exposed dark chestnut "
        "ceiling beams with original patina, walls in raw lime plaster with subtle terra di Siena "
        "pigment. Large central island with thick honed pietra serena countertop, light oak shaker-"
        "style cabinets with brushed brass hardware, professional-grade range with brass details, "
        "linear pendant lights with pale fabric shades. A handmade wooden farmhouse table for "
        "10 in the foreground with linen runner, ceramic bowls, fresh herbs. Tall French window "
        "with iron muntins, view onto vineyard. Editorial photography 35mm f/4, soft daylight."
    ),
    "pin-03-miani-valdorcia.jpg": (
        "Photorealistic Tuscan dining room in Ilaria Miani style for a Val d'Orcia rural "
        "renovation. Walls in vibrant restored terra rossa earthy red lime plaster (slightly "
        "uneven, hand-applied), original cotto antico floor with red-orange warm tones, chestnut "
        "ceiling with closely-spaced wood beams. A long oak farmhouse dining table with mismatched "
        "antique wooden chairs (some painted faded blue, some natural wood), simple linen napkins "
        "and earthenware ceramic plates, brass candlesticks. A 17th-century Tuscan painting on the "
        "wall, simple iron pendant light hanging low. Two tall windows with sheer linen curtains "
        "showing rolling Tuscan hills and cypress trees. Lived-in elegance, country aristocracy. "
        "Editorial photography 35mm, warm golden hour light, f/4."
    ),
    "pin-04-reschio-foresteria.jpg": (
        "Photorealistic guest suite at a Castello di Reschio-style luxury renovation, Umbrian-"
        "Tuscan rural luxury. Beautiful canopy bed in dark stained oak with white linen draping, "
        "original cotto antico floor restored, walls in pale dusty rose lime plaster, exposed "
        "wooden ceiling beams with darker patina. Vintage Persian rug in muted terracotta and "
        "indigo tones, a comfortable plush armchair in cream linen, brass nightstand with marble "
        "top, fluted brass wall sconces casting warm light, antique gilt-framed mirror. Tall French "
        "windows with internal wooden shutters open to a stone-arched balcony with view over "
        "vineyards. Refined yet rustic, monastic luxury. Editorial interior photography, soft "
        "late afternoon light filtering, 35mm f/4."
    ),
    "pin-05-cornue-cucina-pro.jpg": (
        "Photorealistic professional residential kitchen with La Cornue / Officine Gullo style "
        "range cooker as centerpiece, restaurant-quality appointed for a serious home cook. "
        "A massive 1.5m wide red enamel and brass La Cornue range with multiple ovens, integrated "
        "gas and induction surfaces. Surround in light oak cabinets with brushed brass handles, "
        "thick honed Carrara marble countertops, large central island with extra prep space. "
        "Pietra serena floor, pale plaster walls. Hanging copper pots from a ceiling rack, fresh "
        "herbs in small terracotta pots, professional knives on magnetic strip, 2 stainless steel "
        "sinks, integrated wine fridge in vertical cabinet. Tall window providing natural light. "
        "Style: chef's residential kitchen elegant and functional. Editorial 35mm f/5.6."
    ),
    "pin-06-bolle-lab-rurale.jpg": (
        "Photorealistic rural Tuscan farmhouse master bathroom in Bolle Lab style contemporary "
        "intervention. Floor in pietra serena tiles with bocciardata textured finish, walls in "
        "raw lime plaster with subtle terra di Siena pigment, ceiling with restored chestnut "
        "wooden beams. A freestanding cast-iron clawfoot bathtub in the center with brushed brass "
        "fixtures, a walk-in shower in the corner with frameless glass and pietra serena lining, "
        "twin sinks with handcrafted ceramic basins on a thick wooden vanity, brushed brass tap "
        "fixtures. A tall vertical window in stone surround providing view onto landscape, "
        "linen curtain. Vintage Persian runner, white linen towels rolled, a small bench in "
        "weathered wood. Spa-like serene atmosphere, masculine-feminine balance. Editorial "
        "photography, soft natural daylight, 35mm f/4."
    ),
}


OPENAI_IMAGE_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2")


def gen_image(prompt: str, out_path: Path, size: str = "1024x1024") -> bool:
    """Generate one image via OpenAI gpt-image-2."""
    print(f"  → generating {out_path.name} via {OPENAI_IMAGE_MODEL} ({len(prompt)} chars prompt)...", flush=True)
    try:
        resp = client.images.generate(
            model=OPENAI_IMAGE_MODEL,
            prompt=prompt,
            size=size,
            quality="high",
            n=1,
        )
        b64 = resp.data[0].b64_json
        img_bytes = base64.b64decode(b64)
        out_path.write_bytes(img_bytes)
        kb = len(img_bytes) // 1024
        print(f"    ✓ saved {out_path.name} · {kb} KB", flush=True)
        return True
    except Exception as e:
        print(f"    ✗ FAILED {out_path.name}: {e}", flush=True)
        return False


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    success = 0
    total = 0

    if target in ("foto", "all"):
        print("\n=== Stato attuale (1850 colonica · neglected) ===")
        FOTO_DIR.mkdir(parents=True, exist_ok=True)
        for name, prompt in STATO_ATTUALE_PROMPTS.items():
            total += 1
            if gen_image(prompt, FOTO_DIR / name):
                success += 1

    if target in ("pinterest", "all"):
        print("\n=== Pinterest references (tuscan country-modern) ===")
        PIN_DIR.mkdir(parents=True, exist_ok=True)
        for name, prompt in PINTEREST_REFS_PROMPTS.items():
            total += 1
            if gen_image(prompt, PIN_DIR / name):
                success += 1

    print(f"\n{'='*60}")
    print(f"Done · {success}/{total} images generated")
    print(f"  foto/        → {FOTO_DIR}")
    print(f"  pinterest/   → {PIN_DIR}")
    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
