"""lovarch-cli version — single source of truth.

Read by:
- pyproject.toml [tool.hatch.version] for build
- lovarch_cli/__init__.py for runtime
- arch --version flag

Bump policy (semver):
- MAJOR: breaking CLI API (subcommand removal, flag rename)
- MINOR: new subcommands, new agents, new languages
- PATCH: bug fixes, dependency bumps
"""
__version__ = "0.11.0"
