"""
tests/test_ja_docs.py

Verifies that Japanese documentation files exist and contain required content.
"""
from __future__ import annotations

from pathlib import Path

DOCS = Path(__file__).parent.parent / "docs"
JA = DOCS / "ja"


def test_ja_one_pager_exists():
    assert (JA / "ONE_PAGER.md").exists(), \
        "docs/ja/ONE_PAGER.md must exist"


def test_ja_safety_boundary_exists():
    assert (JA / "SAFETY_BOUNDARY.md").exists(), \
        "docs/ja/SAFETY_BOUNDARY.md must exist"


def test_ja_partner_ai_integration_exists():
    assert (JA / "PARTNER_AI_INTEGRATION.md").exists(), \
        "docs/ja/PARTNER_AI_INTEGRATION.md must exist"


def test_ja_one_pager_has_ai_disclaimer():
    content = (JA / "ONE_PAGER.md").read_text(encoding="utf-8")
    assert "AIモデルではありません" in content, \
        "docs/ja/ONE_PAGER.md must include 'AIモデルではありません'"


def test_ja_safety_boundary_has_read_only():
    content = (JA / "SAFETY_BOUNDARY.md").read_text(encoding="utf-8")
    assert "読み取り専用" in content, \
        "docs/ja/SAFETY_BOUNDARY.md must include '読み取り専用'"


def test_ja_partner_ai_integration_has_flow():
    content = (JA / "PARTNER_AI_INTEGRATION.md").read_text(encoding="utf-8")
    assert "EvidencePack" in content, \
        "docs/ja/PARTNER_AI_INTEGRATION.md must mention EvidencePack"


def test_ja_one_pager_has_hardware_prohibition():
    content = (JA / "ONE_PAGER.md").read_text(encoding="utf-8")
    assert "ロボット制御" in content or "ハードウェア" in content, \
        "docs/ja/ONE_PAGER.md must mention hardware control prohibition"
