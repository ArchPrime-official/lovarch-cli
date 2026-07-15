---
name: lovarch-moodboard
description: Genera un moodboard visivo (immagine + analisi) col Content Studio Lovarch — TU scrivi il brief del mood (zero crediti), la piattaforma genera (crediti). Trigger — "moodboard", "mood", "riferimento visivo", "atmosfera del progetto", "board di ispirazione", "moodboard per il render".
---

# Lovarch · Moodboard

Tu scrivi il brief del mood (a costo zero); la piattaforma genera l'immagine del
moodboard e la sua analisi, persistite nell'account dell'utente.

## Craft — un brief di mood che dà buoni risultati
- **Atmosfera** in 3-4 aggettivi (es. "caldo, materico, minimale, naturale").
- **Spazio/stanza** se pertinente (soggiorno, ufficio, esterno…).
- **Materiali e palette** di riferimento (legno, pietra, toni terrosi…).
- **Riferimenti** di stile (senza citare marchi/persone reali).

## Flusso
1. `lovarch context show --json` per stile/brand/lingua dell'utente.
2. Scrivi il brief.
3. Genera (avvisa dei crediti):
   ```
   lovarch_moodboard({ prompt: "<brief del mood>", space_type?: "...", room?: "..." })
   → { moodboard_image_url, analysis }
   ```
4. Usa il moodboard come riferimento per un render (`lovarch-render`) o per una
   proposta al cliente.

## Note
- Crediti solo per la generazione (mai costi in $). L'immagine finisce in galleria.
