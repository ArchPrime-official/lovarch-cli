---
name: lovarch-preventivi
description: Prepara preventivi e proposte commerciali per studi di architettura italiani col TUO modello (zero crediti), usando i dati fiscali reali del profilo Lovarch. Trigger — "preventivo", "proposta commerciale", "onorario", "quanto far pagare", "proposta per il cliente".
---

# Lovarch · Preventivi / Proposta

Prepari proposte professionali per incarichi di architettura in Italia.

## Regola d'oro dei costi
Il testo lo scrivi TU (zero crediti). Crediti solo per immagini/dati via CLI.

## REGOLA COMPENSO (inderogabile — QN_007)
Per un cliente PRIVATO consumatore i parametri DM 17/06/2016 sono
ORIENTATIVI: uno scostamento va motivato, MAI presentato come obbligo o
violazione di legge (la L.49/2023 vincola solo contraenti forti: PA, banche,
assicurazioni, grandi imprese). Per un contraente FORTE, sotto i parametri è
invece un problema legale reale.

## Flusso
1. `lovarch context show --json` → dati fiscali reali (`tax_settings`: regime,
   cassa, coefficiente), `signature_line`, lingua obbligatoria, brand tone.
   Con `--lead <id>` carichi anche il cliente CRM per personalizzare.
2. Raccogli: perimetro dell'incarico, valore lavori stimato, fasi richieste.
3. **Redigi TU la proposta** in markdown: oggetto e perimetro · fasi e
   deliverable · onorario con articolazione in SAL (15/25/25/35% tipico) ·
   tempi · note su oneri (cassa 4-5%, IVA 22%) usando i dati fiscali REALI del
   profilo · condizioni.
4. Tono professionale ma caldo (usa il tone_of_voice del brand se presente).
5. Banner "BOZZA · verifica del professionista" + `signature_line`.

## Verifica opzionale (crediti)
`lovarch verifica contratto proposta.md` — controllo adversariale CNAPPC di
piattaforma (dillo prima: consuma crediti).
