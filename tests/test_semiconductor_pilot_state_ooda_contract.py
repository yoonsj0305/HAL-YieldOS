"""Tests v3.0.3 state_snapshot.json and ooda_frame.json contract for semiconductor pilot-pack.

Verifies snapshot_type, candidate_state, linked_reports, and safety fields in state_snapshot,
and the dict-format act field in ooda_frame.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yieldos.cli.main import main

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


@pytest.fixture(scope="module")
def state_ooda_output(tmp_path_factory):
    if not SAMPLE_DIR.exists() or not (SAMPLE_DIR / "tool_log.csv").exists():
        pytest.skip("pilot_semiconductor samples not found")
    out = tmp_path_factory.mktemp("semi_pilot_state_ooda")
    rc = main([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", str(out),
        "--asset", "state_chip_001",
        "--case", "state_case_001",
    ])
    assert rc == 0, f"semiconductor pilot-pack failed (rc={rc})"
    return out


@pytest.fixture(scope="module")
def ss(state_ooda_output):
    return json.loads(
        (state_ooda_output / "state_snapshot.json").read_text(encoding="utf-8")
    )


@pytest.fixture(scope="module")
def ooda(state_ooda_output):
    return json.loads(
        (state_ooda_output / "ooda_frame.json").read_text(encoding="utf-8")
    )


# ── state_snapshot checks ────────────────────────────────────────────────────

def test_state_snapshot_type(ss):
    assert ss.get("snapshot_type") == "semiconductor_pilot_candidate_state", \
        f"state_snapshot.snapshot_type wrong: {ss.get('snapshot_type')!r}"


def test_state_snapshot_has_candidate_state(ss):
    assert "candidate_state" in ss, "state_snapshot missing candidate_state (v3.0.3)"


def test_state_snapshot_candidate_state_human_review_required(ss):
    assert ss.get("candidate_state", {}).get("human_review_required") is True


def test_state_snapshot_has_linked_reports(ss):
    assert "linked_reports" in ss, "state_snapshot missing linked_reports (v3.0.3)"


def test_state_snapshot_linked_reports_includes_export(ss):
    linked = ss.get("linked_reports", {})
    assert "recovery_compiler_export_ref" in linked, \
        "state_snapshot.linked_reports missing recovery_compiler_export_ref"
    assert linked["recovery_compiler_export_ref"] == "semiconductor_recovery_compiler_export.json"


def test_state_snapshot_linked_reports_includes_intake_preview(ss):
    linked = ss.get("linked_reports", {})
    assert "recovery_compiler_intake_preview_ref" in linked


def test_state_snapshot_safety_recovery_profile_not_generated(ss):
    safety = ss.get("safety", {})
    assert safety.get("recovery_profile_generated") is False, \
        "state_snapshot.safety.recovery_profile_generated must be False"


def test_state_snapshot_safety_recipe_control_disabled(ss):
    safety = ss.get("safety", {})
    assert safety.get("recipe_control_enabled") is False


def test_state_snapshot_safety_tool_control_disabled(ss):
    safety = ss.get("safety", {})
    assert safety.get("tool_control_enabled") is False


def test_state_snapshot_safety_claim_boundary(ss):
    safety = ss.get("safety", {})
    assert "claim_boundary" in safety, "state_snapshot.safety missing claim_boundary"
    assert safety["claim_boundary"] == "candidate_state_snapshot_not_operational_authority"


def test_state_snapshot_mode_read_only(ss):
    assert ss.get("mode") == "read_only_shadow"


def test_state_snapshot_hardware_execution_disabled(ss):
    safety = ss.get("safety", {})
    assert safety.get("hardware_execution_enabled") is False


# ── ooda_frame checks ────────────────────────────────────────────────────────

def test_ooda_act_is_dict(ooda):
    act = ooda.get("act")
    assert isinstance(act, dict), \
        f"ooda_frame.act must be dict for semiconductor pilot, got {type(act)}: {act!r}"


def test_ooda_act_automatic_action_disabled(ooda):
    assert ooda["act"].get("automatic_action_enabled") is False


def test_ooda_act_hardware_control_disabled(ooda):
    assert ooda["act"].get("hardware_control_enabled") is False


def test_ooda_act_recipe_control_disabled(ooda):
    assert ooda["act"].get("recipe_control_enabled") is False


def test_ooda_act_tool_control_disabled(ooda):
    assert ooda["act"].get("tool_control_enabled") is False


def test_ooda_schema_present(ooda):
    assert "schema" in ooda, "ooda_frame missing schema"


def test_recovery_profile_not_generated(state_ooda_output):
    assert not (state_ooda_output / "recovery_profile.json").exists()
