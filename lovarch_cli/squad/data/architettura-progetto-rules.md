# Architettura Progetto · Central Rules Document

> **Mandatory consultation:** ALL agents MUST read this document before any action.
> Source of truth for normative references, conventions, and inviolable principles.
> Version: 2.0.0 · Last updated: 2026-04-25

---

## 1. INVIOLABLE PRINCIPLES

### 1.1 Hub-and-Spoke handoff
- Specialists **NEVER** route directly to other specialists.
- Every handoff returns to `@progetto-chief`, who validates and routes next step.
- Required announcement: `Ritorno al @progetto-chief. {lavoro} concluso.`
- Specialist-to-specialist routing = **VETO** (constitutional violation).

### 1.2 Tier 2 QA mandatory
- Tier 1 output **NEVER** skips Tier 2 QA.
- Min 2 of 4 QA agents (misure, normativa, dati, output) must validate before consolidation.
- QA REJECT after 3 retries → escalate to human (Pablo).

### 1.3 Italian-first
- All deliverables in Italian (IT) primary.
- Multilingue secondary: EN, ES, PT for client presentation only.
- Terminology source: UNI 11337, CNAPPC, ISO 5457.

### 1.4 Zero tolerance on critical metrics
- Measures: ±1mm tolerance (quality-misure verifies).
- Data coherence: 100% cross-document match (quality-dati verifies).
- Normative references: 100% verifiable on Normattiva (quality-normativa verifies).

### 1.5 Self-contained
- All squad files inside `squads/architettura-progetto/`.
- No external file references except: Lovarch edge functions + global APIs (Mapbox, FLUX, Gemini).
- No mind clone DNA in `outputs/minds/` (DNA inline in agent files via Voice DNA + Thinking DNA).

---

## 2. ITALIAN REGULATORY STACK (mandatory references)

### 2.1 DPR 380/2001 · Testo Unico Edilizia

| Articolo | Tema | Quando applicare |
|----------|------|------------------|
| **art. 6** | Edilizia libera | Manutenzione ordinaria, opere temporanee |
| **art. 6-bis** | CILA | Manutenzione straordinaria interna senza struttura |
| **art. 22** | SCIA | Modifiche prospetti / opere strutturali leggere |
| **art. 23** | SCIA alternativa al PdC | Ristrutturazione "pesante" |
| **art. 10** | Permesso di Costruire | Nuova costruzione, sopraelevazione |
| **art. 3** | Definizioni interventi | Riferimento per classificazione |

**Decisione tipo pratica per Attico Brera 120 m²:**
- Ristrutturazione interna senza prospetti né strutturali → **CILA**
- Modifiche prospetti (zona vincolata) → **SCIA + paesaggistica**
- Demolizione muri portanti → **SCIA alternativa o PdC + relazione strutturale**

### 2.2 D.Lgs 42/2004 · Codice Beni Culturali

- **art. 10** · Vincolo monumentale diretto → autorizzazione art. 21 Soprintendenza
- **art. 142** · Vincolo paesaggistico → autorizzazione art. 146
- **DPR 31/2017** · Procedura semplificata (allegato A esonero, B 60gg)

### 2.3 NTC 2018 (DM 17/01/2018) + Circolare 7/2019

| Cap. | Tipo intervento | Quando |
|------|----------------|--------|
| **8.4.1** | Riparazione/locale | No struttura · solo verifica locale |
| **8.4.2** | Miglioramento | Aumento sicurezza · valutazione sismica |
| **8.4.3** | Adeguamento | Cambio destinazione, sopraelevazione, ampliamento >10% |

Per Attico Brera ristrutturazione interna senza struttura → **8.4.1** (verifica locale, no calcolo).

### 2.4 D.Lgs 81/2008 · Sicurezza nei Cantieri

CSP/CSE obbligatori se:
- ≥2 imprese (anche non contemporanee) — art. 90 c.3
- Durata >200 uomini-giorno
- Cantiere >30gg con ≥20 lavoratori-giorno

Per Attico Brera (edile + impianti + serramenti) → **CSP/CSE quasi sempre obbligatori**.

### 2.5 UNI 11337 · BIM Italia

| Parte | Oggetto |
|-------|---------|
| 1:2017 | Modelli, elaborati, oggetti |
| 4:2017 | LOD scala A-G (sostituita progressivamente da LOIN) |
| 5:2017 | Flussi informativi, CDE |
| **7:2018** | Qualificazione figure BIM |
| 9:2024 | Fascicolo digitale del costruito |

**LOIN UNI EN 17412-1:2020** → riferimento per appalti pubblici BIM dal 2025.

### 2.6 CAM Edilizia 2025 (DM 23/06/2022)

- Calcestruzzo: ≥15% riciclato
- Laterizio: ≥30% riciclato
- Demolizione selettiva: ≥70% recupero
- Legno: FSC/PEFC certificato
- Isolanti: con DAP/EPD

**Obbligatorio:** opere pubbliche.
**Privato:** non obbligatorio, ma replicabile per Ecobonus/detrazioni.

### 2.7 Bonus edilizi 2026

| Bonus | Aliquota 2026 |
|-------|---------------|
| Bonus Ristrutturazione | 36% prima casa, 30% seconda |
| Ecobonus | 50% prima, 36% seconda |
| Sismabonus | 50% / 36% |
| Bonus Mobili | 50% fino €5.000 |
| Superbonus | **CESSATO** per privati |

**Cessione credito/sconto fattura:** bloccati (DL 11/2023), salvo eccezioni vincolati.

### 2.8 PGT Milano 2030 · Zona A1 (NAF Brera)

- Conservazione tipologica obbligatoria
- Facciate: divieto modifiche, restauro materiali originali
- Interni: ammessa ristrutturazione se non altera schema distributivo storico
- Doppio binario: Comune (PGT) + Soprintendenza (vincolo MiC)

### 2.9 L. 49/2023 · Equo Compenso

- **Ambito della L.49/2023:** tutela il professionista verso il **contraente forte** (PA, banche, assicurazioni, grandi imprese ≥50 dipendenti o fatturato ≥€10M). **NON si applica al cliente privato consumatore** (es. ristrutturazione di abitazione).
- DM 17/06/2016 = **metodo di calcolo** del compenso equo (CP = V × G × Q × P), riferimento ORIENTATIVO per il cliente privato. **Non esiste un limite legale del 20% di sconto.**
- Categoria E.20 residenziale, grado complessità G = 0.95
- Per ristrutturazione 120 m² @ €1.500/m² = €180.000 valore opera → onorario indicativo €18-22K
- Uno scostamento marcato dai parametri per cliente privato è una scelta commerciale legittima: segnalarlo come rischio di sostenibilità/qualità (non come illecito) e ridefinire il perimetro coerente.

### 2.10 L. 105/2024 · Salva-Casa

- Tolleranze ≤5%
- Sanatorie difformità formali
- Stato legittimo (DL 69/2024)

### 2.11 Reg. UE 2016/679 · GDPR

- Informativa privacy obbligatoria nel contratto
- Titolare: architetto · Finalità: esecuzione incarico
- Conservazione: 10 anni (compliance antiriciclaggio)

**Subprocessori del pipeline (Art. 28 GDPR — responsabili del trattamento):** il briefing del cliente (incl. CF, indirizzo ed eventuali dati particolari, es. esigenze di salute) viene elaborato da fornitori AI/servizi terzi — tipicamente OpenAI, Google (Gemini), DeepL e Mapbox. L'architetto (titolare) deve: (a) indicare questi subprocessori nell'informativa privacy resa al cliente; (b) avere una base giuridica adeguata; (c) minimizzare i dati inviati (evitare dati particolari non necessari). Il dossier generato NON deve esporre dati personali oltre il necessario.

---

## 3. STANDARD UNI ISO PER ELABORATI GRAFICI

### 3.1 UNI ISO 5457 · Formato fogli

| Formato | Dim. (mm) | Uso tipico |
|---------|-----------|------------|
| A0 | 841 × 1189 | Tavole sintesi PRG |
| A1 | 594 × 841 | **Tavole esecutive** (default) |
| A2 | 420 × 594 | Dettagli costruttivi |
| A3 | 297 × 420 | Allegati pratiche |

### 3.2 UNI ISO 128-1 · Linee e simboli grafici

- Spessore linee: 0.13 / 0.18 / 0.25 / 0.35 / 0.50 / 0.70 mm
- Stili: continuo, tratteggiato (linee nascoste), tratto-punto (assi)

### 3.3 Layer ISO standard (DXF)

| Layer | Contenuto |
|-------|-----------|
| `CAD-A-WALL` | Muri interni |
| `CAD-A-WALL-EXT` | Muri perimetrali |
| `CAD-A-DOOR` | Porte |
| `CAD-A-WIND` | Finestre |
| `CAD-A-DIM` | Quote |
| `CAD-A-TEXT` | Testo |
| `CAD-A-SYMB` | Simboli |
| `CAD-A-FURN` | Mobili |
| `CAD-A-CART` | Cartiglio |

### 3.4 Cartiglio CNAPPC

Campi obbligatori:
- Progetto · Cliente · Architetto · n. Ordine
- Tavola · Scala · Data · Fase · Rev.
- Formato (A1, A0)
- File path/nome

### 3.5 Tolleranze geometriche

- Verticalità pareti: ±3 mm su 2 m
- Planarità pavimenti: ±2 mm sotto regolo da 2 m
- Squadratura ambienti: ±5 mm su 4 m
- Quote individuali: **±1 mm** (verifica @quality-misure)

---

## 4. FRAMEWORK DI ANALISI E DIAGNOSI

### 4.1 Phases standard del progetto IT (DM 49/2018)

| Fase | Output principali |
|------|-------------------|
| **PFTE** | Relazione, planimetrie 1:500/1:200, prefattibilità, QE |
| **Definitivo** | Tavole 1:100, relazioni specialistiche, computo estimativo, capitolato prestazionale |
| **Esecutivo** | Tavole 1:50/1:20, particolari costruttivi, computo definitivo, capitolato speciale, PSC |
| **DL** | SAL, contabilità, certificato regolare esecuzione, varianti |

**Privato:** spesso PFTE+Definitivo fusi; Esecutivo+DL sempre separati.

### 4.2 Mapping RIBA POW → IT

- RIBA 0-1 (Strategic) → Studio di fattibilità
- RIBA 2-3 (Concept/Developed) → PFTE + Definitivo
- RIBA 4 (Technical) → Esecutivo
- RIBA 5-6 (Construction/Handover) → DL + Collaudo
- RIBA 7 (In Use) → Fascicolo del costruito (UNI 11337-9)

---

## 5. CONVENTIONS SQUAD ARCHITETTURA-PROGETTO

### 5.1 File naming
- DXF: `{ambito}-{stato}.dxf` (es. `pianta-progetto.dxf`)
- PDF: `{NN}-{categoria}-{nome}.pdf` (es. `01-briefing-strutturato.pdf`)
- IFC: `modello.ifc` (singular per progetto)
- Excel: `{ambito}.xlsx` (es. `computo-metrico.xlsx`)
- ZIP: `DOSSIER-IMPRESA.zip` (uppercase final pacchetto)

### 5.2 Cartelle output
```
~/projects/{slug}/
├── 01-briefing/
├── 02-concept/
├── 03-progetto-definitivo/
├── 04-pratiche-comune/
├── 05-impresa/
├── 06-ingegneri/
├── 07-cliente/
└── 08-studio-interno/
```

### 5.3 Versioning
- Documenti: `v1.0`, `v1.1`, `v2.0` (semver)
- Git tag dopo ogni esecuzione completa: `squad-v1.0-{timestamp}`
- Manifest.json con SHA256 di ogni deliverable

### 5.4 Lingua documenti
- Tecnici (CILA, capitolato, computo): **solo italiano**
- Cliente (presentazione, portale): primaria IT, alternative EN/ES/PT
- Code/JSON/file naming: inglese

### 5.5 Banner obbligatori

Documenti che richiedono firma umana devono avere banner esplicito:

> **BOZZA · Firma del professionista abilitato obbligatoria**
> Documento generato automaticamente da Squad architettura-progetto.
> Verificare e firmare digitalmente con certificato qualificato (eIDAS QES)
> prima della protocollazione.

I documenti con implicazione legale o economica (contratto, preventivo onorari, pratiche edilizie, asseverazione) devono inoltre riportare il disclaimer:

> **⚠️ Documento generato con AI — verifica professionale obbligatoria**
> I riferimenti normativi, gli importi e i calcoli possono contenere errori.
> Verificare con il proprio Ordine professionale e/o commercialista prima dell'uso.
> Il professionista firmatario è l'unico responsabile dei contenuti.

---

## 6. WHAT THE SQUAD DOES NOT DO

Limiti dichiarati per credibilità:

- ❌ Firma digitale del tecnico abilitato (CILA, asseverazione) — solo umano
- ❌ Calcolo strutturale certificato (NTC 2018) — solo ingegnere strutturale iscritto
- ❌ Rilievo metrico topografico certificato — solo geometra/topografo
- ❌ Coordinatore Sicurezza (CSP/CSE) — solo tecnico abilitato D.Lgs 81
- ❌ Progettista antincendio per VV.FF. — solo certificato
- ❌ Visita in loco e responsabilità personale dell'architetto
- ❌ APE ufficiale (la stima preliminare richiede certificatore abilitato)

Ogni deliverable che tocca queste aree è **bozza** con banner.

---

## 7. AGENT RESPONSIBILITY MATRIX

| Agent | Tier | Responsibility | Critical | Mind clone source |
|-------|------|---------------|----------|-------------------|
| @progetto-chief | 0 | Orchestration | hub-and-spoke enforcement | (functional) |
| @auditor-input | 0 | Input gate | 18 mandatory checks | (functional) |
| @briefing-architect | 1 | Brief structuring | UNI 11337 compliance | (functional) |
| @regolatorio-it | 1 | Regulatory determination | DPR 380 + paesaggistica | (functional) |
| @concept-designer | 1 | Visual concept | DS V8 alignment | Patrik Schumacher (ZHA) |
| @cad-engineer | 1 | 2D plans | ±1mm tolerance | (functional) |
| @bim-engineer | 1 | IFC4 LOD 300 | ISO 12006-3 psets | Mark Baldwin |
| @computo-engineer | 1 | Quantity take-off | Prezzario + IVA 10% | (functional) |
| @capitolato-writer | 1 | Capitolato | UNI 11337-7 + CAM 2025 | (functional) |
| @pratiche-it | 1 | CILA/SCIA | Templates Comune Milano | (functional) |
| @contratto-architect | 1 | Contratto CNAPPC | L.49/2023 equo compenso | (functional) |
| @energy-prelim | 1 | APE preliminare | UNI/TS 11300 | Edward Mazria |
| @deliverable-builder | 1 | Final deliverables | DS V8 padrão | (functional) |
| @quality-misure | 2 | Misure verification | ±1mm zero tolerance | W. Edwards Deming |
| @quality-normativa | 2 | Normative compliance | 11 frameworks | Joseph Juran |
| @quality-dati | 2 | Cross-doc coherence | 100% match | Larry English |
| @quality-output | 2 | Deliverable QA | All open + uploaded | Kent C. Dodds |

---

## 8. EMERGENCY PROCEDURES

### 8.1 QA REJECT loop (max 3 retries)
1. QA agent emite REJECT con diff specifico
2. @progetto-chief identifica agente origine
3. Re-invocazione mirata con diff
4. QA re-verifica solo items falliti
5. Se 3 retries falliscono → escalate al humano (Pablo)

### 8.2 API failure
- Edge function 5xx persistente → halt + log + ask Pablo
- Mapbox 429 (rate limit) → backoff exponential (1s, 2s, 4s)
- FLUX timeout >90s → retry su altro modello image (FLUX 2 Pro)

### 8.3 Storage quota
- Lovarch storage piena → halt immediato + log + notify Pablo
- Local disk pieno → halt + log

---

**Reference:** This document is the source of truth. In case of conflict with agent files, this document prevails. Update this document FIRST, then propagate to agents.
