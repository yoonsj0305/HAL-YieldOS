"""Tests for semiconductor_wafer_die_summary.json (v3.0.1)."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from yieldos.domains.semfab.pilot_pack import generate_pilot_pack

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


@pytest.fixture(scope="module")
def wds():
    with (SAMPLE_DIR / "tool_log.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tool_rows = list(reader)
        tool_cols = list(reader.fieldnames or [])
    metro_rows = list(csv.DictReader((SAMPLE_DIR / "metrology.csv").open(encoding="utf-8")))
    test_rows = list(csv.DictReader((SAMPLE_DIR / "test_results.csv").open(encoding="utf-8")))
    reports = generate_pilot_pack(
        input_dir=str(SAMPLE_DIR), case_id="wds_test", asset_id="chip_demo",
        alias_map={}, tool_cols=tool_cols,
        tool_rows=tool_rows, metro_rows=metro_rows, test_rows=test_rows,
    )
    return reports["semiconductor_wafer_die_summary"]


def test_wds_schema(wds):
    assert wds["schema"] == "hal.yieldos.semiconductor.wafer_die_summary.v1"


def test_wds_die_counts_consistent(wds):
    total = wds["die_count_total"]
    p = wds["die_count_pass"]
    f = wds["die_count_fail"]
    u = wds["die_count_unknown"]
    assert total == p + f + u
    assert total >= 0 and p >= 0 and f >= 0


def test_wds_candidate_remaining_die_list(wds):
    assert isinstance(wds["candidate_remaining_die"], list)


def test_wds_candidate_blocked_die_list(wds):
    assert isinstance(wds["candidate_blocked_die"], list)


def test_wds_lot_ids_list(wds):
    assert isinstance(wds["lot_ids"], list)


def test_wds_wafer_ids_list(wds):
    assert isinstance(wds["wafer_ids"], list)


def test_wds_bin_summary_dict(wds):
    assert isinstance(wds["bin_summary"], dict)


def test_wds_safety(wds):
    assert wds["hardware_control_enabled"] is False
    assert wds["human_review_required"] is True


def test_wds_with_failing_test_rows():
    failing_rows = [
        {"die_id": "die_001", "wafer_id": "w1", "pass_fail": "fail",
         "bin_code": "4", "leakage_nA": "200", "margin_score": "0.1",
         "frequency_MHz": "0", "voltage_V": "0", "current_mA": "0", "temperature_C": "25"}
        for _ in range(5)
    ]
    reports = generate_pilot_pack(
        input_dir=str(SAMPLE_DIR), case_id="fail_test", asset_id="chip_test",
        alias_map={}, tool_cols=list(failing_rows[0].keys()),
        tool_rows=[], metro_rows=[], test_rows=failing_rows,
    )
    wds = reports["semiconductor_wafer_die_summary"]
    assert wds["die_count_fail"] == 5
    assert wds["die_count_pass"] == 0
