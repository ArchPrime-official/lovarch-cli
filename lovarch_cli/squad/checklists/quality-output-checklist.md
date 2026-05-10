# Checklist · @quality-output

> **14 items** · 6 CRITICI + 5 SECONDARI + 3 MINORI · Completezza + leggibilità

## Soglia PASS
- 100% CRITICI passano (6/6)
- ≥80% SECONDARI passano (almeno 4/5)
- ≥50% MINORI passano (almeno 2/3)

---

## 🔴 CRITICI (6)

### O-C1 · 25+ deliverable presenti
**Verifica:** Counting di tutti i file nelle cartelle 01- → 08-. Deve essere ≥25.
**Lista minima attesa:**
- 01-briefing/ (3 files)
- 02-concept/ (>15 files: 9 moodboard + 6 render + 4 doc)
- 03-progetto-definitivo/ (5 files)
- 04-pratiche-comune/ (4-6 files)
- 05-impresa/ (5 files + DOSSIER.zip)
- 06-ingegneri/ (3-5 files)
- 07-cliente/ (5 files)
- 08-studio-interno/ (4-5 files)
**Fail action:** REJECT → @deliverable-builder + agenti specifici mancanti

### O-C2 · Ogni PDF apre senza errore
**Verifica:** Per ogni .pdf, `pypdf.PdfReader(file)` non solleva eccezione e `extract_text()` su prima pagina restituisce contenuto non vuoto.
**Fail action:** REJECT → agente che ha generato il PDF

### O-C3 · DXF aprono in QCAD/AutoCAD
**Verifica:** `ezdxf.readfile(file)` parsing successful. Documento ha entities.
**Fail action:** REJECT → @cad-engineer

### O-C4 · IFC valido
**Verifica:** `ifcopenshell.validate(file)` returns no critical errors.
**Fail action:** REJECT → @bim-engineer

### O-C5 · XLSX aprono
**Verifica:** `openpyxl.load_workbook(file)` succeed. File contiene worksheet con dati.
**Fail action:** REJECT → @computo-engineer + @capitolato-writer

### O-C6 · File uploaded → Lovarch pm_documents
**Verifica:** Per ogni file in cartella locale, verificar (a) row in `pm_documents` esiste con SHA256 corrispondente, (b) `public_url` accessibile (HTTP 200).
**Fail action:** REJECT → @progetto-chief (responsabile upload)

---

## 🟡 SECONDARI (5) · ≥80%

### O-S1 · Naming convention
Pattern `NN-categoria-nome.ext` (es. `01-briefing-strutturato.pdf`).

### O-S2 · Dimensione PDF tavole ≤ 50 MB
Tavole tecniche compresse correttamente.

### O-S3 · Render PNG ≥ 4K resolution
Almeno 3840×2160. Nessun render < 1920×1080 nel deliverable cliente.

### O-S4 · Portal URL accessibile
GET HTTP del portale cliente returns 200 + HTML válido (contains expected metatags).

### O-S5 · Presentazione HTML responsive mobile
Test viewport 375×812 (iPhone): no horizontal scroll, fonts ≥14px, buttons ≥44px.

---

## 🟢 MINORI (3) · ≥50%

### O-M1 · README.md indice generato
File `README.md` in root cartella con tabella di tutti i deliverable + descrizione.

### O-M2 · Git commit con tag versione
Commit creato con tag `squad-v1.0-{timestamp}` o simile.

### O-M3 · Manifest.json con SHA256
File `manifest.json` con `{ "files": [{ "path": "...", "sha256": "...", "size": ... }] }`.

---

## Output JSON

```json
{
  "qa_agent": "@quality-output",
  "verdict": "PASS" | "REJECT",
  "score": { "critical": "6/6", "secondary": "5/5", "minor": "3/3" },
  "items": [
    {
      "id": "O-C1",
      "severity": "CRITICO",
      "description": "25+ deliverable presenti",
      "result": true,
      "actual_count": 27,
      "expected_minimum": 25
    },
    {
      "id": "O-C2",
      "severity": "CRITICO",
      "description": "PDF integrità",
      "result": false,
      "files_checked": 18,
      "files_failed": [
        { "file": "07-cliente/contratto-servizi.pdf", "error": "extract_text returned empty" }
      ],
      "reject_target": "@contratto-architect"
    }
  ],
  "summary": {
    "total_files": 27,
    "total_size_mb": 38.4,
    "lovarch_synced": true,
    "git_commit": "a3f8b2e"
  }
}
```
