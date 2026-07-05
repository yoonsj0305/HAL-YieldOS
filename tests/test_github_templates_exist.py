"""Tests for v3.0.7 — GitHub issue templates and PR template existence."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
GITHUB = ROOT / ".github"
TEMPLATES = GITHUB / "ISSUE_TEMPLATE"


def test_github_dir_exists():
    assert GITHUB.exists() and GITHUB.is_dir(), ".github directory must exist"


def test_issue_template_dir_exists():
    assert TEMPLATES.exists() and TEMPLATES.is_dir(), ".github/ISSUE_TEMPLATE must exist"


def test_bug_report_template_exists():
    assert (TEMPLATES / "bug_report.md").exists(), ".github/ISSUE_TEMPLATE/bug_report.md must exist"


def test_sample_data_request_template_exists():
    assert (TEMPLATES / "sample_data_request.md").exists(), \
        ".github/ISSUE_TEMPLATE/sample_data_request.md must exist"


def test_documentation_template_exists():
    assert (TEMPLATES / "documentation.md").exists(), \
        ".github/ISSUE_TEMPLATE/documentation.md must exist"


def test_issue_template_config_exists():
    assert (TEMPLATES / "config.yml").exists(), ".github/ISSUE_TEMPLATE/config.yml must exist"


def test_pull_request_template_exists():
    assert (GITHUB / "PULL_REQUEST_TEMPLATE.md").exists(), \
        ".github/PULL_REQUEST_TEMPLATE.md must exist"


def test_pr_template_has_safety_checklist():
    pr = (GITHUB / "PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
    lower = pr.lower()
    assert "hardware control" in lower, "PR template must include hardware control safety check"
    assert "recipe" in lower, "PR template must include recipe safety check"
    assert "recovery_profile" in lower or "recovery profile" in lower, \
        "PR template must include recovery profile safety check"


def test_pr_template_has_validation_checklist():
    pr = (GITHUB / "PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
    assert "pytest" in pr.lower(), "PR template must include pytest validation check"
    assert "doctor" in pr.lower() or "validate" in pr.lower(), \
        "PR template must include doctor/validate check"
