# Squad Architettura Progetto

> Squad specialistico per esecuzione end-to-end di progetti architettonici italiani.
> Dal briefing del cliente al dossier consegnabile all'impresa in 14 minuti.

**Version:** 2.0.0 · **Locale:** it-IT · **Market:** Italy
**AIOS Quality Score:** 🏆 **10.00/10 · EXCELLENCE**

| Tier | Score | Status |
|------|-------|--------|
| Tier 1 · Structure | 10.00/10 | ✅ |
| Tier 2 · Coverage | 10.00/10 | ✅ |
| Tier 3 · Quality (per-agent average · 17 agents) | 10.00/10 | ✅ |
| Tier 4 · Contextual | 10.00/10 | ✅ |

Validation: `python3 scripts/validate-squad.py --verbose`

---

## Missione

Sostituire 3 settimane di lavoro di uno studio medio italiano (1 architetto + 1 BIM Manager) con 14 minuti di orchestrazione AI, mantenendo:

- Accuratezza millimetrica nelle misure (tolleranza ±1 mm)
- Conformità normativa italiana (UNI 11337, CAM 2025, NTC 2018, DPR 380)
- Coerenza dati cross-documento (pianta ↔ IFC ↔ computo ↔ CILA ↔ contratto)
- Zero reinvenzione — tutto basato su framework documentati

Le eccezioni che restano **umane obbligatorie**: firma digitale del professionista, calcolo strutturale certificato, rilievo metrico topografico, coordinamento sicurezza (CSP/CSE).

---

## Architettura · 17 agenti in 4 tier

> Composizione: **2** Tier 0 (orchestrator + input gate) + **11** Tier 1 (esecuzione tecnica) + **4** Tier 2 (mind-clone QA · Deming, Juran, English, Dodds). Di cui **7 mind clones di elite minds** (Schumacher, Baldwin, Mazria, Deming, Juran, English, Dodds) e **10 agenti funzionali**.
>
> Per la specifica completa di ogni agente (ruolo, DNA, framework, output, ruolo nel workflow) vedi [`data/agents-prd.md`](data/agents-prd.md).

### Tier 0 · Orchestrazione (2 agenti)
| Agent | Ruolo |
|-------|-------|
| `@progetto-chief` | Orchestratore. Distribuisce, riceve QA, decide retry/avanti, consolida. |
| `@auditor-input` | Gate di ingresso. Verifica completezza input prima dell'esecuzione. |

### Tier 1 · Esecuzione tecnica (11 agenti · max parallelizzazione)
| Agent | Specialità | Framework |
|-------|-----------|-----------|
| `@briefing-architect` | Brief strutturato | UNI 11337-1, LOIN EN 17412-1 |
| `@regolatorio-it` | Pratica + vincoli | DPR 380, D.Lgs 42, DPR 31/2017, PGT Milano |
| `@concept-designer` | Moodboard, palette, render | FLUX + Gemini |
| `@cad-engineer` | Pianta, sezione, prospetto | UNI ISO 5457, UNI ISO 128-1, ezdxf |
| `@bim-engineer` | Modello IFC4 LOD 300 | UNI 11337-4, IFC4, APS Viewer |
| `@computo-engineer` | Computo metrico | Prezzario Lombardia 2025, DEI |
| `@capitolato-writer` | Capitolato + cronoprogramma | UNI 11337-7, CAM Edilizia 2025 |
| `@pratiche-it` | CILA, SCIA, paesaggistica | DPR 380 art 6-bis/22, DPR 31/2017 |
| `@contratto-architect` | Contratto + onorari | CNAPPC 2023, L. 49/2023, DM 17/06/2016 |
| `@energy-prelim` | APE + LCA preliminari | UNI/TS 11300, DPR 412/93 |
| `@deliverable-builder` | Presentazione + portale | DS V8 Lovarch, React |

### Tier 2 · Conferenza qualità (4 agenti con checklist)
| Agent | Verifica | Checklist items |
|-------|---------|-----------------|
| `@quality-misure` | Medidas (±1mm) | 24 (5 CRITICI) |
| `@quality-normativa` | Conformità 11 framework | 18 (6 CRITICI) |
| `@quality-dati` | Coerenza cross-documento | 16 (6 CRITICI) |
| `@quality-output` | Completezza + leggibilità | 14 (6 CRITICI) |

Loop: QA `REJECT` → chief → agente origine rifa → ri-QA. Max 3 retry, poi escalation umano.

---

## Workflow principale · `dal-brief-al-cantiere`

```
PABLO (input) ──► @progetto-chief ──► @auditor-input
                                           │ PASS
                                           ▼
              ┌──── Tier 1 · 11 agenti in PARALLELO ────┐
              │                                          │
              └──────────── @progetto-chief ─────────────┘
                                ▼
                      Tier 2 · 4 QA in parallelo
                                ▼
                         ┌──────┴──────┐
                         ▼             ▼
                      REJECT          PASS
                         │             │
                         ▼             ▼
                    retry (max 3)   consolidate
                                       │
                                       ▼
                           upload Lovarch + Finder
```

Dettagli: `workflows/dal-brief-al-cantiere.yaml`

---

## Deliverable · 27 documenti per 5 destinatari

| Destinatario | Documenti |
|-------------|-----------|
| **Cliente** (6) | Contratto, preventivo, privacy, presentazione HTML, portale URL, timeline |
| **Comune** (6) | CILA precompilata, asseverazione bozza, elaborati grafici, relazione tecnica, paesaggistica, foto |
| **Impresa** (8) | Capitolato, computo metrico, cronoprogramma, esecutivi, lista materiali, lettera invito, IFC, DOSSIER.zip |
| **Studio interno** (7) | Scheda progetto, cash flow, task team, social, ore, git commit, APE |
| **Ingegneri** (vari) | Schema strutturale, elettrico, termoidraulico, APE stima, LCA, CSP brief |

---

## Integrazione con Lovarch

### Tabelle Supabase (additive, migration sicura)
- `pm_squad_executions` — 1 row per esecuzione
- `pm_squad_steps` — 1 row per step di agente
- `pm_squad_qa_checks` — dettaglio checklist QA

### Pagine admin-only
- `/admin/squad-execution/:id/live` — live tracking con Supabase Realtime
- `/admin/squad-execution/:id/dossier` — lista cliccabile dei deliverable con preview

### Edge functions Lovarch riutilizzate
Il squad invoca 10+ edge functions esistenti (moodboard-suggest, render-ai-generate, brochure-generate, etc.) per massimizzare riuso e minimizzare costi di sviluppo.

---

## APIs esterne

### Richieste per il demo (2)
- **Mapbox Geocoding** — 100K free/mese, per geocoding indirizzi
- **OpenAPI.com** — catasto + firma digitale IT (può essere mockato per demo)

### Richieste per produzione (7 aggiuntive)
Yousign API, DeepL Pro, Meteostat, EC3 Building Transparency, DEI PLUS, One Click LCA, CubiCasa.

Dettagli setup: `/docs/strategy/salone-arquitetos-2026-04-25/SETUP-APIS.md`

---

## Quick start

### Requisiti
- Claude Code locale
- Node.js 18+ (per scripts)
- Python 3.11+ (per ezdxf, IfcOpenShell, ReportLab)
- Accesso admin Lovarch (service_role key)

### Primo run
```bash
# 1. Preparare input
mkdir -p ~/projects/attico-brera/01-input
# copiare: briefing-cliente.md, stato-attuale.dwg, foto/, visura-catastale.pdf

# 2. Eseguire squad
cd ~/Lovarch
claude "Squad architettura-progetto: esegui workflow dal-brief-al-cantiere con input ~/projects/attico-brera/01-input/"

# 3. Monitorare live
open "https://lovarch.com/admin/squad-execution/{execution_id}/live"

# 4. Visualizzare dossier finale
open "https://lovarch.com/admin/squad-execution/{execution_id}/dossier"
```

---

## Standard qualità · non negoziabili

1. **Tutte le cotas sommano correttamente** — ±1mm tolleranza
2. **Tutti i riferimenti normativi esistono e si applicano** — verifica @quality-normativa
3. **Tutti i numeri coincidono tra documenti** — verifica @quality-dati
4. **Tutti i PDF aprono senza errore** — verifica @quality-output
5. **Tutti i file sono caricati nella piattaforma Lovarch** — verifica @quality-output
6. **Ogni documento ha banner "bozza · firma professionista abilitato"** quando applicabile

---

## Limiti dichiarati · per credibilità

Il squad **non** sostituisce:

- Firma digitale del tecnico abilitato (CILA, asseverazione)
- Calcolo strutturale certificato (NTC 2018, art 65 DPR 380)
- Rilievo metrico con tolleranza catastale (UNI 7357)
- Coordinatore Sicurezza Progettazione/Esecuzione (D.Lgs 81/2008)
- Progettista antincendio per VV.FF.
- Visita in loco e responsabilità personale dell'architetto

Ogni deliverable che tocca queste aree è marcato come **bozza** con banner esplicito.

---

## Squad evolution

- **v1.0** (25 aprile 2026) · Salone del Mobile — prima esecuzione demo
- **v1.1** (giugno 2026) · Integrazione Mapbox + OpenAPI.com in produzione
- **v1.2** (settembre 2026) · Motore regolatorio completo (Normattiva RAG, top-50 comuni)
- **v2.0** (Q1 2027) · Espansione a BR + US (nuovi moduli normativi)

---

## Contatti

Squad creato da: Pablo Ruan (Lovarch · ArchPrime)
Discovery + design: Squad Architect (squad-creator)
Contesto: Presentazione Salone del Mobile Milano 2026 — 25 aprile 2026
