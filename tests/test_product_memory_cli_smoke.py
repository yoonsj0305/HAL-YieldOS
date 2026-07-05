"""
tests/test_product_memory_cli_smoke.py

Minimal CLI smoke test for the Product Memory Rebinning demo command.

Deep functional-yield validation is in test_product_memory_rebinning_demo.py
(default core suite, no subprocess).  This file only verifies that the CLI
entrypoint runs and produces key output files.

v2.8.10: CLI E2E Teardown + Product Memory Demo Isolation Patch.
"""
from __future__ import annotations

import subprocess
import sys

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


def test_product_memory_cli_smoke(tmp_path):
    """CLI product-demo must exit 0 and produce key output files."""
    out = tmp_path / "product_memory_cli"
    result = _run(["memory", "product-demo", "--out", str(out)], timeout=90)
    assert result.returncode == 0, (
        f"product-demo CLI failed (returncode={result.returncode}).\n"
        f"STDERR: {result.stderr[:400]}"
    )
    assert (out / "functional_passport.json").exists(), "functional_passport.json not generated"
    assert (out / "case_manifest.json").exists(), "case_manifest.json not generated"
    assert (out / "baseline_vs_yieldos.json").exists(), "baseline_vs_yieldos.json not generated"
