---
name: lovarch-reel
description: Dirige un reel/short verticale completo col Content Studio Lovarch — TU scrivi hook, script e regia (zero crediti), la piattaforma genera video + voce (crediti). Trigger — "reel", "short", "video verticale", "tiktok", "video social", "reels instagram".
---

# Lovarch · Reel Director

Un reel che funziona vive o muore nei primi 3 secondi. Tu scrivi hook + script +
regia (a costo zero); la piattaforma genera il video e, se serve, la voce.

## Craft — anatomia di un reel che trattiene
1. **Hook (0-3s)** — la prima frase/immagine deve fermare lo scroll. Pattern che
   funzionano: domanda scomoda, promessa specifica ("in 30s ti mostro…"), tensione
   ("stai sbagliando X"), risultato mostrato subito. MAI intro lente o loghi.
2. **Retention (3s-metà)** — una sola idea, ritmo veloce, open loop ("e poi
   succede una cosa…"). Ogni secondo giustifica il successivo.
3. **Payoff + CTA (finale)** — mantieni la promessa dell'hook e chiudi con UN
   invito chiaro (segui / salva / commenta).
4. **Formato** — 9:16 sempre. Testo grande, leggibile senza audio.
5. **Voce (opzionale)** — narrazione ElevenLabs sopra il video per ritmo.

## Flusso
1. `lovarch_context` per brand/stile/lingua.
2. **Scrivi TU**: hook (1 frase forte) + 2-4 beat di script + la regia visiva
   (usa il craft della skill `lovarch-video`: camera, luce, movimento).
3. Avvisa dei crediti, poi genera il video:
   ```
   lovarch_generate_video({ prompt: "<hook visivo + regia>", engine: "seedance-text", aspect: "9:16" })
   → { job_id, engine } ; poi lovarch_video_status({ job_id, engine })
   ```
4. (Opzionale) genera la narrazione:
   ```
   lovarch_tts({ text: "<script parlato, ritmo veloce>" })  → audio_url
   ```
5. Il video e l'audio finiscono in galleria. Il montaggio finale (video+voce+
   sottotitoli) si completa nel Content Studio dell'app (timeline).

## Note
- Per una sequenza narrativa di più scene in UN video usa `lovarch-storyboard`.
- Costa crediti (video + eventuale voce) — avvisa PRIMA con il totale.
