"""tests/test_robot_role_reclassification.py

Tests for robot_role_reclassification_report.json schema and content.
v3.0.0 - Robot Pilot-Ready Edition.
"""
from __future__ import annotations

from yieldos.domains.robot.pilot_pack import CANONICAL_ROBOT_ROLES


def _generate(remaining, blocked, bin_class="degraded_role_candidate"):
    from yieldos.domains.robot.pilot_pack import generate_pilot_pack
    return generate_pilot_pack(
        input_dir=".",
        analysis_result={
            "case_id": "case_rr_test",
            "remaining_roles": remaining,
            "blocked_roles": blocked,
            "bin_class": bin_class,
            "decision_readiness": "ACTION_INELIGIBLE",
        },
        case_id="case_rr_test",
        asset_id="robot_rr_01",
        alias_map={},
        columns=[],
        rows=[],
    )


def test_role_reclassification_report_schema():
    reports = _generate(
        remaining=["background_monitoring"],
        blocked=["normal_payload_operation"],
    )
    rrr = reports["robot_role_reclassification_report"]
    assert rrr["schema"] == "hal.yieldos.robot.role_reclassification_report.v1"
    assert rrr["domain"] == "robot"
    assert isinstance(rrr["reclassification_mapping"], list)


def test_all_canonical_roles_are_assessed():
    reports = _generate(remaining=[], blocked=[])
    rrr = reports["robot_role_reclassification_report"]
    assessed = rrr["canonical_roles_assessed"]
    for role in CANONICAL_ROBOT_ROLES:
        assert role in assessed, f"Canonical role '{role}' not assessed"
    assert len(rrr["reclassification_mapping"]) == len(CANONICAL_ROBOT_ROLES)


def test_remaining_and_blocked_lists_are_present():
    reports = _generate(
        remaining=["background_diagnostics", "recovery_observation_only"],
        blocked=["high_speed_motion", "payload_transport"],
        bin_class="mission_survival_candidate",
    )
    rrr = reports["robot_role_reclassification_report"]
    assert rrr["summary"]["remaining_count"] >= 0
    assert rrr["summary"]["blocked_count"] >= 0
    assert rrr["summary"]["remaining_count"] + rrr["summary"]["blocked_count"] + \
           rrr["summary"]["candidate_count"] == len(CANONICAL_ROBOT_ROLES)
