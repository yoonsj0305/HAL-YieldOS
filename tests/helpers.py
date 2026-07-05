"""
tests/helpers.py

Shared CLI test helpers for the YieldOS test suite.
All subprocess-based CLI calls go through run_yieldos_cli() to ensure:
  - Consistent timeout enforcement (default 60 s, override as needed).
  - sys.executable used instead of the 'yieldos' console script, avoiding
    PATH / venv resolution differences.
  - capture_output=True so pipes never fill and deadlock.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_yieldos_cli(
    args: list[str],
    *,
    timeout: int = 60,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run `python -m yieldos.cli.main <args>` with a hard timeout."""
    return subprocess.run(
        [sys.executable, "-m", "yieldos.cli.main", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
        check=False,
    )
