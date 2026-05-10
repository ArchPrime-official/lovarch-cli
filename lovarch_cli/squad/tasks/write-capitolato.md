# Task: write-capitolato

> **Pattern:** AP-TP-001
> **Executor:** @capitolato-writer (functional · Tier 1)
> **Squad:** architettura-progetto

---

## task_name
Write capitolato speciale d'appalto + cronoprogramma 90gg

## status
ACTIVE · stable · v1.0

## responsible_executor
- **agent**: @capitolato-writer
- **executor_type**: AP-EP-003 (Hybrid · AI 80% + BIM Manager review 20%)

## input
```yaml
required:
  computo_xlsx: "From @computo-engineer"
  materiali_list: "Lista materiali con codici EPD"
  regolatorio_json: "tipo-pratica.json from @regolatorio-it"
  durata_giorni: 90  # default
optional:
  template_uni_11337: "data/architettura-progetto-rules.md §2.5"
```

## output
```yaml
files:
  - "05-impresa/capitolato-speciale.pdf"
  - "05-impresa/cronoprogramma-90gg.pdf"
  - "05-impresa/lista-CAM-rispettati.xlsx"
metrics:
  pages: number  # ≥30
  cam_compliance_percent: number  # target ≥80%
```

## action_items
1. Load template UNI 11337-7 (cached)
2. Build Sezione 1 · Disposizioni generali (3pp)
3. Build Sezione 2 · Descrizione opere (5pp · from computo)
4. Build Sezione 3 · Specifiche tecniche esecuzione (12pp)
5. Build Sezione 4 · Materiali e prodotti (15pp · with CAM tracking)
6. Build Sezione 5 · Modalità esecuzione (8pp)
7. Build Sezione 6 · Tolleranze e prove (4pp · UNI EN 13670)
8. Build Sezione 7 · Sicurezza cantiere (CSP/CSE check + 6pp)
9. Build Sezione 8 · Oneri Appaltatore (8pp)
10. Build Sezione 9 · Direzione Lavori (5pp)
11. Build Sezione 10 · Garanzie + collaudo (4pp)
12. Build Sezione 11 · Penali (3pp)
13. Build Sezione 12 · Disposizioni finali (5pp)
14. Generate cronoprogramma Gantt 90gg via plotly
15. Generate lista-CAM-rispettati.xlsx · tracking ≥80%
16. Add banner BOZZA su tutti PDF

## acceptance_criteria
- [ ] 12 sezioni populated (no skipping)
- [ ] CAM 2025 tracking ≥80%
- [ ] Cronoprogramma 90gg with 6 fasi
- [ ] PSC obrigatorio sezione 7 if multi-impresa OR durata >200g/uomo
- [ ] Tolerances cited UNI EN 13670 + UNI ISO 5457
- [ ] PDF ≥30 pagine
- [ ] Banner BOZZA visible
- [ ] xlsx CAM rispettati 124+ voci tracked

## dependencies
- **APIs/Tools:**
  - Gemini 2.5 Pro (structured generation)
  - WeasyPrint (HTML→PDF qualità tipografica)
  - plotly (Gantt cronoprogramma)
  - edge: brochure-generate (layout)
- **Templates:**
  - UNI 11337-7 cached (12 sezioni)
  - CAM Edilizia 2025 voci (DM 23/06/2022)

## quality_gate
- **Gate:** QG-AP-1.3 (Normativa Verification Gate)
- **Reviewer:** @quality-normativa
- **Threshold:** 6/6 CRITICI Pareto · CAM ≥80%

## handoff
- **From:** @progetto-chief
- **To:** @progetto-chief → @quality-normativa (verifies)
- **Required announcement:** "Retornando ao @progetto-chief. Capitolato {n}pp · CAM {percent}%."

## veto_conditions
- Capitolato <30 pagine → contenuto insufficiente · retry
- Sezione mancante (12 obbligatorie) → halt
- CAM compliance <60% → halt + flag
- Banner BOZZA missing → halt
- PSC sezione vuota su multi-impresa → halt

## estimated_time
**60-90 seconds**

## output_example
See `@capitolato-writer.md` output_examples · 78 pagine · 12 sezioni · CAM 87% · Gantt 90gg · banner BOZZA.
