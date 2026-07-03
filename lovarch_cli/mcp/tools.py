"""Tool implementations for the Lovarch MCP server.

Kept as plain, dependency-injected functions (independent of the FastMCP wiring)
so they can be unit-tested directly. ``server.py`` wraps each of these in an
``@mcp.tool()``.

Every tool that runs paid AI goes through :class:`LovarchAiGateway`, so the
user's Lovarch credits are debited by the 1000cr=$1 rule — the MCP server never
calls a model provider directly.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from lovarch_cli.ai import AiGatewayError, InsufficientCreditsError, LovarchAiGateway
from lovarch_cli.credits.lovarch import LovarchCreditsClient


def _projects_root(home: Path | None = None) -> Path:
    base = home or (Path.home() / ".lovarch")
    return base / "projects"


async def tool_whoami(session: Any) -> dict:
    """Report the authenticated Lovarch user and CLI mode."""
    if session is None:
        return {
            "authenticated": False,
            "mode": "none",
            "hint": "Esegui `lovarch login --premium` per autenticarti.",
        }
    return {
        "authenticated": True,
        "mode": "premium",
        "user_id": session.user_id,
        "email": session.email,
    }


async def tool_credits(session: Any) -> dict:
    """Return the user's Lovarch credit balance (does not debit)."""
    if session is None:
        return {"error": "not_authenticated", "hint": "Esegui `lovarch login --premium`."}
    balance = await LovarchCreditsClient(session).check()
    return {
        "balance": balance.balance,
        "monthly_used": balance.monthly_used,
        "credits_remaining": balance.credits_remaining,
        "is_admin": balance.is_admin,
    }


async def tool_generate_image(
    gateway: LovarchAiGateway | None,
    *,
    prompt: str,
    output_path: str,
    quality: str = "medium",
    aspect: str = "1:1",
    mode: str = "generate",
    image_urls: list[str] | None = None,
) -> dict:
    """Generate an image via the platform (debits credits) and save it to disk.

    Returns the saved path and the exact number of credits charged.
    """
    if gateway is None:
        return {"error": "not_authenticated", "hint": "Esegui `lovarch login --premium`."}
    try:
        result = await gateway.generate_image(
            prompt,
            quality=quality,  # type: ignore[arg-type]
            aspect=aspect,
            mode=mode,  # type: ignore[arg-type]
            image_urls=image_urls,
            operation_type="mcp:generate_image",
        )
    except InsufficientCreditsError as exc:
        return {
            "ok": False,
            "error": "insufficient_credits",
            "credits_available": exc.available,
            "credits_needed": exc.needed,
        }
    except AiGatewayError as exc:
        return {"ok": False, "error": str(exc)}

    out = Path(output_path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(result.image_bytes)
    return {
        "ok": True,
        "saved_to": str(out),
        "content_type": result.content_type,
        "credits_charged": result.credits_charged,
        "balance": result.balance,
        "revised_prompt": result.revised_prompt,
    }


def tool_audit_input(project_dir: str) -> dict:
    """Run the 18-point input audit on a project's ``input/`` directory."""
    # Imported lazily to avoid a hard dependency at module import time.
    from lovarch_cli.commands.audit import _overall_verdict, _run_checks

    root = Path(project_dir).expanduser()
    input_dir = root / "input" if (root / "input").exists() else root
    if not input_dir.exists():
        return {"error": "input_dir_not_found", "path": str(input_dir)}
    results = _run_checks(input_dir)
    verdict = _overall_verdict(results)
    return {
        "verdict": verdict.value,
        "checks": [
            {"index": r.index, "key": r.key, "status": r.status.value,
             "detail": r.detail, "required": r.required}
            for r in results
        ],
    }


def tool_list_projects(home: Path | None = None) -> dict:
    """List local Lovarch projects with their workflow + last audit verdict."""
    root = _projects_root(home)
    if not root.exists():
        return {"projects": []}
    projects = []
    for child in sorted(root.iterdir()):
        meta_file = child / "project.yaml"
        if not meta_file.is_file():
            continue
        try:
            meta = yaml.safe_load(meta_file.read_text()) or {}
        except yaml.YAMLError:
            meta = {}
        projects.append({
            "name": child.name,
            "workflow": meta.get("workflow"),
            "last_audit": (meta.get("last_audit") or {}).get("verdict"),
            "last_run": (meta.get("last_run") or {}).get("status"),
        })
    return {"projects": projects}


async def tool_ai_text(
    gateway: Any,
    *,
    prompt: str,
    role: str = "executor",
    model: str | None = None,
    system: str | None = None,
    max_tokens: int | None = None,
    language: str | None = None,
) -> dict:
    """Generate text via the platform gateway (debits credits by real tokens)."""
    if gateway is None:
        return {"error": "not_authenticated", "hint": "Esegui `lovarch login --premium`."}
    try:
        result = await gateway.generate_text(
            prompt, role=role, model=model, system=system,
            max_tokens=max_tokens, language=language,
            operation_type="mcp:ai_text",
        )
    except InsufficientCreditsError as exc:
        return {"ok": False, "error": "insufficient_credits",
                "credits_available": exc.available, "credits_needed": exc.needed}
    except AiGatewayError as exc:
        return {"ok": False, "error": str(exc)}
    return {
        "ok": True,
        "text": result.text,
        "model": result.model,
        "credits_charged": result.credits_charged,
        "balance": result.balance,
    }


async def tool_user_context(gateway: Any, *, lead_id: str | None = None) -> dict:
    """Fetch the user's personalization bundle (brand, style, signature, language)."""
    if gateway is None:
        return {"error": "not_authenticated", "hint": "Esegui `lovarch login --premium`."}
    try:
        return await gateway.get_user_context(lead_id=lead_id)
    except AiGatewayError as exc:
        return {"ok": False, "error": str(exc)}


async def tool_render(
    workflows: Any,
    *,
    description: str,
    output_path: str,
    mode: str | None = None,
    render_style: str = "moderno",
    aspect_ratio: str = "16:9",
    reference_image_path: str | None = None,
    language: str = "it",
) -> dict:
    """Photorealistic render via the platform (credits debited server-side)."""
    if workflows is None:
        return {"error": "not_authenticated", "hint": "Esegui `lovarch login --premium`."}
    from lovarch_cli.workflows import WorkflowError

    try:
        result = await workflows.render(
            description, mode=mode, render_style=render_style,
            aspect_ratio=aspect_ratio, reference_image_path=reference_image_path,
            language=language,
        )
    except WorkflowError as exc:
        return {"ok": False, "error": str(exc)}
    out: dict = {"ok": True, "message": result.message}
    image_bytes = result.image_bytes
    if result.image_url:
        # The EF persisted the render in the user's Lovarch storage — keep the
        # URL AND download a local copy for CLI convenience (best-effort).
        out["image_url"] = result.image_url
        if image_bytes is None:
            try:
                import httpx

                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.get(result.image_url)
                    if resp.status_code == 200:
                        image_bytes = resp.content
            except Exception:  # noqa: BLE001
                image_bytes = None
    if image_bytes:
        p = Path(output_path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(image_bytes)
        out["saved_to"] = str(p)
    return out


async def tool_colors(
    workflows: Any,
    *,
    style: str = "modern",
    base_colors: list[str] | None = None,
    image_url: str | None = None,
    language: str = "it",
) -> dict:
    """Brand color palette via the platform."""
    if workflows is None:
        return {"error": "not_authenticated", "hint": "Esegui `lovarch login --premium`."}
    from lovarch_cli.workflows import WorkflowError

    try:
        return await workflows.colors(
            style=style, base_colors=base_colors, image_url=image_url, language=language,
        )
    except WorkflowError as exc:
        return {"ok": False, "error": str(exc)}


async def tool_copy(
    workflows: Any,
    *,
    brief: str,
    mode: str = "post",
    slide_count: int = 5,
    language: str = "it",
) -> dict:
    """Marketing copy (caption + hashtags) via the platform."""
    if workflows is None:
        return {"error": "not_authenticated", "hint": "Esegui `lovarch login --premium`."}
    from lovarch_cli.workflows import WorkflowError

    try:
        return await workflows.copy(brief, mode=mode, slide_count=slide_count, language=language)
    except WorkflowError as exc:
        return {"ok": False, "error": str(exc)}


def tool_verify_misure(dxf_path: str) -> dict:
    """Deterministic DXF check (ISO layers, room labels, CNAPPC cartiglio). Free."""
    from lovarch_cli.verify import verify_misure

    report = verify_misure(dxf_path)
    return {"verdict": report.verdict, "findings": report.findings, "stats": report.stats}


async def tool_verify_normativa(
    gateway: Any, *, document_path: str, language: str = "it"
) -> dict:
    """Adversarial normative-citation check (Sonnet extracts → Opus refutes)."""
    if gateway is None:
        return {"error": "not_authenticated", "hint": "Esegui `lovarch login --premium`."}
    from lovarch_cli.verify import verify_normativa
    from lovarch_cli.verify.normativa import NormativaError

    try:
        report = await verify_normativa(gateway, document_path, language=language)
    except NormativaError as exc:
        return {"ok": False, "error": str(exc)}
    except InsufficientCreditsError as exc:
        return {"ok": False, "error": "insufficient_credits",
                "credits_available": exc.available, "credits_needed": exc.needed}
    except AiGatewayError as exc:
        return {"ok": False, "error": str(exc)}
    return {
        "ok": True,
        "verdict": report.verdict,
        "citations": report.citations,
        "verdicts": report.verdicts,
        "canonical_found": report.canonical_found,
        "credits_charged": report.credits_charged,
        "notes": report.notes,
    }


async def tool_job_status(workflows: Any, *, job_id: str | None = None, limit: int = 10) -> dict:
    """Async job status (video/export/upscale). Without job_id lists recent jobs."""
    if workflows is None:
        return {"error": "not_authenticated", "hint": "Esegui `lovarch login --premium`."}
    from lovarch_cli.workflows import WorkflowError

    try:
        if job_id:
            return {"ok": True, "job": await workflows.job_status(job_id)}
        return {"ok": True, "jobs": await workflows.jobs_list(limit=limit)}
    except WorkflowError as exc:
        return {"ok": False, "error": str(exc)}


async def tool_verify_contratto(
    gateway: Any, *, document_path: str, language: str = "it"
) -> dict:
    """Adversarial CNAPPC contract check (structure + compenso QN_007)."""
    if gateway is None:
        return {"error": "not_authenticated", "hint": "Esegui `lovarch login --premium`."}
    from lovarch_cli.verify import verify_contratto
    from lovarch_cli.verify.normativa import NormativaError

    try:
        report = await verify_contratto(gateway, document_path, language=language)
    except NormativaError as exc:
        return {"ok": False, "error": str(exc)}
    except InsufficientCreditsError as exc:
        return {"ok": False, "error": "insufficient_credits",
                "credits_available": exc.available, "credits_needed": exc.needed}
    except AiGatewayError as exc:
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "verdict": report.verdict, "structure": report.structure,
            "findings": report.findings, "credits_charged": report.credits_charged}


async def tool_verify_dossier(
    gateway: Any, *, directory: str, language: str = "it", max_llm_files: int = 8
) -> dict:
    """Full standalone QA over a deliverables folder."""
    if gateway is None:
        return {"error": "not_authenticated", "hint": "Esegui `lovarch login --premium`."}
    from lovarch_cli.verify import verify_dossier
    from lovarch_cli.verify.normativa import NormativaError

    try:
        report = await verify_dossier(gateway, directory, language=language,
                                      max_llm_files=max_llm_files)
    except NormativaError as exc:
        return {"ok": False, "error": str(exc)}
    except InsufficientCreditsError as exc:
        return {"ok": False, "error": "insufficient_credits",
                "credits_available": exc.available, "credits_needed": exc.needed}
    except AiGatewayError as exc:
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "verdict": report.verdict, "files": report.files,
            "skipped": report.skipped, "credits_charged": report.credits_charged}


async def tool_logo(workflows: Any, *, prompt: str, output_path: str,
                    reference_image_path: str | None = None, language: str = "it") -> dict:
    """Brand logo pack via the platform."""
    if workflows is None:
        return {"error": "not_authenticated", "hint": "Esegui `lovarch login --premium`."}
    from lovarch_cli.workflows import WorkflowError

    try:
        result = await workflows.logo(prompt, reference_image_path=reference_image_path, language=language)
    except WorkflowError as exc:
        return {"ok": False, "error": str(exc)}
    out: dict = {"ok": True, "image_url": result.image_url, "message": result.message}
    if result.image_url:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.get(result.image_url)
                if r.status_code == 200:
                    p = Path(output_path).expanduser(); p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(r.content); out["saved_to"] = str(p)
        except Exception:  # noqa: BLE001
            pass
    return out


async def tool_site(workflows: Any, *, prompt: str, output_path: str, language: str = "it") -> dict:
    """Generate a website (HTML) via the platform, saved to disk."""
    if workflows is None:
        return {"error": "not_authenticated", "hint": "Esegui `lovarch login --premium`."}
    from lovarch_cli.workflows import WorkflowError

    try:
        html = await workflows.site(prompt, language=language)
    except WorkflowError as exc:
        return {"ok": False, "error": str(exc)}
    p = Path(output_path).expanduser(); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")
    return {"ok": True, "saved_to": str(p), "bytes": len(html)}



async def tool_agent(gateway: Any, *, agent_id: str, brief: str,
                     language: str = "it", lead_id: str | None = None) -> dict:
    """Run a curated architecture/interior/construction agent via the platform."""
    if gateway is None:
        return {"error": "not_authenticated", "hint": "Esegui `lovarch login --premium`."}
    from lovarch_cli.agents import AGENTS, run_agent
    from lovarch_cli.ai import InsufficientCreditsError

    if agent_id not in AGENTS:
        return {"ok": False, "error": f"unknown_agent: {agent_id}",
                "available": list(AGENTS)}
    try:
        r = await run_agent(gateway, agent_id, brief, language=language, lead_id=lead_id)
    except InsufficientCreditsError as exc:
        return {"ok": False, "error": "insufficient_credits",
                "credits_available": exc.available, "credits_needed": exc.needed}
    except AiGatewayError as exc:
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "agent": r.agent_id, "text": r.text,
            "model": r.model, "credits_charged": r.credits_charged}
