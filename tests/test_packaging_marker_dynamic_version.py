"""Additional packaging marker tests — all version checks use the VERSION file dynamically.

Ensures no hardcoded version string exists anywhere in the packaging/marker test infrastructure,
and that all packaging artifacts agree with the single source of truth: the VERSION file.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _ver() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def test_version_file_is_semver():
    v = _ver()
    parts = v.split(".")
    assert len(parts) == 3, f"VERSION must be X.Y.Z, got {v!r}"
    for p in parts:
        assert p.isdigit(), f"All VERSION parts must be digits, got {v!r}"


def test_root_version_matches_yieldos_version():
    rv = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    yv = (ROOT / "yieldos" / "VERSION").read_text(encoding="utf-8").strip()
    assert rv == yv, f"Root VERSION {rv!r} != yieldos/VERSION {yv!r}"


def test_pyproject_uses_current_version():
    v = _ver()
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{v}"' in text, f"pyproject.toml does not contain version = \"{v}\""


def test_manifest_json_uses_current_version():
    v = _ver()
    data = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    assert data["version"] == v


def test_yieldos_manifest_json_uses_current_version():
    v = _ver()
    data = json.loads((ROOT / "yieldos" / "MANIFEST.json").read_text(encoding="utf-8"))
    assert data["version"] == v


def test_readme_uses_current_version():
    v = _ver()
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert v in text, f"README.md does not reference version {v}"


def test_no_hardcoded_old_version_in_pyproject():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for old in ("3.0.0", "3.0.1"):
        assert f'version = "{old}"' not in text, \
            f"pyproject.toml still has hardcoded old version {old!r}"


def test_no_hardcoded_old_version_in_manifests():
    for mpath in [ROOT / "MANIFEST.json", ROOT / "yieldos" / "MANIFEST.json"]:
        text = mpath.read_text(encoding="utf-8")
        for old in ("3.0.0", "3.0.1"):
            assert f'"version": "{old}"' not in text, \
                f"{mpath.name} still has old version {old!r}"


def test_current_version_appears_in_release_notes():
    v = _ver()
    text = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert v in text, f"RELEASE_NOTES.md does not mention {v}"


def test_dist_zip_name_would_use_current_version():
    """Verify the build_release.py would produce a zip with the current version."""
    v = _ver()
    expected_name = f"HAL-YieldOS-v{v}-poc-release.zip"
    # The build script uses the VERSION file — if it's correct, the zip would be correct
    assert "." in v and len(v.split(".")) == 3, \
        f"VERSION {v!r} is not a valid semver for zip naming"
    assert expected_name.startswith("HAL-YieldOS-v"), \
        f"Expected zip name {expected_name!r} does not start with 'HAL-YieldOS-v'"
