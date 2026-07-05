"""
tests/test_robot_skill_case_study.py

v2.6.2 Robot Skill Memory Case Study — 9 validation tests.

Safety invariants enforced:
  - case study outputs are candidate-only, human-review-only
  - hardware_execution_enabled = false everywhere
  - functional_passport links case study
  - ooda_frame links case study
  - before-after shows baseline vs YieldOS reclassification
  - no forbidden robot control / certification terms in output JSON
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

# ── 1. case study outputs exist ───────────────────────────────────────────────

def test_robot_skill_case_study_outputs_exist():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "robot_skill_memory"
        rc = cmd_robot_skill_demo(argparse.Namespace(out=str(out)))
        assert rc == 0
        assert (out / "robot_skill_memory_case_study.json").exists(), \
            "robot_skill_memory_case_study.json not generated"
        assert (out / "robot_skill_memory_case_study.md").exists(), \
            "robot_skill_memory_case_study.md not generated"
        assert (out / "before_after_functional_reclassification.json").exists(), \
            "before_after_functional_reclassification.json not generated"


# ── 2. case study has safety boundary ────────────────────────────────────────

def test_robot_skill_case_study_has_safety_boundary():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "cs_safety"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))
        case = json.loads((out / "robot_skill_memory_case_study.json").read_text(encoding="utf-8"))

        assert case["schema"] == "hal.yieldos.robot.skill_memory_case_study.v1"
        sb = case["safety_boundary"]
        assert sb["hardware_execution_enabled"] is False
        assert sb["human_review_required"] is True
        assert sb["candidate_only"] is True
        assert sb["root_cause_certification"] is False
        assert sb["safety_certification"] is False


# ── 3. case study links required source outputs ───────────────────────────────

def test_robot_skill_case_study_links_required_outputs():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "cs_links"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))
        case = json.loads((out / "robot_skill_memory_case_study.json").read_text(encoding="utf-8"))
        source_outputs = case["source_outputs"]

        required = {
            "operator_skill_note",
            "human_intervention_timeline",
            "sim_to_real_gap_report",
            "force_compliance_event_log",
            "skill_to_evidence_map",
            "functional_passport",
            "evidence_pack",
        }
        assert required.issubset(set(source_outputs)), \
            f"Missing source_outputs keys: {required - set(source_outputs)}"


# ── 4. before-after includes remaining and blocked roles ──────────────────────

def test_before_after_reclassification_roles():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "before_after"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))
        ba = json.loads(
            (out / "before_after_functional_reclassification.json").read_text(encoding="utf-8")
        )

        assert ba["baseline_view"]["verdict"] == "task_failed"
        assert ba["yieldos_view"]["verdict"] == "degraded_function_candidate"
        assert len(ba["yieldos_view"]["remaining_roles"]) >= 1
        assert len(ba["yieldos_view"]["blocked_roles"]) >= 1
        assert ba["yieldos_view"]["claim_boundary"] == "candidate_only_human_review_required"


# ── 5. functional_passport links case study ───────────────────────────────────

def test_functional_passport_links_case_study():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "fp_links"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))
        passport = json.loads((out / "functional_passport.json").read_text(encoding="utf-8"))

        assert passport.get("case_study_ref") == "robot_skill_memory_case_study.json", \
            "functional_passport missing case_study_ref"
        assert passport.get("before_after_ref") == "before_after_functional_reclassification.json", \
            "functional_passport missing before_after_ref"


# ── 6. ooda_frame links case study ───────────────────────────────────────────

def test_ooda_links_case_study():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "ooda_links"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))
        ooda = json.loads((out / "ooda_frame.json").read_text(encoding="utf-8"))

        assert ooda.get("case_study_ref") == "robot_skill_memory_case_study.json", \
            "ooda_frame missing case_study_ref"


# ── 7. case_manifest includes optional case study outputs ─────────────────────

def test_case_manifest_includes_case_study_optional_outputs():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "manifest_opts"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))
        manifest = json.loads((out / "case_manifest.json").read_text(encoding="utf-8"))
        optional = manifest.get("optional_outputs", {})

        paths = [v["path"] for v in optional.values()]
        assert "robot_skill_memory_case_study.json" in paths, \
            "case_manifest optional_outputs missing robot_skill_memory_case_study.json"
        assert "robot_skill_memory_case_study.md" in paths, \
            "case_manifest optional_outputs missing robot_skill_memory_case_study.md"
        assert "before_after_functional_reclassification.json" in paths, \
            "case_manifest optional_outputs missing before_after_functional_reclassification.json"


# ── 8. output JSON safety invariant ──────────────────────────────────────────

_CASE_STUDY_FORBIDDEN = [
    "send_ros_command",
    "command_robot",
    "move_joint",
    "execute_recovery",
    "apply_control",
    "auto_repair",
    "certified_root_cause",
    "confirmed_root_cause",
    "safety_certified",
    '"hardware_execution_enabled": true',
]


def test_robot_skill_case_study_json_safety_invariant():
    from yieldos.cli.main import cmd_robot_skill_demo

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "cs_invariant"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))

        for json_file in sorted(out.glob("*.json")):
            text = json_file.read_text(encoding="utf-8").lower()
            for term in _CASE_STUDY_FORBIDDEN:
                assert term not in text, \
                    f"Forbidden term '{term}' found in {json_file.name}"


# ── 9. strict validation passes ───────────────────────────────────────────────

def test_robot_skill_case_study_strict_validation_passes():
    from yieldos.cli.main import cmd_robot_skill_demo, cmd_validate

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "cs_strict"
        cmd_robot_skill_demo(argparse.Namespace(out=str(out)))
        rc = cmd_validate(argparse.Namespace(case=str(out), strict=True))
        assert rc == 0, "strict validation FAILED for Robot Skill Memory Case Study outputs"
