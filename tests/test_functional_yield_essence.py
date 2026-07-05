"""
tests/test_functional_yield_essence.py

Verifies that docs/FUNCTIONAL_YIELD_ESSENCE.md exists with required content
and that README.md links to it.

v2.8.7: Functional Yield Essence Guard.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
ESSENCE_DOC = ROOT / "docs" / "FUNCTIONAL_YIELD_ESSENCE.md"
README = ROOT / "README.md"


def test_functional_yield_essence_doc_exists():
    assert ESSENCE_DOC.exists(), "docs/FUNCTIONAL_YIELD_ESSENCE.md must exist"


def test_essence_doc_not_generic_observability():
    text = ESSENCE_DOC.read_text(encoding="utf-8")
    assert "not a generic observability platform" in text.lower() or \
           "not a generic observability" in text, \
        "FUNCTIONAL_YIELD_ESSENCE.md must state it is not a generic observability platform"


def test_essence_doc_functional_yield_evidence_layer():
    text = ESSENCE_DOC.read_text(encoding="utf-8")
    assert "Functional Yield Evidence Layer" in text, \
        "FUNCTIONAL_YIELD_ESSENCE.md must contain 'Functional Yield Evidence Layer'"


def test_essence_doc_core_question():
    text = ESSENCE_DOC.read_text(encoding="utf-8")
    assert "what can still function" in text.lower(), \
        "FUNCTIONAL_YIELD_ESSENCE.md must include the core question"


def test_essence_doc_forbidden_claims_listed():
    text = ESSENCE_DOC.read_text(encoding="utf-8").lower()
    required_forbidden = ["certified root cause", "safety certification", "yield guarantee"]
    for term in required_forbidden:
        assert term in text, f"FUNCTIONAL_YIELD_ESSENCE.md must list forbidden claim: {term}"


def test_essence_doc_design_rule():
    text = ESSENCE_DOC.read_text(encoding="utf-8")
    assert "organizing principle" in text.lower(), \
        "FUNCTIONAL_YIELD_ESSENCE.md must state the organizing principle"


def test_readme_links_functional_yield_essence():
    text = README.read_text(encoding="utf-8")
    assert "FUNCTIONAL_YIELD_ESSENCE" in text, \
        "README.md must reference docs/FUNCTIONAL_YIELD_ESSENCE.md"
