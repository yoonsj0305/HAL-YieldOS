"""
tests/test_human_review_preparation.py

Verifies that decision_readiness_report.json contains a human_review_preparation block
for all demo domains.

v2.8.7: Functional Yield Essence Guard.
v2.8.8: Rewritten to use all_demo_cases fixture (no CLI subprocess per domain).
"""
from __future__ import annotations

import json


def test_decision_readiness_has_human_review_preparation(all_demo_cases: dict):
    for domain, out in all_demo_cases.items():
        dr = json.loads((out / "decision_readiness_report.json").read_text(encoding="utf-8"))
        assert "human_review_preparation" in dr, (
            f"decision_readiness_report.json for {domain} missing human_review_preparation"
        )


def test_human_review_preparation_no_automatic_decision(all_demo_cases: dict):
    for domain, out in all_demo_cases.items():
        dr = json.loads((out / "decision_readiness_report.json").read_text(encoding="utf-8"))
        hrp = dr.get("human_review_preparation", {})
        assert hrp.get("automatic_decision_enabled") is False, (
            f"{domain}: human_review_preparation.automatic_decision_enabled must be false"
        )


def test_human_review_preparation_approval_gate_required(all_demo_cases: dict):
    for domain, out in all_demo_cases.items():
        dr = json.loads((out / "decision_readiness_report.json").read_text(encoding="utf-8"))
        hrp = dr.get("human_review_preparation", {})
        assert hrp.get("approval_gate_required") is True, (
            f"{domain}: human_review_preparation.approval_gate_required must be true"
        )


def test_human_review_preparation_claim_boundary(all_demo_cases: dict):
    for domain, out in all_demo_cases.items():
        dr = json.loads((out / "decision_readiness_report.json").read_text(encoding="utf-8"))
        hrp = dr.get("human_review_preparation", {})
        cb = hrp.get("claim_boundary", "")
        assert "not_approval_execution" in cb, (
            f"{domain}: human_review_preparation.claim_boundary must contain "
            f"not_approval_execution, got: {cb!r}"
        )
