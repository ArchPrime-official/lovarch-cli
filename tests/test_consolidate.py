"""Tests for lovarch_cli.commands.consolidate.

Verifies ZIP creation, routing of files into the conventional folder
structure, last_dossier metadata persistence, and i18n.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
import typer
import yaml
from typer.testing import CliRunner

from lovarch_cli.commands.consolidate import _route_filename, consolidate_command


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _app() -> typer.Typer:
    app = typer.Typer()
    app.command(name="consolidate")(consolidate_command)
    return app


def _make_project(home: Path, name: str, files: dict[str, bytes] | None = None) -> Path:
    proj = home / "projects" / name
    out = proj / "output"
    out.mkdir(parents=True)
    (proj / "input").mkdir()
    (proj / "project.yaml").write_text(
        yaml.safe_dump({"name": name}), encoding="utf-8"
    )
    if files:
        for path, content in files.items():
            target = out / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
    return proj


# ──────────────────────────────────────────────────────────────────────────
# Routing logic
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("input-validation.json", "00-validation"),
        ("audit-report.pdf", "00-validation"),
        ("project-meta.json", "01-bootstrap"),
        ("moodboard-flatlay.png", "02-concept"),
        ("render-soggiorno.png", "02-concept"),
        ("dxf-pianta.dxf", "03-tier1"),
        ("ifc-modello.ifc", "03-tier1"),
        ("computo-metrico.xlsx", "03-tier1"),
        ("contratto-cnappc.pdf", "03-tier1"),
        ("qa-engineering-checklist.pdf", "04-tier2"),
        ("verifica-uni-11337.pdf", "04-tier2"),
        ("briefing-architect.pdf", "05-dossier"),
        ("regolatorio-it.pdf", "05-dossier"),
        ("energy-prelim.pdf", "05-dossier"),
        ("random-noise.txt", "99-other"),
    ],
)
def test_route_filename(filename: str, expected: str):
    assert _route_filename(filename) == expected


# ──────────────────────────────────────────────────────────────────────────
# ZIP creation
# ──────────────────────────────────────────────────────────────────────────


def test_consolidate_zips_routed_files(runner: CliRunner, tmp_path: Path):
    _make_project(
        tmp_path,
        "villa",
        files={
            "input-validation.json": b'{"verdict":"PASS"}',
            "moodboard-flatlay.jpg": b"\xff\xd8\xff",
            "dxf-pianta.dxf": b"DXF",
            "qa-engineering.pdf": b"%PDF",
            "weird-name.txt": b"orphan",
        },
    )
    result = runner.invoke(
        _app(),
        ["villa", "--home", str(tmp_path), "--lang=en"],
    )
    assert result.exit_code == 0, result.stdout

    zips = list((tmp_path / "projects" / "villa").glob("DOSSIER-villa-*.zip"))
    assert len(zips) == 1
    with zipfile.ZipFile(zips[0]) as zf:
        names = zf.namelist()
    assert "00-validation/input-validation.json" in names
    assert "02-concept/moodboard-flatlay.jpg" in names
    assert "03-tier1/dxf-pianta.dxf" in names
    assert "04-tier2/qa-engineering.pdf" in names
    assert "99-other/weird-name.txt" in names
    assert "README.md" in names


def test_consolidate_preserves_existing_subdirs(
    runner: CliRunner, tmp_path: Path
):
    """If the user already organized output/ into 0X-foo/, keep that layout."""
    _make_project(
        tmp_path,
        "villa",
        files={
            "03-tier1/custom-deliverable.pdf": b"%PDF",
            "moodboard-x.jpg": b"\xff\xd8\xff",
        },
    )
    runner.invoke(_app(), ["villa", "--home", str(tmp_path), "--lang=en"])
    zips = list((tmp_path / "projects" / "villa").glob("DOSSIER-*.zip"))
    with zipfile.ZipFile(zips[0]) as zf:
        names = zf.namelist()
    # User-organized path preserved as-is
    assert "03-tier1/custom-deliverable.pdf" in names
    # Routing still applies for top-level files
    assert "02-concept/moodboard-x.jpg" in names


def test_consolidate_persists_last_dossier(runner: CliRunner, tmp_path: Path):
    proj = _make_project(
        tmp_path,
        "villa",
        files={"moodboard-1.jpg": b"\xff\xd8\xff"},
    )
    runner.invoke(_app(), ["villa", "--home", str(tmp_path), "--lang=en"])
    meta = yaml.safe_load((proj / "project.yaml").read_text(encoding="utf-8"))
    assert "last_dossier" in meta
    assert meta["last_dossier"]["files"] == 1
    assert meta["last_dossier"]["path"].endswith(".zip")
    assert meta["last_dossier"]["size_bytes"] > 0


def test_consolidate_custom_output_dir(runner: CliRunner, tmp_path: Path):
    _make_project(tmp_path, "villa", files={"render-x.jpg": b"\xff\xd8\xff"})
    custom = tmp_path / "elsewhere"
    custom.mkdir()
    result = runner.invoke(
        _app(),
        ["villa", "--output", str(custom), "--home", str(tmp_path), "--lang=en"],
    )
    assert result.exit_code == 0
    assert list(custom.glob("DOSSIER-villa-*.zip"))


# ──────────────────────────────────────────────────────────────────────────
# Errors
# ──────────────────────────────────────────────────────────────────────────


def test_consolidate_no_project(runner: CliRunner, tmp_path: Path):
    result = runner.invoke(
        _app(), ["ghost", "--home", str(tmp_path), "--lang=en"]
    )
    assert result.exit_code == 2
    assert "not found" in result.stdout


def test_consolidate_no_output_dir(runner: CliRunner, tmp_path: Path):
    proj = tmp_path / "projects" / "villa"
    (proj / "input").mkdir(parents=True)
    result = runner.invoke(
        _app(), ["villa", "--home", str(tmp_path), "--lang=en"]
    )
    assert result.exit_code == 2
    assert "Output folder not found" in result.stdout


def test_consolidate_empty_output(runner: CliRunner, tmp_path: Path):
    _make_project(tmp_path, "villa", files=None)
    result = runner.invoke(
        _app(), ["villa", "--home", str(tmp_path), "--lang=en"]
    )
    assert result.exit_code == 1
    assert "empty" in result.stdout.lower()


# ──────────────────────────────────────────────────────────────────────────
# i18n
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "lang,marker",
    [
        ("it", "DOSSIER pronto"),
        ("pt", "DOSSIER pronto"),
        ("en", "DOSSIER ready"),
        ("es", "DOSSIER listo"),
    ],
)
def test_consolidate_localized(
    runner: CliRunner, tmp_path: Path, lang: str, marker: str
):
    _make_project(tmp_path, "villa", files={"render-x.jpg": b"\xff\xd8\xff"})
    result = runner.invoke(
        _app(), ["villa", f"--lang={lang}", "--home", str(tmp_path)]
    )
    assert result.exit_code == 0
    assert marker in result.stdout
