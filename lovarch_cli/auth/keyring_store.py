"""OS-native secure storage for premium Lovarch session tokens.

Uses the `keyring` lib (already in pyproject deps) which routes to:
- macOS  → Keychain
- Windows → Windows Credential Manager
- Linux  → Secret Service (gnome-keyring, KWallet, or fallback)

Service identifier: 'lovarch-cli'
Account identifiers (one per stored item):
- 'premium-access-token'
- 'premium-refresh-token'

The non-sensitive bits (user_id, email, full_name, expires_at) live in
~/.lovarch/credentials.json alongside the free-mode payload, with
mode='premium'. Tokens never appear in plain JSON.

Fallback if keyring lib not available or backend fails: store tokens in
~/.lovarch/credentials.json with chmod 0600 + a warning logged. This is
a soft fallback for headless/CI environments.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import keyring as _keyring
    import keyring.errors as _keyring_errors

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

from lovarch_cli.config import DEFAULT_HOME, Credentials, save_credentials

log = logging.getLogger("lovarch_cli.auth.keyring")

KEYRING_SERVICE = "lovarch-cli"
KEY_ACCESS = "premium-access-token"
KEY_REFRESH = "premium-refresh-token"


@dataclass
class PremiumSession:
    """Loaded premium session — non-sensitive metadata + tokens."""

    user_id: str
    email: str
    full_name: str | None
    access_token: str
    refresh_token: str
    expires_at: str  # ISO 8601
    metadata: dict[str, Any] = field(default_factory=dict)


def _backend_available() -> bool:
    if not KEYRING_AVAILABLE:
        return False
    try:
        _keyring.get_password(KEYRING_SERVICE, KEY_ACCESS)
        return True
    except _keyring_errors.NoKeyringError:
        return False
    except Exception:  # noqa: BLE001
        return False


def save_premium_session(
    *,
    user_id: str,
    email: str,
    full_name: str | None,
    access_token: str,
    refresh_token: str,
    expires_at: str,
    language: str = "it",
    home: Path | None = None,
) -> tuple[bool, str]:
    """Save tokens to OS keyring + non-sensitive credentials to JSON.

    Returns (used_keyring, location_description) for UX messaging.
    """
    used_keyring = _backend_available()

    if used_keyring:
        try:
            _keyring.set_password(
                KEYRING_SERVICE, f"{KEY_ACCESS}:{user_id}", access_token
            )
            _keyring.set_password(
                KEYRING_SERVICE, f"{KEY_REFRESH}:{user_id}", refresh_token
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("keyring save failed (%s) — falling back to file", exc)
            used_keyring = False

    creds = Credentials(
        mode="premium",
        user_id=user_id,
        email=email,
        full_name=full_name,
        language=language,
        signed_up_at=datetime.utcnow().isoformat(timespec="seconds"),
        metadata={
            "premium_expires_at": expires_at,
            "tokens_in_keyring": used_keyring,
            # If keyring unavailable, store tokens in JSON as fallback (chmod 0600)
            **(
                {}
                if used_keyring
                else {
                    "fallback_access_token": access_token,
                    "fallback_refresh_token": refresh_token,
                }
            ),
        },
    )
    creds_path = save_credentials(creds, home)

    location = "OS keyring + " if used_keyring else "JSON fallback (chmod 0600): "
    return used_keyring, f"{location}{creds_path}"


def load_premium_session(
    home: Path | None = None,
) -> PremiumSession | None:
    """Load premium session from credentials.json + keyring.

    Returns None if credentials.json is missing, mode != 'premium', or
    keyring lookup fails AND no fallback is present.
    """
    creds_path = (home or DEFAULT_HOME) / "credentials.json"
    if not creds_path.exists():
        return None
    try:
        data: dict[str, Any] = json.loads(creds_path.read_text())
    except (json.JSONDecodeError, ValueError):
        return None
    if data.get("mode") != "premium":
        return None

    user_id = data.get("user_id")
    if not user_id:
        return None

    md = data.get("metadata") or {}
    expires_at = md.get("premium_expires_at", "")

    access_token: str | None = None
    refresh_token: str | None = None

    if md.get("tokens_in_keyring") and KEYRING_AVAILABLE:
        try:
            access_token = _keyring.get_password(
                KEYRING_SERVICE, f"{KEY_ACCESS}:{user_id}"
            )
            refresh_token = _keyring.get_password(
                KEYRING_SERVICE, f"{KEY_REFRESH}:{user_id}"
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("keyring load failed (%s)", exc)

    if not access_token or not refresh_token:
        # Try fallback fields
        access_token = md.get("fallback_access_token")
        refresh_token = md.get("fallback_refresh_token")

    if not access_token or not refresh_token:
        return None

    return PremiumSession(
        user_id=user_id,
        email=data.get("email", ""),
        full_name=data.get("full_name"),
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        metadata=md,
    )


def clear_premium_session(home: Path | None = None) -> bool:
    """Wipe premium tokens from keyring + delete credentials.json.

    Returns True if anything was deleted.
    """
    creds_path = (home or DEFAULT_HOME) / "credentials.json"
    user_id: str | None = None
    if creds_path.exists():
        try:
            user_id = json.loads(creds_path.read_text()).get("user_id")
        except (json.JSONDecodeError, ValueError):
            pass

    keyring_cleared = False
    if user_id and KEYRING_AVAILABLE:
        try:
            _keyring.delete_password(KEYRING_SERVICE, f"{KEY_ACCESS}:{user_id}")
            _keyring.delete_password(KEYRING_SERVICE, f"{KEY_REFRESH}:{user_id}")
            keyring_cleared = True
        except Exception:  # noqa: BLE001
            # Item may not exist — ignore
            pass

    file_cleared = False
    if creds_path.exists():
        creds_path.unlink()
        file_cleared = True

    return keyring_cleared or file_cleared
