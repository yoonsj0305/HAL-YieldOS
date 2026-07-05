"""
tests/test_product_boundary_terms.py

Verifies that product boundary documents exist and that README positions
YieldOS correctly (not as autonomous AI or control OS).
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"


# ── Required boundary docs exist ─────────────────────────────────────────────

def test_yieldos_is_not_ai_doc_exists():
    assert (DOCS / "YIELDOS_IS_NOT_AI.md").exists(), \
        "docs/YIELDOS_IS_NOT_AI.md must exist"


def test_market_positioning_doc_exists():
    assert (DOCS / "MARKET_POSITIONING.md").exists(), \
        "docs/MARKET_POSITIONING.md must exist"


def test_partner_ai_interface_doc_exists():
    assert (DOCS / "PARTNER_AI_INTERFACE.md").exists(), \
        "docs/PARTNER_AI_INTERFACE.md must exist"


def test_forge_export_interface_doc_exists():
    assert (DOCS / "FORGE_EXPORT_INTERFACE.md").exists(), \
        "docs/FORGE_EXPORT_INTERFACE.md must exist"


def test_ja_one_pager_exists():
    assert (DOCS / "ja" / "ONE_PAGER.md").exists(), \
        "docs/ja/ONE_PAGER.md must exist"


# ── README product identity ───────────────────────────────────────────────────

def test_readme_says_not_an_ai_model():
    content = (ROOT / "README.md").read_text(encoding="utf-8")
    lower = content.lower()
    assert "not an ai model" in lower, \
        "README must include 'not an AI model' or equivalent"


def test_readme_includes_read_only():
    content = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    assert "read-only" in content or "read only" in content, \
        "README must include 'read-only'"


def test_readme_includes_candidate_only():
    content = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    assert "candidate" in content, \
        "README must include candidate-only language"


def test_readme_includes_human_review():
    content = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    assert "human review" in content, \
        "README must include 'human review'"


def test_readme_does_not_claim_autonomous_ai():
    content = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    forbidden = [
        "autonomous industrial os",
        "ai operating system",
        "ai autopilot",
        "ai factory os",
        "factory operating system",
    ]
    for term in forbidden:
        assert term not in content, \
            f"README must not contain '{term}' — violates product boundary"


# ── YIELDOS_IS_NOT_AI.md content ─────────────────────────────────────────────

def test_yieldos_is_not_ai_has_core_statement():
    content = (DOCS / "YIELDOS_IS_NOT_AI.md").read_text(encoding="utf-8")
    assert "not an AI model" in content, \
        "docs/YIELDOS_IS_NOT_AI.md must contain 'not an AI model'"


def test_yieldos_is_not_ai_has_constitution():
    content = (DOCS / "YIELDOS_IS_NOT_AI.md").read_text(encoding="utf-8")
    assert "Read-only" in content, \
        "docs/YIELDOS_IS_NOT_AI.md must list YieldOS Constitution principles"


# ── MARKET_POSITIONING.md content ────────────────────────────────────────────

def test_market_positioning_has_positioning_terms():
    content = (DOCS / "MARKET_POSITIONING.md").read_text(encoding="utf-8")
    assert "AI-ready Functional Yield Evidence Layer" in content, \
        "MARKET_POSITIONING.md must include the official short position"


def test_market_positioning_has_forbidden_terms_list():
    content = (DOCS / "MARKET_POSITIONING.md").read_text(encoding="utf-8")
    assert "Avoid" in content or "avoid" in content, \
        "MARKET_POSITIONING.md must list terms to avoid"


# ── Future interface docs are marked as planned ───────────────────────────────

def test_future_interfaces_are_marked_as_planned():
    for path_str in [
        "docs/FORGE_EXPORT_INTERFACE.md",
        "docs/PARTNER_AI_INTERFACE.md",
    ]:
        text = (ROOT / path_str).read_text(encoding="utf-8").lower()
        assert "future" in text or "planned" in text, \
            f"{path_str} must contain 'future' or 'planned'"
        assert "not part of the current release" in text or \
               "not implemented in the current release" in text, \
            f"{path_str} must say interface is not part of the current release"


def test_future_interfaces_do_not_use_version_specific_not_exist():
    for path_str in [
        "docs/FORGE_EXPORT_INTERFACE.md",
        "docs/PARTNER_AI_INTERFACE.md",
    ]:
        text = (ROOT / path_str).read_text(encoding="utf-8")
        assert "does not exist in v2.8.1" not in text, \
            f"{path_str} must not say 'does not exist in v2.8.1'"
        assert "does not exist in v2.8.2" not in text, \
            f"{path_str} must not say 'does not exist in v2.8.2'"
