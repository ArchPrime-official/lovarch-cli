# Handoff — Fix login dominio + guida install (2026-07-11)

## Contesto
Francesca (utente Windows) ha installato il CLI seguendo la guida e, al passo
`lovarch login --premium`, il browser mostrava **«pagina non trovata»** seguito da
**«Timeout: nessuna risposta dal browser in 5 minuti»**. Login impossibile.

## Causa radice (due strati concatenati)

### 1. Bug del codice — già corretto in v0.4.4, ma lei aveva la v0.4.3
La **v0.4.3** in `commands/login.py` aveva il dominio hardcoded:
```python
LOVARCH_WEB_BASE = "https://lovarch.com"   # dominio SBAGLIATO
# commento (invertito!): "/cli-auth React page only exists on lovarch.com"
```
- `lovarch.com` serve il **sito marketing** (SPA `LovarchStudioLP/CMS`) che **non ha**
  la rotta `/cli-auth` → il React Router rende il **404 client-side** = «pagina non trovata».
- La rotta `/cli-auth` esiste solo su **`app.lovarch.com`** (app Lovarch, `App.tsx:290`).

Corretto in **v0.4.4** (#71) centralizzando in `config.DEFAULT_WEB_URL = https://app.lovarch.com`
(override con `LOVARCH_WEB_URL`). La v0.4.3 **non** ha l'override → non recuperabile senza aggiornare.

### 2. Bug di distribuzione — quello che ha davvero rotto l'utente
`README.md` e `docs/installazione-windows.md` puntavano a un **URL wheel fisso della v0.4.3**
(l'ultima release CON il bug). Chi seguiva la guida installava proprio la versione rotta,
pur essendo la 0.4.7 già pubblicata.

## Fix di questa sessione (PR #76)
Bump delle 3 URL wheel fisse **v0.4.3 → v0.4.7** (README:97, installazione-windows.md:66 e :167).
Il placeholder `vX.Y.Z` della sezione upgrade resta invariato.

## Verifica empirica (smoke reale)
- Installata la wheel **0.4.7** reale (Python 3.14, come l'utente) → `lovarch-cli 0.4.7`.
- Codice installato `login.py:98` → monta `https://app.lovarch.com/cli-auth`. ✅
- Browser (Playwright) su `app.lovarch.com/cli-auth?...` → riconosce la rotta e **redirige al
  login preservando `state`/`code_challenge`/`redirect_uri`/`lang`** → flusso corretto. ✅
- Browser su `lovarch.com/cli-auth?...` → **«404 · Pagina non trovata»** → riprodotto
  esattamente l'errore dell'utente. ✅
- Non testabile senza le credenziali dell'utente: il click finale «Autorizza» da loggati
  (flusso OAuth standard, già funzionante per gli altri utenti).

## Soluzione per l'utente (Windows PowerShell)
```powershell
py -m pipx install --force "https://github.com/ArchPrime-official/lovarch-cli/releases/download/v0.4.7/lovarch_cli-0.4.7-py3-none-any.whl"
lovarch --version          # deve mostrare 0.4.7
lovarch login --premium
```

## Debiti aperti (follow-up, NON in questa PR)
- **[APERTO] Formula Homebrew ferma a v0.2.1** (`homebrew-lovarch/Formula/lovarch-cli.rb`) —
  chi installa via `brew` su Mac prende una versione di maggio con lo stesso bug del dominio.
  *Chiusura:* bump formula → v0.4.7 (o automatizzare via `bump-homebrew-formula.yml`).
- **[APERTO] PyPI dormant a 0.3.4** — `pip install lovarch-cli` serve una versione vecchia.
  Il README avvisa di non usarlo, ma resta una trappola. *Chiusura:* pubblicare o deprecare
  esplicitamente il canale PyPI.
- **[APERTO] URL wheel fisse per versione** — richiedono bump manuale a ogni release.
  *Chiusura:* far bumpare README/guida dal pipeline di release, o link `releases/latest`.

## Lezione
Quando una guida di install punta a un **artefatto con versione fissa**, quell'URL diventa
stantìo alla release successiva e serve l'ultima versione **prima** di un fix. Le guide vanno
bumpate insieme al codice (o puntare a `latest`), altrimenti i nuovi utenti ereditano bug già risolti.
