"""
tests/test_release_hygiene.py

Verifies that the release zip produced by scripts/build_release.py:
  - excludes build/, dist/, __pycache__, .pyc, .whl, .tar.gz
  - does not contain stale v2.1.0 / v2.3.0 artifact filenames
  - README does not claim "all 4 domain demos"
  - EXCLUDE_DIRS in build_release.py contains the required entries
"""
from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.release_heavy

ROOT = Path(__file__).parent.parent

# ── build_release.py constants ──────────────────────────────────────────────

def _load_build_release():
    spec = importlib.util.spec_from_file_location(
        "build_release",
        ROOT / "scripts" / "build_release.py",
    )
    mod = importlib.util.module_from_spec(spec)
    # main() is guarded with __name__ == "__main__" so exec_module is safe
    spec.loader.exec_module(mod)
    return mod


def test_build_release_excludes_build_dir():
    mod = _load_build_release()
    assert "build" in mod.EXCLUDE_DIRS, \
        "'build' must be in EXCLUDE_DIRS so build/ is not included in release zip"


def test_build_release_excludes_dist_dir():
    mod = _load_build_release()
    assert "dist" in mod.EXCLUDE_DIRS, \
        "'dist' must be in EXCLUDE_DIRS"


def test_build_release_excludes_output_dir():
    mod = _load_build_release()
    assert "output" in mod.EXCLUDE_DIRS, \
        "'output' must be in EXCLUDE_DIRS"


def test_build_release_excludes_pycache():
    mod = _load_build_release()
    assert "__pycache__" in mod.EXCLUDE_DIRS


def test_build_release_excludes_pytest_cache():
    mod = _load_build_release()
    assert ".pytest_cache" in mod.EXCLUDE_DIRS


def test_build_release_excludes_dist_v_prefix():
    mod = _load_build_release()
    assert hasattr(mod, "EXCLUDE_DIR_PREFIXES"), \
        "build_release must have EXCLUDE_DIR_PREFIXES for pattern-based dir exclusion"
    assert any(p.startswith("dist_v") for p in mod.EXCLUDE_DIR_PREFIXES), \
        "EXCLUDE_DIR_PREFIXES must cover dist_v* pattern (dist_v287, dist_v288, etc.)"


def test_build_release_excludes_whl():
    mod = _load_build_release()
    assert ".whl" in mod.EXCLUDE_EXTS, \
        "'.whl' must be in EXCLUDE_EXTS"


def test_build_release_excludes_tar_gz():
    mod = _load_build_release()
    assert ".tar.gz" in mod.EXCLUDE_EXTS, \
        "'.tar.gz' must be in EXCLUDE_EXTS"


def test_build_release_excludes_pyc():
    mod = _load_build_release()
    assert ".pyc" in mod.EXCLUDE_EXTS


# ── make_release_zip.py is deprecated ───────────────────────────────────────

def test_make_release_zip_is_deprecated():
    """scripts/make_release_zip.py must carry a DEPRECATED marker."""
    legacy = ROOT / "scripts" / "make_release_zip.py"
    assert legacy.exists(), "scripts/make_release_zip.py must still exist (retained for history)"
    content = legacy.read_text(encoding="utf-8")
    assert "DEPRECATED" in content, \
        "make_release_zip.py must be marked DEPRECATED"


def test_make_release_zip_not_used_in_build_release():
    """build_release.py must not import or exec make_release_zip."""
    build = (ROOT / "scripts" / "build_release.py").read_text(encoding="utf-8")
    assert "make_release_zip" not in build


# ── README hygiene ───────────────────────────────────────────────────────────

def test_readme_does_not_say_4_domain_demos():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "all 4 domain demos" not in readme.lower(), \
        "README must not say 'all 4 domain demos' — should say 5"


def test_readme_says_5_domain_demos():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "5 domain" in readme.lower() or "5-domain" in readme.lower() or \
           "run all 5" in readme.lower(), \
        "README must reference 5 domains somewhere"


# ── Release zip contents ──────────────────────────────────────────────────────
# Uses the shared release_zip_path session fixture from conftest.py.
# The archive is built once and reused — no per-test rebuild.

def _get_zip_entries(zip_path: Path) -> list[str]:
    with zipfile.ZipFile(zip_path) as zf:
        return zf.namelist()


def test_release_zip_excludes_build_dir(release_zip_path):
    entries = _get_zip_entries(release_zip_path)
    bad = [e for e in entries if "/build/" in e]
    assert not bad, f"Release zip must not contain build/ entries: {bad[:5]}"


def test_release_zip_excludes_dist_dir(release_zip_path):
    entries = _get_zip_entries(release_zip_path)
    bad = [e for e in entries if "/dist/" in e]
    assert not bad, f"Release zip must not contain dist/ entries: {bad[:5]}"


def test_release_zip_excludes_pyc(release_zip_path):
    entries = _get_zip_entries(release_zip_path)
    bad = [e for e in entries if e.endswith(".pyc")]
    assert not bad, f"Release zip must not contain .pyc files: {bad[:5]}"


def test_release_zip_excludes_pycache(release_zip_path):
    entries = _get_zip_entries(release_zip_path)
    bad = [e for e in entries if "__pycache__" in e]
    assert not bad, f"Release zip must not contain __pycache__ entries: {bad[:5]}"


def test_release_zip_excludes_whl(release_zip_path):
    entries = _get_zip_entries(release_zip_path)
    bad = [e for e in entries if e.endswith(".whl")]
    assert not bad, f"Release zip must not contain .whl files: {bad[:5]}"


def test_release_zip_excludes_tar_gz(release_zip_path):
    entries = _get_zip_entries(release_zip_path)
    bad = [e for e in entries if e.endswith(".tar.gz")]
    assert not bad, f"Release zip must not contain .tar.gz files: {bad[:5]}"


def test_release_zip_excludes_stale_v210_artifacts(release_zip_path):
    """No zip entry should contain 'v2.1.0' in its path."""
    entries = _get_zip_entries(release_zip_path)
    bad = [e for e in entries if "v2.1.0" in e or "2.1.0" in e]
    assert not bad, f"Release zip must not contain v2.1.0 artifacts: {bad[:5]}"


def test_release_zip_excludes_stale_v230_artifacts(release_zip_path):
    """No zip entry should contain a v2.3.0 zip artifact."""
    entries = _get_zip_entries(release_zip_path)
    bad = [e for e in entries if e.endswith(".zip") and "v2.3.0" in e]
    assert not bad, f"Release zip must not contain nested v2.3.0 zips: {bad[:5]}"


def test_release_zip_excludes_ruff_cache(release_zip_path):
    entries = _get_zip_entries(release_zip_path)
    bad = [e for e in entries if ".ruff_cache" in e]
    assert not bad, f"Release zip must not contain .ruff_cache: {bad[:5]}"
