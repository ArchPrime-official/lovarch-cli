"""Credits — Free mode no-op implementation.

Free users bring their own API keys; the CLI never debits Lovarch credits.
This client always reports an unlimited balance with `sufficient=True`.

Kept separate from base.py so the abstract module stays import-light and
free users don't accidentally pay the cost of importing httpx.
"""
from __future__ import annotations

from lovarch_cli.credits.base import CreditsBalance, CreditsClient

# Sentinel used as the "unlimited" balance value. Picked arbitrarily large
# (2^31 - 1) so any reasonable required threshold passes the check.
_UNLIMITED = 2_147_483_647


class FreeCreditsClient(CreditsClient):
    """No-op client — always reports unlimited credits.

    Free users supply their own provider keys (OpenAI, Mapbox), so the CLI
    has no balance to track. We still return a CreditsBalance shape so
    callers don't need to special-case Free vs Premium.
    """

    async def check(self, required: int | None = None) -> CreditsBalance:
        return CreditsBalance(
            balance=_UNLIMITED,
            monthly_used=0,
            credits_remaining=_UNLIMITED,
            is_admin=False,
            required=required,
            sufficient=True,
        )
