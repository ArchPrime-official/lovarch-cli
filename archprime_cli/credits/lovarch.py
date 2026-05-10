"""Credits — Premium mode implementation backed by cli-credits-check EF."""
from __future__ import annotations

from typing import TYPE_CHECKING

from archprime_cli.credits.base import CreditsBalance, CreditsClient

if TYPE_CHECKING:
    from archprime_cli.auth.session import LovarchSession


class LovarchCreditsClient(CreditsClient):
    """Calls the `cli-credits-check` Edge Function with the premium Bearer.

    Uses LovarchSession's auto-refresh-on-401 request method, so a near-
    expired access_token is handled transparently.
    """

    def __init__(self, session: "LovarchSession") -> None:
        self._session = session

    async def check(self, required: int | None = None) -> CreditsBalance:
        body: dict[str, int] = {}
        if required is not None:
            body["required"] = int(required)

        # session.request normalizes URL + injects Bearer + handles 401 refresh.
        # cli-credits-check is at /functions/v1/cli-credits-check.
        path = "/functions/v1/cli-credits-check"
        response = await self._session.request("POST", path, json=body)

        if response.status_code != 200:
            # Try to surface server-localized message when present.
            try:
                payload = response.json()
            except ValueError:
                payload = {}
            msg = payload.get("message") or response.text[:200]
            raise RuntimeError(
                f"cli-credits-check failed (HTTP {response.status_code}): {msg}"
            )

        data = response.json()
        if data.get("ok") is not True:
            raise RuntimeError(
                f"cli-credits-check error: {data.get('error', 'unknown')}"
            )

        return CreditsBalance(
            balance=int(data.get("balance", 0)),
            monthly_used=int(data.get("monthly_used", 0)),
            credits_remaining=int(data.get("credits_remaining", 0)),
            is_admin=bool(data.get("is_admin", False)),
            required=data.get("required"),
            sufficient=bool(data.get("sufficient", False)),
        )
