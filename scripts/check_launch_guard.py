#!/usr/bin/env python3
"""
HAL YieldOS -- Launch Guard

Fast local and CI guard that verifies public launch boundaries.

Checks:
  - Required files exist (README, public docs, GitHub templates, scripts)
  - README content contains required safety and evidence layer statements
  - .gitignore excludes generated artifacts
  - Public docs do not include unsafe affirmative safety claims

No external dependencies. No hardware control. No Recovery Compiler execution.
No recovery_profile.json generated.

Usage:
    python scripts/check_launch_guard.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# ── Negation context check ────────────────────────────────────────────────────

_NEGATION_WINDOW = 500
_NEGATION_TERMS = [
    "does not", "do not", "no ", "not ", "never ", "without ",
    "forbidden", "non-goal", "not intended", "must not",
]

# Unsafe affirmative claims: phrases that are ONLY valid in negative context.
_UNSAFE_PHRASES = [
    "controls hardware",
    "modifies recipes",
    "guarantees yield",
    "certifies root cause",
    "safety certified",
    "performs timing closure",
    "executes recovery profile",
    "autonomous recovery enabled",
]


def _is_negated(text_lower: str, match_start: int) -> bool:
    window = text_lower[max(0, match_start - _NEGATION_WINDOW): match_start]
    return any(neg in window for neg in _NEGATION_TERMS)


def _check_unsafe_claims(
    filepath: str, text: str, failures: list[str]
) -> None:
    lower = text.lower()
    for phrase in _UNSAFE_PHRASES:
        idx = 0
        while True:
            pos = lower.find(phrase, idx)
            if pos == -1:
                break
            if not _is_negated(lower, pos):
                line_no = lower[:pos].count("\n") + 1
                failures.append(
                    f"{filepath}:{line_no} — unsafe affirmative claim '{phrase}' "
                    f"found without negation context"
                )
            idx = pos + 1


# ── File existence checks ─────────────────────────────────────────────────────

_REQUIRED_FILES = [
    # Root
    "README.md",
    "ROADMAP.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CITATION.cff",
    ".gitignore",
    # Docs
    "docs/PUBLIC_SAFETY_BOUNDARY.md",
    "docs/DEMO_GUIDE.md",
    "docs/PILOT_ONE_PAGER.md",
    "docs/SAMPLE_OUTPUTS_GUIDE.md",
    "docs/ARCHITECTURE.md",
    "docs/DOCS_INDEX.md",
    "docs/GITHUB_LAUNCH_NOTES.md",
    "docs/GITHUB_REPO_METADATA.md",
    # GitHub templates
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    # Scripts
    "scripts/run_public_demo.py",
]


def repo_path(rel: str) -> Path:
    return ROOT.joinpath(*rel.split("/"))


def _check_required_files(failures: list[str]) -> None:
    for rel in _REQUIRED_FILES:
        path = repo_path(rel)
        if not path.exists():
            failures.append(f"MISSING: {rel}")


# ── README content checks ─────────────────────────────────────────────────────

_README_REQUIRED = [
    ("Functional Yield Evidence Layer", "README must include 'Functional Yield Evidence Layer'"),
    ("What can still function", "README must include the core question"),
    ("read-only", "README must include 'read-only'"),
    ("candidate-only", "README must include 'candidate-only'"),
    ("human review", "README must include 'human review'"),
    ("control hardware", "README must state no hardware control"),
    ("recipe", "README must state no recipe control"),
    ("yield", "README must state no yield guarantee"),
    ("Recovery Compiler", "README must mention Recovery Compiler boundary"),
    ("recovery", "README must mention recovery profile boundary"),
]


def _check_readme_content(failures: list[str]) -> None:
    readme_path = ROOT / "README.md"
    if not readme_path.exists():
        failures.append("README.md not found — skipping content checks")
        return
    text = readme_path.read_text(encoding="utf-8").lower()
    for phrase, msg in _README_REQUIRED:
        if phrase.lower() not in text:
            failures.append(f"README: {msg}")


# ── .gitignore checks ─────────────────────────────────────────────────────────

_GITIGNORE_REQUIRED = ["output/", "dist/", "__pycache__/"]


def _check_gitignore(failures: list[str]) -> None:
    gi = ROOT / ".gitignore"
    if not gi.exists():
        failures.append("MISSING: .gitignore")
        return
    text = gi.read_text(encoding="utf-8")
    for entry in _GITIGNORE_REQUIRED:
        if entry not in text:
            failures.append(f".gitignore must exclude '{entry}'")


# ── Public docs safety scan ───────────────────────────────────────────────────

def _check_public_docs_safety(failures: list[str]) -> None:
    scan_files = [ROOT / "README.md"]
    scan_files += sorted(DOCS.glob("*.md"))
    for path in scan_files:
        if path.exists():
            text = path.read_text(encoding="utf-8")
            relpath = str(path.relative_to(ROOT)).replace("\\", "/")
            _check_unsafe_claims(relpath, text, failures)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    failures: list[str] = []

    _check_required_files(failures)
    _check_readme_content(failures)
    _check_gitignore(failures)
    _check_public_docs_safety(failures)

    if failures:
        print(f"HAL YieldOS launch guard: FAIL ({len(failures)} issue(s))")
        for f in failures:
            print(f"  FAIL: {f}")
        return 1

    print("HAL YieldOS launch guard: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
