# Changelog

All notable changes to `lovarch-cli` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] — 2026-07-04

### Added
- **`lovarch agent run --cad <id>`** — computo/capitolato usano le QUANTITÀ REALI estratte da un modello CAD/BIM (aree per ambiente, superficie totale, materiali via Autodesk Model Derivative), non stime. `@computo-engineer` e `@capitolato-writer` ora ragionano sul modello.
- **`lovarch verifica dati-modello <computo> --cad <id>`** — cross-check deterministico (gratis): confronta le quantità a mq del computo con la superficie reale del modello; segnala quantità impossibili (più pavimento dell'intero appartamento).

### Changed
- `cad ifc` ora allega Pset_SpaceCommon + Qto_SpaceBaseQuantities (nome/area/altezza) a ogni IfcSpace — l'IFC ha dati leggibili da Revit/ArchiCAD/BIM, non solo geometria.

## [0.4.0] — 2026-07-04

### Added
- **Dati bidirezionali col tuo account Lovarch**: `lovarch media` (list/download/worlds/cad — la galleria nel terminale, download degli asset originali) e `lovarch dati` (progetti/progetto/finanze/prezzario/clienti/contratti, sola lettura, gratis).
- **Tutto ciò che generi dal terminale appare nell'app**: le immagini di `cli-ai-generate`/MCP ora persistono nella galleria; gli elaborati degli agenti e i dossier si salvano nell'account (`--save`, DEFAULT ON → progetto "Documenti CLI") e si riscaricano con signed URL.
- **`lovarch do world`** — mondo 3D navigabile (WorldLabs Marble 1.1) da testo o da un'immagine della tua galleria. 1200 crediti, rimborso automatico, appare anche nell'app (/mondi).
- **`lovarch cad view`** — carica DWG/DXF/RVT/IFC (upload diretto al S3 Autodesk, nessun limite via EF), traduzione SVF2 (RVT/IFC/NWD 1500 cr · DWG/DXF 300 cr) e viewer Autodesk nell'app (/cad/<id>).
- **`lovarch cad ifc`** — export BIM **IFC4 reale** (IfcSpace per ambiente + pareti, geometria estrusa): deterministico, gratis. Extra opzionale `pip install 'lovarch-cli[ifc]'`.
- **4 agenti nuovi (17 totali)**: `@studio-advisor` (analizza i DATI REALI dello studio — finanze/progetti/CRM), `@pratiche-writer` (bozza CILA/SCIA), `@gare-tender` (analisi bando D.Lgs 36/2023 con GO/NO-GO, usa `--file` per allegare il disciplinare), `@stime-immobiliari` (estimo MCA advisory).
- **`lovarch progetto completo --interactive`** — fase 0: il chief chiede i dati mancanti PRIMA di pianificare; il piano ora è **data-aware** (tiene conto di progetti/CRM/prezzario presenti nell'account).
- `lovarch agent run --file` — allega un documento (.pdf/.md/.txt) al brief.
- MCP locale: tools `lovarch_data` e `lovarch_world`.

### Changed
- `leads.stage` → `leads.status` (colonna reale) in `dati clienti` e nel digest del studio-advisor.

## [0.3.5] — 2026-07-04

### Added
- **8 nuovi agenti LLM** (`lovarch agent`, tutti advisory/BOZZA — la firma resta del tecnico abilitato):
  - Ingegneria: `@strutturista` (NTC 2018), `@impianti-engineer` (CEI 64-8/idraulico/termico), `@energia-engineer` (APE/L.10).
  - Progetto: `@progetto-chief` (orchestratore vero: dato un brief decide quali agenti far girare e consolida in dossier), `@capitolato-writer` (capitolato UNI 11337), `@computo-engineer` (computo metrico ragionato).
  - Interior: `@moodboard-curator` (direzione moodboard → `lovarch do render`), `@fornitori-scout` (selezione FF&E ragionata).
- **4 nuove verifiche adversarial** (Sonnet estrae → Opus refuta): `verifica strutturale` (NTC 2018), `verifica antincendio` (DM 03/08/2015), `verifica acustica` (DPCM 5/12/1997), `verifica energetica` (DM 26/06/2015 + L.10).
- `lovarch progetto completo <brief> [--esegui N]` — l'orchestratore `@progetto-chief` pianifica ed esegue i sotto-agenti in un unico dossier.

### Notes
- Copre ora anche l'ICP **ingegnere/impresa** (prima quasi assente). Totale: **13 agenti + 12 verificatori** reali, zero hard-coded.

## [0.3.4] — 2026-07-04

### Removed
- **Rimosso il pipeline demo hard-coded** (`lovarch run/init/audit/consolidate/dev`) e il squad vendored: era uno scaffold di test con contenuti pre-impostati ("Attico Brera"). Il lavoro reale si fa con gli **agenti LLM** (`lovarch agent`), i **workflow componibili** (`lovarch progetto`), le **verifiche** e le **skill** — nessun contenuto hard-coded.
- MCP locale: rimossi i 2 tool del demo (audit_input, list_projects) → 16 tool.

### Changed
- README riscritto sul prodotto reale (agenti LLM · workflow · verifiche · skill · CAD · ArchChat).

## [0.3.3] — 2026-07-04

### Added
- `lovarch verifica sicurezza` — pre-check adversarial di un PSC/POS (D.Lgs 81/2008): CSP/CSE, rischi per fase, costi sicurezza.
- `lovarch verifica accessibilità` — L.13/89 + DM 236/89 (livelli + parametri prescrittivi).
- `lovarch progetto cantiere` — check composto: cronoprogramma → pre-check sicurezza.
- Agente `@sicurezza-advisor` e skill `lovarch-progetto` (orchestratore del mini-dossier).

### Changed
- `lovarch verifica computo` ora funziona **offline/gratis senza login** (prezzario Lombardia integrato); con login usa i prezzari live.
- Tutte le 6 skill hanno il blocco **Free vs Premium** (senza login → procedi e indica `lovarch login --premium`).
- Messaggi **402/401 con CTA** (`lovarch upgrade`) coerenti — costo sempre in crediti.

## [0.3.2] — 2026-07-04

### Added
- `lovarch archchat list|read` — leggi le conversazioni ArchChat del tuo studio (sola lettura, **nessun credito**): non esegue l'IA di ArchChat, ti dà accesso a ciò che c'è già.
- `lovarch cad genera` — genera una **pianta DXF 2D reale** (9 layer ISO + cartiglio CNAPPC) da specifiche di ambienti o da un brief (`--brief`, IA→layout). Geometria deterministica gratis; passa `lovarch verifica misure`.

### Notes
- MCP remoto: OAuth 2.1 (conettori claude.ai senza chiave manuale) + tool `archchat_list`/`archchat_read`.

## [0.3.1] — 2026-07-04

### Added
- `lovarch do script <topic>` — script di contenuto strutturato via piattaforma (schema drift della EF scripts-generate corretto lato monorepo; refund resiliente).
- `lovarch verifica computo <file> [--region --version]` — confronto deterministico (gratis) delle voci di un computo col prezzario regionale (tabella `prezzari`, seed Lombardia): codici inesistenti, prezzi fuori tolleranza (±20%), unità incoerenti, totale.
- `lovarch verifica pratica <file> [--tipo CILA|SCIA]` — verifica adversarial (2 modelli) di una pratica edilizia: completezza (catasto, titolo, asseverazione) e coerenza titolo↔intervento.

### Notes
- Persistenza premium: il runner ora crea il progetto CRM completo nell'account dell'utente tramite la EF `cli-persist` (scrittura controllata lato server, nessuna scrittura cross-tenant).

## [Unreleased]

(No unreleased changes yet — last release was v0.3.0.)

## [0.3.0] — 2026-07-04

### Added — MCP remoto, Skills, agenti, verifica, workflows

Il rilascio che porta agli utenti tutto ciò che è stato costruito dopo v0.2.1:

- **Skills** (`lovarch skills install`) — 6 skill (interior-designer, capitolato,
  preventivi, direzione-lavori, verifica-normativa, render) che il TUO agente
  (Claude Code) esegue col PROPRIO modello: il testo non consuma crediti Lovarch,
  la piattaforma addebita solo immagini/dati/deliverable/verifica. Regola
  architetturale: "il cervello è dell'utente, la piattaforma fa ciò che solo lei fa".
- **MCP remoto** `https://mcp.lovarch.com/mcp` (Streamable HTTP) + chiavi `lvk_`
  (`lovarch mcp key`) — connetti Lovarch a qualsiasi client MCP con URL + header,
  come le altre piattaforme.
- **Agenti** (`lovarch agent`) — interior-designer, direzione-lavori, preventivi,
  geometra-catasto, personalizzati col brand dell'utente (executor=Sonnet 5,
  verifier=Opus 4.8).
- **verifica** (`lovarch verifica`) — misure (DXF, gratis), normativa, contratto
  (regola QN_007), dossier: controllo adversariale a 2 modelli.
- **do** (`lovarch do`) — render, colors, copy, logo, site: workflow della
  piattaforma dal terminale.
- **context** (`lovarch context show [--json]`) — il bundle di personalizzazione.
- **jobs** (`lovarch jobs`) — job asincroni (video/export/upscale).
- **config** (`lovarch config`) — preferenze + API keys BYO per il Free.
- Runner v5: input reale dal progetto (fine del demo hardcoded), run faseadas
  (`--deliverables`), 3 agenti redigono via LLM, chief Opus sul REJECT,
  retry-loop reale del QA.

### Rules

- Costo sempre in crediti (mai USD). Lingua dell'utente sempre. Modello
  scegliibile dal catalogo. Il testo, con un agente proprio, gira in locale.


## [0.2.1] — 2026-07-03

### Fixed

- Python 3.11: f-string with a backslash escape in the expression part
  (verifica contratto) crashed the whole CLI at import time on 3.11
  (3.12+ tolerates it). Moved the escape out of the expression.
- Lint: unused import in tests.

## [0.2.0] — 2026-07-03

### Added — Premium billing, MCP server, platform workflows, verifica

The release that makes the premium CLI bill and behave like the platform:

- **Credit debit for real**: premium `lovarch run` now routes ALL paid AI
  through the `cli-ai-generate` / `cli-ai-text` Edge Functions, debiting the
  user's Lovarch credits (1000cr=$1) with refund on failure. The runner no
  longer needs the student's `OPENAI_API_KEY` nor a service_role key —
  persistence writes as the USER (RLS).
- **MCP server** — `lovarch mcp serve` (stdio; `pip install 'lovarch-cli[mcp]'`
  or bundled). 15 tools: whoami, credits, generate_image, ai_text (multi-model:
  executor=Sonnet 5 · verifier/chief=Opus 4.8, or explicit model from the
  platform catalog), context, render, colors, copy, audit_input, list_projects,
  verify_misure/normativa/contratto/dossier, job_status.
  Register: `claude mcp add lovarch -- lovarch mcp serve`.
- **`lovarch do render|colors|copy`** — platform workflows from the terminal
  (Render Studio 2D/3D with reference image, brand palettes, marketing copy).
- **`lovarch verifica misure|normativa|contratto|dossier`** — data checking for
  professionals: deterministic DXF checks (free) + ADVERSARIAL two-model
  document checks (Sonnet extracts → Opus refutes phantom articles; CNAPPC
  contract structure + compenso rule QN_007).
- **`lovarch context show`** — the personalization bundle agents use (brand,
  style, professional signature, fiscal data, output language).
- **`lovarch jobs list|status`** — async platform jobs (video/export/upscale).
- **`lovarch config`** — user preferences + BYO API keys for free mode.

### Changed

- User-facing cost is ALWAYS credits — provider USD amounts never appear in any
  CLI/MCP output.
- Output language strictly follows the user's configured language.

### Dependencies

- New: `pypdf` (PDF text extraction) · optional extra `[mcp]`.


## [0.1.2] — 2026-06-12

### Fixed

- `lovarch run` now maps the pipeline's `qa_rejected` exit code (3) to a
  distinct `last_run.status`, instead of collapsing it into a generic
  failure. A QA-rejected dossier is no longer reported as completed.
- Vendored squad snapshot refreshed with the 2026-06-12 audit corrections
  (pipeline no longer marks a run COMPLETED when a Tier 2 QA agent returns
  REJECT).

### Docs

- README version examples and test count aligned with the shipped release.

## [0.1.1] — 2026-05-11

### Added — Squad development loop

Unlocks the daily iteration cycle on squad-architettura-progetto agents
without refresh round-trips. Maintainer edits the monorepo, every
`lovarch run` invocation picks up the change immediately.

- `LOVARCH_SQUAD_SRC` environment variable and `--squad-src` flag on
  `lovarch run` and `lovarch init`. Resolution chain: flag > env var >
  bundled vendor. When an override is active, `lovarch run` prints
  `↳ squad: <path> (source)` so the user knows which payload is in use.
- New module `lovarch_cli/squad_loader.py` centralizes the resolution
  logic. Validates that the resolved path looks like a squad payload
  (has `scripts/pipeline_runner.py` + `agents/`) and raises
  `SquadNotFoundError` with an actionable message otherwise.
- `lovarch dev show-squad-root` prints which squad path is currently
  resolved, plus env var value and bundled fallback for debugging.
- `lovarch dev refresh-squad [--source PATH] [--target PATH] [--dry-run]`
  promotes monorepo edits into the vendored snapshot in this repo.
  Auto-detects target via `__file__` heuristic when running from a dev
  install (`pip install -e`).
- `docs/agent-development.md` documents the three-environment model
  (DEV / STAGED / PRODUCTION), the daily iteration loop, the promotion
  flow, release cadence, and common pitfalls.

### Other

- Initial v0.1.0 stable release infrastructure validated end-to-end
  (homebrew tap auto-bump after the secret-context fix in PR #7,
  GitHub Release attach workflow, brew install + smoke test working
  on Pablo's machine).

### Distribution strategy

`lovarch-cli` ships via three channels — **PyPI is NOT one of them** for v0.1:

1. **Homebrew tap** (`brew install lovarch-cli`) — primary install for
   macOS/Linux users
2. **pipx from GitHub** (`pipx install git+https://...`) — for Python-savvy
   users who prefer isolated venv
3. **Source clone + pip install -e** — for contributors

PyPI publication (`pip install lovarch-cli`) is deferred to v0.2+ to avoid
the token/2FA setup overhead. The `publish-pypi.yml` workflow is kept as
manual `workflow_dispatch` so it can be activated when wanted, without
running automatically on every tag.

### Deferred to Q3

- **Story 1.3 — `pipeline_runner.py` refactor**: split the 1821-line legacy
  runner into modular phases. Currently shelled out via subprocess; works
  but is hard to unit-test independently. Adding `--legacy-runner` flag
  to allow fallback during the migration.
- **PyPI publication**: re-enable `publish-pypi.yml` on `push: tags: [v*]`
  trigger once a PyPI account + project-scoped token are configured.

## [0.1.0-beta.1] — 2026-05-10

First public BETA. Repository extracted from the Lovarch monorepo into
`ArchPrime-official/lovarch-cli` via `git filter-repo`. 13 commits of
CLI-specific history preserved.

### Added — Commands (Fase A)

- `lovarch info` — version + squad + mode status panel
- `lovarch init <name>` — scaffold a project with `input/`, `output/`,
  `project.yaml`. `--sample` lazily downloads the villa-chianti starter
  from GitHub Releases (SHA256 verified, cached in `~/.lovarch/cache/`).
  `--workflow`, `--force`, `--home` overrides.
- `lovarch audit <name>` — 18-point input checklist in 3 tiers:
  REQUIRED (10 — failure means FAIL verdict), RECOMMENDED (4 — CONCERNS),
  BRIEFING DEPTH (4 — CONCERNS). `--json` flag for CI integration.
  Persists `last_audit` in `project.yaml`.
- `lovarch run <workflow> <project>` — pre-flight gates (project exists,
  input non-empty, last audit ≠ FAIL, credits for Premium).
  Free mode: subprocess `pipeline_runner.py --dry-run` (simulation, no API
  calls). Premium mode: subprocess `--real` (debits Lovarch credits).
  `--skip-audit`, `--skip-credits`, `--dry-run` escape hatches.
- `lovarch consolidate <name>` — filename-prefix → 6-folder routing
  (`00-validation/`, `01-bootstrap/`, `02-concept/`, `03-tier1/`,
  `04-tier2/`, `05-dossier/`) + `99-other/` fallback. ZIP includes a
  localized README in 4 languages. Persists `last_dossier` in
  `project.yaml`.
- `lovarch status [<name>]` — list view (all projects with workflow + audit
  verdict + dossier state + age) or detail view (audit breakdown, dossier
  path/size, output count). Reads only `project.yaml`, no backend.

### Added — Auth & Account

- `lovarch signup` — interactive Free signup with GDPR consent. Calls
  `cli-signup` Edge Function in the Lovarch monorepo; persists token
  via OS keyring.
- `lovarch login` — interactive mode selection (free/premium). Premium
  uses PKCE OAuth flow with local callback server; falls back to manual
  URL if browser cannot open.
- `lovarch account info` / `lovarch account delete` — GDPR right-to-erasure
  (pseudonymizes remote data, revokes token; optionally wipes
  `~/.lovarch/projects/`).
- `lovarch upgrade` — opens `/cli-upgrade` (Free) or `/settings/credits`
  (Premium) with `creds.language` preference.

### Added — Infrastructure

- 4 languages bundled (it/pt/en/es) with parity anti-drift tests
  (`tests/test_i18n_loader.py`). 120+ keys across `signup`/`account`/
  `login`/`info`/`errors`/`upgrade`/`init`/`audit`/`run`/`consolidate`/
  `status` namespaces. Italian is the default; detection via `--lang`
  flag → `LOVARCH_LANG` env → `LANG` env → `'it'`.
- `DataPersistenceClient` ABC with `LocalSqliteClient` (Free) and
  `LovarchSupabaseClient` (Premium) implementations. Mirrors the
  `pm_squad_executions` / `pm_squad_steps` / `pm_squad_qa_checks`
  monorepo tables.
- `CreditsClient` ABC with `FreeCreditsClient` (no-op) and
  `LovarchCreditsClient` (calls `cli-credits-check` Edge Function with
  auto-refresh-on-401).
- 142 pytest passing in 0.7s (smoke E2E + unit coverage for i18n,
  credits, persistence, audit, init, consolidate, status,
  sample_downloader).
- CI matrix Python 3.11/3.12/3.13 + pyflakes + smoke (lovarch info /
  arch alias).
- Bundled squad (architettura-progetto, ~830KB) — 17 agents, 6 tasks,
  1 workflow (`dal-brief-al-cantiere`), 5 checklists, 4 templates. Heavy
  sample-input villa-chianti (49MB) shipped as a GitHub Releases asset
  and downloaded lazily by `lovarch init --sample`.
- Build hook (`scripts/sync_squad.py`) two-mode behavior: NO-OP in
  standalone repo (preserves vendor); re-syncs from sibling
  `squads/architettura-progetto/` in monorepo dev.
- Manual vendor refresh: `scripts/refresh_squad_vendor.py`.
- Release infrastructure:
  - `.github/workflows/publish-pypi.yml` — verifies tag matches
    `lovarch_cli/version.py`, builds wheel + sdist, uploads to PyPI for
    final tags only (skip pre-release).
  - `.github/workflows/attach-to-release.yml` — attaches wheel + sdist
    to the GitHub Release for every `v*` tag.
  - `.github/workflows/bump-homebrew-formula.yml` — auto-opens bump PR
    in `ArchPrime-official/homebrew-lovarch` when a final tag is pushed.

### Documentation

- `docs/squad-vendoring.md` — what is vendored, what isn't, why, how to
  refresh.
- `docs/release-process.md` — semver bump policy, tag conventions
  (final vs pre-release), PyPI/Homebrew setup steps, rollback guide.
- `MIGRATION-PLAN.md` — executed runbook documenting the monorepo →
  standalone split (filter-repo, history preservation, etc.).

### Companion repositories

- [`ArchPrime-official/homebrew-lovarch`](https://github.com/ArchPrime-official/homebrew-lovarch)
  — Homebrew tap with `Formula/lovarch-cli.rb`. CI tested via
  `brew install --build-from-source` + `brew test` on macos-latest.

### Known limitations

- `pip install lovarch-cli` (from PyPI) is intentionally not supported
  in v0.1 — install via `brew tap` + `brew install` OR `pipx install git+...`
  (see README). PyPI deferred to v0.2+.
- `brew install lovarch-cli` requires the `brew tap archprime-official/lovarch`
  step first (no homebrew-core submission yet).
- `arch run` shells out to the legacy 1821-line `pipeline_runner.py` —
  Story 1.3 refactor deferred to Q3.
- Voice/avatar/render features depend on Edge Functions in the Lovarch
  monorepo — Free dry-run does NOT actually call them.

[Unreleased]: https://github.com/ArchPrime-official/lovarch-cli/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/ArchPrime-official/lovarch-cli/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ArchPrime-official/lovarch-cli/compare/v0.1.0-beta.1...v0.1.0
[0.1.0-beta.1]: https://github.com/ArchPrime-official/lovarch-cli/releases/tag/v0.1.0-beta.1
