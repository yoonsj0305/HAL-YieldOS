"""Tests for yieldos/domains/semfab/field_aliases.py (v3.0.1)."""
from __future__ import annotations

import pytest

from yieldos.domains.semfab.field_aliases import (
    FIELD_ALIASES,
    UNIT_CONVERSIONS,
    apply_aliases,
    build_field_mapping_report,
    detect_aliases,
)


def test_field_aliases_has_required_keys():
    for key in ("tool_id", "chamber_id", "wafer_id", "die_id", "alarm_code", "bin_code"):
        assert key in FIELD_ALIASES


def test_detect_aliases_canonical_passthrough():
    cols = list(FIELD_ALIASES.keys())
    result = detect_aliases(cols)
    assert result == {}


def test_detect_aliases_maps_known_alias():
    result = detect_aliases(["equipment_id", "wafer_no"])
    assert result.get("equipment_id") == "tool_id"
    assert result.get("wafer_no") == "wafer_id"


def test_detect_aliases_ignores_unknown():
    result = detect_aliases(["unknown_col_xyz"])
    assert "unknown_col_xyz" not in result


def test_apply_aliases_renames_columns():
    rows = [{"equipment_id": "t1", "val": "5"}]
    alias_map = {"equipment_id": "tool_id"}
    out = apply_aliases(rows, alias_map)
    assert out[0]["tool_id"] == "t1"
    assert "equipment_id" not in out[0]


def test_apply_aliases_empty_map_noop():
    rows = [{"tool_id": "t1"}]
    out = apply_aliases(rows, {})
    assert out == rows


def test_apply_aliases_unit_conversion_pressure():
    rows = [{"chamber_pressure_torr": "1.0"}]
    alias_map = {"chamber_pressure_torr": "pressure_mTorr"}
    out = apply_aliases(rows, alias_map)
    assert out[0]["pressure_mTorr"] == "1000.0"


def test_build_field_mapping_report_schema():
    report = build_field_mapping_report(["equipment_id"], {"equipment_id": "tool_id"}, "case_001")
    assert report["schema"] == "hal.yieldos.semiconductor.field_mapping_report.v1"
    assert report["hardware_control_enabled"] is False
    assert report["human_review_required"] is True


def test_build_field_mapping_report_mapped_fields():
    report = build_field_mapping_report(["eqp_id"], {"eqp_id": "tool_id"}, "case_001")
    assert len(report["mapped_fields"]) == 1
    assert report["mapped_fields"][0]["canonical_field"] == "tool_id"


def test_unit_conversions_has_pressure_entry():
    assert "pressure_mTorr" in UNIT_CONVERSIONS
    assert "chamber_pressure_torr" in UNIT_CONVERSIONS["pressure_mTorr"]
