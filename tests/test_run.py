"""Tests for lovarch_cli.commands.run.

Exercises the run command without actually launching the squad pipeline:
subprocess.run is patched so we can assert the command line, env vars,
exit code propagation, and pre-flight gates (audit verdict, credits).

Smoke that pipes through to the real pipeline_runner.py is in
tests/test_e2e.py (marked @pytest.mark.slow).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import typer
import yaml
from typer.testing import CliRunner

from lovarch_cli.commands.run import run_command


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _app() -> typer.Typer:
    app = typer.Typer()
    app.command(name="run")(run_command)
    return app


def _make_project(home: Path, name: str, audit_verdict: str | None = "PASS") -> Path:
    """Build a minimal project layout with optional last_audit verdict."""
    proj = home / "projects" / name
    inp = proj / "input"
    inp.mkdir(parents=True)
    (proj / "output").mkdir()
    (inp / "briefing-cliente.md").write_text("# Brief")  # placeholder
    meta: dict = {"name": name, "workflow": "dal-brief-al-cantiere"}
    if audit_verdict is not None:
        meta["last_audit"] = {
            "verdict": audit_verdict,
            "pass_count": 18 if audit_verdict == "PASS" else 10,
            "concerns_count": 0,
            "fail_count": 0 if audit_verdict != "FAIL" else 5,
        }
    (proj / "project.yaml").write_text(yaml.safe_dump(meta), encoding="utf-8")
    return proj


def _fake_completed(returncode: int = 0):
    """Stub for subprocess.run that returns a CompletedProcess."""
    return subprocess.CompletedProcess(args=[], returncode=returncode)


# ──────────────────────────────────────────────────────────────────────────
# Pre-flight gates
# ──────────────────────────────────────────────────────────────────────────


def test_run_no_project(runner: CliRunner, tmp_path: Path):
    result = runner.invoke(
        _app(), ["does-not-exist", "--home", str(tmp_path), "--lang=en"]
    )
    assert result.exit_code == 2
    assert "not found" in result.stdout


def test_run_no_input_dir(runner: CliRunner, tmp_path: Path):
    proj = tmp_path / "projects" / "ghost"
    proj.mkdir(parents=True)
    result = runner.invoke(
        _app(), ["ghost", "--home", str(tmp_path), "--lang=en"]
    )
    assert result.exit_code == 2
    assert "Input folder not found" in result.stdout


def test_run_blocks_when_audit_never_run(runner: CliRunner, tmp_path: Path):
    _make_project(tmp_path, "villa", audit_verdict=None)
    result = runner.invoke(
        _app(), ["villa", "--home", str(tmp_path), "--lang=en"]
    )
    assert result.exit_code == 1
    assert "lovarch audit" in result.stdout


def test_run_blocks_when_audit_failed(runner: CliRunner, tmp_path: Path):
    _make_project(tmp_path, "villa", audit_verdict="FAIL")
    result = runner.invoke(
        _app(), ["villa", "--home", str(tmp_path), "--lang=en"]
    )
    assert result.exit_code == 1
    assert "Audit" in result.stdout and "failed" in result.stdout.lower()


def test_run_skip_audit_bypasses_gate(runner: CliRunner, tmp_path: Path):
    """--skip-audit should let a missing/failing audit through to subprocess."""
    proj = _make_project(tmp_path, "villa", audit_verdict=None)

    with patch(
        "lovarch_cli.commands.run.subprocess.run", return_value=_fake_completed(0)
    ) as mock_run, patch(
        "lovarch_cli.commands.run._pipeline_runner_path",
        return_value=proj,  # any existing path is fine
    ):
        result = runner.invoke(
            _app(),
            ["villa", "--home", str(tmp_path), "--skip-audit", "--lang=en"],
        )
    assert result.exit_code == 0
    mock_run.assert_called_once()


# ──────────────────────────────────────────────────────────────────────────
# Subprocess command construction
# ──────────────────────────────────────────────────────────────────────────


def test_run_free_mode_uses_dry_run_flag(runner: CliRunner, tmp_path: Path):
    proj = _make_project(tmp_path, "villa")
    runner_path = proj / "fake-pipeline-runner.py"
    runner_path.write_text("#!/usr/bin/env python3\n")

    with patch(
        "lovarch_cli.commands.run.subprocess.run", return_value=_fake_completed(0)
    ) as mock_run, patch(
        "lovarch_cli.commands.run._pipeline_runner_path",
        return_value=runner_path,
    ), patch(
        "lovarch_cli.commands.run._resolve_mode_from_creds",
        return_value=__import__(
            "lovarch_cli.clients.persistence", fromlist=["ExecutionMode"]
        ).ExecutionMode.FREE,
    ):
        result = runner.invoke(
            _app(), ["villa", "--home", str(tmp_path), "--lang=en"]
        )

    assert result.exit_code == 0
    cmd = mock_run.call_args[0][0]
    assert sys.executable in cmd
    assert str(runner_path) in cmd
    assert "--dry-run" in cmd
    assert "--real" not in cmd
    # input-dir points at the project's input/
    idx = cmd.index("--input-dir")
    assert cmd[idx + 1] == str(tmp_path / "projects" / "villa" / "input")


def test_run_force_dry_run_overrides_premium(runner: CliRunner, tmp_path: Path):
    """--dry-run flag forces FREE mode subprocess flag even on premium."""
    proj = _make_project(tmp_path, "villa")
    runner_path = proj / "fake-pipeline-runner.py"
    runner_path.write_text("#!/usr/bin/env python3\n")

    with patch(
        "lovarch_cli.commands.run.subprocess.run", return_value=_fake_completed(0)
    ) as mock_run, patch(
        "lovarch_cli.commands.run._pipeline_runner_path",
        return_value=runner_path,
    ):
        result = runner.invoke(
            _app(),
            ["villa", "--home", str(tmp_path), "--dry-run", "--lang=en"],
        )

    assert result.exit_code == 0
    cmd = mock_run.call_args[0][0]
    assert "--dry-run" in cmd


def test_run_propagates_subprocess_exit_code(runner: CliRunner, tmp_path: Path):
    proj = _make_project(tmp_path, "villa")
    runner_path = proj / "fake-pipeline-runner.py"
    runner_path.write_text("#!/usr/bin/env python3\n")

    with patch(
        "lovarch_cli.commands.run.subprocess.run", return_value=_fake_completed(7)
    ), patch(
        "lovarch_cli.commands.run._pipeline_runner_path",
        return_value=runner_path,
    ):
        result = runner.invoke(
            _app(), ["villa", "--home", str(tmp_path), "--lang=en"]
        )

    # subprocess returncode 7 → CLI exits 7, not 0
    assert result.exit_code == 7
    assert "failed" in result.stdout.lower()


def test_run_no_runner_aborts(runner: CliRunner, tmp_path: Path):
    """Bundled pipeline_runner.py missing → exit 2 with helpful message."""
    _make_project(tmp_path, "villa")
    missing = tmp_path / "definitely-not-here.py"
    with patch(
        "lovarch_cli.commands.run._pipeline_runner_path", return_value=missing
    ):
        result = runner.invoke(
            _app(), ["villa", "--home", str(tmp_path), "--lang=en"]
        )
    assert result.exit_code == 2
    assert "pipeline_runner not found" in result.stdout


# ──────────────────────────────────────────────────────────────────────────
# Env vars
# ──────────────────────────────────────────────────────────────────────────


def test_run_passes_env_vars_to_subprocess(runner: CliRunner, tmp_path: Path):
    proj = _make_project(tmp_path, "villa")
    runner_path = proj / "fake-pipeline-runner.py"
    runner_path.write_text("#!/usr/bin/env python3\n")

    with patch(
        "lovarch_cli.commands.run.subprocess.run", return_value=_fake_completed(0)
    ) as mock_run, patch(
        "lovarch_cli.commands.run._pipeline_runner_path",
        return_value=runner_path,
    ):
        runner.invoke(
            _app(),
            ["villa", "--home", str(tmp_path), "--workflow", "custom-flow", "--lang=en"],
        )

    env = mock_run.call_args.kwargs["env"]
    assert env["LOVARCH_PROJECT_NAME"] == "villa"
    assert env["LOVARCH_WORKFLOW"] == "custom-flow"


# ──────────────────────────────────────────────────────────────────────────
# i18n in 4 langs
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "lang,marker",
    [
        ("it", "Modalità"),
        ("pt", "Modo"),
        ("en", "Mode:"),
        ("es", "Modo"),
    ],
)
def test_run_localized(
    runner: CliRunner, tmp_path: Path, lang: str, marker: str
):
    proj = _make_project(tmp_path, "villa")
    runner_path = proj / "fake-pipeline-runner.py"
    runner_path.write_text("#!/usr/bin/env python3\n")

    with patch(
        "lovarch_cli.commands.run.subprocess.run", return_value=_fake_completed(0)
    ), patch(
        "lovarch_cli.commands.run._pipeline_runner_path",
        return_value=runner_path,
    ):
        result = runner.invoke(
            _app(),
            ["villa", "--home", str(tmp_path), f"--lang={lang}"],
        )

    assert result.exit_code == 0
    assert marker in result.stdout
