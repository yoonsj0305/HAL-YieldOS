"""Tests for yieldos/domains/semfab/unit_normalization.py (v3.0.1)."""
from __future__ import annotations

from yieldos.domains.semfab.unit_normalization import (
    CANONICAL_UNITS,
    TYPICAL_RANGES,
    build_unit_normalization_report,
    check_column_units,
)


def test_canonical_units_has_key_fields():
    for f in ("rf_power_W", "pressure_mTorr", "temperature_C", "leakage_nA"):
        assert f in CANONICAL_UNITS


def test_typical_ranges_has_key_fields():
    for f in ("rf_power_W", "pressure_mTorr", "temperature_C"):
        low, high = TYPICAL_RANGES[f]
        assert low < high


def test_check_column_units_within_range():
    rows = [{"rf_power_W": "500"} for _ in range(5)]
    results = check_column_units(["rf_power_W"], rows)
    assert len(results) == 1
    assert results[0]["status"] == "within_typical_range"


def test_check_column_units_mismatch_detected():
    rows = [{"rf_power_W": "0.0001"} for _ in range(5)]
    results = check_column_units(["rf_power_W"], rows)
    assert results[0]["status"] == "possible_unit_mismatch"


def test_check_column_units_no_numeric():
    rows = [{"rf_power_W": "N/A"} for _ in range(3)]
    results = check_column_units(["rf_power_W"], rows)
    assert results[0]["status"] == "no_numeric_values"


def test_check_column_units_skips_unknown_field():
    results = check_column_units(["nonexistent_field_xyz"], [{"nonexistent_field_xyz": "5"}])
    assert results == []


def test_build_unit_normalization_report_schema():
    report = build_unit_normalization_report(["rf_power_W"], [{"rf_power_W": "500"}], "c1")
    assert report["schema"] == "hal.yieldos.semiconductor.unit_normalization_report.v1"


def test_build_unit_normalization_report_safety():
    report = build_unit_normalization_report(["rf_power_W"], [{"rf_power_W": "500"}], "c1")
    assert report["hardware_control_enabled"] is False
    assert report["human_review_required"] is True


def test_build_unit_normalization_report_claim_boundary():
    report = build_unit_normalization_report(["rf_power_W"], [{"rf_power_W": "500"}], "c1")
    assert "unit_normalization_preview" in report["claim_boundary"]


def test_build_unit_normalization_report_alias_map():
    alias_map = {"equipment_id": "tool_id"}
    report = build_unit_normalization_report(["rf_power_W"], [{"rf_power_W": "200"}], "c1", alias_map)
    assert report["aliases_applied"] == alias_map
