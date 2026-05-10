"""Tests for lovarch_cli.commands.audit.

Drives the 18-point checklist against synthetic project layouts in tmp_path:
- All inputs valid → verdict PASS, exit 0, all checks green
- Missing required (briefing) → verdict FAIL, exit 1
- Missing recommended only → verdict CONCERNS, exit 0
- No project / no input dir → exit 2 with localized error
- --json output is machine-readable and contains all 18 checks
- project.yaml gets the last_audit summary appended

Avoids touching the real ~/.lovarch/ via --home override.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer
import yaml
from typer.testing import CliRunner

from lovarch_cli.commands.audit import audit_command


def _app() -> typer.Typer:
    app = typer.Typer()
    app.command(name="audit")(audit_command)
    return app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


# ──────────────────────────────────────────────────────────────────────────
# Synthetic project builders
# ──────────────────────────────────────────────────────────────────────────


_FULL_BRIEFING = """\
# Briefing Cliente

## Cliente
Lorenzo Ferri (45 anni) e Alessandra Conti (42 anni).

## Programma
Restauro casa colonica 1850 + cantina vinificazione.

## Budget
Budget construction: 420.000 EUR + onorari 38.000 EUR.

## Tempi
Tempi di cantiere: 165 giorni · target apertura aprile 2027.

## Vincoli
Vincoli paesaggistici Chianti Classico + soprintendenza belle arti.

## Stile
Stile Tuscan country-modern, materiali locali in vista.

## Spazi
Spazi: cucina laboratorio, foresteria, cantina, soggiorno principale.

## Famiglia
La famiglia ha un figlio di 10 anni e un cane.

## Abitudini
Abitudini quotidiane: smart-working + cucinare per ospiti.

## Materiali
Materiali firma: cotto toscano, pietra serena, legno castagno.

## Sostenibilità
Sostenibilità: pannelli solari, recupero acque piovane, fitodepurazione.
""" + "\n" * 50  # padding to satisfy ≥50 lines


def _make_full_project(home: Path, name: str) -> Path:
    """Build a project layout that should pass all 18 checks."""
    proj = home / "projects" / name
    inp = proj / "input"
    inp.mkdir(parents=True)
    (proj / "output").mkdir()

    (inp / "briefing-cliente.md").write_text(_FULL_BRIEFING, encoding="utf-8")
    (inp / "stato-attuale.dxf").write_bytes(b"\x00" * 10_000)
    (inp / "stato-attuale.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 2_000)
    (inp / "visura-catastale.pdf").write_bytes(b"%PDF-1.4\n" + b"\x00" * 2_000)
    (inp / "architetto-info.json").write_text(
        json.dumps({
            "nome": "Pablo Ruan",
            "iscrizione_ordine": "OAPPC Firenze 1234",
            "codice_fiscale": "RNPBLR85A01H501Z",
        }),
        encoding="utf-8",
    )
    foto = inp / "foto"
    foto.mkdir()
    for i in range(1, 7):
        (foto / f"{i:02d}-foto.jpg").write_bytes(b"\xff\xd8\xff")
    pin = inp / "pinterest-references"
    pin.mkdir()
    for i in range(1, 7):
        (pin / f"ref-{i}.jpg").write_bytes(b"\xff\xd8\xff")

    # project.yaml so audit can persist last_audit summary
    (proj / "project.yaml").write_text(
        yaml.safe_dump({"name": name, "workflow": "dal-brief-al-cantiere"}),
        encoding="utf-8",
    )
    return proj


# ──────────────────────────────────────────────────────────────────────────
# Verdicts
# ──────────────────────────────────────────────────────────────────────────


def test_audit_pass_full_project(runner: CliRunner, tmp_path: Path):
    _make_full_project(tmp_path, "villa-test")
    result = runner.invoke(
        _app(),
        ["villa-test", "--home", str(tmp_path), "--lang=en"],
    )
    assert result.exit_code == 0, result.stdout
    # All 18 marked PASS
    assert result.stdout.count("PASS") >= 18
    assert "FAIL" not in result.stdout or "FAILED" not in result.stdout


def test_audit_fail_missing_required_briefing(
    runner: CliRunner, tmp_path: Path
):
    proj = _make_full_project(tmp_path, "villa-test")
    (proj / "input" / "briefing-cliente.md").unlink()

    result = runner.invoke(
        _app(),
        ["villa-test", "--home", str(tmp_path), "--lang=en"],
    )
    # FAIL because briefing is required
    assert result.exit_code == 1, result.stdout
    assert "FAIL" in result.stdout


def test_audit_fail_missing_visura(runner: CliRunner, tmp_path: Path):
    proj = _make_full_project(tmp_path, "villa-test")
    (proj / "input" / "visura-catastale.pdf").unlink()
    result = runner.invoke(
        _app(),
        ["villa-test", "--home", str(tmp_path), "--lang=en"],
    )
    assert result.exit_code == 1


def test_audit_concerns_when_recommended_missing(
    runner: CliRunner, tmp_path: Path
):
    """Required checks all pass but a recommended one fails → CONCERNS, exit 0."""
    proj = _make_full_project(tmp_path, "villa-test")
    # Wipe sustainability mentions from briefing to drop briefing_sostenibilita
    text = (proj / "input" / "briefing-cliente.md").read_text(encoding="utf-8")
    text = text.replace("Sostenibilità", "X").replace("sostenibilità", "x")
    (proj / "input" / "briefing-cliente.md").write_text(text, encoding="utf-8")

    result = runner.invoke(
        _app(),
        ["villa-test", "--home", str(tmp_path), "--lang=en"],
    )
    # Exit 0 because no required check failed.
    assert result.exit_code == 0
    assert "CONCERNS" in result.stdout


# ──────────────────────────────────────────────────────────────────────────
# Errors
# ──────────────────────────────────────────────────────────────────────────


def test_audit_nonexistent_project(runner: CliRunner, tmp_path: Path):
    result = runner.invoke(
        _app(),
        ["does-not-exist", "--home", str(tmp_path), "--lang=en"],
    )
    assert result.exit_code == 2
    assert "not found" in result.stdout


def test_audit_no_input_dir(runner: CliRunner, tmp_path: Path):
    proj = tmp_path / "projects" / "villa-empty"
    proj.mkdir(parents=True)
    result = runner.invoke(
        _app(),
        ["villa-empty", "--home", str(tmp_path), "--lang=en"],
    )
    assert result.exit_code == 2
    assert "Input folder not found" in result.stdout


# ──────────────────────────────────────────────────────────────────────────
# --json output
# ──────────────────────────────────────────────────────────────────────────


def test_audit_json_output(runner: CliRunner, tmp_path: Path):
    _make_full_project(tmp_path, "villa-test")
    result = runner.invoke(
        _app(),
        ["villa-test", "--json", "--home", str(tmp_path), "--lang=en"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["project"] == "villa-test"
    assert payload["verdict"] == "PASS"
    assert len(payload["checks"]) == 18
    # First check is briefing_present
    assert payload["checks"][0]["key"] == "briefing_present"
    # Last is briefing_sostenibilita
    assert payload["checks"][17]["key"] == "briefing_sostenibilita"


def test_audit_json_fail_exit_1(runner: CliRunner, tmp_path: Path):
    proj = _make_full_project(tmp_path, "villa-test")
    (proj / "input" / "briefing-cliente.md").unlink()
    result = runner.invoke(
        _app(),
        ["villa-test", "--json", "--home", str(tmp_path), "--lang=en"],
    )
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["verdict"] == "FAIL"


# ──────────────────────────────────────────────────────────────────────────
# Side effects: project.yaml gets last_audit appended
# ──────────────────────────────────────────────────────────────────────────


def test_audit_persists_last_audit_in_yaml(
    runner: CliRunner, tmp_path: Path
):
    _make_full_project(tmp_path, "villa-test")
    runner.invoke(_app(), ["villa-test", "--home", str(tmp_path), "--lang=en"])

    yaml_path = tmp_path / "projects" / "villa-test" / "project.yaml"
    meta = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    assert meta["last_audit"]["verdict"] == "PASS"
    assert meta["last_audit"]["pass_count"] == 18
    assert meta["last_audit"]["fail_count"] == 0


# ──────────────────────────────────────────────────────────────────────────
# i18n in 4 langs
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "lang,marker",
    [
        ("it", "controlli"),
        ("pt", "verificações"),
        ("en", "checks"),
        ("es", "controles"),
    ],
)
def test_audit_localized(
    runner: CliRunner, tmp_path: Path, lang: str, marker: str
):
    _make_full_project(tmp_path, "villa-test")
    result = runner.invoke(
        _app(),
        ["villa-test", f"--lang={lang}", "--home", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert marker in result.stdout
