"""lovarch-cli subcommands.

Each command lives in its own module and exposes either:
- a `cmd()` function (single-action subcommand), OR
- an `app: typer.Typer` instance (multi-subcommand group)

The main CLI (lovarch_cli/cli.py) registers each via add_typer or command.

Lazy imports here so heavy commands (audit, run) don't load at startup.
"""
