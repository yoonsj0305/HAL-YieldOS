"""
tests/test_data_sufficiency_embedded.py

Verifies that data_quality_report.json contains a data_sufficiency block
for all demo domains.

v2.8.7: Functional Yield Essence Guard.
v2.8.8: Rewritten to use all_demo_cases fixture (no CLI subprocess per domain).
"""
from __future__ import annotations

import json

_VALID_STATUSES = {
    "SUFFICIENT_FOR_CANDIDATE_REVIEW",
    "PARTIAL_FOR_CANDIDATE_REVIEW",
    "INSUFFICIENT_FOR_CANDIDATE_REVIEW",
    "UNKNOWN",
}

_DOMAINS = ("robot", "space", "semiconductor", "semiforge", "memory")


def test_data_quality_has_data_sufficiency(all_demo_cases: dict):
    for domain, out in all_demo_cases.items():
        dqr = json.loads((out / "data_quality_report.json").read_text(encoding="utf-8"))
        assert "data_sufficiency" in dqr, (
            f"data_quality_report.json for {domain} missing data_sufficiency"
        )


def test_data_sufficiency_status_valid(all_demo_cases: dict):
    for domain, out in all_demo_cases.items():
        dqr = json.loads((out / "data_quality_report.json").read_text(encoding="utf-8"))
        ds = dqr.get("data_sufficiency", {})
        assert ds.get("sufficiency_status") in _VALID_STATUSES, (
            f"{domain}: invalid sufficiency_status: {ds.get('sufficiency_status')!r}"
        )


def test_data_sufficiency_has_not_sufficient_for(all_demo_cases: dict):
    for domain, out in all_demo_cases.items():
        dqr = json.loads((out / "data_quality_report.json").read_text(encoding="utf-8"))
        ds = dqr.get("data_sufficiency", {})
        assert ds.get("not_sufficient_for"), (
            f"{domain}: data_sufficiency.not_sufficient_for must be non-empty"
        )


def test_data_sufficiency_has_claim_boundary(all_demo_cases: dict):
    for domain, out in all_demo_cases.items():
        dqr = json.loads((out / "data_quality_report.json").read_text(encoding="utf-8"))
        ds = dqr.get("data_sufficiency", {})
        assert "claim_boundary" in ds, (
            f"{domain}: data_sufficiency missing claim_boundary"
        )
