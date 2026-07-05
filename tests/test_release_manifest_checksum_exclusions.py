"""
tests/test_release_manifest_checksum_exclusions.py

Verifies that CHECKSUMS.sha256 inside the release zip does not reference
excluded artifacts (cache dirs, build artifacts, old dist_v* dirs, wheels, etc.).

Also verifies MANIFEST.json inside the zip is consistent with version and
does not reference excluded paths.

Uses the shared `release_zip_path` session fixture from conftest.py.
The release archive is built once per pytest session and reused here.

Marker: release_heavy
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


def _read_checksums_from_zip(zip_path: Path, release_name: str) -> str:
    with zipfile.ZipFile(zip_path) as zf:
        return zf.read(f"{release_name}/CHECKSUMS.sha256").decode("utf-8")


def _read_manifest_from_zip(zip_path: Path, release_name: str) -> dict:
    with zipfile.ZipFile(zip_path) as zf:
        return json.loads(zf.read(f"{release_name}/MANIFEST.json"))


# ── CHECKSUMS.sha256 exclusion checks ────────────────────────────────────────

CHECKSUMS_FORBIDDEN = [
    ".pytest_tmp", ".pytest_cache", ".ruff_cache", "__pycache__",
    "output/", "dist_v", ".whl", ".tar.gz", ".zip", "/build/", "/dist/",
]


@pytest.mark.parametrize("forbidden", CHECKSUMS_FORBIDDEN)
def test_checksums_does_not_contain_excluded_path(forbidden, release_zip_path):
    mod = _load_build_release()
    checksums = _read_checksums_from_zip(release_zip_path, mod.RELEASE_NAME)
    offending = [
        line for line in checksums.splitlines()
        if forbidden in line
    ]
    assert not offending, (
        f"CHECKSUMS.sha256 must not reference {forbidden!r}:\n"
        + "\n".join(offending[:5])
    )


def test_checksums_entries_use_versioned_root(release_zip_path):
    mod = _load_build_release()
    checksums = _read_checksums_from_zip(release_zip_path, mod.RELEASE_NAME)
    for line in checksums.splitlines():
        if not line.strip():
            continue
        parts = line.split("  ", 1)
        assert len(parts) == 2, f"Malformed checksum line: {line!r}"
        path_part = parts[1]
        assert path_part.startswith(f"{mod.RELEASE_NAME}/"), (
            f"Checksum entry path must start with {mod.RELEASE_NAME!r}/: {path_part!r}"
        )


def test_checksums_does_not_reference_halyieldos_prefix(release_zip_path):
    mod = _load_build_release()
    checksums = _read_checksums_from_zip(release_zip_path, mod.RELEASE_NAME)
    stale = [
        line for line in checksums.splitlines()
        if "  halyieldos/" in line
    ]
    assert not stale, (
        "CHECKSUMS.sha256 must not use stale 'halyieldos/' prefix:\n"
        + "\n".join(stale[:5])
    )


# ── MANIFEST.json checks ──────────────────────────────────────────────────────

def test_manifest_version_is_current(release_zip_path):
    mod = _load_build_release()
    manifest = _read_manifest_from_zip(release_zip_path, mod.RELEASE_NAME)
    assert manifest["version"] == mod.VERSION, (
        f"MANIFEST.json version {manifest['version']!r} != {mod.VERSION!r}"
    )


def test_manifest_release_name_field(release_zip_path):
    mod = _load_build_release()
    manifest = _read_manifest_from_zip(release_zip_path, mod.RELEASE_NAME)
    assert manifest.get("release_name") == mod.RELEASE_NAME, (
        f"MANIFEST.json release_name must be {mod.RELEASE_NAME!r}"
    )


def test_manifest_checksummed_file_count_positive(release_zip_path):
    mod = _load_build_release()
    manifest = _read_manifest_from_zip(release_zip_path, mod.RELEASE_NAME)
    assert isinstance(manifest.get("checksummed_file_count"), int)
    assert manifest["checksummed_file_count"] > 0


def test_manifest_excluded_artifact_patterns_present(release_zip_path):
    mod = _load_build_release()
    manifest = _read_manifest_from_zip(release_zip_path, mod.RELEASE_NAME)
    patterns = manifest.get("excluded_artifact_patterns")
    assert isinstance(patterns, list)
    assert len(patterns) > 0, "excluded_artifact_patterns must not be empty"
    pattern_str = " ".join(patterns)
    assert "__pycache__" in pattern_str
    assert ".zip" in pattern_str
    assert "dist_v" in pattern_str


def test_manifest_generated_release_files(release_zip_path):
    mod = _load_build_release()
    manifest = _read_manifest_from_zip(release_zip_path, mod.RELEASE_NAME)
    gen = manifest.get("generated_release_files", [])
    assert "MANIFEST.json" in gen
    assert "CHECKSUMS.sha256" in gen
