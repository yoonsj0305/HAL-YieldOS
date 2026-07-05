"""Tests for v3.0.10 -- cross-platform path handling in check_launch_guard.py."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).parent.parent
GUARD_SCRIPT = ROOT / "scripts" / "check_launch_guard.py"


def _load_guard():
    spec = importlib.util.spec_from_file_location("check_launch_guard", GUARD_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_repo_path_function_exists():
    source = GUARD_SCRIPT.read_text(encoding="utf-8")
    assert "def repo_path(" in source, \
        "check_launch_guard.py must define repo_path() helper"


def test_repo_path_uses_joinpath():
    source = GUARD_SCRIPT.read_text(encoding="utf-8")
    assert "joinpath" in source, \
        "repo_path() must use Path.joinpath for cross-platform compatibility"


def test_no_rel_replace_for_path_construction():
    source = GUARD_SCRIPT.read_text(encoding="utf-8")
    assert "rel.replace" not in source, \
        "must not use rel.replace() for path construction -- use repo_path(rel)"


def test_repo_path_readme_resolves_correctly():
    mod = _load_guard()
    p = mod.repo_path("README.md")
    assert p == ROOT / "README.md"


def test_repo_path_nested_doc_resolves_correctly():
    mod = _load_guard()
    p = mod.repo_path("docs/PUBLIC_SAFETY_BOUNDARY.md")
    assert p == ROOT / "docs" / "PUBLIC_SAFETY_BOUNDARY.md"


def test_repo_path_github_template_resolves_correctly():
    mod = _load_guard()
    p = mod.repo_path(".github/PULL_REQUEST_TEMPLATE.md")
    assert p == ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"


def test_repo_path_splits_to_separate_components():
    mod = _load_guard()
    p = mod.repo_path("docs/GITHUB_CI.md")
    parts = p.relative_to(ROOT).parts
    assert "docs" in parts, "docs must be a separate path component"
    assert "GITHUB_CI.md" in parts, "filename must be a separate path component"


def test_repo_path_single_component():
    mod = _load_guard()
    p = mod.repo_path("README.md")
    assert p.name == "README.md"
    assert p.parent == ROOT
