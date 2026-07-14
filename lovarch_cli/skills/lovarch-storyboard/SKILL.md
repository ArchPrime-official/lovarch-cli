---
name: lovarch-storyboard
description: Dirige uno storyboard video multishot (più "piani"/scene in un solo video) col Content Studio Lovarch — TU scrivi la decomposizione in piani con continuità (zero crediti), la piattaforma renderizza (crediti). Trigger — "storyboard", "video con più scene", "multishot", "sequenza di piani", "video narrativo".
---

# Lovarch · Storyboard Director

Uno storyboard è UN video composto da N scene sequenziali ("piani") — non N clip
separate. Il valore sta nella CONTINUITÀ tra i piani: stesso soggetto, stesso
ambiente, luce coerente, linguaggio di camera che racconta. Tu scrivi la
decomposizione (a costo zero); la piattaforma renderizza il multishot.

## Craft — decomporre in piani (cinema)
Per un buon storyboard:
1. **Arco narrativo** — apertura → sviluppo → chiusura. Ogni piano ha uno scopo.
2. **Continuità** — mantieni il soggetto e l'ambiente coerenti tra i piani
   (descrivili allo stesso modo in ogni scena). Rispetta la regola dei 180°:
   non saltare il lato dell'azione tra un piano e l'altro.
3. **Varietà di piani** — alterna wide (stabilisce), medium (azione), close
   (emozione/dettaglio). Non ripetere lo stesso piano.
4. **Movimento coerente** — se un piano finisce con un movimento, il successivo
   lo raccoglie (match-on-action).
5. Ogni scena = 1 frase densa con soggetto + camera + luce.

## Flusso
1. `lovarch_context` per brand/stile (se serve personalizzazione).
2. **Scrivi TU i piani** (min 2, tipicamente 3-6), come array ordinato.
3. Avvisa dei crediti, poi genera con la tool MCP:
   ```
   lovarch_storyboard_video({
     scenes: [
       { prompt: "Piano 1 (wide): <regia con continuità>" },
       { prompt: "Piano 2 (medium): <stesso soggetto/ambiente, nuova angolazione>" },
       { prompt: "Piano 3 (close): <dettaglio/chiusura>" }
     ],
     aspect: "9:16"
   })
   → { job_id, scenes }
   ```
4. ASINCRONO: `lovarch_video_status({ job_id, engine: "kling" })` → quando `done`,
   mostra l'`output_url`. È UN solo video con i piani in sequenza (non N file).

## Note
- Lo storyboard usa il motore Kling multishot. Costa crediti (avvisa prima).
- Se l'utente vuole clip separate (non un video unico), usa invece `lovarch-video`.
