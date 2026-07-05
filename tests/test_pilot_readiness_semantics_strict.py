"""
tests/test_pilot_readiness_semantics_strict.py

Strict readiness semantics tests (v2.9.2).
Verifies score caps, status transitions, and canonical structured fields.
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


def _write_csv(path: Path, rows: int, columns: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for i in range(rows):
            writer.writerow({c: f"v{i}" for c in columns})


def _read_report(out: Path) -> dict:
    return json.loads((out / "pilot_readiness_report.json").read_text(encoding="utf-8"))


def _read_mdr(out: Path) -> dict:
    return json.loads((out / "missing_data_request.json").read_text(encoding="utf-8"))


# ── Case 1: sample data passes minimum viable rows → READY ───────────────────

def test_sample_data_passes_mvr_and_is_ready(tmp_path):
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=SAMPLES_ROOT / "pilot_robot", out_dir=out)
    report = _read_report(out)
    assert report["readiness_status"] == STATUS_READY
    mvr = report["minimum_viable_rows_check"]
    assert isinstance(mvr["passed"], list)
    assert len(mvr["passed"]) >= 1, "READY report must have at least 1 MVR passed entry"


def test_sample_score_is_maximum_when_ready(tmp_path):
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=SAMPLES_ROOT / "pilot_robot", out_dir=out)
    report = _read_report(out)
    if report["readiness_status"] == STATUS_READY:
        assert report["readiness_score"] >= 0.8, "READY score should be high"


# ── Case 2: below minimum viable rows → not READY + score < 1.0 + MVR failed ─

def test_below_mvr_is_not_ready(tmp_path):
    from yieldos.pilot.domain_contracts import DomainContracts
    contract = DomainContracts.get("semiconductor")
    req = contract.required_fields
    if all(f.minimum_viable_rows <= 1 for f in req):
        pytest.skip("semiconductor min viable rows <= 1, cannot test below-MVR")

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
    assert report["readiness_status"] != STATUS_READY, (
        "Files with insufficient rows must not return READY"
    )


def test_below_mvr_score_is_less_than_1(tmp_path):
    from yieldos.pilot.domain_contracts import DomainContracts
    contract = DomainContracts.get("semiconductor")
    req = contract.required_fields
    if all(f.minimum_viable_rows <= 1 for f in req):
        pytest.skip("semiconductor min viable rows <= 1, cannot test below-MVR")

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
    assert report["readiness_score"] < 1.0, "Score must be < 1.0 when MVR fail"


def test_below_mvr_check_failed_not_empty(tmp_path):
    from yieldos.pilot.domain_contracts import DomainContracts
    contract = DomainContracts.get("semiconductor")
    req = contract.required_fields
    if all(f.minimum_viable_rows <= 1 for f in req):
        pytest.skip("semiconductor min viable rows <= 1, cannot test below-MVR")

    input_dir = tmp_path / "fewrows3"
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
    mvr_failed = report["minimum_viable_rows_check"].get("failed", [])
    assert len(mvr_failed) >= 1, "minimum_viable_rows_check.failed must not be empty"


# ── Case 3: missing required file → NOT_READY + required_files_missing ────────

def test_missing_required_file_is_not_ready(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    report = _read_report(out)
    assert report["readiness_status"] == STATUS_NOT_READY


def test_missing_required_file_in_required_files_missing(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    report = _read_report(out)
    assert len(report["required_files_missing"]) >= 1, (
        "required_files_missing must list missing required files"
    )


def test_missing_required_file_in_mdr(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    mdr = _read_mdr(out)
    assert len(mdr["missing_required_files"]) >= 1, (
        "missing_data_request.missing_required_files must list absent required files"
    )


def test_missing_file_score_capped_at_040(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    report = _read_report(out)
    assert report["readiness_score"] <= 0.4, "Score must be capped at 0.4 when required file missing"


# ── Case 4: missing required column → not READY + column_check.failed ─────────

def test_missing_column_not_ready(tmp_path):
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
            _write_csv(input_dir / f.name, rows=f.minimum_viable_rows + 1, columns=f.columns[:1])
        elif f.format == "json":
            (input_dir / f.name).write_text("{}", encoding="utf-8")
        else:
            (input_dir / f.name).write_text("dummy", encoding="utf-8")

    run_pilot_check(domain="robot", input_dir=input_dir, out_dir=out)
    report = _read_report(out)
    assert report["readiness_status"] != STATUS_READY


def test_missing_column_in_column_check_failed(tmp_path):
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
            _write_csv(input_dir / f.name, rows=f.minimum_viable_rows + 1, columns=f.columns[:1])
        elif f.format == "json":
            (input_dir / f.name).write_text("{}", encoding="utf-8")
        else:
            (input_dir / f.name).write_text("dummy", encoding="utf-8")

    run_pilot_check(domain="robot", input_dir=input_dir, out_dir=out)
    report = _read_report(out)
    assert len(report["column_check"]["failed"]) >= 1, (
        "column_check.failed must not be empty when required columns are missing"
    )


def test_missing_column_in_mdr(tmp_path):
    from yieldos.pilot.domain_contracts import DomainContracts
    contract = DomainContracts.get("robot")
    req = contract.required_fields
    csv_fields = [f for f in req if f.format == "csv" and f.columns and len(f.columns) > 1]
    if not csv_fields:
        pytest.skip("robot has no multi-column required CSV fields")

    input_dir = tmp_path / "badcols3"
    input_dir.mkdir()
    out = tmp_path / "out"
    for f in req:
        if f.format == "csv" and f.columns:
            _write_csv(input_dir / f.name, rows=f.minimum_viable_rows + 1, columns=f.columns[:1])
        elif f.format == "json":
            (input_dir / f.name).write_text("{}", encoding="utf-8")
        else:
            (input_dir / f.name).write_text("dummy", encoding="utf-8")

    run_pilot_check(domain="robot", input_dir=input_dir, out_dir=out)
    mdr = _read_mdr(out)
    assert len(mdr["missing_required_columns"]) >= 1, (
        "missing_required_columns must be populated when CSV columns are absent"
    )


# ── Case 5: PARTIAL semantics ─────────────────────────────────────────────────

def test_partial_is_between_ready_and_not_ready(tmp_path):
    """PARTIAL requires all files present but some rows insufficient."""
    from yieldos.pilot.domain_contracts import DomainContracts
    contract = DomainContracts.get("semiconductor")
    req = contract.required_fields
    # Find a required CSV field with minimum_viable_rows > 1
    candidate = next(
        (f for f in req if f.format == "csv" and f.columns and f.minimum_viable_rows > 1),
        None,
    )
    if candidate is None:
        pytest.skip("no suitable candidate for PARTIAL test")

    input_dir = tmp_path / "partial"
    input_dir.mkdir()
    out = tmp_path / "out"
    for f in req:
        if f.name == candidate.name:
            # Write below minimum_viable_rows but > 0
            _write_csv(input_dir / f.name, rows=1, columns=f.columns)
        elif f.format == "csv" and f.columns:
            _write_csv(input_dir / f.name, rows=f.minimum_viable_rows + 1, columns=f.columns)
        elif f.format == "json":
            (input_dir / f.name).write_text(
                json.dumps({k: "val" for k in (f.json_keys or [])}),
                encoding="utf-8",
            )
        else:
            (input_dir / f.name).write_text("dummy", encoding="utf-8")

    run_pilot_check(domain="semiconductor", input_dir=input_dir, out_dir=out)
    report = _read_report(out)
    # PARTIAL or NOT_READY — must not be READY
    assert report["readiness_status"] != STATUS_READY


# ── Canonical status values enforcement ───────────────────────────────────────

def test_readiness_status_not_old_ready(tmp_path):
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=SAMPLES_ROOT / "pilot_robot", out_dir=out)
    report = _read_report(out)
    assert report["readiness_status"] != "READY"
    assert report["readiness_status"] != "OK"
    assert report["readiness_status"] != "PASS"


def test_readiness_status_not_old_not_ready(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    report = _read_report(out)
    assert report["readiness_status"] != "NOT_READY"
    assert report["readiness_status"] == STATUS_NOT_READY


# ── hardware_control_enabled always false ─────────────────────────────────────

def test_hardware_control_disabled_when_ready(tmp_path):
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=SAMPLES_ROOT / "pilot_robot", out_dir=out)
    report = _read_report(out)
    assert report["hardware_control_enabled"] is False


def test_hardware_control_disabled_when_not_ready(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    report = _read_report(out)
    assert report["hardware_control_enabled"] is False
