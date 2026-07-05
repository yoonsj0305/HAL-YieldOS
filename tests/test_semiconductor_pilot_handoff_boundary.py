"""Tests for semiconductor_recovery_compiler_handoff_boundary.json (v3.0.1)."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from yieldos.domains.semfab.pilot_pack import generate_pilot_pack

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


@pytest.fixture(scope="module")
def hb():
    with (SAMPLE_DIR / "tool_log.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tool_rows = list(reader)
        tool_cols = list(reader.fieldnames or [])
    metro_rows = list(csv.DictReader((SAMPLE_DIR / "metrology.csv").open(encoding="utf-8")))
    test_rows = list(csv.DictReader((SAMPLE_DIR / "test_results.csv").open(encoding="utf-8")))
    reports = generate_pilot_pack(
        input_dir=str(SAMPLE_DIR), case_id="hb_test", asset_id="chip_demo",
        alias_map={}, tool_cols=tool_cols,
        tool_rows=tool_rows, metro_rows=metro_rows, test_rows=test_rows,
    )
    return reports["semiconductor_recovery_compiler_handoff_boundary"]


def test_hb_schema(hb):
    assert hb["schema"] == "hal.yieldos.semiconductor.recovery_compiler_handoff_boundary.v1"


def test_hb_yieldos_role(hb):
    assert "yieldos_role" in hb
    assert "generate_candidate" in hb["yieldos_role"]


def test_hb_recovery_compiler_role(hb):
    assert "recovery_compiler_role" in hb


def test_hb_yieldos_does_not_list(hb):
    assert isinstance(hb["yieldos_does_not"], list)
    assert len(hb["yieldos_does_not"]) >= 4
    yd_text = " ".join(hb["yieldos_does_not"]).lower()
    assert "recovery_profile" in yd_text


def test_hb_allowed_handoff_list(hb):
    ah = hb["allowed_handoff"]
    assert isinstance(ah, list)
    assert any("chip_tile_map" in a or "candidate" in a for a in ah)


def test_hb_forbidden_handoff_list(hb):
    fh = hb["forbidden_handoff"]
    assert isinstance(fh, list)
    assert len(fh) > 0


def test_hb_forbidden_has_equipment_control(hb):
    fh_text = " ".join(hb["forbidden_handoff"]).lower()
    assert "equipment_control" in fh_text or "firmware" in fh_text or "command" in fh_text


def test_hb_safety(hb):
    assert hb["hardware_control_enabled"] is False
    assert hb["human_review_required"] is True


def test_hb_claim_boundary(hb):
    assert "claim_boundary" in hb
    assert "handoff_boundary" in hb["claim_boundary"]
