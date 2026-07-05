"""
Synthetic SemFab dataset generator.
Produces realistic TEL-like logs with injected drift events.
"""
from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def generate_tool_log(
    path: str,
    n_lots: int = 10,
    wafers_per_lot: int = 5,
    steps: int = 5,
    drift_step: int = 4,         # STEP_0X where drift is injected (1-indexed)
    drift_start_lot: int = 6,    # which lot index drift begins
    drift_magnitude: float = 0.04,
    seed: int = 42,
) -> list:
    """Generate 1000+ row tool log with realistic drift in one step."""
    rng = random.Random(seed)
    rows = []
    t = datetime(2026, 6, 9, 6, 0, 0, tzinfo=timezone.utc)

    # baseline parameter distributions
    PARAMS = {
        "rf_power_W":      (450.0, 2.0),
        "pressure_mTorr":  (32.5,  0.5),
        "gas_flow_sccm":   (85.0,  0.8),
        "temperature_C":   (20.0,  0.3),
        "endpoint_signal": (0.810, 0.005),
    }

    for lot_idx in range(1, n_lots + 1):
        lot_id = f"L{1020 + lot_idx:04d}"
        for w_idx in range(1, wafers_per_lot + 1):
            wafer_id = f"W{(lot_idx - 1) * wafers_per_lot + w_idx:03d}"
            for step_idx in range(1, steps + 1):
                step_name = f"STEP_{step_idx:02d}"
                # inject drift in drift_step from drift_start_lot onward
                drifting = (step_idx == drift_step and lot_idx >= drift_start_lot)
                drift_factor = drift_magnitude * (lot_idx - drift_start_lot + 1) if drifting else 0.0

                row = {
                    "timestamp": _iso(t),
                    "lot_id": lot_id,
                    "wafer_id": wafer_id,
                    "process_step": step_name,
                    "recipe_id": "R_ETCH_STD",
                }
                for param, (base, sigma) in PARAMS.items():
                    noise = rng.gauss(0, sigma)
                    # drift: rf_power goes up, endpoint signal goes down
                    if drifting and param == "rf_power_W":
                        val = base * (1 + drift_factor) + noise
                    elif drifting and param == "endpoint_signal":
                        val = base * (1 - drift_factor * 0.5) + noise * 0.1
                    elif drifting and param == "pressure_mTorr":
                        val = base * (1 + drift_factor * 0.5) + noise
                    else:
                        val = base + noise
                    row[param] = round(val, 4)

                rows.append(row)
                t += timedelta(minutes=2)

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return rows


def generate_wafer_map(
    path: str,
    n_lots: int = 10,
    wafers_per_lot: int = 5,
    die_rows: int = 5,
    die_cols: int = 5,
    drift_start_lot: int = 6,
    seed: int = 42,
) -> None:
    """Wafer map with increasing edge-concentrated fails after drift starts."""
    rng = random.Random(seed)
    rows = []
    for lot_idx in range(1, n_lots + 1):
        lot_id = f"L{1020 + lot_idx:04d}"
        base_fail_rate = 0.02 + (max(0, lot_idx - drift_start_lot) * 0.03)
        for w_idx in range(1, wafers_per_lot + 1):
            wafer_id = f"W{(lot_idx - 1) * wafers_per_lot + w_idx:03d}"
            for dr in range(die_rows):
                for dc in range(die_cols):
                    # edge dies fail more when drifting
                    edge = (dr in (0, die_rows - 1) or dc in (0, die_cols - 1))
                    fail_p = base_fail_rate * (2.5 if (edge and lot_idx >= drift_start_lot) else 1.0)
                    fail = rng.random() < fail_p
                    rows.append({
                        "wafer_id": wafer_id,
                        "lot_id": lot_id,
                        "die_row": dr,
                        "die_col": dc,
                        "bin_result": "FAIL" if fail else "PASS",
                        "bin_code": rng.choice([3, 4, 5]) if fail else 1,
                    })

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def generate_metrology(
    path: str,
    n_lots: int = 10,
    wafers_per_lot: int = 5,
    target_cd: float = 65.0,
    drift_start_lot: int = 6,
    seed: int = 42,
) -> None:
    rng = random.Random(seed)
    sites = ["CENTER", "N", "S", "E", "W"]
    rows = []
    for lot_idx in range(1, n_lots + 1):
        lot_id = f"L{1020 + lot_idx:04d}"
        cd_offset = max(0, lot_idx - drift_start_lot) * 0.8  # growing CD shift
        for w_idx in range(1, wafers_per_lot + 1):
            wafer_id = f"W{(lot_idx - 1) * wafers_per_lot + w_idx:03d}"
            for site in sites:
                rows.append({
                    "wafer_id": wafer_id,
                    "lot_id": lot_id,
                    "site": site,
                    "target_cd_nm": target_cd,
                    "cd_nm": round(target_cd + cd_offset + rng.gauss(0, 0.3), 2),
                    "thickness_nm": round(120.0 + rng.gauss(0, 0.5), 2),
                    "uniformity_pct": round(abs(rng.gauss(1.5, 0.4)), 2),
                })
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def generate_lot_genealogy(path: str, n_lots: int = 10) -> None:
    rows = []
    t0 = datetime(2026, 6, 9, 0, 0, 0, tzinfo=timezone.utc)
    for i in range(1, n_lots + 1):
        rows.append({
            "lot_id": f"L{1020 + i:04d}",
            "parent_lot_id": f"L{1010 + i:04d}",
            "product_id": "PROD_A",
            "recipe_id": "R_ETCH_STD",
            "start_time": _iso(t0 + timedelta(hours=i * 2)),
            "wafer_count": 5,
            "priority": "normal",
        })
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def generate_all_with_fault(
    data_dir: str,
    n_rows: int = 1000,
    fault: str = "none",
    seed: int = 42,
) -> dict:
    """Generate synthetic SemFab dataset with a specific fault type injected.

    fault options:
      none, chamber_drift, incoming_wafer_variation,
      recipe_step_instability, metrology_shift, yield_drop
    """
    FAULT_PARAMS = {
        "none":                       {"drift_magnitude": 0.0,  "drift_start_lot": 999, "drift_step": 4},
        "chamber_drift":              {"drift_magnitude": 0.06, "drift_start_lot": 5,   "drift_step": 4},
        "incoming_wafer_variation":   {"drift_magnitude": 0.04, "drift_start_lot": 4,   "drift_step": 1},
        "recipe_step_instability":    {"drift_magnitude": 0.05, "drift_start_lot": 3,   "drift_step": 3},
        "metrology_shift":            {"drift_magnitude": 0.03, "drift_start_lot": 6,   "drift_step": 2},
        "yield_drop":                 {"drift_magnitude": 0.08, "drift_start_lot": 4,   "drift_step": 4},
    }
    if fault not in FAULT_PARAMS:
        fault = "none"
    fp = FAULT_PARAMS[fault]

    # Estimate lot count from rows target
    wafers_per_lot = 5
    steps = 5
    rows_per_lot = wafers_per_lot * steps
    n_lots = max(10, n_rows // rows_per_lot)
    drift_start_lot = fp["drift_start_lot"]

    base = Path(data_dir)
    generate_tool_log(
        str(base / "tool_log.csv"), n_lots, wafers_per_lot,
        drift_step=fp["drift_step"],
        drift_start_lot=drift_start_lot,
        drift_magnitude=fp["drift_magnitude"],
        seed=seed,
    )
    generate_wafer_map(str(base / "wafer_map.csv"), n_lots, wafers_per_lot,
                       drift_start_lot=drift_start_lot, seed=seed)
    generate_metrology(str(base / "metrology.csv"), n_lots, wafers_per_lot,
                       drift_start_lot=drift_start_lot, seed=seed)
    generate_lot_genealogy(str(base / "lot_genealogy.csv"), n_lots)
    with open(str(base / "test_result.csv"), "w", newline="", encoding="utf-8") as f:
        f.write("wafer_id,lot_id,die_id,test_site,parametric_bin,leakage_nA,idsat_mA,vth_mV,pass_fail\n")

    total = n_lots * wafers_per_lot * steps
    return {
        "tool_log_rows": total,
        "lots": n_lots,
        "wafers": n_lots * wafers_per_lot,
        "fault": fault,
        "data_dir": str(base),
    }


def generate_all(data_dir: str, n_lots: int = 10, wafers_per_lot: int = 5) -> dict:
    """Generate full synthetic SemFab dataset."""
    base = Path(data_dir)
    generate_tool_log(str(base / "tool_log.csv"), n_lots, wafers_per_lot)
    generate_wafer_map(str(base / "wafer_map.csv"), n_lots, wafers_per_lot)
    generate_metrology(str(base / "metrology.csv"), n_lots, wafers_per_lot)
    generate_lot_genealogy(str(base / "lot_genealogy.csv"), n_lots)
    # Empty test_result placeholder
    with open(str(base / "test_result.csv"), "w", newline="", encoding="utf-8") as f:
        f.write("wafer_id,lot_id,die_id,test_site,parametric_bin,leakage_nA,idsat_mA,vth_mV,pass_fail\n")
    total = n_lots * wafers_per_lot * 5  # steps per wafer
    return {
        "tool_log_rows": total,
        "lots": n_lots,
        "wafers": n_lots * wafers_per_lot,
        "data_dir": str(base),
    }
