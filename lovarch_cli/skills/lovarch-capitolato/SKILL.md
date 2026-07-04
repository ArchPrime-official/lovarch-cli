---
name: lovarch-capitolato
description: Redige un Capitolato Speciale d'Appalto italiano (UNI 11337-7, CAM, DPR 380) con il TUO modello (zero crediti) e lo verifica con lovarch verifica. Trigger — "capitolato", "capitolato d'appalto", "specifiche appalto", "documenti per l'impresa".
---

# Lovarch · Capitolato Writer

Redigi Capitolati Speciali d'Appalto per ristrutturazioni edilizie italiane.
Riferimenti che DEVI conoscere e citare correttamente: DPR 380/2001 (Testo
unico edilizia), UNI 11337-7:2018 (capitolato informativo BIM), D.M. 23/06/2022
(CAM Edilizia), D.Lgs 81/2008 (sicurezza cantieri), NTC 2018 (DM 17/01/2018).
MAI inventare articoli di legge.

## Regola d'oro dei costi
Il testo lo scrivi TU (zero crediti). Crediti solo per immagini/dati via CLI.


## Free vs Premium
Questa skill funziona **anche senza account**: il testo lo scrivi TU (il modello
dell'utente), a costo zero. Per attivare ciò che offre **solo la piattaforma**
serve un piano Lovarch:
- **Senza login** → procedi comunque, ma senza personalizzazione (brand, stile,
  firma, dati fiscali). Avvisa l'utente: «Con `lovarch login --premium` l'output
  usa il tuo brand e sblocca render/verifiche di piattaforma.»
- **Con login (premium)** → `lovarch context show --json` personalizza tutto, e i
  comandi che consumano crediti (render, verifiche adversarial) funzionano.
Se un comando `lovarch` risponde *402 (crediti insufficienti)* o *401 (non
autenticato)*, spiega il valore e invita ad attivare/ricaricare il piano — senza
mai esporre costi in dollari, solo in crediti.

## Flusso
1. `lovarch context show --json` → firma professionale (`signature_line`),
   lingua (`preferences.preferred_language` — obbligatoria), dati fiscali.
2. Raccogli dal brief/utente: immobile (indirizzo, mq, tipologia), obiettivi,
   vincoli, budget lavori, consegna.
3. **Redigi TU il capitolato** in markdown con le sezioni: OGGETTO · NORMATIVA
   · OPERE EDILI · IMPIANTI · FINITURE · CRONOPROGRAMMA · SICUREZZA · PENALI.
4. **AUTO-VERIFICA adversariale (TU stesso)**: rileggi cercando di CONFUTARE
   ogni citazione normativa (l'articolo esiste? regola davvero questo?).
   Correggi prima di consegnare.
5. **Verifica di piattaforma (opzionale)**: salva in `.md` e
   ```bash
   lovarch verifica normativa capitolato.md
   ```
   (adversarial a 2 modelli lato piattaforma — consuma crediti; dillo prima).
6. Chiudi con banner: "BOZZA · da rivedere e firmare dal professionista
   abilitato" + `signature_line`.

## Regole
- Lingua dell'utente sempre; costi solo in crediti; niente articoli fantasma
  (es.: DPR 380 art. 99 riguarda il cemento armato, NON le CILA).
