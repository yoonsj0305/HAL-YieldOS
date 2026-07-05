"""
tests/test_pilot_data_sufficiency_preview_schema.py

Strict schema tests for data_sufficiency_preview.json (v2.9.2).
Asserts top-level canonical fields exist with correct types/values.
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

ALLOWED_SUFFICIENCY_STATUSES = {
    "SUFFICIENT_FOR_CANDIDATE_REVIEW",
    "PARTIAL_FOR_CANDIDATE_REVIEW",
    "INSUFFICIENT_FOR_CANDIDATE_REVIEW",
    "INVALID_INPUT",
}

_STATUS_TO_SUFFICIENCY = {
    STATUS_READY: "SUFFICIENT_FOR_CANDIDATE_REVIEW",
    STATUS_PARTIAL: "PARTIAL_FOR_CANDIDATE_REVIEW",
    STATUS_NOT_READY: "INSUFFICIENT_FOR_CANDIDATE_REVIEW",
}


@pytest.fixture(params=DOMAINS)
def dsp_out(tmp_path, request):
    domain = request.param
    sample_dir = SAMPLES_ROOT / f"pilot_{domain}"
    out = tmp_path / f"dsp_{domain}"
    run_pilot_check(domain=domain, input_dir=sample_dir, out_dir=out)
    data = json.loads((out / "data_sufficiency_preview.json").read_text(encoding="utf-8"))
    report = json.loads((out / "pilot_readiness_report.json").read_text(encoding="utf-8"))
    return domain, data, report


# ── Schema identifier ─────────────────────────────────────────────────────────

def test_schema_field_correct(dsp_out):
    _, data, _ = dsp_out
    assert data["schema"] == "hal.yieldos.pilot.data_sufficiency_preview.v1"


def test_domain_field_matches(dsp_out):
    domain, data, _ = dsp_out
    assert data["domain"] == domain


# ── Top-level sufficiency_status (v2.9.2) ─────────────────────────────────────

def test_sufficiency_status_exists_at_top_level(dsp_out):
    _, data, _ = dsp_out
    assert "sufficiency_status" in data, "top-level 'sufficiency_status' field must exist"


def test_sufficiency_status_not_buried_only_in_per_file(dsp_out):
    _, data, _ = dsp_out
    # Must exist at top level, not just inside per_file entries
    assert "sufficiency_status" in data
    assert not isinstance(data["sufficiency_status"], list)


def test_sufficiency_status_is_allowed_value(dsp_out):
    domain, data, _ = dsp_out
    assert data["sufficiency_status"] in ALLOWED_SUFFICIENCY_STATUSES, (
        f"{domain}: sufficiency_status '{data['sufficiency_status']}' is not allowed"
    )


def test_sufficiency_status_maps_from_readiness_status(dsp_out):
    domain, data, report = dsp_out
    readiness_status = report["readiness_status"]
    expected = _STATUS_TO_SUFFICIENCY.get(readiness_status)
    if expected is None:
        return  # INVALID_INPUT or unknown — skip mapping check
    assert data["sufficiency_status"] == expected, (
        f"{domain}: readiness={readiness_status} → expected sufficiency={expected}, "
        f"got {data['sufficiency_status']}"
    )


# ── Top-level sufficient_for (v2.9.2) ────────────────────────────────────────

def test_sufficient_for_exists_at_top_level(dsp_out):
    _, data, _ = dsp_out
    assert "sufficient_for" in data, "top-level 'sufficient_for' field must exist"


def test_sufficient_for_is_list(dsp_out):
    _, data, _ = dsp_out
    assert isinstance(data["sufficient_for"], list)


# ── Top-level not_sufficient_for (v2.9.2) ────────────────────────────────────

def test_not_sufficient_for_exists_at_top_level(dsp_out):
    _, data, _ = dsp_out
    assert "not_sufficient_for" in data, "top-level 'not_sufficient_for' field must exist"


def test_not_sufficient_for_is_list(dsp_out):
    _, data, _ = dsp_out
    assert isinstance(data["not_sufficient_for"], list)


def test_not_sufficient_for_contains_hardware_control(dsp_out):
    domain, data, _ = dsp_out
    assert "hardware_control" in data.get("not_sufficient_for", []), (
        f"{domain}: not_sufficient_for must include 'hardware_control'"
    )


# ── Top-level functional_yield_gaps (v2.9.2) ─────────────────────────────────

def test_functional_yield_gaps_exists_at_top_level(dsp_out):
    _, data, _ = dsp_out
    assert "functional_yield_gaps" in data, "top-level 'functional_yield_gaps' field must exist"


def test_functional_yield_gaps_is_list(dsp_out):
    _, data, _ = dsp_out
    assert isinstance(data["functional_yield_gaps"], list)


def test_functional_yield_gaps_empty_when_ready(dsp_out):
    domain, data, report = dsp_out
    if report["readiness_status"] != STATUS_READY:
        pytest.skip(f"{domain} sample is not READY")
    assert data["functional_yield_gaps"] == [], (
        f"{domain}: functional_yield_gaps must be empty when READY"
    )


# ── claim_boundary ────────────────────────────────────────────────────────────

def test_claim_boundary_exists(dsp_out):
    _, data, _ = dsp_out
    assert "claim_boundary" in data
    assert data["claim_boundary"]


# ── per_file detail still present ────────────────────────────────────────────

def test_per_file_still_exists(dsp_out):
    _, data, _ = dsp_out
    assert "per_file" in data
    assert isinstance(data["per_file"], list)


def test_per_file_has_sufficiency_status(dsp_out):
    domain, data, _ = dsp_out
    for entry in data["per_file"]:
        assert "sufficiency_status" in entry, (
            f"{domain}/{entry.get('file')}: per_file entry missing 'sufficiency_status'"
        )


# ── sample data: SUFFICIENT_FOR_CANDIDATE_REVIEW for all 5 domains ───────────

@pytest.mark.parametrize("domain", DOMAINS)
def test_sample_data_is_sufficient_for_candidate_review(tmp_path, domain):
    sample_dir = SAMPLES_ROOT / f"pilot_{domain}"
    out = tmp_path / f"dsp_{domain}"
    run_pilot_check(domain=domain, input_dir=sample_dir, out_dir=out)
    data = json.loads((out / "data_sufficiency_preview.json").read_text(encoding="utf-8"))
    assert data["sufficiency_status"] == "SUFFICIENT_FOR_CANDIDATE_REVIEW", (
        f"{domain}: expected SUFFICIENT_FOR_CANDIDATE_REVIEW, got {data['sufficiency_status']}"
    )


def test_empty_dir_is_insufficient(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    run_pilot_check(domain="robot", input_dir=empty, out_dir=out)
    data = json.loads((out / "data_sufficiency_preview.json").read_text(encoding="utf-8"))
    assert data["sufficiency_status"] == "INSUFFICIENT_FOR_CANDIDATE_REVIEW"
