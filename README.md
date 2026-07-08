# lovarch-cli

[![CI](https://github.com/ArchPrime-official/lovarch-cli/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ArchPrime-official/lovarch-cli/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Release](https://img.shields.io/github/v/release/ArchPrime-official/lovarch-cli?include_prereleases)](https://github.com/ArchPrime-official/lovarch-cli/releases)

> **AI per architetti, interior designer, geometri e imprese** — agenti LLM
> (senza contenuti pre-impostati), workflow componibili, render fotorealistici e
> verifiche normative adversariali, dal terminale. Il testo lo genera il TUO
> modello (Claude Code…) a costo zero; la piattaforma addebita crediti solo per
> immagini, dati e verifiche.

> **Status: BETA** — distribuito via Homebrew tap, PyPI e pipx. Parte del
> [Corso IA Avanzato per Architetti](https://lovarch.com/corso).

🌐 **Lingue:** [🇮🇹 Italiano](README.md) (default) · [🇵🇹 Português](README.pt.md) · [🇬🇧 English](README.en.md) · [🇪🇸 Español](README.es.md)

---

## Cosa fa

Tre superfici, un'unica regola dei costi (testo col TUO modello = gratis;
piattaforma = crediti):

- **Agenti LLM reali** (`lovarch agent`) — interior designer, direzione lavori,
  preventivi, geometra/catasto, sicurezza-advisor. Ragionano sul TUO brief,
  personalizzati col tuo brand (nessun contenuto hard-coded).
- **Workflow componibili** (`lovarch progetto interni|cantiere`) — concept →
  render → preventivo, oppure cronoprogramma → pre-check sicurezza.
- **Render Studio** (`lovarch do render/logo/site/colors/copy/script`) — immagini
  e branding via piattaforma (crediti).
- **Verifiche adversariali** (`lovarch verifica`) — misure DXF (gratis) · computo
  vs prezzario (gratis offline) · normativa · contratto CNAPPC · pratica CILA/SCIA
  · sicurezza D.Lgs 81 · accessibilità L.13/89 (2 modelli, crediti).
- **CAD 2D** (`lovarch cad genera`) — pianta DXF reale (9 layer ISO + cartiglio).
- **ArchChat** (`lovarch archchat`) — leggi le conversazioni del tuo studio (gratis).
- **Skills** (`lovarch skills install`) — il tuo Claude Code esegue le personas col
  proprio modello (zero crediti di testo).

## Due modalità

### 🆓 Senza account
Le **skill** e le verifiche locali funzionano subito: il testo lo scrivi TU (il tuo
modello), `lovarch verifica misure` e `lovarch cad genera` girano offline, e
`lovarch verifica computo` usa il prezzario Lombardia integrato. Per render, dati
del tuo studio e verifiche di piattaforma → `lovarch login --premium`.

### ⭐ Premium (login Lovarch)

```bash
lovarch login --premium
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

### 🪟 Windows

Homebrew **non esiste** su Windows nativo: i comandi `brew` qui sopra sono solo
macOS/Linux. Su Windows il CLI si installa con **pipx** (è Python puro — gira
identico). Guida passo-passo completa: **[docs/installazione-windows.md](./docs/installazione-windows.md)**.

```powershell
# 1. installa Python 3.11+ da https://www.python.org/downloads/
#    (spunta "Add python.exe to PATH" durante il setup)

# 2. installa pipx (una volta sola)
py -m pip install --user pipx
py -m pipx ensurepath          # chiudi e riapri il terminale dopo

# 3. installa il Lovarch CLI da GitHub
pipx install git+https://github.com/ArchPrime-official/lovarch-cli.git

# 4. da qui è tutto identico al Mac:
lovarch --version
lovarch login --premium
lovarch agent list
```

`pipx upgrade lovarch-cli` aggiorna. In alternativa, con **WSL** (Ubuntu su
Windows) valgono gli stessi comandi di macOS/Linux (Homebrew o pipx).

> ⚠️ Su Windows usa `pipx install git+…` (GitHub), **non** `pip install lovarch-cli`:
> il pacchetto PyPI è fermo a una versione vecchia.

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
lovarch --version

# Login premium (per render, dati e verifiche di piattaforma)
lovarch login --premium

# Un agente reale sul TUO brief (personalizzato, nessun contenuto hard-coded)
lovarch agent interior-designer "attico 90mq, stile caldo minimale, cliente ama il legno"

# Workflow composto: concept → render → preventivo → mini-dossier
lovarch progetto interni "attico 90mq Milano" --renders 2 -o dossier.md

# Verifiche (misure/computo gratis · normativa/sicurezza a crediti)
lovarch verifica misure pianta.dxf
lovarch verifica sicurezza psc.pdf

# CAD 2D reale
lovarch cad genera -o pianta.dxf

# Skills: il TUO Claude Code esegue le personas (zero crediti di testo)
lovarch skills install
```

## Comandi disponibili

| Comando | Descrizione |
|---------|-------------|
| `lovarch login` | Login Free o Premium |
| `lovarch signup` | Cadastro Free interattivo |
| `lovarch config` | Configurazione (lingua, storage path) |
| `lovarch agent <persona> <brief>` | Agente LLM reale (interior/DL/preventivi/geometra/sicurezza) |
| `lovarch progetto interni\|cantiere` | Workflow componibili (concept→render→preventivo · cronoprogramma→sicurezza) |
| `lovarch do render\|logo\|site\|colors\|copy\|script` | Render Studio / branding (crediti) |
| `lovarch verifica misure\|computo` | Verifiche deterministiche (gratis, anche offline) |
| `lovarch verifica normativa\|contratto\|pratica\|sicurezza\|accessibilita` | Adversariale 2 modelli (crediti) |
| `lovarch cad genera` | Genera una pianta DXF reale |
| `lovarch archchat list\|read` | Leggi le conversazioni ArchChat dello studio (gratis) |
| `lovarch skills install` | Installa le skill (testo col TUO modello, zero crediti) |
| `lovarch mcp serve\|key` | Connessione MCP (locale/remoto) |
| `lovarch context show` | Contesto di personalizzazione (premium) |
| `lovarch status <id>` | Stato di una esecuzione |
| `lovarch upgrade` | CTA per passare da Free a Premium |
| `lovarch account delete` | Right-to-erasure GDPR |
| `arch verifica dossier <cartella>` | QA completo standalone su una cartella (premium) |
| `arch jobs list\|status` | Job asincroni (video, export, upscale) |
| `arch mcp serve` | Server MCP per Claude Code / IDE |

Vedi `arch --help` per dettagli completi.

## Skills — usa il TUO agente (Claude Code, Codex...)

Se usi già un agente con un suo modello, il TESTO lo genera lui (zero crediti
Lovarch); la piattaforma addebita solo immagini, dati e verifiche di piattaforma.

Le skill si installano **da sole**: al primo comando `lovarch` (se hai
`~/.claude`) vengono copiate in `~/.claude/skills` e si aggiornano a ogni
upgrade del CLI. `lovarch skills install` resta per forzare/scegliere il target;
`LOVARCH_NO_SKILLS_SYNC=1` disattiva il sync automatico.

```bash
lovarch skills install     # opzionale — forza la copia in ~/.claude/skills
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
