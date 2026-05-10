# Squad Architettura-Progetto · CHANGELOG

> Cronologia di tutte le esecuzioni del squad e modifiche alla configurazione.
> Mandatory: agents devono aggiungere entry dopo ogni esecuzione completa.
> Format: reverse chronological (newest first).

---

## Execution Log · 2026-04-25 · Mario Rossi demo (sample-input as-is, no rename)

- **execution_id:** `6189721b-da28-402d-a101-83643976f4f5`
- **project_id:** `b3d9b070-7a73-4db4-a353-fe2432188e3d` · Attico Brera (sample-input dataset · briefing intatto · cliente rimane Marco Rossini & Giulia Bianchi nei deliverable)
- **runner:** `pipeline_runner.py v4` · `--real`
- **invocato da:** `/architetturaProgetto Esegui il progetto al 100% per il cliente Mario Rossi. --real` (opzione 1 confermata da Pablo · etichetta "Mario Rossi" solo nel CHANGELOG/folder name, NON applicato sed sul codice)
- **wall-clock:** 17 min 18s (target 14 min · oltrepassato di 3 min per renders i2i gpt-image-2 = 14:32 da soli, il resto in 2:46)
- **deliverables totali:** 32 (4 moodboard imgs + 5 i2i renders + 26 documents)
- **Tier 2 QA verdicts (real verifiers · 17 step rows in pm_squad_steps):**
  - Q1 @quality-misure: **REJECT** (DXF programmatico · layer ISO/cartiglio incompleti)
  - Q2 @quality-normativa: **REJECT 0/8** (DPR 380, UNI 11337, CAM 2025, NTC 2018, D.Lgs 81, D.Lgs 42, L.49/2023, GDPR · PDF stub `gen_pdf` boilerplate non contengono refs letterali)
  - Q3 @quality-dati: **PASS** 32/32 HEAD 200 (upload Lovarch storage tutti integri)
  - Q4 @quality-output: **CONCERNS** 13/14 AC (✗ AC2 5 renders count check)
  - Tier 2 OVERALL: **REJECT** · Phase D ha proseguito (resilient pipeline · execution marked COMPLETED)
- **URLs:**
  - Live: https://lovarch.com/admin/squad-execution/6189721b-da28-402d-a101-83643976f4f5/live
  - Dossier: https://lovarch.com/admin/squad-execution/6189721b-da28-402d-a101-83643976f4f5/dossier
- **Insight (consistente con run precedente 52d9af10):** stessi verdicts Q1/Q2 REJECT confermano limite architetturale del runner v4 — i PDFs Tier 1 (CILA, capitolato, computo, contratto, asseverazione) sono generati da `gen_pdf` con testo template-driven, non LLM-content-rich. Verifiers reali (Q1 ezdxf parse · Q2 grep regulatory refs) li bocciano correttamente. Per produrre dossier veri serve sostituire `gen_pdf` boilerplate con chiamate edge function dedicate (capitolato-writer, pratiche-it, ecc.) — già definite come agenti, non ancora connesse al runner.

---

## Execution Log · 2026-04-25 · Mario Rossi (demo client rebrand · earlier run)

- **execution_id:** `52d9af10-8a10-4595-bf64-24f2db2f1f6e`
- **project_id:** `e2b213b1` · Attico Brera (sample-input dataset · client renamed Mario Rossi)
- **runner:** `pipeline_runner.py v4` · `--real`
- **wall-clock:** ~16 min (target 14 min · oltrepassato per latenza OpenAI gpt-image-2 sui 9 imgs)
- **patches applicate:** sed `Marco Rossini → Mario Rossi` su `pipeline_runner.py` + `deliverable_generators.py` · revert post-execution via `.bak` · git status pulito
- **deliverables totali:** 32 (4 moodboard imgs + 5 i2i renders + 3 DXF + 12 PDF + 4 XLSX + 2 JSON + 1 HTML + 6 foto + 6 pinterest)
- **Tier 2 QA verdicts (real verifiers):**
  - Q1 @quality-misure: **REJECT** (ezdxf parse pianta-progetto.dxf · layer ISO/cartiglio incompleti)
  - Q2 @quality-normativa: **REJECT 0/8** (DPR 380, UNI 11337, CAM 2025, NTC 2018, D.Lgs 81, D.Lgs 42, L.49/2023, GDPR · stub PDFs ~2-3 KB non contengono refs)
  - Q3 @quality-dati: **PASS** (HTTP HEAD storage URLs OK · pm_documents FK validi)
  - Q4 @quality-output: **CONCERNS** (AC2 5 renders presenti · altre AC parziali)
  - Tier 2 OVERALL: **REJECT** · pipeline resilient ha proseguito (Phase D ALWAYS runs)
- **Phase D · Consolidation:** ✅ execution marked COMPLETED · browser auto-aperto su dossier + new-home
- **URLs:**
  - Live: https://lovarch.com/admin/squad-execution/52d9af10-8a10-4595-bf64-24f2db2f1f6e/live
  - Dossier: https://lovarch.com/admin/squad-execution/52d9af10-8a10-4595-bf64-24f2db2f1f6e/dossier
- **Insight:** verifiers reali stanno facendo il loro lavoro · espongono onestamente che i PDFs Tier 1 sono placeholder e non contengono articoli normativi reali. Patch nominale del cliente non altera il contenuto tecnico (CF/indirizzo/coniuge restano del demo Attico Brera).

---

## [2.1.0] — 2026-04-25 · Real Tier 2 QA + AP-VIOLATION-002 fix

### Critical fix
`pipeline_runner.py:1411-1441` `qa_agents` for-loop emitted hardcoded
"PASS · 9/9 ambienti..." strings without verification. All 4 QA agents
executed at identical timestamp (t=1070s) on execution 66db7c46, exposing
the fake. This violates rules.md §1.2 ("Tier 2 QA mandatory · NEVER
skips") and constitutional principle AP-VIOLATION-002.

Replaced with 4 real verifiers:
- **Q1 @quality-misure**: parses pianta-progetto.dxf via ezdxf, checks
  9 ISO layers (rules.md §3.3), 7 expected room labels, 5 cartiglio
  CNAPPC fields. Verdict from facts.
- **Q2 @quality-normativa**: fetches capitolato/CILA/asseverazione/contratto/privacy
  PDFs, regex 8 canonical refs (DPR 380, UNI 11337, CAM 2025, NTC 2018,
  D.Lgs 81/2008, D.Lgs 42/2004, L. 49/2023, GDPR Reg. UE 2016/679).
- **Q3 @quality-dati**: HTTP HEAD on all storage URLs, counts 200/non-200.
- **Q4 @quality-output**: 14 acceptance criteria + size>0 verification.

Each agent inserts pm_squad_steps (tier=2) with real action_desc
including verdict + diff. Overall verdict is REJECT if any REJECT,
CONCERNS if any CONCERNS, else PASS.

### Findings exposed by post-hoc real QA on execution 66db7c46
The squad shipped as "10/10 AIOS Excellence" had 5 structural bugs
hidden by the fake QA. Real verdict on 66db7c46:

| Agent | Verdict | Reason |
|-------|---------|--------|
| Q1 misure | REJECT | 0/9 ISO layers · 3/7 room labels missing · 0/5 cartiglio fields |
| Q2 normativa | REJECT | 0/9 canonical refs · capitolato/CILA/asseverazione 3-4 KB stubs |
| Q3 dati | CONCERNS | 32/32 HEAD OK · but T2 inserts vanished · pm_documents=0 · completed_at=null |
| Q4 output | PASS-superficial | 14/14 AC by filename match (doesn't verify content) |

### Follow-up issues (not in this PR)
1. `gen_dxf_pianta_progetto()` emits non-ISO layer names + missing room
   labels + no cartiglio CNAPPC content
2. `gen_pdf()` produces 3-4 KB stubs without canonical regulatory citations
3. 4 T2 inserts vanished from DB despite no thrown exception (root cause
   unknown · investigation needed)
4. `pm_documents` not populated (32 storage uploads but zero DB rows ·
   frontend cannot list deliverables in project tab)
5. `update_execution(status='completed')` does not set `completed_at`

---

## Execution log

### 2026-04-25 · Attico Brera · execution 66db7c46 · OVERALL REJECT (corrected post-hoc)
- **Project ID:** 16048505-e340-4aec-b526-05f243c245f5
- **Cliente:** Marco Rossini & Giulia Bianchi (sample)
- **Duration:** 17m 52s
- **Deliverables uploaded:** 32 storage assets (1 moodboard + 5 renders i2i + 26 docs)
- **Pipeline self-reported:** 4/4 QA PASS (FALSE POSITIVE · pre-fix)
- **Real QA verdict (manual, by Progetto Chief):** Q1 REJECT · Q2 REJECT · Q3 CONCERNS · Q4 PASS-superficial → OVERALL REJECT
- **Detailed report:** `/tmp/qa-real/REPORT.md` + `/tmp/qa-real/verdict.json`
- **Live:** https://lovarch.com/admin/squad-execution/66db7c46-c052-4ebc-854a-78eb8b883640/live
- **Dossier:** https://lovarch.com/admin/squad-execution/66db7c46-c052-4ebc-854a-78eb8b883640/dossier

#### Run abortado anterior (step_type bug)
project_id `de953667` + execution_id `42f5a19d` orphan rows in DB
(lead+phases+budget+finance+portal+1 moodboard upload). Failed at step 02
because pipeline_runner sent `step_type="execute"` but constraint
`pm_squad_steps_step_type_check` requires `IN ('orchestration','execution','qa')`.
Fix (now in main via PR #667): derive from tier (0→orchestration,
1→execution, 2→qa).

---

## [2.0.0] — 2026-04-25 · 10/10 AIOS Standard Compliance

### Added
- Squad upgraded to AIOS 6-level structure (all 14 agents)
- 7 mind clones with [SOURCE:] traceable signature phrases
- Pattern library AP-* (6 patterns documented)
- Executor types formal (human/agent/hybrid/worker)
- Handoff protocol with 9-state status machine
- Central document `data/architettura-progetto-rules.md` (mandatory consultation)
- Handoff card template `data/handoff-card-template.md`
- Handoff quality gate `checklists/handoff-quality-gate.md` (5 sections, 25+ checks)
- 6 atomic tasks in `tasks/` (audit-input, generate-cad-plan, generate-ifc-model, compute-metric, write-capitolato, consolidate-dossier)
- Validation script `scripts/validate-squad.py` (executable)
- 3 smoke test scripts in `scripts/smoke-tests/`

### Changed
- `config.yaml` upgraded from v1.0 → v2.0 with `pack:` wrapper
- All 14 agents reformatted: ACTIVATION-NOTICE + YAML embedded + 6-level structure
- `slashPrefix` corrected to `architetturaProgetto` (camelCase)
- README.md updated with badge "10/10 AIOS Compliant"

### Mind clones added
- @quality-misure → W. Edwards Deming (Total Quality Management)
- @quality-normativa → Joseph Juran (Quality Trilogy)
- @quality-dati → Larry English (Information Quality)
- @quality-output → Kent C. Dodds (Testing Trophy)
- @concept-designer → Patrik Schumacher (ZHA, AI ideation)
- @bim-engineer → Mark Baldwin (BIM Manager's Handbook)
- @energy-prelim → Edward Mazria (Architecture 2030)

### Quality score
- Tier 1 Structure: 10/10
- Tier 2 Coverage: 10/10
- Tier 3 Quality: 9.5/10
- Tier 4 Contextual: 10/10
- **Final: 9.7/10** (PASS · Excellence)

---

## [1.0.0] — 2026-04-24 · Initial Release (palestra Salone)

### Added
- 14 agents in 4 tiers (Tier 0/1/2)
- 4 QA checklists (misure, normativa, dati, output)
- Workflow `dal-brief-al-cantiere.yaml` (5 phases)
- 4 templates IT (CILA, contratto, capitolato, asseverazione)
- Sample input "Attico Brera" (briefing 251 lines + DWG generator)
- Prezzario Lombardia sample (35 voci)
- API clients (Mapbox real + Catasto/Firma mocks)
- Simulator script (20 steps with QA reject + retry)
- Run script `run_palestra_demo.sh` (5-step orchestrator)
- Migration SQL 3 tables (pm_squad_executions, pm_squad_steps, pm_squad_qa_checks)
- 2 React admin pages (live tracking + dossier)

### Quality score
- Tier 1 Structure: 3/10 (FAIL)
- Tier 2 Coverage: 7/10
- Tier 3 Quality: 0.7/10 (FAIL CRITICO)
- Tier 4 Contextual: 6/10
- **Final: 1.76/10** (FAIL · functional demo only)

### Known limitations (resolved in 2.0.0)
- Agents not in AIOS 6-level structure
- No voice_dna or thinking_dna formal
- No mind clones
- Missing central document, CHANGELOG, handoff-quality-gate
- Missing entry_agent in config

---

## Execution log template

```markdown
## [Execution N] — YYYY-MM-DD · {project name}

**Cliente:** {nome cliente}
**Indirizzo:** {indirizzo immobile}
**Valore opera:** € {valore}
**Durata totale:** {min}m {sec}s
**Steps:** {n}
**QA rejects:** {n}
**Retries:** {n}
**Status:** completed | failed | aborted

**Deliverables:** {n} files in {path}
**Lovarch project_id:** {uuid}
**Live URL:** /admin/squad-execution/{id}/live
**Dossier URL:** /admin/squad-execution/{id}/dossier

**Notes:**
- {any deviation from standard flow}
- {QA reject specifics if any}
```
