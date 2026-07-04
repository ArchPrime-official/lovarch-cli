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
CLI_AI_TEXT_PATH = "/functions/v1/cli-ai-text"
CLI_DATA_PATH = "/functions/v1/cli-data"
# Image generation with gpt-image-2 can take 10-60s; give it generous headroom.
_IMAGE_TIMEOUT = 200.0
_TEXT_TIMEOUT = 300.0

Quality = Literal["low", "medium", "high"]
Mode = Literal["generate", "edit"]
Role = Literal["executor", "verifier", "chief"]


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
    """Result of a successful image generation via the platform gateway.

    Cost is expressed ONLY in the user's credits — provider amounts never
    reach the client.
    """

    image_bytes: bytes
    content_type: str
    revised_prompt: str | None
    credits_charged: int
    balance: int | None
    is_admin: bool


@dataclass
class AiTextResult:
    """Result of a successful text generation via cli-ai-text."""

    text: str
    model: str
    input_tokens: int
    output_tokens: int
    credits_charged: int
    balance: int | None
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
            is_admin=bool(data.get("is_admin", False)),
        )

    async def generate_text(
        self,
        prompt: str | None = None,
        *,
        messages: list[dict] | None = None,
        role: Role = "executor",
        model: str | None = None,
        system: str | None = None,
        max_tokens: int | None = None,
        language: str | None = None,
        operation_type: str | None = None,
    ) -> AiTextResult:
        """Generate text via cli-ai-text, debiting the user's credits.

        Model selection is server-side: pass a ``role`` (executor|verifier|
        chief) for the platform default, or an explicit ``model`` from the
        platform catalog. ``language`` enforces strict output language.
        """
        body: dict[str, object] = {}
        if model:
            body["model"] = model
        else:
            body["role"] = role
        if prompt:
            body["prompt"] = prompt
        if messages:
            body["messages"] = messages
        if system:
            body["system"] = system
        if max_tokens:
            body["max_tokens"] = max_tokens
        if language:
            body["language"] = language
        if operation_type:
            body["operation_type"] = operation_type

        response = await self._session.request(
            "POST", CLI_AI_TEXT_PATH, json=body, timeout=_TEXT_TIMEOUT
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
                f"cli-ai-text ha risposto {response.status_code}: {detail or 'errore sconosciuto'}"
            )

        usage = data.get("usage") or {}
        return AiTextResult(
            text=str(data.get("text", "")),
            model=str(data.get("model", "")),
            input_tokens=int(usage.get("input_tokens", 0) or 0),
            output_tokens=int(usage.get("output_tokens", 0) or 0),
            credits_charged=int(data.get("credits_charged", 0) or 0),
            balance=data.get("balance"),
            is_admin=bool(data.get("is_admin", False)),
        )

    async def get_user_context(self, lead_id: str | None = None) -> dict:
        """Fetch the personalization bundle (cli-user-context).

        Returns the raw bundle dict — brand, style, fiscal, signature_line,
        preferences (incl. mandatory output language) and ``prompt_block``
        ready to prepend to any agent prompt.
        """
        body: dict[str, object] = {}
        if lead_id:
            body["lead_id"] = lead_id
        response = await self._session.request(
            "POST", "/functions/v1/cli-user-context", json=body, timeout=60.0
        )
        try:
            data = response.json()
        except ValueError:
            data = {}
        if response.status_code != 200 or not data.get("ok"):
            detail = data.get("error") if isinstance(data, dict) else None
            raise AiGatewayError(
                f"cli-user-context ha risposto {response.status_code}: {detail or 'errore sconosciuto'}"
            )
        return data

    async def data(self, resource: str, **params: object) -> dict:
        """Read the user's own Lovarch data / save deliverables (cli-data).

        Resources: media_list, media_get, worlds_list, cad_list, projects_list,
        project_get, financial_summary, contracts_list, leads_list, prezzario,
        deliverable_save, deliverable_download. All owner-scoped server-side.
        """
        body: dict[str, object] = {"resource": resource, **params}
        response = await self._session.request(
            "POST", CLI_DATA_PATH, json=body, timeout=120.0
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if response.status_code != 200 or not payload.get("ok"):
            detail = payload.get("error") if isinstance(payload, dict) else None
            raise AiGatewayError(
                f"cli-data/{resource} ha risposto {response.status_code}: {detail or 'errore sconosciuto'}"
            )
        return payload

    async def platform(
        self, function: str, body: dict, *, timeout: float = 180.0
    ) -> dict:
        """Call a platform EF (aps-cad, worldlabs-world) with the session token.

        Raises ``InsufficientCreditsError`` on 402; ``AiGatewayError`` otherwise.
        """
        response = await self._session.request(
            "POST", f"/functions/v1/{function}", json=body, timeout=timeout
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if response.status_code == 402:
            raise InsufficientCreditsError(
                available=int(payload.get("credits_available", 0) or 0),
                needed=int(payload.get("credits_needed", 0) or 0),
            )
        if response.status_code != 200 or not payload.get("ok"):
            detail = payload.get("error") if isinstance(payload, dict) else None
            raise AiGatewayError(
                f"{function} ha risposto {response.status_code}: {detail or 'errore sconosciuto'}"
            )
        return payload
