"""Tests for v3.0.7 — .gitignore coverage for generated artifacts."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
GITIGNORE = ROOT / ".gitignore"


def test_gitignore_exists():
    assert GITIGNORE.exists(), ".gitignore must exist"


def test_gitignore_excludes_output():
    text = GITIGNORE.read_text(encoding="utf-8")
    assert "output/" in text, ".gitignore must exclude output/"


def test_gitignore_excludes_dist():
    text = GITIGNORE.read_text(encoding="utf-8")
    assert "dist/" in text, ".gitignore must exclude dist/"


def test_gitignore_excludes_build():
    text = GITIGNORE.read_text(encoding="utf-8")
    assert "build/" in text, ".gitignore must exclude build/"


def test_gitignore_excludes_pycache():
    text = GITIGNORE.read_text(encoding="utf-8")
    assert "__pycache__/" in text, ".gitignore must exclude __pycache__/"


def test_gitignore_excludes_pytest_cache():
    text = GITIGNORE.read_text(encoding="utf-8")
    assert ".pytest_cache/" in text, ".gitignore must exclude .pytest_cache/"


def test_gitignore_excludes_pyc():
    text = GITIGNORE.read_text(encoding="utf-8")
    assert "*.pyc" in text or "*.py[cod]" in text, ".gitignore must exclude .pyc files"


def test_gitignore_excludes_zip():
    text = GITIGNORE.read_text(encoding="utf-8")
    assert "*.zip" in text, ".gitignore must exclude *.zip (generated release artifacts)"


def test_gitignore_excludes_env():
    text = GITIGNORE.read_text(encoding="utf-8")
    assert ".env" in text, ".gitignore must exclude .env files"


def test_gitignore_excludes_venv():
    text = GITIGNORE.read_text(encoding="utf-8")
    assert ".venv/" in text or "venv/" in text, ".gitignore must exclude virtual environments"
