"""
Lovarch Persistence Client · for squad architettura-progetto

Centralizes all CREATE/UPDATE operations against the Lovarch Supabase backend.
Used by @progetto-chief and @deliverable-builder to persist project data
(projects, clients, documents, renders, moodboards, contracts, tasks, budget items)
into the appropriate Lovarch tables.

Reads SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY from ~/.lovarch/secrets.env.

Usage:
    from squads.architettura_progetto.scripts.lovarch_client import LovarchClient

    client = LovarchClient()

    # 1. Create lead (cliente CRM)
    lead_id = client.create_lead(
        user_id=pablo_uuid,
        name="Marco Rossini",
        email="marco@example.it",
        phone="+39 333 1234567",
        budget=180000,
        notes="Attico Brera ristrutturazione",
    )

    # 2. Create project linked to lead
    project_id = client.create_project(
        user_id=pablo_uuid,
        lead_id=lead_id,
        name="Attico Brera",
        address="Via Fiori Chiari 17, Milano",
        client_name="Marco Rossini & Giulia Bianchi",
        client_email="marco@example.it",
        budget_min=170000,
        budget_max=190000,
    )

    # 3. Create phases
    phases = client.create_phases(project_id, user_id=pablo_uuid)

    # 4. Upload + persist document
    doc_id = client.upload_document(
        project_id=project_id,
        user_id=pablo_uuid,
        local_path="~/projects/attico-brera/05-impresa/capitolato-speciale.pdf",
        doc_type="capitolato",
        name="Capitolato Speciale",
    )

    # 5. Save render + link to project
    render_id = client.save_render(
        user_id=pablo_uuid,
        asset_url="https://...flux-render.png",
        render_mode="plan_to_3d",
        metadata={"project_id": project_id, "ambient": "living"},
    )

    # 6. Create contract
    contract_id = client.create_contract(
        user_id=pablo_uuid,
        lead_id=lead_id,
        title="Contratto Attico Brera",
        client_name="Marco Rossini",
        content_url="...",
    )

    # 7. Bulk create tasks
    task_ids = client.bulk_create_tasks(
        project_id=project_id,
        user_id=pablo_uuid,
        tasks=[
            {"title": "Riunione cliente concept", "phase": "concept", "deadline": "2026-05-08"},
            {"title": "Sopralluogo cantiere", "phase": "esecutivo", "deadline": "2026-06-25"},
            ...
        ],
    )

    # 8. Bulk create budget items
    client.bulk_create_budget_items(
        project_id=project_id,
        user_id=pablo_uuid,
        items=[
            {"category": "Demolizioni", "description": "Tramezze interne", "estimated_amount": 4250},
            ...
        ],
    )

    # 9. Invite client to portal
    portal_data = client.invite_to_portal(
        project_id=project_id,
        email="marco@example.it",
        name="Marco Rossini",
    )
"""
from __future__ import annotations

import json
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.parse
import urllib.request


SECRETS_FILE = Path.home() / ".lovarch" / "secrets.env"
LOVARCH_ROOT = Path("/Users/pablo/Lovarch")
LOVARCH_ENV = LOVARCH_ROOT / ".env"
LOVARCH_ENV_LOCAL = LOVARCH_ROOT / ".env.local"


def _load_secrets() -> Dict[str, str]:
    """Load from ~/.lovarch/secrets.env, /Users/pablo/Lovarch/.env, and .env.local (in priority order)."""
    secrets: Dict[str, str] = {}
    for path in [SECRETS_FILE, LOVARCH_ENV_LOCAL, LOVARCH_ENV]:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            # strip quotes
            v = v.strip().strip('"').strip("'")
            secrets.setdefault(k.strip(), v)
    return secrets


_SECRETS = _load_secrets()


def _env(name: str) -> Optional[str]:
    """Priority: secrets.env > .env.local > shell env. NOTE: shell env is LAST because it
    may contain values for OTHER projects (e.g. PrimeTeam vs Lovarch)."""
    return _SECRETS.get(name) or os.environ.get(name)


# Resolve Lovarch Supabase URL · prefer VITE_SUPABASE_URL from .env.local (Lovarch project)
# over SUPABASE_URL env var (which may point to PrimeTeam)
SUPABASE_URL = _env("VITE_SUPABASE_URL") or _env("LOVARCH_SUPABASE_URL") or _env("SUPABASE_URL")
SUPABASE_KEY = (
    _env("LOVARCH_SUPABASE_SERVICE_ROLE_KEY")
    or _env("SUPABASE_SERVICE_ROLE_KEY")
    or _env("SUPABASE_SERVICE_KEY")
)


class LovarchClientError(Exception):
    pass


class LovarchClient:
    """
    Persistence client for Lovarch backend.

    Uses Supabase REST + Edge Functions with service_role auth (admin bypass).
    All operations are idempotent where possible (UPSERT vs INSERT).
    """

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        self.url = (url or SUPABASE_URL or "").rstrip("/")
        self.key = key or SUPABASE_KEY
        if not self.url or not self.key:
            raise LovarchClientError(
                "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY · "
                f"add to {SECRETS_FILE}"
            )
        # Detect URL/key project mismatch (e.g. Lovarch URL with PrimeTeam key)
        self._validate_project_match()

    def _validate_project_match(self) -> None:
        """Verify that the JWT key's project ref matches the URL host.

        Common pitfall: shell env has SUPABASE_URL=PrimeTeam but config.toml/.env
        points to Lovarch. Detects mismatch early to fail loudly.
        """
        try:
            import base64
            parts = self.key.split(".")
            if len(parts) != 3:
                return
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + "==").decode())
            key_ref = payload.get("ref")
            url_host = self.url.replace("https://", "").split(".")[0]
            if key_ref and url_host and key_ref != url_host:
                raise LovarchClientError(
                    f"Project mismatch: URL points to '{url_host}' but key is for '{key_ref}'. "
                    f"Add LOVARCH_SUPABASE_SERVICE_ROLE_KEY to ~/.lovarch/secrets.env "
                    f"(get it from https://supabase.com/dashboard/project/{url_host}/settings/api)"
                )
        except LovarchClientError:
            raise
        except Exception:
            pass  # if decoding fails, fall through · runtime errors will surface real issue
        self.headers_json = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    # ------------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------------
    def _rest(
        self,
        method: str,
        path: str,
        body: Optional[Any] = None,
    ) -> Any:
        url = f"{self.url}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(
            url, data=data, method=method, headers=self.headers_json
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            raise LovarchClientError(
                f"Supabase {method} {path} failed [{e.code}]: {err}"
            ) from e

    def _edge(self, function_name: str, body: Dict[str, Any]) -> Any:
        return self._rest("POST", f"/functions/v1/{function_name}", body)

    # ------------------------------------------------------------------------
    # 1. LEADS · CRM client
    # ------------------------------------------------------------------------
    def create_lead(
        self,
        *,
        user_id: str,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        budget: Optional[float] = None,
        proposal_value: Optional[float] = None,
        status: str = "proposal",
        source: str = "squad-architettura-progetto",
        channel: Optional[str] = None,
        intervention_type: Optional[str] = None,
        project_type: Optional[str] = None,
        city: Optional[str] = None,
        region: Optional[str] = None,
        country: str = "IT",
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        timeline: Optional[int] = None,
        timeline_unit: str = "days",
    ) -> str:
        """Create lead · matches REAL schema (no `company`/`stage`/`priority` cols)."""
        row = {
            "user_id": user_id,
            "name": name,
            "email": email,
            "phone": phone,
            "budget": budget,
            "proposal_value": proposal_value,
            "status": status,
            "source": source,
            "channel": channel,
            "intervention_type": intervention_type,
            "project_type": project_type,
            "city": city,
            "region": region,
            "country": country,
            "notes": notes,
            "tags": tags or [],
            "timeline": timeline,
            "timeline_unit": timeline_unit,
        }
        # Strip Nones to avoid type conflicts
        row = {k: v for k, v in row.items() if v is not None}
        result = self._rest("POST", "/rest/v1/leads", body=row)
        if not result:
            raise LovarchClientError("create_lead returned empty")
        return result[0]["id"] if isinstance(result, list) else result["id"]

    # ------------------------------------------------------------------------
    # 2. PROJECTS · pm_projects
    # ------------------------------------------------------------------------
    def create_project(
        self,
        *,
        user_id: str,
        name: str,
        lead_id: Optional[str] = None,
        address: Optional[str] = None,
        typology: str = "ristrutturazione",
        client_type: str = "private",
        square_meters: Optional[float] = None,
        client_name: Optional[str] = None,
        client_email: Optional[str] = None,
        client_phone: Optional[str] = None,
        brief_objectives: Optional[str] = None,
        brief_style: Optional[str] = None,
        constraints: Optional[str] = None,
        budget_min: Optional[float] = None,
        budget_max: Optional[float] = None,
        contingency_percent: float = 5.0,
        professional_fee_percent: Optional[float] = None,
        priority: str = "medium",
        status: str = "active",
        current_phase: int = 0,  # INT · matches new-home (was incorrectly string)
        start_date: Optional[str] = None,
        delivery_date: Optional[str] = None,
    ) -> str:
        """Create project · matches new-home useCreateProject (current_phase is INT)."""
        row = {
            "user_id": user_id,
            "lead_id": lead_id,
            "name": name,
            "address": address,
            "typology": typology,
            "client_type": client_type,
            "square_meters": square_meters,
            "client_name": client_name,
            "client_email": client_email,
            "client_phone": client_phone,
            "brief_objectives": brief_objectives,
            "brief_style": brief_style,
            "constraints": constraints,
            "budget_min": budget_min,
            "budget_max": budget_max,
            "contingency_percent": contingency_percent,
            "professional_fee_percent": professional_fee_percent,
            "priority": priority,
            "status": status,
            "current_phase": current_phase,
            "start_date": start_date,
            "delivery_date": delivery_date,
        }
        row = {k: v for k, v in row.items() if v is not None}
        result = self._rest("POST", "/rest/v1/pm_projects", body=row)
        return result[0]["id"] if isinstance(result, list) else result["id"]

    # ------------------------------------------------------------------------
    # 3. PHASES · pm_phases (6 standard phases · matches useCreateProject)
    # ------------------------------------------------------------------------
    DEFAULT_PHASES_IT = [
        "Briefing & Concept",
        "Progetto Definitivo",
        "Pratiche Edilizie",
        "Progetto Esecutivo",
        "Direzione Lavori",
        "Consegna & Collaudo",
    ]

    def create_phases(
        self,
        *,
        project_id: str,
        user_id: str,
    ) -> List[str]:
        """Create 6 standard Italian project phases · matches new-home useCreateProject pattern."""
        rows = [
            {
                "project_id": project_id,
                "user_id": user_id,
                "name": name,
                "order_index": index,
                "status": "in_progress" if index == 0 else "not_started",
            }
            for index, name in enumerate(self.DEFAULT_PHASES_IT)
        ]
        result = self._rest("POST", "/rest/v1/pm_phases", body=rows)
        return [r["id"] for r in result]

    # ------------------------------------------------------------------------
    # 3b. BUDGET CATEGORIES · pm_budget_items (10 default · matches new-home %)
    # ------------------------------------------------------------------------
    DEFAULT_BUDGET_CATEGORIES = [
        ("opere_edili", "Opere edili", 0.35),
        ("impianti", "Impianti", 0.15),
        ("finiture", "Finiture", 0.10),
        ("arredi_misura", "Arredi su misura", 0.10),
        ("arredi_commerciali", "Arredi commerciali", 0.05),
        ("illuminazione", "Illuminazione", 0.05),
        ("decorazioni", "Decorazioni", 0.03),
        ("spese_tecniche", "Spese tecniche", 0.05),
        ("commissione", "Commissione architetto", 0.07),
        ("imprevisti", "Imprevisti", 0.05),
    ]

    def create_default_budget_categories(
        self,
        *,
        project_id: str,
        user_id: str,
        budget_max: float,
    ) -> List[str]:
        """Create 10 default budget categories with % breakdown · matches new-home defaults."""
        if not budget_max or budget_max <= 0:
            return []
        rows = [
            {
                "project_id": project_id,
                "user_id": user_id,
                "category": cat,
                "description": desc,
                "estimated_amount": round(budget_max * pct, 2),
            }
            for cat, desc, pct in self.DEFAULT_BUDGET_CATEGORIES
        ]
        result = self._rest("POST", "/rest/v1/pm_budget_items", body=rows)
        return [r["id"] for r in result]

    # ------------------------------------------------------------------------
    # 4. DOCUMENTS · pm_documents (deliverables PDF/DXF/IFC/XLSX)
    # ------------------------------------------------------------------------
    def upload_document(
        self,
        *,
        project_id: str,
        user_id: str,
        local_path: str,
        doc_type: str,
        name: Optional[str] = None,
        phase_id: Optional[str] = None,
        bucket: str = "pm-documents",
        notes: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Upload local file to Storage + insert pm_documents row.
        Returns (document_id, public_url).
        """
        local = Path(local_path).expanduser()
        if not local.exists():
            raise LovarchClientError(f"File not found: {local}")

        # 1. Upload to Storage
        storage_path = f"squad-arch/{project_id}/{local.name}"
        mime = mimetypes.guess_type(str(local))[0] or "application/octet-stream"
        with local.open("rb") as f:
            file_bytes = f.read()

        upload_url = f"{self.url}/storage/v1/object/{bucket}/{storage_path}"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": mime,
            "x-upsert": "true",
        }
        req = urllib.request.Request(
            upload_url, data=file_bytes, method="POST", headers=headers
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                r.read()
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            raise LovarchClientError(f"Storage upload failed [{e.code}]: {err}") from e

        public_url = f"{self.url}/storage/v1/object/public/{bucket}/{storage_path}"

        # 2. Insert pm_documents row
        row = {
            "project_id": project_id,
            "phase_id": phase_id,
            "user_id": user_id,
            "uploaded_by": user_id,
            "name": name or local.stem,
            "doc_type": doc_type,
            "file_url": public_url,
            "file_size": len(file_bytes),
            "notes": notes,
        }
        result = self._rest("POST", "/rest/v1/pm_documents", body=row)
        doc_id = result[0]["id"] if isinstance(result, list) else result["id"]
        return doc_id, public_url

    def upload_documents_batch(
        self,
        *,
        project_id: str,
        user_id: str,
        files: List[Dict[str, Any]],
    ) -> List[Tuple[str, str]]:
        """Bulk upload · files = [{local_path, doc_type, name?, phase_id?}, ...]"""
        return [
            self.upload_document(
                project_id=project_id,
                user_id=user_id,
                **f,
            )
            for f in files
        ]

    # ------------------------------------------------------------------------
    # 5. RENDERS · render_assets (project_id is FIRST-CLASS · linked to new-home)
    # ------------------------------------------------------------------------
    def save_render(
        self,
        *,
        user_id: str,
        project_id: str,  # required for new-home visibility
        asset_url: str,
        asset_type: str = "image",
        render_mode: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        original_width: Optional[int] = None,
        original_height: Optional[int] = None,
        file_size_bytes: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        row = {
            "user_id": user_id,
            "project_id": project_id,  # ✓ FK to pm_projects · visible in ProjectDetailConnections tab
            "asset_type": asset_type,
            "asset_url": asset_url,
            "thumbnail_url": thumbnail_url,
            "render_mode": render_mode,
            "original_width": original_width,
            "original_height": original_height,
            "file_size_bytes": file_size_bytes,
            "metadata": metadata or {},
        }
        result = self._rest("POST", "/rest/v1/render_assets", body=row)
        return result[0]["id"] if isinstance(result, list) else result["id"]

    def link_render_to_project(self, render_id: str, project_id: str) -> None:
        """Update existing render_assets row with project_id (orphan rescue)."""
        self._rest(
            "PATCH",
            f"/rest/v1/render_assets?id=eq.{render_id}",
            body={"project_id": project_id},
        )

    # ------------------------------------------------------------------------
    # 5b. MOODBOARD · moodboard_analyses + moodboard_generated_assets
    # (THE ENTRY POINT new-home uses · NOT moodboard_images directly)
    # ------------------------------------------------------------------------
    def create_moodboard_analysis(
        self,
        *,
        user_id: str,
        project_id: str,
        name: str,
        user_prompt: Optional[str] = None,
        atmosphere: Optional[str] = None,
        materials: Optional[List[str]] = None,
        color_palette: Optional[List[str]] = None,
        typography: Optional[str] = None,
        geometry: Optional[str] = None,
        spatial_references: Optional[List[str]] = None,
        source_images: Optional[List[str]] = None,
        design_system_md: Optional[str] = None,
        model_used: str = "squad-architettura-progetto",
        status: str = "completed",
    ) -> str:
        """Create moodboard_analyses · matches REAL schema (no title/keywords/feeling cols)."""
        row = {
            "user_id": user_id,
            "project_id": project_id,
            "name": name,
            "user_prompt": user_prompt,
            "atmosphere": atmosphere,
            "materials": materials or [],
            "color_palette": color_palette or [],
            "typography": typography,
            "geometry": geometry,
            "spatial_references": spatial_references or [],
            "source_images": source_images or [],
            "design_system_md": design_system_md,
            "model_used": model_used,
            "status": status,
        }
        row = {k: v for k, v in row.items() if v is not None}
        result = self._rest("POST", "/rest/v1/moodboard_analyses", body=row)
        return result[0]["id"] if isinstance(result, list) else result["id"]

    def add_moodboard_assets(
        self,
        *,
        analysis_id: str,
        assets: List[Dict[str, Any]],
    ) -> List[str]:
        """assets = [{asset_type, asset_url, description?, tags?}, ...]
        asset_type one of: 'flatlay_complete' (priority 3 · cover), 'atmosphere' (2), 'colors' (1)
        NOTE: moodboard_generated_assets has NO user_id col · linked only via analysis_id."""
        rows = []
        for a in assets:
            row = {
                "analysis_id": analysis_id,
                "asset_type": a.get("asset_type", "atmosphere"),
                "asset_url": a["asset_url"],
                "description": a.get("description"),
                "tags": a.get("tags", []),
            }
            rows.append({k: v for k, v in row.items() if v is not None})
        result = self._rest("POST", "/rest/v1/moodboard_generated_assets", body=rows)
        return [r["id"] for r in result]

    # ------------------------------------------------------------------------
    # 6. CONTRACTS · contracts (project_id linked · visible in ProjectDetailContract)
    # ------------------------------------------------------------------------
    def create_contract(
        self,
        *,
        user_id: str,
        title: str,
        client_name: str,
        project_id: Optional[str] = None,  # FK to pm_projects · for new-home tab
        content: Optional[str] = None,
        lead_id: Optional[str] = None,
        proposal_id: Optional[str] = None,
        status: str = "draft",
        signed_at: Optional[str] = None,
        expires_at: Optional[str] = None,
    ) -> str:
        """Create contract · matches REAL schema (no `total` col · use proposal_id for value)."""
        row = {
            "user_id": user_id,
            "project_id": project_id,
            "lead_id": lead_id,
            "proposal_id": proposal_id,
            "title": title,
            "client_name": client_name,
            "content": content,
            "status": status,
            "signed_at": signed_at,
            "expires_at": expires_at,
        }
        row = {k: v for k, v in row.items() if v is not None}
        result = self._rest("POST", "/rest/v1/contracts", body=row)
        return result[0]["id"] if isinstance(result, list) else result["id"]

    # ------------------------------------------------------------------------
    # 7. TASKS · pm_tasks (bulk)
    # ------------------------------------------------------------------------
    def bulk_create_tasks(
        self,
        *,
        project_id: str,
        user_id: str,
        tasks: List[Dict[str, Any]],
    ) -> List[str]:
        """tasks = [{title, description?, status?, priority?, deadline?, phase_id?}, ...]"""
        rows = []
        for t in tasks:
            rows.append(
                {
                    "project_id": project_id,
                    "user_id": user_id,
                    "title": t["title"],
                    "description": t.get("description"),
                    "status": t.get("status", "todo"),
                    "priority": t.get("priority", "medium"),
                    "deadline": t.get("deadline"),
                    "phase_id": t.get("phase_id"),
                    "responsible": t.get("responsible"),
                }
            )
        result = self._rest("POST", "/rest/v1/pm_tasks", body=rows)
        return [r["id"] for r in result]

    # ------------------------------------------------------------------------
    # 8. BUDGET ITEMS · pm_budget_items (computo metrico)
    # ------------------------------------------------------------------------
    def bulk_create_budget_items(
        self,
        *,
        project_id: str,
        user_id: str,
        items: List[Dict[str, Any]],
    ) -> List[str]:
        """items = [{category, description, estimated_amount, approved_amount?}, ...]"""
        rows = []
        for it in items:
            rows.append(
                {
                    "project_id": project_id,
                    "user_id": user_id,
                    "category": it["category"],
                    "description": it["description"],
                    "estimated_amount": it["estimated_amount"],
                    "approved_amount": it.get("approved_amount"),
                    "actual_amount": it.get("actual_amount"),
                }
            )
        result = self._rest("POST", "/rest/v1/pm_budget_items", body=rows)
        return [r["id"] for r in result]

    # ------------------------------------------------------------------------
    # 8b. FINANCIAL · financial_transactions (income onorari · 4 SAL installments)
    # ------------------------------------------------------------------------
    DEFAULT_SAL_BREAKDOWN = [
        ("SAL 1 · Concept + Definitivo", 0.15),
        ("SAL 2 · Pratiche + Esecutivo", 0.25),
        ("SAL 3 · DL inizio cantiere", 0.25),
        ("SAL 4 · Saldo consegna", 0.35),
    ]

    def get_or_create_finance_category(
        self,
        *,
        user_id: str,
        name: str = "Onorari Architetto",
        category_type: str = "vendas",
        subcategories: Optional[List[str]] = None,
    ) -> str:
        """Get existing or create financial_categories row for project income."""
        # Try fetch first (URL-encode name · may contain spaces)
        encoded_name = urllib.parse.quote(name)
        existing = self._rest(
            "GET",
            f"/rest/v1/financial_categories?user_id=eq.{user_id}&name=eq.{encoded_name}&select=id",
        )
        if existing and isinstance(existing, list) and existing:
            return existing[0]["id"]

        # Create new
        row = {
            "user_id": user_id,
            "name": name,
            "type": category_type,
            "subcategories": subcategories or ["SAL1", "SAL2", "SAL3", "SAL4"],
        }
        result = self._rest("POST", "/rest/v1/financial_categories", body=row)
        return result[0]["id"] if isinstance(result, list) else result["id"]

    def create_financial_income(
        self,
        *,
        user_id: str,
        lead_id: Optional[str],
        project_id: Optional[str],  # ✓ financial_transactions HAS project_id directly
        project_name: str,
        total_value: float,
        start_date: str,  # ISO YYYY-MM-DD · first SAL date
        category_id: Optional[str] = None,
        description_prefix: str = "Onorari",
        sal_breakdown: Optional[List[Tuple[str, float]]] = None,
        bank_account_id: Optional[str] = None,
    ) -> List[str]:
        """
        Create financial income rows · 4 SAL installments tied to project.

        Pattern: parent transaction + 4 children with installment_number 1-4 of 4.
        Returns: list of transaction IDs (parent + children).

        Default SAL breakdown · 15%/25%/25%/35% (matches CNAPPC standard).
        Spaced 90 days each · adjustable via sal_breakdown override.
        """
        from datetime import datetime, timedelta

        if not category_id:
            category_id = self.get_or_create_finance_category(user_id=user_id)

        breakdown = sal_breakdown or self.DEFAULT_SAL_BREAKDOWN
        start = datetime.fromisoformat(start_date)

        # Parent transaction (carries the totals; children carry the installments)
        parent_row = {
            "user_id": user_id,
            "lead_id": lead_id,
            "project_id": project_id,
            "type": "income",
            "description": f"{description_prefix}: {project_name}",
            "category_id": category_id,
            "value": total_value,
            "date": start_date,
            "status": "pending",
            "installments": len(breakdown),
            "bank_account_id": bank_account_id,
            "auto_generated": True,
            "project_name": project_name,
        }
        parent_row = {k: v for k, v in parent_row.items() if v is not None}
        parent = self._rest("POST", "/rest/v1/financial_transactions", body=parent_row)
        parent_id = parent[0]["id"] if isinstance(parent, list) else parent["id"]

        # Children: 4 SAL installments
        ids = [parent_id]
        for index, (label, pct) in enumerate(breakdown, start=1):
            sal_date = (start + timedelta(days=90 * (index - 1))).date().isoformat()
            child_row = {
                "user_id": user_id,
                "lead_id": lead_id,
                "project_id": project_id,
                "type": "income",
                "description": f"{description_prefix}: {project_name} · {label}",
                "category_id": category_id,
                "value": round(total_value * pct, 2),
                "date": sal_date,
                "status": "pending",
                "installment_number": index,
                "installments": len(breakdown),
                "parent_transaction_id": parent_id,
                "bank_account_id": bank_account_id,
                "auto_generated": True,
                "project_name": project_name,
            }
            child_row = {k: v for k, v in child_row.items() if v is not None}
            child = self._rest("POST", "/rest/v1/financial_transactions", body=child_row)
            ids.append(child[0]["id"] if isinstance(child, list) else child["id"])

        return ids

    # ------------------------------------------------------------------------
    # 9. PORTAL · portal-auth invite
    # ------------------------------------------------------------------------
    def invite_to_portal(
        self,
        *,
        project_id: str,
        email: str,
        name: str,
        phone: Optional[str] = None,
        locale: str = "it",
    ) -> Dict[str, Any]:
        """
        Calls portal-auth edge function with action=invite.
        Returns {client, magic_link_url, magic_token}.
        """
        return self._edge(
            "portal-auth",
            {
                "action": "invite",
                "email": email,
                "name": name,
                "phone": phone,
                "project_id": project_id,
                "locale": locale,
            },
        )

    # ------------------------------------------------------------------------
    # 10. SQUAD EXECUTION · pm_squad_executions / steps / qa_checks
    # ------------------------------------------------------------------------
    def create_execution(
        self,
        *,
        user_id: str,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        row = {
            "user_id": user_id,
            "project_id": project_id,
            "status": "running",
            "metadata": metadata or {},
        }
        result = self._rest("POST", "/rest/v1/pm_squad_executions", body=row)
        return result[0]["id"] if isinstance(result, list) else result["id"]

    def update_execution(
        self,
        *,
        execution_id: str,
        patch: Dict[str, Any],
    ) -> None:
        self._rest(
            "PATCH",
            f"/rest/v1/pm_squad_executions?id=eq.{execution_id}",
            body=patch,
        )

    # ========================================================================
    # ALL-IN-ONE · create_project_complete
    # Bootstraps lead + project + 6 phases + 10 budget categories +
    # finance category + 4 SAL installments + portal client invitation.
    #
    # This is what @progetto-chief calls at the START of every execution.
    # ========================================================================
    def create_project_complete(
        self,
        *,
        user_id: str,
        client_data: Dict[str, Any],
        project_data: Dict[str, Any],
        finance_config: Optional[Dict[str, Any]] = None,
        invite_to_portal: bool = True,
    ) -> Dict[str, Any]:
        """
        End-to-end project bootstrap · matches new-home useCreateProject + extras.

        client_data: {name, email, phone?, company?, budget?}
        project_data: {name, address?, typology?, square_meters?,
                       brief_objectives?, brief_style?, budget_min?, budget_max?,
                       delivery_date?}
        finance_config: optional · {onorari_total, start_date, sal_breakdown?}
        invite_to_portal: if True, creates portal_clients row + magic link

        Returns:
            {
              lead_id, project_id, phase_ids[], budget_item_ids[],
              finance_category_id?, finance_transaction_ids?[],
              portal: {magic_link_url?}
            }
        """
        # 1. Lead (CRM client)
        lead_id = self.create_lead(
            user_id=user_id,
            name=client_data["name"],
            email=client_data.get("email"),
            phone=client_data.get("phone"),
            budget=client_data.get("budget") or project_data.get("budget_max"),
            proposal_value=client_data.get("proposal_value") or project_data.get("budget_max"),
            status="proposal",
            source="squad-architettura-progetto",
            intervention_type=project_data.get("typology"),
            city=client_data.get("city"),
            region=client_data.get("region"),
            notes=f"Auto-created by squad · project: {project_data['name']}",
        )

        # 2. Project (with lead_id linked)
        project_id = self.create_project(
            user_id=user_id,
            lead_id=lead_id,
            name=project_data["name"],
            address=project_data.get("address"),
            typology=project_data.get("typology", "ristrutturazione"),
            square_meters=project_data.get("square_meters"),
            client_name=client_data["name"],
            client_email=client_data.get("email"),
            client_phone=client_data.get("phone"),
            brief_objectives=project_data.get("brief_objectives"),
            brief_style=project_data.get("brief_style"),
            constraints=project_data.get("constraints"),
            budget_min=project_data.get("budget_min"),
            budget_max=project_data.get("budget_max"),
            professional_fee_percent=project_data.get("professional_fee_percent"),
            priority="high",
            status="active",
            current_phase=0,  # INT · matches new-home pattern
            delivery_date=project_data.get("delivery_date"),
        )

        # 3. Phases (6 default IT)
        phase_ids = self.create_phases(project_id=project_id, user_id=user_id)

        # 4. Budget categories (10 default with % breakdown)
        budget_item_ids = []
        if project_data.get("budget_max"):
            budget_item_ids = self.create_default_budget_categories(
                project_id=project_id,
                user_id=user_id,
                budget_max=project_data["budget_max"],
            )

        # 5. Finance integration (4 SAL onorari) · OPTIONAL
        finance_category_id = None
        finance_transaction_ids = []
        if finance_config:
            finance_category_id = self.get_or_create_finance_category(user_id=user_id)
            finance_transaction_ids = self.create_financial_income(
                user_id=user_id,
                lead_id=lead_id,
                project_id=project_id,  # ✓ financial_transactions HAS project_id col
                project_name=project_data["name"],
                total_value=finance_config["onorari_total"],
                start_date=finance_config.get("start_date"),
                category_id=finance_category_id,
                sal_breakdown=finance_config.get("sal_breakdown"),
            )

        # 6. Portal client invite · OPTIONAL
        portal_data: Dict[str, Any] = {}
        if invite_to_portal and client_data.get("email"):
            try:
                portal_data = self.invite_to_portal(
                    project_id=project_id,
                    email=client_data["email"],
                    name=client_data["name"],
                    phone=client_data.get("phone"),
                )
            except LovarchClientError as e:
                # Don't fail the whole bootstrap if portal invite fails
                portal_data = {"error": str(e)}

        return {
            "lead_id": lead_id,
            "project_id": project_id,
            "phase_ids": phase_ids,
            "budget_item_ids": budget_item_ids,
            "finance_category_id": finance_category_id,
            "finance_transaction_ids": finance_transaction_ids,
            "portal": portal_data,
        }


# ----------------------------------------------------------------------------
# CLI test
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    client = LovarchClient()
    print(f"✓ LovarchClient connected to {client.url}")

    if len(sys.argv) >= 2 and sys.argv[1] == "test":
        # Quick smoke: list 1 project to verify auth works
        result = client._rest("GET", "/rest/v1/pm_projects?limit=1&select=id,name")
        print(f"✓ Auth OK · {len(result)} projects in pm_projects (limit 1)")
