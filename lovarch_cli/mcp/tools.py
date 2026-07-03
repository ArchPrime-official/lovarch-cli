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
        "cost_usd": result.cost_usd,
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
