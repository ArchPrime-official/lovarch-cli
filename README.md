# lovarch-cli

[![CI](https://github.com/ArchPrime-official/lovarch-cli/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ArchPrime-official/lovarch-cli/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Release](https://img.shields.io/github/v/release/ArchPrime-official/lovarch-cli?include_prereleases)](https://github.com/ArchPrime-official/lovarch-cli/releases)

> **AI-powered architectural project execution CLI** — squad di 17 agenti specializzati che esegue audit input, briefing, normativa IT, CAD, BIM/IFC, computo metrico, capitolato, pratiche edilizie (CILA/SCIA), contratto CNAPPC, energy/LCA preliminare, dossier consolidato — in 14 minuti vs 3 settimane di lavoro tradizionale.

> ⚠️ **Status: BETA (v0.1.x)** — distribuito via Homebrew tap + pipx-from-git. Usato in produzione dagli iscritti al [Corso IA Avanzato per Architetti](https://lovarch.com/corso) (€1.497). Pubblicazione su PyPI valutata per v0.2+.

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
lovarch signup
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

## Installazione

### 🍺 Homebrew (raccomandato — macOS / Linux)

Il modo più semplice. Funziona anche per chi non ha familiarità con Python:

```bash
brew tap archprime-official/lovarch
brew install lovarch-cli
lovarch --version
```

`brew upgrade lovarch-cli` aggiorna alla nuova release.

### 📦 pipx — install isolato da GitHub

Se preferisci un'install Python isolata senza Homebrew (utile su Linux server,
WSL, o se hai già pipx configurato):

```bash
# Ultima release (anche pre-release):
pipx install git+https://github.com/ArchPrime-official/lovarch-cli.git@v0.3.0

# Oppure dal branch main (rolling):
pipx install git+https://github.com/ArchPrime-official/lovarch-cli.git
```

`pipx upgrade lovarch-cli` aggiorna alla revisione successiva.

### 🛠️ Da sorgente (per sviluppatori / contributori)

```bash
git clone https://github.com/ArchPrime-official/lovarch-cli.git
cd lovarch-cli
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/      # → 198 passing
lovarch --version
```

Vedi [CONTRIBUTING.md](./CONTRIBUTING.md) per il workflow di sviluppo.

> Backward compatibility: il comando `arch` è alias di `lovarch` per chi ha già muscle memory dalla versione interna di sviluppo.
>
> PyPI: la pubblicazione su `pip install lovarch-cli` è rimandata a v0.2+ (i metodi qui sopra coprono tutti i casi d'uso senza dipendere dalla burocrazia PyPI token/2FA).

## Quick start

```bash
# Verifica installazione
lovarch --version    # → lovarch-cli 0.3.0

# Primo login (interattivo: Free o Premium)
lovarch login

# Inizializza un progetto (con --sample scarica villa-chianti da GitHub Releases)
lovarch init villa-toscana --sample

# Audit dei 18 input prima di girare il pipeline
lovarch audit villa-toscana

# Esegui workflow (Free=dry-run · Premium=produzione)
lovarch run dal-brief-al-cantiere villa-toscana

# Consolida deliverable in DOSSIER.zip
lovarch consolidate villa-toscana

# Stato di tutti i progetti
lovarch status
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
| `arch context show` | Contesto di personalizzazione usato dagli agenti AI (premium) |
| `arch do render\|colors\|copy` | Workflow della piattaforma dal terminale (premium) |
| `arch verifica misure <dxf>` | Verifica DXF: layer ISO, ambienti, cartiglio (gratis) |
| `arch verifica normativa\|contratto <doc>` | Verifica adversariale 2 modelli (premium) |
| `arch verifica dossier <cartella>` | QA completo standalone su una cartella (premium) |
| `arch jobs list\|status` | Job asincroni (video, export, upscale) |
| `arch mcp serve` | Server MCP per Claude Code / IDE |

Vedi `arch --help` per dettagli completi.

## Skills — usa il TUO agente (Claude Code, Codex...)

Se usi già un agente con un suo modello, il TESTO lo genera lui (zero crediti
Lovarch); la piattaforma addebita solo immagini, dati e verifiche di piattaforma.

```bash
lovarch skills install     # → ~/.claude/skills
# poi, nel tuo agente: "progetto di interni per un attico 90mq..." → parte lovarch-interior-designer
```

Skill disponibili: `interior-designer`, `capitolato`, `preventivi`,
`direzione-lavori`, `verifica-normativa`, `render`.

## Guida per persona

Architetto, interior designer, geometra, impresa/DL: quale superficie usare
(Skill / CLI / MCP) e cosa costa crediti → **[docs/guida-per-persona.md](docs/guida-per-persona.md)**.

Workflow composto per interni: `lovarch progetto interni "<brief>" --renders 2`
(concept → render → preventivo → mini-dossier).

## Server MCP (Claude Code / Claude / IDE)

Il CLI espone le sue capacità come server **MCP** — 15 tools (render, verifica,
crediti, contesto, testo multi-modello...). Registrazione in Claude Code:

```bash
claude mcp add lovarch -- lovarch mcp serve
```

Oppure il **server MCP remoto** (nessuna installazione — una URL + una chiave):

```bash
lovarch mcp key                                   # crea una chiave lvk_...
claude mcp add lovarch --transport http https://mcp.lovarch.com/mcp \\
  --header "Authorization: Bearer lvk_..."
```

Ogni tool-call addebita i crediti Lovarch dell'utente esattamente come il CLI
(i costi sono SEMPRE espressi in crediti).

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

- 🌐 [archprime.io](https://archprime.io) · [lovarch.com](https://lovarch.com)
- 📚 [Documentazione](https://docs.archprime.io/cli)
- 🐛 [Issues](https://github.com/ArchPrime-official/lovarch-cli/issues)
- 📋 [Releases](https://github.com/ArchPrime-official/lovarch-cli/releases) · [Changelog](./CHANGELOG.md)
- 🤝 [Contributing](./CONTRIBUTING.md)
- 🎓 [Corso IA Avanzato per Architetti](https://lovarch.com/corso) (€1.497)

---

🤖 Powered by [Lovarch](https://lovarch.com) — AI Growth System for Architects & Designers
