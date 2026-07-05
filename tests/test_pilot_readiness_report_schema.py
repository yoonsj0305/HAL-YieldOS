"""
tests/test_pilot_readiness_report_schema.py

Strict schema tests for pilot_readiness_report.json (v2.9.2).
Asserts all canonical top-level fields exist and have correct types/values.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yieldos.pilot.readiness import (
    STATUS_INVALID,
    STATUS_NOT_READY,
    STATUS_PARTIAL,
    STATUS_READY,
    run_pilot_check,
)

SAMPLES_ROOT = Path(__file__).parent.parent / "samples"
DOMAINS = ["robot", "semiconductor", "space", "memory", "semiforge"]
ALLOWED_STATUSES = {STATUS_READY, STATUS_PARTIAL, STATUS_NOT_READY, STATUS_INVALID}

FY_READINESS_KEYS = [
    "remaining_functions_inputs_ready",
    "blocked_functions_inputs_ready",
    "valid_conditions_inputs_ready",
    "evidence_inputs_ready",
    "human_review_inputs_ready",
]


@pytest.fixture(params=DOMAINS)
def report_out(tmp_path, request):
    domain = request.param
    sample_dir = SAMPLES_ROOT / f"pilot_{domain}"
    out = tmp_path / f"report_{domain}"
    run_pilot_check(domain=domain, input_dir=sample_dir, out_dir=out)
    data = json.loads((out / "pilot_readiness_report.json").read_text(encoding="utf-8"))
    return domain, data


# ── Schema identifier ─────────────────────────────────────────────────────────

def test_schema_field_correct(report_out):
    _, data = report_out
    assert data["schema"] == "hal.yieldos.pilot.readiness_report.v1"


def test_domain_field_matches(report_out):
    domain, data = report_out
    assert data["domain"] == domain


# ── Canonical readiness_status (v2.9.2) ───────────────────────────────────────

def test_readiness_status_exists(report_out):
    _, data = report_out
    assert "readiness_status" in data, "canonical 'readiness_status' field must exist"


def test_readiness_status_is_allowed_value(report_out):
    domain, data = report_out
    assert data["readiness_status"] in ALLOWED_STATUSES, (
        f"{domain}: readiness_status '{data['readiness_status']}' is not allowed"
    )


def test_readiness_status_not_short_value(report_out):
    domain, data = report_out
    forbidden = {"READY", "PARTIAL", "NOT_READY", "OK", "PASS"}
    assert data["readiness_status"] not in forbidden, (
        f"{domain}: readiness_status must not use short/old values"
    )


# ── File presence lists ───────────────────────────────────────────────────────

def test_required_files_present_is_list(report_out):
    _, data = report_out
    assert isinstance(data.get("required_files_present"), list)


def test_required_files_missing_is_list(report_out):
    _, data = report_out
    assert isinstance(data.get("required_files_missing"), list)


def test_optional_files_present_is_list(report_out):
    _, data = report_out
    assert isinstance(data.get("optional_files_present"), list)


def test_optional_files_missing_is_list(report_out):
    _, data = report_out
    assert isinstance(data.get("optional_files_missing"), list)


# ── column_check structure ────────────────────────────────────────────────────

def test_column_check_exists(report_out):
    _, data = report_out
    assert "column_check" in data


def test_column_check_passed_is_list(report_out):
    _, data = report_out
    assert isinstance(data["column_check"].get("passed"), list)


def test_column_check_failed_is_list(report_out):
    _, data = report_out
    assert isinstance(data["column_check"].get("failed"), list)


# ── unit_check structure ──────────────────────────────────────────────────────

def test_unit_check_exists(report_out):
    _, data = report_out
    assert "unit_check" in data


def test_unit_check_passed_is_list(report_out):
    _, data = report_out
    assert isinstance(data["unit_check"].get("passed"), list)


def test_unit_check_warnings_is_list(report_out):
    _, data = report_out
    assert isinstance(data["unit_check"].get("warnings"), list)


# ── minimum_viable_rows_check structure ───────────────────────────────────────

def test_mvr_check_exists(report_out):
    _, data = report_out
    assert "minimum_viable_rows_check" in data


def test_mvr_check_passed_is_list(report_out):
    _, data = report_out
    assert isinstance(data["minimum_viable_rows_check"].get("passed"), list)


def test_mvr_check_failed_is_list(report_out):
    _, data = report_out
    assert isinstance(data["minimum_viable_rows_check"].get("failed"), list)


def test_mvr_check_warnings_is_list(report_out):
    _, data = report_out
    assert isinstance(data["minimum_viable_rows_check"].get("warnings"), list)


# ── functional_yield_readiness (5 booleans) ───────────────────────────────────

def test_functional_yield_readiness_exists(report_out):
    _, data = report_out
    assert "functional_yield_readiness" in data


def test_functional_yield_readiness_has_all_five_keys(report_out):
    domain, data = report_out
    fyr = data["functional_yield_readiness"]
    for key in FY_READINESS_KEYS:
        assert key in fyr, f"{domain}: functional_yield_readiness missing '{key}'"


def test_functional_yield_readiness_values_are_bool(report_out):
    domain, data = report_out
    fyr = data["functional_yield_readiness"]
    for key in FY_READINESS_KEYS:
        val = fyr.get(key)
        assert isinstance(val, bool), (
            f"{domain}: functional_yield_readiness['{key}'] must be bool, got {type(val)}"
        )


# ── Safety fields ─────────────────────────────────────────────────────────────

def test_human_review_required_is_true(report_out):
    _, data = report_out
    assert data.get("human_review_required") is True


def test_hardware_control_enabled_is_false(report_out):
    _, data = report_out
    assert data.get("hardware_control_enabled") is False


def test_claim_boundary_exists(report_out):
    _, data = report_out
    assert "claim_boundary" in data
    assert data["claim_boundary"]


# ── Claim context lists ───────────────────────────────────────────────────────

def test_sufficient_for_is_list(report_out):
    _, data = report_out
    assert isinstance(data.get("sufficient_for"), list)


def test_not_sufficient_for_is_list(report_out):
    _, data = report_out
    assert isinstance(data.get("not_sufficient_for"), list)


def test_not_sufficient_for_contains_hardware_control(report_out):
    domain, data = report_out
    assert "hardware_control" in data.get("not_sufficient_for", []), (
        f"{domain}: not_sufficient_for must include 'hardware_control'"
    )


# ── Sample data READY → functional_yield_readiness all True ──────────────────

def test_ready_domain_fy_readiness_all_true(report_out):
    domain, data = report_out
    if data["readiness_status"] != STATUS_READY:
        pytest.skip(f"{domain} sample is not READY")
    fyr = data["functional_yield_readiness"]
    for key in FY_READINESS_KEYS:
        assert fyr[key] is True, (
            f"{domain}: expected {key}=True when READY, got {fyr[key]}"
        )
