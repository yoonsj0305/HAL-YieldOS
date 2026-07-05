"""Tests consistency between intake_preview, recovery_compiler_export, and handoff_manifest.

Ensures that handoff_status, case_id, and availability flags are consistent
across the three inter-related handoff artifacts.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yieldos.cli.main import main

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


@pytest.fixture(scope="module")
def consistency_output(tmp_path_factory):
    if not SAMPLE_DIR.exists() or not (SAMPLE_DIR / "tool_log.csv").exists():
        pytest.skip("pilot_semiconductor samples not found")
    out = tmp_path_factory.mktemp("semi_pilot_consistency")
    rc = main([
        "semiconductor", "pilot-pack",
        "--input", str(SAMPLE_DIR),
        "--out", str(out),
        "--asset", "consistency_chip_001",
        "--case", "consistency_case_001",
    ])
    assert rc == 0, f"semiconductor pilot-pack failed (rc={rc})"
    return out


@pytest.fixture(scope="module")
def intake(consistency_output):
    return json.loads(
        (consistency_output / "semiconductor_recovery_compiler_intake_preview.json")
        .read_text(encoding="utf-8")
    )


@pytest.fixture(scope="module")
def export(consistency_output):
    return json.loads(
        (consistency_output / "semiconductor_recovery_compiler_export.json")
        .read_text(encoding="utf-8")
    )


@pytest.fixture(scope="module")
def manifest(consistency_output):
    return json.loads(
        (consistency_output / "semiconductor_handoff_manifest.json")
        .read_text(encoding="utf-8")
    )


def test_intake_and_export_case_id_match(intake, export):
    assert intake.get("case_id") == export.get("case_id"), \
        f"case_id mismatch: intake={intake.get('case_id')!r}, export={export.get('case_id')!r}"


def test_intake_and_manifest_case_id_match(intake, manifest):
    assert intake.get("case_id") == manifest.get("case_id"), \
        f"case_id mismatch: intake={intake.get('case_id')!r}, manifest={manifest.get('case_id')!r}"


def test_intake_and_export_handoff_status_match(intake, export):
    intake_status = intake.get("handoff_status")
    export_status = export.get("export_status")
    assert intake_status == export_status, \
        f"handoff_status mismatch: intake={intake_status!r}, export={export_status!r}"


def test_intake_and_manifest_handoff_status_match(intake, manifest):
    intake_status = intake.get("handoff_status")
    manifest_status = manifest.get("handoff_status")
    assert intake_status == manifest_status, \
        f"handoff_status mismatch: intake={intake_status!r}, manifest={manifest_status!r}"


def test_intake_export_ref_points_to_export(intake):
    assert intake.get("export_ref") == "semiconductor_recovery_compiler_export.json", \
        "intake_preview.export_ref must point to semiconductor_recovery_compiler_export.json"


def test_intake_handoff_manifest_ref_points_to_manifest(intake):
    assert intake.get("handoff_manifest_ref") == "semiconductor_handoff_manifest.json", \
        "intake_preview.handoff_manifest_ref must point to semiconductor_handoff_manifest.json"


def test_intake_recovery_profile_generated_false(intake):
    assert intake.get("recovery_profile_generated") is False, \
        "intake_preview.recovery_profile_generated must be False (v3.0.3)"


def test_export_allowed_files_consistent_with_manifest(export, manifest):
    manifest_allowed = set(manifest.get("allowed_files", []))
    assert "semiconductor_recovery_compiler_export.json" in manifest_allowed, \
        "manifest.allowed_files must include the export file"


def test_chip_tile_map_availability_consistent(intake, export):
    intake_present = intake.get("handoff_inputs", {}).get("chip_tile_map_ref") is not None
    export_avail = export.get("compiler_input_availability", {}).get("chip_tile_map_present", False)
    assert intake_present == export_avail, \
        (f"chip_tile_map availability inconsistent: "
         f"intake_present={intake_present}, export_avail={export_avail}")


def test_workload_roles_availability_consistent(intake, export):
    intake_present = intake.get("handoff_inputs", {}).get("workload_roles_ref") is not None
    export_avail = export.get("compiler_input_availability", {}).get("workload_roles_present", False)
    assert intake_present == export_avail, \
        (f"workload_roles availability inconsistent: "
         f"intake_present={intake_present}, export_avail={export_avail}")


def test_recovery_constraints_availability_consistent(intake, export):
    intake_present = intake.get("handoff_inputs", {}).get("recovery_constraints_ref") is not None
    export_avail = export.get("compiler_input_availability", {}).get("recovery_constraints_present", False)
    assert intake_present == export_avail, \
        (f"recovery_constraints availability inconsistent: "
         f"intake_present={intake_present}, export_avail={export_avail}")


def test_all_three_hardware_control_disabled(intake, export, manifest):
    for name, doc in [("intake", intake), ("export", export), ("manifest", manifest)]:
        assert doc.get("hardware_control_enabled") is False, \
            f"{name} hardware_control_enabled must be False"


def test_no_recovery_profile_generated(consistency_output):
    assert not (consistency_output / "recovery_profile.json").exists()
