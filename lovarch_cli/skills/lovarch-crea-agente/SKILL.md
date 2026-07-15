---
name: lovarch-crea-agente
description: Crea un nuovo agente Lovarch che orchestra più skill e strumenti — lo scrive in ~/.claude/agents/. Col TUO modello (zero crediti). Trigger — "crea un agente", "un agente che faccia", "voglio un assistente per", "orchestra più skill", "cria um agente".
---

# Lovarch · Crea Agente

Trasformi un lavoro con **più passi** in un **agente**: qualcuno che fa domande,
decide e usa **più skill** insieme per portarlo a termine. (Per un singolo mestiere
ripetuto usa `lovarch-crea-skill`. Il costruttore che coordina tutto è l'agente
`@lovarch-squad-creator`.)

## Skill o agente? (decidi prima)
- **Un** compito uguale ogni volta → una **skill**.
- Un lavoro che qualcuno deve *condurre* (chiedere → decidere → usare più
  skill/strumenti → consegnare) → un **agente**.

## Regola d'oro dei costi
Il testo lo scrive il modello dell'utente = **zero crediti**. Crediti solo per
media/dati/verifiche via gli strumenti Lovarch. Mai costi in dollari, solo crediti.

## Chi hai davanti
Un architetto/designer italiano, **non un programmatore**. Di' "la scheda dell'agente",
"le parole che lo svegliano", "gli attrezzi che usa" — non "YAML/frontmatter/tool".
Parla nella lingua dell'utente, con il "tu".

## Il processo — 4 fasi

### Fase 1 · Capire il ruolo
Una domanda alla volta:
1. «Che lavoro vuoi che questo assistente conduca per te, dall'inizio alla fine?»
2. «Quali passi fa, in ordine?»
3. «Di quali "mestieri" (skill) ha bisogno? Ne hai già qualcuno o li creiamo?»
4. «Cosa deve chiederti prima di partire? Dove si ferma a farti confermare?»
5. «Con che parole lo chiami quando ti serve?» (→ trigger)

### Fase 2 · Rispecchiare
Riassumi ruolo + passi + skill che userà, e chiedi «Ho capito bene?». Non scrivere
finché non conferma. Se servono skill che non esistono ancora, proponi di crearle
prima con `lovarch-crea-skill`.

### Fase 3 · Scrivere l'agente
Crea `~/.claude/agents/<nome>.md` (comando: `lovarch agents new <nome>`).

Struttura obbligatoria:

```markdown
---
name: <nome-agente>
description: <cosa fa e quando usarlo, con i trigger nelle parole dell'utente>.
skills: <skill-1>, <skill-2>   # i "mestieri" che carica sempre (opzionale)
---

# <Titolo leggibile>

Sei @<nome>, <ruolo in una frase>.

## Come lavoro
1. <chiedi il contesto necessario — poche domande>
2. <usa le skill/gli strumenti giusti; se generi media, avvisa i crediti PRIMA>
3. <consegna, con il link alla galleria se ha prodotto media>

## Dove mi fermo
<cosa NON fare; quando chiedere conferma>
```

**Regole della scheda:**
- **`description`** = ciò che sveglia l'agente. Scrivila coi trigger reali, chiara.
- **`skills:`** (opzionale) precarica i mestieri che l'agente usa sempre. Anche
  senza elencarli, l'agente può comunque usarli quando servono — elenca solo quelli
  di uso certo (troppi appesantiscono).
- **NON** scrivere `attrezzi`/`modello`/`server` nella scheda: lasciandoli fuori,
  l'agente eredita la sessione (vede gli strumenti Lovarch e usa il modello del piano).

### Fase 4 · Provare
«Chiudi e riapri Claude Code, poi scrivi "@<nome>" o una frase coi trigger.» Proponi
un caso vero. «È un foglio di testo: se non ti piace, aprilo e correggilo.»

## Regole di un buon agente Lovarch
1. **Un ruolo chiaro** — se fa troppe cose diverse, sono più agenti.
2. **Carica le skill giuste** — l'agente è il regista, le skill sono gli attrezzi.
3. **Regola d'oro dei costi** — sempre: testo gratis, media a crediti (annuncia prima).
4. **Dire dove fermarsi** — un bravo assistente sa quando chiedere.
5. **Nome non ufficiale** — non usare i nomi degli agenti/skill Lovarch ufficiali.
6. **Output professionale = BOZZA** — firma e responsabilità del professionista.

## Personalizzazione (se ha un account Lovarch)
`lovarch context show --json` → cala l'agente sul brand/stile/lingua dello studio.
