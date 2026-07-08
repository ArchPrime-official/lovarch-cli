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

import os
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


def _sync_to(dest_root: Path) -> list[str]:
    """Copy every bundled skill into ``dest_root`` (overwriting). Returns names.

    Shared by the explicit ``skills install`` command and the automatic
    start-up sync so both stay byte-for-byte identical.
    """
    src = _bundled_skills_dir()
    dest_root.mkdir(parents=True, exist_ok=True)
    installed: list[str] = []
    for skill_dir in sorted(p.parent for p in src.glob("*/SKILL.md")):
        dest = dest_root / skill_dir.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        installed.append(skill_dir.name)
    return installed


# Stamp file (in ~/.lovarch) recording the CLI version the skills were last
# synced for. Lets the start-up sync short-circuit on the common case.
_SKILLS_STAMP = ".skills-synced"


def ensure_skills_synced() -> None:
    """Auto-install/refresh the Lovarch skills into ~/.claude/skills on start-up.

    Design goals (see `lovarch skills install` for the manual counterpart):
    - **Idempotent + cheap**: version-gated by a stamp in ~/.lovarch, so the
      common case is a single file read + `exists()` check.
    - **Self-healing**: re-syncs if the destination was deleted even when the
      stamp still matches.
    - **Non-invasive**: never provisions ~/.claude for users who don't run
      Claude Code (no ~/.claude and no prior install → skip silently).
    - **Best-effort**: any failure is swallowed — a skills hiccup must never
      break a real `lovarch` command.
    - **Opt-out**: set LOVARCH_NO_SKILLS_SYNC=1 to disable entirely.
    """
    try:
        if os.environ.get("LOVARCH_NO_SKILLS_SYNC"):
            return

        from lovarch_cli.config import DEFAULT_HOME
        from lovarch_cli.version import __version__

        claude_root = Path.home() / ".claude"
        dest_root = claude_root / "skills"
        # Don't create a Claude Code config for someone who doesn't use it,
        # unless they've already installed the skills here before.
        if not claude_root.exists() and not dest_root.exists():
            return

        stamp = DEFAULT_HOME / _SKILLS_STAMP
        try:
            current = stamp.read_text(encoding="utf-8").strip()
        except OSError:
            current = ""
        # Fast path: already synced for this version AND still on disk.
        if current == __version__ and dest_root.exists():
            return

        first_time = not dest_root.exists()
        _sync_to(dest_root)
        DEFAULT_HOME.mkdir(parents=True, exist_ok=True)
        stamp.write_text(__version__, encoding="utf-8")

        # Quiet one-line heads-up on first install only (upgrades sync in
        # silence). stderr so it never contaminates stdout data/JSON.
        if first_time:
            err_console.print(
                "[dim]· Skill Lovarch installate in ~/.claude/skills — "
                "riavvia l'agente per caricarle "
                "(disattiva con LOVARCH_NO_SKILLS_SYNC=1).[/dim]"
            )
    except Exception:
        # Auto-sync is best-effort: never break a real command.
        pass


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
    dest_root = (target or (Path.home() / ".claude" / "skills")).expanduser()
    installed = _sync_to(dest_root)

    # Record the version so the automatic start-up sync short-circuits.
    try:
        from lovarch_cli.config import DEFAULT_HOME
        from lovarch_cli.version import __version__

        DEFAULT_HOME.mkdir(parents=True, exist_ok=True)
        (DEFAULT_HOME / _SKILLS_STAMP).write_text(__version__, encoding="utf-8")
    except OSError:
        pass

    console.print(f"[green]✓[/green] {len(installed)} skill installate in [bold]{dest_root}[/bold]:")
    for name in installed:
        console.print(f"  · /{name}")
    console.print(
        "\n[dim]Nel tuo agente: il testo usa il TUO modello (zero crediti); "
        "immagini/dati passano da `lovarch` (crediti). Riavvia la sessione per "
        "caricare le skill.[/dim]"
    )
