# Checklist · @quality-normativa

> **18 items** · 6 CRITICI + 7 SECONDARI + 5 MINORI

## Soglia PASS
- 100% CRITICI passano (6/6)
- ≥80% SECONDARI passano (almeno 6/7)
- ≥50% MINORI passano (almeno 3/5)

---

## 🔴 CRITICI (6) · 100% obbligatorio

### N-C1 · Tipo pratica corretto per intervento
**Verifica:** `tipo_pratica` in `tipo-pratica.json` corrisponde all'intervento descritto.
- Ristrutturazione interna senza prospetti né strutturali → **CILA**
- Modifiche prospetti **o** strutturali leggere → **SCIA**
- Demolizione + ricostruzione **o** ampliamento volumi → **SCIA alternativa o PdC**
**Fail action:** REJECT → @regolatorio-it

### N-C2 · Articoli DPR 380 citati esistono e si applicano
**Verifica:** Cross-check con Normattiva XML cached. Articolo cited deve esistere E essere in vigore E applicarsi al caso.
**Fail action:** REJECT → @regolatorio-it + @capitolato-writer

### N-C3 · Aut. paesaggistica considerata se zona vincolata
**Verifica:** Se Zona A1 PGT Milano OR vincolo paesaggistico/monumentale → autorizzazione paesaggistica DPR 31/2017 deve essere documentata.
**Fail action:** REJECT → @regolatorio-it + @pratiche-it

### N-C4 · CAM Edilizia 2025 voci rispettate ≥80%
**Verifica:** In `lista-CAM-rispettati.xlsx`, almeno 80% voci CAM applicabili (DM 23/06/2022 + agg. 2024) sono rispettate. Voci minimum:
- Calcestruzzo ≥15% riciclato
- Laterizio ≥30% riciclato
- Demolizione selettiva ≥70% recupero
- Legno FSC/PEFC certificato
- Isolanti con DAP/EPD
**Fail action:** REJECT → @capitolato-writer

### N-C5 · NTC 2018 cap 8 corretto
**Verifica:** Classificazione intervento secondo NTC 2018 cap 8:
- 8.4.1 Riparazione/locale → solo verifica locale
- 8.4.2 Miglioramento → valutazione sismica obbligatoria
- 8.4.3 Adeguamento → calcolo strutturale completo

Per ristrutturazione interna senza opere strutturali: 8.4.1 OK.
**Fail action:** REJECT → @regolatorio-it

### N-C6 · CSP/CSE valutato
**Verifica:** Se ≥2 imprese OR durata >200 g/uomo → CSP/CSE obbligatori (D.Lgs 81/2008).
Documento deve menzionare: "CSP/CSE necessario" e indicare nome professionista o "da nominare".
**Fail action:** REJECT → @regolatorio-it + @capitolato-writer

---

## 🟡 SECONDARI (7) · ≥80%

### N-S1 · Onorari ≥ parametri DM 17/06/2016 (L.49/2023)
Verifica calcolo onorari rispetta parametri ministeriali equo compenso.

### N-S2 · Vincoli PRG Milano Zona A1 rispettati
Se zona A1 NAF: divieto modifica facciata, conservazione tipologica, materiali tradizionali.

### N-S3 · UNI 11337 LOIN 300 verificato in IFC
Property sets ISO 12006-3 presenti, classificazione UniFormat/Uniclass.

### N-S4 · Bonus edilizi 2026 corretti
- No Superbonus (cessato per privati)
- Bonus Ristrutturazione 36% prima casa, 30% seconda
- Ecobonus 50% prima, 36% seconda
- Sismabonus 50%/36%

### N-S5 · IVA edilizia 10% ristrutturazione
Documenti finanziari includono IVA al 10% (non 22%) per opere di ristrutturazione DPR 633/72.

### N-S6 · Privacy GDPR clausole presenti
Informativa privacy include: titolare, finalità, base giuridica, conservazione, diritti, DPO se applicabile.

### N-S7 · Antiriciclaggio L.231 menzione obbligatoria
Contratto include clausola antiriciclaggio (L. 197/2014).

---

## 🟢 MINORI (5) · ≥50%

### N-M1 · Polizza RC professionale citata
Contratto menziona polizza RC architetto.

### N-M2 · Foro competente
Foro identificato (es. Foro di Milano).

### N-M3 · Mediazione obbligatoria
D.Lgs 28/2010: clausola mediazione preventiva obbligatoria.

### N-M4 · Citazioni con link Normattiva
Articoli cited hanno link/URL a Normattiva.it dove possibile.

### N-M5 · Banner aggiornamento
Documenti regolatori hanno banner "Ultimo aggiornamento DD/MM/2026".

---

## Output JSON

```json
{
  "qa_agent": "@quality-normativa",
  "verdict": "PASS" | "REJECT",
  "score": { "critical": "6/6", "secondary": "6/7", "minor": "4/5" },
  "items": [
    {
      "id": "N-C2",
      "severity": "CRITICO",
      "result": false,
      "issue": "DPR 380 art. 88 cited but article does not exist",
      "verified_against": "Normattiva XML 2024-12-01",
      "file": "analisi-regolamentare.pdf",
      "page": 3
    }
  ],
  "reject_target_agents": ["@regolatorio-it"]
}
```
