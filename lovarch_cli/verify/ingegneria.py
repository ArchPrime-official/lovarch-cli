"""Adversarial verifiers for the engineer ICP: strutturale (NTC 2018),
antincendio (DM 03/08/2015), acustica (DPCM 5/12/1997), energetica (L.10/APE).

Each is a thin config over run_adversarial (Sonnet extract → Opus refute). ADVISORY:
the signed calculation/report and responsibility stay with the licensed engineer.
"""
from __future__ import annotations

from typing import Any

from lovarch_cli.verify._adversarial import AdversarialReport, run_adversarial, _REFUTE_TAIL

# ── Strutturale · NTC 2018 (DM 17/01/2018) ────────────────────────────────────
_STRUT_REQ = [
    "zona sismica e categoria sottosuolo", "classe d'uso e vita nominale",
    "elementi strutturali interessati (muri portanti/architravi/cordoli/solai)",
    "verifiche SLU/SLE e sismica", "deposito sismico / autorizzazione art. 93-94 DPR 380",
    "relazione di calcolo e collaudo",
]
_STRUT_EXTRACT = (
    "Sei un assistente per verifiche strutturali (NTC 2018, Circolare 7/2019). "
    "Estrai dalla relazione/progetto: inquadramento sismico (zona, sottosuolo, "
    "classe d'uso, vita nominale), interventi strutturali descritti, verifiche "
    "dichiarate, documenti citati. Rispondi SOLO con JSON valido: "
    '{"inquadramento": {"zona_sismica": "...|null", "sottosuolo": "...|null", '
    '"classe_uso": "...|null"}, "interventi": ["..."], "verifiche_dichiarate": '
    '["..."], "documenti": ["..."], "note": ["..."]}'
)
_STRUT_REFUTE = (
    "Sei un verificatore ADVERSARIALE strutturale (NTC 2018). Controlla che: "
    "l'inquadramento sismico sia presente e coerente; gli interventi su elementi "
    "portanti (aperture, demolizioni) abbiano le verifiche SLU/SLE e sismiche "
    "richieste; sia previsto il deposito sismico/autorizzazione ex art. 93-94 DPR "
    "380 e il collaudo. NON validare calcoli né dare dimensionamenti: segnala solo "
    "lacune e incoerenze (il calcolo è dell'ingegnere abilitato)." + _REFUTE_TAIL
)

# ── Antincendio · DM 03/08/2015 (Codice PI) + DPR 151/2011 ────────────────────
_FIRE_REQ = [
    "attività soggette (DPR 151/2011) e categoria A/B/C", "carico d'incendio e compartimentazione",
    "vie di esodo e lunghezza massima", "reazione/resistenza al fuoco (REI)",
    "impianti di rivelazione/spegnimento", "SCIA antincendio / valutazione progetto",
]
_FIRE_EXTRACT = (
    "Sei un assistente antincendio (DM 03/08/2015 Codice di prevenzione incendi, "
    "DPR 151/2011). Estrai: se l'attività è soggetta e la categoria, misure "
    "descritte (compartimentazione, esodo, reazione/resistenza al fuoco, impianti), "
    "adempimenti citati. Rispondi SOLO con JSON valido: {\"soggetta\": true|false|"
    'null, "categoria": "A|B|C|null", "misure_presenti": ["..."], '
    '"misure_mancanti": ["..."], "adempimenti": ["..."], "note": ["..."]}'
)
_FIRE_REFUTE = (
    "Sei un verificatore ADVERSARIALE antincendio (DM 03/08/2015). Controlla: se "
    "l'attività è soggetta a controllo VV.F. (DPR 151/2011) e se sono definiti "
    "compartimentazione, vie di esodo (lunghezze), reazione/resistenza al fuoco "
    "(classi REI), impianti di rivelazione/spegnimento, e la SCIA/valutazione "
    "progetto. Segnala lacune critiche." + _REFUTE_TAIL
)

# ── Acustica · DPCM 5/12/1997 (requisiti acustici passivi) ─────────────────────
_ACU_REQ = [
    "categoria dell'edificio (A-G)", "isolamento acustico di facciata D2m,nT,w",
    "potere fonoisolante tra unità R'w", "rumore di calpestio L'n,w",
    "rumorosità impianti (LASmax/LAeq)", "relazione acustica / collaudo in opera",
]
_ACU_EXTRACT = (
    "Sei un assistente di acustica edilizia (DPCM 5/12/1997, requisiti acustici "
    "passivi). Estrai dalla relazione i valori dichiarati e la categoria "
    "dell'edificio. Rispondi SOLO con JSON valido: {\"categoria\": \"...|null\", "
    '"D2m_nT_w": "...|null", "R_w": "...|null", "L_n_w": "...|null", '
    '"impianti": "...|null", "note": ["..."]}'
)
_ACU_REFUTE = (
    "Sei un verificatore ADVERSARIALE acustico (DPCM 5/12/1997). Controlla i "
    "valori dichiarati contro i limiti per la categoria: es. residenza (cat. A) "
    "→ D2m,nT,w ≥ 40 dB, R'w ≥ 50 dB, L'n,w ≤ 63 dB, impianti a funzionamento "
    "continuo LAeq ≤ 35 dB. Segnala valori sotto soglia o mancanti." + _REFUTE_TAIL
)

# ── Energetica · D.Lgs 192/2005 + DM 26/06/2015 + L.10 ────────────────────────
_ENE_REQ = [
    "zona climatica e gradi giorno", "trasmittanze U (pareti/copertura/serramenti) vs limiti",
    "quota obbligatoria di fonti rinnovabili (D.Lgs 199/2021)", "ponti termici",
    "classe APE stimata", "relazione ex L.10 e APE a fine lavori",
]
_ENE_EXTRACT = (
    "Sei un assistente di prestazione energetica (D.Lgs 192/2005, DM 26/06/2015, "
    "L.10/1991). Estrai: zona climatica, trasmittanze dichiarate, quota FER, classe "
    "APE, documenti. Rispondi SOLO con JSON valido: {\"zona_climatica\": \"...|null\", "
    '"trasmittanze": {"pareti": "...|null", "serramenti": "...|null"}, "FER": '
    '"...|null", "classe_APE": "...|null", "documenti": ["..."], "note": ["..."]}'
)
_ENE_REFUTE = (
    "Sei un verificatore ADVERSARIALE energetico (DM 26/06/2015 requisiti minimi). "
    "Controlla che le trasmittanze U rispettino i limiti della zona climatica, che "
    "sia rispettata la quota obbligatoria di fonti rinnovabili (D.Lgs 199/2021), e "
    "che siano previsti relazione ex L.10 e APE. Segnala superamenti dei limiti e "
    "documenti mancanti." + _REFUTE_TAIL
)


async def verify_strutturale(gateway: Any, path: str, *, language: str = "it") -> AdversarialReport:
    return await run_adversarial(gateway, path, extract_system=_STRUT_EXTRACT,
        refute_system=_STRUT_REFUTE, required=_STRUT_REQ, op_prefix="verify:strutturale",
        doc_label="RELAZIONE / PROGETTO STRUTTURALE", language=language)


async def verify_antincendio(gateway: Any, path: str, *, language: str = "it") -> AdversarialReport:
    return await run_adversarial(gateway, path, extract_system=_FIRE_EXTRACT,
        refute_system=_FIRE_REFUTE, required=_FIRE_REQ, op_prefix="verify:antincendio",
        doc_label="PROGETTO ANTINCENDIO", language=language)


async def verify_acustica(gateway: Any, path: str, *, language: str = "it") -> AdversarialReport:
    return await run_adversarial(gateway, path, extract_system=_ACU_EXTRACT,
        refute_system=_ACU_REFUTE, required=_ACU_REQ, op_prefix="verify:acustica",
        doc_label="RELAZIONE ACUSTICA", language=language)


async def verify_energetica(gateway: Any, path: str, *, language: str = "it") -> AdversarialReport:
    return await run_adversarial(gateway, path, extract_system=_ENE_EXTRACT,
        refute_system=_ENE_REFUTE, required=_ENE_REQ, op_prefix="verify:energetica",
        doc_label="RELAZIONE ENERGETICA / L.10", language=language)
