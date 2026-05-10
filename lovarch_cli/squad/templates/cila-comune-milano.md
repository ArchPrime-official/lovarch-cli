# Template CILA · Comune di Milano

> Modulo standard per Comunicazione Inizio Lavori Asseverata (DPR 380/2001 art. 6-bis).
> Variabili tra `{{...}}` da sostituire dal `@pratiche-it`.

---

## COMUNE DI MILANO
**Sportello Unico per l'Edilizia** · Direzione Urbanistica
Via Giovanni Pirelli 39 · 20124 Milano

## COMUNICAZIONE DI INIZIO LAVORI ASSESERATA (CILA)

ai sensi dell'art. 6-bis del DPR 6 giugno 2001 n. 380 (TU Edilizia)
e ai sensi della L.R. Lombardia 11 marzo 2005 n. 12

---

### A · Identificazione del committente

Il/la sottoscritt{{cliente_genere}} **{{cliente_nome}} {{cliente_cognome}}**
nato/a a {{cliente_nato_a}} il {{cliente_data_nascita}}
residente in {{cliente_residenza_indirizzo}}, {{cliente_residenza_comune}} ({{cliente_residenza_provincia}})
codice fiscale **{{cliente_codice_fiscale}}**
in qualità di **{{cliente_qualita}}** (es. proprietario, comproprietario, usufruttuario)

(eventuale comproprietario)
{{secondo_cliente_block_se_presente}}

### B · Identificazione dell'immobile

Posizione: **{{immobile_indirizzo_completo}}**
Comune: **{{immobile_comune}}** ({{immobile_provincia}})
Cap: {{immobile_cap}}

Identificativi catastali:
- Sezione: {{catastale_sezione}}
- Foglio: **{{catastale_foglio}}**
- Mappale: **{{catastale_mappale}}**
- Subalterno: **{{catastale_subalterno}}**
- Categoria: {{catastale_categoria}} (es. A/2)
- Classe: {{catastale_classe}}
- Consistenza: {{catastale_consistenza}}
- Rendita catastale: € {{catastale_rendita}}

### C · Tecnico abilitato (asseveratore)

Nome e cognome: **{{architetto_nome}} {{architetto_cognome}}**
Codice fiscale: {{architetto_codice_fiscale}}
P.IVA: {{architetto_piva}}
Iscritto all'**Ordine degli Architetti, Pianificatori, Paesaggisti e Conservatori**
della Provincia di **Milano** al n. **{{architetto_n_ordine}}**
Studio in: {{architetto_studio_indirizzo}}
PEC: **{{architetto_pec}}**
Email ordinaria: {{architetto_email}}
Telefono: {{architetto_telefono}}

### D · Descrizione dell'intervento

#### D.1 · Tipo di intervento (art. 3 DPR 380/2001)

[ ] manutenzione ordinaria
[ ] manutenzione straordinaria
[**X**] {{tipo_intervento}} (es. ristrutturazione edilizia leggera senza modifica volumi/sagoma)
[ ] altro: ____

#### D.2 · Descrizione dei lavori

{{descrizione_lavori}}

Esempio standard:
> Ristrutturazione interna dell'unità immobiliare per la riconfigurazione distributiva
> degli ambienti, con demolizione e ricostruzione di tramezzature interne, rifacimento
> degli impianti tecnologici (elettrico, idrico-sanitario, termico, VMC), sostituzione
> dei serramenti interni, posa di nuovi pavimenti e rivestimenti.
> Non sono previsti interventi su elementi strutturali, prospetti, sagome o volumi.

#### D.3 · Superfici interessate

- Superficie utile prima dei lavori: {{sup_utile_pre_m2}} m²
- Superficie utile dopo i lavori: {{sup_utile_post_m2}} m²
- Variazione: {{sup_variazione_m2}} m²
- Volume immobile: {{volume_m3}} m³
- Eventuali superfici esterne (terrazzi/balconi): {{sup_esterne_m2}} m²

#### D.4 · Inizio lavori

Data prevista di inizio: **{{data_inizio_lavori}}**
Durata stimata: **{{durata_lavori_giorni}} giorni**

### E · Asseverazione del tecnico

Il sottoscritto tecnico abilitato di cui al punto C, in qualità di asseveratore di questa CILA,

**ASSEVERA**

a) la conformità dei lavori al **PGT vigente** e al Regolamento Edilizio del Comune di Milano;
b) la **non incidenza strutturale** dei lavori (gli interventi non riguardano parti strutturali);
c) il rispetto delle norme **antisismiche, di sicurezza, antincendio, igienico-sanitarie**;
d) il rispetto delle norme **efficientamento energetico** e dei minimi di legge;
e) il rispetto delle **norme paesaggistiche e dei beni culturali** ove applicabili;
f) di aver verificato lo **stato legittimo** dell'unità immobiliare;
g) di operare in **assenza di conflitti di interesse** con il committente.

### F · Vincoli ambientali e paesaggistici

[ ] Immobile NON ricade in zona vincolata
[**{{vincolato}}**] Immobile ricade in **{{vincolo_descrizione}}**
   (es. Zona A1 PGT Milano · NAF Brera · vincolo paesaggistico D.Lgs 42/2004)

In caso di vincolo paesaggistico:
[ ] Esonerato (allegato A DPR 31/2017)
[**{{paesaggistica_tipo}}**] Procedura semplificata (allegato B DPR 31/2017)
[ ] Procedura ordinaria (art. 146 D.Lgs 42/2004)

Autorizzazione paesaggistica (se richiesta): **{{paesaggistica_riferimento}}**

### G · Conformità urbanistica e regolamentare

L'intervento è conforme:
- al PGT (Piano di Governo del Territorio) vigente del Comune di Milano (variante 2024);
- al Piano delle Regole;
- al Regolamento Edilizio comunale (in particolare artt. 38 sup. minime, RAI minima);
- al Codice Civile artt. 871, 873, 905-906;
- alla normativa CAM Edilizia 2025 (DM 23/06/2022) ove applicabile a materiali utilizzati.

### H · Allegati

Documenti allegati alla presente CILA:

1. ☑ **Elaborati grafici stato attuale** (pianta, sezioni, prospetti) scala 1:50
2. ☑ **Elaborati grafici stato di progetto** (pianta, sezioni, prospetti) scala 1:50
3. ☑ **Elaborati grafici stato sovrapposto** (rosso/giallo) scala 1:50
4. ☑ **Documentazione fotografica** (interno + esterno + dettagli)
5. ☑ **Visura catastale** aggiornata
6. ☑ **Relazione tecnica illustrativa**
7. ☑ **Relazione paesaggistica semplificata** (se applicabile)
8. ☑ **Asseverazione strutturale** (anche se intervento non strutturale, dichiarazione)
9. ☑ **Documentazione conformità impianti**
10. ☑ **Computo metrico estimativo dei lavori**
11. ☑ Procura del condominio (se richiesta dal regolamento)
12. ☑ **Nulla osta condominio** (Art. 1117 e regolamento di condominio)

### I · Bonus fiscali richiesti

[ ] Bonus Ristrutturazione (art. 16-bis TUIR, DPR 917/86): {{bonus_ristr_aliquota}}%
[ ] Ecobonus (art. 14 DL 63/2013): {{bonus_eco_aliquota}}%
[ ] Sismabonus (art. 16 DL 63/2013): non applicabile (non strutturale)
[ ] Bonus Mobili (art. 16 DL 63/2013, c. 2): {{bonus_mobili}}%

### J · Importo lavori

Importo totale lavori: **€ {{importo_lavori}}** (IVA 10% inclusa, art. 7 DPR 633/72)

### K · Firme

**Comune di Milano · Sportello Unico per l'Edilizia**
Pratica protocollata il: ___ / ___ / 2026
Numero protocollo: ___________

**Il committente:**
{{cliente_nome}} {{cliente_cognome}}
Firma digitale qualificata: __________________________
Data firma: ___ / ___ / 2026

**Il tecnico abilitato:**
{{architetto_nome}} {{architetto_cognome}}
Firma digitale qualificata + timbro Ordine: __________________________
Data firma: ___ / ___ / 2026

---

> **Note:**
> - La presente CILA è auto-asseverativa: i lavori possono iniziare contestualmente alla protocollazione.
> - Il Comune si riserva 30 giorni per controlli di conformità (DPR 380 art. 6-bis c. 4).
> - Eventuali variazioni in corso d'opera richiedono CILA in variante.
> - Il documento deve essere firmato digitalmente con certificato qualificato (eIDAS QES).
