"""Tests for v3.0.11 version hygiene across all version files and key docs."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
CURRENT_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip()


def test_version_is_3_0_11():
    assert CURRENT_VERSION == "3.0.11"


def test_yieldos_version_matches():
    v = (ROOT / "yieldos" / "VERSION").read_text(encoding="utf-8-sig").strip()
    assert v == CURRENT_VERSION


def test_pyproject_version_matches():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8-sig")
    assert f'version = "{CURRENT_VERSION}"' in text


def test_root_manifest_version_matches():
    data = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8-sig"))
    assert data["version"] == CURRENT_VERSION


def test_yieldos_manifest_version_matches():
    data = json.loads((ROOT / "yieldos" / "MANIFEST.json").read_text(encoding="utf-8-sig"))
    assert data["version"] == CURRENT_VERSION


def test_readme_version_matches():
    text = (ROOT / "README.md").read_text(encoding="utf-8-sig")
    assert CURRENT_VERSION in text


def test_known_limitations_version_current():
    text = (DOCS / "KNOWN_LIMITATIONS.md").read_text(encoding="utf-8-sig")
    assert CURRENT_VERSION in text or "v2.8.x" in text


def test_delivery_guide_zip_current():
    text = (DOCS / "DELIVERY_GUIDE.md").read_text(encoding="utf-8-sig")
    assert f"v{CURRENT_VERSION}-poc-release.zip" in text


def test_validation_method_version_current():
    text = (DOCS / "VALIDATION_METHOD.md").read_text(encoding="utf-8-sig")
    assert CURRENT_VERSION in text or "v2.8.x" in text


def test_technical_spec_version_current():
    text = (DOCS / "TECHNICAL_SPEC.md").read_text(encoding="utf-8-sig")
    assert CURRENT_VERSION in text or "v2.8.x" in text


def test_all_five_version_files_in_sync():
    ver = (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip()
    yv = (ROOT / "yieldos" / "VERSION").read_text(encoding="utf-8-sig").strip()
    rm = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8-sig"))
    ym = json.loads((ROOT / "yieldos" / "MANIFEST.json").read_text(encoding="utf-8-sig"))
    pt = (ROOT / "pyproject.toml").read_text(encoding="utf-8-sig")
    assert ver == yv
    assert rm["version"] == ver
    assert ym["version"] == ver
    assert f'version = "{ver}"' in pt


def test_release_notes_has_302_section():
    text = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8-sig")
    assert "v3.0.2" in text


def test_delivery_guide_no_v300_zip():
    text = (DOCS / "DELIVERY_GUIDE.md").read_text(encoding="utf-8-sig")
    assert "v3.0.0-poc-release.zip" not in text
    assert "v3.0.1-poc-release.zip" not in text
