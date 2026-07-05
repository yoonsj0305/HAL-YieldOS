"""
tests/test_robot_physical_gap.py

v2.6.1 Physical Reality Gap — 9 validation tests.

Safety invariants enforced:
  - no robot control commands
  - no certified root cause claims
  - hardware_execution_enabled = false everywhere
  - all physical gap outputs are candidate_only, require human review
  - sim-to-real gap: claim_boundary = candidate_only_sim_to_real_gap
  - force events: claim_boundary = candidate_physical_event_only
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

SAMPLE_DIR = (
    Path(__file__).parent.parent
    / "yieldos" / "sample_data" / "robot_skill_memory"
)

_ALLOWED_FORCE_EVENT_TYPES = {
    "force_spike",
    "torque_anomaly",
    "slip_event",
    "grip_failure_candidate",
    "contact_instability",
    "excessive_payload_resistance",
    "position_error_deviation",
    "unknown_physical_event",
}


# ── 1. sim_expectation.csv sample exists ──────────────────────────────────────

def test_robot_skill_memory_sim_expectation_sample_exists():
    sim_path = SAMPLE_DIR / "sim_expectation.csv"
    assert sim_path.exists(), "sim_expectation.csv not found in robot_skill_memory sample dir"
    header = sim_path.read_text(encoding="utf-8").splitlines()[0]
    assert "task_id" in header
    assert "sim_expected_success" in header
    assert "expected_max_joint_torque_Nm" in header
    assert "expected_max_force_sensor_N" in header
    assert "expected_min_gripper_force_N" in header


# ── 2. skill-demo generates physical gap outputs ──────────────────────────────

def test_robot_skill_demo_generates_physical_gap_outputs():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "robot_skill_memory"
        rc = cmd_robot_skill_demo(argparse.Namespace(out=str(out)))
        assert rc == 0
        assert (out / "sim_to_real_gap_report.json").exists(), \
            "sim_to_real_gap_report.json not generated"
        assert (out / "force_compliance_event_log.json").exists(), \
            "force_compliance_event_log.json not generated"


# ── 3. sim_to_real_gap_report candidate boundary ─────────────────────────────

def test_sim_to_real_gap_report_candidate_boundary():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "gap_boundary"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))
        report = json.loads((out / "sim_to_real_gap_report.json").read_text(encoding="utf-8"))

        assert report["schema"] == "hal.yieldos.robot.sim_to_real_gap_report.v1"
        sb = report["safety_boundary"]
        assert sb["hardware_execution_enabled"] is False
        assert sb["human_review_required"] is True
        assert sb["candidate_only"] is True
        assert len(report["gap_events"]) >= 1, "Expected at least 1 sim-to-real gap event"
        for event in report["gap_events"]:
            assert event["claim_boundary"] == "candidate_only_sim_to_real_gap", \
                f"gap_event claim_boundary violated: {event['claim_boundary']}"
            assert "candidate_gap_factors" in event
            assert len(event["candidate_gap_factors"]) >= 1


# ── 4. force_compliance_event_log candidate boundary ─────────────────────────

def test_force_compliance_event_log_candidate_boundary():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "force_boundary"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))
        log = json.loads((out / "force_compliance_event_log.json").read_text(encoding="utf-8"))

        assert log["schema"] == "hal.yieldos.robot.force_compliance_event_log.v1"
        sb = log["safety_boundary"]
        assert sb["hardware_execution_enabled"] is False
        assert sb["human_review_required"] is True
        assert sb["candidate_only"] is True
        assert len(log["events"]) >= 1, "Expected at least 1 force compliance event"
        for event in log["events"]:
            assert event["claim_boundary"] == "candidate_physical_event_only", \
                f"force_event claim_boundary violated: {event['claim_boundary']}"
            assert event["event_type"] in _ALLOWED_FORCE_EVENT_TYPES, \
                f"Forbidden event_type: {event['event_type']}"


# ── 5. functional_passport has physical_reality_context ──────────────────────

def test_robot_skill_functional_passport_has_physical_reality_context():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "physical_passport"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))
        passport = json.loads((out / "functional_passport.json").read_text(encoding="utf-8"))

        assert "physical_reality_context" in passport, \
            "functional_passport missing physical_reality_context"
        ctx = passport["physical_reality_context"]
        assert ctx["sim_to_real_gap_observed"] is True
        assert ctx["force_compliance_events_present"] is True
        assert ctx["context_capture_status"] in {"partial", "complete"}

        assert passport["physical_context_boundary"] == "candidate_context_not_certification"


# ── 6. skill_to_evidence_map references physical gap events ──────────────────

def test_skill_to_evidence_map_references_physical_gap_events():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "skill_map_physical"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))
        skill_map = json.loads((out / "skill_to_evidence_map.json").read_text(encoding="utf-8"))

        assert len(skill_map["mappings"]) >= 1
        found_force_ref = False
        found_gap_ref = False
        for mapping in skill_map["mappings"]:
            if mapping.get("linked_force_event_refs"):
                found_force_ref = True
            if mapping.get("linked_gap_event_refs"):
                found_gap_ref = True
            assert mapping["claim_boundary"] == "candidate_only"

        assert found_force_ref, "skill_to_evidence_map has no linked_force_event_refs"
        assert found_gap_ref, "skill_to_evidence_map has no linked_gap_event_refs"


# ── 7. source_data_manifest includes sim_expectation.csv ─────────────────────

def test_robot_skill_source_manifest_includes_sim_expectation():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "sim_manifest"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))
        manifest = json.loads((out / "source_data_manifest.json").read_text(encoding="utf-8"))

        paths = [f.get("path", "") for f in manifest.get("input_files", [])]
        assert any("robot_telemetry.csv" in p for p in paths), \
            "source_data_manifest missing robot_telemetry.csv"
        assert any("operator_notes.csv" in p for p in paths), \
            "source_data_manifest missing operator_notes.csv"
        assert any("maintenance_notes.csv" in p for p in paths), \
            "source_data_manifest missing maintenance_notes.csv"
        assert any("sim_expectation.csv" in p for p in paths), \
            "source_data_manifest missing sim_expectation.csv"


# ── 8. strict validation passes ───────────────────────────────────────────────

def test_robot_physical_gap_strict_validation_passes():
    from yieldos.cli.main import cmd_robot_skill_demo, cmd_validate

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "gap_strict"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))
        rc = cmd_validate(argparse.Namespace(case=str(out), strict=True))
        assert rc == 0, "strict validation FAILED for Robot Physical Gap outputs"


# ── 9. safety invariant — no forbidden terms in any JSON ─────────────────────

_PHYSICAL_FORBIDDEN = [
    "send_ros_command",
    "command_robot",
    "move_joint",
    "execute_recovery",
    "apply_control",
    "auto_repair",
    '"certified_root_cause"',   # match as standalone JSON value, not in "not_certified_root_cause"
    '"confirmed_root_cause"',   # same
    '"safety_certified"',       # same
    '"hardware_execution_enabled": true',
]


def test_robot_physical_gap_output_safety_invariant():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "gap_safety"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))

        for json_file in sorted(out.glob("*.json")):
            text = json_file.read_text(encoding="utf-8").lower()
            for term in _PHYSICAL_FORBIDDEN:
                assert term not in text, \
                    f"Forbidden term '{term}' found in {json_file.name}"

        for gap_file in ["sim_to_real_gap_report.json", "force_compliance_event_log.json"]:
            data = json.loads((out / gap_file).read_text(encoding="utf-8"))
            sb = data.get("safety_boundary", {})
            assert sb.get("hardware_execution_enabled") is False, \
                f"{gap_file} safety_boundary.hardware_execution_enabled must be false"
            assert sb.get("human_review_required") is True, \
                f"{gap_file} safety_boundary.human_review_required must be true"
            assert sb.get("candidate_only") is True, \
                f"{gap_file} safety_boundary.candidate_only must be true"
