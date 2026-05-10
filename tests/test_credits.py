"""Tests for lovarch_cli.credits.

Covers:
- CreditsBalance dataclass: deficit math, sufficient flag interaction
- InsufficientCreditsError carries the balance
- FreeCreditsClient (no-op) always sufficient
- Factory routing: ExecutionMode.FREE → FreeCreditsClient
- check_or_raise success and failure paths

Premium-mode end-to-end (real EF call) is left for an integration test
marked @pytest.mark.premium — not run by default.
"""
from __future__ import annotations

import pytest

from lovarch_cli.clients.persistence import ExecutionMode
from lovarch_cli.credits import (
    CreditsBalance,
    InsufficientCreditsError,
    get_credits_client,
)
from lovarch_cli.credits.local import FreeCreditsClient


# ──────────────────────────────────────────────────────────────────────────
# CreditsBalance
# ──────────────────────────────────────────────────────────────────────────

def test_balance_deficit_zero_when_sufficient():
    bal = CreditsBalance(
        balance=10_000,
        monthly_used=2_000,
        credits_remaining=8_000,
        is_admin=False,
        required=5_000,
        sufficient=True,
    )
    assert bal.deficit == 0


def test_balance_deficit_zero_when_no_required():
    bal = CreditsBalance(
        balance=100,
        monthly_used=50,
        credits_remaining=50,
        is_admin=False,
        required=None,
        sufficient=True,
    )
    assert bal.deficit == 0


def test_balance_deficit_nonzero_when_insufficient():
    bal = CreditsBalance(
        balance=1_000,
        monthly_used=500,
        credits_remaining=500,
        is_admin=False,
        required=3_500,
        sufficient=False,
    )
    assert bal.deficit == 3_000


def test_admin_deficit_zero_even_with_required():
    bal = CreditsBalance(
        balance=0,
        monthly_used=0,
        credits_remaining=0,
        is_admin=True,
        required=10_000,
        sufficient=True,  # server flips sufficient=True for admins
    )
    assert bal.deficit == 0


# ──────────────────────────────────────────────────────────────────────────
# InsufficientCreditsError
# ──────────────────────────────────────────────────────────────────────────

def test_error_carries_balance():
    bal = CreditsBalance(
        balance=100,
        monthly_used=50,
        credits_remaining=50,
        is_admin=False,
        required=3_500,
        sufficient=False,
    )
    err = InsufficientCreditsError(bal)
    assert err.balance is bal
    msg = str(err)
    assert "50" in msg  # credits_remaining
    assert "3500" in msg  # required


# ──────────────────────────────────────────────────────────────────────────
# FreeCreditsClient
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_free_client_always_sufficient_no_required():
    client = FreeCreditsClient()
    bal = await client.check()
    assert bal.sufficient is True
    assert bal.required is None
    assert bal.credits_remaining > 0


@pytest.mark.asyncio
async def test_free_client_sufficient_with_huge_required():
    client = FreeCreditsClient()
    # Even a million-credit pipeline should pass for Free users.
    bal = await client.check(required=1_000_000)
    assert bal.sufficient is True
    assert bal.required == 1_000_000


@pytest.mark.asyncio
async def test_free_client_check_or_raise_passes():
    client = FreeCreditsClient()
    bal = await client.check_or_raise(required=999_999)
    assert bal.sufficient is True


# ──────────────────────────────────────────────────────────────────────────
# Factory routing
# ──────────────────────────────────────────────────────────────────────────

def test_factory_free_returns_free_client():
    client = get_credits_client(ExecutionMode.FREE)
    assert isinstance(client, FreeCreditsClient)


def test_factory_unknown_mode_raises():
    # Bypass the enum constraint by passing a sentinel string;
    # the factory should reject unknown values.
    with pytest.raises(ValueError, match="Unknown execution mode"):
        get_credits_client("carrier_pigeon")  # type: ignore[arg-type]


def test_factory_premium_without_session_raises(monkeypatch, tmp_path):
    """Premium mode without keyring session must raise RuntimeError."""
    # Force LovarchSession.load() to return None by clearing keyring + falling
    # back to a temp credentials path.
    monkeypatch.setenv("HOME", str(tmp_path))
    # Block keyring so it doesn't surface a real session
    monkeypatch.setattr(
        "lovarch_cli.auth.keyring_store.load_premium_session",
        lambda: None,
    )
    with pytest.raises(RuntimeError, match="arch login --premium"):
        get_credits_client(ExecutionMode.PREMIUM)


# ──────────────────────────────────────────────────────────────────────────
# check_or_raise failure path (mocked Lovarch client)
# ──────────────────────────────────────────────────────────────────────────

class _StubInsufficientClient(FreeCreditsClient):
    """Stub that always reports insufficient credits."""

    async def check(self, required=None):
        return CreditsBalance(
            balance=100,
            monthly_used=80,
            credits_remaining=20,
            is_admin=False,
            required=required,
            sufficient=False,
        )


@pytest.mark.asyncio
async def test_check_or_raise_raises_when_insufficient():
    client = _StubInsufficientClient()
    with pytest.raises(InsufficientCreditsError) as exc_info:
        await client.check_or_raise(required=3_500)
    assert exc_info.value.balance.credits_remaining == 20
    assert exc_info.value.balance.deficit == 3_480
