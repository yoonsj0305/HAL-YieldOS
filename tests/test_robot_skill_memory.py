"""
tests/test_robot_skill_memory.py

v2.6.0 Robot Skill Memory MVP — 6 validation tests.

Safety invariants enforced:
  - no robot control commands
  - no certified root cause claims
  - hardware_execution_enabled = false everywhere
  - all outputs are candidate_only, require human review
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


# ── 1. Sample data existence ───────────────────────────────────────────────────

def test_robot_skill_memory_sample_exists():
    assert (SAMPLE_DIR / "robot_telemetry.csv").exists(), \
        "robot_skill_memory/robot_telemetry.csv not found"
    assert (SAMPLE_DIR / "operator_notes.csv").exists(), \
        "robot_skill_memory/operator_notes.csv not found"
    assert (SAMPLE_DIR / "maintenance_notes.csv").exists(), \
        "robot_skill_memory/maintenance_notes.csv not found"

    telemetry_header = (SAMPLE_DIR / "robot_telemetry.csv").read_text(encoding="utf-8").splitlines()[0]
    assert "human_intervention" in telemetry_header
    assert "slip_detected" in telemetry_header
    assert "motor_current_A" in telemetry_header

    op_header = (SAMPLE_DIR / "operator_notes.csv").read_text(encoding="utf-8").splitlines()[0]
    assert "operator_id_hash" in op_header
    assert "note_text_redacted" in op_header

    maint_header = (SAMPLE_DIR / "maintenance_notes.csv").read_text(encoding="utf-8").splitlines()[0]
    assert "technician_id_hash" in maint_header
    assert "note_text_redacted" in maint_header


# ── 2. CLI command runs ────────────────────────────────────────────────────────

def test_robot_skill_demo_cli_runs():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "skill_demo"
        result = cmd_robot_skill_demo(argparse.Namespace(out=str(out)))
        assert result == 0

        assert (out / "state_snapshot.json").exists()
        assert (out / "evidence_pack.json").exists()
        assert (out / "functional_passport.json").exists()
        assert (out / "operator_skill_note.json").exists(), \
            "operator_skill_note.json not generated"
        assert (out / "human_intervention_timeline.json").exists(), \
            "human_intervention_timeline.json not generated"
        assert (out / "skill_to_evidence_map.json").exists(), \
            "skill_to_evidence_map.json not generated"


# ── 3. Strict validation passes ───────────────────────────────────────────────

def test_robot_skill_demo_strict_validation():
    from yieldos.cli.main import cmd_robot_skill_demo, cmd_validate

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "skill_strict"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))

        val_args = argparse.Namespace(case=str(out), strict=True)
        rc = cmd_validate(val_args)
        assert rc == 0, "strict validation FAILED for robot skill demo output"


# ── 4. Functional passport has human_skill_context ────────────────────────────

def test_robot_skill_functional_passport_has_skill_context():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "skill_passport"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))

        fp = json.loads((out / "functional_passport.json").read_text(encoding="utf-8"))

        assert "human_skill_context" in fp, \
            "functional_passport.json missing human_skill_context"
        hsc = fp["human_skill_context"]
        assert hsc.get("operator_note_present") is True
        assert hsc.get("maintenance_note_present") is True
        assert "skill_capture_status" in hsc

        assert "candidate_validity_conditions" in fp
        assert "advisory_not_to_do" in fp
        assert fp.get("validity_boundary") == "candidate_context_not_certification"

        assert fp.get("hardware_execution_enabled") is False
        assert fp.get("human_approval_required") is True


# ── 5. Safety invariant — no forbidden terms in any JSON ──────────────────────

FORBIDDEN_STRINGS = [
    "send_ros_command",
    "execute_recovery_auto",
    "auto_repair_engine",
    "certified_safety_decision",
    "autonomous_control_loop",
    "production_decision_automation",
    '"hardware_execution_enabled": true',
]


def test_robot_skill_safety_invariant():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "skill_safety"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))

        for json_file in sorted(out.glob("*.json")):
            text = json_file.read_text(encoding="utf-8").lower()
            for term in FORBIDDEN_STRINGS:
                assert term.lower() not in text, \
                    f"Forbidden term '{term}' found in {json_file.name}"

        for skill_file in [
            "operator_skill_note.json",
            "human_intervention_timeline.json",
            "skill_to_evidence_map.json",
        ]:
            data = json.loads((out / skill_file).read_text(encoding="utf-8"))
            sb = data.get("safety_boundary", {})
            assert sb.get("hardware_execution_enabled") is False, \
                f"{skill_file} safety_boundary.hardware_execution_enabled must be false"
            assert sb.get("human_review_required") is True, \
                f"{skill_file} safety_boundary.human_review_required must be true"
            assert sb.get("candidate_only") is True, \
                f"{skill_file} safety_boundary.candidate_only must be true"

        from yieldos.domains.robot.skill_memory import ALLOWED_INTERVENTION_TYPES
        timeline = json.loads(
            (out / "human_intervention_timeline.json").read_text(encoding="utf-8")
        )
        for entry in timeline.get("interventions", []):
            itype = entry.get("intervention_type", "")
            assert itype in ALLOWED_INTERVENTION_TYPES, \
                f"Forbidden intervention_type '{itype}' — not in allowed set"


# ── 6. Source data manifest includes skill memory input files ─────────────────

def test_robot_skill_source_manifest_includes_skill_files():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "skill_manifest"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))

        manifest_path = out / "source_data_manifest.json"
        assert manifest_path.exists(), "source_data_manifest.json not found"

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        input_files = manifest.get("input_files", [])
        paths_in_manifest = {f.get("path", "") for f in input_files}

        assert "operator_notes.csv" in paths_in_manifest, \
            "source_data_manifest missing operator_notes.csv"
        assert "maintenance_notes.csv" in paths_in_manifest, \
            "source_data_manifest missing maintenance_notes.csv"
        assert "robot_telemetry.csv" in paths_in_manifest, \
            "source_data_manifest missing robot_telemetry.csv"
