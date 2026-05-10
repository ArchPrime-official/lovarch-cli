"""
Simulate Squad Architettura-Progetto execution by inserting realistic steps
into Supabase tables progressively.

Use cases:
  1. Test the /admin/squad-execution/:id/live page (Realtime)
  2. Backup demo if real squad execution fails on stage
  3. Demo previews / dev iteration

Usage:
    # 1. Set env vars or write secrets in ~/.lovarch/secrets.env:
    #    SUPABASE_URL=https://xxx.supabase.co
    #    SUPABASE_SERVICE_ROLE_KEY=eyJ...
    #
    # 2. Run:
    python3 simulate_squad_execution.py
    python3 simulate_squad_execution.py --speed 2.0   # 2x faster
    python3 simulate_squad_execution.py --user-id <uuid>
    python3 simulate_squad_execution.py --dry-run

The simulator creates 1 execution + ~30 steps + ~20 QA checks across 14 minutes
(or compressed by --speed factor). It mimics the dal-brief-al-cantiere workflow
including 1 deliberate QA REJECT + retry to demonstrate the loop.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


SECRETS_FILE = Path.home() / ".lovarch" / "secrets.env"


def load_secrets() -> Dict[str, str]:
    secrets: Dict[str, str] = {}
    if SECRETS_FILE.exists():
        for line in SECRETS_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            secrets[k.strip()] = v.strip()
    return secrets


_SECRETS = load_secrets()


def get_env(name: str, fallback: Optional[str] = None) -> Optional[str]:
    return os.environ.get(name) or _SECRETS.get(name) or fallback


SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_KEY = get_env("SUPABASE_SERVICE_ROLE_KEY") or get_env("SUPABASE_SERVICE_KEY")


# ----------------------------------------------------------------------------
# Supabase REST client (no SDK · stdlib only)
# ----------------------------------------------------------------------------

class SupabaseRest:
    def __init__(self, url: str, key: str):
        self.url = url.rstrip("/")
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def insert(self, table: str, row: dict) -> dict:
        return self._req("POST", f"/rest/v1/{table}", body=row)

    def update(self, table: str, where: str, patch: dict) -> dict:
        return self._req("PATCH", f"/rest/v1/{table}?{where}", body=patch)

    def select(self, table: str, where: str = "select=*") -> list:
        result = self._req("GET", f"/rest/v1/{table}?{where}")
        return result if isinstance(result, list) else [result]

    def _req(self, method: str, path: str, body: Optional[dict] = None) -> Any:
        url = f"{self.url}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read().decode("utf-8") or "[]"
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Supabase {method} {path} failed [{e.code}]: {err}") from e


# ----------------------------------------------------------------------------
# Step definitions · simulating the workflow
# ----------------------------------------------------------------------------

@dataclass
class StepDef:
    agent: str
    tier: int
    step_type: str
    duration: float
    action: str
    output_files: List[Dict[str, Any]] = field(default_factory=list)
    qa_outcome: Optional[str] = None  # "PASS" | "REJECT"
    qa_checks: List[Dict[str, Any]] = field(default_factory=list)


def _file(name: str, path: str, size_kb: int, mime: str = "application/pdf") -> dict:
    return {
        "name": name,
        "path": path,
        "size": size_kb * 1024,
        "mime": mime,
    }


# Workflow simulation · 28 steps + 1 QA REJECT + retry
WORKFLOW: List[StepDef] = [
    # TIER 0 · ORCHESTRAZIONE
    StepDef("@progetto-chief", 0, "orchestration", 4, "init: caricato briefing-cliente.md (1.4k parole)"),
    StepDef("@auditor-input", 0, "orchestration", 12, "validazione 18 items input · PASS",
            output_files=[_file("input_validation.json", "00-validation/", 2, "application/json")]),

    # TIER 1 · ESECUZIONE PARALLELA
    StepDef("@briefing-architect", 1, "execution", 28, "brief strutturato 12 sezioni UNI 11337",
            output_files=[
                _file("brief-strutturato.pdf", "01-briefing/", 412),
                _file("requisiti.json", "01-briefing/", 4, "application/json"),
                _file("programma-spaziale.xlsx", "01-briefing/", 22, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ]),
    StepDef("@regolatorio-it", 1, "execution", 38, "tipo pratica = CILA · paesaggistica DPR 31/2017 procedura semplificata",
            output_files=[
                _file("analisi-regolamentare.pdf", "01-briefing/", 624),
                _file("tipo-pratica.json", "01-briefing/", 3, "application/json"),
                _file("vincoli.json", "01-briefing/", 2, "application/json"),
            ]),
    StepDef("@cad-engineer", 1, "execution", 95, "pianta-progetto.dxf · 8 ambienti · cotazioni UNI ISO 5457",
            output_files=[
                _file("pianta-stato-attuale.dxf", "03-progetto-definitivo/", 78, "application/dxf"),
                _file("pianta-stato-attuale.pdf", "03-progetto-definitivo/", 312),
                _file("pianta-progetto.dxf", "03-progetto-definitivo/", 96, "application/dxf"),
                _file("pianta-progetto.pdf", "03-progetto-definitivo/", 387),
                _file("sezione-AA.pdf", "03-progetto-definitivo/", 218),
                _file("prospetti.pdf", "03-progetto-definitivo/", 442),
                _file("schema-quotato.json", "03-progetto-definitivo/", 5, "application/json"),
            ]),
    StepDef("@bim-engineer", 1, "execution", 78, "modello.ifc LOD 300 · viewer APS embeddable",
            output_files=[
                _file("modello.ifc", "03-progetto-definitivo/", 1834, "application/x-step"),
                _file("thumbnail-3d.png", "03-progetto-definitivo/", 412, "image/png"),
                _file("quantitativi.json", "03-progetto-definitivo/", 8, "application/json"),
            ]),
    StepDef("@concept-designer", 1, "execution", 168,
            "moodboard 9 immagini + 6 render FLUX 1.1 Pro + palette + tipografia",
            output_files=[
                _file("moodboard.pdf", "02-concept/", 8420),
                _file("living-moderno-a.png", "02-concept/renders/", 4280, "image/png"),
                _file("living-moderno-b.png", "02-concept/renders/", 4156, "image/png"),
                _file("cucina-moderna-a.png", "02-concept/renders/", 4350, "image/png"),
                _file("cucina-moderna-b.png", "02-concept/renders/", 4120, "image/png"),
                _file("camera-sofia-a.png", "02-concept/renders/", 3980, "image/png"),
                _file("camera-sofia-b.png", "02-concept/renders/", 4042, "image/png"),
                _file("palette-progetto.pdf", "02-concept/", 187),
                _file("tipografia.pdf", "02-concept/", 142),
            ]),
    StepDef("@computo-engineer", 1, "execution", 52,
            "computo metrico estimativo · 124 voci Prezzario Lombardia · totale €180.000",
            output_files=[
                _file("computo-metrico.xlsx", "05-impresa/", 240, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                _file("computo-metrico.pdf", "05-impresa/", 524),
                _file("quadro-economico.pdf", "05-impresa/", 142),
                _file("lista-materiali-EPDs.xlsx", "05-impresa/", 98, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ]),
    StepDef("@capitolato-writer", 1, "execution", 78,
            "capitolato speciale 78 pp · UNI 11337-7 + CAM 2025 · cronoprogramma 90gg",
            output_files=[
                _file("capitolato-speciale.pdf", "05-impresa/", 3420),
                _file("cronoprogramma-90gg.pdf", "05-impresa/", 412),
                _file("lista-CAM-rispettati.xlsx", "05-impresa/", 76, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ]),
    StepDef("@pratiche-it", 1, "execution", 42,
            "CILA precompilata + asseverazione + paesaggistica + 6 elaborati",
            output_files=[
                _file("CILA-precompilata.pdf", "04-pratiche-comune/", 512),
                _file("asseverazione-bozza.pdf", "04-pratiche-comune/", 189),
                _file("paesaggistica-bozza.pdf", "04-pratiche-comune/", 734),
                _file("relazione-paesaggistica.pdf", "04-pratiche-comune/", 412),
                _file("documentazione-fotografica.pdf", "04-pratiche-comune/", 12340),
            ]),
    StepDef("@contratto-architect", 1, "execution", 22,
            "contratto CNAPPC + preventivo + privacy GDPR · onorari €22.000",
            output_files=[
                _file("contratto-servizi.pdf", "07-cliente/", 412),
                _file("preventivo-onorari.pdf", "07-cliente/", 298),
                _file("informativa-privacy-GDPR.pdf", "07-cliente/", 156),
            ]),
    StepDef("@energy-prelim", 1, "execution", 36,
            "APE preliminare · classe stimata B → A · LCA embodied carbon",
            output_files=[
                _file("APE-stima-preliminare.pdf", "06-ingegneri/", 682),
                _file("LCA-embodied-carbon.pdf", "06-ingegneri/", 934),
                _file("trasmittanze-pareti.xlsx", "06-ingegneri/", 42, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ]),
    StepDef("@deliverable-builder", 1, "execution", 32,
            "presentazione HTML V8 + portale cliente + DOSSIER.zip",
            output_files=[
                _file("presentazione-cliente.html", "07-cliente/", 1240, "text/html"),
                _file("timeline-90gg-cliente.pdf", "07-cliente/", 187),
                _file("DOSSIER-IMPRESA.zip", "05-impresa/", 15240, "application/zip"),
                _file("scheda-progetto.json", "08-studio-interno/", 8, "application/json"),
                _file("cash-flow-proiezione.xlsx", "08-studio-interno/", 42, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                _file("task-list-team.json", "08-studio-interno/", 12, "application/json"),
                _file("social-instagram.json", "08-studio-interno/", 28, "application/json"),
            ]),

    # TIER 2 · QA · 1 deliberate REJECT to show the loop
    StepDef("@quality-misure", 2, "qa", 18, "verifica 24 items · 5/5 critici PASS · 9/11 secondari PASS",
            qa_outcome="PASS",
            qa_checks=[
                {"check_id": "C1", "severity": "CRITICO", "description": "Somma quote orizzontali", "result": True},
                {"check_id": "C2", "severity": "CRITICO", "description": "Somma quote verticali", "result": True},
                {"check_id": "C3", "severity": "CRITICO", "description": "Sup utile = somma ambienti", "result": True},
                {"check_id": "C4", "severity": "CRITICO", "description": "Sup lorda = utile + muratura", "result": True},
                {"check_id": "C5", "severity": "CRITICO", "description": "Volume = sup × altezza", "result": True},
            ]),
    StepDef("@quality-normativa", 2, "qa", 22, "verifica 18 items · DPR 380 art 6-bis OK · CAM 2025 89% rispettato",
            qa_outcome="PASS",
            qa_checks=[
                {"check_id": "N-C1", "severity": "CRITICO", "description": "Tipo pratica corretto", "result": True},
                {"check_id": "N-C2", "severity": "CRITICO", "description": "Articoli DPR 380 esistono", "result": True},
                {"check_id": "N-C3", "severity": "CRITICO", "description": "Aut paesaggistica considerata", "result": True},
                {"check_id": "N-C4", "severity": "CRITICO", "description": "CAM Edilizia 2025 ≥80%", "result": True},
            ]),
    StepDef("@quality-dati", 2, "qa", 26,
            "REJECT · Volume parete IFC 18.5 m² ≠ computo 19.2 m² (diff 3.7%)",
            qa_outcome="REJECT",
            qa_checks=[
                {"check_id": "D-C1", "severity": "CRITICO", "description": "Sup lorda pianta=IFC=CILA", "result": True},
                {"check_id": "D-C2", "severity": "CRITICO", "description": "Volumi parete IFC = computo", "result": False,
                 "expected_value": "18.5 m²", "actual_value": "19.2 m²", "diff": "+0.7 m² (3.7%)"},
                {"check_id": "D-C3", "severity": "CRITICO", "description": "Totale computo=capitolato=contratto", "result": True},
            ]),

    # RETRY · @computo-engineer corrige
    StepDef("@computo-engineer", 1, "execution", 12, "RETRY 1/3 · correzione voce muratura demolizione (18.5 m²)",
            output_files=[
                _file("computo-metrico.xlsx", "05-impresa/", 240, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ]),

    # QA RE-RUN
    StepDef("@quality-dati", 2, "qa", 14, "RE-VERIFY · 16/16 items · PASS",
            qa_outcome="PASS",
            qa_checks=[
                {"check_id": "D-C2", "severity": "CRITICO", "description": "Volumi parete IFC = computo (re-check)", "result": True,
                 "expected_value": "18.5 m²", "actual_value": "18.5 m²"},
            ]),
    StepDef("@quality-output", 2, "qa", 16, "verifica 14 items · 27 deliverable · tutti i PDF aprono · upload Lovarch OK",
            qa_outcome="PASS",
            qa_checks=[
                {"check_id": "O-C1", "severity": "CRITICO", "description": "25+ deliverable presenti", "result": True,
                 "actual_value": "27"},
                {"check_id": "O-C2", "severity": "CRITICO", "description": "PDF aprono senza errore", "result": True,
                 "actual_value": "18/18"},
                {"check_id": "O-C6", "severity": "CRITICO", "description": "File uploaded → Lovarch", "result": True,
                 "actual_value": "27/27"},
            ]),

    # TIER 0 · CONSOLIDATION
    StepDef("@progetto-chief", 0, "orchestration", 8, "consolidamento dossier · git commit · open Finder",
            output_files=[
                _file("README.md", "", 4, "text/markdown"),
                _file("manifest.json", "", 6, "application/json"),
            ]),
]


# ----------------------------------------------------------------------------
# Simulator
# ----------------------------------------------------------------------------

def run_simulation(
    *,
    user_id: str,
    project_id: Optional[str] = None,
    speed: float = 1.0,
    dry_run: bool = False,
    sb: Optional[SupabaseRest] = None,
) -> Dict[str, Any]:
    """Run the simulation, inserting rows progressively."""
    execution_id = str(uuid.uuid4())

    if dry_run:
        print(f"[DRY-RUN] would create execution {execution_id} with {len(WORKFLOW)} steps")
        print(f"[DRY-RUN] estimated total duration (real): {sum(s.duration for s in WORKFLOW):.0f}s "
              f"({sum(s.duration for s in WORKFLOW) / speed:.0f}s with speed={speed})")
        return {"execution_id": execution_id, "dry_run": True}

    if sb is None:
        raise ValueError("SupabaseRest client required when not dry_run")

    # 1. Create execution
    print(f"\n▶ Creating execution {execution_id[:8]}...")
    exec_row = {
        "id": execution_id,
        "user_id": user_id,
        "project_id": project_id,
        "status": "running",
        "metadata": {
            "simulator": True,
            "scenario": "Attico Brera demo",
            "client": "Marco Rossini & Giulia Bianchi",
        },
    }
    sb.insert("pm_squad_executions", exec_row)

    # 2. AUTO-OPEN live tracking page in browser (so Pablo can watch real-time)
    base_url = os.environ.get("LOVARCH_WEB_URL", "https://lovarch.com")
    live_url = f"{base_url}/admin/squad-execution/{execution_id}/live"
    print(f"  Opening live tracking page: {live_url}")
    try:
        import webbrowser
        webbrowser.open(live_url, new=2)  # new=2 = new tab if possible
    except Exception as e:
        print(f"  (could not auto-open browser: {e} · open manually)")

    # 3. Iterate steps
    total_steps = 0
    total_qa_rejects = 0
    total_retries = 0

    for i, step_def in enumerate(WORKFLOW, start=1):
        step_id = str(uuid.uuid4())

        # Insert pending step
        step_row = {
            "id": step_id,
            "execution_id": execution_id,
            "agent_name": step_def.agent,
            "tier": step_def.tier,
            "step_type": step_def.step_type,
            "status": "pending",
            "action_description": step_def.action,
        }
        sb.insert("pm_squad_steps", step_row)

        # Mark as running
        time.sleep(0.5 / speed)
        started_at_ms = int(time.time() * 1000)
        sb.update(
            "pm_squad_steps",
            f"id=eq.{step_id}",
            {
                "status": "running",
                "started_at": _ts(),
            },
        )
        print(f"  [{i:2d}/{len(WORKFLOW)}] {step_def.agent:<25} {step_def.action[:60]}...", end="", flush=True)

        # Wait simulated duration
        time.sleep(step_def.duration / speed)

        # Determine final status
        if step_def.qa_outcome == "REJECT":
            final_status = "rejected"
            total_qa_rejects += 1
        else:
            final_status = "done"

        # If this is a retry step, mark with retry_count
        retry_count = 1 if "RETRY" in step_def.action.upper() else 0
        if retry_count:
            total_retries += 1

        # Compute duration
        elapsed = (int(time.time() * 1000) - started_at_ms) / 1000

        sb.update(
            "pm_squad_steps",
            f"id=eq.{step_id}",
            {
                "status": final_status,
                "completed_at": _ts(),
                "duration_seconds": int(elapsed),
                "output_files": step_def.output_files,
                "qa_report": {"verdict": step_def.qa_outcome} if step_def.qa_outcome else None,
                "retry_count": retry_count,
            },
        )

        # Insert QA checks if applicable
        if step_def.qa_checks:
            for chk in step_def.qa_checks:
                sb.insert("pm_squad_qa_checks", {
                    "step_id": step_id,
                    "execution_id": execution_id,
                    "qa_agent": step_def.agent,
                    "check_id": chk["check_id"],
                    "check_description": chk["description"],
                    "severity": chk["severity"],
                    "result": chk["result"],
                    "expected_value": chk.get("expected_value"),
                    "actual_value": chk.get("actual_value"),
                    "diff": chk.get("diff"),
                })

        total_steps += 1
        print(f" {final_status.upper()}")

    # 4. Mark execution as completed
    sb.update(
        "pm_squad_executions",
        f"id=eq.{execution_id}",
        {
            "status": "completed",
            "completed_at": _ts(),
            "total_steps": total_steps,
            "total_qa_rejects": total_qa_rejects,
            "total_retries": total_retries,
        },
    )

    # 5. AUTO-OPEN dossier page (final deliverables) when complete
    dossier_url = f"{base_url}/admin/squad-execution/{execution_id}/dossier"
    print(f"\n✓ Execution complete: {execution_id}")
    print(f"  Total steps: {total_steps}")
    print(f"  QA rejects: {total_qa_rejects} (loop demonstrato)")
    print(f"  Retries: {total_retries}")
    print(f"\n  Opening dossier page: {dossier_url}")
    try:
        import webbrowser
        webbrowser.open(dossier_url, new=2)
    except Exception:
        pass  # already opened live, dossier is bonus

    return {
        "execution_id": execution_id,
        "user_id": user_id,
        "total_steps": total_steps,
        "total_qa_rejects": total_qa_rejects,
        "total_retries": total_retries,
        "live_url": f"/admin/squad-execution/{execution_id}/live",
        "dossier_url": f"/admin/squad-execution/{execution_id}/dossier",
    }


def _ts() -> str:
    """ISO timestamp in UTC."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Simulate squad execution")
    parser.add_argument("--user-id", default=None, help="Supabase user UUID (defaults to env SUPABASE_USER_ID)")
    parser.add_argument("--project-id", default=None, help="Project UUID (optional)")
    parser.add_argument("--speed", type=float, default=1.0, help="Speed multiplier (1.0 = real time, 5.0 = 5× faster)")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without inserting")
    args = parser.parse_args()

    if args.dry_run:
        result = run_simulation(
            user_id=args.user_id or "00000000-0000-0000-0000-000000000000",
            project_id=args.project_id,
            speed=args.speed,
            dry_run=True,
        )
        print(json.dumps(result, indent=2))
        return

    if not SUPABASE_URL or not SUPABASE_KEY:
        sys.stderr.write(
            "ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing.\n"
            "Add to ~/.lovarch/secrets.env or env vars.\n"
        )
        sys.exit(1)

    user_id = args.user_id or get_env("SUPABASE_USER_ID")
    if not user_id:
        sys.stderr.write(
            "ERROR: --user-id required (or set SUPABASE_USER_ID).\n"
            "Get yours: SELECT id FROM auth.users WHERE email='pablo@archprime.io';\n"
        )
        sys.exit(1)

    sb = SupabaseRest(SUPABASE_URL, SUPABASE_KEY)
    result = run_simulation(
        user_id=user_id,
        project_id=args.project_id,
        speed=args.speed,
        sb=sb,
    )
    base_url = os.environ.get("LOVARCH_WEB_URL", "https://lovarch.com")
    print(f"\nLive tracking: {base_url}{result['live_url']}")
    print(f"Dossier:       {base_url}{result['dossier_url']}")
    print("\n(Browser was auto-opened on these pages during execution)")


if __name__ == "__main__":
    main()
