"""
tests/test_pilot_readiness_score_caps.py

Score cap semantics tests (v2.9.3).
Verifies that readiness_score and readiness_score_percent are capped
appropriately when data is insufficient or missing.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from yieldos.pilot.readiness import (
    STATUS_NOT_READY,
    STATUS_READY,
    run_pilot_check,
)

SAMPLES_ROOT = Path(__file__).parent.parent / "samples"


def _write_csv(path: Path, rows: int, columns: list) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for i in range(rows):
            writer.writerow({c: f"v{i}" for c in columns})


def _read_report(out: Path) -> dict:
    return json.loads((out / "pilot_readiness_report.json").read_text(encoding="utf-8"))


# ── Cap 1: below minimum viable rows → score < 1.0 ────────────────────────────

def test_below_mvr_score_below_1(tmp_path):
    from yieldos.pilot.domain_contracts import DomainContracts
    contract = DomainContracts.get("semiconductor")
    req = contract.required_fields
    if all(f.minimum_viable_rows <= 1 for f in req):
        pytest.skip("no field with minimum_viable_rows > 1")

    input_dir = tmp_path / "fewrows"
    input_dir.mkdir()
    out = tmp_path / "out"
    for f in req:
        rows = max(0, f.minimum_viable_rows - 1)
        if f.format == "csv" and f.columns:
            _write_csv(input_dir / f.name, rows=rows, columns=f.columns)
        elif f.format == "json":
            (input_dir / f.name).write_text(
                json.dumps({k: "val" for k in (f.json_keys or [])}),
                encoding="utf-8",
            )
        else:
            (input_dir / f.name).write_text("dummy", encoding="utf-8")

    run_pilot_check(domain="semiconductor", input_dir=input_dir, out_dir=out)
    report = _read_report(out)
    assert report["readiness_score"] < 1.0, "Score must be < 1.0 when MVR fails"
    assert report["readiness_score_percent"] < 100.0


def test_below_mvr_status_not_ready(tmp_path):
    from yieldos.pilot.domain_contracts import DomainContracts
    contract = DomainContracts.get("semiconductor")
    req = contract.required_fields
    if all(f.minimum_viable_rows <= 1 for f in req):
        pytest.skip("no field with minimum_viable_rows > 1")

    input_dir = tmp_path / "fewrows2"
    input_dir.mkdir()
    out = tmp_path / "out"
    for f in req:
        rows = max(0, f.minimum_viable_rows - 1)
        if f.format == "csv" and f.columns:
            _write_csv(input_dir / f.name, rows=rows, columns=f.columns)
        elif f.format == "json":
            (input_dir / f.name).write_text(
                json.dumps({k: "val" for k in (f.json_keys or [])}),
                encoding="utf-8",
            )
        else:
            (input_dir / f.name).write_text("dummy", encoding="utf-8")

    run_pilot_check(domain="semiconductor", input_dir=input_dir, out_dir=out)
    report = _read_report(out)
    assert report["readiness_status"] != STATUS_READY


# ── Cap 2: missing required file → score ≤ 0.70 ───────────────────────────────

def test_missing_required_file_score_capped_at_070(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    report = _read_report(out)
    assert report["readiness_score"] <= 0.70, (
        f"Score must be ≤ 0.70 when required file missing, got {report['readiness_score']}"
    )
    assert report["readiness_score_percent"] <= 70.0


def test_missing_required_file_score_percent_capped(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    report = _read_report(out)
    assert report["readiness_score_percent"] <= 70.0
    assert report["readiness_status"] == STATUS_NOT_READY


# ── Cap 3: missing required identifier/column → score ≤ 0.60 ─────────────────

def test_missing_required_column_score_capped_at_060(tmp_path):
    from yieldos.pilot.domain_contracts import DomainContracts
    contract = DomainContracts.get("robot")
    req = contract.required_fields
    csv_fields = [f for f in req if f.format == "csv" and f.columns and len(f.columns) > 1]
    if not csv_fields:
        pytest.skip("robot has no multi-column required CSV fields")

    input_dir = tmp_path / "badcols"
    input_dir.mkdir()
    out = tmp_path / "out"
    for f in req:
        if f.format == "csv" and f.columns:
            # Write with only first column — all identifier columns missing
            _write_csv(input_dir / f.name, rows=f.minimum_viable_rows + 5, columns=f.columns[:1])
        elif f.format == "json":
            (input_dir / f.name).write_text("{}", encoding="utf-8")
        else:
            (input_dir / f.name).write_text("dummy", encoding="utf-8")

    run_pilot_check(domain="robot", input_dir=input_dir, out_dir=out)
    report = _read_report(out)
    assert report["readiness_score"] <= 0.60, (
        f"Score must be ≤ 0.60 when required columns missing, got {report['readiness_score']}"
    )
    assert report["readiness_score_percent"] <= 60.0


def test_missing_required_column_status_not_ready(tmp_path):
    from yieldos.pilot.domain_contracts import DomainContracts
    contract = DomainContracts.get("robot")
    req = contract.required_fields
    csv_fields = [f for f in req if f.format == "csv" and f.columns and len(f.columns) > 1]
    if not csv_fields:
        pytest.skip("robot has no multi-column required CSV fields")

    input_dir = tmp_path / "badcols2"
    input_dir.mkdir()
    out = tmp_path / "out"
    for f in req:
        if f.format == "csv" and f.columns:
            _write_csv(input_dir / f.name, rows=f.minimum_viable_rows + 5, columns=f.columns[:1])
        elif f.format == "json":
            (input_dir / f.name).write_text("{}", encoding="utf-8")
        else:
            (input_dir / f.name).write_text("dummy", encoding="utf-8")

    run_pilot_check(domain="robot", input_dir=input_dir, out_dir=out)
    report = _read_report(out)
    assert report["readiness_status"] != STATUS_READY


# ── Score percent invariant under all cap scenarios ───────────────────────────

def test_score_percent_invariant_under_caps(tmp_path):
    """readiness_score_percent == round(readiness_score * 100, 2) always holds."""
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    report = _read_report(out)
    score = report["readiness_score"]
    percent = report["readiness_score_percent"]
    expected = round(score * 100, 2)
    assert percent == expected, f"Invariant broken: {percent} != {expected}"


def test_score_percent_invariant_sample(tmp_path):
    """Invariant holds for READY sample data."""
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=SAMPLES_ROOT / "pilot_robot", out_dir=out)
    report = _read_report(out)
    score = report["readiness_score"]
    percent = report["readiness_score_percent"]
    assert percent == round(score * 100, 2)
