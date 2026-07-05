"""
tests/test_functional_yield_lineage_summary.py

Verifies that case_manifest.json contains a functional_yield_lineage_summary block
for all demo domains.

v2.8.7: Functional Yield Essence Guard.
v2.8.8: Rewritten to use all_demo_cases fixture (no CLI subprocess per domain).
"""
from __future__ import annotations

import json

_REQUIRED_REFS = (
    "source_manifest_ref",
    "evidence_pack_ref",
    "functional_passport_ref",
    "decision_readiness_ref",
)


def test_case_manifest_has_lineage_summary(all_demo_cases: dict):
    for domain, out in all_demo_cases.items():
        cm = json.loads((out / "case_manifest.json").read_text(encoding="utf-8"))
        assert "functional_yield_lineage_summary" in cm, (
            f"case_manifest.json for {domain} missing functional_yield_lineage_summary"
        )


def test_lineage_summary_has_required_refs(all_demo_cases: dict):
    for domain, out in all_demo_cases.items():
        cm = json.loads((out / "case_manifest.json").read_text(encoding="utf-8"))
        fyl = cm.get("functional_yield_lineage_summary", {})
        for ref_key in _REQUIRED_REFS:
            assert ref_key in fyl, (
                f"{domain}: functional_yield_lineage_summary missing {ref_key}"
            )


def test_lineage_summary_claim_boundary(all_demo_cases: dict):
    for domain, out in all_demo_cases.items():
        cm = json.loads((out / "case_manifest.json").read_text(encoding="utf-8"))
        fyl = cm.get("functional_yield_lineage_summary", {})
        cb = fyl.get("claim_boundary", "")
        assert "not_legal_chain_of_custody" in cb, (
            f"{domain}: lineage_summary.claim_boundary must contain "
            f"not_legal_chain_of_custody, got: {cb!r}"
        )
