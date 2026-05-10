# Checklist · @quality-misure

> **24 items** · 5 CRITICI + 11 SECONDARI + 8 MINORI · Tolleranza ±1 mm

## Soglia PASS
- 100% CRITICI passano
- ≥80% SECONDARI passano (almeno 9/11)
- ≥50% MINORI passano (almeno 4/8)

Se anche 1 CRITICO fallisce → **REJECT**.

---

## 🔴 CRITICI (5)

### C1 · Somma quote orizzontali = larghezza totale parete
**Verifica:** Per ogni parete in `pianta-progetto.dxf`, somma delle quote orizzontali = lunghezza totale dichiarata.
**Tolleranza:** ±1 mm
**Source di verità:** geometria DXF
**Fail action:** REJECT → @cad-engineer

### C2 · Somma quote verticali = altezza totale parete
**Verifica:** Per ogni sezione, somma delle quote verticali = altezza totale.
**Tolleranza:** ±1 mm
**Fail action:** REJECT → @cad-engineer

### C3 · Sup. utile = somma sup. ambienti
**Verifica:** `superficie_utile_totale` in `schema-quotato.json` = somma di `ambienti[i].superficie_m2`.
**Tolleranza:** ±0.5%
**Fail action:** REJECT → @cad-engineer + @bim-engineer

### C4 · Sup. lorda = sup. utile + sup. murature
**Verifica:** `superficie_lorda` = `superficie_utile` + `muratura_m2`.
**Tolleranza:** ±0.5%
**Fail action:** REJECT → @cad-engineer

### C5 · Volume ambienti = sup × altezza
**Verifica:** Per ogni ambiente: `volume_m3` = `superficie_m2 × altezza_m`.
**Tolleranza:** ±0.1 m³
**Fail action:** REJECT → @bim-engineer

---

## 🟡 SECONDARI (11) · ≥80% (9/11)

### S1 · Spessore pareti UNI 8290
Pareti devono essere multipli di 8/10/12/15/25 cm.

### S2 · Larghezza minima passaggi
Tutti i passaggi/corridoi ≥ 80 cm (regolamento igienico Milano).

### S3 · Altezza minima ambienti residenziali
Tutti gli ambienti abitabili ≥ 270 cm Milano (RE Milano art. 38).
**Eccezione:** ambienti accessori (ripostigli) ≥ 240 cm.

### S4 · Sup. minima camera singola
≥ 9 m².

### S5 · Sup. minima camera doppia
≥ 14 m².

### S6 · Sup. cucina
≥ 9 m² (cucina autonoma) **oppure** angolo cottura ≥ 4 m² in living open-space.

### S7 · Bagno aerazione
Almeno 1 finestra **oppure** sistema VMC dichiarato.

### S8 · RAI (Rapporto Aero-Illuminante)
Sup. finestre ≥ 1/8 sup. pavimento per ogni ambiente abitabile (DM 5/7/1975).

### S9 · Quote in DXF leggibili
Text height ≥ 2.5mm in scala plot 1:50.

### S10 · Layer DXF segue ISO standard
Layer presenti: `CAD-A-WALL`, `CAD-A-DIM`, `CAD-A-DOOR`, `CAD-A-WIND`, `CAD-A-TEXT`, `CAD-A-SYMB`.

### S11 · Cartiglio CNAPPC compilato
Tutti i campi: architetto, n. Ordine, cliente, progetto, scala, data, fase, tavola.

---

## 🟢 MINORI (8) · ≥50% (4/8)

### M1 · Scala grafica presente
Indicata 1:50 o 1:100 in tavola.

### M2 · Nord magnetico indicato
Simbolo nord visibile in pianta.

### M3 · Nomi ambienti scritti
Ogni ambiente ha label testuale leggibile.

### M4 · Schede ambienti coerenti
Schede dettaglio ambienti coerenti con planimetria principale.

### M5 · Stato attuale vs progetto in 2 layer separati
Possibilità di toggle visualizzazione stato attuale / progetto.

### M6 · Sezioni AA/BB con riferimenti in pianta
Tracce di sezione in pianta con etichette AA, BB.

### M7 · Prospetti con altezze fronte e aperture
Prospetti includono quote verticali principali.

### M8 · Modello IFC volumi coerenti con DXF
Volumi calcolati da IFC differiscono da DXF di ≤ 2%.

---

## Output JSON format

```json
{
  "qa_agent": "@quality-misure",
  "execution_id": "uuid",
  "verdict": "PASS" | "REJECT",
  "score": {
    "critical": "5/5",
    "secondary": "9/11",
    "minor": "6/8",
    "total": "20/24"
  },
  "items": [
    {
      "id": "C1",
      "severity": "CRITICO",
      "description": "Somma quote orizzontali = larghezza totale parete",
      "result": true,
      "expected": "245.0 cm",
      "actual": "245.0 cm",
      "tolerance": "±1mm",
      "file": "pianta-progetto.dxf",
      "wall_id": "WALL-N-01"
    }
  ],
  "reject_target_agents": ["@cad-engineer"],
  "reject_summary": "Sup. utile differente sup. somma ambienti di 0.5 m². Cota Q12 errata."
}
```
