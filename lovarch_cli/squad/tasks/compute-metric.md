# Task: compute-metric

> **Pattern:** AP-TP-001
> **Executor:** @computo-engineer (functional · Tier 1 · critical: dati_zero_tolerance)
> **Squad:** architettura-progetto

---

## task_name
Compute metric estimative · Prezzario Lombardia 2025 · IVA 10%

## status
ACTIVE · stable · v1.0

## responsible_executor
- **agent**: @computo-engineer
- **executor_type**: AP-EP-002 (Agent + Python worker)
- **worker**: xlsxwriter, openpyxl, pdfplumber

## execution_type
**Synchronous after BIM** · Output feeds @capitolato-writer + @quality-dati

## input
```yaml
required:
  quantitativi_json: "From @bim-engineer"
  prezzario_path: "data/prezzario-lombardia-sample.json"
optional:
  dei_plus_subscription: bool  # fallback per voci mancanti
  ec3_for_epd: bool  # for EPD tracking
```

## output
```yaml
files:
  - "05-impresa/computo-metrico.xlsx"
  - "05-impresa/computo-metrico.pdf"
  - "05-impresa/quadro-economico.pdf"
  - "05-impresa/lista-materiali-EPDs.xlsx"
metrics:
  voci_count: number
  totale_lavori_eur: number
  iva_eur: number
  totale_iva_inclusa: number
  cam_compliance_percent: number
```

## action_items
1. Read quantitativi.json (volumi muri, aree pavimenti, count, etc.)
2. Match each quantity to Prezzario Lombardia voce (semantic + code)
3. For unmatched: query DEI fallback OR mark [VERIFY-CUSTOM]
4. Compute Q × prezzo_unitario per voce
5. Aggregate per categoria DEI (demolizioni, murature, impianti, etc.)
6. Apply IVA 10% (ristrutturazione · DPR 633/72)
7. Build quadro economico (lavori + onorari + oneri + IVA + imprevisti)
8. Track CAM 2025 compliance per voce (target ≥80%)
9. Cross-reference EC3 for EPDs in materials list
10. Generate xlsx with formulas (SUM, IVA calc)
11. Generate PDF version
12. Self-verify: sum quantitativi IFC = sum computo (diff <2%)

## acceptance_criteria
- [ ] ≥100 voci with codice Prezzario or [VERIFY-CUSTOM]
- [ ] Aggregazione per categoria DEI completa
- [ ] IVA 10% applied (NOT 22%)
- [ ] Quadro economico generato
- [ ] Cross-check IFC quantitativi · diff <2%
- [ ] CAM 2025 tracking ≥80% target
- [ ] xlsx with working formulas
- [ ] PDF readable

## dependencies
- **Libraries:**
  - xlsxwriter (xlsx generation)
  - openpyxl (template editing)
  - pdfplumber (parse Prezzario PDF if needed)
- **APIs:**
  - DEI PLUS (optional · fallback)
  - EC3 Building Transparency (EPDs)
  - Gemini 2.5 Pro (semantic mapping descrizione → voce)
- **Data:**
  - Prezzario Regione Lombardia 2025 cached JSON
  - quantitativi.json (@bim-engineer)

## quality_gate
- **Gate:** QG-AP-1.4 (Cross-Doc Data Gate)
- **Reviewer:** @quality-dati
- **Threshold:** Cross-check IFC = computo · diff <2%

## handoff
- **From:** @progetto-chief
- **To:** @progetto-chief → @capitolato-writer (uses computo) + @quality-dati (verifies)
- **Required announcement:** "Retornando ao @progetto-chief. Computo · {n} voci · totale € {X}."

## veto_conditions
- Totale computo ≠ sum voci > 0.5% → halt
- IVA 22% applied → halt (errata · ristrutturazione = 10%)
- Voci senza prezzo → halt
- Diff vs IFC quantitativi >2% → halt + flag @quality-dati REJECT predicted

## estimated_time
**45-60 seconds**

## output_example
See `@computo-engineer.md` output_examples · 124 voci · €162,327 · CAM 87% · cross-check pass.
