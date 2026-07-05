"""tests/test_robot_pilot_outputs.py

Tests that generate_pilot_pack() returns all expected output keys.
v3.0.0 - Robot Pilot-Ready Edition.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

_SAMPLES = Path(__file__).parent.parent / "samples" / "pilot_robot"

_EXPECTED_JSON_KEYS = [
    "robot_pilot_readiness_report",
    "robot_evidence_completeness_report",
    "robot_role_reclassification_report",
    "robot_valid_conditions_report",
    "robot_human_review_packet",
    "robot_missing_evidence_request",
    "robot_unit_normalization_report",
]


def _get_all_reports():
    path = _SAMPLES / "robot_telemetry.csv"
    if not path.exists():
        pytest.skip("pilot_robot samples not found")
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        cols = list(reader.fieldnames or [])
    from yieldos.domains.robot.field_aliases import detect_aliases
    from yieldos.domains.robot.pilot_pack import generate_pilot_pack
    from yieldos.domains.robot.unit_normalization import build_unit_normalization_report
    alias_map = detect_aliases(cols)
    unit_norm = build_unit_normalization_report(cols, rows, "case_po_test", alias_map)
    reports = generate_pilot_pack(
        input_dir=str(_SAMPLES),
        analysis_result={
            "case_id": "case_po_test",
            "remaining_roles": ["background_diagnostics", "remote_supervised_mode"],
            "blocked_roles": ["high_speed_motion", "payload_transport"],
            "bin_class": "degraded_role_candidate",
            "decision_readiness": "PASSPORT_ELIGIBLE",
        },
        case_id="case_po_test",
        asset_id="robot_po_01",
        alias_map=alias_map,
        columns=cols,
        rows=rows,
    )
    reports["robot_unit_normalization_report"] = unit_norm
    return reports


def test_all_expected_json_report_keys_returned():
    reports = _get_all_reports()
    for key in _EXPECTED_JSON_KEYS:
        assert key in reports, f"Missing report key: {key}"


def test_pilot_readiness_report_has_required_top_level_fields():
    reports = _get_all_reports()
    rpr = reports["robot_pilot_readiness_report"]
    required = [
        "schema", "case_id", "domain", "readiness_status", "readiness_score",
        "readiness_score_percent", "pilot_checks", "not_sufficient_for",
        "hardware_control_enabled", "human_review_required", "safety_boundary",
    ]
    for field in required:
        assert field in rpr, f"readiness_report missing field: {field}"


def test_readiness_score_in_valid_range():
    reports = _get_all_reports()
    rpr = reports["robot_pilot_readiness_report"]
    assert 0.0 <= rpr["readiness_score"] <= 1.0
    assert 0.0 <= rpr["readiness_score_percent"] <= 100.0
    assert abs(rpr["readiness_score_percent"] - rpr["readiness_score"] * 100) < 0.01


def test_pilot_case_summary_md_content():
    from yieldos.domains.robot.pilot_pack import build_pilot_case_summary_md
    md = build_pilot_case_summary_md(
        case_id="case_md_test",
        asset_id="robot_md_01",
        readiness_status="PARTIAL_PILOT_READY",
        readiness_score=0.72,
        remaining_roles=["background_diagnostics"],
        blocked_roles=["high_speed_motion"],
        bin_class="degraded_role_candidate",
        slip_events=2,
        contact_events=1,
        interventions=3,
        files_missing=[],
    )
    assert "# Robot Pilot Case Summary" in md
    assert "SAFETY BOUNDARY" in md
    assert "hardware_execution_enabled: false" in md
    assert "PARTIAL_PILOT_READY" in md
    assert "0.72" in md
