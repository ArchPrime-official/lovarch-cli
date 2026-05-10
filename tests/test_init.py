"""Tests for lovarch_cli.commands.init.

Exercises:
- Name validation (regex)
- Directory layout creation
- --sample flag (with mocked bundled sample)
- --force overwrite behavior
- Pre-existing project rejection
- project.yaml metadata content
- i18n in 4 langs

Uses tmp_path to isolate $HOME and never touches the real ~/.lovarch/.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import typer
import yaml
from typer.testing import CliRunner

from lovarch_cli.commands.init import init_command


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _app() -> typer.Typer:
    app = typer.Typer()
    app.command(name="init")(init_command)
    return app


def _make_fake_sample(tmp_path: Path) -> Path:
    """Build a tiny fake sample-input dir so we don't depend on the real squad."""
    src = tmp_path / "fake-sample"
    src.mkdir()
    (src / "briefing-cliente.md").write_text("# Brief\n", encoding="utf-8")
    (src / "stato-attuale.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    sub = src / "foto"
    sub.mkdir()
    (sub / "01-ingresso.jpg").write_bytes(b"\xff\xd8\xff")
    (sub / "02-soggiorno.jpg").write_bytes(b"\xff\xd8\xff")
    return src


# ──────────────────────────────────────────────────────────────────────────
# Name validation
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "bad_name",
    [
        "A",                # too short + uppercase
        "x",                # too short
        "Has_Underscores",  # underscores not allowed
        "has spaces",       # spaces
        "../etc/passwd",    # path traversal
        "UPPER",            # uppercase
        "-leading-dash",    # cannot start with dash
        "a" * 64,           # too long (>63)
    ],
)
def test_invalid_names_rejected(runner: CliRunner, tmp_path: Path, bad_name: str):
    # Use `--` to stop Typer flag parsing so leading-dash names reach our regex.
    result = runner.invoke(
        _app(), ["--home", str(tmp_path), "--lang=en", "--", bad_name]
    )
    assert result.exit_code == 2
    assert "Invalid name" in result.stdout or "Invalid" in result.stdout


@pytest.mark.parametrize(
    "good_name",
    [
        "ab",                 # minimum length 2
        "my-villa",
        "villa-chianti-2026",
        "a1b2",
        "x" + "y" * 62,       # exactly 63 chars
    ],
)
def test_valid_names_accepted(runner: CliRunner, tmp_path: Path, good_name: str):
    result = runner.invoke(
        _app(), [good_name, "--home", str(tmp_path), "--lang=en"]
    )
    assert result.exit_code == 0, result.stdout
    assert (tmp_path / "projects" / good_name).is_dir()


# ──────────────────────────────────────────────────────────────────────────
# Directory layout
# ──────────────────────────────────────────────────────────────────────────

def test_init_creates_input_and_output_dirs(runner: CliRunner, tmp_path: Path):
    result = runner.invoke(
        _app(), ["villa-test", "--home", str(tmp_path), "--lang=en"]
    )
    assert result.exit_code == 0
    proj = tmp_path / "projects" / "villa-test"
    assert proj.is_dir()
    assert (proj / "input").is_dir()
    assert (proj / "output").is_dir()
    assert (proj / "project.yaml").is_file()


def test_project_yaml_contains_metadata(runner: CliRunner, tmp_path: Path):
    result = runner.invoke(
        _app(),
        [
            "villa-test",
            "--home", str(tmp_path),
            "--workflow", "custom-workflow",
            "--lang=en",
        ],
    )
    assert result.exit_code == 0
    meta = yaml.safe_load(
        (tmp_path / "projects" / "villa-test" / "project.yaml").read_text()
    )
    assert meta["name"] == "villa-test"
    assert meta["workflow"] == "custom-workflow"
    assert meta["sample"] is False
    assert "created_at" in meta
    assert "cli_version" in meta


# ──────────────────────────────────────────────────────────────────────────
# --sample flag
# ──────────────────────────────────────────────────────────────────────────

def test_sample_flag_copies_resolved_source(
    runner: CliRunner, tmp_path: Path
):
    """When the downloader resolves a sample (bundled/cache/download), init
    copies its contents into the project's input/ dir."""
    fake_src = _make_fake_sample(tmp_path)
    from lovarch_cli.sample_downloader import SampleSource

    with patch(
        "lovarch_cli.sample_downloader.resolve_sample_source",
        return_value=SampleSource(path=fake_src, origin="cache"),
    ):
        result = runner.invoke(
            _app(),
            ["villa-test", "--sample", "--home", str(tmp_path), "--lang=en"],
        )
    assert result.exit_code == 0
    input_dir = tmp_path / "projects" / "villa-test" / "input"
    assert (input_dir / "briefing-cliente.md").is_file()
    assert (input_dir / "stato-attuale.png").is_file()
    assert (input_dir / "foto" / "01-ingresso.jpg").is_file()
    assert (input_dir / "foto" / "02-soggiorno.jpg").is_file()
    # Output mentions the count of copied files (4 files in our fake sample).
    assert "4" in result.stdout
    # Metadata records --sample was used
    meta = yaml.safe_load(
        (tmp_path / "projects" / "villa-test" / "project.yaml").read_text()
    )
    assert meta["sample"] is True


def test_sample_download_error_does_not_fail_dir_creation(
    runner: CliRunner, tmp_path: Path
):
    """If the downloader cannot obtain the sample (offline, checksum fail, etc.),
    the project dir is still created so the user can populate input/ manually."""
    from lovarch_cli.sample_downloader import SampleDownloadError

    with patch(
        "lovarch_cli.sample_downloader.resolve_sample_source",
        side_effect=SampleDownloadError("network down"),
    ):
        result = runner.invoke(
            _app(),
            ["villa-test", "--sample", "--home", str(tmp_path), "--lang=en"],
        )
    # Exit 0 because we don't bail — user can still add input manually.
    assert result.exit_code == 0
    assert (tmp_path / "projects" / "villa-test" / "input").is_dir()
    # The downloader's error message is surfaced to the user
    assert "network down" in result.stdout


# ──────────────────────────────────────────────────────────────────────────
# Existing project handling
# ──────────────────────────────────────────────────────────────────────────

def test_existing_project_rejected_without_force(
    runner: CliRunner, tmp_path: Path
):
    # First create
    runner.invoke(_app(), ["villa-test", "--home", str(tmp_path), "--lang=en"])
    # Second attempt should fail
    result = runner.invoke(
        _app(), ["villa-test", "--home", str(tmp_path), "--lang=en"]
    )
    assert result.exit_code == 1
    assert "already exists" in result.stdout
    assert "--force" in result.stdout


def test_force_flag_overwrites_existing(runner: CliRunner, tmp_path: Path):
    # First create + drop a marker file
    runner.invoke(_app(), ["villa-test", "--home", str(tmp_path), "--lang=en"])
    marker = tmp_path / "projects" / "villa-test" / "input" / "user-file.txt"
    marker.write_text("legacy content")
    assert marker.exists()

    # --force re-creates from scratch (legacy file gone)
    result = runner.invoke(
        _app(),
        ["villa-test", "--force", "--home", str(tmp_path), "--lang=en"],
    )
    assert result.exit_code == 0
    assert not marker.exists()
    # But fresh layout exists
    assert (tmp_path / "projects" / "villa-test" / "input").is_dir()


# ──────────────────────────────────────────────────────────────────────────
# i18n in 4 langs
# ──────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "lang,marker",
    [
        ("it", "Progetto"),
        ("pt", "Projeto"),
        ("en", "Project"),
        ("es", "Proyecto"),
    ],
)
def test_init_localized_in_4_langs(
    runner: CliRunner, tmp_path: Path, lang: str, marker: str
):
    result = runner.invoke(
        _app(),
        ["villa-test", f"--lang={lang}", "--home", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert marker in result.stdout
