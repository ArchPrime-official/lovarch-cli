#!/usr/bin/env python3
"""Generate photorealistic sample images for Attico Brera demo.

Replaces PIL placeholders with real AI-generated photos:
- 6 stato attuale (1980s mediocre renovation, dated aesthetic)
- 6 reference style photos (wabi-sabi · neoclassico contemporaneo · italian residential)

Uses OpenAI gpt-image-1 via direct API.
"""

import os
import sys
import base64
from pathlib import Path
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
FOTO_DIR = ROOT / "data" / "sample-input" / "foto"
PIN_DIR = ROOT / "data" / "sample-input" / "pinterest-references"

client = OpenAI()

STATO_ATTUALE_PROMPTS = {
    "01-facciata.jpg": (
        "Photorealistic exterior photo of a 1910 historic Milanese palazzo facade in Brera district, "
        "Via Fiori Chiari Milan. Italian neo-Renaissance style, ochre plaster walls with white stone "
        "framing around windows, original wrought iron balcony railings, weathered wooden shutters in "
        "warm green-grey, ground floor with arched portico. Real architectural photography, golden hour "
        "afternoon light, narrow cobblestone street perspective, slight wear and patina showing 100+ "
        "years of history. Camera: 35mm full-frame, f/8, eye-level shot. Documentary realism, "
        "no people, no cars."
    ),
    "02-ingresso.jpg": (
        "Photorealistic interior photo of a long narrow Italian apartment entrance corridor from a "
        "1980s mediocre renovation. Cold cream-white walls, dated polished marble travertine floor "
        "with grey veining, single hanging pendant lamp from the 80s with frosted glass, brown wooden "
        "doors with metal handles, narrow corridor about 1.2m wide and 5m long with three closed "
        "doors visible. Some small wear marks on walls, electrical outlets visible, dated white plastic "
        "switches. Slightly cluttered, real-estate photography style, neutral indoor lighting, "
        "documentary not aspirational. Camera: 24mm wide, f/5.6."
    ),
    "03-soggiorno.jpg": (
        "Photorealistic interior of a Milanese living room in a 1910 building with 1980s renovation. "
        "Original Venetian seminato terrazzo flooring with warm earth tones (terracotta, cream, ochre), "
        "preserved decorated coffered ceiling with subtle stucco details typical of early 1900s "
        "Italian palazzo. Dated 1980s elements: a beige tiled wall behind a dark wood unit with TV "
        "from the 90s, brown velvet sofa, ugly aluminum-frame split AC unit mounted high on the wall. "
        "Tall French window leading to a terrace with old aluminum frame. Warm afternoon natural light. "
        "Real estate photography, 24mm lens, slight clutter, lived-in but dated, NOT staged. "
        "Documentary realism."
    ),
    "04-cucina.jpg": (
        "Photorealistic interior of a narrow Italian kitchen from a 1980s renovation, only about 2.5m "
        "wide. Cheap brown laminate cabinets with brass handles, dated beige ceramic tile backsplash "
        "with floral motifs, white melamine countertop with rounded edges, old gas stove with 4 burners, "
        "small white domestic refrigerator from 90s on the right, single small window with frosted "
        "glass at the end. Beige terracotta floor tiles. Yellowish fluorescent ceiling light. "
        "Cramped, functional, dated, real-estate photo, not aspirational. 24mm, neutral light."
    ),
    "05-camera-padronale.jpg": (
        "Photorealistic Italian master bedroom about 12 sqm, 1910 building 1980s renovation. "
        "Preserved original decorated stucco ceiling rosette in cream and pale grey, but room itself "
        "is small and dated. Beige walls, aged parquet wood floor with darker tones near edges, "
        "a wardrobe with mirrored doors from the 80s, plain double bed with simple cream linens, "
        "outdated wall sconces, single window with white aluminum frame. Modest split AC visible. "
        "Awkward proportions making it feel cramped. Real-estate photo, soft window daylight, "
        "no staging, dated, documentary."
    ),
    "06-bagno.jpg": (
        "Photorealistic interior of a small windowless Italian bathroom (bagno cieco) from 1980s "
        "renovation. Mottled beige and pink ceramic tiles on walls floor to ceiling, ugly geometric "
        "patterns, white porcelain sink with chrome faucet from the 80s, plain white toilet and bidet, "
        "small old shower stall in the corner with frosted plastic doors and limescale stains, "
        "dated white framed mirror with fluorescent light strip above, ventilation grate on ceiling. "
        "Cramped 5 sqm, beige tile floor matching walls. Yellowish artificial light, no natural light, "
        "claustrophobic feel. Real-estate photo, dated, urgent renovation needed, documentary realism."
    ),
}

PINTEREST_REFS_PROMPTS = {
    "pin-01-de-cotiis.jpg": (
        "Photorealistic interior of an exclusive Milanese palazzo apartment, modernist contemporary "
        "intervention inside a 1900s historic shell. Polished cement floor with subtle veining, "
        "original ornate stucco ceiling preserved and slightly aged, warm white walls with patina "
        "treatment, large abstract artwork, brutalist concrete coffee table with smooth bronze sculpture, "
        "low-profile sofa in raw natural linen pale cream, antique brass floor lamp. Atmosphere is "
        "monastic and refined, dialog between old and new, material honesty. Soft north light from "
        "tall window. Editorial interior photography, 35mm, f/4, wide composition. No clutter."
    ),
    "pin-02-studiopepe.jpg": (
        "Photorealistic Italian residential living room with sophisticated warm earth tones palette: "
        "terracotta, ochre, dusty rose, sage green. Hand-painted decorative wall in geometric pattern "
        "with matte finish, herringbone parquet oak floor, curved velvet sofa in dusty rose, round "
        "marble coffee table in beige travertine, sculptural ceramic vases, brass arc lamp, vintage "
        "Italian armchair in caramel leather. Layered textiles, warm afternoon light through tall "
        "window with linen curtains. Style: contemporary Italian eclectic, female-driven aesthetic, "
        "bold but refined. Editorial photography 50mm f/2.8."
    ),
    "pin-03-marcante-testa.jpg": (
        "Photorealistic Italian apartment in a Turin historic building, contemporary renovation that "
        "celebrates restored decorated ceilings with bold pastel colors. Pale pink walls, restored "
        "ornate ceiling rosette in cream and gold, polished oak parquet, mid-century modern furniture: "
        "saffron yellow Cassina-style armchair, blue velvet ottoman, glass and brass coffee table, "
        "abstract artwork, plenty of natural light. Bright cheerful but sophisticated. Italian eclectic "
        "warm contemporary. Editorial interior photography, 35mm, daylight."
    ),
    "pin-04-vilon.jpg": (
        "Photorealistic Roman boutique hotel suite interior with refined neoclassic-contemporary mix. "
        "Original Venetian seminato terrazzo floor in cream-pink-grey tones, restored decorated "
        "ceiling with classical motifs, warm cream walls, contemporary canopy bed in pale linen, "
        "gold-framed mirror, fluted brass wall sconces, plump linen armchair, brass nightstand with "
        "marble top, tall French windows with sheer curtains, vintage Persian rug in muted tones. "
        "Cozy and luxurious, masculine-feminine balance. Editorial photo, golden hour, 35mm f/4."
    ),
    "pin-05-cassina.jpg": (
        "Photorealistic upscale Italian living room featuring iconic mid-century Italian design. "
        "Cream Maralunga-style modular sofa with curved soft cushions, Cab black leather chairs around "
        "an oval glass dining table, Castiglioni Arco-style floor lamp with marble base and brass arc, "
        "warm parquet oak floor, off-white walls, large abstract painting, sculptural side table. "
        "Restrained, elegant, Italian classical contemporary. Soft natural light, editorial photography "
        "50mm f/4, refined neutral palette."
    ),
    "pin-06-devon-devon.jpg": (
        "Photorealistic high-end Italian kitchen with light oak natural wood cabinetry, classic shaker "
        "doors with polished brass handles, large central island with thick honed granite countertop "
        "in pale beige speckled with grey, brass faucet, linear pendant lights with frosted glass globes, "
        "honed travertine backsplash, warm white walls, light oak parquet floor, comfortable wooden "
        "stools at the island, fresh herbs and ceramic bowls on counter. Devon-Devon-Cassina-Boffi style "
        "blend. Bright window light, editorial photography, 35mm f/5.6."
    ),
}


OPENAI_IMAGE_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2")  # latest released 2026-04-21


def gen_image(prompt: str, out_path: Path, size: str = "1024x1024") -> bool:
    """Generate one image via OpenAI gpt-image-2 (mirror archchat-generate-image)."""
    print(f"  → generating {out_path.name} via {OPENAI_IMAGE_MODEL} ({len(prompt)} chars prompt)...", flush=True)
    try:
        resp = client.images.generate(
            model=OPENAI_IMAGE_MODEL,
            prompt=prompt,
            size=size,
            quality="high",  # mirror edge function archchat-generate-image
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
        print("\n=== Stato attuale (1980s mediocre renovation) ===")
        FOTO_DIR.mkdir(parents=True, exist_ok=True)
        for name, prompt in STATO_ATTUALE_PROMPTS.items():
            total += 1
            if gen_image(prompt, FOTO_DIR / name):
                success += 1

    if target in ("pinterest", "all"):
        print("\n=== Pinterest references (style refs) ===")
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
