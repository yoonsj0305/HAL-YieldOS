"""Tests for v3.0.8 — docs/GITHUB_LAUNCH_NOTES.md and docs/GITHUB_REPO_METADATA.md."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
LAUNCH_NOTES = DOCS / "GITHUB_LAUNCH_NOTES.md"
REPO_META = DOCS / "GITHUB_REPO_METADATA.md"


# ── docs/GITHUB_LAUNCH_NOTES.md ───────────────────────────────────────────────

def test_github_launch_notes_exists():
    assert LAUNCH_NOTES.exists(), "docs/GITHUB_LAUNCH_NOTES.md must exist"


def test_launch_notes_has_release_title():
    text = LAUNCH_NOTES.read_text(encoding="utf-8")
    assert "Release title" in text or "release title" in text.lower(), \
        "GITHUB_LAUNCH_NOTES.md must include release title"


def test_launch_notes_mentions_safety_boundary():
    text = LAUNCH_NOTES.read_text(encoding="utf-8").lower()
    assert "safety boundary" in text, \
        "GITHUB_LAUNCH_NOTES.md must mention safety boundary"


def test_launch_notes_says_no_hardware_control():
    text = LAUNCH_NOTES.read_text(encoding="utf-8").lower()
    assert "hardware control" in text or "control hardware" in text, \
        "GITHUB_LAUNCH_NOTES.md must state no hardware control"


def test_launch_notes_says_no_recipe_control():
    text = LAUNCH_NOTES.read_text(encoding="utf-8").lower()
    assert "recipe" in text, \
        "GITHUB_LAUNCH_NOTES.md must state no recipe control"


def test_launch_notes_says_no_yield_guarantee():
    text = LAUNCH_NOTES.read_text(encoding="utf-8").lower()
    assert "yield" in text and "guarantee" in text, \
        "GITHUB_LAUNCH_NOTES.md must state no yield guarantee"


def test_launch_notes_says_no_recovery_compiler():
    text = LAUNCH_NOTES.read_text(encoding="utf-8").lower()
    assert "recovery compiler" in text, \
        "GITHUB_LAUNCH_NOTES.md must mention Recovery Compiler boundary"


def test_launch_notes_says_no_recovery_profile():
    text = LAUNCH_NOTES.read_text(encoding="utf-8").lower()
    assert "recovery_profile" in text or "recovery profile" in text, \
        "GITHUB_LAUNCH_NOTES.md must mention no recovery_profile.json generation"


def test_launch_notes_has_quickstart():
    text = LAUNCH_NOTES.read_text(encoding="utf-8")
    assert "pip install" in text or "venv" in text, \
        "GITHUB_LAUNCH_NOTES.md must include quickstart commands"


def test_launch_notes_says_read_only():
    text = LAUNCH_NOTES.read_text(encoding="utf-8").lower()
    assert "read-only" in text or "read_only" in text, \
        "GITHUB_LAUNCH_NOTES.md must mention read-only"


def test_launch_notes_says_candidate_only():
    text = LAUNCH_NOTES.read_text(encoding="utf-8").lower()
    assert "candidate" in text, \
        "GITHUB_LAUNCH_NOTES.md must mention candidate-only"


# ── docs/GITHUB_REPO_METADATA.md ─────────────────────────────────────────────

def test_github_repo_metadata_exists():
    assert REPO_META.exists(), "docs/GITHUB_REPO_METADATA.md must exist"


def test_repo_metadata_has_topics():
    text = REPO_META.read_text(encoding="utf-8")
    assert "topics" in text.lower() or "Topics" in text, \
        "docs/GITHUB_REPO_METADATA.md must include suggested topics"


def test_repo_metadata_includes_functional_yield_topic():
    text = REPO_META.read_text(encoding="utf-8")
    assert "functional-yield" in text, \
        "docs/GITHUB_REPO_METADATA.md topics must include functional-yield"


def test_repo_metadata_has_repo_description():
    text = REPO_META.read_text(encoding="utf-8").lower()
    assert "description" in text or "about" in text, \
        "docs/GITHUB_REPO_METADATA.md must include suggested description"


def test_repo_metadata_says_read_only():
    text = REPO_META.read_text(encoding="utf-8").lower()
    assert "read-only" in text or "read_only" in text, \
        "docs/GITHUB_REPO_METADATA.md must say read-only"
