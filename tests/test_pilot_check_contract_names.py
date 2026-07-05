"""
tests/test_pilot_check_contract_names.py

Tests canonical output file names for `yieldos pilot check` (v2.9.1).
Verifies all 4 canonical files are generated with correct schemas.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yieldos.pilot.readiness import (
    STATUS_NOT_READY,
    STATUS_PARTIAL,
    STATUS_READY,
    run_pilot_check,
)

SAMPLES_ROOT = Path(__file__).parent.parent / "samples"

DOMAINS = ["robot", "semiconductor", "space", "memory", "semiforge"]

CANONICAL_CHECK_FILES = [
    "pilot_readiness_report.json",
    "missing_data_request.json",
    "data_sufficiency_preview.json",
    "pilot_decision_boundary.json",
]

VALID_STATUSES = {STATUS_READY, STATUS_PARTIAL, STATUS_NOT_READY}


@pytest.fixture(params=DOMAINS)
def check_out(tmp_path, request):
    domain = request.param
    sample_dir = SAMPLES_ROOT / f"pilot_{domain}"
    out = tmp_path / f"check_{domain}"
    run_pilot_check(domain=domain, input_dir=sample_dir, out_dir=out)
    return domain, out


# ── All canonical files exist ─────────────────────────────────────────────────

def test_canonical_check_files_exist(check_out):
    domain, out = check_out
    for fname in CANONICAL_CHECK_FILES:
        assert (out / fname).exists(), f"{domain}: canonical file '{fname}' not generated"


# ── pilot_readiness_report.json ───────────────────────────────────────────────

def test_pilot_readiness_report_schema(check_out):
    domain, out = check_out
    data = json.loads((out / "pilot_readiness_report.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot.readiness_report.v1"
    assert data["domain"] == domain


def test_pilot_readiness_report_canonical_status(check_out):
    domain, out = check_out
    data = json.loads((out / "pilot_readiness_report.json").read_text(encoding="utf-8"))
    assert data["status"] in VALID_STATUSES, (
        f"{domain}: status '{data['status']}' is not a canonical v2.9.1 status value"
    )


def test_pilot_readiness_report_score_range(check_out):
    domain, out = check_out
    data = json.loads((out / "pilot_readiness_report.json").read_text(encoding="utf-8"))
    assert 0.0 <= data["readiness_score"] <= 1.0


def test_pilot_readiness_report_human_review(check_out):
    domain, out = check_out
    data = json.loads((out / "pilot_readiness_report.json").read_text(encoding="utf-8"))
    assert data["human_review_required"] is True
    assert data["automatic_decision_enabled"] is False


def test_pilot_readiness_report_has_functional_yield_mapping(check_out):
    domain, out = check_out
    data = json.loads((out / "pilot_readiness_report.json").read_text(encoding="utf-8"))
    assert "functional_yield_mapping" in data
    fym = data["functional_yield_mapping"]
    assert set(fym.keys()) == {
        "remaining_functions_inputs",
        "blocked_functions_inputs",
        "valid_conditions_inputs",
        "evidence_inputs",
        "human_review_inputs",
    }


def test_sample_data_returns_ready(check_out):
    """Sample data with Option A minimum_viable_rows should return READY."""
    domain, out = check_out
    data = json.loads((out / "pilot_readiness_report.json").read_text(encoding="utf-8"))
    assert data["status"] == STATUS_READY, (
        f"{domain}: expected {STATUS_READY} but got '{data['status']}'. "
        f"Score: {data['readiness_score']}"
    )


# ── missing_data_request.json ─────────────────────────────────────────────────

def test_missing_data_request_schema(check_out):
    domain, out = check_out
    data = json.loads((out / "missing_data_request.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot.missing_data_request.v1"


def test_missing_data_request_sample_has_no_blocking(check_out):
    """Sample data has all required files — missing_data_request items should be empty."""
    domain, out = check_out
    data = json.loads((out / "missing_data_request.json").read_text(encoding="utf-8"))
    p0_items = [i for i in data.get("items", []) if i.get("priority") == "P0_blocking"]
    assert p0_items == [], (
        f"{domain}: sample data should have no P0 blocking missing files, "
        f"got: {[i['file'] for i in p0_items]}"
    )


def test_missing_data_request_has_why_needed(check_out):
    """Any items in missing_data_request must have why_needed_for_functional_yield."""
    domain, out = check_out
    data = json.loads((out / "missing_data_request.json").read_text(encoding="utf-8"))
    for item in data.get("items", []):
        assert "why_needed_for_functional_yield" in item, (
            f"{domain}: {item['file']} missing why_needed_for_functional_yield"
        )


# ── data_sufficiency_preview.json ─────────────────────────────────────────────

def test_data_sufficiency_preview_schema(check_out):
    domain, out = check_out
    data = json.loads((out / "data_sufficiency_preview.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot.data_sufficiency_preview.v1"


def test_data_sufficiency_preview_has_per_file(check_out):
    domain, out = check_out
    data = json.loads((out / "data_sufficiency_preview.json").read_text(encoding="utf-8"))
    assert "per_file" in data
    assert len(data["per_file"]) >= 2


def test_data_sufficiency_preview_sufficiency_status_values(check_out):
    domain, out = check_out
    data = json.loads((out / "data_sufficiency_preview.json").read_text(encoding="utf-8"))
    valid = {"SUFFICIENT", "INSUFFICIENT", "MISSING"}
    for pf in data["per_file"]:
        assert pf["sufficiency_status"] in valid, (
            f"{domain}: {pf['file']} has invalid sufficiency_status: {pf['sufficiency_status']}"
        )


def test_data_sufficiency_preview_sample_all_sufficient(check_out):
    """Sample data files should all be SUFFICIENT."""
    domain, out = check_out
    data = json.loads((out / "data_sufficiency_preview.json").read_text(encoding="utf-8"))
    required_files = [pf for pf in data["per_file"] if pf.get("required")]
    not_sufficient = [
        pf for pf in required_files if pf["sufficiency_status"] != "SUFFICIENT"
    ]
    assert not_sufficient == [], (
        f"{domain}: required files not SUFFICIENT: "
        f"{[(pf['file'], pf['sufficiency_status']) for pf in not_sufficient]}"
    )


def test_data_sufficiency_preview_has_functional_yield_mapping(check_out):
    domain, out = check_out
    data = json.loads((out / "data_sufficiency_preview.json").read_text(encoding="utf-8"))
    assert "functional_yield_mapping" in data


# ── pilot_decision_boundary.json ──────────────────────────────────────────────

def test_pilot_decision_boundary_schema(check_out):
    domain, out = check_out
    data = json.loads((out / "pilot_decision_boundary.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot.decision_boundary.v1"


def test_pilot_decision_boundary_safety(check_out):
    domain, out = check_out
    data = json.loads((out / "pilot_decision_boundary.json").read_text(encoding="utf-8"))
    assert data["human_review_required"] is True
    assert data["automatic_decision_enabled"] is False
    assert data["hardware_control_enabled"] is False
    assert data["read_only"] is True
    assert data["candidate_only"] is True


def test_pilot_decision_boundary_sample_can_proceed(check_out):
    """Sample data should allow pilot to proceed."""
    domain, out = check_out
    data = json.loads((out / "pilot_decision_boundary.json").read_text(encoding="utf-8"))
    assert data["pilot_can_proceed"] is True, (
        f"{domain}: sample data should allow pilot to proceed"
    )


def test_pilot_decision_boundary_status_matches_report(check_out):
    domain, out = check_out
    report = json.loads((out / "pilot_readiness_report.json").read_text(encoding="utf-8"))
    boundary = json.loads((out / "pilot_decision_boundary.json").read_text(encoding="utf-8"))
    assert boundary["readiness_status"] == report["status"], (
        f"{domain}: decision boundary status does not match readiness report status"
    )
