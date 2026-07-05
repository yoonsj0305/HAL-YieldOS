"""
tests/test_release_hygiene_excludes_pytest_tmp.py

Verifies that the release ZIP builder excludes .pytest_tmp/ and other
test-only artifacts.

Uses the shared `release_zip_path` session fixture from conftest.py.
The release archive is built once per pytest session and reused here.

v2.8.8: Release Hygiene Patch.
v2.9.5: Refactored to use shared session fixture (no per-test rebuild).
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.release_heavy

_ROOT = Path(__file__).parent.parent


def test_release_builder_excludes_pytest_tmp(release_zip_path):
    """Release ZIP must not include .pytest_tmp/ contents."""
    with zipfile.ZipFile(release_zip_path) as zf:
        names = zf.namelist()
    offenders = [n for n in names if ".pytest_tmp" in n or "should_not_ship" in n]
    assert not offenders, (
        "Release ZIP contains .pytest_tmp/ entries:\n" + "\n".join(offenders)
    )


def test_release_builder_excludes_pytest_cache(release_zip_path):
    """Release ZIP must not include .pytest_cache/ contents."""
    with zipfile.ZipFile(release_zip_path) as zf:
        names = zf.namelist()
    offenders = [n for n in names if ".pytest_cache" in n or "__pycache__" in n]
    assert not offenders, (
        "Release ZIP contains test cache entries:\n" + "\n".join(offenders[:10])
    )
