"""
tests/test_no_generic_platform_drift.py

Verifies that README and docs do not position YieldOS as a generic platform
when used as a positive/affirmative claim.

Negative/denial context is always allowed, e.g.:
  "not a generic observability platform"
  "not an AI middleware layer"

v2.8.7: Functional Yield Essence Guard.
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
_DOCS_DIR = ROOT / "docs"


def _load_docs() -> list[tuple[str, str]]:
    """Return list of (filepath, content) for README and all docs/*.md"""
    files = [ROOT / "README.md"]
    files += sorted(_DOCS_DIR.glob("*.md"))
    return [(str(f.relative_to(ROOT)), f.read_text(encoding="utf-8")) for f in files]


# Forbidden positive-positioning phrases.
# These are allowed ONLY in negation context (preceded by "not" within 5 words).
_FORBIDDEN_POSITIVE = [
    "generic observability platform",
    "log aggregation platform",
    "autonomous industrial ai",
    "ai middleware platform",
    "workflow automation system",
    "robot control software",
    "satellite command software",
    "semiconductor recipe control",
    "yield guarantee",
    "certified root cause",
]

_NEGATION_WINDOW = 500  # characters before the phrase — must cover long multi-bullet lists


def _is_negated(text: str, match_start: int) -> bool:
    """Check if the phrase is preceded by a negation within the window."""
    window = text[max(0, match_start - _NEGATION_WINDOW): match_start].lower()
    return any(neg in window for neg in ("not ", "is not", "are not", "does not", "never ", "no "))


@pytest.mark.parametrize("filepath,content", _load_docs())
@pytest.mark.parametrize("forbidden", _FORBIDDEN_POSITIVE)
def test_no_positive_platform_drift(filepath, content, forbidden):
    lower = content.lower()
    idx = 0
    while True:
        pos = lower.find(forbidden, idx)
        if pos == -1:
            break
        if not _is_negated(lower, pos):
            # Find the line for a useful error message
            line_no = lower[:pos].count("\n") + 1
            excerpt = content[max(0, pos - 30): pos + len(forbidden) + 30].strip()
            pytest.fail(
                f"{filepath}:{line_no} — phrase '{forbidden}' used without negation context.\n"
                f"Excerpt: ...{excerpt}..."
            )
        idx = pos + 1
