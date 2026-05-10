#!/usr/bin/env python3
"""Architect Profile Loader.

Consolidates all platform data about the architect/professional into a single dict.
Pulls from: profiles, user_settings, brand_profiles, style_profiles, avatars, user_tax_settings.

Italian-specific professional credentials (OAPPC, matricola, PEC) are loaded from:
1. Environment variables (ARCH_OAPPC_ORDINE, ARCH_MATRICOLA, ARCH_PEC, ARCH_ALBO)
2. data/sample-input/architetto-info.json (fallback)
3. Hardcoded placeholders (last resort, with WARN)

Usage:
    from architect_profile import load_architect_profile
    profile = load_architect_profile(client, user_id)
    print(profile["full_name"], profile["company_name"], profile["fiscal_address"])
"""
from __future__ import annotations
import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

ROOT = Path(__file__).resolve().parents[1]


def _safe_get(client, table: str, user_id: str, select: str = "*") -> Optional[Dict[str, Any]]:
    """GET single row · returns None if not found."""
    try:
        result = client._rest("GET", f"/rest/v1/{table}?user_id=eq.{user_id}&select={select}&limit=1")
        if isinstance(result, list) and result:
            return result[0]
        return None
    except Exception as e:
        print(f"  ⚠ failed to load {table}: {e}", file=sys.stderr)
        return None


def _safe_get_by_id(client, table: str, row_id: str, select: str = "*") -> Optional[Dict[str, Any]]:
    """GET by id · returns None if not found."""
    try:
        result = client._rest("GET", f"/rest/v1/{table}?id=eq.{row_id}&select={select}&limit=1")
        if isinstance(result, list) and result:
            return result[0]
        return None
    except Exception:
        return None


def _load_italian_credentials() -> Dict[str, str]:
    """Load Italian-specific credentials from env vars or sample-input JSON.

    Required fields for Italian arch deliverables:
    - ordine_professionale (e.g., "OAPPC Milano")
    - matricola (license number)
    - pec (certified email)
    - albo (e.g., "Arch. Sez. A")
    """
    # Try env vars first
    creds = {
        "ordine_professionale": os.environ.get("ARCH_OAPPC_ORDINE", ""),
        "matricola": os.environ.get("ARCH_MATRICOLA", ""),
        "pec": os.environ.get("ARCH_PEC", ""),
        "albo": os.environ.get("ARCH_ALBO", ""),
    }
    if all(creds.values()):
        return creds

    # Try sample-input JSON
    sample_path = ROOT / "data" / "sample-input" / "architetto-info.json"
    if sample_path.exists():
        try:
            with open(sample_path) as f:
                data = json.load(f)
            for k in creds:
                if not creds[k] and data.get(k):
                    creds[k] = data[k]
        except Exception as e:
            print(f"  ⚠ failed to read {sample_path}: {e}", file=sys.stderr)

    # Fallback placeholders with WARN
    if not creds["ordine_professionale"]:
        print(f"  ⚠ ARCH_OAPPC_ORDINE not configured · using placeholder", file=sys.stderr)
        creds["ordine_professionale"] = "OAPPC Milano"
    if not creds["matricola"]:
        print(f"  ⚠ ARCH_MATRICOLA not configured · using placeholder", file=sys.stderr)
        creds["matricola"] = "XXXX"
    if not creds["pec"]:
        creds["pec"] = "[da configurare]@archiworldpec.it"
    if not creds["albo"]:
        creds["albo"] = "Arch. Sez. A"

    return creds


def load_architect_profile(client, user_id: str) -> Dict[str, Any]:
    """Load complete architect profile from all platform tables.

    Returns dict with structure:
    {
      user_id, email, full_name, first_name, last_name,
      phone, instagram, position, subscription_status,
      company_name, company_size,
      fiscal: {country, city, region, postal_code, street, province, tax_id, tax_id_type},
      currency, preferred_language,
      brand: {name, mission, vision, values, promise, palette, fonts, logo_url, favicon_url, tone_of_voice},
      style: {style_name, keywords, palette, materials, strengths, weaknesses},
      avatar: {name, summary, demographic_profile, lifestyle_preferences, motivations_goals},
      tax_settings: {tax_rate, tax_regime, tax_rate_imposta, tax_rate_inps, tax_rate_irap, profitability_coefficient},
      italian_credentials: {ordine_professionale, matricola, pec, albo},
    }
    """
    profile = {"user_id": user_id}

    # === profiles ===
    p = _safe_get(client, "profiles", user_id) or {}
    # profiles uses id not user_id · try by id
    if not p:
        p = _safe_get_by_id(client, "profiles", user_id) or {}
    profile["email"] = p.get("email", "")
    profile["full_name"] = p.get("full_name", "")
    profile["phone"] = p.get("phone", "")
    profile["instagram"] = p.get("instagram_handle", "")
    profile["position"] = p.get("position", "")
    profile["subscription_status"] = p.get("subscription_status", "")
    profile["is_admin"] = p.get("is_admin", False)

    # === user_settings (fiscal info) ===
    s = _safe_get(client, "user_settings", user_id) or {}
    profile["first_name"] = s.get("first_name", "") or profile.get("full_name", "")
    profile["last_name"] = s.get("last_name", "")
    full_name_combined = f"{profile['first_name']} {profile['last_name']}".strip()
    if full_name_combined:
        profile["full_name"] = full_name_combined
    profile["company_name"] = s.get("company_name", "") or p.get("company", "")
    profile["company_size"] = s.get("company_size", "")
    profile["professional_role"] = s.get("professional_role", "")
    profile["preferred_language"] = s.get("preferred_language", "it")
    profile["currency"] = s.get("currency", "EUR")
    profile["fiscal"] = {
        "country": s.get("fiscal_address_country") or s.get("country", ""),
        "city": s.get("fiscal_address_city") or s.get("city", ""),
        "region": s.get("region", ""),
        "postal_code": s.get("fiscal_address_postal_code", ""),
        "street": s.get("fiscal_address_street", ""),
        "province": s.get("fiscal_address_province", ""),
        "tax_id": s.get("tax_id", ""),
        "tax_id_type": s.get("tax_id_type", ""),
        "fiscal_country_code": s.get("fiscal_country", ""),
        "fiscal_regime": s.get("fiscal_regime", ""),
    }

    # === brand_profiles ===
    b = _safe_get(client, "brand_profiles", user_id) or {}
    profile["brand"] = {
        "name": b.get("name", "") or profile.get("company_name", ""),
        "mission": b.get("mission", ""),
        "vision": b.get("vision", ""),
        "values": b.get("values", ""),
        "promise": b.get("promise", ""),
        "tone_of_voice": b.get("tone_of_voice", ""),
        "palette": b.get("palette", []),
        "fonts": b.get("fonts", {}),
        "logo_url": b.get("logo_url", ""),
        "favicon_url": b.get("favicon_url", ""),
        "keywords": b.get("keywords", []),
    }

    # === style_profiles ===
    st = _safe_get(client, "style_profiles", user_id) or {}
    profile["style"] = {
        "style_name": st.get("style_name", ""),
        "keywords": st.get("keywords", []),
        "palette": st.get("palette", []),
        "materials": st.get("materials", []),
        "strengths": st.get("strengths", []),
        "weaknesses": st.get("weaknesses", []),
        "summary": st.get("summary", ""),
    }

    # === avatars (target cliente persona) ===
    av = _safe_get(client, "avatars", user_id) or {}
    profile["avatar"] = {
        "name": av.get("name", ""),
        "summary": av.get("summary", ""),
        "demographic_profile": av.get("demographic_profile", {}),
        "lifestyle_preferences": av.get("lifestyle_preferences", {}),
        "motivations_goals": av.get("motivations_goals", {}),
        "barriers_objections": av.get("barriers_objections", {}),
    }

    # === user_tax_settings ===
    tx = _safe_get(client, "user_tax_settings", user_id) or {}
    profile["tax_settings"] = {
        "tax_rate": tx.get("tax_rate", 22),
        "tax_regime": tx.get("tax_regime", "manual"),
        "tax_rate_imposta": tx.get("tax_rate_imposta", 25),
        "tax_rate_inps": tx.get("tax_rate_inps", 4),
        "tax_rate_irap": tx.get("tax_rate_irap", 0),
        "profitability_coefficient": tx.get("profitability_coefficient", 78),
    }

    # === Italian professional credentials (env or JSON) ===
    profile["italian_credentials"] = _load_italian_credentials()

    return profile


def format_address(fiscal: Dict[str, str]) -> str:
    """Format fiscal address as readable string."""
    parts = []
    if fiscal.get("street"):
        parts.append(fiscal["street"])
    city_zip = ""
    if fiscal.get("postal_code"):
        city_zip = fiscal["postal_code"]
    if fiscal.get("city"):
        city_zip = f"{city_zip} {fiscal['city']}".strip()
    if fiscal.get("province"):
        city_zip = f"{city_zip} ({fiscal['province']})".strip()
    if city_zip:
        parts.append(city_zip)
    if fiscal.get("country"):
        parts.append(fiscal["country"])
    return ", ".join(parts) if parts else "[indirizzo da configurare]"


def format_tax_id(fiscal: Dict[str, str]) -> str:
    """Format tax_id with country prefix."""
    tax_id = fiscal.get("tax_id", "")
    tid_type = fiscal.get("tax_id_type", "")
    if not tax_id:
        return "[P.IVA da configurare]"
    if tid_type.startswith("vat_"):
        country = tid_type.replace("vat_", "").upper()
        return f"P.IVA {country} {tax_id}"
    return f"P.IVA {tax_id}"


def format_architect_signature(profile: Dict[str, Any]) -> str:
    """Format full architect signature line for documents.

    Example: "Pablo Ruan · architetto · OAPPC Milano n. matr. 12345 · ArchPrime · Lambeth (GB)"
    """
    parts = []
    if profile.get("full_name"):
        parts.append(profile["full_name"])
    parts.append("architetto")
    creds = profile.get("italian_credentials", {})
    if creds.get("ordine_professionale") and creds.get("matricola"):
        parts.append(f"{creds['ordine_professionale']} n. matr. {creds['matricola']}")
    if profile.get("company_name"):
        parts.append(profile["company_name"])
    fiscal = profile.get("fiscal", {})
    if fiscal.get("city"):
        loc = fiscal["city"]
        if fiscal.get("country"):
            loc = f"{loc} ({fiscal['country']})"
        parts.append(loc)
    return " · ".join(parts)


# ----------------------------------------------------------------------------
# CLI test
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    from lovarch_client import LovarchClient
    client = LovarchClient()
    user_id = sys.argv[1] if len(sys.argv) > 1 else "a5f3ee03-a7df-4571-a68d-baf168bd4ba8"
    profile = load_architect_profile(client, user_id)
    print(json.dumps(profile, indent=2, ensure_ascii=False))
    print("\n=== Formatted ===")
    print(f"Signature: {format_architect_signature(profile)}")
    print(f"Address:   {format_address(profile['fiscal'])}")
    print(f"Tax ID:    {format_tax_id(profile['fiscal'])}")
