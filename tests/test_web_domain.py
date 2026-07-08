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


# Paths that returned 404 in the 2026-07-08 link audit — must never come back.
# Real pages: /settings/credits (credits+upgrade), /terms-of-service (ToS),
# /settings (account). /corso does not exist anywhere.
DEAD_PATHS = (
    "app.lovarch.com/cli-upgrade",
    "app.lovarch.com/credits",  # bare; real page is /settings/credits
    "app.lovarch.com/legal/cli-tos",
    "app.lovarch.com/settings/account/delete",
    "/corso",
)


def test_translations_have_no_dead_paths():
    for f in I18N_DIR.glob("*.json"):
        raw = f.read_text(encoding="utf-8")
        json.loads(raw)  # still valid JSON
        for dead in DEAD_PATHS:
            assert dead not in raw, f"{f.name} still references dead path {dead}"


def test_signup_tos_and_upgrade_paths_are_live():
    from lovarch_cli.commands import signup, upgrade

    src = Path(signup.__file__).read_text(encoding="utf-8")
    assert "legal/cli-tos" not in src
    assert "lovarch.com/terms-of-service" in src
    assert upgrade.UPGRADE_PATH == "/settings/credits"
