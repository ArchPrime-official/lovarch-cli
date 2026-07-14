---
name: lovarch-post
description: Dirige un'immagine social singola (post feed/story) col Content Studio Lovarch — TU scrivi il concept e la regia visiva (zero crediti), la piattaforma genera l'immagine (crediti). Trigger — "post", "immagine social", "grafica instagram", "single image", "creativo", "visual per feed".
---

# Lovarch · Post / Single Image

Tu scrivi il concept e la regia visiva (a costo zero); la piattaforma genera
l'immagine con gpt-image-2, persistita in galleria.

## Craft — un'immagine social che si distingue
1. **Un messaggio solo** — l'immagine comunica UNA idea. Niente affollamento.
2. **Composizione** — soggetto chiaro, spazio negativo, gerarchia visiva. Regola
   dei terzi. Per il feed usa 4:5 (più area verticale), per story 9:16.
3. **Palette del brand** — coerente con `lovarch_context` (stile del quiz + brand).
4. **Testo nell'immagine** — GPT Image 2 rende bene il testo: se serve una
   headline nell'immagine, scrivila esplicitamente nel prompt tra virgolette.
5. **Luce e materia** — descrivi luce (morbida/dura), materiali, mood.

## Flusso
1. `lovarch_context` per brand/stile/palette.
2. **Scrivi TU** il concept + la regia visiva densa.
3. Genera (avvisa dei crediti):
   ```
   lovarch_generate_image({ prompt: "<concept + regia + eventuale headline>", quality: "high", aspect: "4:5" })
   → asset_url (in galleria)
   ```
   Per editare un'immagine esistente: mode "edit" + image_urls.

## Note
- Costa crediti (per immagine). L'immagine finisce in galleria.
- Per una sequenza di slide usa `lovarch-carosello`; per video `lovarch-video`.
