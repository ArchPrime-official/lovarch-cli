"""Wrappers over Lovarch platform Edge Functions (Render Studio, branding,
contents). First batch of the TOP-12 catalog: render, colors, copy.

Design rules (Pablo, 2026-07-03):
- Cost is the USER's credits, debited server-side by each EF — never expose
  provider amounts. Wrappers report outputs; balance can be read via
  `lovarch credits`.
- Output language follows the user's configured language — every call takes an
  explicit ``language`` that callers should source from cli-user-context.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lovarch_cli.auth.session import LovarchSession

# Render generation regularly takes 30-120s (image models).
_RENDER_TIMEOUT = 300.0
_DEFAULT_TIMEOUT = 120.0

RENDER_MODES = {
    None,             # legacy sketch/text → render (2D)
    "room_render",    # 3D room render
    "render_3d",
    "plan_to_3d",     # 2D plan → 3D
    "lighting_only",
    "closeup_detail",
    "closeup_angle",
}
COLOR_STYLES = {"modern", "vintage", "natural", "bold", "custom"}
COPY_MODES = {"post", "story", "carousel"}


class WorkflowError(Exception):
    """A platform workflow call failed (message is user-safe)."""


@dataclass
class RenderResult:
    image_bytes: bytes | None   # decoded when the EF returns a data URL
    image_url: str | None       # set when the EF returns a hosted URL
    message: str | None


class PlatformWorkflows:
    """Platform feature calls bound to a premium session."""

    def __init__(self, session: LovarchSession) -> None:
        self._session = session

    async def _invoke(
        self, ef: str, body: dict, *, timeout: float = _DEFAULT_TIMEOUT
    ) -> dict:
        response = await self._session.request(
            "POST", f"/functions/v1/{ef}", json=body, timeout=timeout
        )
        try:
            data = response.json()
        except ValueError:
            data = {}
        if response.status_code == 402:
            raise WorkflowError(
                "Crediti insufficienti per questa operazione. "
                f"(disponibili: {data.get('credits_available', '?')}, "
                f"richiesti: {data.get('credits_needed', '?')})"
            )
        if response.status_code != 200:
            detail = data.get("error") if isinstance(data, dict) else None
            raise WorkflowError(f"{ef}: {detail or f'HTTP {response.status_code}'}")
        return data if isinstance(data, dict) else {}

    # ── Render Studio ──────────────────────────────────────────────────────

    async def render(
        self,
        description: str,
        *,
        mode: str | None = None,
        render_style: str = "moderno",
        aspect_ratio: str = "16:9",
        reference_image_path: str | Path | None = None,
        language: str = "it",
    ) -> RenderResult:
        """Photorealistic render via render-ai-generate.

        ``mode=None`` = sketch/text→render (2D). ``room_render``/``plan_to_3d``
        = 3D modes (higher credit cost, debited server-side). A reference image
        (sketch, photo, plan) is sent base64-inline when provided.
        """
        if mode not in RENDER_MODES:
            raise WorkflowError(
                f"Modo render non valido: {mode}. Validi: "
                + ", ".join(sorted(m or "(default)" for m in RENDER_MODES))
            )
        body: dict[str, Any] = {
            "description": description,
            "renderStyle": render_style,
            "aspectRatio": aspect_ratio,
            "language": language,
        }
        if mode:
            body["mode"] = mode
        if reference_image_path:
            raw = Path(reference_image_path).expanduser().read_bytes()
            body["referenceImage"] = (
                "data:image/png;base64," + base64.b64encode(raw).decode()
            )
        data = await self._invoke("render-ai-generate", body, timeout=_RENDER_TIMEOUT)
        image = data.get("image")
        if not image:
            raise WorkflowError("render-ai-generate non ha restituito un'immagine.")
        if isinstance(image, str) and image.startswith("data:"):
            payload = image.split(",", 1)[1]
            return RenderResult(
                image_bytes=base64.b64decode(payload),
                image_url=None,
                message=data.get("message"),
            )
        return RenderResult(image_bytes=None, image_url=str(image), message=data.get("message"))

    # ── Branding: color palette ────────────────────────────────────────────

    async def colors(
        self,
        *,
        style: str = "modern",
        base_colors: list[str] | None = None,
        image_url: str | None = None,
        language: str = "it",
    ) -> dict:
        """Color palette via colors-generate. With ``image_url`` the palette is
        extracted from the image; otherwise generated from style/base colors."""
        if style not in COLOR_STYLES:
            raise WorkflowError(
                f"Stile non valido: {style}. Validi: {', '.join(sorted(COLOR_STYLES))}"
            )
        body: dict[str, Any] = {"style": style, "language": language}
        if base_colors:
            body["baseColors"] = base_colors
        if image_url:
            body["imageUrl"] = image_url
            body["extractFromImage"] = True
        return await self._invoke("colors-generate", body)

    # ── Contents: copy/caption ─────────────────────────────────────────────

    async def copy(
        self,
        brief: str,
        *,
        mode: str = "post",
        slide_count: int = 5,
        language: str = "it",
    ) -> dict:
        """Marketing copy (caption + hashtags + headline/slides) via
        content-copy-generate."""
        if mode not in COPY_MODES:
            raise WorkflowError(
                f"Formato non valido: {mode}. Validi: {', '.join(sorted(COPY_MODES))}"
            )
        data = await self._invoke("content-copy-generate", {
            "brief": brief,
            "mode": mode,
            "slideCount": slide_count,
            "language": language,
        })
        return data.get("copy") or data


# ── Async jobs (video / Shotstack / upscale) ───────────────────────────────

# User-facing job fields. cost_usd is deliberately EXCLUDED — user-facing cost
# is always credits (credits_charged/credits_refunded).
_JOB_FIELDS = (
    "id,engine,model,status,prompt,output_url,credits_charged,credits_refunded,"
    "error_message,duration,aspect_ratio,created_at,done_at"
)


class JobsMixin:
    """PostgREST reads of content_video_jobs (owner RLS) via the user session."""

    async def jobs_list(self, *, limit: int = 10) -> list[dict]:
        response = await self._session.request(
            "GET",
            f"/rest/v1/content_video_jobs?select={_JOB_FIELDS}"
            f"&order=created_at.desc&limit={limit}",
        )
        if response.status_code != 200:
            raise WorkflowError(f"jobs: HTTP {response.status_code}")
        data = response.json()
        return data if isinstance(data, list) else []

    async def job_status(self, job_id: str) -> dict:
        response = await self._session.request(
            "GET",
            f"/rest/v1/content_video_jobs?id=eq.{job_id}&select={_JOB_FIELDS}",
        )
        if response.status_code != 200:
            raise WorkflowError(f"job {job_id}: HTTP {response.status_code}")
        data = response.json()
        if not data:
            raise WorkflowError(f"job non trovato: {job_id}")
        return data[0]


# Attach the mixin methods to PlatformWorkflows (single public class).
PlatformWorkflows.jobs_list = JobsMixin.jobs_list        # type: ignore[attr-defined]
PlatformWorkflows.job_status = JobsMixin.job_status      # type: ignore[attr-defined]
