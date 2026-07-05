"""tests/test_robot_evidence_completeness.py

Tests for robot_evidence_completeness_report.json schema and content.
v3.0.0 - Robot Pilot-Ready Edition.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

_SAMPLES = Path(__file__).parent.parent / "samples" / "pilot_robot"


def _get_reports():
    path = _SAMPLES / "robot_telemetry.csv"
    if not path.exists():
        pytest.skip("pilot_robot samples not found")
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        cols = list(reader.fieldnames or [])
    from yieldos.domains.robot.pilot_pack import generate_pilot_pack
    return generate_pilot_pack(
        input_dir=str(_SAMPLES),
        analysis_result={
            "case_id": "case_ec_test_001",
            "remaining_roles": ["background_diagnostics"],
            "blocked_roles": ["high_speed_motion"],
            "bin_class": "degraded_role_candidate",
            "decision_readiness": "PASSPORT_ELIGIBLE",
        },
        case_id="case_ec_test_001",
        asset_id="robot_ec_01",
        alias_map={},
        columns=cols,
        rows=rows,
    )


def test_evidence_completeness_report_schema():
    reports = _get_reports()
    ecr = reports["robot_evidence_completeness_report"]
    assert ecr["schema"] == "hal.yieldos.robot.evidence_completeness_report.v1"
    assert ecr["case_id"] == "case_ec_test_001"
    assert ecr["domain"] == "robot"


def test_completeness_summary_has_required_fields():
    reports = _get_reports()
    summary = reports["robot_evidence_completeness_report"]["completeness_summary"]
    assert "completeness_status" in summary
    assert summary["completeness_status"] in {
        "SUFFICIENT_FOR_CANDIDATE_REVIEW",
        "PARTIAL_FOR_CANDIDATE_REVIEW",
        "INSUFFICIENT_FOR_CANDIDATE_REVIEW",
    }
    assert isinstance(summary["files_present"], int)
    assert isinstance(summary["telemetry_row_count"], int)


def test_pilot_telemetry_has_expected_row_count():
    reports = _get_reports()
    summary = reports["robot_evidence_completeness_report"]["completeness_summary"]
    assert summary["telemetry_row_count"] >= 20, (
        f"Expected at least 20 rows, got {summary['telemetry_row_count']}"
    )


def test_slip_events_detected_in_sample_data():
    reports = _get_reports()
    summary = reports["robot_evidence_completeness_report"]["completeness_summary"]
    assert summary["slip_events_detected"] >= 1, (
        "Expected at least 1 slip event in sample telemetry"
    )
