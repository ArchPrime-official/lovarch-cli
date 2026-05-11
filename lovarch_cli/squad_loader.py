"""Resolve which squad payload directory the CLI should use at runtime.

Three resolution sources, in priority order:

1. Explicit override (CLI flag `--squad-src`) — highest priority. Used for
   ad-hoc one-off runs against a custom squad path.
2. `LOVARCH_SQUAD_SRC` environment variable — for the developer's daily
   loop. Export once in `~/.zshrc` and every CLI invocation picks it up.
3. Bundled `lovarch_cli/squad/` — the vendored snapshot shipped with the
   package. This is what `brew install` users get.

The override paths MUST point at a directory that looks like the squad
(must contain at minimum `scripts/pipeline_runner.py` and `agents/`).
We validate the shape early so the failure message is actionable instead
of a cryptic FileNotFoundError two layers deeper.

This module is the single source-of-truth for squad path resolution. All
commands that read squad assets (run, init --sample, future dev tooling)
go through `resolve_squad_root()`.
"""
from __future__ import annotations

import os
from pathlib import Path


# Environment variable name. Document this widely — it's the daily dev
# override most contributors will use.
ENV_VAR = "LOVARCH_SQUAD_SRC"

# Bundled vendor — shipped with the wheel via the build hook
# (scripts/sync_squad.py). See docs/squad-vendoring.md.
_BUNDLED_DIR: Path = Path(__file__).resolve().parent / "squad"

# Shape markers — files we expect to find in any valid squad payload.
# `scripts/pipeline_runner.py` is the orchestration entrypoint that
# `lovarch run` shells out to. `agents/` is the directory of agent prompts.
_REQUIRED_MARKERS: tuple[str, ...] = (
    "scripts/pipeline_runner.py",
    "agents",
)


class SquadNotFoundError(RuntimeError):
    """The configured squad root does not exist or does not look like a squad."""


def _looks_like_squad(path: Path) -> bool:
    """Return True if every marker in _REQUIRED_MARKERS exists under path."""
    return all((path / marker).exists() for marker in _REQUIRED_MARKERS)


def _validate_or_raise(path: Path, source_label: str) -> Path:
    """Raise SquadNotFoundError unless `path` looks like a valid squad payload."""
    if not path.is_dir():
        raise SquadNotFoundError(
            f"Squad path from {source_label} does not exist or is not a "
            f"directory: {path}"
        )
    if not _looks_like_squad(path):
        missing = [m for m in _REQUIRED_MARKERS if not (path / m).exists()]
        raise SquadNotFoundError(
            f"Squad path from {source_label} is missing required files: "
            f"{', '.join(missing)} (looked under {path})"
        )
    return path


def resolve_squad_root(override: str | os.PathLike[str] | None = None) -> Path:
    """Return the directory the CLI should treat as the squad payload root.

    Priority:
        1. `override` argument (typically wired from `--squad-src` flag)
        2. `LOVARCH_SQUAD_SRC` env var
        3. Bundled `lovarch_cli/squad/`

    Raises:
        SquadNotFoundError if no source resolves to a valid squad shape.
    """
    if override is not None:
        candidate = Path(override).expanduser().resolve()
        return _validate_or_raise(candidate, "--squad-src flag")

    env_path = os.environ.get(ENV_VAR)
    if env_path:
        candidate = Path(env_path).expanduser().resolve()
        return _validate_or_raise(candidate, f"${ENV_VAR}")

    if _BUNDLED_DIR.is_dir() and any(_BUNDLED_DIR.iterdir()):
        return _validate_or_raise(_BUNDLED_DIR, "bundled vendor")

    raise SquadNotFoundError(
        "No squad payload available. Bundled directory is empty and no "
        f"override was provided. Set ${ENV_VAR} to a squad source path, "
        "or pass --squad-src, or reinstall lovarch-cli."
    )


def squad_source_label(squad_root: Path) -> str:
    """Return a short human-readable label for where this path came from.

    Used by `lovarch dev show-squad-root` and run-summary panels.
    """
    if squad_root == _BUNDLED_DIR.resolve():
        return "bundled"
    env_path = os.environ.get(ENV_VAR)
    if env_path and Path(env_path).expanduser().resolve() == squad_root:
        return f"override (${ENV_VAR})"
    return "override (flag)"


def bundled_squad_dir() -> Path:
    """Public accessor for the bundled vendor path — used by refresh tooling."""
    return _BUNDLED_DIR
