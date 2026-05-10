"""
API Clients for squad architettura-progetto.

Centralizes all external API calls used by the agents.
Reads secrets from ~/.lovarch/secrets.env (NOT committed to git).

Usage:
    from squads.architettura_progetto.scripts.api_clients import (
        mapbox_geocode,
        catasto_visura,
        firma_qes_create_envelope,
    )

    result = mapbox_geocode("Via Fiori Chiari 17, Milano")
    print(result["lat"], result["lon"], result["comune"])
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote

import urllib.request
import urllib.error


SECRETS_FILE = Path.home() / ".lovarch" / "secrets.env"
MOCKS_DIR = Path(__file__).parent.parent / "data" / "mocks"


def _load_secrets() -> Dict[str, str]:
    """Read ~/.lovarch/secrets.env (KEY=VALUE format)."""
    secrets: Dict[str, str] = {}
    if not SECRETS_FILE.exists():
        return secrets
    for line in SECRETS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            secrets[k.strip()] = v.strip()
    return secrets


_SECRETS = _load_secrets()


# ----------------------------------------------------------------------------
# Mapbox Geocoding · REAL API (P1 critico)
# ----------------------------------------------------------------------------

def mapbox_geocode(
    address: str,
    *,
    country: str = "IT",
    limit: int = 1,
) -> Optional[Dict[str, Any]]:
    """
    Geocoda un indirizzo italiano via Mapbox Geocoding API.

    Returns:
        dict con keys: lat, lon, place_name, comune, postcode, region.
        None se nessun risultato.

    Raises:
        ValueError: se MAPBOX_TOKEN non è configurato.
        urllib.error.HTTPError: se la API ritorna errore.
    """
    token = _SECRETS.get("MAPBOX_TOKEN") or os.environ.get("MAPBOX_TOKEN")
    if not token:
        raise ValueError(
            "MAPBOX_TOKEN missing. Add to ~/.lovarch/secrets.env or env."
        )

    url = (
        f"https://api.mapbox.com/geocoding/v5/mapbox.places/{quote(address)}.json"
        f"?access_token={token}&country={country}&limit={limit}"
    )

    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.load(resp)

    features = data.get("features", [])
    if not features:
        return None

    f = features[0]
    coords = f.get("center", [None, None])

    # Extract context fields (postcode, place=comune, region)
    ctx = {item.get("id", "").split(".")[0]: item for item in f.get("context", [])}

    return {
        "lat": coords[1],
        "lon": coords[0],
        "place_name": f.get("place_name"),
        "comune": ctx.get("place", {}).get("text"),
        "postcode": ctx.get("postcode", {}).get("text"),
        "region": ctx.get("region", {}).get("text"),
        "country": ctx.get("country", {}).get("text"),
        "raw": f,  # full Mapbox feature for advanced use
    }


# ----------------------------------------------------------------------------
# Catasto · MOCK (OpenAPI.com substitute)
# ----------------------------------------------------------------------------

def catasto_visura(
    address: str,
    comune: str,
    *,
    foglio: Optional[str] = None,
    mappale: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Restituisce una visura catastale.

    Implementazione MOCK · per il demo. In produzione: OpenAPI.com Catasto.
    Carica `data/mocks/catasto-visura.json` e sostituisce i campi address/comune
    con i parametri ricevuti per dare l'aspetto di una risposta personalizzata.
    """
    mock_path = MOCKS_DIR / "catasto-visura.json"
    visura = json.loads(mock_path.read_text(encoding="utf-8"))

    visura["request"]["indirizzo"] = address
    visura["request"]["comune"] = comune
    if foglio:
        visura["dati_catastali"]["foglio"] = foglio
    if mappale:
        visura["dati_catastali"]["mappale"] = mappale

    visura["meta"]["mock"] = True
    return visura


# ----------------------------------------------------------------------------
# Firma Digitale QES · MOCK (Yousign / OpenAPI.com firma substitute)
# ----------------------------------------------------------------------------

def firma_qes_create_envelope(
    *,
    document_path: str,
    signer_name: str,
    signer_email: str,
    signer_cf: str,
    document_title: str = "Documento da firmare",
) -> Dict[str, Any]:
    """
    Crea un envelope di firma digitale qualificata (eIDAS).

    Implementazione MOCK · per il demo. In produzione: Yousign API o OpenAPI.com firma.
    Restituisce un URL di firma simulato che il cliente cliccherebbe.
    """
    mock_path = MOCKS_DIR / "firma-envelope.json"
    envelope = json.loads(mock_path.read_text(encoding="utf-8"))

    envelope["envelope"]["document_path"] = document_path
    envelope["envelope"]["document_title"] = document_title
    envelope["envelope"]["signer"]["name"] = signer_name
    envelope["envelope"]["signer"]["email"] = signer_email
    envelope["envelope"]["signer"]["codice_fiscale"] = signer_cf
    envelope["meta"]["mock"] = True
    return envelope


# ----------------------------------------------------------------------------
# CLI test
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python api_clients.py <command> [args]")
        print("Commands:")
        print("  geocode <address>          — Mapbox real API")
        print("  catasto <address> <comune> — Catasto mock")
        print("  firma <doc_path> <name> <email> <cf>  — Firma QES mock")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "geocode":
        addr = " ".join(sys.argv[2:])
        result = mapbox_geocode(addr)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "catasto":
        addr = sys.argv[2]
        comune = sys.argv[3]
        result = catasto_visura(addr, comune)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "firma":
        doc, name, email, cf = sys.argv[2:6]
        result = firma_qes_create_envelope(
            document_path=doc, signer_name=name,
            signer_email=email, signer_cf=cf,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
