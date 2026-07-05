"""Tests that `yieldos validate --strict` passes on a semiconductor pilot-pack output.

Generates a complete semiconductor pilot-pack then validates it in strict mode.
All checks must pass (return code 0).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from yieldos.cli.main import cmd_validate, main

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"

_SEMI_PP_FILES = [
    "semiconductor_pilot_readiness_report.json",
    "semiconductor_evidence_completeness_report.json",
    "semiconductor_wafer_die_summary.json",
    "semiconductor_functional_region_map.json",
    "semiconductor_role_candidate_map.json",
    "semiconductor_valid_conditions_report.json",
    "semiconductor_process_evidence_report.json",
    "semiconductor_human_review_packet.json",
    "semiconductor_missing_evidence_request.json",
    "semiconductor_recovery_compiler_intake_preview.json",
    "semiconductor_recovery_compiler_handoff_boundary.json",
    "semiconductor_pilot_case_summary.md",
]


@pytest.fixture(scope="module")
def semi_pilot_case(tmp_path_factory):
    if not SAMPLE_DIR.exists() or not (SAMPLE_DIR / "tool_log.csv").exists():
        pytest.skip("pilot_semiconductor samples not found")
    out = tmp_path_factory.mktemp("semi_pilot_strict")
    rc = main([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", str(out),
        "--asset", "strict_test_chip",
        "--case", "strict_test_case_001",
    ])
    assert rc == 0, f"semiconductor pilot-pack generation failed (rc={rc})"
    return out


def _validate_strict(case_dir: Path) -> int:
    args = argparse.Namespace(case=str(case_dir), strict=True)
    return cmd_validate(args)


def test_strict_validation_passes(semi_pilot_case):
    """validate --strict must return 0 (all checks pass) on semiconductor pilot-pack output."""
    rc = _validate_strict(semi_pilot_case)
    assert rc == 0, "Strict validation FAILED on semiconductor pilot-pack output"


def test_all_11_pilot_files_exist(semi_pilot_case):
    for fname in _SEMI_PP_FILES:
        assert (semi_pilot_case / fname).exists(), \
            f"Semiconductor pilot file missing: {fname}"


def test_no_recovery_profile_generated(semi_pilot_case):
    assert not (semi_pilot_case / "recovery_profile.json").exists(), \
        "YieldOS must NEVER generate recovery_profile.json"


def test_standard_files_exist(semi_pilot_case):
    for fname in ["state_snapshot.json", "evidence_pack.json", "ooda_frame.json",
                  "report.html", "case_manifest.json", "functional_passport.json",
                  "input_validation.json", "decision_readiness_report.json"]:
        assert (semi_pilot_case / fname).exists(), \
            f"Standard bundle file missing: {fname}"


def test_intake_preview_no_recovery_profile_key(semi_pilot_case):
    ip = json.loads(
        (semi_pilot_case / "semiconductor_recovery_compiler_intake_preview.json")
        .read_text(encoding="utf-8")
    )
    assert "recovery_profile" not in ip, \
        "intake_preview MUST NOT have a recovery_profile key"


def test_handoff_boundary_has_forbidden_handoff(semi_pilot_case):
    hb = json.loads(
        (semi_pilot_case / "semiconductor_recovery_compiler_handoff_boundary.json")
        .read_text(encoding="utf-8")
    )
    assert isinstance(hb.get("forbidden_handoff"), list)
    assert len(hb["forbidden_handoff"]) > 0


def test_readiness_report_safety_fields(semi_pilot_case):
    rr = json.loads(
        (semi_pilot_case / "semiconductor_pilot_readiness_report.json")
        .read_text(encoding="utf-8")
    )
    assert rr.get("hardware_control_enabled") is False
    assert rr.get("human_review_required") is True


def test_human_review_packet_has_forbidden_decisions(semi_pilot_case):
    hrp = json.loads(
        (semi_pilot_case / "semiconductor_human_review_packet.json")
        .read_text(encoding="utf-8")
    )
    fds = hrp.get("forbidden_decisions", [])
    assert isinstance(fds, list) and len(fds) > 0, \
        "semiconductor_human_review_packet must have non-empty forbidden_decisions"


def test_all_pilot_files_have_claim_boundary(semi_pilot_case):
    """All 11 semiconductor pilot JSONs must have a top-level claim_boundary field."""
    for fname in _SEMI_PP_FILES:
        if not fname.endswith(".json"):
            continue
        data = json.loads((semi_pilot_case / fname).read_text(encoding="utf-8"))
        assert "claim_boundary" in data, \
            f"{fname} is missing top-level claim_boundary"


def test_ooda_frame_act_is_review_only_dict(semi_pilot_case):
    ooda = json.loads((semi_pilot_case / "ooda_frame.json").read_text(encoding="utf-8"))
    act = ooda.get("act")
    assert isinstance(act, dict), \
        f"semiconductor pilot ooda.act must be dict (v3.0.3), got {act!r}"
    assert act.get("automatic_action_enabled") is False, \
        "ooda.act.automatic_action_enabled must be False"
    assert act.get("hardware_control_enabled") is False, \
        "ooda.act.hardware_control_enabled must be False"
    assert act.get("recipe_control_enabled") is False, \
        "ooda.act.recipe_control_enabled must be False"
