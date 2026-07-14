---
name: lovarch-branding
description: Dirige l'identità visiva (logo + palette) col Content Studio Lovarch — TU scrivi il brief di brand (zero crediti), la piattaforma genera logo e colori (crediti). Trigger — "logo", "identità visiva", "brand", "marchio", "palette", "colori del brand", "identidade visual".
---

# Lovarch · Branding Director

Tu scrivi il brief di brand (a costo zero); la piattaforma genera il logo e la
palette, coerenti col profilo dell'utente.

## Craft — un brief di brand che dà buoni risultati
1. **Personalità** — 3 aggettivi del brand (es. "essenziale, caldo, artigianale").
2. **Settore + pubblico** — studio di architettura? interior? per che cliente?
3. **Stile del logo** — geometrico / tipografico / simbolico / minimale.
4. **Riferimenti** — cosa evitare (troppo corporate? troppo playful?).
5. Il prompt del logo deve descrivere il SIMBOLO e il feeling, non chiedere testo.

## Flusso
1. `lovarch_context` → brand/stile/palette già esistenti (per coerenza).
2. **Logo** (avvisa dei crediti):
   ```
   lovarch_generate_logo({ prompt: "<brief: personalità + stile simbolo>" })  → { logo_url }
   ```
   Per iterare su un logo esistente passa `existing_logo_url`.
3. **Palette** (usa il contesto del brand):
   ```
   lovarch_generate_colors({})  → { palette }
   ```
   Oppure passa `brand_context`/`style_context` per guidarla.

## Note
- Tutto in crediti. Logo e palette finiscono nell'account (brand-assets/profilo).
- Per un moodboard visivo completo (analisi di immagini) usa l'app (non ancora
  esposto via conector).
