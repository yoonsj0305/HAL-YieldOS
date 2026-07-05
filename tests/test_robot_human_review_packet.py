"""tests/test_robot_human_review_packet.py

Tests for robot_human_review_packet.json schema and content.
v3.0.0 - Robot Pilot-Ready Edition.
"""
from __future__ import annotations


def _generate(remaining=None, blocked=None, bin_class="degraded_role_candidate"):
    from yieldos.domains.robot.pilot_pack import generate_pilot_pack
    return generate_pilot_pack(
        input_dir=".",
        analysis_result={
            "case_id": "case_hrp_test",
            "remaining_roles": remaining or ["background_diagnostics"],
            "blocked_roles": blocked or ["high_speed_motion"],
            "bin_class": bin_class,
            "decision_readiness": "ACTION_INELIGIBLE",
        },
        case_id="case_hrp_test",
        asset_id="robot_hrp_01",
        alias_map={},
        columns=["motor_current_A", "joint_temp_C", "slip_detected"],
        rows=[{"motor_current_A": "5.2", "joint_temp_C": "42.0", "slip_detected": "1"}] * 5,
    )


def test_human_review_packet_schema():
    reports = _generate()
    hrp = reports["robot_human_review_packet"]
    assert hrp["schema"] == "hal.yieldos.robot.human_review_packet.v1"
    assert hrp["domain"] == "robot"
    assert hrp["case_id"] == "case_hrp_test"


def test_review_checklist_is_nonempty():
    reports = _generate()
    hrp = reports["robot_human_review_packet"]
    assert isinstance(hrp["review_checklist"], list)
    assert len(hrp["review_checklist"]) >= 3
    for item in hrp["review_checklist"]:
        assert "item" in item
        assert "priority" in item
        assert item["priority"] in ("HIGH", "MEDIUM", "LOW")


def test_hardware_control_is_disabled():
    reports = _generate()
    hrp = reports["robot_human_review_packet"]
    sa = hrp["safety_assertions"]
    assert sa["hardware_control_enabled"] is False
    assert sa["autonomous_action_blocked"] is True
    assert sa["human_approval_required_before_any_deployment"] is True
