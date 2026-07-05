"""Semiconductor unit normalization preview for pilot-pack."""
from __future__ import annotations

CANONICAL_UNITS: dict[str, str] = {
    "rf_power_W": "W",
    "pressure_mTorr": "mTorr",
    "gas_flow_sccm": "sccm",
    "temperature_C": "C",
    "leakage_nA": "nA",
    "voltage_V": "V",
    "current_mA": "mA",
    "frequency_MHz": "MHz",
    "process_duration_s": "s",
}

SAFE_CONVERSIONS: dict[str, dict[str, float]] = {
    "pressure_mTorr": {"torr": 1000.0, "mtorr": 1.0},
    "rf_power_W": {"kw": 1000.0, "mw": 0.001, "w": 1.0},
    "temperature_C": {"celsius": 1.0, "c": 1.0},
    "leakage_nA": {"na": 1.0, "ua": 1000.0},
    "current_mA": {"ma": 1.0, "a": 1000.0},
    "frequency_MHz": {"mhz": 1.0, "khz": 0.001, "hz": 0.000001},
    "process_duration_s": {"s": 1.0, "ms": 0.001},
}

TYPICAL_RANGES: dict[str, tuple[float, float]] = {
    "rf_power_W": (100.0, 1000.0),
    "pressure_mTorr": (1.0, 100.0),
    "gas_flow_sccm": (10.0, 500.0),
    "temperature_C": (15.0, 500.0),
    "leakage_nA": (0.1, 500.0),
    "voltage_V": (0.5, 2.0),
    "current_mA": (1.0, 200.0),
    "frequency_MHz": (100.0, 5000.0),
    "process_duration_s": (10.0, 7200.0),
}


def check_column_units(
    columns: list[str], rows: list[dict]
) -> list[dict]:
    results = []
    for field, canonical_unit in CANONICAL_UNITS.items():
        if field not in columns:
            continue
        vals = []
        for row in rows:
            raw = row.get(field, "")
            try:
                vals.append(float(raw))
            except (ValueError, TypeError):
                pass
        obs_min = min(vals) if vals else None
        obs_max = max(vals) if vals else None
        low, high = TYPICAL_RANGES.get(field, (None, None))
        if obs_min is None:
            status = "no_numeric_values"
        elif low is not None and (obs_min < low * 0.01 or obs_max > high * 100):
            status = "possible_unit_mismatch"
        else:
            status = "within_typical_range"
        results.append({
            "field": field,
            "canonical_unit": canonical_unit,
            "status": status,
            "observed_min": obs_min,
            "observed_max": obs_max,
            "typical_range": [low, high] if low is not None else None,
        })
    return results


def build_unit_normalization_report(
    columns: list[str],
    rows: list[dict],
    case_id: str,
    alias_map: dict[str, str] | None = None,
) -> dict:
    checks = check_column_units(columns, rows)
    normalized = [c for c in checks if c["status"] == "within_typical_range"]
    warnings = [c for c in checks if c["status"] == "possible_unit_mismatch"]
    unresolved = [c for c in checks if c["status"] == "no_numeric_values"]
    return {
        "schema": "hal.yieldos.semiconductor.unit_normalization_report.v1",
        "case_id": case_id,
        "domain": "semiconductor",
        "normalized_fields": normalized,
        "unit_warnings": warnings,
        "unresolved_units": unresolved,
        "aliases_applied": alias_map or {},
        "human_review_required": True,
        "hardware_control_enabled": False,
        "claim_boundary": "unit_normalization_preview_not_metrology_certification",
    }
