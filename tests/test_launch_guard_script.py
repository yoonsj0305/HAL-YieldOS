"""Tests for v3.0.9 — scripts/check_launch_guard.py existence and execution."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
GUARD_SCRIPT = ROOT / "scripts" / "check_launch_guard.py"


def test_launch_guard_exists():
    assert GUARD_SCRIPT.exists(), "scripts/check_launch_guard.py must exist"


def test_launch_guard_is_valid_python():
    import ast
    source = GUARD_SCRIPT.read_text(encoding="utf-8")
    try:
        ast.parse(source)
    except SyntaxError as e:
        raise AssertionError(f"check_launch_guard.py has syntax error: {e}") from e


def test_launch_guard_runs_successfully():
    result = subprocess.run(
        [sys.executable, str(GUARD_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=30,
    )
    assert result.returncode == 0, (
        f"check_launch_guard.py exited with code {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_launch_guard_prints_pass():
    result = subprocess.run(
        [sys.executable, str(GUARD_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=30,
    )
    assert "PASS" in result.stdout, (
        f"check_launch_guard.py must print PASS\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_launch_guard_exits_zero():
    result = subprocess.run(
        [sys.executable, str(GUARD_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=30,
    )
    assert result.returncode == 0, \
        f"check_launch_guard.py must exit 0, got {result.returncode}"


def test_launch_guard_does_not_require_network():
    text = GUARD_SCRIPT.read_text(encoding="utf-8")
    lower = text.lower()
    assert "requests" not in lower
    assert "urllib.request.urlopen" not in lower
    assert "http.client" not in lower
    assert "socket.connect" not in lower


def test_launch_guard_does_not_call_recovery_compiler():
    text = GUARD_SCRIPT.read_text(encoding="utf-8").lower()
    assert "run_recovery_compiler" not in text
    assert "hal-recovery-compiler" not in text


def test_launch_guard_does_not_generate_recovery_profile():
    text = GUARD_SCRIPT.read_text(encoding="utf-8")
    lower = text.lower()
    # recovery_profile.json should only appear in check/assertion context, not written
    if "recovery_profile.json" in lower:
        assert "write_text" not in lower or "recovery_profile" not in lower
        assert "open(" not in lower or "recovery_profile" not in lower
