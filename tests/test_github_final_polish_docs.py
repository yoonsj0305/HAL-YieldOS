"""Tests for v3.0.8 — GitHub final polish: README, CITATION, docs safety claims."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
README = (ROOT / "README.md").read_text(encoding="utf-8")
CURRENT_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip()


# ── README badges ─────────────────────────────────────────────────────────────

def test_readme_has_badges():
    assert "shields.io" in README, "README must include shields.io badge links"


def test_readme_has_poc_badge():
    assert "PoC" in README or "poc" in README.lower(), \
        "README must have a PoC badge"


def test_readme_has_read_only_badge():
    lower = README.lower()
    assert "read--only" in lower or "read-only" in lower, \
        "README must have a read-only badge"


def test_readme_has_candidate_only_badge():
    lower = README.lower()
    assert "candidate--only" in lower or "candidate-only" in lower, \
        "README must have a candidate-only badge"


# ── README core content ───────────────────────────────────────────────────────

def test_readme_has_functional_yield_evidence_layer():
    assert "Functional Yield Evidence Layer" in README, \
        "README must include 'Functional Yield Evidence Layer'"


def test_readme_has_core_question():
    assert "What can still function" in README, \
        "README must include the core question"


def test_readme_has_hardware_control_denial():
    lower = README.lower()
    assert "control hardware" in lower or "hardware control" in lower, \
        "README must state no hardware control"


def test_readme_has_recipe_control_denial():
    lower = README.lower()
    assert "recipe" in lower, "README must state no recipe control"


def test_readme_has_yield_guarantee_denial():
    lower = README.lower()
    assert "yield" in lower and "guarantee" in lower, \
        "README must state no yield guarantee"


def test_readme_has_recovery_compiler_denial():
    lower = README.lower()
    assert "recovery compiler" in lower, \
        "README must state no Recovery Compiler execution"


def test_readme_has_documentation_section():
    assert "## Documentation" in README, \
        "README must include a '## Documentation' section"


def test_readme_links_roadmap():
    assert "ROADMAP" in README, "README must link to ROADMAP.md"


def test_readme_links_docs_index():
    assert "DOCS_INDEX" in README, "README must link to DOCS_INDEX.md"


# ── CITATION.cff ─────────────────────────────────────────────────────────────

def test_citation_version_is_current():
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert CURRENT_VERSION in cff, \
        f"CITATION.cff must contain current version {CURRENT_VERSION}"


# ── RELEASE_NOTES ─────────────────────────────────────────────────────────────

def test_release_notes_has_current_version_section():
    text = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert f"v{CURRENT_VERSION}" in text, \
        f"RELEASE_NOTES.md must include v{CURRENT_VERSION} section"


# ── Public docs safety claims ─────────────────────────────────────────────────

def _load_new_public_docs() -> list[tuple[str, str]]:
    targets = [
        ROOT / "ROADMAP.md",
        DOCS / "ARCHITECTURE.md",
        DOCS / "DOCS_INDEX.md",
        DOCS / "GITHUB_LAUNCH_NOTES.md",
        DOCS / "GITHUB_REPO_METADATA.md",
    ]
    return [(str(p.relative_to(ROOT)), p.read_text(encoding="utf-8")) for p in targets if p.exists()]


def test_new_docs_no_safety_certification_claim():
    for relpath, text in _load_new_public_docs():
        lower = text.lower()
        assert "yieldos is safety certified" not in lower, \
            f"{relpath}: must not claim YieldOS is safety certified"
        assert "production certified" not in lower, \
            f"{relpath}: must not claim production certification"


def test_new_docs_no_yield_guarantee_claim():
    for relpath, text in _load_new_public_docs():
        lower = text.lower()
        assert "yieldos guarantees yield" not in lower, \
            f"{relpath}: must not claim yield guarantee"
        assert "yield guaranteed" not in lower, \
            f"{relpath}: must not claim yield guaranteed"


def test_new_docs_no_timing_closure_claim():
    for relpath, text in _load_new_public_docs():
        lower = text.lower()
        assert "yieldos performs timing closure" not in lower, \
            f"{relpath}: must not claim timing closure"


def test_new_docs_no_certified_root_cause_positive_claim():
    for relpath, text in _load_new_public_docs():
        lower = text.lower()
        assert "yieldos certifies root cause" not in lower, \
            f"{relpath}: must not claim certified root cause"


def test_new_docs_no_hardware_control_claim():
    for relpath, text in _load_new_public_docs():
        lower = text.lower()
        assert "yieldos controls hardware" not in lower, \
            f"{relpath}: must not claim hardware control"
