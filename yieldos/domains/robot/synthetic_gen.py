"""
Robot telemetry synthetic data generator.
Produces 500+ rows with gradual mechanical degradation and fault injection.
"""
from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_robot_telemetry(
    out_dir: str,
    n_samples: int = 500,
    joint_id: str = "J3",
    degradation_start: int = 300,
    fault_start: int = 420,
    seed: int = 42,
) -> dict:
    """
    Generate synthetic robot telemetry with degradation.

    Phases:
      0 .. degradation_start-1  : nominal (small noise)
      degradation_start .. fault_start-1 : gradual wear (rising trend)
      fault_start .. end        : fault active (controller_fault_code=201)
    """
    rng = random.Random(seed)
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    t0 = datetime(2026, 6, 1, 6, 0, 0)
    interval = timedelta(minutes=5)

    rows = []
    for i in range(n_samples):
        ts = t0 + interval * i
        phase = (i - degradation_start) / max(n_samples - degradation_start, 1)
        wear = max(0.0, phase)  # 0 → 1 over degradation phase

        # Base values
        motor_current = 3.20 + wear * 1.20
        joint_temp = 42.0 + wear * 12.0
        vibration = 0.012 + wear * 0.055
        position_error = 0.08 + wear * 0.40
        latency = 12.0 + wear * 9.0
        error_count = int(max(0, wear * 6 + rng.gauss(0, 0.3)))
        battery_voltage = max(22.0, 24.2 - wear * 1.5)
        fault_code = 201 if i >= fault_start else 0

        # Gaussian noise (small in nominal, larger in degraded)
        noise_scale = 0.01 + wear * 0.03
        motor_current += rng.gauss(0, 0.05 + noise_scale)
        joint_temp += rng.gauss(0, 0.3 + noise_scale * 5)
        vibration += rng.gauss(0, 0.001 + noise_scale * 0.005)
        position_error += rng.gauss(0, 0.005 + noise_scale * 0.02)
        latency += rng.gauss(0, 0.3 + noise_scale * 1.5)
        battery_voltage += rng.gauss(0, 0.05)

        rows.append({
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
            "joint_id": joint_id,
            "motor_current_A": round(max(0.0, motor_current), 3),
            "joint_temp_C": round(max(0.0, joint_temp), 2),
            "imu_vibration_g": round(max(0.0, vibration), 4),
            "position_error_mm": round(max(0.0, position_error), 3),
            "latency_ms": round(max(0.0, latency), 2),
            "error_count": error_count,
            "battery_voltage_V": round(battery_voltage, 2),
            "controller_fault_code": fault_code,
        })

    out_path = Path(out_dir) / "robot_telemetry.csv"
    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return {
        "rows": len(rows),
        "joint_id": joint_id,
        "degradation_start": degradation_start,
        "fault_start": fault_start,
        "out_path": str(out_path),
        "data_dir": out_dir,
    }


def generate_all(
    out_dir: str,
    n_samples: int = 500,
    seed: int = 42,
) -> dict:
    return generate_robot_telemetry(
        out_dir=out_dir,
        n_samples=n_samples,
        degradation_start=int(n_samples * 0.60),
        fault_start=int(n_samples * 0.84),
        seed=seed,
    )


def generate_all_with_fault(
    out_dir: str,
    n_samples: int = 1000,
    fault: str = "none",
    seed: int = 42,
) -> dict:
    """Generate synthetic robot telemetry with a specific fault type.

    fault options:
      none, joint_degradation, vibration_increase,
      position_error_growth, latency_spike, battery_drop
    """
    FAULT_CONFIG = {
        "none":                   {"deg_ratio": 0.99, "fault_ratio": 0.99},
        "joint_degradation":      {"deg_ratio": 0.60, "fault_ratio": 0.84},
        "vibration_increase":     {"deg_ratio": 0.50, "fault_ratio": 0.80},
        "position_error_growth":  {"deg_ratio": 0.55, "fault_ratio": 0.82},
        "latency_spike":          {"deg_ratio": 0.65, "fault_ratio": 0.88},
        "battery_drop":           {"deg_ratio": 0.70, "fault_ratio": 0.90},
    }
    if fault not in FAULT_CONFIG:
        fault = "none"
    fc = FAULT_CONFIG[fault]
    info = generate_robot_telemetry(
        out_dir=out_dir,
        n_samples=n_samples,
        degradation_start=int(n_samples * fc["deg_ratio"]),
        fault_start=int(n_samples * fc["fault_ratio"]),
        seed=seed,
    )
    info["fault"] = fault
    return info
