from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List


def load_tool_log(path: str) -> List[dict]:
    """Load TEL-like equipment log CSV."""
    p = Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def load_wafer_map(path: str) -> List[dict]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def load_metrology(path: str) -> List[dict]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def load_test_result(path: str) -> List[dict]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def load_lot_genealogy(path: str) -> List[dict]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def load_all(data_dir: str) -> Dict[str, List[dict]]:
    base = Path(data_dir)
    return {
        "tool_log": load_tool_log(str(base / "tool_log.csv")),
        "wafer_map": load_wafer_map(str(base / "wafer_map.csv")),
        "metrology": load_metrology(str(base / "metrology.csv")),
        "test_result": load_test_result(str(base / "test_result.csv")),
        "lot_genealogy": load_lot_genealogy(str(base / "lot_genealogy.csv")),
    }
