"""archprime-cli — HTTP client wrapper for Lovarch API.

Thin httpx wrapper that adds:
- Default API URL (overridable via LOVARCH_API_URL env)
- Anon key as default header (for public EFs like cli-signup)
- Bearer token injection for authenticated calls (premium)
- Error normalization to LovarchApiError
- Timeout defaults (30s connect, 120s read for long EFs)

For EF endpoints, the URL pattern is:
    {API_URL}/functions/v1/{ef_name}
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from archprime_cli.config import DEFAULT_API_ANON_KEY, DEFAULT_API_URL
from archprime_cli.i18n import t


class LovarchApiError(Exception):
    """Normalized error from Lovarch API calls."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_code: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.payload = payload or {}


@dataclass
class ApiClient:
    """HTTP client for Lovarch Supabase APIs (REST + Edge Functions)."""

    base_url: str = DEFAULT_API_URL
    anon_key: str = DEFAULT_API_ANON_KEY
    bearer_token: str | None = None
    timeout_connect: float = 30.0
    timeout_read: float = 120.0

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "archprime-cli/0.1.0",
        }
        if self.anon_key:
            headers["apikey"] = self.anon_key
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        elif self.anon_key:
            headers["Authorization"] = f"Bearer {self.anon_key}"
        return headers

    async def invoke_ef(
        self,
        function_name: str,
        body: dict[str, Any],
        bearer_token: str | None = None,
    ) -> dict[str, Any]:
        """Call a Supabase Edge Function and return its parsed JSON response.

        Raises LovarchApiError on HTTP errors or `{ok: false}` body.
        """
        url = f"{self.base_url}/functions/v1/{function_name}"
        headers = self._headers()
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"

        timeout = httpx.Timeout(self.timeout_read, connect=self.timeout_connect)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=body, headers=headers)
        except httpx.RequestError as exc:
            msg = t("errors.network", function_name=function_name, exc=str(exc))
            raise LovarchApiError(msg) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            msg = t(
                "errors.invalid_json",
                function_name=function_name,
                status_code=response.status_code,
                snippet=response.text[:200],
            )
            raise LovarchApiError(msg, status_code=response.status_code) from exc

        if response.status_code >= 400 or payload.get("ok") is False:
            error_code = payload.get("error", "unknown_error")
            # Server-localized message wins; otherwise build a localized fallback.
            message = payload.get("message") or t(
                "errors.unknown_api_error", error_code=error_code
            )
            raise LovarchApiError(
                message=message,
                status_code=response.status_code,
                error_code=error_code,
                payload=payload,
            )

        return payload
