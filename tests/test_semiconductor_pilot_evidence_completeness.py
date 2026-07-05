"""Tests for semiconductor_evidence_completeness_report.json (v3.0.1)."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from yieldos.domains.semfab.pilot_pack import generate_pilot_pack

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


@pytest.fixture(scope="module")
def ecr():
    with (SAMPLE_DIR / "tool_log.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tool_rows = list(reader)
        tool_cols = list(reader.fieldnames or [])
    metro_rows = list(csv.DictReader((SAMPLE_DIR / "metrology.csv").open(encoding="utf-8")))
    test_rows = list(csv.DictReader((SAMPLE_DIR / "test_results.csv").open(encoding="utf-8")))
    reports = generate_pilot_pack(
        input_dir=str(SAMPLE_DIR), case_id="ecr_test", asset_id="chip_demo",
        alias_map={}, tool_cols=tool_cols,
        tool_rows=tool_rows, metro_rows=metro_rows, test_rows=test_rows,
    )
    return reports["semiconductor_evidence_completeness_report"]


def test_ecr_schema(ecr):
    assert ecr["schema"] == "hal.yieldos.semiconductor.evidence_completeness_report.v1"


def test_ecr_completeness_score_range(ecr):
    assert 0.0 <= ecr["completeness_score"] <= 1.0


def test_ecr_completeness_score_percent(ecr):
    assert 0.0 <= ecr["completeness_score_percent"] <= 100.0
    assert abs(ecr["completeness_score"] * 100 - ecr["completeness_score_percent"]) < 0.1


def test_ecr_required_inputs_dict(ecr):
    ri = ecr["required_inputs"]
    assert isinstance(ri, dict)
    assert "tool_log_present" in ri
    assert "metrology_present" in ri
    assert "chip_tile_map_present" in ri


def test_ecr_functional_yield_inputs(ecr):
    fyi = ecr["functional_yield_inputs"]
    assert isinstance(fyi, dict)
    assert "remaining_die_evidence_ready" in fyi
    assert "blocked_die_evidence_ready" in fyi
    assert "recovery_compiler_intake_ready" in fyi


def test_ecr_not_sufficient_for(ecr):
    assert "not_sufficient_for" in ecr
    assert len(ecr["not_sufficient_for"]) > 0


def test_ecr_safety(ecr):
    assert ecr["hardware_control_enabled"] is False
    assert ecr["human_review_required"] is True


def test_ecr_with_no_files(tmp_path):
    from yieldos.domains.semfab.pilot_pack import generate_pilot_pack
    reports = generate_pilot_pack(
        input_dir=str(tmp_path), case_id="empty_test", asset_id="x",
        alias_map={}, tool_cols=[], tool_rows=[], metro_rows=[], test_rows=[],
    )
    ecr = reports["semiconductor_evidence_completeness_report"]
    assert ecr["completeness_score"] <= 0.75
