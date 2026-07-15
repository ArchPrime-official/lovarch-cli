"""`lovarch agents` — install/manage the Lovarch subagents for Claude Code.

    lovarch agents list                 # bundled Lovarch + your own
    lovarch agents install              # → ~/.claude/agents/
    lovarch agents new <name>           # scaffold YOUR own agent
    lovarch agents install --target DIR

These are Claude Code *subagents* (`~/.claude/agents/*.md`): a directing layer
ON TOP of the Lovarch skills. `lovarch-content-chief` orchestrates content
creation; `lovarch-squad-creator` helps the user craft their OWN agents/skills.

Distinct from `lovarch agent` (singular) — those are the 17 server-side LLM
personas that run on the gateway and debit credits. The subagents here run in
the user's own Claude Code with the user's own model (free text).

Why a separate module (and NOT `lovarch_cli/agents/`, and NOT reusing the skills
sync): the directory `lovarch_cli/agents/` is already the Python module for the
server-side personas. And the skills sync overwrites/removes without ceremony —
here we MUST preserve the agents/skills the USER creates. So this sync is
manifest-guarded: it only ever touches files the CLI itself installed.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import typer
from rich.console import Console

console = Console()
err_console = Console(stderr=True)

agents_app = typer.Typer(
    help="Subagent Lovarch per Claude Code: content-chief (regia) e squad-creator (crea i TUOI agenti/skill).",
    no_args_is_help=True,
)

# Manifest (in ~/.lovarch) recording exactly which agent files the CLI installed
# — the key that lets the sync preserve user-created agents. Format:
#   {"version": "0.7.0", "files": ["lovarch-content-chief.md", ...]}
_MANIFEST = ".agents-manifest.json"


def _fail(msg: str) -> int:
    err_console.print(f"[red]✗ {msg}[/red]")
    return 1


def _bundled_agents_dir() -> Path:
    """Locate the bundled claude_agents/ directory (repo checkout or wheel)."""
    candidates = [
        Path(__file__).resolve().parents[1] / "claude_agents",
        Path(__file__).resolve().parents[2] / "claude_agents",
    ]
    for c in candidates:
        if c.is_dir() and any(c.glob("lovarch-*.md")):
            return c
    raise typer.Exit(code=_fail("agents bundle non trovato nell'installazione."))


def _bundled_names() -> list[str]:
    """Filenames of the official bundled agents (e.g. lovarch-content-chief.md)."""
    return sorted(p.name for p in _bundled_agents_dir().glob("lovarch-*.md"))


def _read_manifest(home: Path) -> dict:
    try:
        return json.loads((home / _MANIFEST).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_manifest(home: Path, files: list[str]) -> None:
    from lovarch_cli.version import __version__

    try:
        home.mkdir(parents=True, exist_ok=True)
        (home / _MANIFEST).write_text(
            json.dumps({"version": __version__, "files": files}, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        pass


def _sync_to(dest_root: Path, home: Path) -> tuple[list[str], list[str]]:
    """Install the bundled agents into ``dest_root``, manifest-guarded.

    Returns ``(installed, removed_orphans)``.

    Rules that make it safe for user-authored agents:
    - Copy every bundled ``lovarch-*.md`` (overwrite — these are ours).
    - Remove files that WERE ours last time (in the manifest) but are no longer
      in the bundle — retired official agents. Nothing else is deleted.
    - NEVER touch a file the user created (not in bundle, not in manifest) —
      even one named ``lovarch-*.md``.
    """
    src = _bundled_agents_dir()
    dest_root.mkdir(parents=True, exist_ok=True)

    bundled = _bundled_names()
    prev = set(_read_manifest(home).get("files", []))

    installed: list[str] = []
    for name in bundled:
        shutil.copy2(src / name, dest_root / name)
        installed.append(name)

    removed: list[str] = []
    for orphan in sorted(prev - set(bundled)):
        target = dest_root / orphan
        if target.exists():
            target.unlink()
            removed.append(orphan)

    _write_manifest(home, bundled)
    return installed, removed


def ensure_agents_synced() -> None:
    """Auto-install/refresh the Lovarch subagents into ~/.claude/agents on start-up.

    Twin of ``ensure_skills_synced`` (same idempotent/self-healing/non-invasive/
    best-effort/opt-out design), but manifest-guarded so it never clobbers or
    deletes agents the USER authored.

    Opt-out: LOVARCH_NO_AGENTS_SYNC=1.
    """
    try:
        if os.environ.get("LOVARCH_NO_AGENTS_SYNC"):
            return

        from lovarch_cli.config import DEFAULT_HOME
        from lovarch_cli.version import __version__

        claude_root = Path.home() / ".claude"
        dest_root = claude_root / "agents"
        # Don't provision ~/.claude for someone who doesn't run Claude Code,
        # unless they've already installed the agents here before.
        if not claude_root.exists() and not dest_root.exists():
            return

        manifest = _read_manifest(DEFAULT_HOME)
        bundled = _bundled_names()
        # Fast path: synced for this version, destination present, and every
        # bundled agent still on disk.
        if (
            manifest.get("version") == __version__
            and dest_root.exists()
            and all((dest_root / n).exists() for n in bundled)
        ):
            return

        first_time = not dest_root.exists()
        _sync_to(dest_root, DEFAULT_HOME)

        if first_time:
            err_console.print(
                "[dim]· Agenti Lovarch installati in ~/.claude/agents — "
                "riavvia l'agente per caricarli "
                "(disattiva con LOVARCH_NO_AGENTS_SYNC=1).[/dim]"
            )
    except Exception:
        # Auto-sync is best-effort: never break a real command.
        pass


def _first_field(md_path: Path, field: str) -> str:
    """First value of a frontmatter field, handling YAML block scalars (`>`/`|`)."""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith(f"{field}:"):
            val = line.split(":", 1)[1].strip()
            if val in (">", ">-", "|", "|-"):
                # Block scalar: take the first non-empty indented line.
                for nxt in lines[i + 1:]:
                    if nxt.strip():
                        return nxt.strip()
                return ""
            return val
    return ""


@agents_app.command("list")
def list_command() -> None:
    """Elenca gli agenti Lovarch (bundle) e i TUOI (in ~/.claude/agents)."""
    bundled = set(_bundled_names())
    console.print("[bold]Agenti Lovarch (ufficiali):[/bold]")
    for name in sorted(bundled):
        desc = _first_field(_bundled_agents_dir() / name, "description")[:80]
        console.print(f"  [cyan]{name[:-3]}[/cyan] — {desc}…")

    dest = Path.home() / ".claude" / "agents"
    if dest.is_dir():
        mine = sorted(
            p.name for p in dest.glob("*.md") if p.name not in bundled
        )
        if mine:
            console.print("\n[bold]I tuoi agenti (creati da te):[/bold]")
            for name in mine:
                desc = _first_field(dest / name, "description")[:80]
                console.print(f"  [green]{name[:-3]}[/green] — {desc}…")


@agents_app.command("install")
def install_command(
    target: Path = typer.Option(
        None, "--target",
        help="Directory di destinazione (default: ~/.claude/agents).",
    ),
) -> None:
    """Installa i subagent Lovarch in ~/.claude/agents (Claude Code)."""
    from lovarch_cli.config import DEFAULT_HOME

    dest_root = (target or (Path.home() / ".claude" / "agents")).expanduser()
    installed, removed = _sync_to(dest_root, DEFAULT_HOME)

    console.print(f"[green]✓[/green] {len(installed)} agenti installati in [bold]{dest_root}[/bold]:")
    for name in installed:
        console.print(f"  · @{name[:-3]}")
    if removed:
        console.print(f"[dim]  ({len(removed)} agenti ritirati rimossi)[/dim]")
    console.print(
        "\n[dim]Nel tuo agente: invoca @lovarch-content-chief per la regia dei "
        "contenuti, o @lovarch-squad-creator per creare i tuoi agenti/skill. "
        "Riavvia la sessione per caricarli.[/dim]"
    )


_AGENT_TEMPLATE = """\
---
name: {name}
description: >
  {desc}
  Trigger — "{trigger}".
# skills: lovarch-video, lovarch-render   # (opzionale) skill da precaricare
---

# {title}

Sei @{name}, {role}.

## Cosa fai
Descrivi qui il ruolo in 2-3 frasi.

## Processo
1. Chiedi il contesto necessario (max poche domande).
2. (Se generi media) usa gli strumenti del connettore Lovarch — es.
   `lovarch_generate_image`, `lovarch_generate_video`, `lovarch_render`.
   **Avvisa SEMPRE la stima in crediti PRIMA di generare.**
3. Consegna con il link alla galleria dell'utente.

## Regole
- Il testo lo scrivi TU (modello dell'utente) — zero crediti.
- I media passano dagli strumenti Lovarch — crediti dell'utente (1000 cr = 1$).
- Rispondi nella lingua dell'utente.
"""


@agents_app.command("new")
def new_command(
    name: str = typer.Argument(..., help="Nome dell'agente (es. mio-copywriter)."),
    desc: str = typer.Option(
        "Agente personalizzato.", "--desc", help="Descrizione breve (quando usarlo)."
    ),
    role: str = typer.Option(
        "specialista", "--role", help="Ruolo dell'agente in una frase."
    ),
    trigger: str = typer.Option(
        "", "--trigger", help="Parole che attivano l'agente (separate da virgola)."
    ),
    target: Path = typer.Option(
        None, "--target", help="Directory (default: ~/.claude/agents)."
    ),
) -> None:
    """Crea lo scheletro di un TUO agente in ~/.claude/agents (non gestito da Lovarch)."""
    slug = name.strip().lower().replace(" ", "-")
    if slug in {n[:-3] for n in _bundled_names()}:
        raise typer.Exit(code=_fail(
            f"'{slug}' è un agente Lovarch ufficiale. Scegli un altro nome "
            "(i tuoi agenti non devono collidere con quelli ufficiali)."
        ))
    dest_root = (target or (Path.home() / ".claude" / "agents")).expanduser()
    dest_root.mkdir(parents=True, exist_ok=True)
    dest = dest_root / f"{slug}.md"
    if dest.exists():
        raise typer.Exit(code=_fail(f"{dest} esiste già. Modificalo o scegli un altro nome."))
    dest.write_text(
        _AGENT_TEMPLATE.format(
            name=slug,
            desc=desc,
            trigger=trigger or slug,
            title=slug.replace("-", " ").title(),
            role=role,
        ),
        encoding="utf-8",
    )
    console.print(f"[green]✓[/green] Agente creato: [bold]{dest}[/bold]")
    console.print(
        "[dim]È TUO: il sync di Lovarch non lo tocca mai. Aprilo e personalizzalo, "
        "oppure chiedi a @lovarch-squad-creator di aiutarti a scriverlo. "
        "Riavvia la sessione per caricarlo.[/dim]"
    )


def _official_skill_names() -> set[str]:
    """Nomi delle skill ufficiali (bundle) — per NON fare backup di quelle."""
    try:
        from lovarch_cli.commands.skills_cmd import _bundled_skills_dir
        return {p.parent.name for p in _bundled_skills_dir().glob("*/SKILL.md")}
    except Exception:
        return set()


def _collect_user_files() -> list[dict]:
    """Enumera SÓ os agentes/skills criados pelo USUÁRIO (fora do bundle/manifest)."""
    from lovarch_cli.config import DEFAULT_HOME

    files: list[dict] = []
    official_agents = set(_bundled_names()) | set(_read_manifest(DEFAULT_HOME).get("files", []))
    agents_dir = Path.home() / ".claude" / "agents"
    if agents_dir.is_dir():
        for md in sorted(agents_dir.glob("*.md")):
            if md.name in official_agents:
                continue
            files.append({"kind": "agent", "slug": md.stem, "relative_path": md.name,
                          "content": md.read_text(encoding="utf-8")})

    official_skills = _official_skill_names()
    skills_dir = Path.home() / ".claude" / "skills"
    if skills_dir.is_dir():
        for sk in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
            if sk.name in official_skills:
                continue
            for f in sorted(sk.rglob("*")):
                if f.is_file():
                    rel = f"{sk.name}/{f.relative_to(sk).as_posix()}"
                    files.append({"kind": "skill", "slug": sk.name, "relative_path": rel,
                                  "content": f.read_text(encoding="utf-8")})
    return files


@agents_app.command("push")
def push_command() -> None:
    """Salva i TUOI agenti e skill nell'account Lovarch (backup nel cloud)."""
    import asyncio
    from lovarch_cli.ai import AiGatewayError, LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession
    from lovarch_cli.upsell import not_authenticated

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)
    files = _collect_user_files()
    if not files:
        console.print("[dim]Nessun agente/skill TUO da salvare (gli ufficiali non si salvano).[/dim]")
        return
    try:
        asyncio.run(LovarchAiGateway(session).data("agents_push", files=files))
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)
    n_agents = len({f["slug"] for f in files if f["kind"] == "agent"})
    n_skills = len({f["slug"] for f in files if f["kind"] == "skill"})
    console.print(f"[green]✓[/green] Backup salvato: {n_agents} agenti + {n_skills} skill ({len(files)} file).")


@agents_app.command("pull")
def pull_command() -> None:
    """Ripristina i TUOI agenti e skill dall'account Lovarch (in un'altra macchina)."""
    import asyncio
    from lovarch_cli.ai import AiGatewayError, LovarchAiGateway
    from lovarch_cli.auth.session import LovarchSession
    from lovarch_cli.upsell import not_authenticated

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)
    try:
        data = asyncio.run(LovarchAiGateway(session).data("agents_pull"))
    except AiGatewayError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)

    official_agents = set(_bundled_names())
    official_skills = _official_skill_names()
    claude = Path.home() / ".claude"
    written = 0
    for f in data.get("files", []):
        kind, rel, content = f.get("kind"), f.get("relative_path"), f.get("content", "")
        if not rel or kind not in ("agent", "skill"):
            continue
        # Nunca sobrescrever oficiais.
        if kind == "agent" and rel in official_agents:
            continue
        if kind == "skill" and rel.split("/")[0] in official_skills:
            continue
        target = (claude / ("agents" if kind == "agent" else "skills") / rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written += 1
    console.print(f"[green]✓[/green] Ripristinati {written} file in ~/.claude. Riavvia la sessione per caricarli.")
