# lovarch-cli

> **AI-powered architectural project execution CLI** — squad di 17 agenti specializzati che esegue audit input, briefing, normativa IT, CAD, BIM/IFC, computo metrico, capitolato, pratiche edilizie (CILA/SCIA), contratto CNAPPC, energy/LCA preliminare, dossier consolidato — in 14 minuti vs 3 settimane di lavoro tradizionale.

> ⚠️ **Status: ALPHA (v0.x)** — non ancora pubblicato su PyPI. Distribuzione attuale: wheel privato fornito agli iscritti al [Corso IA Avanzato per Architetti](https://lovarch.com/corso) (€1.497).
>
> Source code attualmente nel monorepo [ByPabloRuanL/lovarch](https://github.com/ByPabloRuanL/lovarch/tree/main/cli) (privato). Lo split verso `Lovarch-official/lovarch-cli` (pubblico) è pianificato pre-v1.0 prima del primo release PyPI. Vedi [MIGRATION-PLAN.md](MIGRATION-PLAN.md).

🌐 **Lingue:** [🇮🇹 Italiano](README.md) (default) · [🇵🇹 Português](README.pt.md) · [🇬🇧 English](README.en.md) · [🇪🇸 Español](README.es.md)

---

## Cosa fa

`lovarch-cli` orchestra il **Squad Architettura-Progetto** di Lovarch — 17 agenti AI con framework documentati (mind clones di Schumacher, Baldwin, Mazria, Deming, Juran, English, Dodds) — per generare 27 deliverable architettonici conformi alla normativa italiana:

- **Audit input** (18 controlli) prima di iniziare
- **CAD quotato** DXF/PDF (UNI ISO 5457, ±1mm)
- **BIM IFC4 LOD 300**
- **Computo metrico** (Prezzario Lombardia 2025)
- **Capitolato Speciale d'Appalto** (UNI 11337-7 + CAM 2025)
- **Pratiche edilizie pre-compilate** (CILA/SCIA/Paesaggistica)
- **Contratto CNAPPC** + Equo Compenso L.49/2023
- **APE Preliminare + LCA Embodied Carbon**
- **Dossier finale** ZIP con 27 documenti

## Due modalità

### 🆓 Free Mode (registrazione richiesta)

```bash
pip install lovarch-cli
arch login --free
# → Cadastro: Nome completo, email, telefono, paese, lingua
```

- Esegui il squad **localmente** con i tuoi propri API keys (OpenAI, Mapbox, fal.ai)
- Storage in `~/.lovarch/projects/` (filesystem locale)
- Database in `~/.lovarch/local.db` (SQLite)
- Tutti i 17 agenti disponibili
- Tu paghi le tue API direttamente ai provider

### ⭐ Premium Mode (login Lovarch)

```bash
arch login --premium
# → Apre il browser per autenticazione Lovarch (PKCE flow)
```

- Login con il tuo account Lovarch esistente
- Crediti inclusi nel piano (Personal €49 / Studio €99 / Business €199)
- Backend Lovarch (Supabase + S3 + Edge Functions ottimizzate)
- Sincronizzazione web app `lovarch.com/admin/squad-execution/{id}/live`
- Team member ownership automatico

## Quick start

```bash
# Installa (consigliato pipx per ambiente isolato)
pipx install lovarch-cli

# Primo login
arch login

# Inizializza un progetto
arch init villa-toscana

# Audit dell'input (18 controlli prima di iniziare)
arch audit villa-toscana

# Esegui workflow completo (14 min)
arch run dal-brief-al-cantiere --project villa-toscana

# Consolida deliverable
arch consolidate villa-toscana
```

## Comandi disponibili

| Comando | Descrizione |
|---------|-------------|
| `arch login` | Login Free o Premium |
| `arch signup` | Cadastro Free interattivo |
| `arch config` | Configurazione (API keys, lingua, storage path) |
| `arch init <progetto>` | Crea nuovo progetto con struttura sample-input |
| `arch audit <progetto>` | Esegue audit input (gate di ingresso) |
| `arch run <workflow>` | Esegue workflow completo |
| `arch consolidate <progetto>` | Genera DOSSIER.zip finale |
| `arch status <id>` | Stato di una esecuzione |
| `arch upgrade` | CTA per passare da Free a Premium |
| `arch account delete` | Right-to-erasure GDPR |

Vedi `arch --help` per dettagli completi.

## Limiti dichiarati

`lovarch-cli` **NON** sostituisce:

- ❌ Firma digitale qualificata (QES) dell'architetto abilitato
- ❌ Calcolo strutturale NTC 2018 (richiede ingegnere strutturale)
- ❌ Rilievo metrico in loco (richiede sopralluogo)
- ❌ Coordinamento sicurezza CSP/CSE (D.Lgs 81/2008)
- ❌ Responsabilità professionale del tecnico

L'utente assume la responsabilità di verifica e revisione professionale prima di qualsiasi presentazione ad autorità.

## Licenza

MIT License — vedi [LICENSE](LICENSE).

## Link

- 🌐 [archprime.io](https://archprime.io)
- 📚 [Documentazione](https://docs.archprime.io/cli)
- 🐛 [Issues](https://github.com/lovarch/lovarch-cli/issues)
- 🎓 [Corso IA Avanzato per Architetti](https://lovarch.com/corso) (€1.497)

---

🤖 Powered by [Lovarch](https://lovarch.com) — AI Growth System for Architects & Designers
