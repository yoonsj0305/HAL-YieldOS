"""
Satellite telemetry synthetic data generator.
Simulates 10-day orbital operation with battery degradation and fault injection.

Orbital period: ~96 min (LEO). Panel current oscillates sunlit/eclipse.
Battery degrades from row 320 onward; fault_flag from row 430.
"""
from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

ORBITAL_PERIOD_MIN = 96.0   # LEO orbit period in minutes
ECLIPSE_FRACTION  = 0.38    # fraction of orbit in eclipse


def _panel_current(t_min: float, rng: random.Random, degradation: float = 0.0) -> float:
    """Simulate solar panel current: high in sunlight, near-zero in eclipse."""
    phase = (t_min % ORBITAL_PERIOD_MIN) / ORBITAL_PERIOD_MIN
    # eclipse: phase in [0.31, 0.69]
    in_eclipse = 0.31 <= phase <= 0.69
    if in_eclipse:
        return max(0.0, rng.gauss(0.06, 0.02))
    healthy = 2.10 * (1.0 - degradation * 0.4)
    return max(0.0, rng.gauss(healthy, 0.08))


def generate_satellite_telemetry(
    out_dir: str,
    n_samples: int = 500,
    asset_id: str = "cubesat_01",
    degradation_start: int = 320,
    fault_start: int = 430,
    seed: int = 17,
) -> dict:
    rng = random.Random(seed)
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    t0 = datetime(2026, 6, 1, 0, 0, 0)
    interval = timedelta(minutes=30)  # 30-min telemetry beacon

    battery_soc = 88.0  # start healthy
    rows = []

    for i in range(n_samples):
        ts = t0 + interval * i
        t_min = i * 30.0

        # Degradation ramps from 0→1 after degradation_start
        deg_phase = max(0.0, (i - degradation_start) / max(n_samples - degradation_start, 1))

        panel_cur = _panel_current(t_min, rng, degradation=deg_phase)
        payload_cur = max(0.0, rng.gauss(0.45, 0.02))

        # Battery model: charge when panel > load, discharge otherwise
        bus_load = payload_cur + 0.30  # platform baseline
        net_current = panel_cur - bus_load
        capacity_ah = max(5.0, 8.0 * (1.0 - deg_phase * 0.5))  # capacity shrinks with age
        delta_soc = (net_current * 0.5) / capacity_ah * 100.0  # 30-min step
        battery_soc = max(3.0, min(100.0, battery_soc + delta_soc))

        # Bus voltage tracks SOC
        bus_voltage = 20.0 + battery_soc * 0.04 + rng.gauss(0, 0.05)
        bus_voltage = max(19.0, min(29.0, bus_voltage))

        # Thermal: warm when sunlit, cool in eclipse
        is_eclipse = 0.31 <= ((t_min % ORBITAL_PERIOD_MIN) / ORBITAL_PERIOD_MIN) <= 0.69
        temp_base = 15.0 if is_eclipse else 28.0
        temperature = temp_base + deg_phase * 5.0 + rng.gauss(0, 1.5)

        # Attitude error: grows with degradation (gyro drift accumulates)
        attitude_error = max(0.0, 0.10 + deg_phase * 0.90 + rng.gauss(0, 0.03))

        # Comms SNR: degrades slightly with attitude error
        snr = max(2.0, 22.0 - attitude_error * 8.0 + rng.gauss(0, 0.8))

        # Gyro drift
        gyro_drift = max(0.0, 0.008 + deg_phase * 0.050 + rng.gauss(0, 0.002))

        fault_flag = 1 if i >= fault_start else 0

        rows.append({
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
            "battery_soc_pct": round(battery_soc, 2),
            "bus_voltage_V": round(bus_voltage, 2),
            "panel_current_A": round(panel_cur, 3),
            "temperature_C": round(temperature, 2),
            "attitude_error_deg": round(attitude_error, 3),
            "comms_snr_dB": round(snr, 2),
            "fault_flag": fault_flag,
            "payload_current_A": round(payload_cur, 3),
            "gyro_drift_deg_s": round(gyro_drift, 4),
        })

    out_path = Path(out_dir) / "satellite_telemetry.csv"
    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return {
        "rows": len(rows),
        "asset_id": asset_id,
        "degradation_start": degradation_start,
        "fault_start": fault_start,
        "out_path": str(out_path),
        "data_dir": out_dir,
    }


def generate_all(
    out_dir: str,
    n_samples: int = 500,
    seed: int = 17,
) -> dict:
    return generate_satellite_telemetry(
        out_dir=out_dir,
        n_samples=n_samples,
        degradation_start=int(n_samples * 0.64),
        fault_start=int(n_samples * 0.86),
        seed=seed,
    )


def generate_all_with_fault(
    out_dir: str,
    n_samples: int = 1000,
    fault: str = "none",
    seed: int = 17,
) -> dict:
    """Generate synthetic satellite telemetry with a specific fault type.

    fault options:
      none, power_margin_drop, thermal_rise,
      attitude_error_growth, comms_snr_drop, fault_flag_event
    """
    FAULT_CONFIG = {
        "none":                 {"deg_ratio": 0.99, "fault_ratio": 0.99},
        "power_margin_drop":    {"deg_ratio": 0.50, "fault_ratio": 0.80},
        "thermal_rise":         {"deg_ratio": 0.45, "fault_ratio": 0.78},
        "attitude_error_growth":{"deg_ratio": 0.55, "fault_ratio": 0.82},
        "comms_snr_drop":       {"deg_ratio": 0.60, "fault_ratio": 0.85},
        "fault_flag_event":     {"deg_ratio": 0.65, "fault_ratio": 0.70},
    }
    if fault not in FAULT_CONFIG:
        fault = "none"
    fc = FAULT_CONFIG[fault]
    info = generate_satellite_telemetry(
        out_dir=out_dir,
        n_samples=n_samples,
        degradation_start=int(n_samples * fc["deg_ratio"]),
        fault_start=int(n_samples * fc["fault_ratio"]),
        seed=seed,
    )
    info["fault"] = fault
    return info
