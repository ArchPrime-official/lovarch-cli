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

    @mcp.tool()
    async def lovarch_logo(prompt: str, output_path: str,
                           reference_image_path: str | None = None, language: str = "it") -> dict:
        """Logo pack del brand via piattaforma Lovarch (crediti addebitati)."""
        return await tools.tool_logo(workflows, prompt=prompt, output_path=output_path,
                                     reference_image_path=reference_image_path, language=language)

    @mcp.tool()
    async def lovarch_site(prompt: str, output_path: str, language: str = "it") -> dict:
        """Genera un sito web (HTML) via piattaforma Lovarch e lo salva su disco."""
        return await tools.tool_site(workflows, prompt=prompt, output_path=output_path, language=language)


    @mcp.tool()
    def lovarch_verify_misure(dxf_path: str) -> dict:
        """Verifica deterministica di un DXF: layer ISO (UNI ISO 5457),
        etichette ambienti, cartiglio CNAPPC. Gratuita (nessun credito)."""
        return tools.tool_verify_misure(dxf_path)

    @mcp.tool()
    async def lovarch_agent(agent_id: str, brief: str, language: str = "it",
                            lead_id: str | None = None) -> dict:
        """Esegue un agente curato (interior-designer, direzione-lavori,
        preventivi, geometra-catasto) su un brief, personalizzato col brand
        dell'utente e addebitando i crediti. Vedi anche le altre tool."""
        return await tools.tool_agent(gateway, agent_id=agent_id, brief=brief,
                                      language=language, lead_id=lead_id)

    @mcp.tool()
    async def lovarch_verify_normativa(document_path: str, language: str = "it") -> dict:
        """Verifica ADVERSARIALE delle citazioni normative di un documento
        (.pdf/.md/.txt): Sonnet 5 estrae le citazioni, Opus 4.8 prova a
        confutarle (articoli fantasma, norme citate a sproposito). Addebita
        crediti per i token reali. Verdetto PASS/CONCERNS/REJECT."""
        return await tools.tool_verify_normativa(
            gateway, document_path=document_path, language=language,
        )

    @mcp.tool()
    async def lovarch_verify_contratto(document_path: str, language: str = "it") -> dict:
        """Verifica ADVERSARIALE di un contratto CNAPPC (.pdf/.md/.txt):
        completezza delle 12 sezioni + regola compenso (per cliente privato i
        parametri DM 17/06/2016 sono orientativi → CONCERN, mai illecito).
        Addebita crediti per i token reali."""
        return await tools.tool_verify_contratto(
            gateway, document_path=document_path, language=language,
        )

    @mcp.tool()
    async def lovarch_verify_dossier(directory: str, language: str = "it",
                                     max_llm_files: int = 8) -> dict:
        """QA completo standalone su una cartella di deliverable: DXF (gratis) +
        documenti normativi/contratti (adversarial, crediti). Verdetto
        aggregato PASS/CONCERNS/REJECT per file e complessivo."""
        return await tools.tool_verify_dossier(
            gateway, directory=directory, language=language, max_llm_files=max_llm_files,
        )

    @mcp.tool()
    async def lovarch_job_status(job_id: str | None = None, limit: int = 10) -> dict:
        """Stato dei job asincroni della piattaforma (video, export Shotstack,
        upscale). Senza job_id elenca i job recenti. Costi solo in crediti."""
        return await tools.tool_job_status(workflows, job_id=job_id, limit=limit)

    return mcp


def serve() -> None:
    """Build the server and run it over stdio (blocking)."""
    build_server().run()
