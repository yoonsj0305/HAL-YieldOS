"""Tests for v3.0.7 — public documentation files existence."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"


def test_public_safety_boundary_exists():
    assert (DOCS / "PUBLIC_SAFETY_BOUNDARY.md").exists(), "docs/PUBLIC_SAFETY_BOUNDARY.md must exist"


def test_github_release_checklist_exists():
    assert (DOCS / "GITHUB_RELEASE_CHECKLIST.md").exists(), "docs/GITHUB_RELEASE_CHECKLIST.md must exist"


def test_demo_guide_exists():
    assert (DOCS / "DEMO_GUIDE.md").exists(), "docs/DEMO_GUIDE.md must exist"


def test_pilot_one_pager_exists():
    assert (DOCS / "PILOT_ONE_PAGER.md").exists(), "docs/PILOT_ONE_PAGER.md must exist"


def test_sample_outputs_guide_exists():
    assert (DOCS / "SAMPLE_OUTPUTS_GUIDE.md").exists(), "docs/SAMPLE_OUTPUTS_GUIDE.md must exist"


def test_repository_map_exists():
    assert (DOCS / "REPOSITORY_MAP.md").exists(), "docs/REPOSITORY_MAP.md must exist"


def test_contributing_exists():
    assert (ROOT / "CONTRIBUTING.md").exists(), "CONTRIBUTING.md must exist"


def test_security_exists():
    assert (ROOT / "SECURITY.md").exists(), "SECURITY.md must exist"


def test_citation_cff_exists():
    assert (ROOT / "CITATION.cff").exists(), "CITATION.cff must exist"
