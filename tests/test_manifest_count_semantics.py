"""
tests/test_manifest_count_semantics.py

Verifies that MANIFEST.json has clear file count semantics:
- file_count_kind or checksummed_file_count present
- generated_release_files listed
- zip_entry_count >= checksummed_file_count if both present
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _manifest() -> dict:
    return json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))


def test_manifest_has_file_count_kind_or_checksummed_count():
    m = _manifest()
    has_kind = "file_count_kind" in m
    has_count = "checksummed_file_count" in m
    assert has_kind or has_count, \
        "MANIFEST.json must have 'file_count_kind' or 'checksummed_file_count'"


def test_manifest_has_generated_release_files():
    m = _manifest()
    assert "generated_release_files" in m, \
        "MANIFEST.json must have 'generated_release_files'"


def test_manifest_generated_release_files_includes_manifest():
    m = _manifest()
    grf = m.get("generated_release_files", [])
    assert "MANIFEST.json" in grf, \
        "generated_release_files must include 'MANIFEST.json'"


def test_manifest_generated_release_files_includes_checksums():
    m = _manifest()
    grf = m.get("generated_release_files", [])
    assert "CHECKSUMS.sha256" in grf, \
        "generated_release_files must include 'CHECKSUMS.sha256'"


def test_manifest_zip_entry_count_gte_checksummed_if_both_present():
    m = _manifest()
    if "zip_entry_count" in m and "checksummed_file_count" in m:
        assert m["zip_entry_count"] >= m["checksummed_file_count"], \
            "zip_entry_count must be >= checksummed_file_count"
