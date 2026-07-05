"""
tests/test_pilot_readiness_semantics.py

Tests readiness semantic correctness (v2.9.1):
  - READY_FOR_FUNCTIONAL_YIELD_PILOT: all required files present + sufficient rows
  - PARTIAL_FOR_FUNCTIONAL_YIELD_PILOT: required files present but some insufficient rows
  - NOT_READY_FOR_FUNCTIONAL_YIELD_PILOT: some required files missing
  - minimum_viable_rows per-file check
  - Row count checking: files below minimum_viable_rows are treated as blocking
  - Score capping when any required file is missing
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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_csv(path: Path, rows: int, columns: list[str]) -> Path:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for i in range(rows):
            writer.writerow({c: f"val_{i}" for c in columns})
    return path


def _read_report(out: Path) -> dict:
    return json.loads((out / "pilot_readiness_report.json").read_text(encoding="utf-8"))


def _read_boundary(out: Path) -> dict:
    return json.loads((out / "pilot_decision_boundary.json").read_text(encoding="utf-8"))


def _read_dsp(out: Path) -> dict:
    return json.loads((out / "data_sufficiency_preview.json").read_text(encoding="utf-8"))


# ── Status: READY_FOR_FUNCTIONAL_YIELD_PILOT ──────────────────────────────────

def test_robot_sample_is_ready(tmp_path):
    """Built-in sample data must return READY (Option A: low minimum_viable_rows)."""
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=SAMPLES_ROOT / "pilot_robot", out_dir=out)
    report = _read_report(out)
    assert report["status"] == STATUS_READY


def test_semiconductor_sample_is_ready(tmp_path):
    out = tmp_path / "out"
    run_pilot_check(
        domain="semiconductor",
        input_dir=SAMPLES_ROOT / "pilot_semiconductor",
        out_dir=out,
    )
    report = _read_report(out)
    assert report["status"] == STATUS_READY


def test_space_sample_is_ready(tmp_path):
    out = tmp_path / "out"
    run_pilot_check(domain="space", input_dir=SAMPLES_ROOT / "pilot_space", out_dir=out)
    report = _read_report(out)
    assert report["status"] == STATUS_READY


def test_memory_sample_is_ready(tmp_path):
    out = tmp_path / "out"
    run_pilot_check(domain="memory", input_dir=SAMPLES_ROOT / "pilot_memory", out_dir=out)
    report = _read_report(out)
    assert report["status"] == STATUS_READY


def test_semiforge_sample_is_ready(tmp_path):
    out = tmp_path / "out"
    run_pilot_check(
        domain="semiforge",
        input_dir=SAMPLES_ROOT / "pilot_semiforge",
        out_dir=out,
    )
    report = _read_report(out)
    assert report["status"] == STATUS_READY


def test_ready_score_is_above_threshold(tmp_path):
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=SAMPLES_ROOT / "pilot_robot", out_dir=out)
    report = _read_report(out)
    assert report["readiness_score"] >= 0.8


def test_ready_pilot_can_proceed(tmp_path):
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=SAMPLES_ROOT / "pilot_robot", out_dir=out)
    boundary = _read_boundary(out)
    assert boundary["pilot_can_proceed"] is True


# ── Status: NOT_READY_FOR_FUNCTIONAL_YIELD_PILOT ──────────────────────────────

def test_empty_dir_is_not_ready(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    report = _read_report(out)
    assert report["status"] == STATUS_NOT_READY


def test_empty_dir_score_is_capped(tmp_path):
    """Score must be ≤ 0.4 when required files are missing."""
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    report = _read_report(out)
    assert report["readiness_score"] <= 0.4


def test_empty_dir_blocking_count_matches_required_files(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    report = _read_report(out)
    # robot has 2 required files → 2 blocking
    assert report["blocking_issue_count"] >= 2


def test_empty_dir_pilot_cannot_proceed(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    boundary = _read_boundary(out)
    assert boundary["pilot_can_proceed"] is False


def test_missing_one_required_file_is_not_ready(tmp_path):
    """Providing only one of two required files → NOT_READY."""
    from yieldos.pilot.domain_contracts import DomainContracts

    input_dir = tmp_path / "partial"
    input_dir.mkdir()
    out = tmp_path / "out"

    contract = DomainContracts.get("robot")
    req = contract.required_fields
    # Write only the first required file with enough rows
    first = req[0]
    if first.format == "csv" and first.columns:
        _write_csv(
            input_dir / first.name,
            rows=first.minimum_viable_rows + 2,
            columns=first.columns,
        )
    else:
        (input_dir / first.name).write_text("{}", encoding="utf-8")

    run_pilot_check(domain="robot", input_dir=input_dir, out_dir=out)
    report = _read_report(out)
    assert report["status"] == STATUS_NOT_READY


# ── Status: PARTIAL_FOR_FUNCTIONAL_YIELD_PILOT ────────────────────────────────

def test_insufficient_rows_is_partial_or_not_ready(tmp_path):
    """
    A required file present but with too few rows is blocking → NOT_READY or PARTIAL.
    We just confirm it's not READY.
    """
    from yieldos.pilot.domain_contracts import DomainContracts

    input_dir = tmp_path / "partial_rows"
    input_dir.mkdir()
    out = tmp_path / "out"

    contract = DomainContracts.get("semiconductor")
    req = contract.required_fields

    # Write all required files but with only 1 row each (below minimum_viable_rows=5)
    for f in req:
        if f.format == "csv" and f.columns:
            _write_csv(input_dir / f.name, rows=1, columns=f.columns)
        elif f.format == "json":
            (input_dir / f.name).write_text(
                json.dumps({k: "val" for k in (f.json_keys or [])}),
                encoding="utf-8",
            )
        else:
            (input_dir / f.name).write_text("dummy", encoding="utf-8")

    run_pilot_check(domain="semiconductor", input_dir=input_dir, out_dir=out)
    report = _read_report(out)
    assert report["status"] != STATUS_READY, (
        "Files with insufficient rows should not return READY"
    )


# ── minimum_viable_rows enforcement ───────────────────────────────────────────

def test_file_with_exact_minimum_rows_is_sufficient(tmp_path):
    """A file with exactly minimum_viable_rows rows must be SUFFICIENT."""
    from yieldos.pilot.domain_contracts import DomainContracts

    input_dir = tmp_path / "exact"
    input_dir.mkdir()
    out = tmp_path / "out"

    contract = DomainContracts.get("semiconductor")
    req = contract.required_fields

    for f in req:
        if f.format == "csv" and f.columns:
            _write_csv(input_dir / f.name, rows=f.minimum_viable_rows, columns=f.columns)
        elif f.format == "json":
            (input_dir / f.name).write_text(
                json.dumps({k: "val" for k in (f.json_keys or [])}),
                encoding="utf-8",
            )
        else:
            (input_dir / f.name).write_text("dummy", encoding="utf-8")

    run_pilot_check(domain="semiconductor", input_dir=input_dir, out_dir=out)
    dsp = _read_dsp(out)
    for pf in dsp["per_file"]:
        if pf["required"]:
            assert pf["sufficiency_status"] == "SUFFICIENT", (
                f"semiconductor/{pf['file']}: expected SUFFICIENT at minimum_viable_rows "
                f"({pf['minimum_viable_rows']}), got {pf['sufficiency_status']}"
            )


def test_file_below_minimum_rows_is_insufficient(tmp_path):
    """A required file with rows < minimum_viable_rows must be INSUFFICIENT."""
    from yieldos.pilot.domain_contracts import DomainContracts

    input_dir = tmp_path / "below"
    input_dir.mkdir()
    out = tmp_path / "out"

    contract = DomainContracts.get("semiconductor")
    req = contract.required_fields

    for f in req:
        # Write 1 row less than minimum_viable_rows for all required files
        rows = max(1, f.minimum_viable_rows - 1)
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

    if min(f.minimum_viable_rows for f in req) > 1:
        # At least one file should be INSUFFICIENT
        dsp = _read_dsp(out)
        required_files = [pf for pf in dsp["per_file"] if pf["required"]]
        insufficient = [
            pf for pf in required_files if pf["sufficiency_status"] == "INSUFFICIENT"
        ]
        assert len(insufficient) >= 1, (
            "Files with fewer than minimum_viable_rows rows must be INSUFFICIENT"
        )


# ── Data sufficiency_status values ────────────────────────────────────────────

def test_missing_file_has_missing_sufficiency_status(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    dsp = _read_dsp(out)
    required_checks = [pf for pf in dsp["per_file"] if pf["required"]]
    assert all(pf["sufficiency_status"] == "MISSING" for pf in required_checks)


def test_sample_required_files_are_sufficient(tmp_path):
    """All required sample files must be SUFFICIENT (built-in sample meets minimum_viable_rows)."""
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=SAMPLES_ROOT / "pilot_robot", out_dir=out)
    dsp = _read_dsp(out)
    required_checks = [pf for pf in dsp["per_file"] if pf["required"]]
    assert all(pf["sufficiency_status"] == "SUFFICIENT" for pf in required_checks), (
        f"Required files not all SUFFICIENT: "
        f"{[(pf['file'], pf['sufficiency_status']) for pf in required_checks if pf['sufficiency_status'] != 'SUFFICIENT']}"
    )


# ── FileNotFoundError for missing input dir ───────────────────────────────────

def test_missing_input_dir_raises(tmp_path):
    out = tmp_path / "out"
    with pytest.raises(FileNotFoundError):
        run_pilot_check(
            domain="robot",
            input_dir=tmp_path / "nonexistent",
            out_dir=out,
        )


# ── Canonical status does not use old short values ───────────────────────────

def test_canonical_status_not_old_value_ready(tmp_path):
    """pilot_readiness_report must not use old 'READY' value."""
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=SAMPLES_ROOT / "pilot_robot", out_dir=out)
    report = _read_report(out)
    assert report["status"] != "READY", (
        "pilot_readiness_report.json must use canonical v2.9.1 status, not old 'READY'"
    )
    assert report["status"] == STATUS_READY


def test_canonical_status_not_old_value_not_ready(tmp_path):
    """pilot_readiness_report must not use old 'NOT_READY' value."""
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    report = _read_report(out)
    assert report["status"] != "NOT_READY", (
        "pilot_readiness_report.json must use canonical v2.9.1 status, not old 'NOT_READY'"
    )
    assert report["status"] == STATUS_NOT_READY


# ── Compat alias still uses old values ───────────────────────────────────────

def test_compat_readiness_report_uses_old_status(tmp_path):
    """readiness_report.json (compat alias) must still return old 'READY' value."""
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=SAMPLES_ROOT / "pilot_robot", out_dir=out)
    compat = json.loads((out / "readiness_report.json").read_text(encoding="utf-8"))
    assert compat["status"] == "READY"
    assert compat["status_v291"] == STATUS_READY


def test_compat_readiness_report_not_ready_uses_old_value(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    compat = json.loads((out / "readiness_report.json").read_text(encoding="utf-8"))
    assert compat["status"] == "NOT_READY"
    assert compat["status_v291"] == STATUS_NOT_READY
