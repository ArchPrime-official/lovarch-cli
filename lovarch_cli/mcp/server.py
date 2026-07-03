"""Lovarch MCP server — exposes the CLI's capabilities as MCP tools.

Run with ``lovarch mcp serve`` (stdio transport). Register in Claude Code with:

    claude mcp add lovarch -- lovarch mcp serve

The server reuses the exact same premium session (OS keyring), credit gateway,
and project logic as the CLI, so an MCP tool call debits the user's Lovarch
credits identically to ``lovarch run``. Nothing here calls a model provider
directly.

The ``mcp`` SDK is an optional dependency; install with ``pip install
'lovarch-cli[mcp]'`` (or it ships via the Homebrew formula).
"""
from __future__ import annotations

from lovarch_cli.ai import LovarchAiGateway
from lovarch_cli.auth.session import LovarchSession
from lovarch_cli.mcp import tools


def build_server():
    """Construct the FastMCP server with all Lovarch tools wired in.

    Raises a clear error if the ``mcp`` SDK is not installed.
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - exercised via install matrix
        raise SystemExit(
            "Il pacchetto 'mcp' non è installato. Esegui: pip install 'lovarch-cli[mcp]'"
        ) from exc

    # Load the premium session once at startup (None if not logged in premium).
    session = LovarchSession.load()
    gateway = LovarchAiGateway(session) if session is not None else None

    mcp = FastMCP("lovarch")

    @mcp.tool()
    async def lovarch_whoami() -> dict:
        """Mostra l'utente Lovarch autenticato e la modalità della CLI."""
        return await tools.tool_whoami(session)

    @mcp.tool()
    async def lovarch_credits() -> dict:
        """Mostra il saldo crediti Lovarch dell'utente (non addebita)."""
        return await tools.tool_credits(session)

    @mcp.tool()
    async def lovarch_generate_image(
        prompt: str,
        output_path: str,
        quality: str = "medium",
        aspect: str = "1:1",
        mode: str = "generate",
        image_urls: list[str] | None = None,
    ) -> dict:
        """Genera (o modifica) un'immagine via piattaforma Lovarch, addebitando
        i crediti dell'utente (1000cr=$1), e la salva su disco. quality:
        low|medium|high. mode: generate (testo→immagine) o edit (con image_urls)."""
        return await tools.tool_generate_image(
            gateway, prompt=prompt, output_path=output_path, quality=quality,
            aspect=aspect, mode=mode, image_urls=image_urls,
        )

    @mcp.tool()
    def lovarch_audit_input(project_dir: str) -> dict:
        """Esegue l'audit dei 18 input su un progetto (gate di ingresso)."""
        return tools.tool_audit_input(project_dir)

    @mcp.tool()
    def lovarch_list_projects() -> dict:
        """Elenca i progetti Lovarch locali con workflow e ultimo audit."""
        return tools.tool_list_projects()

    return mcp


def serve() -> None:
    """Build the server and run it over stdio (blocking)."""
    build_server().run()
