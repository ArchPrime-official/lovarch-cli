"""archprime-cli config + credentials management.

Stores user state in ~/.archprime/:
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

DEFAULT_HOME = Path.home() / ".archprime"

# Primary URL — overridable via env for staging/dev
DEFAULT_API_URL = os.environ.get("LOVARCH_API_URL", "https://api.lovarch.com")
DEFAULT_API_ANON_KEY = os.environ.get("LOVARCH_ANON_KEY", "")


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
