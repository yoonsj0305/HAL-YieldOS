"""tests/test_robot_field_aliases.py

Unit tests for yieldos/domains/robot/field_aliases.py.
v3.0.0 - Robot Pilot-Ready Edition.
"""
from __future__ import annotations

from yieldos.domains.robot.field_aliases import (
    FIELD_ALIASES,
    apply_aliases,
    build_field_mapping_report,
    detect_aliases,
)


def test_detect_aliases_returns_empty_for_canonical_columns():
    canonical_cols = list(FIELD_ALIASES.keys())
    result = detect_aliases(canonical_cols)
    assert result == {}, f"Canonical columns should produce no alias map, got: {result}"


def test_detect_aliases_maps_temperature_c_to_joint_temp():
    cols = ["timestamp", "temperature_c", "vibration_rms", "position_error_deg"]
    result = detect_aliases(cols)
    assert "temperature_c" in result
    assert result["temperature_c"] == "joint_temp_C"
    assert "vibration_rms" in result
    assert result["vibration_rms"] == "imu_vibration_g"


def test_apply_aliases_remaps_column_names():
    rows = [
        {"temperature_c": "38.5", "vibration_rms": "0.021", "position_error_deg": "0.45"},
    ]
    alias_map = {"temperature_c": "joint_temp_C", "vibration_rms": "imu_vibration_g"}
    result = apply_aliases(rows, alias_map)
    assert len(result) == 1
    assert "joint_temp_C" in result[0]
    assert "imu_vibration_g" in result[0]
    assert result[0]["joint_temp_C"] == "38.5"
    assert "temperature_c" not in result[0]


def test_apply_aliases_applies_unit_conversion_for_position_error_deg():
    rows = [{"position_error_deg": "1.0"}]
    alias_map = {"position_error_deg": "position_error_mm"}
    result = apply_aliases(rows, alias_map)
    assert "position_error_mm" in result[0]
    val = float(result[0]["position_error_mm"])
    assert abs(val - 17.4533) < 0.01, f"Expected ~17.45 mm, got {val}"


def test_build_field_mapping_report_schema():
    columns = ["timestamp", "temperature_c", "vibration_rms"]
    alias_map = {"temperature_c": "joint_temp_C", "vibration_rms": "imu_vibration_g"}
    report = build_field_mapping_report(columns, alias_map, case_id="case_test_001")
    assert report["schema"] == "hal.yieldos.robot.field_mapping_report.v1"
    assert report["field_mapping_required"] is True
    assert len(report["alias_mappings"]) == 2
    assert report["safety_boundary"]["hardware_execution_enabled"] is False
    assert report["safety_boundary"]["human_review_required"] is True


def test_build_field_mapping_report_no_aliases():
    columns = ["motor_current_A", "joint_temp_C"]
    alias_map: dict = {}
    report = build_field_mapping_report(columns, alias_map, case_id="case_test_002")
    assert report["field_mapping_required"] is False
    assert report["alias_mappings"] == []
    assert set(report["passthrough_columns"]) == {"motor_current_A", "joint_temp_C"}
