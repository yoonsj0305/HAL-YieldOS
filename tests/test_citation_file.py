"""Tests for v3.0.7 — CITATION.cff content validation."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
CITATION = ROOT / "CITATION.cff"
CURRENT_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip()


def test_citation_cff_exists():
    assert CITATION.exists(), "CITATION.cff must exist"


def test_citation_cff_has_cff_version():
    text = CITATION.read_text(encoding="utf-8")
    assert "cff-version" in text, "CITATION.cff must declare cff-version"


def test_citation_cff_has_title():
    text = CITATION.read_text(encoding="utf-8")
    assert "title:" in text, "CITATION.cff must have title"
    assert "YieldOS" in text, "CITATION.cff title must mention YieldOS"


def test_citation_cff_has_authors():
    text = CITATION.read_text(encoding="utf-8")
    assert "authors:" in text, "CITATION.cff must have authors"


def test_citation_cff_version_matches_current():
    text = CITATION.read_text(encoding="utf-8")
    assert CURRENT_VERSION in text, \
        f"CITATION.cff version must match VERSION file ({CURRENT_VERSION})"


def test_citation_cff_has_abstract():
    text = CITATION.read_text(encoding="utf-8")
    assert "abstract:" in text, "CITATION.cff must have abstract"


def test_citation_cff_mentions_read_only():
    text = CITATION.read_text(encoding="utf-8")
    assert "read-only" in text.lower() or "read_only" in text.lower(), \
        "CITATION.cff abstract must mention read-only nature"


def test_citation_cff_has_keywords():
    text = CITATION.read_text(encoding="utf-8")
    assert "keywords:" in text, "CITATION.cff must have keywords"
    assert "functional yield" in text.lower(), "CITATION.cff must mention functional yield in keywords"
