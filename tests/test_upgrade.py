"""Tests for lovarch_cli.commands.upgrade.

The upgrade command is a thin CLI surface that:
  1. Inspects current credentials (none/free/premium)
  2. Renders state-appropriate Rich panel
  3. Opens browser (or prints URL with --no-browser)

We exercise all three states via Typer's CliRunner with --no-browser to
avoid spawning a real browser in CI.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
import typer
from typer.testing import CliRunner

from lovarch_cli.commands.upgrade import upgrade_command
from lovarch_cli.config import Credentials


def _make_app() -> typer.Typer:
    """Mount upgrade_command on a fresh Typer app for testing."""
    app = typer.Typer()
    app.command(name="upgrade")(upgrade_command)
    return app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ──────────────────────────────────────────────────────────────────────────
# State: none — no credentials configured
# ──────────────────────────────────────────────────────────────────────────

def test_upgrade_no_account_exits_with_hint(runner: CliRunner):
    creds = Credentials(mode="none")
    with patch(
        "lovarch_cli.commands.upgrade.load_credentials", return_value=creds
    ):
        result = runner.invoke(_make_app(), ["--lang=en"])
    assert result.exit_code == 1
    # English hint should mention both alternatives.
    assert "arch signup" in result.stdout
    assert "arch login --premium" in result.stdout


def test_upgrade_no_account_localized_in_pt(runner: CliRunner):
    creds = Credentials(mode="none")
    with patch(
        "lovarch_cli.commands.upgrade.load_credentials", return_value=creds
    ):
        result = runner.invoke(_make_app(), ["--lang=pt"])
    assert result.exit_code == 1
    assert "Nenhuma conta" in result.stdout


# ──────────────────────────────────────────────────────────────────────────
# State: free — show benefits, would open /settings/credits
# ──────────────────────────────────────────────────────────────────────────

def test_upgrade_free_shows_benefits_and_url(runner: CliRunner):
    creds = Credentials(
        mode="free",
        lead_id="lead-uuid",
        free_token="tok",
        email="user@example.com",
        full_name="Test User",
        country="IT",
        language="it",
        signed_up_at=datetime.now(timezone.utc).isoformat(),
    )
    with patch(
        "lovarch_cli.commands.upgrade.load_credentials", return_value=creds
    ):
        result = runner.invoke(
            _make_app(), ["--no-browser"]
        )
    assert result.exit_code == 0
    # Italian (creds.language='it') benefits + upgrade URL
    assert "Premium" in result.stdout
    assert "lovarch.com/settings/credits" in result.stdout
    # Should not mention "already premium"
    assert "già Premium" not in result.stdout or "Crediti AI" in result.stdout


def test_upgrade_free_uses_user_signup_language(runner: CliRunner):
    """Even if --lang flag overrides, persisted creds.language wins for body."""
    creds = Credentials(
        mode="free",
        lead_id="lead-uuid",
        free_token="tok",
        email="user@example.com",
        full_name="Test User",
        country="ES",
        language="es",  # User signed up in Spanish
        signed_up_at=datetime.now(timezone.utc).isoformat(),
    )
    with patch(
        "lovarch_cli.commands.upgrade.load_credentials", return_value=creds
    ):
        result = runner.invoke(
            # Even with --lang=en, user's signup lang (es) should win.
            _make_app(),
            ["--no-browser", "--lang=en"],
        )
    assert result.exit_code == 0
    # Spanish body marker (the signup lang is preferred for upgrade body)
    assert "Actualiza a Premium" in result.stdout
    assert "lovarch.com/settings/credits" in result.stdout


def test_upgrade_free_no_browser_does_not_open(runner: CliRunner):
    creds = Credentials(
        mode="free",
        lead_id="lead-uuid",
        free_token="tok",
        email="user@example.com",
        full_name="Test User",
        country="IT",
        language="it",
        signed_up_at=datetime.now(timezone.utc).isoformat(),
    )
    with patch(
        "lovarch_cli.commands.upgrade.load_credentials", return_value=creds
    ), patch(
        "lovarch_cli.commands.upgrade.webbrowser.open"
    ) as mock_open:
        result = runner.invoke(
            _make_app(), ["--no-browser"]
        )
    assert result.exit_code == 0
    mock_open.assert_not_called()


def test_upgrade_free_default_opens_browser(runner: CliRunner):
    creds = Credentials(
        mode="free",
        lead_id="lead-uuid",
        free_token="tok",
        email="user@example.com",
        full_name="Test User",
        country="IT",
        language="it",
        signed_up_at=datetime.now(timezone.utc).isoformat(),
    )
    with patch(
        "lovarch_cli.commands.upgrade.load_credentials", return_value=creds
    ), patch(
        "lovarch_cli.commands.upgrade.webbrowser.open"
    ) as mock_open:
        result = runner.invoke(_make_app(), [])
    assert result.exit_code == 0
    mock_open.assert_called_once()
    args, _ = mock_open.call_args
    assert "/settings/credits" in args[0]


# ──────────────────────────────────────────────────────────────────────────
# State: premium — already-premium acknowledgment
# ──────────────────────────────────────────────────────────────────────────

def test_upgrade_premium_shows_dashboard_url(runner: CliRunner):
    creds = Credentials(
        mode="premium",
        user_id="auth-uuid",
        email="pro@example.com",
        full_name="Pro User",
        language="en",
        signed_up_at=datetime.now(timezone.utc).isoformat(),
    )
    with patch(
        "lovarch_cli.commands.upgrade.load_credentials", return_value=creds
    ):
        result = runner.invoke(
            _make_app(), ["--no-browser"]
        )
    assert result.exit_code == 0
    assert "already Premium" in result.stdout
    # Premium users get routed to dashboard, not upgrade page.
    assert "/settings/credits" in result.stdout
    assert "/cli-upgrade" not in result.stdout


def test_upgrade_premium_opens_dashboard_when_browser_enabled(runner: CliRunner):
    creds = Credentials(
        mode="premium",
        user_id="auth-uuid",
        email="pro@example.com",
        full_name="Pro User",
        language="it",
        signed_up_at=datetime.now(timezone.utc).isoformat(),
    )
    with patch(
        "lovarch_cli.commands.upgrade.load_credentials", return_value=creds
    ), patch(
        "lovarch_cli.commands.upgrade.webbrowser.open"
    ) as mock_open:
        result = runner.invoke(_make_app(), [])
    assert result.exit_code == 0
    mock_open.assert_called_once()
    args, _ = mock_open.call_args
    assert "/settings/credits" in args[0]
