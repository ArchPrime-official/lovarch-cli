---
name: lovarch-voce
description: Genera narrazione (voce) e musica col Content Studio Lovarch — TU scrivi lo script col ritmo giusto (zero crediti), la piattaforma genera l'audio (crediti). Trigger — "voce", "narrazione", "voiceover", "speak", "text to speech", "musica di sottofondo", "colonna sonora".
---

# Lovarch · Voce & Musica

Tu scrivi lo script (a costo zero); la piattaforma genera l'audio (ElevenLabs),
persistito in galleria come URL.

## Craft — uno script parlato che suona bene
- **Frasi brevi**, una idea per frase. La TTS respira meglio con punteggiatura.
- **Ritmo** — alterna frasi corte e medie; usa i punti per le pause.
- **Tono** coerente col brand (autorevole, caldo, energico) — dichiaralo all'inizio.
- Evita sigle e numeri lunghi non scritti per esteso (la TTS li legge male).

## Flusso — voce (TTS)
1. `lovarch_context` per lingua e tono del brand.
2. **Scrivi TU** lo script.
3. Genera (avvisa dei crediti):
   ```
   lovarch_tts({ text: "<script>", voice_id: "<opzionale>" })  → { audio_url }
   ```
   Voce default = Rachel. Per una voce diversa passa un voice_id ElevenLabs.

## Flusso — musica
```
lovarch_music({ mood: "uplifting", genre: "cinematic", intensity: "medium", duration: 30 })
→ { audio_url }
```
Descrivi mood + genere coerenti col contenuto (es. reel energico → mood energico).

## Note
- Tutto in crediti (mai costi in $). L'audio finisce in galleria.
- Per un reel completo (video + voce) usa `lovarch-reel`.
