"""Tests that semiconductor pilot-pack v3.0.3 contract alignment fields are correct.

Verifies that functional_passport.json contains semiconductor_pilot_context,
and that decision_readiness_report.json has the new allowed/forbidden decision lists.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yieldos.cli.main import main

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


@pytest.fixture(scope="module")
def contract_output(tmp_path_factory):
    if not SAMPLE_DIR.exists() or not (SAMPLE_DIR / "tool_log.csv").exists():
        pytest.skip("pilot_semiconductor samples not found")
    out = tmp_path_factory.mktemp("semi_pilot_contract")
    rc = main([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", str(out),
        "--asset", "contract_chip_001",
        "--case", "contract_case_001",
    ])
    assert rc == 0, f"semiconductor pilot-pack failed (rc={rc})"
    return out


def test_functional_passport_has_semiconductor_pilot_context(contract_output):
    fp = json.loads((contract_output / "functional_passport.json").read_text(encoding="utf-8"))
    assert "semiconductor_pilot_context" in fp, \
        "functional_passport.json missing semiconductor_pilot_context (v3.0.3)"


def test_semiconductor_pilot_context_has_required_refs(contract_output):
    fp = json.loads((contract_output / "functional_passport.json").read_text(encoding="utf-8"))
    spc = fp.get("semiconductor_pilot_context", {})
    required_refs = [
        "evidence_completeness_report_ref",
        "wafer_die_summary_ref",
        "functional_region_map_ref",
        "role_candidate_map_ref",
        "valid_conditions_report_ref",
        "recovery_compiler_intake_preview_ref",
        "recovery_compiler_handoff_boundary_ref",
        "recovery_compiler_export_ref",
        "handoff_manifest_ref",
        "pilot_case_summary_ref",
    ]
    for ref in required_refs:
        assert ref in spc, f"semiconductor_pilot_context missing {ref!r}"


def test_semiconductor_pilot_context_export_ref_correct(contract_output):
    fp = json.loads((contract_output / "functional_passport.json").read_text(encoding="utf-8"))
    spc = fp.get("semiconductor_pilot_context", {})
    assert spc.get("recovery_compiler_export_ref") == "semiconductor_recovery_compiler_export.json"


def test_semiconductor_pilot_context_handoff_manifest_ref_correct(contract_output):
    fp = json.loads((contract_output / "functional_passport.json").read_text(encoding="utf-8"))
    spc = fp.get("semiconductor_pilot_context", {})
    assert spc.get("handoff_manifest_ref") == "semiconductor_handoff_manifest.json"


def test_decision_readiness_has_allowed_decisions(contract_output):
    drr = json.loads((contract_output / "decision_readiness_report.json").read_text(encoding="utf-8"))
    allowed = drr.get("allowed_decisions", [])
    assert isinstance(allowed, list) and len(allowed) > 0, \
        "decision_readiness_report missing allowed_decisions list (v3.0.3)"


def test_decision_readiness_has_forbidden_decisions(contract_output):
    drr = json.loads((contract_output / "decision_readiness_report.json").read_text(encoding="utf-8"))
    forbidden = drr.get("forbidden_decisions", [])
    assert isinstance(forbidden, list) and len(forbidden) > 0, \
        "decision_readiness_report missing forbidden_decisions list (v3.0.3)"


def test_decision_readiness_forbidden_includes_recipe_control(contract_output):
    drr = json.loads((contract_output / "decision_readiness_report.json").read_text(encoding="utf-8"))
    forbidden = drr.get("forbidden_decisions", [])
    assert "modify_recipe" in forbidden, \
        "decision_readiness forbidden_decisions must include 'modify_recipe'"


def test_decision_readiness_forbidden_includes_root_cause(contract_output):
    drr = json.loads((contract_output / "decision_readiness_report.json").read_text(encoding="utf-8"))
    forbidden = drr.get("forbidden_decisions", [])
    assert "claim_root_cause" in forbidden, \
        "decision_readiness forbidden_decisions must include 'claim_root_cause'"


def test_decision_readiness_hardware_control_disabled(contract_output):
    drr = json.loads((contract_output / "decision_readiness_report.json").read_text(encoding="utf-8"))
    assert drr.get("hardware_control_enabled") is False
    assert drr.get("automatic_decision_enabled") is False
    assert drr.get("recipe_control_enabled") is False
    assert drr.get("tool_control_enabled") is False


def test_decision_readiness_human_review_required(contract_output):
    drr = json.loads((contract_output / "decision_readiness_report.json").read_text(encoding="utf-8"))
    assert drr.get("human_review_required") is True


def test_decision_readiness_claim_boundary_present(contract_output):
    drr = json.loads((contract_output / "decision_readiness_report.json").read_text(encoding="utf-8"))
    assert "claim_boundary" in drr, "decision_readiness_report missing claim_boundary"
    assert drr["claim_boundary"] == "decision_readiness_not_operational_authority"
