"""Tests for the automatic start-up skills sync (ensure_skills_synced).

The sync keeps ~/.claude/skills in lockstep with the installed CLI version.
It must be idempotent, self-healing, non-invasive and best-effort.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from lovarch_cli.commands import skills_cmd
from lovarch_cli.commands.skills_cmd import ensure_skills_synced
from lovarch_cli.version import __version__


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Redirect Path.home() and DEFAULT_HOME to a throwaway directory."""
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    # ensure_skills_synced imports DEFAULT_HOME from config at call time.
    monkeypatch.setattr("lovarch_cli.config.DEFAULT_HOME", tmp_path / ".lovarch")
    monkeypatch.delenv("LOVARCH_NO_SKILLS_SYNC", raising=False)
    return tmp_path


def _skill_names(dest_root: Path) -> set[str]:
    return {p.name for p in dest_root.glob("*") if (p / "SKILL.md").exists()}


def test_installs_when_claude_present(fake_home):
    (fake_home / ".claude").mkdir()

    ensure_skills_synced()

    dest = fake_home / ".claude" / "skills"
    assert dest.is_dir()
    assert _skill_names(dest)  # at least one skill copied
    # stamp records the current version
    assert (fake_home / ".lovarch" / ".skills-synced").read_text().strip() == __version__


def test_skips_when_no_claude_and_no_prior_install(fake_home):
    # No ~/.claude → user doesn't run Claude Code → don't provision it.
    ensure_skills_synced()
    assert not (fake_home / ".claude").exists()


def test_opt_out_env(fake_home, monkeypatch):
    (fake_home / ".claude").mkdir()
    monkeypatch.setenv("LOVARCH_NO_SKILLS_SYNC", "1")

    ensure_skills_synced()

    assert not (fake_home / ".claude" / "skills").exists()


def test_idempotent_fast_path(fake_home):
    (fake_home / ".claude").mkdir()
    ensure_skills_synced()
    dest = fake_home / ".claude" / "skills"
    before = {p.name: p.stat().st_mtime_ns for p in dest.glob("*")}

    # Second run must be a no-op (stamp matches, dest present): nothing recopied.
    ensure_skills_synced()
    after = {p.name: p.stat().st_mtime_ns for p in dest.glob("*")}

    assert before == after


def test_self_heals_deleted_skills(fake_home):
    (fake_home / ".claude").mkdir()
    ensure_skills_synced()
    dest = fake_home / ".claude" / "skills"

    # Stamp still says current version, but the skills were removed.
    import shutil

    shutil.rmtree(dest)
    assert (fake_home / ".lovarch" / ".skills-synced").read_text().strip() == __version__

    ensure_skills_synced()
    assert dest.is_dir() and _skill_names(dest)


def test_resyncs_on_version_change(fake_home):
    (fake_home / ".claude").mkdir()
    ensure_skills_synced()
    stamp = fake_home / ".lovarch" / ".skills-synced"

    # Simulate an older install: stamp from a previous version.
    stamp.write_text("0.0.1", encoding="utf-8")

    ensure_skills_synced()
    assert stamp.read_text().strip() == __version__


def test_never_raises_on_failure(fake_home, monkeypatch):
    (fake_home / ".claude").mkdir()
    # Force the copy to blow up; ensure_skills_synced must swallow it.
    monkeypatch.setattr(
        skills_cmd, "_sync_to", lambda *_a, **_k: (_ for _ in ()).throw(OSError("boom"))
    )
    ensure_skills_synced()  # no exception propagates
