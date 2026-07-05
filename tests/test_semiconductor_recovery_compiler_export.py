"""Tests for semiconductor_recovery_compiler_export.json (v3.0.3).

Verifies the new export artifact: structure, safety invariants, compiler_project,
export_status, and that it is candidate-only (not a recovery profile).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yieldos.cli.main import main

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"

VALID_EXPORT_STATUSES = {
    "READY_FOR_OFFLINE_COMPILER_TEST",
    "PARTIAL_FOR_OFFLINE_COMPILER_TEST",
    "NOT_READY_FOR_COMPILER_HANDOFF",
    "INVALID_COMPILER_EXPORT",
}


@pytest.fixture(scope="module")
def export_output(tmp_path_factory):
    if not SAMPLE_DIR.exists() or not (SAMPLE_DIR / "tool_log.csv").exists():
        pytest.skip("pilot_semiconductor samples not found")
    out = tmp_path_factory.mktemp("semi_pilot_export")
    rc = main([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", str(out),
        "--asset", "export_chip_001",
        "--case", "export_case_001",
    ])
    assert rc == 0, f"semiconductor pilot-pack failed (rc={rc})"
    return out


@pytest.fixture(scope="module")
def rce(export_output):
    return json.loads(
        (export_output / "semiconductor_recovery_compiler_export.json").read_text(encoding="utf-8")
    )


def test_recovery_compiler_export_file_exists(export_output):
    assert (export_output / "semiconductor_recovery_compiler_export.json").exists(), \
        "semiconductor_recovery_compiler_export.json not generated (v3.0.3)"


def test_export_schema(rce):
    assert rce.get("schema") == "hal.yieldos.semiconductor.recovery_compiler_export.v1"


def test_export_compiler_project(rce):
    assert rce.get("compiler_project") == "hal-recovery-compiler"


def test_export_status_is_valid_enum(rce):
    status = rce.get("export_status")
    assert status in VALID_EXPORT_STATUSES, \
        f"export_status invalid: {status!r} (expected one of {VALID_EXPORT_STATUSES})"


def test_export_type_is_candidate(rce):
    assert rce.get("export_type") == "candidate_recovery_compiler_intake"


def test_export_recovery_profile_not_generated(rce):
    assert rce.get("recovery_profile_generated") is False, \
        "recovery_profile_generated must be False in export"


def test_export_hardware_control_disabled(rce):
    assert rce.get("hardware_control_enabled") is False


def test_export_human_review_required(rce):
    assert rce.get("human_review_required") is True


def test_export_claim_boundary(rce):
    assert "claim_boundary" in rce
    assert rce["claim_boundary"] == "compiler_export_candidate_only_not_recovery_profile"


def test_export_has_case_id(rce):
    assert rce.get("case_id"), "export missing case_id"


def test_export_source_yieldos_case(rce):
    src = rce.get("source_yieldos_case", {})
    assert src.get("domain") == "semiconductor"
    assert "functional_passport_ref" in src
    assert "evidence_pack_ref" in src


def test_export_compiler_inputs_structure(rce):
    inputs = rce.get("compiler_inputs", {})
    assert "chip_defect_map_candidate" in inputs
    assert "workloads_candidate" in inputs
    assert "constraints_candidate" in inputs


def test_export_constraints_candidate_has_safety_fields(rce):
    constraints = rce.get("compiler_inputs", {}).get("constraints_candidate", {})
    assert constraints.get("hardware_control_enabled") is False
    assert constraints.get("human_review_required") is True


def test_export_has_what_not_to_do(rce):
    wntd = rce.get("what_not_to_do", [])
    assert isinstance(wntd, list) and len(wntd) > 0, \
        "export what_not_to_do must be a non-empty list"


def test_export_not_sufficient_for_hardware(rce):
    nsf = rce.get("not_sufficient_for", [])
    assert "hardware_control" in nsf, \
        "export not_sufficient_for must include 'hardware_control'"


def test_export_compiler_input_availability(rce):
    avail = rce.get("compiler_input_availability", {})
    assert "chip_tile_map_present" in avail
    assert "workload_roles_present" in avail
    assert "recovery_constraints_present" in avail


def test_export_not_a_recovery_profile_file(export_output):
    assert not (export_output / "recovery_profile.json").exists(), \
        "YieldOS must NEVER generate recovery_profile.json"
