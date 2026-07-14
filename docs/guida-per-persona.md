# Guida per persona — quale superficie usare

Lovarch ti raggiunge in tre modi (come Higgsfield): **Skill**, **CLI**, **MCP**.
La regola d'oro dei costi è sempre la stessa:

> **Il testo lo genera il TUO modello quando ne hai uno** (Claude Code, un IDE
> agent): zero crediti Lovarch. La piattaforma addebita crediti solo per ciò che
> **solo lei** offre — immagini/render, dati del tuo studio, deliverable
> persistiti, verifiche di piattaforma.

Non esponiamo mai i costi API: per te il costo è **sempre in crediti**.

## Le tre superfici

| | Quando usarla | Testo | Immagini / dati |
|---|---|---|---|
| **Skill** (`lovarch skills install`) | Hai già Claude Code / un agente | il TUO modello (0 crediti) | via `lovarch` (crediti) |
| **CLI** (`lovarch …`) | Lavori nel terminale, con o senza agente | modelli piattaforma (crediti) | crediti |
| **MCP** (`mcp.lovarch.com`) | Claude/IDE via connettore, una chiave `lvk_` | fallback (crediti) — preferisci le Skill se hai un modello | crediti |

Gratis (nessun credito): `lovarch context show`, `lovarch verifica misure`,
`lovarch verifica computo`, `lovarch skills install`, `lovarch jobs`.

---

## Architetto / progettista

- **Progetto completo**: `lovarch progetto completo "<brief>" --esegui 3` (il chief pianifica e gli specialisti eseguono) oppure `lovarch progetto interni "<brief>" --renders 2` (concept → render → preventivo → dossier).
- **Render**: `lovarch do render "<scena>"` · logo/sito: `lovarch do logo|site`.
- **Contenuti**: `lovarch do script "<argomento>"`, `lovarch do copy`.
- **Verifiche**: `lovarch verifica normativa capitolato.pdf` (adversarial), `lovarch verifica contratto contratto.pdf`.
- **Con Claude Code**: installa le Skill — il concept/relazioni li scrive il tuo modello, e chiami `lovarch do render` solo per le immagini.

## Interior designer

- **Workflow dedicato**: `lovarch progetto interni "attico 90mq, stile caldo minimale, cliente ama il legno" --renders 3` → concept + render + preventivo + mini-dossier.
- **Standalone**: `lovarch agent interior-designer "<brief>"`.
- **Skill**: `lovarch-interior-designer` (parte da sola nel tuo agente descrivendo il progetto).
- Personalizzazione automatica: brand, stile, lingua dal tuo profilo (`lovarch context show`).

## Geometra / tecnico catastale

- **Misure DXF** (gratis): `lovarch verifica misure pianta.dxf` — layer ISO, etichette ambienti, cartiglio CNAPPC.
- **Computo** (gratis): `lovarch verifica computo computo.csv --region Lombardia` — voci vs prezzario, prezzi fuori tolleranza, unità.
- **Pratica edilizia**: `lovarch verifica pratica pratica.pdf --tipo CILA` — completezza + coerenza titolo↔intervento (adversarial).
- **Catasto**: `lovarch agent geometra-catasto "<dati visura>"` (controllo, la firma resta tua).

## Impresa / Direzione Lavori

- **Cronoprogramma e cantiere**: `lovarch agent direzione-lavori "<progetto>"` — SAL, visite, verbali, sicurezza (D.Lgs 81/2008).
- **Preventivi**: `lovarch agent preventivi "<incarico>"` — proposta con onorario (per privati i parametri DM 17/06/2016 sono orientativi).
- **Computo di controllo** (gratis): `lovarch verifica computo`.

---

## Costi: come rispondere al cliente

Se un cliente chiede quanto costa, si parla **solo dei crediti** e del prezzo che
paga per i pacchetti di crediti — mai del costo API. Esempio: un render `medium`
costa ~53 crediti; con un pacchetto da *N* crediti a *€X*, il costo per render è
`53 × (X/N)`. Il listino dei crediti è quello dei piani/pacchetti Lovarch.

## Lingua

L'output è sempre nella lingua impostata nel tuo profilo (`preferred_language`)
o forzata con `--language`. Non si mescola mai un'altra lingua.
