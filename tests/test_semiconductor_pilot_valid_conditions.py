"""Tests for semiconductor_valid_conditions_report.json (v3.0.1)."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from yieldos.domains.semfab.pilot_pack import generate_pilot_pack

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


@pytest.fixture(scope="module")
def vcr():
    with (SAMPLE_DIR / "tool_log.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tool_rows = list(reader)
        tool_cols = list(reader.fieldnames or [])
    metro_rows = list(csv.DictReader((SAMPLE_DIR / "metrology.csv").open(encoding="utf-8")))
    test_rows = list(csv.DictReader((SAMPLE_DIR / "test_results.csv").open(encoding="utf-8")))
    reports = generate_pilot_pack(
        input_dir=str(SAMPLE_DIR), case_id="vcr_test", asset_id="chip_demo",
        alias_map={}, tool_cols=tool_cols,
        tool_rows=tool_rows, metro_rows=metro_rows, test_rows=test_rows,
    )
    return reports["semiconductor_valid_conditions_report"]


def test_vcr_schema(vcr):
    assert vcr["schema"] == "hal.yieldos.semiconductor.valid_conditions_report.v1"


def test_vcr_valid_conditions_list(vcr):
    assert isinstance(vcr["valid_conditions"], list)


def test_vcr_valid_conditions_entries_have_condition(vcr):
    for c in vcr["valid_conditions"]:
        assert "condition" in c, "valid_condition entry missing 'condition'"
        assert "condition_id" in c


def test_vcr_what_not_to_do_non_empty(vcr):
    wntd = vcr["what_not_to_do"]
    assert isinstance(wntd, list)
    assert len(wntd) > 0


def test_vcr_what_not_to_do_has_recipe_control(vcr):
    wntd_text = " ".join(vcr["what_not_to_do"]).lower()
    assert "recipe" in wntd_text or "control" in wntd_text


def test_vcr_invalid_or_unknown_conditions_list(vcr):
    assert isinstance(vcr.get("invalid_or_unknown_conditions"), list)


def test_vcr_safety(vcr):
    assert vcr["hardware_control_enabled"] is False
    assert vcr["human_review_required"] is True
