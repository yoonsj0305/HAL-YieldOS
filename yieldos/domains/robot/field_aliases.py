"""Robot field alias mapping module.

Maps non-canonical field names from external robot log formats to the
canonical YieldOS field names expected by RobotAnalyzer. No hardware
control. Read-only evidence layer.
"""
from __future__ import annotations

# Canonical field → list of accepted alias names
FIELD_ALIASES: dict[str, list[str]] = {
    "motor_current_A": [
        "current_a", "motor_current", "current_amp", "motor_current_amp",
        "current_ma_x0.001",
    ],
    "joint_temp_C": [
        "temperature_c", "temp_celsius", "joint_temperature_c",
        "joint_temp", "temperature",
    ],
    "imu_vibration_g": [
        "vibration_rms", "vibration_g", "vibration",
        "vibration_ms2_x0.101972", "vibration_rms_g",
    ],
    "position_error_mm": [
        "position_error_deg", "pos_error_mm", "joint_position_error_mm",
        "pos_err_mm", "position_error",
    ],
    "latency_ms": [
        "latency", "control_latency_ms", "response_time_ms",
        "controller_latency_ms",
    ],
    "controller_fault_code": [
        "fault_code", "error_code", "fault", "fault_flag",
    ],
    "error_count": [
        "errors", "fault_count", "error_total", "error_cnt",
    ],
}

# Unit conversion factors: {canonical_field: {alias_name: factor}}
# Applied as: canonical_value = alias_value * factor
UNIT_CONVERSIONS: dict[str, dict[str, float]] = {
    "position_error_mm": {
        "position_error_deg": 17.4533,
    },
    "imu_vibration_g": {
        "vibration_ms2_x0.101972": 0.101972,
    },
    "motor_current_A": {
        "current_ma_x0.001": 0.001,
    },
}


def detect_aliases(columns: list[str]) -> dict[str, str]:
    """Detect which input columns need alias remapping.

    Returns: {input_column → canonical_column} for non-canonical columns only.
    Canonical columns that are already correct pass through untouched.
    """
    alias_reverse: dict[str, str] = {}
    for canonical, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            alias_reverse[alias] = canonical

    detected: dict[str, str] = {}
    canonical_set = set(FIELD_ALIASES.keys())
    for col in columns:
        if col not in canonical_set and col in alias_reverse:
            detected[col] = alias_reverse[col]
    return detected


def apply_aliases(rows: list[dict], alias_map: dict[str, str]) -> list[dict]:
    """Apply alias renaming to a list of CSV row dicts.

    Renames non-canonical column names to canonical names and applies
    any registered unit conversions. Canonical columns pass through unchanged.
    """
    if not alias_map:
        return rows

    result = []
    for row in rows:
        new_row: dict[str, str] = {}
        for k, v in row.items():
            canonical = alias_map.get(k, k)
            conv_factor = UNIT_CONVERSIONS.get(canonical, {}).get(k)
            if conv_factor is not None and v not in (None, ""):
                try:
                    v = str(round(float(v) * conv_factor, 6))
                except (TypeError, ValueError):
                    pass
            new_row[canonical] = v
        result.append(new_row)
    return result


def build_field_mapping_report(
    columns: list[str],
    alias_map: dict[str, str],
    case_id: str,
) -> dict:
    """Build the robot_field_mapping_report.json payload."""
    mappings = []
    for input_col, canonical_col in alias_map.items():
        conv_factor = UNIT_CONVERSIONS.get(canonical_col, {}).get(input_col)
        mappings.append({
            "input_field": input_col,
            "canonical_field": canonical_col,
            "unit_conversion_applied": conv_factor is not None,
            "conversion_factor": conv_factor,
            "claim_boundary": "field_mapping_is_structural_not_semantic_equivalence",
        })

    passthrough = [c for c in columns if c not in alias_map]

    return {
        "schema": "hal.yieldos.robot.field_mapping_report.v1",
        "case_id": case_id,
        "domain": "robot",
        "field_mapping_required": bool(alias_map),
        "input_columns": list(columns),
        "alias_mappings": mappings,
        "passthrough_columns": passthrough,
        "canonical_target_fields": list(FIELD_ALIASES.keys()),
        "claim_boundary": "field_mapping_is_structural_not_semantic_equivalence",
        "safety_boundary": {
            "hardware_execution_enabled": False,
            "human_review_required": True,
            "candidate_only": True,
        },
    }
