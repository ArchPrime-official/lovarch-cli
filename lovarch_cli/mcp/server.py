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
from lovarch_cli.workflows import PlatformWorkflows


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
    workflows = PlatformWorkflows(session) if session is not None else None

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

    @mcp.tool()
    async def lovarch_ai_text(
        prompt: str,
        role: str = "executor",
        model: str | None = None,
        system: str | None = None,
        max_tokens: int | None = None,
        language: str | None = None,
    ) -> dict:
        """Genera testo via piattaforma Lovarch addebitando i crediti dell'utente
        per i token reali. role: executor (default) | verifier | chief — il
        server sceglie il modello; oppure model esplicito dal catalogo della
        piattaforma. language forza la lingua dell'output."""
        return await tools.tool_ai_text(
            gateway, prompt=prompt, role=role, model=model, system=system,
            max_tokens=max_tokens, language=language,
        )

    @mcp.tool()
    async def lovarch_context(lead_id: str | None = None) -> dict:
        """Bundle di personalizzazione dell'utente Lovarch: brand, stile,
        firma professionale, dati fiscali, lingua preferita e prompt_block
        pronto. lead_id opzionale carica anche un cliente del CRM."""
        return await tools.tool_user_context(gateway, lead_id=lead_id)

    @mcp.tool()
    async def lovarch_render(
        description: str,
        output_path: str,
        mode: str | None = None,
        render_style: str = "moderno",
        aspect_ratio: str = "16:9",
        reference_image_path: str | None = None,
        language: str = "it",
    ) -> dict:
        """Render fotorealistico via Render Studio Lovarch (crediti addebitati
        dalla piattaforma). mode: null=sketch/testo→render 2D ·
        room_render/render_3d/plan_to_3d=3D (costo maggiore) ·
        lighting_only/closeup_detail/closeup_angle. reference_image_path invia
        uno sketch/foto/pianta come riferimento."""
        return await tools.tool_render(
            workflows, description=description, output_path=output_path,
            mode=mode, render_style=render_style, aspect_ratio=aspect_ratio,
            reference_image_path=reference_image_path, language=language,
        )

    @mcp.tool()
    async def lovarch_colors(
        style: str = "modern",
        base_colors: list[str] | None = None,
        image_url: str | None = None,
        language: str = "it",
    ) -> dict:
        """Palette colori brand via piattaforma Lovarch. Con image_url la
        palette è estratta dall'immagine. style: modern|vintage|natural|bold|custom."""
        return await tools.tool_colors(
            workflows, style=style, base_colors=base_colors,
            image_url=image_url, language=language,
        )

    @mcp.tool()
    async def lovarch_copy(
        brief: str,
        mode: str = "post",
        slide_count: int = 5,
        language: str = "it",
    ) -> dict:
        """Copy di marketing (caption + hashtags + headline) via piattaforma
        Lovarch. mode: post|story|carousel."""
        return await tools.tool_copy(
            workflows, brief=brief, mode=mode, slide_count=slide_count, language=language,
        )

    return mcp


def serve() -> None:
    """Build the server and run it over stdio (blocking)."""
    build_server().run()
