"""
tests/test_pilot_cli.py

CLI integration tests for `yieldos pilot init` and `yieldos pilot check`.
Direct Python tests use cmd_pilot_init/cmd_pilot_check directly.
Subprocess smoke tests are marked cli_e2e.
"""
from __future__ import annotations

import subprocess
import sys
import types
from pathlib import Path

import pytest

SAMPLES_ROOT = Path(__file__).parent.parent / "samples"

# ── Direct Python dispatch tests (default core suite) ────────────────────────


def _make_init_args(domain: str, out: Path):
    args = types.SimpleNamespace(domain=domain, out=str(out))
    return args


def _make_check_args(domain: str, input_dir: Path, out: Path):
    args = types.SimpleNamespace(domain=domain, input=str(input_dir), out=str(out))
    return args


def test_cmd_pilot_init_robot(tmp_path):
    from yieldos.pilot.cli import cmd_pilot_init

    out = tmp_path / "pilot_init_robot"
    rc = cmd_pilot_init(_make_init_args("robot", out))
    assert rc == 0
    # canonical files
    assert (out / "pilot_input_contract.json").exists()
    assert (out / "pilot_boundary_statement.md").exists()
    assert (out / "README.md").exists()
    # compat aliases still generated
    assert (out / "pilot_contract.json").exists()
    assert (out / "boundary_statement.json").exists()


def test_cmd_pilot_init_all_domains(tmp_path):
    from yieldos.pilot.cli import cmd_pilot_init

    for domain in ["robot", "semiconductor", "space", "memory", "semiforge"]:
        out = tmp_path / f"init_{domain}"
        rc = cmd_pilot_init(_make_init_args(domain, out))
        assert rc == 0, f"pilot init failed for domain: {domain}"
        assert (out / "pilot_input_contract.json").exists(), (
            f"{domain}: pilot_input_contract.json not generated"
        )
        assert (out / "sample_file_manifest.json").exists(), (
            f"{domain}: sample_file_manifest.json not generated"
        )
        assert (out / "missing_data_request_template.json").exists(), (
            f"{domain}: missing_data_request_template.json not generated"
        )
        assert (out / "sanitization_checklist.md").exists(), (
            f"{domain}: sanitization_checklist.md not generated"
        )
        assert (out / "pilot_boundary_statement.md").exists(), (
            f"{domain}: pilot_boundary_statement.md not generated"
        )
        assert (out / "README.md").exists(), (
            f"{domain}: README.md not generated"
        )


def test_cmd_pilot_init_invalid_domain_returns_1(tmp_path):
    from yieldos.pilot.cli import cmd_pilot_init

    out = tmp_path / "bad"
    rc = cmd_pilot_init(_make_init_args("not_real", out))
    assert rc == 1


def test_cmd_pilot_check_robot_sample(tmp_path):
    from yieldos.pilot.cli import cmd_pilot_check

    out = tmp_path / "check_robot"
    rc = cmd_pilot_check(_make_check_args("robot", SAMPLES_ROOT / "pilot_robot", out))
    assert rc == 0
    # canonical files
    assert (out / "pilot_readiness_report.json").exists()
    assert (out / "missing_data_request.json").exists()
    assert (out / "data_sufficiency_preview.json").exists()
    assert (out / "pilot_decision_boundary.json").exists()
    # compat aliases
    assert (out / "readiness_report.json").exists()


def test_cmd_pilot_check_all_sample_domains(tmp_path):
    from yieldos.pilot.cli import cmd_pilot_check

    for domain in ["robot", "semiconductor", "space", "memory", "semiforge"]:
        sample_dir = SAMPLES_ROOT / f"pilot_{domain}"
        out = tmp_path / f"check_{domain}"
        rc = cmd_pilot_check(_make_check_args(domain, sample_dir, out))
        assert rc == 0, f"pilot check failed for domain: {domain}"
        assert (out / "pilot_readiness_report.json").exists(), (
            f"{domain}: pilot_readiness_report.json not generated"
        )
        assert (out / "pilot_decision_boundary.json").exists(), (
            f"{domain}: pilot_decision_boundary.json not generated"
        )


def test_cmd_pilot_check_missing_input_dir_returns_1(tmp_path):
    from yieldos.pilot.cli import cmd_pilot_check

    out = tmp_path / "check_out"
    rc = cmd_pilot_check(_make_check_args("robot", tmp_path / "nonexistent", out))
    assert rc == 1


# ── Subprocess smoke tests (cli_e2e, excluded from default suite) ─────────────

pytestmark_cli = pytest.mark.cli_e2e


def _run_cli(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "yieldos.cli.main", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


@pytest.mark.cli_e2e
def test_pilot_init_cli_smoke(tmp_path):
    out = tmp_path / "pilot_init_smoke"
    result = _run_cli(["pilot", "init", "--domain", "semiconductor", "--out", str(out)])
    assert result.returncode == 0, f"STDERR: {result.stderr[:300]}"
    # canonical
    assert (out / "pilot_input_contract.json").exists()
    assert (out / "README.md").exists()
    # compat aliases
    assert (out / "pilot_contract.json").exists()
    assert (out / "pilot_readme.md").exists()


@pytest.mark.cli_e2e
def test_pilot_check_cli_smoke(tmp_path):
    out = tmp_path / "pilot_check_smoke"
    sample = SAMPLES_ROOT / "pilot_semiconductor"
    result = _run_cli([
        "pilot", "check",
        "--domain", "semiconductor",
        "--input", str(sample),
        "--out", str(out),
    ])
    assert result.returncode == 0, f"STDERR: {result.stderr[:300]}"
    # canonical
    assert (out / "pilot_readiness_report.json").exists()
    assert (out / "pilot_decision_boundary.json").exists()
    # compat aliases
    assert (out / "readiness_report.json").exists()
    assert (out / "next_steps.json").exists()
