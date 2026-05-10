"""Tests for lovarch_cli.commands.status."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import typer
import yaml
from typer.testing import CliRunner

from lovarch_cli.commands.status import _format_relative_age, status_command


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _app() -> typer.Typer:
    app = typer.Typer()
    app.command(name="status")(status_command)
    return app


def _make_project(
    home: Path,
    name: str,
    workflow: str = "dal-brief-al-cantiere",
    audit: dict | None = None,
    dossier: dict | None = None,
) -> Path:
    proj = home / "projects" / name
    proj.mkdir(parents=True)
    (proj / "input").mkdir()
    (proj / "output").mkdir()
    meta: dict = {
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "workflow": workflow,
        "sample": False,
    }
    if audit is not None:
        meta["last_audit"] = audit
    if dossier is not None:
        meta["last_dossier"] = dossier
    (proj / "project.yaml").write_text(yaml.safe_dump(meta), encoding="utf-8")
    return proj


# ──────────────────────────────────────────────────────────────────────────
# _format_relative_age
# ──────────────────────────────────────────────────────────────────────────


def test_relative_age_seconds():
    ts = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()
    assert "s ago" in _format_relative_age(ts)


def test_relative_age_minutes():
    ts = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    assert "5m ago" in _format_relative_age(ts)


def test_relative_age_hours():
    ts = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    assert "3h ago" in _format_relative_age(ts)


def test_relative_age_days():
    ts = (datetime.now(timezone.utc) - timedelta(days=2, hours=1)).isoformat()
    assert "2d ago" in _format_relative_age(ts)


def test_relative_age_none():
    assert _format_relative_age(None) == "-"


def test_relative_age_invalid_string():
    assert _format_relative_age("not-an-iso-string") == "not-an-iso-string"


# ──────────────────────────────────────────────────────────────────────────
# Empty / missing state
# ──────────────────────────────────────────────────────────────────────────


def test_status_no_projects_dir(runner: CliRunner, tmp_path: Path):
    result = runner.invoke(
        _app(), ["--home", str(tmp_path), "--lang=en"]
    )
    assert result.exit_code == 0
    assert "No projects yet" in result.stdout


def test_status_empty_projects_dir(runner: CliRunner, tmp_path: Path):
    (tmp_path / "projects").mkdir()
    result = runner.invoke(
        _app(), ["--home", str(tmp_path), "--lang=en"]
    )
    assert result.exit_code == 0
    # Hint about lovarch init villa-test --sample
    assert "villa-test" in result.stdout


# ──────────────────────────────────────────────────────────────────────────
# List view
# ──────────────────────────────────────────────────────────────────────────


def test_status_list_shows_all_projects(runner: CliRunner, tmp_path: Path):
    _make_project(tmp_path, "villa-a")
    _make_project(
        tmp_path,
        "villa-b",
        audit={
            "verdict": "PASS",
            "pass_count": 18,
            "concerns_count": 0,
            "fail_count": 0,
        },
    )
    _make_project(
        tmp_path,
        "villa-c",
        audit={"verdict": "FAIL", "pass_count": 8, "concerns_count": 2, "fail_count": 8},
        dossier={
            "files": 27,
            "size_bytes": 1024 * 50,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    result = runner.invoke(
        _app(), ["--home", str(tmp_path), "--lang=en"]
    )
    assert result.exit_code == 0
    assert "villa-a" in result.stdout
    assert "villa-b" in result.stdout
    assert "villa-c" in result.stdout
    assert "PASS" in result.stdout
    assert "FAIL" in result.stdout


# ──────────────────────────────────────────────────────────────────────────
# Detail view
# ──────────────────────────────────────────────────────────────────────────


def test_status_detail_shows_audit_and_dossier(
    runner: CliRunner, tmp_path: Path
):
    _make_project(
        tmp_path,
        "villa",
        audit={
            "verdict": "PASS",
            "pass_count": 18,
            "concerns_count": 0,
            "fail_count": 0,
        },
        dossier={
            "files": 27,
            "size_bytes": 102_400,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "path": "/home/test/villa/DOSSIER-villa-2026-05-10.zip",
        },
    )

    result = runner.invoke(
        _app(), ["villa", "--home", str(tmp_path), "--lang=en"]
    )
    assert result.exit_code == 0
    assert "Project status" in result.stdout
    assert "PASS" in result.stdout
    assert "27" in result.stdout  # files
    assert "100" in result.stdout  # 102400 // 1024 = 100 KB


def test_status_detail_no_audit_yet(runner: CliRunner, tmp_path: Path):
    _make_project(tmp_path, "villa")
    result = runner.invoke(
        _app(), ["villa", "--home", str(tmp_path), "--lang=en"]
    )
    assert result.exit_code == 0
    assert "not run yet" in result.stdout


def test_status_detail_project_not_found(
    runner: CliRunner, tmp_path: Path
):
    (tmp_path / "projects").mkdir()
    result = runner.invoke(
        _app(), ["does-not-exist", "--home", str(tmp_path), "--lang=en"]
    )
    assert result.exit_code == 2
    assert "not found" in result.stdout


# ──────────────────────────────────────────────────────────────────────────
# i18n
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "lang,marker",
    [
        ("it", "Progetti lovarch"),
        ("pt", "Projetos lovarch"),
        ("en", "lovarch projects"),
        ("es", "Proyectos lovarch"),
    ],
)
def test_status_list_localized(
    runner: CliRunner, tmp_path: Path, lang: str, marker: str
):
    _make_project(tmp_path, "villa")
    result = runner.invoke(
        _app(), ["--home", str(tmp_path), f"--lang={lang}"]
    )
    assert result.exit_code == 0
    assert marker in result.stdout
