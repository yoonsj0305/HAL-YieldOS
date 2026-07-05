"""tests/test_robot_valid_conditions.py

Tests for robot_valid_conditions_report.json schema and content.
v3.0.0 - Robot Pilot-Ready Edition.
"""
from __future__ import annotations


def _generate(remaining, blocked, bin_class="degraded_role_candidate"):
    from yieldos.domains.robot.pilot_pack import generate_pilot_pack
    return generate_pilot_pack(
        input_dir=".",
        analysis_result={
            "case_id": "case_vc_test",
            "remaining_roles": remaining,
            "blocked_roles": blocked,
            "bin_class": bin_class,
            "decision_readiness": "PASSPORT_ELIGIBLE",
        },
        case_id="case_vc_test",
        asset_id="robot_vc_01",
        alias_map={},
        columns=[],
        rows=[],
    )


def test_valid_conditions_report_schema():
    reports = _generate(
        remaining=["background_diagnostics"],
        blocked=["high_speed_motion"],
    )
    vcr = reports["robot_valid_conditions_report"]
    assert vcr["schema"] == "hal.yieldos.robot.valid_conditions_report.v1"
    assert vcr["domain"] == "robot"
    assert isinstance(vcr["valid_conditions"], list)
    assert isinstance(vcr["global_conditions"], list)
    assert len(vcr["global_conditions"]) >= 2


def test_remaining_role_has_conditions():
    reports = _generate(
        remaining=["inspection_only_mode"],
        blocked=[],
        bin_class="inspection_candidate",
    )
    vcr = reports["robot_valid_conditions_report"]
    remaining_entries = [e for e in vcr["valid_conditions"]
                         if e["role"] == "inspection_only_mode" and e["status"] == "REMAINING"]
    assert remaining_entries, "inspection_only_mode should appear in valid_conditions as REMAINING"
    assert len(remaining_entries[0]["conditions"]) >= 1


def test_conditions_include_human_review_requirement():
    reports = _generate(
        remaining=["remote_supervised_mode"],
        blocked=[],
    )
    vcr = reports["robot_valid_conditions_report"]
    all_conditions = []
    for entry in vcr["valid_conditions"]:
        all_conditions.extend(entry.get("conditions", []))
    all_conditions_str = " ".join(all_conditions).lower()
    assert "human" in all_conditions_str or "human" in " ".join(vcr["global_conditions"]).lower()
