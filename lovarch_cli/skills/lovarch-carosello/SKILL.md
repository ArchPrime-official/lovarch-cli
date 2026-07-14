---
name: lovarch-carosello
description: Dirige un carosello social (Instagram/LinkedIn) col Content Studio Lovarch — TU scrivi leva, headline e narrativa slide-per-slide (zero crediti), la piattaforma genera le immagini (crediti). Trigger — "carosello", "carousel", "post multi-slide", "carrossel", "sequenza di slide".
---

# Lovarch · Carosello Director

Un buon carosello non è N immagini a caso: è una NARRATIVA che trattiene. Tu
scrivi la struttura (a costo zero); la piattaforma genera le slide (crediti).

## Craft — struttura di un carosello che funziona
1. **Leva + hook (slide 1)** — la copertina deve fermare lo scroll: promessa
   chiara, tensione o curiosità. Una frase forte, non un titolo generico.
2. **Sviluppo (slide 2..N-1)** — un'idea per slide, progressione logica; ogni
   slide "apre" la successiva (open loop). Testo breve, leggibile su mobile.
3. **Chiusura + CTA (ultima slide)** — sintesi + invito all'azione chiaro.
4. **Estetica coerente** — palette del brand, stesso stile visivo in tutte le
   slide, formato 4:5 (feed) o 9:16 (story).
5. Numero di slide: 5-8 è l'ideale (min 3, max 10).

## Flusso
1. `lovarch_context` per brand/stile/palette (personalizzazione).
2. **Scrivi TU** la leva, la headline e il testo di ogni slide + una descrizione
   visiva coerente per le immagini.
3. Avvisa dei crediti, poi genera con la tool MCP:
   ```
   lovarch_carousel({ theme: "<tema + struttura narrativa>", slides: 6, aspect: "4:5" })
   → genera le slide, salvate in galleria (carousel_id)
   ```
4. Le immagini finiscono nella galleria dell'utente. Rivedi e, se serve,
   rigenera una slide o affina il tema.

## Note
- Costa crediti (una generazione per slide) — avvisa PRIMA con il totale stimato.
- Per un reel/video usa `lovarch-video`; per uno storyboard multishot `lovarch-storyboard`.
