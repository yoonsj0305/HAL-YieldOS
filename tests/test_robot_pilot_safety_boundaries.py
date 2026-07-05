"""tests/test_robot_pilot_safety_boundaries.py

Safety boundary invariant tests for robot pilot-pack outputs.
Verifies that hardware_execution_enabled=false and candidate_only=true
across all pilot-pack report schemas.
v3.0.0 - Robot Pilot-Ready Edition.
"""
from __future__ import annotations

import csv
from pathlib import Path

_SAMPLES = Path(__file__).parent.parent / "samples" / "pilot_robot"


def _load_telemetry() -> tuple[list[str], list[dict]]:
    path = _SAMPLES / "robot_telemetry.csv"
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        cols = list(reader.fieldnames or [])
    return cols, rows


def test_pilot_readiness_report_hardware_execution_disabled():
    from yieldos.domains.robot.pilot_pack import generate_pilot_pack
    cols, rows = _load_telemetry()
    result_stub = {
        "case_id": "case_safety_test_001",
        "remaining_roles": ["background_diagnostics"],
        "blocked_roles": ["high_speed_motion"],
        "bin_class": "degraded_role_candidate",
        "decision_readiness": "ACTION_INELIGIBLE",
    }
    reports = generate_pilot_pack(
        input_dir=str(_SAMPLES),
        analysis_result=result_stub,
        case_id="case_safety_test_001",
        asset_id="robot_test_01",
        alias_map={},
        columns=cols,
        rows=rows,
    )
    rpr = reports["robot_pilot_readiness_report"]
    assert rpr["hardware_control_enabled"] is False
    assert rpr["human_review_required"] is True
    assert rpr["safety_boundary"]["hardware_execution_enabled"] is False
    assert rpr["safety_boundary"]["candidate_only"] is True


def test_role_reclassification_safety_boundary():
    from yieldos.domains.robot.pilot_pack import generate_pilot_pack
    cols, rows = _load_telemetry()
    result_stub = {
        "case_id": "case_safety_test_002",
        "remaining_roles": ["recovery_observation_only"],
        "blocked_roles": ["payload_transport", "high_speed_motion"],
        "bin_class": "mission_survival_candidate",
        "decision_readiness": "ACTION_INELIGIBLE",
    }
    reports = generate_pilot_pack(
        input_dir=str(_SAMPLES),
        analysis_result=result_stub,
        case_id="case_safety_test_002",
        asset_id="robot_test_02",
        alias_map={},
        columns=cols,
        rows=rows,
    )
    rrr = reports["robot_role_reclassification_report"]
    assert rrr["safety_boundary"]["hardware_execution_enabled"] is False
    assert rrr["safety_boundary"]["human_review_required"] is True
    assert rrr["safety_boundary"]["candidate_only"] is True
    for mapping in rrr["reclassification_mapping"]:
        assert mapping.get("human_review_required") is True


def test_evidence_completeness_report_safety_boundary():
    from yieldos.domains.robot.pilot_pack import generate_pilot_pack
    cols, rows = _load_telemetry()
    result_stub = {
        "case_id": "case_safety_test_003",
        "remaining_roles": ["inspection_only_mode"],
        "blocked_roles": [],
        "bin_class": "inspection_candidate",
        "decision_readiness": "PASSPORT_ELIGIBLE",
    }
    reports = generate_pilot_pack(
        input_dir=str(_SAMPLES),
        analysis_result=result_stub,
        case_id="case_safety_test_003",
        asset_id="robot_test_03",
        alias_map={},
        columns=cols,
        rows=rows,
    )
    ecr = reports["robot_evidence_completeness_report"]
    assert ecr["safety_boundary"]["hardware_execution_enabled"] is False
    assert ecr["safety_boundary"]["read_only"] is True
