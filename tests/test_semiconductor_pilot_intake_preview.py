"""Tests for semiconductor_recovery_compiler_intake_preview.json (v3.0.1)."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from yieldos.domains.semfab.pilot_pack import generate_pilot_pack

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


@pytest.fixture(scope="module")
def intake():
    with (SAMPLE_DIR / "tool_log.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tool_rows = list(reader)
        tool_cols = list(reader.fieldnames or [])
    metro_rows = list(csv.DictReader((SAMPLE_DIR / "metrology.csv").open(encoding="utf-8")))
    test_rows = list(csv.DictReader((SAMPLE_DIR / "test_results.csv").open(encoding="utf-8")))
    reports = generate_pilot_pack(
        input_dir=str(SAMPLE_DIR), case_id="intake_test", asset_id="chip_demo",
        alias_map={}, tool_cols=tool_cols,
        tool_rows=tool_rows, metro_rows=metro_rows, test_rows=test_rows,
    )
    return reports["semiconductor_recovery_compiler_intake_preview"]


def test_intake_schema(intake):
    assert intake["schema"] == "hal.yieldos.semiconductor.recovery_compiler_intake_preview.v1"


def test_intake_handoff_status_valid(intake):
    assert intake["handoff_status"] in {
        "READY_FOR_OFFLINE_COMPILER_TEST",
        "PARTIAL_FOR_OFFLINE_COMPILER_TEST",
        "NOT_READY_FOR_COMPILER_HANDOFF",
        "INVALID_COMPILER_INTAKE",
    }


def test_intake_ready_when_all_inputs_present(intake):
    # With sample data that has chip_tile_map, workload_roles, and recovery_constraints
    assert intake["handoff_status"] == "READY_FOR_OFFLINE_COMPILER_TEST"


def test_intake_has_handoff_inputs(intake):
    hi = intake["handoff_inputs"]
    assert isinstance(hi, dict)
    assert "chip_tile_map_ref" in hi
    assert "workload_roles_ref" in hi
    assert "recovery_constraints_ref" in hi


def test_intake_no_recovery_profile_key(intake):
    text = json.dumps(intake)
    # The intake preview must never contain an actual recovery_profile
    assert "recovery_profile" not in intake
    # "recovery_profile" as a string value in claim_boundary context is ok
    assert intake.get("claim_boundary") is not None


def test_intake_not_sufficient_for(intake):
    assert "not_sufficient_for" in intake
    nss = intake["not_sufficient_for"]
    assert "hardware_control" in nss or len(nss) > 0


def test_intake_safety(intake):
    assert intake["hardware_control_enabled"] is False
    assert intake["human_review_required"] is True


def test_intake_partial_when_missing_workload(tmp_path):
    import json
    tile_map = {"tiles": [{"tile_id": "T_0_0", "status": "usable", "confidence": 0.9,
                            "evidence_refs": []}]}
    (tmp_path / "chip_tile_map.json").write_text(json.dumps(tile_map), encoding="utf-8")
    # workload_roles.json intentionally NOT created
    reports = generate_pilot_pack(
        input_dir=str(tmp_path), case_id="partial_test", asset_id="x",
        alias_map={}, tool_cols=[], tool_rows=[], metro_rows=[], test_rows=[],
    )
    intake = reports["semiconductor_recovery_compiler_intake_preview"]
    assert intake["handoff_status"] in {
        "PARTIAL_FOR_OFFLINE_COMPILER_TEST",
        "NOT_READY_FOR_COMPILER_HANDOFF",
    }


def test_intake_not_ready_when_no_inputs(tmp_path):
    reports = generate_pilot_pack(
        input_dir=str(tmp_path), case_id="notready_test", asset_id="x",
        alias_map={}, tool_cols=[], tool_rows=[], metro_rows=[], test_rows=[],
    )
    intake = reports["semiconductor_recovery_compiler_intake_preview"]
    assert intake["handoff_status"] == "NOT_READY_FOR_COMPILER_HANDOFF"
