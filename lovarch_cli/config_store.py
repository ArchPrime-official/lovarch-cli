"""User config store — ~/.lovarch/config.json.

Holds non-secret preferences (language, storage path) and, for FREE mode, the
student's own provider API keys (OpenAI, Mapbox) — legacy free-mode keys
can pick them up without exporting shell env vars. Premium mode never needs
these — paid AI is debited via the platform.

Secret values are stored chmod 0600 and masked when displayed.
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

from lovarch_cli.config import DEFAULT_HOME

# Allowed keys and whether each is secret (masked on display).
CONFIG_KEYS: dict[str, bool] = {
    "language": False,      # it | en | pt | es
    "storage_path": False,  # where free-mode projects live (default ~/.lovarch/projects)
    "openai_key": True,     # BYO key for free mode
    "mapbox_token": True,   # BYO token for free mode (geocoding)
}

_VALID_LANGS = {"it", "en", "pt", "es"}


class ConfigError(Exception):
    """Invalid config key or value."""


def config_path(home: Path | None = None) -> Path:
    return (home or DEFAULT_HOME) / "config.json"


def load_config(home: Path | None = None) -> dict[str, Any]:
    path = config_path(home)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, ValueError, OSError):
        return {}


def _save_config(data: dict[str, Any], home: Path | None = None) -> Path:
    path = config_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    # Config may hold BYO API keys → keep it private.
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0600
    except OSError:
        pass
    return path


def _validate(key: str, value: str) -> str:
    if key not in CONFIG_KEYS:
        raise ConfigError(
            f"Chiave sconosciuta: '{key}'. Valide: {', '.join(sorted(CONFIG_KEYS))}."
        )
    if key == "language" and value not in _VALID_LANGS:
        raise ConfigError(f"Lingua non valida: '{value}'. Valide: it, en, pt, es.")
    if not value:
        raise ConfigError("Il valore non può essere vuoto (usa `unset` per rimuovere).")
    return value


def set_value(key: str, value: str, home: Path | None = None) -> None:
    value = _validate(key, value)
    data = load_config(home)
    data[key] = value
    _save_config(data, home)


def get_value(key: str, home: Path | None = None) -> Any:
    if key not in CONFIG_KEYS:
        raise ConfigError(f"Chiave sconosciuta: '{key}'.")
    return load_config(home).get(key)


def unset_value(key: str, home: Path | None = None) -> bool:
    if key not in CONFIG_KEYS:
        raise ConfigError(f"Chiave sconosciuta: '{key}'.")
    data = load_config(home)
    if key in data:
        del data[key]
        _save_config(data, home)
        return True
    return False


def mask(key: str, value: Any) -> str:
    """Mask secret values for display (show only the last 4 chars)."""
    if value is None:
        return "—"
    text = str(value)
    if CONFIG_KEYS.get(key) and len(text) > 4:
        return "•" * (len(text) - 4) + text[-4:]
    return text


def display_items(home: Path | None = None) -> list[tuple[str, str, bool]]:
    """Return (key, masked_value, is_secret) for every known key."""
    data = load_config(home)
    return [(k, mask(k, data.get(k)), CONFIG_KEYS[k]) for k in CONFIG_KEYS]
