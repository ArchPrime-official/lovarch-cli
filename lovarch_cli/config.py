"""lovarch-cli config + credentials management.

Stores user state in ~/.lovarch/:
- credentials.json — auth tokens (free_token or premium refresh_token)
- config.yaml      — preferences (language, default workflow, API keys)

Free mode token is saved as plain text (low-sensitivity lead-tracking ID).
Premium mode tokens go through OS keyring (keyring lib) — see auth/credentials.py.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_HOME = Path.home() / ".lovarch"

# Lovarch Supabase API endpoint.
#
# Decision 2026-05-10 (Pablo + Orion): Opção A — URL Supabase direta.
# Custom domain api.lovarch.com fica para fase pre-PyPI public publish
# (ver cli/MIGRATION-PLAN.md). Quando criado, usuários instalados continuam
# funcionando via env LOVARCH_API_URL override ou bump de versão.
#
# The anon key below is PUBLIC by Supabase design (role=anon, RLS-protected).
# Same key shipped in Lovarch web frontend bundle. Safe to embed in
# distributed CLI source.
DEFAULT_API_URL = os.environ.get(
    "LOVARCH_API_URL", "https://cuxbydmyahjaplzkthkr.supabase.co"
)
DEFAULT_API_ANON_KEY = os.environ.get(
    "LOVARCH_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN1eGJ5ZG15YWhqYXBsemt0aGtyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIzODM3OTYsImV4cCI6MjA4Nzk1OTc5Nn0.UtHrPjSP40pwsRy6vCQseC5YA4DZ6e-hO8sXcRL8w_E",
)


@dataclass
class Credentials:
    """User authentication state.

    Free mode: free_token + lead_id (saved here in plain JSON).
    Premium mode: only marker; actual tokens live in OS keyring.
    """

    mode: str  # 'free' | 'premium' | 'none'
    lead_id: str | None = None
    user_id: str | None = None
    free_token: str | None = None
    email: str | None = None
    full_name: str | None = None
    country: str | None = None
    language: str = "it"
    signed_up_at: str | None = None
    upgrade_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> Credentials:
        return cls(mode="none")


def credentials_path(home: Path | None = None) -> Path:
    return (home or DEFAULT_HOME) / "credentials.json"


def load_credentials(home: Path | None = None) -> Credentials:
    path = credentials_path(home)
    if not path.exists():
        return Credentials.empty()
    try:
        data = json.loads(path.read_text())
        return Credentials(**data)
    except (json.JSONDecodeError, TypeError, ValueError):
        return Credentials.empty()


def save_credentials(creds: Credentials, home: Path | None = None) -> Path:
    path = credentials_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(creds), indent=2, ensure_ascii=False))
    # Restrict permissions on POSIX (rw-------)
    if os.name == "posix":
        path.chmod(0o600)
    return path


def clear_credentials(home: Path | None = None) -> bool:
    path = credentials_path(home)
    if path.exists():
        path.unlink()
        return True
    return False


def is_authenticated(home: Path | None = None) -> bool:
    creds = load_credentials(home)
    return creds.mode in {"free", "premium"} and (
        creds.free_token is not None or creds.user_id is not None
    )
