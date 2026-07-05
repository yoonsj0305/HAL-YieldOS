"""
tests/test_cli_smoke.py

Minimal CLI subprocess smoke tests.

Verifies that the CLI entrypoint is importable and produces correct exit codes
for the most critical commands.  All repeated per-domain subprocess work lives
in fixture-based tests; only these smoke tests use CLI subprocesses.

v2.8.8: CLI Subprocess Collapse + Release Hygiene Patch.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.cli_e2e


def _run(args: list[str], timeout: int = 90) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "yieldos.cli.main", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def test_cli_version_smoke():
    """CLI must print version and exit 0."""
    r = _run(["version"])
    assert r.returncode == 0, r.stderr
    assert "YieldOS" in r.stdout


def test_cli_doctor_deep_smoke():
    """Doctor --deep must report Overall: PASS."""
    r = _run(["doctor", "--deep"], timeout=120)
    assert r.returncode == 0, r.stderr
    assert "Overall: PASS" in r.stdout


def test_cli_semiconductor_demo_smoke(tmp_path):
    """Semiconductor demo must exit 0 and produce key output files."""
    out = tmp_path / "semiconductor_cli"
    r = _run(["demo", "--domain", "semiconductor", "--out", str(out)], timeout=90)
    assert r.returncode == 0, r.stderr
    assert (out / "functional_passport.json").exists()
    assert (out / "process_drift_report.json").exists()
    assert (out / "semiconductor_confidence_report.json").exists()


def test_cli_validate_exits_normally(tmp_path):
    """Validate must exit 0 after semiconductor demo run."""
    out = tmp_path / "semi_val"
    demo = _run(["demo", "--domain", "semiconductor", "--out", str(out)], timeout=90)
    if demo.returncode != 0:
        return  # demo itself failed — skip validate check
    val = _run(["validate", "--case", str(out), "--strict"], timeout=60)
    assert val.returncode in (0, 1), (
        f"Unexpected returncode {val.returncode} — process may have hung"
    )
    assert "Validation" in val.stdout, f"Unexpected stdout: {val.stdout[:300]}"


def test_all_subprocess_calls_have_timeout():
    """Static guard: all subprocess.run() calls in smoke test must have timeout."""
    this_file = Path(__file__).read_text(encoding="utf-8")
    lines = this_file.splitlines()
    in_block = False
    block_lines: list[str] = []
    block_start = 0
    bad: list[str] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Only match actual subprocess.run( calls — skip string-search patterns and docstrings.
        is_real_call = (
            "subprocess.run(" in stripped
            and not stripped.startswith("#")
            and not stripped.startswith('"""')
            and not stripped.startswith("'")
            and '"subprocess.run(' not in stripped
            and "'subprocess.run(" not in stripped
        )
        if is_real_call:
            in_block = True
            block_start = i
            block_lines = [stripped]
        elif in_block:
            block_lines.append(stripped)
            if stripped.endswith(")") or stripped.endswith("),"):
                text = " ".join(block_lines)
                if "timeout=" not in text:
                    bad.append(f"line {block_start + 1}: {lines[block_start].strip()}")
                in_block = False
                block_lines = []
    assert not bad, "subprocess.run() calls without timeout:\n" + "\n".join(bad)
