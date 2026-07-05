"""
tests/test_pilot_readiness_docs.py

Documentation content tests (v3.0.0).
Verifies that PILOT_READINESS.md documents the score fields and cap semantics.
"""
from __future__ import annotations

from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "docs"
PILOT_READINESS_MD = DOCS_DIR / "PILOT_READINESS.md"


def _text() -> str:
    return PILOT_READINESS_MD.read_text(encoding="utf-8")


def test_pilot_readiness_md_exists():
    assert PILOT_READINESS_MD.exists(), "docs/PILOT_READINESS.md must exist"


def test_docs_mentions_readiness_score():
    assert "readiness_score" in _text(), (
        "PILOT_READINESS.md must document the readiness_score field"
    )


def test_docs_mentions_readiness_score_percent():
    assert "readiness_score_percent" in _text(), (
        "PILOT_READINESS.md must document readiness_score_percent (v3.0.0)"
    )


def test_docs_mentions_score_range_0_1():
    text = _text()
    assert "0.0" in text and "1.0" in text, (
        "PILOT_READINESS.md must describe the readiness_score range 0.0–1.0"
    )


def test_docs_mentions_score_percent_range():
    text = _text()
    assert "100.0" in text or "100" in text, (
        "PILOT_READINESS.md must describe readiness_score_percent range up to 100"
    )


def test_docs_mentions_score_cap_semantics():
    text = _text()
    assert "cap" in text.lower() or "capped" in text.lower(), (
        "PILOT_READINESS.md must describe score cap semantics"
    )


def test_docs_mentions_readiness_status():
    assert "readiness_status" in _text(), (
        "PILOT_READINESS.md must document the readiness_status canonical field"
    )


def test_docs_mentions_all_canonical_statuses():
    text = _text()
    assert "READY_FOR_FUNCTIONAL_YIELD_PILOT" in text
    assert "PARTIAL_FOR_FUNCTIONAL_YIELD_PILOT" in text
    assert "NOT_READY_FOR_FUNCTIONAL_YIELD_PILOT" in text


def test_docs_version_is_current():
    text = _text()
    assert "3.0.0" in text, "PILOT_READINESS.md must reference the current version 3.0.0"
