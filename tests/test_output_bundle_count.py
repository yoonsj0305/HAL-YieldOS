"""
tests/test_output_bundle_count.py

Verifies that README and MANIFEST.json consistently document 22 standard output files.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent


def test_manifest_has_22_standard_output_files():
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    bundle = manifest.get("standard_output_bundle", [])
    assert len(bundle) == 22, \
        f"MANIFEST.json standard_output_bundle must have 22 files, got {len(bundle)}"


def test_readme_says_22_core_output_files():
    content = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "22 core output files" in content or "22 core" in content, \
        "README must say '22 core output files'"


def test_readme_does_not_say_17_standard_files():
    content = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "produces 17 files" not in content and "17 standard" not in content, \
        "README must not claim 17 standard output files — should be 22"


def test_manifest_bundle_includes_all_22_files():
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    bundle = set(manifest.get("standard_output_bundle", []))
    required = {
        "state_snapshot.json",
        "evidence_pack.json",
        "ooda_frame.json",
        "recovery_candidates.json",
        "report.md",
        "report.html",
        "input_validation.json",
        "decision_readiness_report.json",
        "functional_yield_scorecard.json",
        "functional_binning_result.json",
        "functional_passport.json",
        "evidence_pack.md",
        "recovery_route_report.json",
        "failure_scenario_record.json",
        "next_data_request.json",
        "analysis_trace.json",
        "source_data_manifest.json",
        "data_quality_report.json",
        "evidence_conflict_report.json",
        "baseline_vs_yieldos.json",
        "business_case_summary.json",
        "case_manifest.json",
    }
    missing = required - bundle
    assert not missing, \
        f"MANIFEST.json standard_output_bundle missing: {sorted(missing)}"
