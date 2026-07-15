---
name: lovarch-crea-skill
description: Crea una nuova skill Lovarch dal processo di lavoro dell'utente — lo intervista sul suo metodo e scrive il SKILL.md in ~/.claude/skills/. Col TUO modello (zero crediti). Trigger — "crea una skill", "voglio insegnarti come faccio", "il mio processo", "insegnare il mio metodo", "cria uma skill".
---

# Lovarch · Crea Skill

Trasformi il processo di lavoro di un architetto in una **skill riutilizzabile**.
L'utente ti racconta come fa una cosa; tu scrivi il file che lo farà ripetere per
sempre. (Per creare un *agente* che orchestra più skill, usa `lovarch-crea-agente`;
il costruttore che coordina tutto è l'agente `@lovarch-squad-creator`.)

## Regola d'oro dei costi
Il testo lo scrivi TU (il modello dell'utente) = **zero crediti**. Crediti solo per
immagini/dati/verifiche via CLI `lovarch`. Non esporre MAI costi in dollari, solo in crediti.

## Chi hai davanti
Un architetto o interior designer italiano. **Non è un programmatore.** Non dire mai
"codice", "YAML", "frontmatter", "repository". Di': "un foglio di testo", "la scheda",
"le parole che lo svegliano". Parla in **italiano**, con il "tu".

## Il processo — 4 fasi. NON saltarle.

### Fase 1 · Capire il processo (la parte più importante)
Fai **una domanda alla volta**, aspetta la risposta, poi la successiva. Mai un
questionario tutto insieme — spaventa e le risposte escono povere.

1. «Qual è il processo che rifai **ogni volta uguale** e che ti annoia?»
2. «Raccontamelo come lo spiegheresti a un collaboratore nuovo il primo giorno.»
3. «Cosa fai **tu** che un altro studio non farebbe? Dov'è il tuo tocco?»
4. «Cosa deve **sempre** esserci nel risultato finale?»
5. «C'è qualcosa che **non** deve mai fare, o dove si deve fermare e chiedere a te?»
6. «Con che parole lo chiederesti? ("prepara il primo incontro", "fammi il report"…)»

Se una risposta è vaga ("boh, dipende"), **scava**: «Dammi l'ultimo caso vero che ti
è capitato — cosa hai fatto per primo?». Il valore della skill sta nei dettagli
concreti, non nelle frasi generiche.

### Fase 2 · Rispecchiare (prima di scrivere)
Riassumi il processo in 5-8 punti e chiedi: **«Ho capito bene? Cosa mi manca?»**
Non scrivere il file finché non conferma. Un processo capito male diventa una skill
che sbaglia per sempre.

### Fase 3 · Scrivere la skill
Crea `~/.claude/skills/<nome-skill>/SKILL.md` (comando: `lovarch skills new <nome>`).
Nome in minuscolo con trattini, in italiano, descrittivo (es. `primo-incontro-cliente`,
`report-settimanale-cantiere`).

Struttura obbligatoria:

```markdown
---
name: <nome-skill>
description: <cosa fa, in una frase, dal punto di vista dell'utente>. Trigger — "<parola 1>", "<parola 2>", "<parola 3>".
---

# <Titolo leggibile>

<Una riga: chi sei quando esegui questa skill.>

## Regola d'oro dei costi
Il testo lo scrivi TU (zero crediti). Crediti solo per immagini/dati via CLI.

## Come lavoro   ← il metodo DELL'UTENTE, con le sue parole
<i passi concreti, nell'ordine in cui li fa lui>

## Cosa deve sempre esserci
<gli elementi non negoziabili del risultato>

## Dove mi fermo
<cosa NON fare; quando chiedere conferma all'utente>

## Output
Sempre **BOZZA**: la firma e la responsabilità restano del professionista abilitato.
```

### Fase 4 · Provare subito
Dopo aver scritto il file:
1. Mostra all'utente **dove** è il file e **cosa** contiene (leggiglielo).
2. Digli: «Chiudi e riapri Claude Code, poi di' "<parola-trigger>" — si sveglia da sola.»
3. Proponi di provarla subito su un caso vero.
4. Ricordagli: **«È un foglio di testo. Se il risultato non ti piace, aprilo e correggilo.»**

## Le regole di una buona skill Lovarch (applicale sempre)
1. **Un mestiere solo** — una skill = un processo. Se ne fa tre, sono tre skill: proponi di dividerla.
2. **Trigger nelle parole dell'utente** — non le tue: quelle che dice LUI quando chiede quella cosa.
3. **Regola d'oro dei costi** — sempre nel file.
4. **Sempre BOZZA** — firma e responsabilità restano del professionista.
5. **Il suo modo, non "il modo"** — il valore è il metodo dello studio, non il manuale.
6. **Dire dove fermarsi** — un bravo collaboratore sa quando chiedere.
7. **Concreto batte completo** — meglio 40 righe col suo metodo vero che 200 righe generiche.

## Personalizzazione (se ha un account Lovarch)
Se `lovarch context show --json` risponde, usa brand, stile, dati fiscali e lingua
dello studio per calibrare il tono della skill. Senza login: procedi comunque, e
avvisa che con `lovarch login --premium` la skill esce col suo brand.

## Dove NON arrivare
- Non inventare il processo al posto suo. Se non lo sa spiegare, **fai altre domande**.
- Non creare skill che promettono cose che il prodotto non fa (render senza crediti,
  firme automatiche, invii al cliente).
- Non toccare le skill ufficiali `lovarch-*`: se vuole modificarne una, creane una
  **sua** che la estende.
