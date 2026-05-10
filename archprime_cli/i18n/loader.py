"""i18n string loader — reads bundled JSON translations and provides t()."""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

log = logging.getLogger("archprime_cli.i18n")

VALID_LANGUAGES: tuple[str, ...] = ("it", "pt", "en", "es")
DEFAULT_LANGUAGE = "it"
FALLBACK_CHAIN = ("it", "en")  # tried in order if key missing in requested lang

_TRANSLATIONS_DIR = Path(__file__).parent / "translations"

# Module-level mutable holder for the active language. Set by cli.py at
# startup via set_current_lang() based on the --lang flag.
_current_lang: str | None = None


@lru_cache(maxsize=4)
def _load_translations(lang: str) -> dict[str, Any]:
    """Load a translations JSON from bundled package data."""
    path = _TRANSLATIONS_DIR / f"{lang}.json"
    if not path.exists():
        log.warning("i18n: translations file missing: %s", path)
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("i18n: failed to load %s: %s", path, exc)
        return {}


def _detect_from_env() -> str:
    """Detect language from environment variables only."""
    arch_lang = os.environ.get("ARCHPRIME_LANG", "").lower().strip()
    if arch_lang in VALID_LANGUAGES:
        return arch_lang
    sys_lang = os.environ.get("LANG", "").split("_")[0].lower()
    if sys_lang in VALID_LANGUAGES:
        return sys_lang
    return DEFAULT_LANGUAGE


def current_lang() -> str:
    """Return the active language for translation lookups."""
    global _current_lang
    if _current_lang is None:
        _current_lang = _detect_from_env()
    return _current_lang


def set_current_lang(lang: str | None) -> str:
    """Override the active language (used by --lang flag at CLI start).

    Pass None to reset to env-based detection on next current_lang() call.
    Returns the resolved language (after validation/normalization).
    """
    global _current_lang
    if lang is None:
        _current_lang = None
        return current_lang()
    normalized = lang.lower().strip()
    if normalized not in VALID_LANGUAGES:
        log.warning(
            "i18n: invalid lang override %r — falling back to env detection",
            lang,
        )
        _current_lang = None
        return current_lang()
    _current_lang = normalized
    return normalized


def _lookup(key: str, lang: str) -> str | None:
    """Walk dotted key (e.g. 'signup.welcome_title') in nested dict."""
    data = _load_translations(lang)
    parts = key.split(".")
    node: Any = data
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    if isinstance(node, str):
        return node
    return None


def t(key: str, lang: str | None = None, **vars: Any) -> str:
    """Translate a key to the target language with fallback chain.

    Args:
        key: dotted key path (e.g. 'signup.welcome_title')
        lang: optional override; defaults to current_lang()
        vars: optional Python-format vars (e.g. t('cli.greet', name='Pablo'))

    Returns:
        Translated string, or the key itself if missing in all fallback langs
        (so the developer can spot missing translations visually).
    """
    target = lang or current_lang()
    chain = (target, *(L for L in FALLBACK_CHAIN if L != target))
    value: str | None = None
    for candidate in chain:
        value = _lookup(key, candidate)
        if value is not None:
            break
    if value is None:
        log.warning("i18n: missing key %r in all langs %s", key, chain)
        return key
    if vars:
        try:
            return value.format(**vars)
        except (KeyError, IndexError) as exc:
            log.warning("i18n: format error for key %r vars %r: %s", key, vars, exc)
            return value
    return value
