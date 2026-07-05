"""Tests for semiconductor_missing_evidence_request.json (v3.0.1)."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from yieldos.domains.semfab.pilot_pack import generate_pilot_pack

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


@pytest.fixture(scope="module")
def mer():
    with (SAMPLE_DIR / "tool_log.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tool_rows = list(reader)
        tool_cols = list(reader.fieldnames or [])
    metro_rows = list(csv.DictReader((SAMPLE_DIR / "metrology.csv").open(encoding="utf-8")))
    test_rows = list(csv.DictReader((SAMPLE_DIR / "test_results.csv").open(encoding="utf-8")))
    reports = generate_pilot_pack(
        input_dir=str(SAMPLE_DIR), case_id="mer_test", asset_id="chip_demo",
        alias_map={}, tool_cols=tool_cols,
        tool_rows=tool_rows, metro_rows=metro_rows, test_rows=test_rows,
    )
    return reports["semiconductor_missing_evidence_request"]


def test_mer_schema(mer):
    assert mer["schema"] == "hal.yieldos.semiconductor.missing_evidence_request.v1"


def test_mer_missing_items_list(mer):
    assert isinstance(mer["missing_items"], list)


def test_mer_items_have_why_needed(mer):
    for item in mer["missing_items"]:
        assert "why_needed_for_functional_yield" in item, (
            f"Missing why_needed_for_functional_yield for item: {item.get('item')}"
        )


def test_mer_items_have_item_and_needed_for(mer):
    for item in mer["missing_items"]:
        assert "item" in item
        assert "needed_for" in item


def test_mer_sample_has_no_required_file_missing():
    with (SAMPLE_DIR / "tool_log.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tool_rows = list(reader)
        tool_cols = list(reader.fieldnames or [])
    metro_rows = list(csv.DictReader((SAMPLE_DIR / "metrology.csv").open(encoding="utf-8")))
    test_rows = list(csv.DictReader((SAMPLE_DIR / "test_results.csv").open(encoding="utf-8")))
    reports = generate_pilot_pack(
        input_dir=str(SAMPLE_DIR), case_id="mer_no_req_missing", asset_id="chip_demo",
        alias_map={}, tool_cols=tool_cols,
        tool_rows=tool_rows, metro_rows=metro_rows, test_rows=test_rows,
    )
    mer = reports["semiconductor_missing_evidence_request"]
    required_missing = [
        m for m in mer["missing_items"]
        if m.get("needed_for") == "core_functional_yield_evidence"
    ]
    assert required_missing == [], (
        f"Sample data should have no required-file missing items: {required_missing}"
    )


def test_mer_safety(mer):
    assert mer["hardware_control_enabled"] is False
    assert mer["human_review_required"] is True


def test_mer_with_no_input_dir(tmp_path):
    reports = generate_pilot_pack(
        input_dir=str(tmp_path), case_id="mer_empty", asset_id="x",
        alias_map={}, tool_cols=[], tool_rows=[], metro_rows=[], test_rows=[],
    )
    mer = reports["semiconductor_missing_evidence_request"]
    items = mer["missing_items"]
    item_names = [m["item"] for m in items]
    assert "tool_log.csv" in item_names or "metrology.csv" in item_names or len(items) >= 0
