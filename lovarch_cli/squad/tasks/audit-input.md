# Task: audit-input

> **Pattern:** AP-TP-001 (Atomic Task Anatomy · 8 mandatory fields)
> **Executor:** @auditor-input (functional · Tier 0)
> **Squad:** architettura-progetto

---

## task_name
Audit input completeness · 18-item checklist gate

## status
ACTIVE · stable · v1.0

## responsible_executor
- **agent**: @auditor-input
- **executor_type**: AP-EP-002 (Agent Executor)
- **fallback**: @progetto-chief escalation if agent timeout

## execution_type
**Synchronous · Pre-flight gate** · Blocks workflow if FAIL

## input
```yaml
required:
  brief_path: "Path to briefing-cliente.md"
  dwg_path: "Path to stato-attuale.dxf"
  photos_dir: "Directory with stato attuale photos"
  cliente_data:
    nome: string
    cognome: string
    codice_fiscale: string  # 16-char Italian CF
    email: string
    telefono: string
  studio_data:
    architetto: string
    n_ordine: string
    piva: string
    pec: string
  valore_opera: number  # EUR
optional:
  visura_path: "Catastal record PDF"
```

## output
```yaml
file: "input_validation.json"
schema:
  validation_id: uuid
  status: "PASS | FAIL"
  missing: array[string]  # item ids that failed
  warnings: array[string]
  extracted_data:
    client_name: string
    client_cf_primary: string
    address: string
    geocoded:
      lat: number
      lon: number
      comune: string
      postcode: string
    project_value: number
    studio: object
```

## action_items
1. **A1** Read briefing-cliente.md · verify char count ≥500
2. **A2** Verify briefing has ≥3 of 12 sezioni UNI 11337
3. **A3** Extract budget numerico (regex /€\s?[\d,.]+/)
4. **A4** Extract timeline indicators
5. **A5** Verify briefing has cliente expectations section
6. **B1** Run `ezdxf.readfile(dwg)` · entities count > 0
7. **B2** Iterate photos · verify ≥3 JPG/PNG · resolution ≥800x600
8. **B3** Check visura PDF if present
9. **C1** Verify cliente nome+cognome non-empty
10. **C2-C3** Verify CF format /^[A-Z0-9]{16}$/ · Italian checksum algorithm
11. **C4** Verify email regex
12. **C5** Mapbox API call · geocode address · features.length > 0
13. **D1** Verify architetto nome
14. **D2** Verify n. Ordine (digit string)
15. **D3** Verify P.IVA studio (11-digit + checksum)
16. **D4** Verify PEC format
17. **E1** Verify valore_opera numeric > 0
18. **Final** Build extracted_data + verdict

## acceptance_criteria
- [ ] All 18 items checked (no skipping)
- [ ] If 5/5 critici (A1, A2, B1, C2, C5) PASS → status=PASS
- [ ] If ANY critico FAIL → status=FAIL · workflow halts
- [ ] JSON output valid against schema
- [ ] If PASS · extracted_data populated for downstream
- [ ] If FAIL · missing[] lists exact item_ids
- [ ] Verdict announcement returned to @progetto-chief

## dependencies
- **APIs:**
  - Mapbox Geocoding API (item C5 critical)
  - Italian CF checksum library (item C2-C3)
- **Files:**
  - All input files (brief, dwg, photos, etc.)
- **Agents:**
  - @progetto-chief (invoker · returns to)

## templates
- `~/projects/{slug}/01-input/` (expected input directory structure)
- input_validation.json schema (above)

## quality_gate
- **Gate:** QG-AP-1.1 (Input Validation Gate)
- **Threshold:** 5/5 CRITICI must PASS
- **Reviewer:** @progetto-chief on receipt

## handoff
- **From:** @progetto-chief (outbound card)
- **To:** @progetto-chief (inbound card with validation_id + verdict)
- **Required announcement:** "Retornando ao @progetto-chief. Audit completato — verdict: {PASS|FAIL}."

## veto_conditions
- Briefing < 500 chars → FAIL (A1)
- DWG corrupted (ezdxf raises) → FAIL (B1)
- Photos < 3 → FAIL (B2)
- Address not geocodable → FAIL (C5)
- Invalid CF → FAIL (C2-C3)
- Invalid P.IVA → FAIL (D3)
- Valore opera ≤0 → FAIL (E1)

## estimated_time
**60-90 seconds** (Mapbox API call dominant)

## output_example
```json
{
  "validation_id": "v_a7f4b2",
  "status": "PASS",
  "missing": [],
  "warnings": [],
  "extracted_data": {
    "client_name": "Marco Rossini & Giulia Bianchi",
    "client_cf_primary": "RSSMRC83A15F205X",
    "address": "Via Fiori Chiari 17, 20121 Milano",
    "geocoded": {"lat": 45.471823, "lon": 9.184828, "comune": "Milano", "postcode": "20121"},
    "project_value": 180000,
    "studio": {"nome": "Pablo Ruan", "ordine_n": "XXXX", "piva": "01234567890"}
  }
}
```
