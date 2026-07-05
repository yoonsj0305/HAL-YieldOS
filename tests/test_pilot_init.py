"""
tests/test_pilot_init.py

Tests for yieldos.pilot.init_pack.generate_init_pack().
Verifies all 6 output files are generated with correct schemas and content.
"""
from __future__ import annotations

import json

import pytest

from yieldos.pilot.init_pack import generate_init_pack

DOMAINS = ["robot", "semiconductor", "space", "memory", "semiforge"]


@pytest.fixture(params=DOMAINS)
def init_pack_out(tmp_path, request):
    domain = request.param
    out = tmp_path / f"pilot_init_{domain}"
    generate_init_pack(domain=domain, out_dir=out)
    return domain, out


# ── All 6 files exist ────────────────────────────────────────────────────────

def test_all_init_files_exist(init_pack_out):
    domain, out = init_pack_out
    required = [
        "pilot_contract.json",
        "input_requirements.json",
        "missing_data_request.json",
        "sanitization_checklist.json",
        "boundary_statement.json",
        "pilot_readme.md",
    ]
    for f in required:
        assert (out / f).exists(), f"{domain}: {f} not generated"


# ── pilot_contract.json ───────────────────────────────────────────────────────

def test_pilot_contract_schema(init_pack_out):
    domain, out = init_pack_out
    data = json.loads((out / "pilot_contract.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot_contract.v1"
    assert data["domain"] == domain


def test_pilot_contract_has_generated_by(init_pack_out):
    domain, out = init_pack_out
    data = json.loads((out / "pilot_contract.json").read_text(encoding="utf-8"))
    assert "generated_by" in data
    assert data["generated_by"]["product"] == "HAL YieldOS"


def test_pilot_contract_has_input_fields(init_pack_out):
    domain, out = init_pack_out
    data = json.loads((out / "pilot_contract.json").read_text(encoding="utf-8"))
    assert len(data["input_fields"]) >= 2


# ── input_requirements.json ───────────────────────────────────────────────────

def test_input_requirements_schema(init_pack_out):
    domain, out = init_pack_out
    data = json.loads((out / "input_requirements.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot_input_requirements.v1"
    assert data["domain"] == domain


def test_input_requirements_has_required_files(init_pack_out):
    domain, out = init_pack_out
    data = json.loads((out / "input_requirements.json").read_text(encoding="utf-8"))
    assert len(data["required_files"]) >= 2


def test_input_requirements_min_records(init_pack_out):
    domain, out = init_pack_out
    data = json.loads((out / "input_requirements.json").read_text(encoding="utf-8"))
    assert data["min_records"] > 0
    assert data["recommended_records"] >= data["min_records"]


# ── missing_data_request.json ─────────────────────────────────────────────────

def test_missing_data_request_schema(init_pack_out):
    domain, out = init_pack_out
    data = json.loads((out / "missing_data_request.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot_missing_data_request.v1"


def test_missing_data_request_has_blocking_count(init_pack_out):
    domain, out = init_pack_out
    data = json.loads((out / "missing_data_request.json").read_text(encoding="utf-8"))
    assert data["blocking_count"] >= 2, "Must have at least 2 required files"
    assert "items" in data


def test_missing_data_request_items_have_priority(init_pack_out):
    domain, out = init_pack_out
    data = json.loads((out / "missing_data_request.json").read_text(encoding="utf-8"))
    for item in data["items"]:
        assert "priority" in item
        assert item["priority"] in ("P0_blocking", "P1_recommended")


# ── sanitization_checklist.json ───────────────────────────────────────────────

def test_sanitization_checklist_schema(init_pack_out):
    domain, out = init_pack_out
    data = json.loads((out / "sanitization_checklist.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot_sanitization_checklist.v1"


def test_sanitization_checklist_has_required_universal_steps(init_pack_out):
    domain, out = init_pack_out
    data = json.loads((out / "sanitization_checklist.json").read_text(encoding="utf-8"))
    # Must include PII removal step
    categories = [s["category"] for s in data["steps"]]
    assert "PII_removal" in categories
    assert "credentials" in categories
    assert "format_validation" in categories


def test_sanitization_checklist_required_steps_count(init_pack_out):
    domain, out = init_pack_out
    data = json.loads((out / "sanitization_checklist.json").read_text(encoding="utf-8"))
    assert data["required_steps_count"] >= 4


# ── boundary_statement.json ────────────────────────────────────────────────────

def test_boundary_statement_schema(init_pack_out):
    domain, out = init_pack_out
    data = json.loads((out / "boundary_statement.json").read_text(encoding="utf-8"))
    assert data["schema"] == "hal.yieldos.pilot_boundary_statement.v1"


def test_boundary_statement_read_only(init_pack_out):
    domain, out = init_pack_out
    data = json.loads((out / "boundary_statement.json").read_text(encoding="utf-8"))
    assert data["read_only"] is True
    assert data["human_review_required"] is True
    assert data["automatic_decision_enabled"] is False
    assert data["approval_gate_required"] is True


def test_boundary_statement_no_forbidden_terms(init_pack_out):
    domain, out = init_pack_out
    text = (out / "boundary_statement.json").read_text(encoding="utf-8")
    forbidden = [
        "safety_certified",
        "yield_guarantee",
        "automatic_recovery_execution",
    ]
    for term in forbidden:
        # these should appear only in blocked_claims list, not as positive claims
        data = json.loads(text)
        for claim in data.get("evidence_claims", []):
            assert term not in claim, f"{domain}: forbidden term '{term}' in evidence_claims"


# ── pilot_readme.md ────────────────────────────────────────────────────────────

def test_pilot_readme_exists_and_nonempty(init_pack_out):
    domain, out = init_pack_out
    readme = out / "pilot_readme.md"
    assert readme.exists()
    content = readme.read_text(encoding="utf-8")
    assert len(content) > 200
    assert domain in content
    assert "pilot check" in content
