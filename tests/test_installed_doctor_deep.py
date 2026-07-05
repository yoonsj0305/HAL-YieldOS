"""
tests/test_installed_doctor_deep.py

Tests for v2.7.1 installed-mode doctor --deep support.
Verifies:
  1. bundled yieldos/MANIFEST.json exists
  2. bundled MANIFEST has correct standard_output_bundle (22 files)
  3. root and bundled MANIFEST are consistent
  4. doctor deep runs correctly in forced installed mode (monkeypatched)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.installed_wheel

ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Test 1 — bundled MANIFEST.json exists inside the yieldos package
# ---------------------------------------------------------------------------

def test_bundled_manifest_exists():
    from importlib import resources

    pkg_root = resources.files("yieldos")
    # Support two possible locations
    candidates = [
        pkg_root / "MANIFEST.json",
        pkg_root / "resources" / "MANIFEST.json",
    ]
    found = False
    for c in candidates:
        try:
            if c.is_file():
                found = True
                break
        except Exception:
            pass
    assert found, "yieldos/MANIFEST.json (or yieldos/resources/MANIFEST.json) not found as package data"


# ---------------------------------------------------------------------------
# Test 2 — bundled MANIFEST has standard_output_bundle with 22 files
# ---------------------------------------------------------------------------

def test_bundled_manifest_standard_output_bundle():
    from importlib import resources

    pkg_root = resources.files("yieldos")
    path = pkg_root / "MANIFEST.json"
    if not path.is_file():
        path = pkg_root / "resources" / "MANIFEST.json"

    assert path.is_file(), "bundled MANIFEST.json not found"

    manifest = json.loads(path.read_text(encoding="utf-8"))
    bundle = manifest.get("standard_output_bundle", [])

    assert len(bundle) == 22, f"standard_output_bundle must have 22 files, got {len(bundle)}"
    assert "source_data_manifest.json" in bundle
    assert "data_quality_report.json" in bundle
    assert "evidence_conflict_report.json" in bundle
    assert "baseline_vs_yieldos.json" in bundle
    assert "business_case_summary.json" in bundle
    assert "case_manifest.json" in bundle


# ---------------------------------------------------------------------------
# Test 3 — root MANIFEST and bundled MANIFEST are consistent
# ---------------------------------------------------------------------------

def test_root_and_bundled_manifest_consistency():
    root_manifest_path = ROOT / "MANIFEST.json"
    if not root_manifest_path.exists():
        pytest.skip("Root MANIFEST.json not present (installed-only environment)")

    from importlib import resources

    pkg_root = resources.files("yieldos")
    bundled_path = pkg_root / "MANIFEST.json"
    if not bundled_path.is_file():
        bundled_path = pkg_root / "resources" / "MANIFEST.json"

    assert bundled_path.is_file(), "bundled MANIFEST.json not found"

    root_data = json.loads(root_manifest_path.read_text(encoding="utf-8"))
    bundled_data = json.loads(bundled_path.read_text(encoding="utf-8"))

    assert root_data["version"] == bundled_data["version"], (
        f"Version mismatch: root={root_data['version']}, bundled={bundled_data['version']}"
    )
    assert root_data["standard_output_bundle"] == bundled_data["standard_output_bundle"], (
        "standard_output_bundle differs between root and bundled MANIFEST"
    )
    assert root_data.get("domains") == bundled_data.get("domains"), (
        "domains differ between root and bundled MANIFEST"
    )


# ---------------------------------------------------------------------------
# Test 4 — doctor deep runs in forced installed mode (monkeypatch)
# ---------------------------------------------------------------------------

def test_doctor_deep_installed_mode_uses_metadata_and_bundled_manifest(monkeypatch):
    """
    Force installed mode by patching _find_project_root to return None,
    then run _run_deep_checks() and assert overall PASS.
    """
    from yieldos.cli import main as doctor_module

    # Patch _find_project_root to return None → forces installed mode
    monkeypatch.setattr(doctor_module, "_find_project_root", lambda: None)

    result = doctor_module._run_deep_checks()

    assert result.runtime_mode == "installed", (
        f"Expected runtime_mode='installed', got '{result.runtime_mode}'"
    )
    assert result.overall_status == "PASS", (
        "doctor deep installed mode FAILED. Checks:\n"
        + "\n".join(
            f"  [{'PASS' if ok else 'FAIL'}] {msg}" + (f"\n    hint: {h}" if not ok and h else "")
            for ok, msg, h in result.checks
        )
    )


# ---------------------------------------------------------------------------
# Test 5 — bundled VERSION exists
# ---------------------------------------------------------------------------

def test_bundled_version_exists():
    from importlib import resources

    pkg_root = resources.files("yieldos")
    vpath = pkg_root / "VERSION"
    try:
        exists = vpath.is_file()
    except Exception:
        exists = False
    assert exists, "yieldos/VERSION not found as package data"


# ---------------------------------------------------------------------------
# Test 6 — _find_project_root returns source root from source tree
# ---------------------------------------------------------------------------

def test_find_project_root_returns_source_root():
    from yieldos.cli.main import _find_project_root

    root = _find_project_root()
    # In the source tree (not installed-only), root should not be None
    assert root is not None, (
        "_find_project_root() returned None from source tree "
        "(VERSION, pyproject.toml, MANIFEST.json must all be present)"
    )
    assert (root / "VERSION").exists()
    assert (root / "pyproject.toml").exists()
    assert (root / "MANIFEST.json").exists()
