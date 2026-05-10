# Template Capitolato Speciale d'Appalto · UNI 11337-7 + CAM 2025

> Struttura del capitolato che il `@capitolato-writer` deve generare.
> 12 sezioni standard. ~60-80 pagine totali quando popolato.

---

## CAPITOLATO SPECIALE D'APPALTO

per i lavori di **{{descrizione_breve_intervento}}**
sito in **{{immobile_indirizzo}}**

Committente: **{{cliente_nome}} {{cliente_cognome}}**
Progettista: **Arch. {{architetto_nome}} {{architetto_cognome}}**
Importo lavori a base d'asta: **€ {{importo_lavori}}** (IVA 10% inclusa)
Durata cantiere: **{{durata_giorni}} giorni** lavorativi

---

## Indice

1. Disposizioni generali
2. Descrizione delle opere
3. Specifiche tecniche di esecuzione
4. Materiali e prodotti
5. Modalità di esecuzione
6. Tolleranze e prove
7. Sicurezza in cantiere
8. Oneri e obblighi dell'Appaltatore
9. Direzione lavori
10. Garanzie e collaudo
11. Penali e contestazioni
12. Disposizioni finali

---

## 1 · Disposizioni generali

### 1.1 Oggetto del capitolato
Il presente capitolato disciplina l'appalto dei lavori di {{descrizione_intervento}} all'immobile sito in {{immobile_indirizzo_completo}}, identificato catastalmente al Foglio {{foglio}} · Mappale {{mappale}} · Sub {{subalterno}}.

### 1.2 Riferimenti normativi
- Codice Civile artt. 1655-1677 (appalto);
- Legge 109/1994 e D.Lgs 36/2023 (Codice Appalti) — per analogia, ove applicabile a privato;
- DPR 380/2001 (TU Edilizia);
- D.Lgs 81/2008 (sicurezza nei cantieri);
- DM 17/01/2018 (NTC 2018);
- UNI 11337-7:2018 (qualificazione figure BIM);
- DM 23/06/2022 (CAM Edilizia 2025);
- DM 5/7/1975 (norme igienico-sanitarie).

### 1.3 Documenti contrattuali (in ordine di prevalenza)
1. Contratto di appalto;
2. Presente capitolato speciale;
3. Capitolato generale (se presente);
4. Elaborati di progetto esecutivo;
5. Computo metrico estimativo;
6. Cronoprogramma lavori;
7. Piano di sicurezza e coordinamento (PSC) — quando obbligatorio.

### 1.4 Definizioni
- **Stazione appaltante:** Committente
- **Direzione Lavori (DL):** {{architetto_nome}} {{architetto_cognome}}
- **Coordinatore Sicurezza Esecuzione (CSE):** {{cse_nome}} (ove obbligatorio)
- **Appaltatore:** impresa aggiudicataria

---

## 2 · Descrizione delle opere

### 2.1 Descrizione generale
{{descrizione_estesa_intervento}}

### 2.2 Lavorazioni previste

| Categoria | Descrizione |
|-----------|-------------|
| Demolizioni | Demolizione tramezze interne, rimozione pavimenti, smontaggio impianti vetusti |
| Strutture | Nessun intervento strutturale |
| Murature | Costruzione nuove tramezze in laterizio cm 8/12 |
| Impianti elettrici | Rifacimento completo impianto elettrico unitamente a domotica leggera |
| Impianti idro-sanitari | Rifacimento completo, riposizionamento bagni |
| Impianti termici | Riscaldamento a pavimento + VMC con recupero |
| Pavimenti | Posa parquet rovere, gres bagni, conservazione seminato |
| Rivestimenti | Rivestimenti bagni in gres effetto travertino |
| Serramenti interni | Sostituzione completa porte interne |
| Falegnameria | Cucina su misura, libreria studio, cabina armadio |
| Finiture | Tinteggiatura calce, restauro decori soffitti |
| Pulizia finale | Pulizia post-cantiere con consegna chiavi |

### 2.3 Esclusioni
- Sostituzione caldaia (esistente in buono stato);
- Lavori sul terrazzo/pavimentazione esterna terrazzo (non oggetto del presente appalto);
- Forniture mobili (ad eccezione di cucina, libreria, cabina armadio commissionate dall'architetto).

---

## 3 · Specifiche tecniche di esecuzione

### 3.1 Demolizioni
- Tutte le demolizioni interne devono essere **selettive** (CAM 2025);
- Recupero ≥ 70% dei rifiuti edili (laterizi, ferro, vetro);
- Smaltimento esclusivamente presso impianti autorizzati con FIR;
- Documentazione di tracciabilità obbligatoria per ogni rifiuto.

### 3.2 Tramezze
- Laterizio forato 8 cm interpiano stanze abitabili;
- Laterizio forato 12 cm divisori bagni (per insonorizzazione);
- Allettamento con malta cementizia o adesivi specifici;
- Intonaco di finitura calce naturale spessore minimo 1.5 cm.

### 3.3 Impianti elettrici
- Filo ordito antifumo (LSZH) di marca {{marca_filo}};
- Quadro generale {{marca_quadro}} dimensionato per 4.5 kW + cabina armadio;
- Tutte le prese 16A schuko + USB type-C nella zona living;
- Comando luci tramite domotica {{marca_domotica}} (es. KNX, Loxone, Crestron);
- Predisposizione fibra ottica in studio + cabina armadio + camera padronale.

### 3.4 Riscaldamento
- Sistema a pavimento (pannelli radianti) in tutte le zone;
- Tubazione in PEX-A 17×2 mm passo 10 cm;
- Massetto cementizio additivato spessore 8 cm;
- Termoregolazione zonale (1 zona per ogni stanza);
- Caldaia esistente: verifica idoneità, eventuale sostituzione modulo elettronico.

### 3.5 VMC
- Sistema centralizzato con recupero di calore ≥ 75% (efficienza certificata UNI EN 13141-7);
- Marca {{marca_vmc}} o equivalente;
- Bocchette di aspirazione in cucina + bagni;
- Bocchette di immissione in living + camere;
- Filtri F7 + ePM1 (allergie cliente).

### 3.6 Pavimenti
- Living + camere: parquet rovere chiaro spazzolato sp. 14/3.5 mm — marca {{marca_parquet}};
- Bagni: gres porcellanato effetto travertino formato 60×120 cm — marca {{marca_gres}};
- Cucina: continuazione parquet (con trattamento idro-resistente);
- Conservazione **seminato veneziano esistente** in zona dedicata del soggiorno (intervento di restauro a cura di restauratore qualificato).

### 3.7 Rivestimenti bagni
- Effetto travertino tonalità calda fino a h. 220 cm;
- Posa rettificata 2 mm, fuga in epossidica color travertino;
- Top lavabo in pietra naturale travertino classico spessore 4 cm.

---

## 4 · Materiali e prodotti

Tutti i materiali devono essere:

a) **Conformi alle norme tecniche italiane ed europee** (CE, UNI EN);
b) Dotati di **scheda tecnica** consegnata al DL prima della posa;
c) **CAM-compliant** dove possibile (DM 23/06/2022):
   - Laterizi con riciclato ≥ 30%;
   - Calcestruzzo con riciclato ≥ 15%;
   - Legno **FSC/PEFC** certificato;
   - Isolanti con **DAP/EPD** (Dichiarazione Ambientale di Prodotto);
d) **Privi di formaldeide** (UNI EN 717) per finiture interne (richiesta esplicita cliente per camera Sofia);
e) **Vernici naturali** o ecologiche in classe E1 minimo.

### 4.1 Lista materiali principali
La lista completa dei materiali con marca, codice, scheda tecnica, EPD e quantitativo è allegata in *allegato A*.

---

## 5 · Modalità di esecuzione

### 5.1 Cronoprogramma
Vedi *allegato B · Cronoprogramma 90 giorni*.

### 5.2 Sequenza lavorazioni
- Fase 1 (gg 1-15): Demolizioni e preparazione
- Fase 2 (gg 16-35): Impianti (elettrico + idraulico + termico + VMC)
- Fase 3 (gg 36-55): Murature e tracce
- Fase 4 (gg 56-75): Pavimenti, rivestimenti, finiture
- Fase 5 (gg 76-85): Falegnameria su misura, accessori
- Fase 6 (gg 86-90): Pulizia finale, consegna

### 5.3 Orari di lavoro in cantiere
- Lunedì - Venerdì: 8:00 - 18:00 (con pausa 12:00-13:30)
- Sabato: 8:00 - 13:00 (solo se necessario)
- Domenica e festivi: vietato (regolamento condominio)

---

## 6 · Tolleranze e prove

### 6.1 Tolleranze geometriche
- Verticalità pareti: ± 3 mm su 2 m
- Planarità pavimenti: ± 2 mm sotto regolo da 2 m
- Squadratura ambienti: ± 5 mm su 4 m

### 6.2 Prove obbligatorie
- Prova di tenuta impianto idraulico (a pressione 2 bar per 24 h)
- Prova funzionamento riscaldamento a pavimento (test acceso 7 gg)
- Misurazione termocamera del massetto (verifica omogeneità)
- Test efficienza VMC con misuratore portate

---

## 7 · Sicurezza in cantiere

[Sezione popolata da CSP/CSE quando nominato]

### 7.1 PSC
Per il presente cantiere è obbligatoria la nomina del **Coordinatore per la Sicurezza in fase di Progettazione (CSP)** ed Esecuzione (CSE) ai sensi del D.Lgs 81/2008 art. 90, in quanto:
- Sono presenti **più imprese** (impresa edile + impianti elettrici + idraulici);
- Durata totale stimata > 200 uomini-giorno.

Il CSP/CSE è **incarico separato dal presente contratto**.

### 7.2 Notifica preliminare
L'Appaltatore deve trasmettere notifica preliminare ad ASL e ITL almeno 30 giorni prima dell'inizio lavori.

---

## 8-12 · [Sezioni successive]

[Sezioni 8 (Oneri Appaltatore), 9 (Direzione Lavori), 10 (Garanzie e Collaudo), 11 (Penali), 12 (Disposizioni finali) — popolate dal `@capitolato-writer`]

---

## Allegati

- A · Lista materiali con marche e schede tecniche
- B · Cronoprogramma 90 giorni
- C · Tavole di progetto esecutivo (richiamate per riferimento)
- D · Computo metrico estimativo
- E · Schede tecniche EPDs / DAP

---

**Approvato dal Committente e dal Progettista, in data {{data_firma}}.**

**Firma Committente:** _________________________
**Firma Progettista:** _________________________
