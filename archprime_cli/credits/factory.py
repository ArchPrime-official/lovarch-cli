"""Credits — backend factory."""
from __future__ import annotations

from archprime_cli.clients.persistence import ExecutionMode
from archprime_cli.credits.base import CreditsClient
from archprime_cli.credits.local import FreeCreditsClient


def get_credits_client(mode: ExecutionMode) -> CreditsClient:
    """Return the credits client matching the execution mode.

    Free mode returns a no-op client (always sufficient).
    Premium mode loads the keyring session and returns LovarchCreditsClient.

    Raises:
        RuntimeError: premium requested but no session in keyring.
    """
    if mode == ExecutionMode.FREE:
        return FreeCreditsClient()

    if mode == ExecutionMode.PREMIUM:
        # Lazy imports — Free flows shouldn't pay for httpx + Supabase modules.
        from archprime_cli.auth.session import LovarchSession
        from archprime_cli.credits.lovarch import LovarchCreditsClient

        session = LovarchSession.load()
        if session is None:
            msg = (
                "Premium credits check requires authentication. Run "
                "'arch login --premium' first."
            )
            raise RuntimeError(msg)
        return LovarchCreditsClient(session)

    msg = f"Unknown execution mode: {mode}"
    raise ValueError(msg)
