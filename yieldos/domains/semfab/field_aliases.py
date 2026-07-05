"""Semiconductor field alias mapping for pilot-pack intake."""
from __future__ import annotations

FIELD_ALIASES: dict[str, list[str]] = {
    "timestamp": ["time", "ts", "event_time", "process_time"],
    "tool_id": ["equipment_id", "eqp_id", "tool"],
    "chamber_id": ["chamber", "module_id", "process_module"],
    "lot_id": ["lot", "batch_id", "lot_name_redacted"],
    "wafer_id": ["wafer", "substrate_id", "wafer_no"],
    "die_id": ["die", "die_key", "die_uid"],
    "die_x": ["x", "x_index", "col"],
    "die_y": ["y", "y_index", "row"],
    "step_id": ["step", "process_step", "operation_id"],
    "bin_code": ["bin", "soft_bin", "hard_bin"],
    "pass_fail": ["result", "test_result", "pf"],
    "rf_power_W": ["power_w", "rf_power", "forward_power_w"],
    "pressure_mTorr": ["pressure", "chamber_pressure", "chamber_pressure_torr"],
    "gas_flow_sccm": ["gas_flow", "flow_sccm", "mfc_flow"],
    "temperature_C": ["temp_c", "temperature", "chuck_temp_c"],
    "alarm_code": ["alarm", "fault_code", "alarm_flag"],
    "metric_name": ["parameter", "param_name", "measurement_id"],
    "metric_value": ["value", "meas_value", "measurement"],
    "unit": ["units", "meas_unit", "uom"],
}

UNIT_CONVERSIONS: dict[str, dict[str, float]] = {
    "pressure_mTorr": {
        "chamber_pressure_torr": 1000.0,
    },
    "rf_power_W": {
        "power_kw": 1000.0,
        "power_mw": 0.001,
    },
}


def detect_aliases(columns: list[str]) -> dict[str, str]:
    """Return {input_col: canonical_col} for any detected aliases."""
    result: dict[str, str] = {}
    canonical_set = set(FIELD_ALIASES.keys())
    present_canonical = {c for c in columns if c in canonical_set}
    for col in columns:
        if col in canonical_set:
            continue
        for canonical, aliases in FIELD_ALIASES.items():
            if canonical in present_canonical:
                continue
            if col in aliases:
                result[col] = canonical
                break
    return result


def apply_aliases(
    rows: list[dict], alias_map: dict[str, str]
) -> list[dict]:
    """Rename aliased columns to canonical names, applying unit conversions."""
    if not alias_map:
        return rows
    out = []
    for row in rows:
        new_row = {}
        for k, v in row.items():
            canonical = alias_map.get(k, k)
            if k in alias_map:
                src_unit_map = UNIT_CONVERSIONS.get(canonical, {})
                if k in src_unit_map:
                    try:
                        v = str(float(v) * src_unit_map[k])
                    except (ValueError, TypeError):
                        pass
            new_row[canonical] = v
        out.append(new_row)
    return out


def build_field_mapping_report(
    original_columns: list[str],
    alias_map: dict[str, str],
    case_id: str,
) -> dict:
    mapped = [
        {
            "canonical_field": v,
            "source_field": k,
            "mapping_type": "known_alias",
        }
        for k, v in alias_map.items()
    ]
    unmapped = [
        c for c in original_columns
        if c not in alias_map and c not in FIELD_ALIASES
    ]
    return {
        "schema": "hal.yieldos.semiconductor.field_mapping_report.v1",
        "case_id": case_id,
        "domain": "semiconductor",
        "mapped_fields": mapped,
        "unmapped_required_fields": [],
        "ambiguous_fields": [
            {"field": c, "note": "not in canonical list or known alias set"}
            for c in unmapped[:10]
        ],
        "human_review_required": True,
        "hardware_control_enabled": False,
        "claim_boundary": "field_mapping_for_candidate_review_only",
    }
