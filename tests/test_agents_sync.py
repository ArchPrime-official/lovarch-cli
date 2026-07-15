"""Tests for the automatic start-up agents sync (ensure_agents_synced).

Twin of test_skills_sync, PLUS the guarantees that don't exist for skills and
that make it safe for user-authored agents:
  - a file the USER created is never overwritten or deleted;
  - a retired official agent (in the manifest, gone from the bundle) IS removed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from lovarch_cli.commands import agents_sync
from lovarch_cli.commands.agents_sync import ensure_agents_synced
from lovarch_cli.version import __version__

MANIFEST = ".agents-manifest.json"


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    monkeypatch.setattr("lovarch_cli.config.DEFAULT_HOME", tmp_path / ".lovarch")
    monkeypatch.delenv("LOVARCH_NO_AGENTS_SYNC", raising=False)
    return tmp_path


def _agent_files(dest: Path) -> set[str]:
    return {p.name for p in dest.glob("*.md")}


def test_installs_when_claude_present(fake_home):
    (fake_home / ".claude").mkdir()

    ensure_agents_synced()

    dest = fake_home / ".claude" / "agents"
    assert dest.is_dir()
    names = _agent_files(dest)
    assert "lovarch-content-chief.md" in names
    assert "lovarch-squad-creator.md" in names
    manifest = json.loads((fake_home / ".lovarch" / MANIFEST).read_text())
    assert manifest["version"] == __version__
    assert set(manifest["files"]) == names


def test_skips_when_no_claude_and_no_prior_install(fake_home):
    ensure_agents_synced()
    assert not (fake_home / ".claude").exists()


def test_opt_out_env(fake_home, monkeypatch):
    (fake_home / ".claude").mkdir()
    monkeypatch.setenv("LOVARCH_NO_AGENTS_SYNC", "1")

    ensure_agents_synced()

    assert not (fake_home / ".claude" / "agents").exists()


def test_idempotent_fast_path(fake_home):
    (fake_home / ".claude").mkdir()
    ensure_agents_synced()
    dest = fake_home / ".claude" / "agents"
    chief = dest / "lovarch-content-chief.md"
    before = chief.stat().st_mtime_ns

    ensure_agents_synced()  # second run: manifest version matches → no-op
    assert chief.stat().st_mtime_ns == before


def test_self_heals_if_deleted(fake_home):
    (fake_home / ".claude").mkdir()
    ensure_agents_synced()
    dest = fake_home / ".claude" / "agents"
    (dest / "lovarch-content-chief.md").unlink()  # user/system nuked one

    ensure_agents_synced()  # stamp matches but a bundled file is missing → re-sync
    assert (dest / "lovarch-content-chief.md").exists()


def test_preserves_user_created_agent(fake_home):
    """The whole point: a user's own agent survives every sync."""
    (fake_home / ".claude").mkdir()
    ensure_agents_synced()
    dest = fake_home / ".claude" / "agents"
    mine = dest / "mio-agente.md"
    mine.write_text("---\nname: mio-agente\ndescription: roba mia\n---\nciao", encoding="utf-8")

    # Force a re-sync (simulate a version bump) and confirm mine is untouched.
    ensure_agents_synced()
    assert mine.exists()
    assert "roba mia" in mine.read_text(encoding="utf-8")


def test_removes_retired_official_orphan(fake_home):
    """A file that WAS ours (in the manifest) but left the bundle gets removed —
    but only that one, never the user's files."""
    (fake_home / ".claude").mkdir()
    dest = fake_home / ".claude" / "agents"
    dest.mkdir(parents=True)
    # Simulate a previous version that had shipped an extra official agent.
    retired = dest / "lovarch-old-thing.md"
    retired.write_text("old", encoding="utf-8")
    mine = dest / "mio-agente.md"
    mine.write_text("mine", encoding="utf-8")
    (fake_home / ".lovarch").mkdir(parents=True)
    (fake_home / ".lovarch" / MANIFEST).write_text(
        json.dumps({"version": "0.0.1", "files": ["lovarch-old-thing.md"]}),
        encoding="utf-8",
    )

    ensure_agents_synced()

    assert not retired.exists()   # retired official agent removed
    assert mine.exists()          # user's own agent preserved


def test_best_effort_never_raises(fake_home, monkeypatch):
    (fake_home / ".claude").mkdir()

    def boom(*a, **k):
        raise RuntimeError("disk on fire")

    monkeypatch.setattr(agents_sync, "_sync_to", boom)
    # Must swallow — a sync hiccup can't break a real command.
    ensure_agents_synced()
