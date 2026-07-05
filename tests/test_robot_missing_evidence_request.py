"""tests/test_robot_missing_evidence_request.py

Tests for robot_missing_evidence_request.json schema and content.
v3.0.0 - Robot Pilot-Ready Edition.
"""
from __future__ import annotations

from pathlib import Path

import pytest

_SAMPLES = Path(__file__).parent.parent / "samples" / "pilot_robot"


def _generate_with_samples():
    import csv
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
            "case_id": "case_mer_test",
            "remaining_roles": ["background_diagnostics"],
            "blocked_roles": ["high_speed_motion"],
            "bin_class": "degraded_role_candidate",
            "decision_readiness": "ACTION_INELIGIBLE",
        },
        case_id="case_mer_test",
        asset_id="robot_mer_01",
        alias_map={},
        columns=cols,
        rows=rows,
    )


def test_missing_evidence_request_schema():
    reports = _generate_with_samples()
    mer = reports["robot_missing_evidence_request"]
    assert mer["schema"] == "hal.yieldos.robot.missing_evidence_request.v1"
    assert mer["domain"] == "robot"
    assert mer["case_id"] == "case_mer_test"


def test_missing_evidence_arrays_present():
    reports = _generate_with_samples()
    mer = reports["robot_missing_evidence_request"]
    assert isinstance(mer["missing_required_evidence"], list)
    assert isinstance(mer["missing_optional_evidence"], list)


def test_why_needed_for_functional_yield_present():
    reports = _generate_with_samples()
    mer = reports["robot_missing_evidence_request"]
    wnfy = mer["why_needed_for_functional_yield"]
    assert isinstance(wnfy, dict)
    assert len(wnfy) >= 3
    assert "sim_expectation" in wnfy or "slip_events" in wnfy
