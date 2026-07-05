"""Tests for semiconductor_functional_region_map.json (v3.0.1)."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from yieldos.domains.semfab.pilot_pack import generate_pilot_pack

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


@pytest.fixture(scope="module")
def frm():
    with (SAMPLE_DIR / "tool_log.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tool_rows = list(reader)
        tool_cols = list(reader.fieldnames or [])
    metro_rows = list(csv.DictReader((SAMPLE_DIR / "metrology.csv").open(encoding="utf-8")))
    test_rows = list(csv.DictReader((SAMPLE_DIR / "test_results.csv").open(encoding="utf-8")))
    reports = generate_pilot_pack(
        input_dir=str(SAMPLE_DIR), case_id="frm_test", asset_id="chip_demo",
        alias_map={}, tool_cols=tool_cols,
        tool_rows=tool_rows, metro_rows=metro_rows, test_rows=test_rows,
    )
    return reports["semiconductor_functional_region_map"]


def test_frm_schema(frm):
    assert frm["schema"] == "hal.yieldos.semiconductor.functional_region_map.v1"


def test_frm_has_regions_lists(frm):
    assert isinstance(frm["regions"], list)
    assert isinstance(frm["blocked_regions"], list)
    assert isinstance(frm["unknown_regions"], list)


def test_frm_region_entries_have_classification(frm):
    valid_cls = {
        "candidate_remaining", "candidate_reduced", "candidate_blocked",
        "unknown_insufficient_evidence",
    }
    for r in frm["regions"] + frm["blocked_regions"] + frm["unknown_regions"]:
        assert r["classification"] in valid_cls, f"Invalid classification: {r['classification']}"


def test_frm_region_entries_have_claim_boundary(frm):
    for r in frm["regions"] + frm["blocked_regions"]:
        assert "claim_boundary" in r


def test_frm_region_level(frm):
    assert frm["region_level"] in {"chip_tile", "wafer_region", "die_level"}


def test_frm_safety(frm):
    assert frm["hardware_control_enabled"] is False
    assert frm["human_review_required"] is True


def test_frm_with_chip_tile_map(tmp_path):
    import json
    tile_map = {
        "tiles": [
            {"tile_id": "T_0_0", "status": "usable", "confidence": 0.95, "evidence_refs": []},
            {"tile_id": "T_1_0", "status": "defective", "confidence": 0.05, "evidence_refs": []},
            {"tile_id": "T_2_0", "status": "weak", "confidence": 0.65, "evidence_refs": []},
        ]
    }
    (tmp_path / "chip_tile_map.json").write_text(json.dumps(tile_map), encoding="utf-8")
    reports = generate_pilot_pack(
        input_dir=str(tmp_path), case_id="tile_test", asset_id="chip_x",
        alias_map={}, tool_cols=[], tool_rows=[], metro_rows=[], test_rows=[],
    )
    frm = reports["semiconductor_functional_region_map"]
    assert frm["region_level"] == "chip_tile"
    assert len(frm["blocked_regions"]) >= 1
