"""Client for the ``cli-ai-generate`` Edge Function.

This is the ONLY path the premium CLI (and the future MCP server) should use to
run paid image generation. It forces the call through the Lovarch platform,
which debits the authenticated user's credits by the 1000cr=$1 rule and refunds
on failure. The CLI must never call OpenAI/Mapbox/etc. directly in premium mode
— doing so bypasses the credit system.

Returns the generated image as raw bytes for the caller to persist (Fase 2 adds
server-side Storage persistence tied to the user's Lovarch account).
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Literal

from lovarch_cli.auth.session import LovarchSession

CLI_AI_GENERATE_PATH = "/functions/v1/cli-ai-generate"
# Image generation with gpt-image-2 can take 10-60s; give it generous headroom.
_IMAGE_TIMEOUT = 200.0

Quality = Literal["low", "medium", "high"]
Mode = Literal["generate", "edit"]


class AiGatewayError(Exception):
    """Generic failure calling cli-ai-generate."""


class InsufficientCreditsError(AiGatewayError):
    """The user does not have enough credits for the requested operation."""

    def __init__(self, available: int, needed: int) -> None:
        self.available = available
        self.needed = needed
        super().__init__(
            f"Crediti insufficienti: disponibili {available}, richiesti {needed}."
        )


@dataclass
class AiImageResult:
    """Result of a successful image generation via the platform gateway."""

    image_bytes: bytes
    content_type: str
    revised_prompt: str | None
    credits_charged: int
    balance: int | None
    cost_usd: float
    is_admin: bool


def _decode_data_url(data_url: str) -> tuple[bytes, str]:
    """Split a ``data:<mime>;base64,<payload>`` URL into (bytes, content_type)."""
    if not data_url.startswith("data:"):
        raise AiGatewayError("Risposta immagine non è un data URL.")
    header, _, payload = data_url.partition(",")
    if not payload:
        raise AiGatewayError("Risposta immagine senza payload base64.")
    content_type = header[len("data:") :].split(";")[0] or "image/png"
    try:
        return base64.b64decode(payload), content_type
    except (ValueError, TypeError) as exc:  # pragma: no cover - defensive
        raise AiGatewayError(f"Base64 immagine non valido: {exc}") from exc


class LovarchAiGateway:
    """Thin client over ``cli-ai-generate`` bound to a premium session."""

    def __init__(self, session: LovarchSession) -> None:
        self._session = session

    async def generate_image(
        self,
        prompt: str,
        *,
        quality: Quality = "medium",
        aspect: str = "1:1",
        mode: Mode = "generate",
        image_urls: list[str] | None = None,
        operation_type: str | None = None,
    ) -> AiImageResult:
        """Generate (or edit) an image via the platform, debiting credits.

        Raises ``InsufficientCreditsError`` on HTTP 402 and ``AiGatewayError``
        on any other non-success response.
        """
        body: dict[str, object] = {
            "mode": mode,
            "prompt": prompt,
            "quality": quality,
            "aspect": aspect,
        }
        if image_urls:
            body["image_urls"] = image_urls
        if operation_type:
            body["operation_type"] = operation_type

        response = await self._session.request(
            "POST", CLI_AI_GENERATE_PATH, json=body, timeout=_IMAGE_TIMEOUT
        )

        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.status_code == 402:
            raise InsufficientCreditsError(
                available=int(data.get("credits_available", 0) or 0),
                needed=int(data.get("credits_needed", 0) or 0),
            )

        if response.status_code != 200 or not data.get("ok"):
            detail = data.get("error") if isinstance(data, dict) else None
            raise AiGatewayError(
                f"cli-ai-generate ha risposto {response.status_code}: {detail or 'errore sconosciuto'}"
            )

        image_bytes, content_type = _decode_data_url(str(data.get("image_base64", "")))
        return AiImageResult(
            image_bytes=image_bytes,
            content_type=content_type,
            revised_prompt=data.get("revised_prompt"),
            credits_charged=int(data.get("credits_charged", 0) or 0),
            balance=data.get("balance"),
            cost_usd=float(data.get("cost_usd", 0.0) or 0.0),
            is_admin=bool(data.get("is_admin", False)),
        )
