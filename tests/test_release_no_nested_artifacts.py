"""
tests/test_release_no_nested_artifacts.py

Verifies that the release zip produced by scripts/build_release.py does not
include old nested release zips, dist_v* folders, output/demo artifacts, or
.pytest_tmp artifacts.

Uses the shared `release_zip_path` session fixture from conftest.py.
The release archive is built once per pytest session and reused here.

Marker: release_heavy
"""
from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.release_heavy

ROOT = Path(__file__).parent.parent


def _load_build_release():
    spec = importlib.util.spec_from_file_location(
        "build_release",
        ROOT / "scripts" / "build_release.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _get_entries(zip_path: Path) -> list[str]:
    with zipfile.ZipFile(zip_path) as zf:
        return zf.namelist()


# ── No nested zip files ───────────────────────────────────────────────────────

def test_no_nested_zip_files(release_zip_path):
    entries = _get_entries(release_zip_path)
    nested_zips = [e for e in entries if e.endswith(".zip")]
    assert not nested_zips, (
        f"Release zip must not contain nested zip files: {nested_zips}"
    )


def test_no_old_release_zip_by_name(release_zip_path):
    entries = _get_entries(release_zip_path)
    old = [e for e in entries if "v2.9.1-poc-release.zip" in e or "v2.9.2-poc-release.zip" in e]
    assert not old, f"Release zip must not contain old release zips: {old}"


# ── No dist_v* directories ────────────────────────────────────────────────────

def test_no_dist_v_directories(release_zip_path):
    entries = _get_entries(release_zip_path)
    dist_v = [e for e in entries if "/dist_v" in e]
    assert not dist_v, f"Release zip must not contain dist_v* entries: {dist_v}"


# ── No output/demo artifacts ──────────────────────────────────────────────────

def test_no_output_directory(release_zip_path):
    entries = _get_entries(release_zip_path)
    output_entries = [e for e in entries if "/output/" in e or "/outputs/" in e]
    assert not output_entries, (
        f"Release zip must not contain output/ entries: {output_entries[:5]}"
    )


# ── No .pytest_tmp artifacts ──────────────────────────────────────────────────

def test_no_pytest_tmp_artifacts(release_zip_path):
    entries = _get_entries(release_zip_path)
    tmp = [e for e in entries if ".pytest_tmp" in e]
    assert not tmp, f"Release zip must not contain .pytest_tmp entries: {tmp}"


# ── No wheel files ────────────────────────────────────────────────────────────

def test_no_wheel_files(release_zip_path):
    entries = _get_entries(release_zip_path)
    wheels = [e for e in entries if e.endswith(".whl")]
    assert not wheels, f"Release zip must not contain .whl files: {wheels}"


# ── build_release.py hygiene scan passes ─────────────────────────────────────

def test_build_release_hygiene_scan_passes(release_zip_path):
    """Verify that scan_release_zip() passes on the session-built zip."""
    mod = _load_build_release()
    violations = mod.scan_release_zip(release_zip_path)
    assert not violations, (
        "scan_release_zip() found violations in built zip:\n"
        + "\n".join(violations)
    )
