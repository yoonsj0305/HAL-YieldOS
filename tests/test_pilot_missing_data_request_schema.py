"""
tests/test_pilot_missing_data_request_schema.py

Strict schema tests for missing_data_request.json (v2.9.2).
Asserts canonical missing arrays exist and why_needed entries have FY relevance.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from yieldos.pilot.readiness import run_pilot_check

SAMPLES_ROOT = Path(__file__).parent.parent / "samples"
DOMAINS = ["robot", "semiconductor", "space", "memory", "semiforge"]

_FY_KEYWORDS = {
    "remaining function",
    "remaining functions",
    "blocked function",
    "blocked functions",
    "valid condition",
    "valid conditions",
    "evidence",
    "human review",
    "functional yield",
}

REQUIRED_CANONICAL_ARRAYS = [
    "missing_required_files",
    "missing_required_columns",
    "missing_units",
    "minimum_viable_rows_failures",
    "recommended_optional_files",
    "why_needed_for_functional_yield",
]


def _has_fy_keyword(reason: str) -> bool:
    reason_lower = reason.lower()
    return any(kw in reason_lower for kw in _FY_KEYWORDS)


def _write_csv(path: Path, rows: int, columns: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for i in range(rows):
            writer.writerow({c: f"v{i}" for c in columns})


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(params=DOMAINS)
def mdr_complete(tmp_path, request):
    """missing_data_request from complete sample data."""
    domain = request.param
    sample_dir = SAMPLES_ROOT / f"pilot_{domain}"
    out = tmp_path / f"mdr_complete_{domain}"
    run_pilot_check(domain=domain, input_dir=sample_dir, out_dir=out)
    data = json.loads((out / "missing_data_request.json").read_text(encoding="utf-8"))
    return domain, data


@pytest.fixture
def mdr_missing_required(tmp_path):
    """missing_data_request when a required file is absent (robot domain)."""
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    data = json.loads((out / "missing_data_request.json").read_text(encoding="utf-8"))
    return data


@pytest.fixture
def mdr_missing_column(tmp_path):
    """missing_data_request when required CSV columns are absent."""
    from yieldos.pilot.domain_contracts import DomainContracts
    contract = DomainContracts.get("robot")
    req = contract.required_fields
    input_dir = tmp_path / "badcols"
    input_dir.mkdir()
    out = tmp_path / "out"
    for f in req:
        if f.format == "csv" and f.columns:
            # Write CSV with only first column — rest are missing
            _write_csv(input_dir / f.name, rows=f.minimum_viable_rows + 1, columns=f.columns[:1])
        elif f.format == "json":
            (input_dir / f.name).write_text("{}", encoding="utf-8")
        else:
            (input_dir / f.name).write_text("dummy", encoding="utf-8")
    run_pilot_check(domain="robot", input_dir=input_dir, out_dir=out)
    data = json.loads((out / "missing_data_request.json").read_text(encoding="utf-8"))
    return data


@pytest.fixture
def mdr_insufficient_rows(tmp_path):
    """missing_data_request when required files have too few rows."""
    from yieldos.pilot.domain_contracts import DomainContracts
    contract = DomainContracts.get("semiconductor")
    req = contract.required_fields
    input_dir = tmp_path / "fewrows"
    input_dir.mkdir()
    out = tmp_path / "out"
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
    data = json.loads((out / "missing_data_request.json").read_text(encoding="utf-8"))
    return data


# ── Schema and canonical arrays ───────────────────────────────────────────────

def test_schema_field_correct(mdr_complete):
    _, data = mdr_complete
    assert data["schema"] == "hal.yieldos.pilot.missing_data_request.v1"


def test_domain_field_matches(mdr_complete):
    domain, data = mdr_complete
    assert data["domain"] == domain


@pytest.mark.parametrize("array_key", REQUIRED_CANONICAL_ARRAYS)
def test_canonical_array_exists(mdr_complete, array_key):
    domain, data = mdr_complete
    assert array_key in data, f"{domain}: canonical array '{array_key}' must exist"
    assert isinstance(data[array_key], list), (
        f"{domain}: '{array_key}' must be a list"
    )


def test_human_review_required_is_true(mdr_complete):
    _, data = mdr_complete
    assert data.get("human_review_required") is True


def test_claim_boundary_exists(mdr_complete):
    _, data = mdr_complete
    assert "claim_boundary" in data
    assert data["claim_boundary"]


# ── Complete sample: all canonical arrays are lists (may be empty) ────────────

def test_complete_sample_missing_required_files_is_list(mdr_complete):
    _, data = mdr_complete
    assert isinstance(data["missing_required_files"], list)


def test_complete_sample_missing_required_columns_is_list(mdr_complete):
    _, data = mdr_complete
    assert isinstance(data["missing_required_columns"], list)


def test_complete_sample_missing_units_is_list(mdr_complete):
    _, data = mdr_complete
    assert isinstance(data["missing_units"], list)


def test_complete_sample_mvr_failures_is_list(mdr_complete):
    _, data = mdr_complete
    assert isinstance(data["minimum_viable_rows_failures"], list)


def test_complete_sample_recommended_optional_is_list(mdr_complete):
    _, data = mdr_complete
    assert isinstance(data["recommended_optional_files"], list)


def test_complete_sample_why_needed_is_list(mdr_complete):
    _, data = mdr_complete
    assert isinstance(data["why_needed_for_functional_yield"], list)


# ── Missing required file → missing_required_files populated ─────────────────

def test_missing_required_file_populated(mdr_missing_required):
    data = mdr_missing_required
    assert len(data["missing_required_files"]) >= 1, (
        "missing_required_files must be populated when required files are absent"
    )


def test_missing_required_file_why_needed_populated(mdr_missing_required):
    data = mdr_missing_required
    assert len(data["why_needed_for_functional_yield"]) >= 1


def test_why_needed_items_have_required_keys(mdr_missing_required):
    data = mdr_missing_required
    for item in data["why_needed_for_functional_yield"]:
        assert "missing_item" in item, "why_needed item must have 'missing_item'"
        assert "needed_for" in item, "why_needed item must have 'needed_for'"
        assert "reason" in item, "why_needed item must have 'reason'"


def test_why_needed_reason_has_fy_relevance(mdr_missing_required):
    data = mdr_missing_required
    for item in data["why_needed_for_functional_yield"]:
        reason = item.get("reason", "")
        assert _has_fy_keyword(reason), (
            f"why_needed reason must mention functional-yield concept. Got: '{reason}'"
        )


# ── Missing column → missing_required_columns populated ──────────────────────

def test_missing_column_populated(mdr_missing_column):
    data = mdr_missing_column
    assert len(data["missing_required_columns"]) >= 1, (
        "missing_required_columns must be populated when CSV columns are absent"
    )


def test_missing_column_entry_has_file_and_columns(mdr_missing_column):
    data = mdr_missing_column
    for entry in data["missing_required_columns"]:
        assert "file" in entry
        assert "missing_columns" in entry
        assert isinstance(entry["missing_columns"], list)


# ── Insufficient rows → minimum_viable_rows_failures populated ────────────────

def test_insufficient_rows_mvr_failures_populated(mdr_insufficient_rows):
    data = mdr_insufficient_rows
    # semiconductor has min_viable_rows=5, we wrote 1 row — should have failures
    req_contract = None
    from yieldos.pilot.domain_contracts import DomainContracts
    req_contract = DomainContracts.get("semiconductor")
    if all(f.minimum_viable_rows <= 1 for f in req_contract.required_fields):
        pytest.skip("semiconductor minimum_viable_rows <= 1, skip failure test")
    assert len(data["minimum_viable_rows_failures"]) >= 1, (
        "minimum_viable_rows_failures must be populated when rows are below minimum"
    )


def test_insufficient_rows_mvr_entry_has_required_keys(mdr_insufficient_rows):
    data = mdr_insufficient_rows
    for entry in data["minimum_viable_rows_failures"]:
        assert "file" in entry
        assert "row_count" in entry
        assert "minimum_viable_rows" in entry
