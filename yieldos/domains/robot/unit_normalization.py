"""Robot unit normalization preview module.

Checks observed value ranges for canonical robot telemetry columns
against typical operating ranges to detect potential unit mismatches.
No hardware control. Read-only evidence layer. Results are heuristic only.
"""
from __future__ import annotations

from typing import Any

# {canonical_field: spec_dict}
UNIT_SPECS: dict[str, dict[str, Any]] = {
    "motor_current_A": {
        "canonical_unit": "A",
        "description": "Motor current in Amperes",
        "accepted_inputs": ["A", "mA"],
        "conversion_notes": {"mA": "divide by 1000 to convert to A"},
        "typical_range": [0.0, 30.0],
    },
    "joint_temp_C": {
        "canonical_unit": "deg_C",
        "description": "Joint temperature in Celsius",
        "accepted_inputs": ["deg_C", "K", "deg_F"],
        "conversion_notes": {"K": "subtract 273.15", "deg_F": "(x-32)*5/9"},
        "typical_range": [15.0, 90.0],
    },
    "imu_vibration_g": {
        "canonical_unit": "g",
        "description": "IMU vibration in g-force",
        "accepted_inputs": ["g", "m/s^2"],
        "conversion_notes": {"m/s^2": "divide by 9.80665"},
        "typical_range": [0.0, 2.0],
    },
    "position_error_mm": {
        "canonical_unit": "mm",
        "description": "Position error in millimeters",
        "accepted_inputs": ["mm", "deg", "m", "um"],
        "conversion_notes": {
            "deg": "multiply by 17.4533 (assumes 1m arm length)",
            "m": "multiply by 1000",
            "um": "divide by 1000",
        },
        "typical_range": [0.0, 10.0],
    },
    "latency_ms": {
        "canonical_unit": "ms",
        "description": "Controller latency in milliseconds",
        "accepted_inputs": ["ms", "s", "us"],
        "conversion_notes": {"s": "multiply by 1000", "us": "divide by 1000"},
        "typical_range": [0.0, 100.0],
    },
    "force_sensor_N": {
        "canonical_unit": "N",
        "description": "Force sensor reading in Newtons",
        "accepted_inputs": ["N", "kN", "lbf"],
        "conversion_notes": {"kN": "multiply by 1000", "lbf": "multiply by 4.44822"},
        "typical_range": [0.0, 600.0],
    },
    "gripper_force_N": {
        "canonical_unit": "N",
        "description": "Gripper force in Newtons",
        "accepted_inputs": ["N", "kgf"],
        "conversion_notes": {"kgf": "multiply by 9.80665"},
        "typical_range": [0.0, 120.0],
    },
    "payload_kg": {
        "canonical_unit": "kg",
        "description": "Payload mass in kilograms",
        "accepted_inputs": ["kg", "lb", "g"],
        "conversion_notes": {"lb": "multiply by 0.453592", "g": "divide by 1000"},
        "typical_range": [0.0, 60.0],
    },
}


def check_column_units(columns: list[str], rows: list[dict]) -> list[dict]:
    """Check observed value ranges for each known canonical column.

    Returns one result dict per known column that is present in columns.
    Status is LIKELY_CORRECT when values fall within typical_range * 2,
    else POSSIBLE_UNIT_MISMATCH.
    """
    results = []
    for col, spec in UNIT_SPECS.items():
        if col not in columns:
            continue
        vals: list[float] = []
        for row in rows:
            v = row.get(col)
            if v not in (None, ""):
                try:
                    vals.append(float(v))
                except (TypeError, ValueError):
                    pass
        if not vals:
            results.append({
                "field": col,
                "canonical_unit": spec["canonical_unit"],
                "status": "NO_DATA",
                "note": "No numeric values found in column",
                "typical_range": spec["typical_range"],
            })
            continue

        min_v, max_v = min(vals), max(vals)
        lo, hi = spec["typical_range"]
        in_range = min_v >= lo and max_v <= hi * 2
        results.append({
            "field": col,
            "canonical_unit": spec["canonical_unit"],
            "observed_min": round(min_v, 4),
            "observed_max": round(max_v, 4),
            "typical_range": spec["typical_range"],
            "in_typical_range": in_range,
            "status": "LIKELY_CORRECT" if in_range else "POSSIBLE_UNIT_MISMATCH",
            "accepted_inputs": spec["accepted_inputs"],
            "note": (
                ""
                if in_range
                else (
                    f"Values outside typical range {spec['typical_range']} "
                    f"- verify unit is {spec['canonical_unit']}"
                )
            ),
        })
    return results


def build_unit_normalization_report(
    columns: list[str],
    rows: list[dict],
    case_id: str,
    alias_map: dict[str, str],
) -> dict:
    """Build the robot_unit_normalization_report.json payload."""
    unit_checks = check_column_units(columns, rows)
    issues = [c for c in unit_checks if c["status"] == "POSSIBLE_UNIT_MISMATCH"]
    no_data = [c for c in unit_checks if c["status"] == "NO_DATA"]

    return {
        "schema": "hal.yieldos.robot.unit_normalization_report.v1",
        "case_id": case_id,
        "domain": "robot",
        "unit_normalization_preview": True,
        "columns_checked": len(unit_checks),
        "unit_issues_detected": len(issues),
        "no_data_columns": [c["field"] for c in no_data],
        "unit_checks": unit_checks,
        "alias_conversions_applied": [
            {"input_field": k, "canonical_field": v}
            for k, v in alias_map.items()
        ],
        "claim_boundary": "unit_check_is_heuristic_not_calibrated_measurement",
        "safety_boundary": {
            "hardware_execution_enabled": False,
            "human_review_required": True,
            "candidate_only": True,
        },
    }
