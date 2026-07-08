# Installazione su Windows

Homebrew (`brew tap` / `brew install`) è **solo macOS e Linux**: su Windows non
esiste. Ma il Lovarch CLI è scritto in **Python puro** e non usa nulla di
specifico di macOS — quindi gira identico su Windows. Cambia solo il **modo di
installarlo**: si usa **pipx**.

Tutti i comandi *dopo* l'installazione (`lovarch login`, `lovarch agent`,
`lovarch cad`, le skill…) sono **uguali** su Windows, macOS e Linux.

Hai due strade:

| | Per chi | Difficoltà |
|---|---|---|
| **A. pipx (Windows nativo)** | Vuoi lavorare direttamente in PowerShell | ⭐ consigliata |
| **B. WSL (Ubuntu su Windows)** | Sei già a tuo agio col terminale Linux | ⭐⭐ |

---

## A. pipx — Windows nativo (consigliato)

> **Attenzione al `$`.** Nelle guide (e nelle slide del corso) i comandi sono
> preceduti da `$` o `PS C:\>`: è solo il **simbolo del prompt**, non fa parte
> del comando. In PowerShell digita il comando **senza** quel simbolo — altrimenti
> vedi l'errore «`$` non è riconosciuto». E `brew` **non** esiste su Windows.

### 1. Installa Python 3.11+ (unico prerequisito obbligatorio)

Con **winget** (già presente su Windows 10/11), in PowerShell:

```powershell
winget install --id Python.Python.3.12 -e
```

Oppure scarica da <https://www.python.org/downloads/> e, **durante il setup,
spunta "Add python.exe to PATH"** (è il passo che quasi tutti dimenticano —
senza, `python`/`py` non funzionano dal terminale).

**Chiudi e riapri PowerShell**, poi verifica:

```powershell
py --version      # deve stampare Python 3.11.x o superiore
```

> Con il metodo qui sotto (wheel della release) **non serve git**: l'unico
> prerequisito è Python.

### 2. Installa pipx (una volta sola)

pipx installa app Python in ambienti isolati, così le dipendenze del CLI non si
mescolano con altro:

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
```

**Chiudi e riapri il terminale** dopo `ensurepath` (aggiorna il PATH).

### 3. Installa il Lovarch CLI (dal wheel della release — nessun git)

```powershell
pipx install "https://github.com/ArchPrime-official/lovarch-cli/releases/download/v0.4.3/lovarch_cli-0.4.3-py3-none-any.whl"
```

> Le virgolette servono in PowerShell. Trovi l'URL dell'ultima versione tra gli
> asset di ogni release: <https://github.com/ArchPrime-official/lovarch-cli/releases>
> (file `lovarch_cli-<versione>-py3-none-any.whl`).
>
> *Alternativa per sviluppatori* (richiede git installato,
> <https://git-scm.com/download/win>): `pipx install git+https://github.com/ArchPrime-official/lovarch-cli.git`

### 4. Verifica e accedi

```powershell
lovarch --version
lovarch login --premium      # si apre il browser → login Lovarch
lovarch agent list           # 17 agenti pronti
```

Da qui in poi è **identico al Mac**.

---

## B. WSL (Ubuntu dentro Windows)

Se usi WSL, hai un vero ambiente Linux: valgono **gli stessi comandi di
macOS/Linux**. Puoi usare Homebrew *oppure* pipx:

```bash
# opzione Homebrew (dentro WSL)
brew tap archprime-official/lovarch
brew install lovarch-cli

# opzione pipx (dentro WSL)
pipx install git+https://github.com/ArchPrime-official/lovarch-cli.git

lovarch login --premium
```

> Nota: il browser per il login si apre in Windows; se WSL non lo apre da solo,
> il CLI stampa l'URL — copialo e incollalo nel browser.

---

## Aggiornare

Rilancia l'install puntando al wheel della **nuova** versione, con `--force`:

```powershell
pipx install --force "https://github.com/ArchPrime-official/lovarch-cli/releases/download/vX.Y.Z/lovarch_cli-X.Y.Z-py3-none-any.whl"
```

(Sostituisci `X.Y.Z` con l'ultima versione dalla pagina delle release.) Se hai
installato con `git+…`, invece basta `pipx upgrade lovarch-cli`.

Le **skill** (`/lovarch-*` per Claude Code) si aggiornano **da sole** al primo
comando `lovarch` dopo l'upgrade — non serve reinstallarle.

## Disinstallare

```powershell
pipx uninstall lovarch-cli
```

---

## Dove salva i dati (Windows)

Tutto sotto il tuo profilo utente, **indipendente dalla cartella di progetto**:

- **Sessione di login**: Windows Credential Manager (via `keyring`), con fallback
  in `C:\Users\<tuo-utente>\.lovarch\credentials.json`.
- **Stato / config**: `C:\Users\<tuo-utente>\.lovarch\`
- **Skill di Claude Code**: `C:\Users\<tuo-utente>\.claude\skills\`
  (l'auto-sync funziona anche qui).

Login e skill valgono quindi per **tutti i progetti** dello stesso utente
Windows. Cambiando macchina o utente di Windows, reinstalli e rifai il login.

---

## Problemi frequenti

| Sintomo | Causa / soluzione |
|---|---|
| «`$` non è riconosciuto» | Il `$` è solo il simbolo del prompt — digita il comando **senza** `$` (e `brew` non esiste su Windows). |
| `lovarch` non riconosciuto | PATH non aggiornato → riapri il terminale; se persiste, ri-esegui `py -m pipx ensurepath`. |
| `py` / `python` non riconosciuto | Python non è nel PATH → reinstalla Python (`winget install --id Python.Python.3.12 -e`) o spunta **"Add python.exe to PATH"**. |
| Ho fatto `pip install lovarch-cli` e la versione è vecchia | Il pacchetto PyPI è fermo a una release vecchia. Disinstalla (`pip uninstall lovarch-cli`) e usa il **wheel della release** (vedi passo 3). |
| Il browser non si apre al login | Copia l'URL stampato dal CLI e incollalo manualmente nel browser. |
| Voglio disattivare l'auto-sync delle skill | Imposta la variabile d'ambiente `LOVARCH_NO_SKILLS_SYNC=1`. |

---

## In sintesi

```powershell
# una volta per macchina (senza $, senza git):
winget install --id Python.Python.3.12 -e                              # riapri il terminale
py -m pip install --user pipx
py -m pipx ensurepath                                                  # riapri il terminale
pipx install "https://github.com/ArchPrime-official/lovarch-cli/releases/download/v0.4.3/lovarch_cli-0.4.3-py3-none-any.whl"
lovarch login --premium

# ogni giorno, in qualsiasi progetto:
lovarch agent run ...      # già loggato, skill già sincronizzate
```
