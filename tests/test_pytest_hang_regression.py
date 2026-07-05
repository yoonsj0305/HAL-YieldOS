"""
tests/test_pytest_hang_regression.py

Regression guard: CLI subprocess calls must complete within a bounded timeout.

v2.8.5: Pytest Hang regression guard.
v2.8.8: Simplified — CLI smoke tests moved to test_cli_smoke.py.
        This file retains the memory product-demo hang guard and the static
        subprocess-timeout check for test_product_memory_rebinning_demo.py.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers import run_yieldos_cli as run_cli

pytestmark = pytest.mark.cli_e2e


def test_memory_product_demo_exits_within_timeout(tmp_path):
    """Memory product-demo CLI must exit, not hang, within 120 seconds."""
    out = tmp_path / "product_demo"
    result = run_cli(["memory", "product-demo", "--out", str(out)], timeout=120)
    assert result.returncode == 0, (
        f"product-demo exited with error (returncode={result.returncode}).\n"
        f"STDERR: {result.stderr[:500]}"
    )


def test_all_cli_timeouts_are_bounded():
    """Static check: all subprocess.run() calls in product-demo test have timeout."""
    demo_file = Path(__file__).parent / "test_product_memory_rebinning_demo.py"
    if not demo_file.exists():
        return
    content = demo_file.read_text(encoding="utf-8")
    lines = content.splitlines()
    in_subprocess_block = False
    missing = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "subprocess.run(" in stripped:
            in_subprocess_block = True
            block_start = i
            block_lines = [stripped]
        elif in_subprocess_block:
            block_lines.append(stripped)
            if ")," in stripped or stripped.endswith(")"):
                block_text = " ".join(block_lines)
                if "timeout=" not in block_text:
                    missing.append(f"line {block_start + 1}: {lines[block_start].strip()}")
                in_subprocess_block = False
                block_lines = []
    assert not missing, (
        "subprocess.run() calls without timeout in test_product_memory_rebinning_demo.py:\n"
        + "\n".join(missing)
    )
