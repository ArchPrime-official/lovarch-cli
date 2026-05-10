"""Credits — pre-flight balance check for Premium pipelines.

Free mode users bring their own API keys (OpenAI, Mapbox, etc.) — they pay
their providers directly, so the CLI never debits credits. The Free client
is a no-op that always returns an "unlimited" balance.

Premium users pay via Lovarch credits. Before starting a long pipeline
(`arch run dal-brief-al-cantiere` consumes ~3,500 credits typical), we hit
the `cli-credits-check` Edge Function to verify the user has enough headroom
and abort EARLY with a clear message rather than failing mid-pipeline.

Usage:
    from lovarch_cli.credits import (
        InsufficientCreditsError,
        get_credits_client,
    )

    client = get_credits_client(mode)
    balance = await client.check(required=3500)
    if not balance.sufficient:
        raise InsufficientCreditsError(balance)
"""
from lovarch_cli.credits.base import (
    CreditsBalance,
    CreditsClient,
    InsufficientCreditsError,
)
from lovarch_cli.credits.factory import get_credits_client

__all__ = [
    "CreditsBalance",
    "CreditsClient",
    "InsufficientCreditsError",
    "get_credits_client",
]
