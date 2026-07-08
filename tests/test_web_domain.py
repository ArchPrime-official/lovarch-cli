"""Regression: the CLI's browser redirects must target the APP domain
(app.lovarch.com), not the marketing site (lovarch.com).

Guards against the bug where `lovarch login` opened lovarch.com/cli-auth.
"""
from __future__ import annotations

import json
from pathlib import Path

from lovarch_cli.config import DEFAULT_WEB_URL

I18N_DIR = Path(__file__).resolve().parents[1] / "lovarch_cli" / "i18n" / "translations"


def test_default_web_url_is_app_domain():
    assert DEFAULT_WEB_URL == "https://app.lovarch.com"


def test_login_uses_app_domain():
    from lovarch_cli.commands import login

    assert login.LOVARCH_WEB_BASE == "https://app.lovarch.com"


def test_upgrade_uses_app_domain():
    from lovarch_cli.commands import upgrade

    assert upgrade.LOVARCH_WEB_BASE == "https://app.lovarch.com"
    assert (upgrade.LOVARCH_WEB_BASE + upgrade.PREMIUM_DASHBOARD_PATH).startswith(
        "https://app.lovarch.com/"
    )


def test_env_override(monkeypatch):
    import importlib

    monkeypatch.setenv("LOVARCH_WEB_URL", "https://staging.lovarch.com")
    import lovarch_cli.config as config

    importlib.reload(config)
    try:
        assert config.DEFAULT_WEB_URL == "https://staging.lovarch.com"
    finally:
        monkeypatch.delenv("LOVARCH_WEB_URL", raising=False)
        importlib.reload(config)


def test_no_bare_marketing_domain_in_translations():
    # No user-facing string should point to the bare marketing domain for
    # app pages — everything moved to app.lovarch.com.
    for f in I18N_DIR.glob("*.json"):
        raw = f.read_text(encoding="utf-8")
        json.loads(raw)  # still valid JSON
        assert "https://lovarch.com" not in raw, f"{f.name} still references lovarch.com"
