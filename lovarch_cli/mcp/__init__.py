"""Lovarch MCP server package.

Exposes the CLI's capabilities (credits, image generation, project audit) as an
MCP server so Claude Code / Claude / IDEs can drive Lovarch while debiting the
user's credits identically to the CLI. Entry point: ``lovarch mcp serve``.
"""
from lovarch_cli.mcp.server import build_server, serve

__all__ = ["build_server", "serve"]
