"""`lovarch skills` — install the Lovarch skills into the user's agent.

    lovarch skills list
    lovarch skills install            # → ~/.claude/skills/
    lovarch skills install --target DIR

The skills make the user's OWN agent (Claude Code etc.) run the personas with
its own model — zero Lovarch text credits — calling the `lovarch` CLI only for
what requires the platform (images, profile data, deliverables, deterministic
checks).
"""
from __future__ import annotations

import shutil
from pathlib import Path

import typer
from rich.console import Console

console = Console()
err_console = Console(stderr=True)

skills_app = typer.Typer(
    help="Skills Lovarch per il tuo agente (Claude Code...): testo col TUO modello, piattaforma solo per immagini/dati.",
    no_args_is_help=True,
)


def _bundled_skills_dir() -> Path:
    """Locate the bundled skills/ directory (repo checkout or installed pkg)."""
    # packaged inside lovarch_cli/skills (ships with the wheel/brew/PyPI)
    candidates = [
        Path(__file__).resolve().parents[1] / "skills",
        Path(__file__).resolve().parents[2] / "skills",
    ]
    for c in candidates:
        if c.is_dir() and any(c.glob("*/SKILL.md")):
            return c
    raise typer.Exit(code=_fail("skills bundle non trovato nell'installazione."))


def _fail(msg: str) -> int:
    err_console.print(f"[red]✗ {msg}[/red]")
    return 1


@skills_app.command("list")
def list_command() -> None:
    """Elenca le skill disponibili nel bundle."""
    src = _bundled_skills_dir()
    for skill_md in sorted(src.glob("*/SKILL.md")):
        name = skill_md.parent.name
        desc = ""
        for line in skill_md.read_text(encoding="utf-8").splitlines():
            if line.startswith("description:"):
                desc = line.split(":", 1)[1].strip()[:90]
                break
        console.print(f"  [cyan]{name}[/cyan] — {desc}…")


@skills_app.command("install")
def install_command(
    target: Path = typer.Option(
        None, "--target",
        help="Directory di destinazione (default: ~/.claude/skills).",
    ),
) -> None:
    """Installa le skill Lovarch in ~/.claude/skills (Claude Code)."""
    src = _bundled_skills_dir()
    dest_root = (target or (Path.home() / ".claude" / "skills")).expanduser()
    dest_root.mkdir(parents=True, exist_ok=True)

    installed = []
    for skill_dir in sorted(p.parent for p in src.glob("*/SKILL.md")):
        dest = dest_root / skill_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        installed.append(skill_dir.name)

    console.print(f"[green]✓[/green] {len(installed)} skill installate in [bold]{dest_root}[/bold]:")
    for name in installed:
        console.print(f"  · /{name}")
    console.print(
        "\n[dim]Nel tuo agente: il testo usa il TUO modello (zero crediti); "
        "immagini/dati passano da `lovarch` (crediti). Riavvia la sessione per "
        "caricare le skill.[/dim]"
    )
