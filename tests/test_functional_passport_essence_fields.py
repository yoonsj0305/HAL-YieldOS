"""
tests/test_functional_passport_essence_fields.py

Verifies that functional_passport.json contains functional_yield_organizing_principle
for all demo domains.

v2.8.7: Functional Yield Essence Guard.
v2.8.8: Rewritten to use all_demo_cases fixture (no CLI subprocess per domain).
"""
from __future__ import annotations

import json


def test_passport_has_functional_yield_organizing_principle(all_demo_cases: dict):
    for domain, out in all_demo_cases.items():
        fp = json.loads((out / "functional_passport.json").read_text(encoding="utf-8"))
        assert "functional_yield_organizing_principle" in fp, (
            f"functional_passport.json for {domain} missing functional_yield_organizing_principle"
        )


def test_passport_fyop_has_core_question(all_demo_cases: dict):
    for domain, out in all_demo_cases.items():
        fp = json.loads((out / "functional_passport.json").read_text(encoding="utf-8"))
        fyop = fp.get("functional_yield_organizing_principle", {})
        assert "core_question" in fyop, (
            f"{domain}: functional_yield_organizing_principle missing core_question"
        )


def test_passport_fyop_human_review_required(all_demo_cases: dict):
    for domain, out in all_demo_cases.items():
        fp = json.loads((out / "functional_passport.json").read_text(encoding="utf-8"))
        fyop = fp.get("functional_yield_organizing_principle", {})
        assert fyop.get("human_review_required") is True, (
            f"{domain}: functional_yield_organizing_principle.human_review_required must be true"
        )


def test_passport_fyop_claim_boundary_not_certification(all_demo_cases: dict):
    for domain, out in all_demo_cases.items():
        fp = json.loads((out / "functional_passport.json").read_text(encoding="utf-8"))
        fyop = fp.get("functional_yield_organizing_principle", {})
        cb = fyop.get("claim_boundary", "")
        assert "not_certification" in cb, (
            f"{domain}: claim_boundary must contain 'not_certification', got: {cb!r}"
        )
