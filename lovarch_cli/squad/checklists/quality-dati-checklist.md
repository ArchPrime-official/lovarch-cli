# Checklist · @quality-dati

> **16 items** · 6 CRITICI + 5 SECONDARI + 5 MINORI · Cross-check inter-document

## Soglia PASS
- 100% CRITICI passano (6/6)
- ≥80% SECONDARI passano (almeno 4/5)
- ≥50% MINORI passano (almeno 3/5)

## Principio
**Lo stesso dato non può apparire con valori differenti in documenti diversi.** Sup. lorda nella pianta deve essere identica alla sup. lorda nella CILA. Importo nel computo deve essere identico al contratto. Etc.

---

## 🔴 CRITICI (6)

### D-C1 · Sup. lorda pianta = IFC = CILA
**Source di verità:** geometria DXF di `@cad-engineer`
**Comparison points:**
- `pianta-progetto.dxf` (sup. lorda calcolata da geometria)
- `modello.ifc` (sum di IfcSlab pianoterra/superiore)
- `CILA-precompilata.pdf` (campo "superficie utile lorda")
**Tolleranza:** ±0.5%
**Fail action:** REJECT → tutti gli agenti coinvolti

### D-C2 · Volumi parete IFC = quantità computo
**Comparison points:**
- `quantitativi.json` da `@bim-engineer`
- `computo-metrico.xlsx` voci muratura
**Tolleranza:** ±2%
**Fail action:** REJECT → @bim-engineer + @computo-engineer

### D-C3 · Totale computo = capitolato = contratto
**Comparison points:**
- `computo-metrico.xlsx` riga TOTALE
- `capitolato-speciale.pdf` valore opera dichiarato
- `contratto-servizi.pdf` valore opera nel preambolo
**Tolleranza:** ±€0.01 (centesimi arrotondamento)
**Fail action:** REJECT → @computo-engineer + @capitolato-writer + @contratto-architect

### D-C4 · Indirizzo identico in CILA + contratto + paesaggistica
**Comparison points:**
- `CILA-precompilata.pdf`
- `contratto-servizi.pdf`
- `paesaggistica-bozza.pdf`
**Tolleranza:** case-insensitive, normalizzazione spazi
**Fail action:** REJECT → @pratiche-it + @contratto-architect

### D-C5 · Dati catastali coerenti con visura
**Comparison:** foglio + mappale + subalterno in CILA = visura catastale.
**Fail action:** REJECT → @pratiche-it

### D-C6 · Cronoprogramma 90gg coerente con timeline cliente
**Comparison points:**
- `cronoprogramma-90gg.pdf` durata totale
- `timeline-90gg-cliente.pdf` data inizio/fine
- `contratto-servizi.pdf` durata dichiarata
**Tolleranza:** ±2 giorni
**Fail action:** REJECT → @capitolato-writer + @deliverable-builder

---

## 🟡 SECONDARI (5) · ≥80%

### D-S1 · Materiali capitolato = computo = EPDs LCA
Materiali specificati in `capitolato-speciale.pdf` corrispondono a quelli in `computo-metrico.xlsx` corrispondono a quelli in `LCA-embodied-carbon.pdf`.

### D-S2 · Onorari preventivo = importo contratto
`preventivo-onorari.pdf` totale = `contratto-servizi.pdf` art. compenso.

### D-S3 · P.IVA studio identico ovunque
P.IVA architetto in tutti i documenti.

### D-S4 · Numero protocollo Ordine Architetti
Numero iscrizione coerente in tutti i documenti.

### D-S5 · CF cliente identico CILA + contratto + privacy
Codice Fiscale cliente formattato identicamente (uppercase, no spaces).

---

## 🟢 MINORI (5) · ≥50%

### D-M1 · Date coerenti
Firma contratto ≤ data inizio progetto ≤ data inizio lavori.

### D-M2 · Naming convention
Pattern `NN-categoria-nome.ext` rispettato in tutti i file della cartella.

### D-M3 · Versioni documento
Tutti i PDF hanno indicazione versione (es. "v1.0", "rev. 0").

### D-M4 · Manifest.json
File `manifest.json` esiste in root con SHA256 di ogni deliverable.

### D-M5 · Lingua corretta
Tutti i documenti tecnici sono in italiano (IT-IT). Solo presentazione cliente può essere multilingue.

---

## Output JSON

```json
{
  "qa_agent": "@quality-dati",
  "verdict": "PASS" | "REJECT",
  "score": { "critical": "6/6", "secondary": "4/5", "minor": "5/5" },
  "diffs_log": [
    {
      "id": "D-C3",
      "severity": "CRITICO",
      "field": "Totale lavori",
      "occurrences": [
        { "file": "computo-metrico.xlsx", "value": "180000.00", "row": "TOTALE" },
        { "file": "capitolato-speciale.pdf", "value": "180.000,00", "page": 3 },
        { "file": "contratto-servizi.pdf", "value": "180000.00", "page": 1 }
      ],
      "result": true
    },
    {
      "id": "D-C2",
      "severity": "CRITICO",
      "field": "Volume muratura demolita",
      "occurrences": [
        { "file": "quantitativi.json", "value": "18.5", "key": "muri_demolizione_m2" },
        { "file": "computo-metrico.xlsx", "value": "19.2", "row": "VOCE-D-001" }
      ],
      "result": false,
      "diff": "0.7 m² (3.7%)"
    }
  ],
  "reject_target_agents": ["@bim-engineer", "@computo-engineer"]
}
```
