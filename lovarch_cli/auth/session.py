"""LovarchSession — manages Supabase access/refresh tokens with auto-refresh.

Wraps httpx and the Supabase /auth/v1/token endpoint to:
- Inject Authorization: Bearer {access_token} on every call
- Detect 401 responses and automatically refresh tokens
- Persist refreshed tokens back to OS keyring + credentials.json
- Surface fatal errors (refresh failed) so callers can prompt re-login

Used by LovarchSupabaseClient (DataPersistenceClient impl) and
LovarchStorage (StorageClient impl). NOT used by free-mode clients.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from lovarch_cli.auth.keyring_store import (
    PremiumSession,
    load_premium_session,
    save_premium_session,
)
from lovarch_cli.config import DEFAULT_API_ANON_KEY, DEFAULT_API_URL


class LovarchSessionError(Exception):
    """Raised when token refresh fails permanently — caller should re-login."""


@dataclass
class _RefreshResult:
    access_token: str
    refresh_token: str
    expires_in: int


class LovarchSession:
    """Holds + auto-refreshes a Supabase user session."""

    def __init__(
        self,
        session: PremiumSession,
        api_url: str = DEFAULT_API_URL,
        anon_key: str = DEFAULT_API_ANON_KEY,
    ) -> None:
        self._session = session
        self._api_url = api_url.rstrip("/")
        self._anon_key = anon_key
        self._refresh_lock = asyncio.Lock()

    # ─── Public load/save helpers ─────────────────────────────────────────

    @classmethod
    def load(cls) -> "LovarchSession | None":
        """Load from keyring + credentials.json, return None if no session."""
        ps = load_premium_session()
        if ps is None:
            return None
        return cls(ps)

    @property
    def user_id(self) -> str:
        return self._session.user_id

    @property
    def email(self) -> str:
        return self._session.email

    @property
    def access_token(self) -> str:
        return self._session.access_token

    # ─── HTTP request with auto-refresh ───────────────────────────────────

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        timeout: float = 60.0,
    ) -> httpx.Response:
        """Perform HTTP request with Authorization injected; refresh on 401."""
        url = f"{self._api_url}{path}" if path.startswith("/") else path

        merged_headers: dict[str, str] = {
            "User-Agent": "lovarch-cli/0.1.0",
            "apikey": self._anon_key,
            "Authorization": f"Bearer {self._session.access_token}",
        }
        if headers:
            merged_headers.update(headers)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method,
                url,
                params=params,
                json=json,
                headers=merged_headers,
                content=content,
            )

            if response.status_code != 401:
                return response

            # ─── Try refresh + retry once ────────────────────────────────
            try:
                await self._refresh()
            except LovarchSessionError:
                return response  # bubble original 401 to caller

            merged_headers["Authorization"] = f"Bearer {self._session.access_token}"
            response = await client.request(
                method,
                url,
                params=params,
                json=json,
                headers=merged_headers,
                content=content,
            )
            return response

    # ─── Refresh logic ────────────────────────────────────────────────────

    async def _refresh(self) -> None:
        """Refresh access_token using refresh_token. Persist on success."""
        async with self._refresh_lock:
            url = f"{self._api_url}/auth/v1/token?grant_type=refresh_token"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json={"refresh_token": self._session.refresh_token},
                    headers={
                        "apikey": self._anon_key,
                        "Content-Type": "application/json",
                    },
                )

            if response.status_code >= 400:
                msg = (
                    f"Token refresh failed: HTTP {response.status_code} "
                    f"{response.text[:200]}"
                )
                raise LovarchSessionError(msg)

            try:
                data = response.json()
            except ValueError as exc:
                raise LovarchSessionError(
                    f"Invalid JSON from refresh endpoint: {exc}"
                ) from exc

            access = data.get("access_token")
            refresh = data.get("refresh_token") or self._session.refresh_token
            expires_in = int(data.get("expires_in", 3600))

            if not access:
                raise LovarchSessionError("Refresh response missing access_token")

            new_expires = (
                datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            ).isoformat(timespec="seconds")

            # Update in-memory + persist
            self._session = PremiumSession(
                user_id=self._session.user_id,
                email=self._session.email,
                full_name=self._session.full_name,
                access_token=access,
                refresh_token=refresh,
                expires_at=new_expires,
                metadata=self._session.metadata,
            )
            save_premium_session(
                user_id=self._session.user_id,
                email=self._session.email,
                full_name=self._session.full_name,
                access_token=access,
                refresh_token=refresh,
                expires_at=new_expires,
                language=self._session.metadata.get("language", "it"),
            )
