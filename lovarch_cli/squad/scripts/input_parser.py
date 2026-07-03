"""input_parser — dados REAIS do projeto a partir do --input-dir.

Fim do demo hardcoded "Attico Brera / Marco Rossini": o runner passa a montar
client_data / project_data / finance_config a partir do input do usuário, com
três fontes em ordem de prioridade:

  1. `dati-progetto.yaml` no input-dir — explícito e determinístico (grátis).
  2. Extração via LLM do `briefing-cliente.md` — modo premium (usa a EF
     cli-ai-text, role executor, JSON estrito; debita créditos do usuário).
  3. Fallback demo (Attico Brera) com AVISO explícito no terminal — mantém a
     compatibilidade do sample e do dry-run.

Formato do dati-progetto.yaml (todas as chaves opcionais):

    cliente:
      nome: "Marco Bianchi"
      email: "marco@example.com"
      telefono: "+39 333 000 0000"
      citta: "Milano"
      regione: "Lombardia"
    progetto:
      nome: "Appartamento Navigli"
      indirizzo: "Via Vigevano 8, 20144 Milano"
      tipologia: "ristrutturazione"
      superficie_mq: 95
      budget_min: 120000
      budget_max: 140000
      onorari: 16000
      percentuale_onorari: 12.0
      consegna: "2026-12-15"
      obiettivi: "..."
      stile: "..."
      vincoli: "..."
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


# Demo defaults — the historical sample. Used ONLY as last resort, with a
# loud warning, so `lovarch init --sample` and free dry-runs keep working.
DEMO_CLIENT = {
    "name": "Marco Rossini",
    "email": "marco.rossini@studiorossinibianchi.it",
    "phone": "+39 333 123 4567",
    "city": "Milano",
    "region": "Lombardia",
}
DEMO_PROJECT = {
    "name": "Attico Brera",
    "address": "Via Fiori Chiari 17, 20121 Milano",
    "typology": "ristrutturazione",
    "square_meters": 120,
    "brief_objectives": "Ristrutturazione integrale attico 3° piano · open-space + studio + 2 camere + 2 bagni · 90gg",
    "brief_style": "Wabi-sabi neoclassico · materiali naturali · NO total white",
    "constraints": "Zona A1 NAF · facciata vincolata · soffitti decorati · seminato veneziano",
    "budget_min": 165000,
    "budget_max": 180000,
    "professional_fee_percent": 12.2,
    "delivery_date": "2026-10-31",
}
DEMO_FINANCE = {
    "onorari_total": 22000,
    "start_date": "2026-04-25",
    "sal_breakdown": [("SAL 1 · firma", 0.15), ("SAL 2 · CILA", 0.25),
                      ("SAL 3 · 50% lavori", 0.25), ("SAL 4 · consegna", 0.35)],
}

_EXTRACT_SYSTEM = (
    "Sei un assistente che estrae dati strutturati dal briefing di un progetto "
    "di architettura italiano. Estrai SOLO ciò che è presente nel testo; usa "
    "null per i campi assenti. Rispondi SOLO con JSON valido: "
    '{"cliente": {"nome": null, "email": null, "telefono": null, "citta": null, '
    '"regione": null}, "progetto": {"nome": null, "indirizzo": null, '
    '"tipologia": null, "superficie_mq": null, "budget_min": null, '
    '"budget_max": null, "onorari": null, "consegna": null, "obiettivi": null, '
    '"stile": null, "vincoli": null}}'
)


@dataclass
class ProjectInput:
    client_data: Dict[str, Any]
    project_data: Dict[str, Any]
    finance_config: Dict[str, Any]
    source: str = "demo"            # "yaml" | "llm" | "demo"
    warnings: list = field(default_factory=list)


def _gateway_extract(briefing_text: str) -> Optional[Dict[str, Any]]:
    """Premium: extract structured data from the brief via cli-ai-text
    (executor role — debits the user's credits by real tokens)."""
    token = os.environ.get("LOVARCH_ACCESS_TOKEN")
    if not token:
        return None
    api_url = os.environ.get("LOVARCH_API_URL", "https://cuxbydmyahjaplzkthkr.supabase.co").rstrip("/")
    anon = os.environ.get("LOVARCH_ANON_KEY", "")
    body = json.dumps({
        "role": "executor",
        "system": _EXTRACT_SYSTEM,
        "prompt": f"BRIEFING:\n\n{briefing_text[:40000]}",
        "max_tokens": 1200,
        "operation_type": "cli:input_parser",
    }).encode()
    req = urllib.request.Request(f"{api_url}/functions/v1/cli-ai-text", data=body, method="POST")
    req.add_header("apikey", anon)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return None
    if not data.get("ok"):
        return None
    raw = str(data.get("text", "")).strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.S)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _merge_extracted(extracted: Dict[str, Any]) -> ProjectInput:
    """Build ProjectInput from a yaml/LLM dict, demo-filling missing fields."""
    cli = extracted.get("cliente") or {}
    prj = extracted.get("progetto") or {}
    warnings: list = []

    def pick(val, demo_val, label):
        if val is None or val == "" or val == []:
            warnings.append(f"campo '{label}' assente nell'input — uso il default")
            return demo_val
        return val

    client_data = {
        "name": pick(cli.get("nome"), DEMO_CLIENT["name"], "cliente.nome"),
        "email": cli.get("email") or DEMO_CLIENT["email"],
        "phone": cli.get("telefono") or DEMO_CLIENT["phone"],
        "city": cli.get("citta") or DEMO_CLIENT["city"],
        "region": cli.get("regione") or DEMO_CLIENT["region"],
    }
    sqm = prj.get("superficie_mq")
    budget_max = prj.get("budget_max") or prj.get("budget")
    project_data = {
        "name": pick(prj.get("nome"), DEMO_PROJECT["name"], "progetto.nome"),
        "address": pick(prj.get("indirizzo"), DEMO_PROJECT["address"], "progetto.indirizzo"),
        "typology": prj.get("tipologia") or DEMO_PROJECT["typology"],
        "square_meters": int(sqm) if sqm else DEMO_PROJECT["square_meters"],
        "brief_objectives": prj.get("obiettivi") or DEMO_PROJECT["brief_objectives"],
        "brief_style": prj.get("stile") or DEMO_PROJECT["brief_style"],
        "constraints": prj.get("vincoli") or DEMO_PROJECT["constraints"],
        "budget_min": int(prj.get("budget_min") or (int(budget_max * 0.9) if budget_max else DEMO_PROJECT["budget_min"])),
        "budget_max": int(budget_max or DEMO_PROJECT["budget_max"]),
        "professional_fee_percent": float(prj.get("percentuale_onorari") or DEMO_PROJECT["professional_fee_percent"]),
        "delivery_date": str(prj.get("consegna") or DEMO_PROJECT["delivery_date"]),
    }
    onorari = prj.get("onorari")
    finance_config = dict(DEMO_FINANCE)
    if onorari:
        finance_config = {**DEMO_FINANCE, "onorari_total": int(onorari)}
    return ProjectInput(
        client_data=client_data,
        project_data=project_data,
        finance_config=finance_config,
        warnings=warnings,
    )


def parse_project_input(input_dir: str | Path) -> ProjectInput:
    """Resolve the project data for a run. Priority:
    dati-progetto.yaml > LLM extraction of briefing (premium) > demo."""
    root = Path(input_dir).expanduser()

    # 1 · explicit yaml
    yaml_path = root / "dati-progetto.yaml"
    if yaml_path.is_file() and yaml is not None:
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            result = _merge_extracted(data)
            result.source = "yaml"
            return result
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️  dati-progetto.yaml non leggibile ({str(exc)[:80]}) — provo il briefing")

    # 2 · LLM extraction from the brief (premium only)
    briefing = root / "briefing-cliente.md"
    if briefing.is_file():
        text = briefing.read_text(encoding="utf-8", errors="ignore")
        if text.strip():
            extracted = _gateway_extract(text)
            if extracted:
                result = _merge_extracted(extracted)
                result.source = "llm"
                return result

    # 3 · demo fallback — loud warning
    result = ProjectInput(
        client_data=dict(DEMO_CLIENT),
        project_data=dict(DEMO_PROJECT),
        finance_config=dict(DEMO_FINANCE),
        source="demo",
        warnings=["ATTENZIONE: nessun dato di progetto trovato (né dati-progetto.yaml "
                  "né briefing estraibile) — uso i dati DEMO 'Attico Brera'."],
    )
    return result
