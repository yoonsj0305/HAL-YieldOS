"""
tests/test_release_scan_function.py

Unit tests for the scan_release_zip() function in scripts/build_release.py.
Tests verify that the scanner correctly detects hygiene violations and passes
clean archives without requiring a full build.

Marker: release_heavy (runs via `python -m pytest -q -m release_heavy`)
"""
from __future__ import annotations

import importlib.util
import json
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


def _make_zip(tmp_path: Path, entries: list[tuple[str, str]]) -> Path:
    zp = tmp_path / "test.zip"
    with zipfile.ZipFile(zp, "w") as zf:
        for name, content in entries:
            zf.writestr(name, content)
    return zp


# ── Module constants ──────────────────────────────────────────────────────────

def test_release_name_constant_has_version():
    mod = _load_build_release()
    assert hasattr(mod, "RELEASE_NAME")
    assert mod.VERSION in mod.RELEASE_NAME
    assert mod.RELEASE_NAME.startswith("HAL-YieldOS-v")
    assert mod.RELEASE_NAME.endswith("-poc-release")


def test_release_name_matches_zip_name():
    mod = _load_build_release()
    assert mod.ZIP_NAME == f"{mod.RELEASE_NAME}.zip"


def test_exclude_dir_prefixes_covers_dist_v():
    mod = _load_build_release()
    assert hasattr(mod, "EXCLUDE_DIR_PREFIXES")
    assert any(p.startswith("dist_v") for p in mod.EXCLUDE_DIR_PREFIXES), \
        "EXCLUDE_DIR_PREFIXES must cover dist_v* pattern"


def test_excluded_artifact_patterns_present():
    mod = _load_build_release()
    assert hasattr(mod, "EXCLUDED_ARTIFACT_PATTERNS")
    patterns = mod.EXCLUDED_ARTIFACT_PATTERNS
    assert any("dist_v" in p for p in patterns), "must include dist_v*/ pattern"
    assert any(".zip" in p for p in patterns), "must include *.zip pattern"
    assert any("__pycache__" in p for p in patterns), "must include __pycache__ pattern"


# ── scan_release_zip: violations ─────────────────────────────────────────────

def test_scan_detects_wrong_root_folder(tmp_path):
    mod = _load_build_release()
    zp = _make_zip(tmp_path, [("wrong-root/file.txt", "content")])
    violations = mod.scan_release_zip(zp, release_name="HAL-YieldOS-v3.0.0-poc-release")
    assert any("WRONG_ROOT" in v for v in violations), \
        f"Expected WRONG_ROOT violation, got: {violations}"


def test_scan_detects_build_dir(tmp_path):
    mod = _load_build_release()
    release_name = "HAL-YieldOS-v3.0.0-poc-release"
    zp = _make_zip(tmp_path, [(f"{release_name}/build/artifact.py", "content")])
    violations = mod.scan_release_zip(zp, release_name=release_name)
    assert any("/build/" in v for v in violations), \
        f"Expected /build/ violation, got: {violations}"


def test_scan_detects_pytest_tmp(tmp_path):
    mod = _load_build_release()
    release_name = "HAL-YieldOS-v3.0.0-poc-release"
    zp = _make_zip(tmp_path, [(f"{release_name}/.pytest_tmp/fake.txt", "content")])
    violations = mod.scan_release_zip(zp, release_name=release_name)
    assert any(".pytest_tmp" in v for v in violations), \
        f"Expected .pytest_tmp violation, got: {violations}"


def test_scan_detects_nested_zip(tmp_path):
    mod = _load_build_release()
    release_name = "HAL-YieldOS-v3.0.0-poc-release"
    zp = _make_zip(tmp_path, [(f"{release_name}/old_release.zip", "PK")])
    violations = mod.scan_release_zip(zp, release_name=release_name)
    assert any("NESTED_ZIP" in v or ".zip" in v for v in violations), \
        f"Expected nested zip violation, got: {violations}"


def test_scan_detects_pyc_files(tmp_path):
    mod = _load_build_release()
    release_name = "HAL-YieldOS-v3.0.0-poc-release"
    zp = _make_zip(tmp_path, [(f"{release_name}/yieldos/__pycache__/mod.cpython-312.pyc", "bc")])
    violations = mod.scan_release_zip(zp, release_name=release_name)
    assert violations, "Expected violations for .pyc or __pycache__, got none"


def test_scan_detects_dist_v_dir(tmp_path):
    mod = _load_build_release()
    release_name = "HAL-YieldOS-v3.0.0-poc-release"
    zp = _make_zip(tmp_path, [(f"{release_name}/dist_v289/old.whl", "PK")])
    violations = mod.scan_release_zip(zp, release_name=release_name)
    assert violations, "Expected violations for dist_v* or .whl, got none"


# ── scan_release_zip: clean zip ───────────────────────────────────────────────

def test_scan_passes_clean_zip(tmp_path):
    mod = _load_build_release()
    release_name = "HAL-YieldOS-v3.0.0-poc-release"
    entries = [
        (f"{release_name}/README.md", "# HAL YieldOS"),
        (f"{release_name}/yieldos/__init__.py", ""),
        (f"{release_name}/VERSION", "3.0.0"),
        (f"{release_name}/MANIFEST.json", json.dumps({"version": "3.0.0"})),
        (f"{release_name}/CHECKSUMS.sha256", "abc123  file.txt\n"),
    ]
    zp = _make_zip(tmp_path, entries)
    violations = mod.scan_release_zip(zp, release_name=release_name)
    assert not violations, "Expected clean zip, got violations:\n" + "\n".join(violations)


def test_scan_multiple_violations_all_reported(tmp_path):
    mod = _load_build_release()
    release_name = "HAL-YieldOS-v3.0.0-poc-release"
    entries = [
        ("wrong-root/file.txt", "x"),
        (f"{release_name}/build/artifact.py", "x"),
        (f"{release_name}/nested.zip", "PK"),
    ]
    zp = _make_zip(tmp_path, entries)
    violations = mod.scan_release_zip(zp, release_name=release_name)
    assert len(violations) >= 2, \
        f"Expected multiple violations, got: {violations}"
