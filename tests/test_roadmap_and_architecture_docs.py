"""Tests for v3.0.8 — ROADMAP.md, docs/ARCHITECTURE.md, docs/DOCS_INDEX.md."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
ROADMAP = ROOT / "ROADMAP.md"
ARCH = DOCS / "ARCHITECTURE.md"
DOCS_IDX = DOCS / "DOCS_INDEX.md"


# ── ROADMAP.md ────────────────────────────────────────────────────────────────

def test_roadmap_exists():
    assert ROADMAP.exists(), "ROADMAP.md must exist"


def test_roadmap_has_non_goals():
    text = ROADMAP.read_text(encoding="utf-8")
    assert "Non-goals" in text or "Non-Goals" in text or "non-goals" in text.lower(), \
        "ROADMAP.md must include a Non-goals section"


def test_roadmap_lists_hardware_control_as_nongloal():
    text = ROADMAP.read_text(encoding="utf-8").lower()
    assert "hardware control" in text, \
        "ROADMAP.md must list hardware control as a non-goal"


def test_roadmap_lists_yield_guarantee_as_nongoal():
    text = ROADMAP.read_text(encoding="utf-8").lower()
    assert "yield guarantee" in text or "guarantee yield" in text, \
        "ROADMAP.md must list yield guarantee as a non-goal"


def test_roadmap_lists_recipe_modification_as_nongoal():
    text = ROADMAP.read_text(encoding="utf-8").lower()
    assert "recipe" in text, \
        "ROADMAP.md must list recipe modification as a non-goal"


def test_roadmap_lists_recovery_compiler_as_nongoal():
    text = ROADMAP.read_text(encoding="utf-8").lower()
    assert "recovery compiler" in text, \
        "ROADMAP.md non-goals must mention Recovery Compiler"


def test_roadmap_has_current_baseline():
    text = ROADMAP.read_text(encoding="utf-8")
    assert "Current baseline" in text or "current baseline" in text.lower(), \
        "ROADMAP.md must describe current baseline"


# ── docs/ARCHITECTURE.md ─────────────────────────────────────────────────────

def test_architecture_doc_exists():
    assert ARCH.exists(), "docs/ARCHITECTURE.md must exist"


def test_architecture_has_recovery_compiler_boundary():
    text = ARCH.read_text(encoding="utf-8")
    assert "Recovery Compiler boundary" in text or \
           "recovery compiler boundary" in text.lower(), \
        "docs/ARCHITECTURE.md must include Recovery Compiler boundary section"


def test_architecture_says_no_recovery_profile_generated():
    text = ARCH.read_text(encoding="utf-8").lower()
    assert "recovery_profile.json" in text, \
        "docs/ARCHITECTURE.md must mention recovery_profile.json"
    assert "does not" in text or "never" in text, \
        "docs/ARCHITECTURE.md must say YieldOS does not generate recovery_profile.json"


def test_architecture_has_core_invariants():
    text = ARCH.read_text(encoding="utf-8")
    assert "Core invariants" in text or "core invariants" in text.lower(), \
        "docs/ARCHITECTURE.md must list core invariants"


def test_architecture_mentions_no_hardware_control():
    text = ARCH.read_text(encoding="utf-8").lower()
    assert "no hardware control" in text or "does not" in text, \
        "docs/ARCHITECTURE.md must state no hardware control"


def test_architecture_mentions_candidate_only():
    text = ARCH.read_text(encoding="utf-8").lower()
    assert "candidate" in text, \
        "docs/ARCHITECTURE.md must mention candidate-only"


def test_architecture_mentions_read_only():
    text = ARCH.read_text(encoding="utf-8").lower()
    assert "read-only" in text or "read_only" in text, \
        "docs/ARCHITECTURE.md must mention read-only"


def test_architecture_mentions_human_review():
    text = ARCH.read_text(encoding="utf-8").lower()
    assert "human review" in text or "human-review" in text, \
        "docs/ARCHITECTURE.md must mention human review"


# ── docs/DOCS_INDEX.md ────────────────────────────────────────────────────────

def test_docs_index_exists():
    assert DOCS_IDX.exists(), "docs/DOCS_INDEX.md must exist"


def test_docs_index_links_safety_boundary():
    text = DOCS_IDX.read_text(encoding="utf-8")
    assert "PUBLIC_SAFETY_BOUNDARY" in text, \
        "docs/DOCS_INDEX.md must link to PUBLIC_SAFETY_BOUNDARY.md"


def test_docs_index_links_architecture():
    text = DOCS_IDX.read_text(encoding="utf-8")
    assert "ARCHITECTURE" in text, \
        "docs/DOCS_INDEX.md must link to ARCHITECTURE.md"


def test_docs_index_links_roadmap():
    text = DOCS_IDX.read_text(encoding="utf-8")
    assert "ROADMAP" in text, \
        "docs/DOCS_INDEX.md must link to ROADMAP.md"
