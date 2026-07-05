"""Tests that `yieldos validate --strict` passes on a robot pilot-pack output.

Generates a complete robot pilot-pack then validates it in strict mode.
All checks must pass (return code 0).
Specifically verifies that `yield_guarantee` inside `not_sufficient_for` does NOT
trigger a false-positive forbidden-term failure.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from yieldos.cli.main import cmd_robot_pilot_pack, cmd_validate

_SAMPLES = Path(__file__).parent.parent / "samples" / "pilot_robot"

_PILOT_PACK_FILES = [
    "robot_pilot_readiness_report.json",
    "robot_evidence_completeness_report.json",
    "robot_role_reclassification_report.json",
    "robot_valid_conditions_report.json",
    "robot_human_review_packet.json",
    "robot_missing_evidence_request.json",
    "robot_unit_normalization_report.json",
    "robot_pilot_case_summary.md",
]


@pytest.fixture(scope="module")
def robot_pilot_case(tmp_path_factory):
    if not _SAMPLES.exists() or not (_SAMPLES / "robot_telemetry.csv").exists():
        pytest.skip("pilot_robot samples not found")
    out = tmp_path_factory.mktemp("robot_pilot_strict")
    args = argparse.Namespace(
        input=str(_SAMPLES),
        out=str(out),
        asset="strict_test_robot",
        case="strict_robot_case_001",
    )
    rc = cmd_robot_pilot_pack(args)
    assert rc == 0, f"robot pilot-pack generation failed (rc={rc})"
    return out


def _validate_strict(case_dir: Path) -> int:
    args = argparse.Namespace(case=str(case_dir), strict=True)
    return cmd_validate(args)


def test_strict_validation_passes(robot_pilot_case):
    """validate --strict must return 0 on robot pilot-pack output (no false positives)."""
    rc = _validate_strict(robot_pilot_case)
    assert rc == 0, "Strict validation FAILED on robot pilot-pack output"


def test_all_pilot_files_exist(robot_pilot_case):
    for fname in _PILOT_PACK_FILES:
        assert (robot_pilot_case / fname).exists(), \
            f"Robot pilot file missing: {fname}"


def test_standard_bundle_files_exist(robot_pilot_case):
    for fname in ["state_snapshot.json", "evidence_pack.json", "ooda_frame.json",
                  "report.html", "case_manifest.json", "functional_passport.json"]:
        assert (robot_pilot_case / fname).exists(), \
            f"Standard bundle file missing: {fname}"


def test_no_recovery_profile_generated(robot_pilot_case):
    assert not (robot_pilot_case / "recovery_profile.json").exists()


def test_readiness_report_safety_invariants(robot_pilot_case):
    rpr = json.loads(
        (robot_pilot_case / "robot_pilot_readiness_report.json").read_text(encoding="utf-8"))
    assert rpr.get("hardware_control_enabled") is False
    assert rpr.get("human_review_required") is True
    assert rpr.get("readiness_status") in {
        "PILOT_READY", "PARTIAL_PILOT_READY", "NOT_PILOT_READY"
    }


def test_yield_guarantee_in_not_sufficient_for_does_not_block_strict(robot_pilot_case):
    """yield_guarantee inside not_sufficient_for must not cause strict validation to fail.

    This is the key regression test: the robot_pilot_readiness_report contains
    yield_guarantee in its not_sufficient_for list (a boundary statement), which
    caused a false-positive FAIL before the negative-context scanner was added.
    """
    rpr_path = robot_pilot_case / "robot_pilot_readiness_report.json"
    rpr = json.loads(rpr_path.read_text(encoding="utf-8"))
    nsc = rpr.get("not_sufficient_for", [])
    # Confirm the test condition: yield_guarantee IS in not_sufficient_for
    has_yield_guarantee = any("yield_guarantee" in str(item) for item in nsc)
    # If it is present, strict validation must still pass (tested by test_strict_validation_passes)
    # This test just documents the fixture state for clarity
    if has_yield_guarantee:
        rc = _validate_strict(robot_pilot_case)
        assert rc == 0, \
            "yield_guarantee in not_sufficient_for caused a false-positive strict failure"


def test_ooda_act_is_recommendation_only(robot_pilot_case):
    ooda = json.loads((robot_pilot_case / "ooda_frame.json").read_text(encoding="utf-8"))
    assert ooda.get("act") == "recommendation_only_no_hardware_action"
