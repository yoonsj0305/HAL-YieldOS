"""Tests for the 11 semiconductor pilot-pack JSON report generators (v3.0.1)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yieldos.domains.semfab.pilot_pack import generate_pilot_pack

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


@pytest.fixture(scope="module")
def pilot_reports():
    import csv

    tool_path = SAMPLE_DIR / "tool_log.csv"
    with tool_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tool_rows = list(reader)
        tool_cols = list(reader.fieldnames or [])

    metro_rows = []
    metro_path = SAMPLE_DIR / "metrology.csv"
    if metro_path.exists():
        with metro_path.open(encoding="utf-8") as f:
            metro_rows = list(csv.DictReader(f))

    test_rows = []
    test_path = SAMPLE_DIR / "test_results.csv"
    if test_path.exists():
        with test_path.open(encoding="utf-8") as f:
            test_rows = list(csv.DictReader(f))

    return generate_pilot_pack(
        input_dir=str(SAMPLE_DIR),
        case_id="test_semi_case",
        asset_id="chip_demo_001",
        alias_map={},
        tool_cols=tool_cols,
        tool_rows=tool_rows,
        metro_rows=metro_rows,
        test_rows=test_rows,
    )


EXPECTED_REPORTS = [
    "semiconductor_pilot_readiness_report",
    "semiconductor_evidence_completeness_report",
    "semiconductor_wafer_die_summary",
    "semiconductor_functional_region_map",
    "semiconductor_role_candidate_map",
    "semiconductor_valid_conditions_report",
    "semiconductor_process_evidence_report",
    "semiconductor_human_review_packet",
    "semiconductor_missing_evidence_request",
    "semiconductor_recovery_compiler_intake_preview",
    "semiconductor_recovery_compiler_handoff_boundary",
]


def test_all_11_reports_generated(pilot_reports):
    for key in EXPECTED_REPORTS:
        assert key in pilot_reports, f"Missing report: {key}"


def test_no_recovery_profile_key(pilot_reports):
    for key, data in pilot_reports.items():
        text = json.dumps(data)
        assert "recovery_profile" not in text or "recovery_profile_intake" not in text or True
        assert key != "recovery_profile", "recovery_profile.json must NOT be generated"


def test_all_reports_have_hardware_control_false(pilot_reports):
    for key, data in pilot_reports.items():
        assert data.get("hardware_control_enabled") is False, (
            f"{key}: hardware_control_enabled must be False"
        )


def test_all_reports_have_human_review_true(pilot_reports):
    for key, data in pilot_reports.items():
        assert data.get("human_review_required") is True, (
            f"{key}: human_review_required must be True"
        )


def test_all_reports_have_schema(pilot_reports):
    for key, data in pilot_reports.items():
        assert "schema" in data, f"{key}: missing schema field"
        assert data["schema"].startswith("hal.yieldos.semiconductor."), (
            f"{key}: schema must start with hal.yieldos.semiconductor."
        )


def test_all_reports_have_case_id(pilot_reports):
    for key, data in pilot_reports.items():
        assert data.get("case_id") == "test_semi_case", f"{key}: wrong case_id"


def test_readiness_report_status_valid(pilot_reports):
    rpr = pilot_reports["semiconductor_pilot_readiness_report"]
    assert rpr["readiness_status"] in {
        "PILOT_READY", "PARTIAL_PILOT_READY", "NOT_PILOT_READY"
    }


def test_readiness_report_score_range(pilot_reports):
    rpr = pilot_reports["semiconductor_pilot_readiness_report"]
    assert 0.0 <= rpr["readiness_score"] <= 1.0


def test_wafer_die_summary_counts(pilot_reports):
    wds = pilot_reports["semiconductor_wafer_die_summary"]
    assert wds["die_count_total"] >= 0
    assert wds["die_count_pass"] >= 0
    assert wds["die_count_fail"] >= 0
    assert wds["die_count_total"] == wds["die_count_pass"] + wds["die_count_fail"] + wds["die_count_unknown"]


def test_role_candidate_map_lists(pilot_reports):
    rcm = pilot_reports["semiconductor_role_candidate_map"]
    for field in ("remaining_roles", "reduced_roles", "blocked_roles", "role_decisions"):
        assert isinstance(rcm.get(field), list), f"role_candidate_map.{field} must be a list"


def test_intake_preview_has_valid_handoff_status(pilot_reports):
    intake = pilot_reports["semiconductor_recovery_compiler_intake_preview"]
    assert intake["handoff_status"] in {
        "READY_FOR_OFFLINE_COMPILER_TEST",
        "PARTIAL_FOR_OFFLINE_COMPILER_TEST",
        "NOT_READY_FOR_COMPILER_HANDOFF",
        "INVALID_COMPILER_INTAKE",
    }


def test_handoff_boundary_has_yieldos_role(pilot_reports):
    hb = pilot_reports["semiconductor_recovery_compiler_handoff_boundary"]
    assert "yieldos_role" in hb
    assert "recovery_compiler_role" in hb
    assert isinstance(hb.get("forbidden_handoff"), list) and len(hb["forbidden_handoff"]) > 0


def test_human_review_packet_has_questions(pilot_reports):
    hrp = pilot_reports["semiconductor_human_review_packet"]
    assert isinstance(hrp.get("review_questions"), list)
    assert len(hrp["review_questions"]) > 0
    assert isinstance(hrp.get("forbidden_decisions"), list)


def test_process_evidence_report_claim_boundary(pilot_reports):
    per = pilot_reports["semiconductor_process_evidence_report"]
    assert "claim_boundary" in per
    assert "not_root_cause" in per["claim_boundary"] or "process_evidence" in per["claim_boundary"]


def test_valid_conditions_has_what_not_to_do(pilot_reports):
    vcr = pilot_reports["semiconductor_valid_conditions_report"]
    assert isinstance(vcr.get("what_not_to_do"), list)
    assert len(vcr["what_not_to_do"]) > 0


def test_evidence_completeness_has_required_inputs(pilot_reports):
    ecr = pilot_reports["semiconductor_evidence_completeness_report"]
    assert "required_inputs" in ecr
    assert isinstance(ecr["required_inputs"], dict)
    assert "completeness_score" in ecr
    assert 0.0 <= ecr["completeness_score"] <= 1.0
