"""
tests/conftest.py

Shared pytest fixtures for the YieldOS test suite.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    pass


_ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def release_zip_path() -> Path:
    """Build the official release zip once per pytest session.

    All release-heavy archive-inspection tests must use this fixture
    instead of calling scripts/build_release.py individually per test.
    """
    result = subprocess.run(
        [sys.executable, "scripts/build_release.py"],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
        cwd=str(_ROOT),
    )
    assert result.returncode == 0, (
        f"build_release.py failed:\n{result.stdout}\n{result.stderr}"
    )
    spec = importlib.util.spec_from_file_location(
        "build_release",
        _ROOT / "scripts" / "build_release.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    zip_path = _ROOT / "dist" / mod.ZIP_NAME
    assert zip_path.exists(), f"Release zip not found after build: {zip_path}"
    return zip_path


@pytest.fixture(autouse=True)
def _clear_yieldos_test_env(monkeypatch: pytest.MonkeyPatch):
    """Prevent environment-variable leakage between CLI tests."""
    for key in (
        "YIELDOS_OUTPUT_DIR",
        "YIELDOS_CASE_DIR",
        "YIELDOS_CONFIG",
    ):
        monkeypatch.delenv(key, raising=False)
    yield


@pytest.fixture(autouse=True)
def _cleanup_product_memory_output():
    """Clean up product-memory demo output dirs that may land in CWD."""
    yield
    for path in (
        Path("output/product_memory_rebinning"),
        Path("output/product_memory_demo"),
    ):
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)


# ── Direct demo runner fixtures ────────────────────────────────────────────────
# Use these instead of spawning CLI subprocesses in tests.
# run_domain_demo_direct() / run_all_domain_demos_direct() call the same
# underlying analysis and report-writing code as the CLI — no subprocess overhead.


@pytest.fixture
def demo_case_factory(tmp_path):
    """Return a factory that generates a single-domain demo output directory.

    Usage::

        def test_foo(demo_case_factory):
            out = demo_case_factory("semiconductor")
            fp = json.loads((out / "functional_passport.json").read_text())
            ...
    """
    from yieldos.demo_runner import run_domain_demo_direct

    def _make(domain: str) -> Path:
        out = tmp_path / domain
        return run_domain_demo_direct(domain=domain, out_dir=out)

    return _make


@pytest.fixture(scope="module")
def all_demo_cases(tmp_path_factory):
    """Generate all five domain demo outputs once per test module.

    Returns ``{"robot": Path, "space": Path, "semiconductor": Path,
               "semiforge": Path, "memory": Path}``.

    Scope is *module* so that each test file that uses this fixture generates
    the demos once, but different test files don't share (and potentially
    conflict over) the same output directory.
    """
    from yieldos.demo_runner import run_all_domain_demos_direct

    out = tmp_path_factory.mktemp("all_demo_cases")
    return run_all_domain_demos_direct(out_dir=out)
