"""
tests/test_packaging_marker_smoke.py

Lightweight packaging smoke tests.
Marked with `packaging` so `python -m pytest -q -m packaging` selects at least one test
and returns exit code 0.

Does NOT run `python -m build` — that is reserved for release-heavy tests.
Reads the current version dynamically from VERSION so tests never need to be updated
when the version number changes.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.packaging

ROOT = Path(__file__).parent.parent


def _current_version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def test_version_file_exists():
    assert (ROOT / "VERSION").exists(), "VERSION must exist"


def test_version_file_non_empty():
    ver = _current_version()
    assert ver, "VERSION must not be empty"
    parts = ver.split(".")
    assert len(parts) >= 2, f"VERSION must be semver-like, got: '{ver}'"


def test_pyproject_toml_exists():
    assert (ROOT / "pyproject.toml").exists(), "pyproject.toml must exist"


def test_pyproject_toml_has_project_name():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "name" in text
    assert "yieldos" in text.lower()


def test_pyproject_toml_has_current_version():
    ver = _current_version()
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{ver}"' in text, \
        f"pyproject.toml must contain version = \"{ver}\", current VERSION is '{ver}'"


def test_pyproject_toml_has_entrypoint():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "yieldos" in text
    assert "[project.scripts]" in text


def test_manifest_json_exists():
    assert (ROOT / "MANIFEST.json").exists(), "MANIFEST.json must exist"


def test_manifest_json_has_current_version():
    ver = _current_version()
    data = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    assert data.get("version") == ver, \
        f"MANIFEST.json version must be '{ver}', got '{data.get('version')}'"


def test_manifest_json_has_domains():
    data = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    domains = data.get("domains", [])
    assert len(domains) >= 5
    assert "semiconductor" in domains
    assert "robot" in domains


def test_yieldos_version_file_matches():
    ver = _current_version()
    yv = (ROOT / "yieldos" / "VERSION").read_text(encoding="utf-8").strip()
    assert yv == ver, f"yieldos/VERSION must be '{ver}', got: '{yv}'"


def test_yieldos_manifest_version_matches():
    ver = _current_version()
    data = json.loads((ROOT / "yieldos" / "MANIFEST.json").read_text(encoding="utf-8"))
    assert data.get("version") == ver, \
        f"yieldos/MANIFEST.json version must be '{ver}', got '{data.get('version')}'"


def test_all_version_files_consistent():
    ver = _current_version()
    yv = (ROOT / "yieldos" / "VERSION").read_text(encoding="utf-8").strip()
    assert yv == ver, f"yieldos/VERSION ({yv}) != VERSION ({ver})"
    root_manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    pkg_manifest = json.loads((ROOT / "yieldos" / "MANIFEST.json").read_text(encoding="utf-8"))
    assert root_manifest["version"] == ver
    assert pkg_manifest["version"] == ver


def test_safety_flags_in_manifest():
    data = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    safety = data.get("safety", {})
    assert safety.get("read_only") is True
    assert safety.get("hardware_execution_enabled") is False
    assert safety.get("human_review_required") is True
