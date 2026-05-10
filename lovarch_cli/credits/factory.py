"""Credits — backend factory."""
from __future__ import annotations

from lovarch_cli.clients.persistence import ExecutionMode
from lovarch_cli.credits.base import CreditsClient
from lovarch_cli.credits.local import FreeCreditsClient


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
        from lovarch_cli.auth.session import LovarchSession
        from lovarch_cli.credits.lovarch import LovarchCreditsClient

        session = LovarchSession.load()
        if session is None:
            msg = (
                "Premium credits check requires authentication. Run "
                "'lovarch login --premium' first."
            )
            raise RuntimeError(msg)
        return LovarchCreditsClient(session)

    msg = f"Unknown execution mode: {mode}"
    raise ValueError(msg)
