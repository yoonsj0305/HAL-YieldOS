"""Tests for semiconductor_handoff_manifest.json (v3.0.3).

Verifies the new handoff manifest: structure, allowed_files, forbidden_files,
handoff_conditions, and safety invariants.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yieldos.cli.main import main

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


@pytest.fixture(scope="module")
def manifest_output(tmp_path_factory):
    if not SAMPLE_DIR.exists() or not (SAMPLE_DIR / "tool_log.csv").exists():
        pytest.skip("pilot_semiconductor samples not found")
    out = tmp_path_factory.mktemp("semi_pilot_manifest")
    rc = main([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", str(out),
        "--asset", "manifest_chip_001",
        "--case", "manifest_case_001",
    ])
    assert rc == 0, f"semiconductor pilot-pack failed (rc={rc})"
    return out


@pytest.fixture(scope="module")
def hm(manifest_output):
    return json.loads(
        (manifest_output / "semiconductor_handoff_manifest.json").read_text(encoding="utf-8")
    )


def test_handoff_manifest_file_exists(manifest_output):
    assert (manifest_output / "semiconductor_handoff_manifest.json").exists(), \
        "semiconductor_handoff_manifest.json not generated (v3.0.3)"


def test_handoff_manifest_schema(hm):
    assert hm.get("schema") == "hal.yieldos.semiconductor.handoff_manifest.v1"


def test_handoff_manifest_target(hm):
    assert hm.get("handoff_target") == "hal-recovery-compiler"


def test_handoff_manifest_has_case_id(hm):
    assert hm.get("case_id"), "handoff_manifest missing case_id"


def test_handoff_manifest_status_valid(hm):
    valid = {
        "READY_FOR_OFFLINE_COMPILER_TEST",
        "PARTIAL_FOR_OFFLINE_COMPILER_TEST",
        "NOT_READY_FOR_COMPILER_HANDOFF",
        "INVALID_COMPILER_INTAKE",
    }
    status = hm.get("handoff_status")
    assert status in valid, f"handoff_status invalid: {status!r}"


def test_handoff_manifest_allowed_files_includes_export(hm):
    allowed = hm.get("allowed_files", [])
    assert "semiconductor_recovery_compiler_export.json" in allowed, \
        "allowed_files must include semiconductor_recovery_compiler_export.json"


def test_handoff_manifest_forbidden_files_includes_recovery_profile(hm):
    forbidden = hm.get("forbidden_files", [])
    assert "recovery_profile.json" in forbidden, \
        "forbidden_files must include recovery_profile.json"


def test_handoff_manifest_forbidden_files_includes_firmware_flash(hm):
    forbidden = hm.get("forbidden_files", [])
    assert "firmware_flash_payload.bin" in forbidden, \
        "forbidden_files must include firmware_flash_payload.bin"


def test_handoff_manifest_has_handoff_conditions(hm):
    conditions = hm.get("handoff_conditions", [])
    assert isinstance(conditions, list) and len(conditions) > 0, \
        "handoff_manifest must have non-empty handoff_conditions"


def test_handoff_manifest_conditions_mention_human_review(hm):
    conditions = hm.get("handoff_conditions", [])
    assert any("human review" in c.lower() for c in conditions), \
        "handoff_conditions must mention human review"


def test_handoff_manifest_hardware_control_disabled(hm):
    assert hm.get("hardware_control_enabled") is False


def test_handoff_manifest_human_review_required(hm):
    assert hm.get("human_review_required") is True


def test_handoff_manifest_claim_boundary(hm):
    assert "claim_boundary" in hm
    assert hm["claim_boundary"] == "handoff_manifest_not_operational_authority"


def test_handoff_manifest_recovery_profile_not_generated(manifest_output):
    assert not (manifest_output / "recovery_profile.json").exists(), \
        "YieldOS must NEVER generate recovery_profile.json"
