"""tests/test_robot_unit_normalization.py

Unit tests for yieldos/domains/robot/unit_normalization.py.
v3.0.0 - Robot Pilot-Ready Edition.
"""
from __future__ import annotations

from yieldos.domains.robot.unit_normalization import (
    build_unit_normalization_report,
    check_column_units,
)


def _make_rows(col: str, values: list) -> list[dict]:
    return [{col: str(v)} for v in values]


def test_check_column_units_canonical_normal_values():
    columns = ["motor_current_A", "joint_temp_C"]
    rows = [
        {"motor_current_A": "5.2", "joint_temp_C": "42.3"},
        {"motor_current_A": "6.1", "joint_temp_C": "44.8"},
    ]
    results = check_column_units(columns, rows)
    by_field = {r["field"]: r for r in results}
    assert by_field["motor_current_A"]["status"] == "LIKELY_CORRECT"
    assert by_field["joint_temp_C"]["status"] == "LIKELY_CORRECT"


def test_check_column_units_possible_unit_mismatch_detects_milliamps():
    columns = ["motor_current_A"]
    rows = _make_rows("motor_current_A", [5200.0, 6100.0, 4800.0])
    results = check_column_units(columns, rows)
    assert results[0]["status"] == "POSSIBLE_UNIT_MISMATCH"


def test_check_column_units_no_data():
    columns = ["motor_current_A"]
    rows = [{"motor_current_A": ""}, {"motor_current_A": None}]
    results = check_column_units(columns, rows)
    assert results[0]["status"] == "NO_DATA"


def test_build_unit_normalization_report_schema():
    columns = ["motor_current_A", "joint_temp_C", "imu_vibration_g", "position_error_mm"]
    rows = [
        {"motor_current_A": "5.2", "joint_temp_C": "42.0",
         "imu_vibration_g": "0.025", "position_error_mm": "0.45"},
    ]
    report = build_unit_normalization_report(columns, rows, "case_001", {})
    assert report["schema"] == "hal.yieldos.robot.unit_normalization_report.v1"
    assert report["unit_normalization_preview"] is True
    assert report["columns_checked"] >= 4
    assert report["safety_boundary"]["hardware_execution_enabled"] is False
    assert report["safety_boundary"]["human_review_required"] is True
    assert report["claim_boundary"] == "unit_check_is_heuristic_not_calibrated_measurement"


def test_build_unit_normalization_report_with_alias_conversions():
    columns = ["joint_temp_C"]
    rows = [{"joint_temp_C": "38.5"}]
    alias_map = {"temperature_c": "joint_temp_C"}
    report = build_unit_normalization_report(columns, rows, "case_002", alias_map)
    assert len(report["alias_conversions_applied"]) == 1
    assert report["alias_conversions_applied"][0]["input_field"] == "temperature_c"
