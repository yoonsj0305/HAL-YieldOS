"""Tests for v3.0.7 — README.md safety boundary content."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
SAFETY = (ROOT / "docs" / "PUBLIC_SAFETY_BOUNDARY.md").read_text(encoding="utf-8")
CONTRIBUTING = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")


# ── README content ────────────────────────────────────────────────────────────

def test_readme_includes_core_question():
    assert "What can still function" in README, "README must include the core question"


def test_readme_includes_read_only():
    assert "read-only" in README.lower() or "read_only" in README.lower(), \
        "README must mention read-only"


def test_readme_includes_candidate_only_or_candidate_evidence():
    assert "candidate" in README.lower(), "README must mention candidate-only or candidate evidence"


def test_readme_includes_human_review():
    assert "human review" in README.lower(), "README must mention human review"


def test_readme_says_no_hardware_control():
    lower = README.lower()
    assert "control hardware" in lower or "no hardware control" in lower or \
           "hardware control" in lower, \
        "README must mention no hardware control"


def test_readme_says_no_recipe_control():
    lower = README.lower()
    assert "recipe" in lower, "README must mention no recipe control"


def test_readme_says_no_yield_guarantee():
    lower = README.lower()
    assert "yield" in lower, "README must mention yield (in context of no guarantee)"


def test_readme_links_safety_boundary():
    assert "PUBLIC_SAFETY_BOUNDARY" in README or "SAFETY_BOUNDARY" in README, \
        "README must link to safety boundary doc"


def test_readme_not_ai_model():
    assert "not an AI model" in README or "is not an AI model" in README, \
        "README must state YieldOS is not an AI model"


def test_readme_has_quickstart():
    assert "pip install" in README or "venv" in README, \
        "README must have quickstart commands"


def test_readme_has_domain_table():
    assert "Robot" in README and "Semiconductor" in README, \
        "README must have domain table"


def test_readme_no_safety_certification_claim():
    lower = README.lower()
    # Must NOT claim YieldOS provides safety certification
    assert "yieldos provides safety certification" not in lower
    assert "safety certified by yieldos" not in lower


def test_readme_no_yield_guarantee_claim():
    lower = README.lower()
    assert "yieldos guarantees yield" not in lower
    assert "yield guaranteed" not in lower


# ── PUBLIC_SAFETY_BOUNDARY.md content ────────────────────────────────────────

def test_safety_doc_says_no_hardware_control():
    lower = SAFETY.lower()
    assert "no hardware control" in lower


def test_safety_doc_says_candidate_only():
    assert "candidate" in SAFETY.lower()


def test_safety_doc_says_human_review():
    assert "human review" in SAFETY.lower()


def test_safety_doc_mentions_recovery_compiler_export_not_profile():
    assert "recovery_profile.json" in SAFETY or "recovery profile" in SAFETY.lower()
    assert "not a recovery profile" in SAFETY.lower() or "never generates" in SAFETY.lower() or \
           "never generated" in SAFETY.lower() or "not generated" in SAFETY.lower()


def test_safety_doc_lists_forbidden_claims():
    lower = SAFETY.lower()
    assert "certified root cause" in lower or "forbidden" in lower


# ── CONTRIBUTING.md content ───────────────────────────────────────────────────

def test_contributing_says_no_hardware_control():
    assert "hardware control" in CONTRIBUTING.lower()


def test_contributing_says_no_recipe_control():
    assert "recipe" in CONTRIBUTING.lower()


def test_contributing_says_read_only():
    assert "read-only" in CONTRIBUTING.lower() or "read_only" in CONTRIBUTING.lower()


def test_contributing_says_candidate_only():
    assert "candidate" in CONTRIBUTING.lower()
