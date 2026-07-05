"""
Synthetic memory block health data generator for testing and demos.
Produces block_health.csv and device_info.json.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

_DEFAULT_DEVICE_INFO = {
    "device_id": "memdev_01",
    "memory_type": "nand_flash_simulated",
    "raw_capacity_gb": 128,
    "block_size_gb": 1,
    "ecc_policy": {
        "corrected_error_warning_threshold": 100,
        "uncorrectable_error_fail_threshold": 1,
    },
    "endurance_policy": {
        "pe_cycle_warning_ratio": 0.80,
        "pe_cycle_fail_ratio": 0.95,
    },
    "retention_policy": {
        "min_retention_hours": 72,
    },
}

_COLUMNS = [
    "block_id",
    "block_size_gb",
    "is_factory_bad",
    "is_runtime_bad",
    "corrected_error_count",
    "uncorrectable_error_count",
    "pe_cycles",
    "max_pe_cycles",
    "retention_hours",
    "min_retention_hours",
    "temperature_C",
    "read_count",
    "write_count",
    "last_scrub_age_hours",
]


def _gen_block(idx: int, rng_seed: int, n_blocks: int) -> dict:
    """Deterministically generate one block row given its index."""
    # Simple LCG-based pseudo-random (no random module to keep determinism simple)
    seed = (idx * 6364136223846793005 + rng_seed) & 0xFFFFFFFFFFFFFFFF
    def _rnd() -> float:
        nonlocal seed
        seed = (seed * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        return (seed >> 33) / (2**31)

    block_id = f"B{idx:04d}"
    is_factory_bad = "false"
    is_runtime_bad = "false"
    corrected = 0
    uncorrectable = 0
    pe = 0
    max_pe = 10000
    retention = 200.0
    min_ret = 72.0
    temp = 45.0

    noise = _rnd()

    if idx < int(n_blocks * 0.04):
        # factory bad blocks (~4%)
        is_factory_bad = "true"
        corrected = int(noise * 50)
    elif idx < int(n_blocks * 0.07):
        # runtime bad blocks with uncorrectable errors (~3%)
        is_runtime_bad = "true"
        uncorrectable = 1
        corrected = int(noise * 200 + 80)
        pe = int(8500 + noise * 1400)
    elif idx < int(n_blocks * 0.12):
        # high corrected error rate → approximate_cache (~5%)
        corrected = int(100 + noise * 300)
        pe = int(4000 + noise * 3000)
        retention = 80.0 + noise * 40.0
    elif idx < int(n_blocks * 0.18):
        # high PE cycles, low corrected → read_only_archive (~6%)
        pe = int(8200 + noise * 1600)
        corrected = int(noise * 30)
        retention = 150.0 + noise * 50.0
    elif idx < int(n_blocks * 0.22):
        # low retention → approximate_cache (~4%)
        retention = 20.0 + noise * 45.0  # below min 72h
        corrected = int(noise * 60)
        pe = int(3000 + noise * 2000)
    else:
        # safe blocks (~78%)
        corrected = int(noise * 50)
        pe = int(500 + noise * 3500)
        retention = 150.0 + noise * 200.0
        temp = 35.0 + noise * 25.0

    read_count = int(pe * 8 + _rnd() * 1000)
    write_count = pe
    scrub_age = round(24.0 + _rnd() * 72.0, 1)

    return {
        "block_id": block_id,
        "block_size_gb": 1,
        "is_factory_bad": is_factory_bad,
        "is_runtime_bad": is_runtime_bad,
        "corrected_error_count": corrected,
        "uncorrectable_error_count": uncorrectable,
        "pe_cycles": pe,
        "max_pe_cycles": max_pe,
        "retention_hours": round(retention, 1),
        "min_retention_hours": min_ret,
        "temperature_C": round(temp, 1),
        "read_count": read_count,
        "write_count": write_count,
        "last_scrub_age_hours": scrub_age,
    }


def generate_all(
    out_dir: str,
    n_blocks: int = 128,
    device_id: str = "memdev_01",
    seed: int = 42,
) -> dict:
    """
    Generate block_health.csv and device_info.json in out_dir.
    Returns metadata about what was generated.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    device_info = dict(_DEFAULT_DEVICE_INFO)
    device_info["device_id"] = device_id
    device_info["raw_capacity_gb"] = n_blocks  # 1 GB per block

    device_path = out / "device_info.json"
    device_path.write_text(
        json.dumps(device_info, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    rows = [_gen_block(i, seed, n_blocks) for i in range(n_blocks)]

    csv_path = out / "block_health.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    factory_bad = sum(1 for r in rows if r["is_factory_bad"] == "true")
    runtime_bad = sum(1 for r in rows if r["is_runtime_bad"] == "true")
    return {
        "blocks": n_blocks,
        "device_id": device_id,
        "block_health_csv": str(csv_path),
        "device_info_json": str(device_path),
        "factory_bad": factory_bad,
        "runtime_bad": runtime_bad,
    }
