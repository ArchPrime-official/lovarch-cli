"""Entry point for `python -m archprime_cli`.

This allows users to invoke the CLI both as:
- `arch <command>` (via [project.scripts] entry point)
- `python -m archprime_cli <command>` (via this module)
"""
from archprime_cli.cli import app

if __name__ == "__main__":
    app()
