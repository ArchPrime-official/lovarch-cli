"""Entry point for `python -m lovarch_cli`.

This allows users to invoke the CLI both as:
- `arch <command>` (via [project.scripts] entry point)
- `python -m lovarch_cli <command>` (via this module)
"""
from lovarch_cli.cli import app

if __name__ == "__main__":
    app()
