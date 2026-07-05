"""Tests for semiconductor_process_evidence_report.json (v3.0.1)."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from yieldos.domains.semfab.pilot_pack import generate_pilot_pack

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


@pytest.fixture(scope="module")
def per():
    with (SAMPLE_DIR / "tool_log.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tool_rows = list(reader)
        tool_cols = list(reader.fieldnames or [])
    metro_rows = list(csv.DictReader((SAMPLE_DIR / "metrology.csv").open(encoding="utf-8")))
    test_rows = list(csv.DictReader((SAMPLE_DIR / "test_results.csv").open(encoding="utf-8")))
    reports = generate_pilot_pack(
        input_dir=str(SAMPLE_DIR), case_id="per_test", asset_id="chip_demo",
        alias_map={}, tool_cols=tool_cols,
        tool_rows=tool_rows, metro_rows=metro_rows, test_rows=test_rows,
    )
    return reports["semiconductor_process_evidence_report"]


def test_per_schema(per):
    assert per["schema"] == "hal.yieldos.semiconductor.process_evidence_report.v1"


def test_per_candidate_signals_list(per):
    assert isinstance(per["candidate_process_signals"], list)


def test_per_signals_have_claim_boundary(per):
    for sig in per["candidate_process_signals"]:
        assert "claim_boundary" in sig
        assert "not_root_cause" in sig["claim_boundary"]


def test_per_candidate_correlations_list(per):
    assert isinstance(per["candidate_correlations"], list)


def test_per_correlations_have_claim_boundary(per):
    for corr in per["candidate_correlations"]:
        assert "claim_boundary" in corr
        assert "not_root_cause" in corr["claim_boundary"]


def test_per_warnings_list(per):
    assert isinstance(per["warnings"], list)
    assert len(per["warnings"]) > 0


def test_per_no_root_cause_claim_in_correlations(per):
    for corr in per["candidate_correlations"]:
        text = str(corr.get("candidate_interpretation", "")).lower()
        assert "root cause" not in text or "candidate" in text


def test_per_safety(per):
    assert per["hardware_control_enabled"] is False
    assert per["human_review_required"] is True
    assert "process_evidence_not_root_cause" in per["claim_boundary"]
