"""Tests for v3.0.9 — GitHub Actions workflows and CI docs existence."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"
DOCS = ROOT / "docs"
README = (ROOT / "README.md").read_text(encoding="utf-8")


# ── Workflow files ────────────────────────────────────────────────────────────

def test_workflows_directory_exists():
    assert WORKFLOWS.exists() and WORKFLOWS.is_dir(), \
        ".github/workflows/ directory must exist"


def test_workflow_tests_yml_exists():
    assert (WORKFLOWS / "tests.yml").exists(), \
        ".github/workflows/tests.yml must exist"


def test_workflow_tests_has_pytest():
    text = (WORKFLOWS / "tests.yml").read_text(encoding="utf-8")
    assert "python -m pytest -q" in text, \
        "tests.yml must include 'python -m pytest -q'"


def test_workflow_tests_has_doctor():
    text = (WORKFLOWS / "tests.yml").read_text(encoding="utf-8")
    assert "yieldos doctor --deep" in text, \
        "tests.yml must include 'yieldos doctor --deep'"


def test_workflow_tests_has_launch_guard():
    text = (WORKFLOWS / "tests.yml").read_text(encoding="utf-8")
    assert "check_launch_guard.py" in text, \
        "tests.yml must include 'check_launch_guard.py' launch guard step"


def test_workflow_public_demo_exists():
    assert (WORKFLOWS / "public-demo.yml").exists(), \
        ".github/workflows/public-demo.yml must exist"


def test_workflow_public_demo_has_run_public_demo():
    text = (WORKFLOWS / "public-demo.yml").read_text(encoding="utf-8")
    assert "run_public_demo.py" in text, \
        "public-demo.yml must include 'run_public_demo.py'"


def test_workflow_public_demo_has_recovery_profile_check():
    text = (WORKFLOWS / "public-demo.yml").read_text(encoding="utf-8")
    assert "recovery_profile.json" in text, \
        "public-demo.yml must verify no recovery_profile.json was generated"


def test_workflow_tests_no_private_secrets():
    text = (WORKFLOWS / "tests.yml").read_text(encoding="utf-8").lower()
    assert "secrets.api_key" not in text, \
        "tests.yml must not reference private API key secrets"
    assert "secrets.private_token" not in text, \
        "tests.yml must not reference private token secrets"
    assert "secrets.password" not in text, \
        "tests.yml must not reference password secrets"


def test_workflow_public_demo_no_private_secrets():
    text = (WORKFLOWS / "public-demo.yml").read_text(encoding="utf-8").lower()
    assert "secrets.api_key" not in text, \
        "public-demo.yml must not reference private API key secrets"
    assert "secrets.private_token" not in text, \
        "public-demo.yml must not reference private token secrets"


def test_workflow_public_demo_is_manual():
    text = (WORKFLOWS / "public-demo.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch" in text, \
        "public-demo.yml must use workflow_dispatch (manual trigger)"


# ── README CI badge ───────────────────────────────────────────────────────────

def test_readme_has_ci_badge_since_workflow_exists():
    if (WORKFLOWS / "tests.yml").exists():
        assert "tests.yml" in README, \
            "README must include CI badge linking to tests.yml since workflow exists"


def test_readme_ci_badge_is_linked():
    if (WORKFLOWS / "tests.yml").exists():
        assert "actions/workflows/tests.yml/badge.svg" in README, \
            "README must include linked CI badge ([![tests]...]...)"


# ── CI documentation files ────────────────────────────────────────────────────

def test_github_ci_doc_exists():
    assert (DOCS / "GITHUB_CI.md").exists(), \
        "docs/GITHUB_CI.md must exist"


def test_github_upload_checklist_exists():
    assert (DOCS / "GITHUB_UPLOAD_CHECKLIST.md").exists(), \
        "docs/GITHUB_UPLOAD_CHECKLIST.md must exist"


def test_github_ci_doc_mentions_tests_workflow():
    text = (DOCS / "GITHUB_CI.md").read_text(encoding="utf-8")
    assert "tests.yml" in text or "tests workflow" in text.lower(), \
        "docs/GITHUB_CI.md must mention the tests workflow"


def test_github_ci_doc_mentions_public_demo_workflow():
    text = (DOCS / "GITHUB_CI.md").read_text(encoding="utf-8")
    assert "public-demo" in text or "public demo" in text.lower(), \
        "docs/GITHUB_CI.md must mention the public-demo workflow"


def test_github_ci_doc_mentions_launch_guard():
    text = (DOCS / "GITHUB_CI.md").read_text(encoding="utf-8")
    assert "launch guard" in text.lower() or "check_launch_guard" in text, \
        "docs/GITHUB_CI.md must mention the launch guard"


def test_github_ci_doc_mentions_safety_boundary():
    text = (DOCS / "GITHUB_CI.md").read_text(encoding="utf-8").lower()
    assert "safety boundary" in text or "hardware" in text, \
        "docs/GITHUB_CI.md must mention safety boundary"


def test_upload_checklist_has_recovery_profile_check():
    text = (DOCS / "GITHUB_UPLOAD_CHECKLIST.md").read_text(encoding="utf-8").lower()
    assert "recovery_profile" in text or "recovery profile" in text, \
        "docs/GITHUB_UPLOAD_CHECKLIST.md must mention recovery_profile check"


def test_upload_checklist_mentions_launch_guard():
    text = (DOCS / "GITHUB_UPLOAD_CHECKLIST.md").read_text(encoding="utf-8")
    assert "check_launch_guard" in text or "launch guard" in text.lower(), \
        "docs/GITHUB_UPLOAD_CHECKLIST.md must mention launch guard"
