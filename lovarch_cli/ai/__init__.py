"""Lovarch AI gateway — routes CLI AI generation through the platform.

Every paid AI call the CLI makes in premium mode goes through the
``cli-ai-generate`` Edge Function so the user's Lovarch credits are debited by
the canonical rule (1000 credits = $1 of API cost). See ``gateway.py``.
"""
from lovarch_cli.ai.gateway import (
    AiGatewayError,
    AiImageResult,
    AiTextResult,
    InsufficientCreditsError,
    LovarchAiGateway,
)

__all__ = [
    "AiGatewayError",
    "AiImageResult",
    "AiTextResult",
    "InsufficientCreditsError",
    "LovarchAiGateway",
]
