---
name: lovarch-verifica-normativa
description: Verifica ADVERSARIALE delle citazioni normative edilizie italiane in un documento — col TUO modello (zero crediti), con opzione di doppia verifica di piattaforma. Trigger — "verifica normativa", "controlla i riferimenti", "questo documento cita bene le norme?", "articoli di legge corretti?".
---

# Lovarch · Verifica Normativa (adversariale)

Verifichi le citazioni normative di documenti edilizi italiani cercando
attivamente di CONFUTARLE. Nel dubbio, sii scettico e segnala.

## Regola d'oro dei costi
La verifica la fai TU (zero crediti). La doppia verifica di piattaforma è
opzionale e consuma crediti — dillo prima.

## Tabella canonica (riferimenti che DEVI riconoscere)
- DPR 380/2001 · Testo unico edilizia (⚠️ art. 99 = conglomerato cementizio
  armato, NON le CILA; le CILA sono art. 6-bis)
- UNI 11337 · gestione digitale/BIM
- CAM Edilizia · D.M. 23/06/2022 (criteri ambientali minimi)
- NTC 2018 · DM 17/01/2018 (norme tecniche costruzioni)
- D.Lgs 81/2008 · sicurezza cantieri (art. 90: CSP/CSE; art. 99: notifica preliminare)
- D.Lgs 42/2004 · codice beni culturali/paesaggio (art. 142)
- L. 49/2023 · equo compenso — SOLO contraenti forti (PA/banche/grandi imprese);
  per cliente privato i parametri DM 17/06/2016 sono orientativi
- GDPR · Reg. UE 2016/679

## Flusso
1. Leggi il documento (chiedi il file/testo se non fornito).
2. **Estrai** ogni citazione normativa + cosa il documento AFFERMA che regoli.
3. **Confuta** ciascuna: l'articolo esiste? Regola davvero questo? Status per
   citazione: ✓ ok · ✗ refuted (con motivo) · ? doubt.
4. **Verdetto**: REJECT se ≥1 refuted · CONCERNS se doubt · PASS altrimenti.
   Report in tabella, nella lingua dell'utente (`lovarch context show --json`
   → preferences.preferred_language).
5. **Doppia verifica di piattaforma (opzionale, crediti)** — un secondo paio di
   occhi indipendente (Sonnet estrae → Opus refuta lato Lovarch):
   ```bash
   lovarch verifica normativa documento.pdf
   ```
6. Per DXF: `lovarch verifica misure file.dxf` è deterministico e GRATUITO.
