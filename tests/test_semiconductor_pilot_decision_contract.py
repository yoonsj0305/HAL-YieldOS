"""Tests that decision_readiness_report.json and ooda_frame.json fulfill v3.0.3 decision contract.

Checks allowed/forbidden decision lists, automatic_decision_enabled=false,
and ooda_frame.decide structure for semiconductor pilot-pack output.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yieldos.cli.main import main

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"

EXPECTED_ALLOWED_DECISIONS = {
    "request_missing_data",
    "accept_for_offline_functional_yield_review",
    "allow_recovery_compiler_intake_preview",
    "allow_recovery_compiler_export_for_offline_testing",
    "reject_due_to_insufficient_evidence",
}

EXPECTED_FORBIDDEN_DECISIONS = {
    "modify_recipe",
    "control_equipment",
    "execute_recovery_profile",
    "claim_root_cause",
    "guarantee_yield",
    "certify_timing",
    "flash_firmware",
    "runtime_apply_profile",
}


@pytest.fixture(scope="module")
def decision_output(tmp_path_factory):
    if not SAMPLE_DIR.exists() or not (SAMPLE_DIR / "tool_log.csv").exists():
        pytest.skip("pilot_semiconductor samples not found")
    out = tmp_path_factory.mktemp("semi_pilot_decision")
    rc = main([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", str(out),
        "--asset", "decision_chip_001",
        "--case", "decision_case_001",
    ])
    assert rc == 0, f"semiconductor pilot-pack failed (rc={rc})"
    return out


@pytest.fixture(scope="module")
def drr(decision_output):
    return json.loads(
        (decision_output / "decision_readiness_report.json").read_text(encoding="utf-8")
    )


@pytest.fixture(scope="module")
def ooda(decision_output):
    return json.loads(
        (decision_output / "ooda_frame.json").read_text(encoding="utf-8")
    )


def test_drr_allowed_decisions_is_list(drr):
    allowed = drr.get("allowed_decisions", [])
    assert isinstance(allowed, list) and len(allowed) > 0


@pytest.mark.parametrize("decision", sorted(EXPECTED_ALLOWED_DECISIONS))
def test_drr_allowed_decision_present(drr, decision):
    assert decision in drr.get("allowed_decisions", []), \
        f"decision_readiness allowed_decisions missing: {decision!r}"


def test_drr_forbidden_decisions_is_list(drr):
    forbidden = drr.get("forbidden_decisions", [])
    assert isinstance(forbidden, list) and len(forbidden) > 0


@pytest.mark.parametrize("decision", sorted(EXPECTED_FORBIDDEN_DECISIONS))
def test_drr_forbidden_decision_present(drr, decision):
    assert decision in drr.get("forbidden_decisions", []), \
        f"decision_readiness forbidden_decisions missing: {decision!r}"


def test_drr_automatic_decision_disabled(drr):
    assert drr.get("automatic_decision_enabled") is False


def test_drr_hardware_control_disabled(drr):
    assert drr.get("hardware_control_enabled") is False


def test_drr_recipe_control_disabled(drr):
    assert drr.get("recipe_control_enabled") is False


def test_drr_tool_control_disabled(drr):
    assert drr.get("tool_control_enabled") is False


def test_drr_human_review_required(drr):
    assert drr.get("human_review_required") is True


def test_ooda_act_is_dict(ooda):
    act = ooda.get("act")
    assert isinstance(act, dict), \
        f"ooda_frame.act must be dict for semiconductor pilot (v3.0.3), got {type(act)}: {act!r}"


def test_ooda_act_automatic_action_disabled(ooda):
    assert ooda["act"].get("automatic_action_enabled") is False


def test_ooda_act_hardware_control_disabled(ooda):
    assert ooda["act"].get("hardware_control_enabled") is False


def test_ooda_act_recipe_control_disabled(ooda):
    assert ooda["act"].get("recipe_control_enabled") is False


def test_ooda_act_tool_control_disabled(ooda):
    assert ooda["act"].get("tool_control_enabled") is False


def test_ooda_act_claim_boundary(ooda):
    assert "claim_boundary" in ooda["act"], "ooda.act missing claim_boundary"


def test_ooda_decide_allowed_decisions(ooda):
    decide = ooda.get("decide", {})
    allowed = decide.get("allowed_decisions", [])
    assert isinstance(allowed, list) and len(allowed) > 0, \
        "ooda_frame.decide.allowed_decisions must be a non-empty list"


def test_ooda_decide_forbidden_decisions(ooda):
    decide = ooda.get("decide", {})
    forbidden = decide.get("forbidden_decisions", [])
    assert isinstance(forbidden, list) and len(forbidden) > 0, \
        "ooda_frame.decide.forbidden_decisions must be a non-empty list"


def test_ooda_decide_human_review_required(ooda):
    decide = ooda.get("decide", {})
    assert decide.get("human_review_required") is True


def test_recovery_profile_not_generated(decision_output):
    assert not (decision_output / "recovery_profile.json").exists()
