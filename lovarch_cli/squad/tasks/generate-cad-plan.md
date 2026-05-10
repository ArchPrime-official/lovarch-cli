# Task: generate-cad-plan

> **Pattern:** AP-TP-001 (Atomic Task Anatomy · 8 mandatory fields)
> **Executor:** @cad-engineer (functional · Tier 1 · critical: misure_zero_tolerance)
> **Squad:** architettura-progetto

---

## task_name
Generate planimetrie quotate DXF + PDF UNI ISO 5457

## status
ACTIVE · stable · v1.0

## responsible_executor
- **agent**: @cad-engineer
- **executor_type**: AP-EP-002 (Agent · Python local)
- **worker**: ezdxf, Shapely, ReportLab

## execution_type
**Asynchronous · Tier 1 parallel** · Output feeds @bim-engineer + @quality-misure

## input
```yaml
required:
  stato_attuale_dxf: "Path to existing state DXF"
  programma_spaziale_xlsx: "Path to room program from @briefing-architect"
  requisiti_json: "Path to requisiti from @briefing-architect"
  height_target_cm: 290  # default Milan A1
optional:
  altezza_override: number  # if non-standard
  scale: "1:50"  # default
```

## output
```yaml
files:
  - "03-progetto-definitivo/pianta-stato-attuale.dxf"
  - "03-progetto-definitivo/pianta-stato-attuale.pdf"
  - "03-progetto-definitivo/pianta-progetto.dxf"
  - "03-progetto-definitivo/pianta-progetto.pdf"
  - "03-progetto-definitivo/sezione-AA.pdf"
  - "03-progetto-definitivo/prospetti.pdf"
  - "03-progetto-definitivo/schema-quotato.json"
schema_quotato:
  ambienti: array[{ nome, sup_m2, altezza_cm, rai }]
  totale_utile_m2: number
  totale_lordo_m2: number
  muratura_m2: number
  quote_principali: array[{ id, valore_cm, elemento, verified }]
```

## action_items
1. Read stato-attuale.dxf · validate parseable
2. Compute layout from programma-spaziale.xlsx
3. Build perimeter walls (12cm) using ezdxf
4. Build internal partitions (8cm)
5. Add doors (block insertions, swing arcs)
6. Add windows (perimeter only · facade vincolata)
7. Generate dimension chains horizontal + vertical
8. Add room labels with name + area
9. Insert cartiglio CNAPPC bottom-right
10. Export DXF (R2018) + PDF (A1 scale 1:50)
11. Generate sezione-AA + prospetti
12. Compute schema-quotato.json
13. Self-verify sum chains match perimeter (±1mm)

## acceptance_criteria
- [ ] DXF parseable via `ezdxf.readfile()`
- [ ] 9 layer ISO present (CAD-A-WALL, CAD-A-DIM, etc.)
- [ ] Cartiglio CNAPPC 12/12 fields populated
- [ ] All quotes within ±1mm tolerance
- [ ] Sum verification: sup utile + muratura = sup lorda (±0.5%)
- [ ] schema-quotato.json valid (matches schema)
- [ ] PDF readable at 1:50 scale (text height ≥2.5mm)
- [ ] Min sup ambienti respect normativa (camera ≥9m², ecc.)
- [ ] RAI ≥1/8 sup pavimento per ambienti abitabili

## dependencies
- **Tools (Python local):**
  - ezdxf 1.4.3
  - Shapely 2.x
  - ReportLab
  - Trimesh (volume verification)
- **Files:**
  - stato-attuale.dxf (input)
  - programma-spaziale.xlsx (from @briefing-architect)
  - requisiti.json
- **Templates:**
  - data/architettura-progetto-rules.md §3 (UNI ISO standards)

## templates
- Cartiglio CNAPPC standard (ezdxf primitives)
- Layer ISO setup function
- Dimension style UNI

## quality_gate
- **Gate:** QG-AP-1.2 (Misure Verification Gate)
- **Reviewer:** @quality-misure (24-item checklist)
- **Threshold:** 5/5 CRITICI + ≥80% SECONDARI
- **Self-check:** Sum verification before handoff

## handoff
- **From:** @progetto-chief (outbound card)
- **To:** @progetto-chief (inbound card with files + schema-quotato.json)
- **Then via chief:** @bim-engineer (uses schema-quotato) + @quality-misure (verifies)
- **Required announcement:** "Retornando ao @progetto-chief. Plans generati · {n} entities · cotazioni verificate ±1mm."

## veto_conditions
- DWG sorgente impossibile da leggere → halt
- Sup lorda ≠ sup utile + muratura > 0.5% → halt
- Quota negativa o zero → halt
- Layer non-ISO → halt
- Cartiglio incompleto → halt

## estimated_time
**90-120 seconds** (DXF entities count + PDF rendering)

## output_example
See `@cad-engineer.md` output_examples · 187 entities · 9 layers · 24/24 quote check · 102.3 m² utile · 120.0 lorda · 17.7 muratura.
