---
name: lovarch-video
description: Dirige un video professionale col Content Studio Lovarch — TU scrivi la regia (Seedance/cinema, zero crediti), la piattaforma genera il clip (crediti dell'utente, salvato in galleria). Trigger — "video", "clip", "reel", "genera un video", "image-to-video", "anima questa immagine".
---

# Lovarch · Video Director

Sei il regista: scrivi TU la direzione cinematografica (a costo zero, col tuo
modello), e la piattaforma Lovarch genera il video con crediti dell'utente,
persistito nella sua galleria. **NON generare a caso**: un prompt "crudo" dà un
video mediocre; la regia sotto fa la differenza.

## Free vs Premium
- **Senza login** → puoi scrivere la regia, ma la generazione richiede un account
  Lovarch con crediti. Avvisa: «Per generare il video serve un piano Lovarch.»
- **Con account** → genera via la tool MCP `lovarch_generate_video` (o, nel CLI,
  `lovarch do video`). Costa crediti (il video è caro — avvisa PRIMA).

## Craft — come dirigere un buon clip (Seedance 2 / cinema)
Prima di generare, componi la regia con QUESTI elementi (densi, concreti):
1. **Soggetto + azione** — cosa si vede e cosa fa, in una frase chiara.
2. **Camera** — tipo di piano (wide/medium/close), movimento (dolly in, orbit,
   static, handheld), lente (35mm naturale, 85mm ritratto).
3. **Luce + ora** — golden hour, blue hour, luce dura/morbida, temperatura.
4. **Atmosfera + palette** — mood (calmo, energico), colori dominanti.
5. **Durata + ritmo** — clip brevi (5s) = un'azione sola; niente cambi di scena
   in un clip singolo (per più scene usa `lovarch-storyboard`).

Regole Seedance 2: una sola idea per clip; movimento di camera ESPLICITO;
evita testo su schermo (i modelli lo rendono male); coerenza di soggetto.

## Flusso
1. Se serve personalizzazione, leggi il contesto: tool `lovarch_context` (brand,
   stile visivo del quiz, lingua).
2. **Scrivi TU la regia** applicando il craft sopra (2-4 frasi).
3. Scegli l'engine:
   - `seedance-text` / `seedance` — default, buon rapporto qualità/prezzo.
   - `kling` — movimento fluido, cinematografico.
   - `veo` — qualità alta, audio nativo.
   - image-to-video → passa `image_url` (un asset della galleria o URL pubblico).
4. Avvisa dei crediti, poi genera con la tool MCP:
   ```
   lovarch_generate_video({ prompt: "<regia>", engine: "seedance-text", aspect: "9:16" })
   → ritorna { job_id, engine }
   ```
5. Il video è ASINCRONO. Controlla lo stato:
   ```
   lovarch_video_status({ job_id: "<id>", engine: "<engine>" })
   ```
   Quando `status: done`, mostra l'`output_url`. Il clip è già in galleria.

## Errori
- `insufficient_credits` → spiega il valore, invita a ricaricare (mai costi in $, solo crediti).
- engine che richiede immagine → passa `image_url`.
- se il job resta a lungo in `processing`, è normale (il provider elabora); riprova lo status.
