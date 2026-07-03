"""`lovarch mcp` — run the Lovarch MCP server.

The heavy ``mcp`` SDK import is lazy (inside the command) so that
``lovarch --help`` and every other command keep working even when the optional
``[mcp]`` extra is not installed.
"""
from __future__ import annotations

import typer

mcp_app = typer.Typer(
    help="Server MCP di Lovarch (per Claude Code / IDE). Richiede l'extra [mcp].",
    no_args_is_help=True,
)


@mcp_app.command("serve")
def serve_command() -> None:
    """Avvia il server MCP su stdio.

    Registra in Claude Code con:
        claude mcp add lovarch -- lovarch mcp serve
    """
    from lovarch_cli.mcp.server import serve

    serve()
